import logging
from typing import List, Dict, Optional
from ..models.cold_climate import (
    ColdClimateInput,
    ColdClimateResponse,
    PerformanceAnalysis,
    BackupHeatRecommendation,
    BackupHeatType,
    TemperatureCapacityPoint,
)
from .design_temp_service import design_temp_service
from .capacity_curve_service import capacity_curve_service

logger = logging.getLogger("heatpumpiq.service.cold_climate")


class ColdClimateService:
    # Design load calculation (simplified - should match Quick-Sizer logic)
    DESIGN_LOAD_COEFFICIENTS = {
        "1A": {"old": 35, "medium": 30, "new": 25},
        "2A": {"old": 35, "medium": 30, "new": 25},
        "3A": {"old": 40, "medium": 35, "new": 30},
        "3B": {"old": 35, "medium": 30, "new": 25},
        "4A": {"old": 45, "medium": 40, "new": 35},
        "4B": {"old": 40, "medium": 35, "new": 30},
        "4C": {"old": 40, "medium": 35, "new": 30},
        "5A": {"old": 50, "medium": 45, "new": 40},
        "5B": {"old": 45, "medium": 40, "new": 35},
        "6A": {"old": 55, "medium": 50, "new": 45},
        "6B": {"old": 50, "medium": 45, "new": 40},
        "7": {"old": 60, "medium": 55, "new": 50},
        "8": {"old": 65, "medium": 60, "new": 55},
    }

    def check_performance(self, input_data: ColdClimateInput) -> ColdClimateResponse:
        """Check cold climate performance - alias for analyze_cold_climate_performance."""
        return self.analyze_cold_climate_performance(input_data)

    def analyze_cold_climate_performance(self, input_data: ColdClimateInput) -> ColdClimateResponse:
        """Analyze heat pump performance in cold climate"""
        try:
            logger.info(
                f"🧊 Starting cold climate analysis for {input_data.square_feet} sqft, ZIP {input_data.zip_code}, model {input_data.heat_pump_model}"
            )

            # Get location and climate data (validates ZIP code)
            temp_data = design_temp_service.get_design_temp(input_data.zip_code)
            logger.info(
                f"🌡️ Found climate data: {temp_data['city']}, {temp_data['state']} - Zone {temp_data['climate_zone']}, Design temp {temp_data['design_temp']}°F"
            )

            design_temp = temp_data["design_temp"]
            climate_zone = temp_data["climate_zone"]

            # Calculate design heating load
            logger.info(
                f"🔥 Calculating design heating load for {input_data.square_feet} sqft home"
            )
            design_load = self._calculate_design_load(
                input_data.square_feet, input_data.build_year, climate_zone, design_temp
            )
            logger.info(f"🔥 Design heating load: {design_load:,.0f} BTU at {design_temp}°F")

            # Get heat pump capacity curve
            logger.info(f"📋 Getting capacity curve for {input_data.heat_pump_model}")
            capacity_curve = capacity_curve_service.get_capacity_curve(
                input_data.heat_pump_model, temp_range=(int(design_temp) - 5, 50)
            )

            # Get capacity at design temperature
            hp_capacity_at_design, cop_at_design = (
                capacity_curve_service.get_capacity_at_temperature(
                    input_data.heat_pump_model, design_temp
                )
            )
            logger.info(
                f"🔧 Heat pump capacity at design temp: {hp_capacity_at_design:,.0f} BTU, COP: {cop_at_design:.2f}"
            )

            # Performance analysis
            coverage_percent = (hp_capacity_at_design / design_load) * 100
            backup_needed = max(0, design_load - hp_capacity_at_design)

            logger.info(f"📊 Performance analysis: {coverage_percent:.1f}% coverage")
            if backup_needed > 0:
                logger.info(f"🌡️ Backup heat needed: {backup_needed:,.0f} BTU")
            else:
                logger.info(f"✅ No backup heat required - full coverage achieved")

            performance_rating = self._get_performance_rating(coverage_percent)
            logger.info(f"🏅 Performance rating: {performance_rating}")

            performance_analysis = PerformanceAnalysis(
                design_temperature=design_temp,
                design_load_btu=int(design_load),
                heat_pump_capacity_at_design=int(hp_capacity_at_design),
                capacity_coverage_percent=round(coverage_percent, 1),
                backup_heat_needed_btu=int(backup_needed),
                performance_rating=performance_rating,
            )

            # Backup heat recommendation
            backup_recommendation = None
            if backup_needed > 0:
                logger.info(f"🔧 Generating backup heat recommendation")
                backup_recommendation = self._get_backup_heat_recommendation(
                    backup_needed, input_data.existing_backup_heat, climate_zone
                )
                logger.info(
                    f"🔧 Backup recommendation: {backup_recommendation.recommended_type.value}, {backup_recommendation.required_capacity_btu:,} BTU"
                )

            # Temperature range analysis
            logger.info(f"🌡️ Analyzing performance across temperature range")
            temp_analysis = self._analyze_temperature_range(
                capacity_curve, design_load, design_temp
            )

            # Key findings and warnings
            key_findings = self._generate_key_findings(
                performance_analysis, backup_recommendation, temp_data
            )
            logger.info(f"📋 Generated {len(key_findings)} key findings")

            warnings = self._generate_warnings(performance_analysis, design_temp, climate_zone)
            if warnings:
                logger.warning(f"⚠️ Generated {len(warnings)} warnings for cold climate analysis")
            else:
                logger.info(f"✅ No warnings generated - good cold climate performance")

            # Calculation notes
            calculation_notes = [
                f"Design load calculated for {input_data.square_feet} sq ft home built in {input_data.build_year}",
                f"Heat pump capacity data from manufacturer specifications",
                f"Analysis based on 99% design temperature of {design_temp}°F",
                f"Backup heat sizing includes 10% safety factor",
            ]

            logger.info(
                f"✅ Cold climate analysis completed successfully: {performance_rating} performance, {coverage_percent:.1f}% coverage"
            )

            return ColdClimateResponse(
                location_info={
                    "city": temp_data.get("city", "Unknown"),
                    "state": temp_data.get("state", "Unknown"),
                    "climate_zone": climate_zone,
                },
                heat_pump_model=input_data.heat_pump_model,
                design_conditions={
                    "design_temperature": design_temp,
                    "design_load_btu": design_load,
                },
                capacity_curve=capacity_curve,
                performance_analysis=performance_analysis,
                backup_heat_recommendation=backup_recommendation,
                temperature_range_analysis=temp_analysis,
                key_findings=key_findings,
                warnings=warnings,
                calculation_notes=calculation_notes,
            )

        except Exception as e:
            logger.error(
                f"❌ Cold climate analysis FAILED for {input_data.square_feet} sqft, ZIP {input_data.zip_code}"
            )
            logger.error(f"❌ Input data: {input_data.model_dump()}")
            logger.error(f"❌ Error details: {str(e)}", exc_info=True)
            raise

    def _calculate_design_load(
        self, sqft: int, build_year: int, climate_zone: str, design_temp: float
    ) -> float:
        """Calculate design heating load - matches Quick-Sizer logic"""

        # Determine age category
        current_year = 2025
        age = current_year - build_year
        if age > 40:
            age_category = "old"
        elif age > 20:
            age_category = "medium"
        else:
            age_category = "new"

        # Get coefficient
        if climate_zone not in self.DESIGN_LOAD_COEFFICIENTS:
            climate_zone = "4A"  # Default

        coefficient = self.DESIGN_LOAD_COEFFICIENTS[climate_zone][age_category]

        # Calculate load
        design_load = sqft * coefficient

        return design_load

    def _get_performance_rating(self, coverage_percent: float) -> str:
        """Get performance rating based on coverage percentage"""

        if coverage_percent >= 100:
            return "Excellent"
        elif coverage_percent >= 90:
            return "Good"
        elif coverage_percent >= 75:
            return "Marginal"
        else:
            return "Inadequate"

    def _get_backup_heat_recommendation(
        self, backup_needed: float, existing_backup: Optional[BackupHeatType], climate_zone: str
    ) -> BackupHeatRecommendation:
        """Generate backup heat recommendation"""

        # Add 10% safety factor
        required_capacity = int(backup_needed * 1.1)

        # Determine best backup type based on climate and existing system
        if existing_backup and existing_backup != BackupHeatType.NONE:
            recommended_type = existing_backup
            complexity = "Simple"
            reasoning = f"Upgrade existing {existing_backup.value.replace('_', ' ')} system"
        else:
            # Electric strip is most common for heat pumps
            recommended_type = BackupHeatType.ELECTRIC_STRIP
            complexity = "Moderate"
            reasoning = "Electric resistance strips integrate well with heat pump systems"

        # Estimate cost range based on capacity
        if required_capacity < 10000:
            cost_range = "$500-$1,500"
        elif required_capacity < 20000:
            cost_range = "$1,500-$3,000"
        else:
            cost_range = "$3,000-$6,000"

        return BackupHeatRecommendation(
            recommended_type=recommended_type,
            required_capacity_btu=required_capacity,
            estimated_cost_range=cost_range,
            installation_complexity=complexity,
            reasoning=reasoning,
        )

    def _analyze_temperature_range(
        self, capacity_curve: List[TemperatureCapacityPoint], design_load: float, design_temp: float
    ) -> List[Dict]:
        """Analyze performance across temperature range"""

        analysis = []

        for point in capacity_curve:
            temp = point.temperature
            capacity = point.capacity_btu
            cop = point.cop

            coverage = (capacity / design_load) * 100

            if temp <= design_temp:
                status = "Critical" if coverage < 75 else "Adequate" if coverage < 100 else "Good"
            else:
                status = "Good"

            analysis.append(
                {
                    "temperature": temp,
                    "capacity_btu": capacity,
                    "cop": cop,
                    "coverage_percent": round(coverage, 1),
                    "status": status,
                }
            )

        return analysis

    def _generate_key_findings(
        self,
        performance: PerformanceAnalysis,
        backup: Optional[BackupHeatRecommendation],
        temp_data: Dict,
    ) -> List[str]:
        """Generate key findings from analysis"""

        findings = []

        # Coverage finding
        findings.append(
            f"Heat pump provides {performance.capacity_coverage_percent}% of design heating load at {performance.design_temperature}°F"
        )

        # Performance rating
        findings.append(
            f"Overall cold-climate performance rated as '{performance.performance_rating}'"
        )

        # Backup heat finding
        if backup:
            findings.append(
                f"Backup heating system needed: {backup.required_capacity_btu:,} BTU capacity"
            )
        else:
            findings.append("No backup heating required - heat pump covers full load")

        # Efficiency finding
        if performance.capacity_coverage_percent < 100:
            findings.append("Heat pump will operate efficiently above design temperature")

        return findings

    def _generate_warnings(
        self, performance: PerformanceAnalysis, design_temp: float, climate_zone: str
    ) -> List[str]:
        """Generate warnings based on analysis"""

        warnings = []

        # Inadequate performance warning
        if performance.performance_rating == "Inadequate":
            warnings.append(
                "⚠️ Heat pump provides less than 75% of heating capacity at design temperature"
            )

        # Very cold climate warning
        if design_temp < 0:
            warnings.append(
                "⚠️ Extremely cold climate - consider high-performance cold-climate heat pump"
            )

        # No backup warning
        if performance.backup_heat_needed_btu > 10000:
            warnings.append(
                "⚠️ Significant backup heating required - ensure adequate electrical capacity"
            )

        # Climate zone warning
        if climate_zone in ["6A", "6B", "7", "8"]:
            warnings.append("⚠️ Very cold climate zone - heat pump performance may be limited")

        return warnings


# Singleton instance
cold_climate_service = ColdClimateService()
