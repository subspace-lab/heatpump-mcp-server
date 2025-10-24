"""
Multi-Zone Heat Pump Sizing Service

Calculates heating/cooling loads for multiple zones and recommends
system configurations based on Reddit analysis insights.
"""

from typing import List, Dict, Tuple
from ..models.multi_zone import (
    Zone, ZoneType, SunExposure, OccupancyLevel, AirSealing, HeatSource,
    ZoneResult, SystemOption, MultiZoneResponse
)
from .design_temp_service import design_temp_service

def get_climate_zone_coefficient(build_year: int, zip_code: str) -> Dict[str, float]:
    """Get climate zone specific coefficients for heating and cooling."""
    # Simplified climate zone determination based on first digit of ZIP
    # In real implementation, would use proper climate zone data
    zip_prefix = int(zip_code[0])
    
    # Climate zone adjustments based on region
    climate_factors = {
        0: {"cooling": 0.9, "heating": 1.2},   # Northeast (cold)
        1: {"cooling": 0.95, "heating": 1.15}, # Mid-Atlantic  
        2: {"cooling": 1.0, "heating": 1.1},   # Southeast
        3: {"cooling": 1.1, "heating": 0.9},   # South
        4: {"cooling": 0.9, "heating": 1.0},   # Midwest
        5: {"cooling": 0.85, "heating": 1.1},  # Central Plains
        6: {"cooling": 1.0, "heating": 0.95},  # South Central
        7: {"cooling": 1.15, "heating": 0.8},  # Southwest
        8: {"cooling": 0.95, "heating": 0.9},  # Mountain
        9: {"cooling": 0.8, "heating": 0.85}   # Pacific
    }
    
    # Age factor (older homes are less efficient)
    if build_year < 1960:
        age_factor = 1.3
    elif build_year < 1980:
        age_factor = 1.2
    elif build_year < 2000:
        age_factor = 1.1
    else:
        age_factor = 1.0
    
    base_factors = climate_factors.get(zip_prefix, {"cooling": 1.0, "heating": 1.0})
    
    return {
        "cooling": base_factors["cooling"] * age_factor,
        "heating": base_factors["heating"] * age_factor
    }

