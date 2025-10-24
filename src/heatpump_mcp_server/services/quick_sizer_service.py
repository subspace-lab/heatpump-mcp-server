import logging
from typing import List
from ..models.quick_sizer import QuickSizerInput, QuickSizerResponse, HeatPumpModel
from .design_temp_service import design_temp_service
from .heat_pump_models_service import heat_pump_models_service

logger = logging.getLogger("heatpumpiq.service.quick_sizer")


class QuickSizerService:
    # BTU coefficients based on build age and climate zone
    # Format: {climate_zone: {age_category: coefficient}}
    BTU_COEFFICIENTS = {
        "1A": {"old": 35, "medium": 30, "new": 25},  # Hot humid
        "1B": {
            "old": 35,
            "medium": 30,
            "new": 30,
        },  # Hot dry (Phoenix, Las Vegas) - higher cooling load
        "2A": {"old": 35, "medium": 30, "new": 25},  # Hot humid
        "2B": {"old": 30, "medium": 25, "new": 20},  # Hot dry
        "3A": {"old": 40, "medium": 35, "new": 30},  # Mixed humid
        "3B": {"old": 35, "medium": 30, "new": 25},  # Hot dry
        "3C": {"old": 35, "medium": 30, "new": 25},  # Marine (San Francisco)
        "4A": {"old": 45, "medium": 40, "new": 35},  # Mixed humid
        "4B": {"old": 40, "medium": 35, "new": 30},  # Mixed dry
        "4C": {"old": 40, "medium": 35, "new": 30},  # Marine
        "5A": {"old": 50, "medium": 45, "new": 40},  # Cool humid
        "5B": {"old": 45, "medium": 40, "new": 35},  # Cool dry
        "6A": {"old": 55, "medium": 50, "new": 45},  # Cold humid
        "6B": {"old": 50, "medium": 45, "new": 40},  # Cold dry
        "7": {"old": 60, "medium": 55, "new": 50},  # Very cold
        "8": {"old": 65, "medium": 60, "new": 55},  # Subarctic
    }

    @property
    def HEAT_PUMP_MODELS(self):
        """Get heat pump models from data service"""
        return heat_pump_models_service.get_all_models()

    def calculate_btu(self, input_data: QuickSizerInput) -> QuickSizerResponse:
        try:
            logger.info(
                f"🧮 Starting BTU calculation for {input_data.square_feet} sqft, ZIP {input_data.zip_code}, built {input_data.build_year}"
            )

            # Get design temperature and climate zone (validates ZIP code)
            temp_data = design_temp_service.get_design_temp(input_data.zip_code)
            logger.info(
                f"🌡️ Found design data: {temp_data['city']}, {temp_data['state']} - Zone {temp_data['climate_zone']}, Design temp {temp_data['design_temp']}°F"
            )

            # Determine age category
            current_year = 2025
            age = current_year - input_data.build_year
            if age > 40:
                age_category = "old"
            elif age > 20:
                age_category = "medium"
            else:
                age_category = "new"

            logger.info(f"🏠 Building age: {age} years, category: {age_category}")

            # Get coefficient for climate zone
            climate_zone = temp_data["climate_zone"]

            # Map simple zone numbers to ASHRAE zones
            if climate_zone not in self.BTU_COEFFICIENTS:
                zone_map = {
                    "1": "1A",  # Hot humid
                    "2": "2A",  # Hot humid
                    "3": "3A",  # Mixed humid (California coastal/Mediterranean)
                    "4": "4A",  # Mixed humid (Northeast)
                    "5": "5A",  # Cool humid
                    "6": "6A",  # Cold humid
                    "7": "7",  # Very cold
                    "8": "8",  # Subarctic
                }
                mapped_zone = zone_map.get(str(climate_zone), "4A")
                logger.info(f"🗺️ Mapped climate zone {climate_zone} → {mapped_zone}")
                climate_zone = mapped_zone

            base_coefficient = self.BTU_COEFFICIENTS[climate_zone][age_category]
            logger.info(
                f"🎯 Base BTU coefficient: {base_coefficient} BTU/sqft for zone {climate_zone}, {age_category} construction"
            )

            # Apply size-based adjustments
            coefficient = self._apply_size_adjustments(
                base_coefficient, input_data.square_feet, input_data.build_year
            )
            logger.info(f"⚖️ Adjusted coefficient after size factors: {coefficient:.2f} BTU/sqft")

            # Calculate required BTU
            required_btu = input_data.square_feet * coefficient
            logger.info(
                f"🧮 Base BTU calculation: {input_data.square_feet} sqft × {coefficient:.2f} = {required_btu:.0f} BTU"
            )

            # Apply humidity adjustments if needed
            humidity_adjustments = {}
            if input_data.humidity_concerns or input_data.humidity_level != "normal":
                logger.info(
                    f"💧 Applying humidity adjustments for level: {input_data.humidity_level}"
                )
                humidity_factor, humidity_adjustments = self._calculate_humidity_adjustments(
                    input_data, climate_zone
                )
                original_btu = required_btu
                required_btu *= humidity_factor
                logger.info(
                    f"💧 Humidity factor: {humidity_factor:.3f}, BTU adjusted from {original_btu:.0f} to {required_btu:.0f}"
                )
                if humidity_adjustments:
                    logger.info(f"💧 Humidity adjustment breakdown: {humidity_adjustments}")

            # Check for oversizing warnings
            btu_per_sqft = required_btu / input_data.square_feet
            logger.info(f"📏 Final BTU/sqft ratio: {btu_per_sqft:.1f}")
            oversizing_warnings = self._check_oversizing_warnings(
                btu_per_sqft, climate_zone, input_data
            )
            if oversizing_warnings:
                logger.warning(
                    f"⚠️ Oversizing warnings generated: {len(oversizing_warnings)} warnings"
                )

            # Add 10% margin for safety
            btu_range_min = int(required_btu * 0.9)
            btu_range_max = int(required_btu * 1.1)
            logger.info(f"📊 BTU range: {btu_range_min:,} - {btu_range_max:,} BTU")

            # Find recommended models (considering humidity needs)
            recommended_models = self._find_recommended_models(required_btu, input_data)
            logger.info(f"🔧 Found {len(recommended_models)} recommended heat pump models")

            # Generate humidity recommendations
            humidity_recommendations = None
            dehumidification_capacity = None
            if input_data.humidity_concerns or input_data.humidity_level != "normal":
                humidity_recommendations = self._generate_humidity_recommendations(
                    input_data, climate_zone
                )
                dehumidification_capacity = self._calculate_dehumidification_capacity(
                    required_btu, input_data
                )
                logger.info(
                    f"💧 Generated humidity recommendations and dehumidification capacity: {dehumidification_capacity} pints/day"
                )

            # Create calculation notes
            calculation_notes = (
                f"Calculation based on {input_data.square_feet} sq ft home built in {input_data.build_year} "
                f"({age_category} construction) in climate zone {climate_zone}. "
                f"Using coefficient of {coefficient} BTU/sq ft."
            )

            if humidity_adjustments:
                calculation_notes += f" Humidity adjustments applied: +{((sum(humidity_adjustments.values())) * 100):.1f}% for moisture control."

            if temp_data.get("approximate"):
                calculation_notes += " Note: Exact ZIP code not found, using nearby location data."
                logger.info(f"📍 Used approximate location data for ZIP {input_data.zip_code}")

            logger.info(
                f"✅ BTU calculation completed successfully: {int(required_btu):,} BTU required"
            )

            return QuickSizerResponse(
                required_btu=int(required_btu),
                btu_range_min=btu_range_min,
                btu_range_max=btu_range_max,
                design_temperature=temp_data["design_temp"],
                climate_zone=climate_zone,
                recommended_models=recommended_models,
                calculation_notes=calculation_notes,
                humidity_recommendations=humidity_recommendations,
                dehumidification_capacity=dehumidification_capacity,
                humidity_adjustments=humidity_adjustments,
                oversizing_warnings=oversizing_warnings,
            )

        except Exception as e:
            logger.error(
                f"❌ BTU calculation FAILED for {input_data.square_feet} sqft, ZIP {input_data.zip_code}"
            )
            logger.error(f"❌ Input data: {input_data.model_dump()}")
            logger.error(f"❌ Error details: {str(e)}", exc_info=True)
            raise

    def _find_recommended_models(
        self, required_btu: int, input_data: QuickSizerInput = None
    ) -> List[HeatPumpModel]:
        # Find models within +/- 20% of required BTU
        min_btu = required_btu * 0.8
        max_btu = required_btu * 1.2

        suitable_models = []
        for model in self.HEAT_PUMP_MODELS:
            if min_btu <= model["btu_capacity"] <= max_btu:
                suitable_models.append(HeatPumpModel(**model))

        # Sort by HSPF2 (efficiency) descending, but consider humidity needs
        if input_data and (input_data.humidity_concerns or input_data.dehumidification_priority):
            # Prioritize models known for better dehumidification (like Mitsubishi and Fujitsu)
            def humidity_priority_sort(model):
                brand_bonus = 0.5 if model.brand in ["Mitsubishi", "Fujitsu"] else 0
                return model.hspf2 + brand_bonus

            suitable_models.sort(key=humidity_priority_sort, reverse=True)
        else:
            suitable_models.sort(key=lambda x: x.hspf2, reverse=True)

        # Return top 3
        return suitable_models[:3]

    def _calculate_humidity_adjustments(
        self, input_data: QuickSizerInput, climate_zone: str
    ) -> tuple:
        """Calculate humidity-related adjustments to BTU requirements."""
        adjustments = {}
        total_factor = 1.0

        # Base humidity adjustment by climate zone
        humid_zones = ["1A", "2A", "3A", "4A", "5A", "6A"]  # Humid zones
        is_humid_climate = climate_zone in humid_zones

        # Count active humidity factors to prevent excessive stacking
        humidity_factors_count = 0
        active_factors = []

        # Humidity level adjustments (reduced from previous aggressive multipliers)
        humidity_multipliers = {
            "low": 0.98 if is_humid_climate else 1.0,  # Slight reduction in humid climates
            "normal": 1.0,
            "high": 1.06 if is_humid_climate else 1.02,  # Further reduced for stacking
            "extreme": 1.10 if is_humid_climate else 1.05,  # Much more conservative
        }

        if input_data.humidity_level in humidity_multipliers:
            level_factor = humidity_multipliers[input_data.humidity_level]
            if level_factor != 1.0:
                adjustments["humidity_level"] = level_factor - 1.0
                total_factor *= level_factor
                if input_data.humidity_level in ["high", "extreme"]:
                    humidity_factors_count += 1
                    active_factors.append("humidity_level")

        # Dehumidification priority adds capacity (reduced and capped)
        if input_data.dehumidification_priority:
            dehumid_factor = 1.03 if humidity_factors_count == 0 else 1.02  # Reduced when stacking
            adjustments["dehumidification_priority"] = dehumid_factor - 1.0
            total_factor *= dehumid_factor
            humidity_factors_count += 1
            active_factors.append("dehumidification_priority")

        # Basement moisture issues (reduced and capped)
        if input_data.basement_moisture:
            basement_factor = (
                1.03 if humidity_factors_count <= 1 else 1.01
            )  # Much smaller when stacking
            adjustments["basement_moisture"] = basement_factor - 1.0
            total_factor *= basement_factor
            humidity_factors_count += 1
            active_factors.append("basement_moisture")

        # Poor bathroom ventilation increases load (reduced and capped)
        if input_data.bathroom_ventilation == "poor":
            ventilation_factor = (
                1.02 if humidity_factors_count <= 2 else 1.01
            )  # Minimal when stacking
            adjustments["poor_ventilation"] = ventilation_factor - 1.0
            total_factor *= ventilation_factor
            humidity_factors_count += 1
            active_factors.append("bathroom_ventilation")

        # Cap total humidity multiplier to prevent extreme oversizing
        # For small homes (<1000 sq ft), be even more conservative
        max_multiplier = 1.15 if input_data.square_feet < 1000 else 1.20
        if total_factor > max_multiplier:
            original_factor = total_factor
            total_factor = max_multiplier
            adjustments["humidity_cap_applied"] = (
                f"Capped at {(max_multiplier - 1) * 100:.0f}% (was {(original_factor - 1) * 100:.1f}%)"
            )

        return total_factor, adjustments

    def _generate_humidity_recommendations(
        self, input_data: QuickSizerInput, climate_zone: str
    ) -> dict:
        """Generate humidity-specific recommendations."""
        recommendations = {
            "equipment_features": [],
            "installation_tips": [],
            "operational_advice": [],
            "additional_equipment": [],
        }

        # Equipment features for humidity control
        if input_data.dehumidification_priority or input_data.humidity_level in ["high", "extreme"]:
            recommendations["equipment_features"].extend(
                [
                    "Variable speed compressor for better humidity control",
                    "Enhanced dehumidification mode",
                    "Dry mode operation capability",
                ]
            )

        # Installation recommendations
        if input_data.basement_moisture:
            recommendations["installation_tips"].extend(
                [
                    "Consider basement dehumidifier integration",
                    "Ensure proper drainage around outdoor unit",
                    "Install moisture barriers if needed",
                ]
            )

        if input_data.bathroom_ventilation == "poor":
            recommendations["additional_equipment"].append(
                "Bathroom exhaust fan upgrade recommended"
            )

        # Operational advice based on climate
        humid_zones = ["1A", "2A", "3A", "4A", "5A", "6A"]
        if climate_zone in humid_zones:
            recommendations["operational_advice"].extend(
                [
                    "Set fan to 'auto' mode for better dehumidification",
                    "Consider running system continuously during humid months",
                    "Regular filter changes crucial in humid climates",
                ]
            )

        # High humidity specific advice
        if input_data.humidity_level == "extreme":
            recommendations["additional_equipment"].extend(
                [
                    "Whole-house dehumidifier recommended",
                    "Smart humidity controls for optimal comfort",
                ]
            )

        return recommendations

    def _calculate_dehumidification_capacity(
        self, required_btu: int, input_data: QuickSizerInput
    ) -> float:
        """Calculate estimated dehumidification capacity in pints per day."""
        # Base dehumidification capacity (rough estimate: 1 pint/day per 1000 BTU)
        base_capacity = required_btu / 1000

        # Adjust based on humidity factors
        if input_data.humidity_level == "high":
            base_capacity *= 1.2
        elif input_data.humidity_level == "extreme":
            base_capacity *= 1.5

        if input_data.dehumidification_priority:
            base_capacity *= 1.3

        return round(base_capacity, 1)

    def _check_oversizing_warnings(
        self, btu_per_sqft: float, climate_zone: str, input_data: QuickSizerInput
    ) -> List[str]:
        """Check for potential oversizing issues and return warnings."""
        warnings = []

        # Define reasonable BTU/sq ft ranges by climate zone
        btu_ranges = {
            "1A": {"max": 40, "typical": 30},  # Hot humid
            "1B": {"max": 35, "typical": 25},  # Hot dry
            "2A": {"max": 40, "typical": 30},  # Hot humid
            "2B": {"max": 35, "typical": 25},  # Hot dry
            "3A": {"max": 45, "typical": 35},  # Mixed humid
            "3B": {"max": 40, "typical": 30},  # Hot dry
            "3C": {"max": 40, "typical": 30},  # Marine
            "4A": {"max": 50, "typical": 40},  # Mixed humid
            "4B": {"max": 45, "typical": 35},  # Mixed dry
            "4C": {"max": 45, "typical": 35},  # Marine
            "5A": {"max": 55, "typical": 45},  # Cold humid
            "5B": {"max": 50, "typical": 40},  # Cold dry
            "6A": {"max": 60, "typical": 50},  # Cold humid
            "6B": {"max": 55, "typical": 45},  # Cold dry
            "7": {"max": 65, "typical": 55},  # Very cold
            "8": {"max": 70, "typical": 60},  # Subarctic
        }

        zone_limits = btu_ranges.get(climate_zone, {"max": 50, "typical": 40})

        # Check for excessive BTU/sq ft
        if btu_per_sqft > zone_limits["max"]:
            warnings.append(
                f"High BTU/sq ft ratio ({btu_per_sqft:.1f}). Consider energy efficiency improvements before oversizing."
            )
        elif btu_per_sqft > zone_limits["typical"] * 1.3:
            warnings.append(
                f"Above-average BTU/sq ft ratio ({btu_per_sqft:.1f}). Verify insulation and air sealing."
            )

        # Check for humidity-driven oversizing
        if (
            input_data.humidity_level in ["high", "extreme"]
            and btu_per_sqft > zone_limits["typical"] * 1.2
        ):
            warnings.append(
                "Humidity concerns may be driving oversizing. Consider dedicated dehumidification instead."
            )

        # Check for very small homes (different sizing rules)
        if input_data.square_feet < 800 and btu_per_sqft > 50:
            warnings.append(
                "Small homes often require higher BTU/sq ft ratios. Consider mini-split systems for better efficiency."
            )

        # Check for very large homes
        if input_data.square_feet > 4000 and btu_per_sqft > zone_limits["typical"]:
            warnings.append(
                "Large homes benefit from zoned systems. Consider multi-zone or ducted systems for better efficiency."
            )

        return warnings

    def _apply_size_adjustments(
        self, base_coefficient: float, square_feet: int, build_year: int
    ) -> float:
        """Apply size-based adjustments to BTU coefficient based on building science.

        Adjustment is based on surface-area-to-volume ratio:
        - Smaller homes: Higher surface area relative to volume = more heat loss per sq ft
        - Larger homes: Lower surface area relative to volume = less heat loss per sq ft

        Note: Thermal mass does NOT reduce total heating load - it only delays
        temperature changes. The dominant factor is insulation quality (by age).
        """
        current_year = 2025
        age = current_year - build_year

        # Determine construction quality category for insulation levels
        if age > 80:
            construction_quality = "very_old"  # Pre-1945: minimal/no insulation
        elif age > 40:
            construction_quality = "old"  # 1945-1985: basic insulation
        elif age > 15:
            construction_quality = "modern"  # 1985-2010: code insulation
        else:
            construction_quality = "new"  # Post-2010: enhanced insulation

        # Size-based adjustments following surface-area-to-volume principles
        if square_feet <= 800:
            # Very small homes: Highest surface area to volume ratio
            size_factor = 1.20  # +20% - high heat loss relative to floor area
        elif square_feet <= 1200:
            # Small homes: Above average surface area to volume ratio
            size_factor = 1.10  # +10% - increased heat loss per sq ft
        elif square_feet <= 2000:
            # Medium homes: Average ratio (baseline)
            size_factor = 1.00  # No adjustment - reference point
        elif square_feet <= 3500:
            # Large homes: Below average surface area to volume ratio
            size_factor = 0.95  # -5% - reduced heat loss per sq ft
        else:
            # Very large homes: Lowest surface area to volume ratio
            size_factor = 0.90  # -10% - lowest heat loss per sq ft

        # REMOVED: Previous thermal mass adjustments for old buildings
        # Research shows thermal mass does not reduce heating energy consumption
        # The base coefficient already accounts for insulation quality by age

        return base_coefficient * size_factor


# Singleton instance
quick_sizer_service = QuickSizerService()