class MultiZoneService:
    
    # Zone-specific base coefficients (BTU per sq ft)
    ZONE_BASE_COEFFICIENTS = {
        ZoneType.LIVING_AREA: {"cooling": 25, "heating": 30},
        ZoneType.BEDROOMS: {"cooling": 20, "heating": 25}, 
        ZoneType.KITCHEN: {"cooling": 30, "heating": 35},
        ZoneType.BASEMENT: {"cooling": 15, "heating": 35},
        ZoneType.ATTIC: {"cooling": 35, "heating": 20},
        ZoneType.GARAGE: {"cooling": 12, "heating": 40},
        ZoneType.OTHER: {"cooling": 22, "heating": 28}
    }
    
    # Sun exposure multipliers
    SUN_EXPOSURE_FACTORS = {
        SunExposure.SOUTH: {"cooling": 1.15, "heating": 0.95},
        SunExposure.WEST: {"cooling": 1.10, "heating": 1.0},
        SunExposure.EAST: {"cooling": 1.05, "heating": 1.0}, 
        SunExposure.NORTH: {"cooling": 0.90, "heating": 1.05},
        SunExposure.MINIMAL: {"cooling": 0.85, "heating": 1.10}
    }
    
    # Occupancy multipliers
    OCCUPANCY_FACTORS = {
        OccupancyLevel.HIGH: {"cooling": 1.15, "heating": 1.1},
        OccupancyLevel.MEDIUM: {"cooling": 1.0, "heating": 1.0},
        OccupancyLevel.LOW: {"cooling": 0.85, "heating": 0.9}
    }
    
    # Air sealing impact
    AIR_SEALING_FACTORS = {
        AirSealing.TIGHT: {"cooling": 0.9, "heating": 0.85},
        AirSealing.AVERAGE: {"cooling": 1.0, "heating": 1.0},
        AirSealing.LEAKY: {"cooling": 1.15, "heating": 1.25}
    }
    
    # Heat source additions (BTU)
    HEAT_SOURCE_LOADS = {
        HeatSource.KITCHEN_APPLIANCES: {"cooling": 2000, "heating": -500},
        HeatSource.ELECTRONICS: {"cooling": 500, "heating": 0},
        HeatSource.HOME_OFFICE: {"cooling": 800, "heating": 0},
        HeatSource.LAUNDRY: {"cooling": 1200, "heating": -300},
        HeatSource.FIREPLACE: {"cooling": 0, "heating": -2000}
    }

    def calculate_zone_load(self, zone: Zone, zip_code: str, build_year: int) -> Tuple[int, int, Dict]:
        """Calculate heating and cooling loads for a single zone."""
        
        # Get base coefficient adjusted for build year and climate
        climate_coefficient = get_climate_zone_coefficient(build_year, zip_code)
        base_coeff = self.ZONE_BASE_COEFFICIENTS[zone.zone_type]
        
        # Base load calculation
        cooling_base = zone.square_feet * base_coeff["cooling"] * climate_coefficient["cooling"]
        heating_base = zone.square_feet * base_coeff["heating"] * climate_coefficient["heating"]
        
        # Ceiling height adjustment
        height_factor = zone.ceiling_height / 8.0  # 8ft is baseline
        
        # Sun exposure adjustment
        sun_factor = self.SUN_EXPOSURE_FACTORS[zone.sun_exposure]
        
        # Window coverage impact
        window_factor = 1.0 + (zone.window_coverage - 0.15) * 2.0  # 15% is baseline
        
        # Occupancy adjustment
        occupancy_factor = self.OCCUPANCY_FACTORS[zone.occupancy]
        
        # Air sealing impact
        air_factor = self.AIR_SEALING_FACTORS[zone.air_sealing]
        
        # Below grade adjustment (basements are cooler in summer, harder to heat)
        grade_factor = {"cooling": 0.7, "heating": 1.3} if not zone.is_above_grade else {"cooling": 1.0, "heating": 1.0}
        
        # Calculate adjusted loads
        cooling_load = (cooling_base * height_factor * sun_factor["cooling"] * 
                       window_factor * occupancy_factor["cooling"] * 
                       air_factor["cooling"] * grade_factor["cooling"])
        
        heating_load = (heating_base * height_factor * sun_factor["heating"] * 
                       window_factor * occupancy_factor["heating"] * 
                       air_factor["heating"] * grade_factor["heating"])
        
        # Add heat source impacts
        for heat_source in zone.heat_sources:
            source_load = self.HEAT_SOURCE_LOADS[heat_source]
            cooling_load += source_load["cooling"]
            heating_load += source_load["heating"]
        
        # Track factors for transparency
        load_factors = {
            "base_coefficient": base_coeff,
            "climate_coefficient": climate_coefficient,
            "height_factor": height_factor,
            "sun_exposure_factor": sun_factor,
            "window_coverage_factor": window_factor,
            "occupancy_factor": occupancy_factor,
            "air_sealing_factor": air_factor,
            "grade_factor": grade_factor,
            "heat_source_additions": sum(self.HEAT_SOURCE_LOADS[hs]["cooling"] for hs in zone.heat_sources)
        }
        
        return int(cooling_load), int(heating_load), load_factors

    def recommend_equipment_for_zone(self, cooling_load: int, heating_load: int) -> List[Dict]:
        """Recommend equipment options for a specific zone load."""
        
        # Determine capacity in tons (use higher of cooling/heating)
        max_load = max(cooling_load, heating_load)
        capacity_tons = max_load / 12000  # 12,000 BTU = 1 ton
        
        recommendations = []
        
        # Round to nearest 0.5 ton
        recommended_tons = round(capacity_tons * 2) / 2
        recommended_tons = max(1.0, recommended_tons)  # Minimum 1 ton
        
        if recommended_tons <= 2.0:
            # Mini-split recommendations
            recommendations.extend([
                {
                    "type": "mini_split",
                    "brand": "Mitsubishi",
                    "model": f"MSZ-FH{int(recommended_tons * 12)}VE",
                    "capacity_tons": recommended_tons,
                    "capacity_btu": int(recommended_tons * 12000),
                    "hspf2": 10.0,
                    "seer2": 23.0,
                    "price_range": f"${2500 + int(recommended_tons * 800)}-{3000 + int(recommended_tons * 1000)}",
                    "features": ["Variable speed", "Quiet operation", "WiFi capable"]
                },
                {
                    "type": "mini_split", 
                    "brand": "Daikin",
                    "model": f"RXS{int(recommended_tons * 12)}LVJU",
                    "capacity_tons": recommended_tons,
                    "capacity_btu": int(recommended_tons * 12000),
                    "hspf2": 9.5,
                    "seer2": 22.0,
                    "price_range": f"${2200 + int(recommended_tons * 700)}-{2700 + int(recommended_tons * 900)}",
                    "features": ["Inverter technology", "Low ambient operation"]
                }
            ])
        
        if recommended_tons >= 1.5:
            # Ducted options for larger zones
            recommendations.append({
                "type": "ducted_heat_pump",
                "brand": "Carrier",
                "model": f"25HCE{int(recommended_tons * 2)}",
                "capacity_tons": recommended_tons,
                "capacity_btu": int(recommended_tons * 12000),
                "hspf2": 9.0,
                "seer2": 20.0,
                "price_range": f"${3000 + int(recommended_tons * 1200)}-{4500 + int(recommended_tons * 1500)}",
                "features": ["Ducted system", "Zoning compatible", "High efficiency"]
            })
        
        return recommendations

    def generate_system_options(self, zone_results: List[ZoneResult]) -> List[SystemOption]:
        """Generate different system configuration options."""
        
        options = []
        total_cooling = sum(zr.cooling_load_btu for zr in zone_results)
        total_heating = sum(zr.heating_load_btu for zr in zone_results)
        
        # Option 1: Individual mini-splits per zone
        individual_cost = 0
        equipment_list = []
        for zone_result in zone_results:
            if zone_result.equipment_recommendations:
                best_option = zone_result.equipment_recommendations[0]  # First is usually best
                individual_cost += int(best_option["price_range"].split('-')[0].replace('$', '').replace(',', ''))
                equipment_list.append({
                    "zone": zone_result.zone_name,
                    "equipment": best_option
                })
        
        options.append(SystemOption(
            option_name="Individual Zone Systems",
            description="Separate mini-split for each zone - maximum control and efficiency",
            total_equipment_cost=individual_cost,
            installation_complexity="moderate",
            energy_efficiency_rating=9.5,
            zones_served=[zr.zone_name for zr in zone_results],
            equipment_list=equipment_list
        ))
        
        # Option 2: Multi-zone system (if 2-4 zones)
        if 2 <= len(zone_results) <= 4:
            total_tons = sum(zr.recommended_capacity_tons for zr in zone_results)
            multi_zone_cost = int(4000 + total_tons * 1500)  # Base cost + per ton
            
            options.append(SystemOption(
                option_name="Multi-Zone System",
                description="Single outdoor unit with multiple indoor heads - good balance of cost and control",
                total_equipment_cost=multi_zone_cost,
                installation_complexity="complex",
                energy_efficiency_rating=9.0,
                zones_served=[zr.zone_name for zr in zone_results],
                equipment_list=[{
                    "type": "multi_zone_system",
                    "outdoor_unit": f"Multi-zone {total_tons:.1f} ton system",
                    "indoor_units": len(zone_results),
                    "estimated_cost": multi_zone_cost
                }]
            ))
        
        # Option 3: Hybrid approach (main system + mini-splits)
        if len(zone_results) >= 3:
            main_zones = zone_results[:2]  # Largest zones
            mini_zones = zone_results[2:]  # Smaller zones
            
            main_load = sum(zr.cooling_load_btu + zr.heating_load_btu for zr in main_zones) / 2
            main_tons = main_load / 12000
            
            hybrid_cost = int(3500 + main_tons * 1200)  # Main system
            for zone_result in mini_zones:
                if zone_result.equipment_recommendations:
                    mini_cost = int(zone_result.equipment_recommendations[0]["price_range"].split('-')[0].replace('$', '').replace(',', ''))
                    hybrid_cost += mini_cost
            
            options.append(SystemOption(
                option_name="Hybrid System",
                description="Main system for primary zones + mini-splits for additional areas",
                total_equipment_cost=hybrid_cost,
                installation_complexity="complex",
                energy_efficiency_rating=8.5,
                zones_served=[zr.zone_name for zr in zone_results],
                equipment_list=[{
                    "main_system": f"{main_tons:.1f} ton ducted system",
                    "mini_splits": len(mini_zones),
                    "estimated_cost": hybrid_cost
                }]
            ))
        
        return sorted(options, key=lambda x: x.total_equipment_cost)

    def calculate_multi_zone(self, zones: List[Zone], zip_code: str, build_year: int) -> MultiZoneResponse:
        """Main entry point for multi-zone calculations."""
        
        # Calculate load for each zone
        zone_results = []
        total_cooling = 0
        total_heating = 0
        
        for zone in zones:
            cooling_load, heating_load, load_factors = self.calculate_zone_load(zone, zip_code, build_year)
            equipment_recs = self.recommend_equipment_for_zone(cooling_load, heating_load)
            
            # Calculate recommended capacity (use higher load)
            max_load = max(cooling_load, heating_load)
            recommended_tons = max(1.0, round((max_load / 12000) * 2) / 2)
            
            zone_result = ZoneResult(
                zone_name=zone.name,
                cooling_load_btu=cooling_load,
                heating_load_btu=heating_load,
                recommended_capacity_tons=recommended_tons,
                load_factors=load_factors,
                equipment_recommendations=equipment_recs
            )
            zone_results.append(zone_result)
            
            total_cooling += cooling_load
            total_heating += heating_load
        
        # Get climate info
        climate_data = design_temp_service.get_design_temp(zip_code)
        
        # Generate system options
        system_options = self.generate_system_options(zone_results)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(zone_results, total_cooling, total_heating)
        
        return MultiZoneResponse(
            total_cooling_load=total_cooling,
            total_heating_load=total_heating,
            zone_results=zone_results,
            system_options=system_options,
            climate_info=climate_data,
            recommendations=recommendations
        )

    def _generate_recommendations(self, zone_results: List[ZoneResult], total_cooling: int, total_heating: int) -> Dict:
        """Generate general recommendations based on results."""
        
        recommendations = {
            "sizing_notes": [],
            "system_considerations": [],
            "efficiency_tips": []
        }
        
        # Sizing recommendations
        if len(zone_results) > 1:
            recommendations["sizing_notes"].append(
                f"Multi-zone approach allows for {len(zone_results)} independent temperature controls"
            )
        
        avg_tons_per_zone = (total_cooling + total_heating) / 2 / 12000 / len(zone_results)
        if avg_tons_per_zone < 1.5:
            recommendations["sizing_notes"].append(
                "Zones are relatively small - mini-splits may be most cost-effective"
            )
        elif avg_tons_per_zone > 3.0:
            recommendations["sizing_notes"].append(
                "Large zones detected - consider ducted systems for better air distribution"
            )
        
        # System considerations based on zone types
        zone_types = [zr.zone_name.lower() for zr in zone_results]
        if any("basement" in zt for zt in zone_types):
            recommendations["system_considerations"].append(
                "Basement zones require special attention to humidity control and drainage"
            )
        
        if any("kitchen" in zt for zt in zone_types):
            recommendations["system_considerations"].append(
                "Kitchen zones have higher cooling loads due to appliance heat gain"
            )
        
        # Efficiency tips
        recommendations["efficiency_tips"].extend([
            "Consider zoning controls to avoid conditioning unused spaces",
            "Proper insulation and air sealing will reduce loads significantly",
            "Variable-speed equipment provides better comfort and efficiency"
        ])
        
        return recommendations

# Service instance
multi_zone_service = MultiZoneService()