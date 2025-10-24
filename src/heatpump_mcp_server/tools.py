"""MCP tools for heat pump calculations."""

import logging
from typing import Optional, List, Dict, Any
from pydantic import Field

logger = logging.getLogger(__name__)

# Import services
from .services.quick_sizer_service import quick_sizer_service
from .services.bill_estimator_service import bill_estimator_service
from .services.cold_climate_service import cold_climate_service
from .services.multi_zone_service import multi_zone_service
from .services.electricity_rate_service import electricity_rate_service
from .services.heat_pump_models_service import heat_pump_models_service


async def calculate_heat_pump_sizing(
    zip_code: str = Field(..., description="5-digit US ZIP code"),
    square_feet: int = Field(..., description="Home square footage (100-10000)", ge=100, le=10000),
    build_year: int = Field(..., description="Year home was built (1900-2025)", ge=1900, le=2025),
    humidity_concerns: bool = Field(False, description="Does home have humidity issues?"),
    humidity_level: str = Field("normal", description="Humidity level: low, normal, high, extreme"),
    dehumidification_priority: bool = Field(
        False, description="Prioritize dehumidification capability"
    ),
) -> Dict[str, Any]:
    """
    Calculate required BTU capacity for a single-zone heat pump installation.

    This tool performs a quick sizing calculation based on:
    - Home location (ZIP code) for climate zone and design temperature
    - Square footage and building age for heat loss estimation
    - Optional humidity considerations for enhanced dehumidification needs

    Returns:
        Dictionary with:
        - required_btu: Recommended BTU capacity
        - btu_range_min/max: Acceptable range for equipment selection
        - design_temperature: Design heating temperature for location
        - climate_zone: ASHRAE climate zone
        - recommended_models: List of suitable heat pump models
        - calculation_notes: Detailed explanation of calculations
        - humidity_recommendations: Optional humidity control advice
        - oversizing_warnings: Warnings if system may be oversized
    """
    try:
        from .models.quick_sizer import QuickSizerInput

        logger.info(
            f"Quick sizing calculation: {square_feet} sqft, ZIP {zip_code}, built {build_year}"
        )

        # Create Pydantic model instance
        input_data = QuickSizerInput(
            zip_code=zip_code,
            square_feet=square_feet,
            build_year=build_year,
            humidity_concerns=humidity_concerns,
            humidity_level=humidity_level,
            dehumidification_priority=dehumidification_priority,
        )

        result = quick_sizer_service.calculate_btu(input_data)

        return result.model_dump()
    except Exception as e:
        logger.error(f"Quick sizing failed: {str(e)}", exc_info=True)
        raise


async def calculate_multi_zone_sizing(
    zip_code: str = Field(..., description="5-digit US ZIP code"),
    build_year: int = Field(..., description="Year home was built (1900-2025)", ge=1900, le=2025),
    zones: List[Dict[str, Any]] = Field(..., description="List of zone configurations"),
) -> Dict[str, Any]:
    """
    Calculate heating/cooling loads for a multi-zone home with detailed zone-by-zone analysis.

    Each zone should specify:
    - name: User-defined zone name
    - square_feet: Zone area (50-5000 sqft)
    - ceiling_height: Height in feet (7-20 ft, default 8)
    - zone_type: living_area, bedrooms, kitchen, basement, attic, garage, other
    - sun_exposure: north, south, east, west, minimal
    - window_coverage: Percentage of wall area as windows (0.0-0.5, default 0.15)
    - occupancy: high, medium, low
    - heat_sources: List like ["kitchen_appliances", "electronics", "home_office"]
    - air_sealing: tight, average, leaky
    - is_above_grade: True if above ground level

    Returns:
        Dictionary with:
        - total_cooling_load/total_heating_load: Total BTU requirements
        - zone_results: Detailed results for each zone
        - system_options: Recommended multi-zone configurations
        - climate_info: Location-specific climate data
        - recommendations: Installation and design recommendations
    """
    try:
        logger.info(
            f"Multi-zone calculation: {len(zones)} zones, ZIP {zip_code}, built {build_year}"
        )

        result = multi_zone_service.calculate_multi_zone(
            zip_code=zip_code,
            build_year=build_year,
            zones=zones,
        )

        return result.model_dump()
    except Exception as e:
        logger.error(f"Multi-zone calculation failed: {str(e)}", exc_info=True)
        raise


async def estimate_energy_costs(
    zip_code: str = Field(..., description="5-digit US ZIP code"),
    square_feet: int = Field(..., description="Home square footage (100-10000)", ge=100, le=10000),
    build_year: int = Field(..., description="Year home was built (1900-2025)", ge=1900, le=2025),
    heat_pump_model: str = Field(..., description="Selected heat pump model name"),
    gas_price_per_therm: Optional[float] = Field(
        None, description="Local gas price per therm ($)", ge=0, le=10
    ),
    electricity_rate_override: Optional[float] = Field(
        None, description="Manual electricity rate ($/kWh)", ge=0, le=1
    ),
    current_heating_fuel: str = Field(
        "gas", description="Current heating fuel: gas, oil, propane, electric"
    ),
) -> Dict[str, Any]:
    """
    Estimate annual electricity costs and payback period for heat pump vs current heating system.

    Analyzes:
    - Monthly heating load based on location and home characteristics
    - Heat pump electricity consumption using model's efficiency (HSPF2)
    - Comparison with current heating fuel costs
    - 10-year cost projection with savings analysis
    - Break-even year calculation

    Returns:
        Dictionary with:
        - location_info: Climate and location details
        - electricity_rate: Rate used for calculations ($/kWh)
        - gas_rate: Comparison fuel rate if applicable
        - heat_pump_info: Selected model specifications
        - monthly_breakdown: Month-by-month cost comparison
        - annual_summary: Annual totals and payback analysis
        - ten_year_projection: Long-term savings projection
        - calculation_notes: Important assumptions and notes
    """
    try:
        logger.info(f"Cost estimation: {heat_pump_model}, ZIP {zip_code}, {square_feet} sqft")

        result = await bill_estimator_service.calculate_costs(
            zip_code=zip_code,
            square_feet=square_feet,
            build_year=build_year,
            heat_pump_model=heat_pump_model,
            gas_price_per_therm=gas_price_per_therm,
            electricity_rate_override=electricity_rate_override,
            current_heating_fuel=current_heating_fuel,
        )

        return result.model_dump()
    except Exception as e:
        logger.error(f"Cost estimation failed: {str(e)}", exc_info=True)
        raise


async def check_cold_climate_performance(
    zip_code: str = Field(..., description="5-digit US ZIP code"),
    square_feet: int = Field(..., description="Home square footage (100-10000)", ge=100, le=10000),
    build_year: int = Field(..., description="Year home was built (1900-2025)", ge=1900, le=2025),
    heat_pump_model: str = Field(..., description="Heat pump model to analyze"),
    existing_backup_heat: Optional[str] = Field(
        None, description="Existing backup: electric_strip, gas_furnace, oil_boiler, none"
    ),
) -> Dict[str, Any]:
    """
    Verify heat pump performance at design temperature and determine backup heat requirements.

    Analyzes:
    - Heat pump capacity at design temperature (coldest expected outdoor temp)
    - Percentage of heating load covered by heat pump alone
    - Required backup heat capacity to cover shortfall
    - Temperature range where heat pump provides full heating
    - COP (efficiency) across temperature range

    Critical for cold-climate installations to ensure adequate heating on coldest days.

    Returns:
        Dictionary with:
        - location_info: Climate zone and design conditions
        - heat_pump_model: Selected model name
        - capacity_curve: Heat pump capacity at various outdoor temperatures
        - performance_analysis: Coverage at design temp, backup heat needed
        - backup_heat_recommendation: Recommended backup system if needed
        - temperature_range_analysis: Performance across temperature ranges
        - key_findings: Important observations
        - warnings: Critical issues or limitations
    """
    try:
        from .models.cold_climate import ColdClimateInput, BackupHeatType

        logger.info(f"Cold climate check: {heat_pump_model}, ZIP {zip_code}, {square_feet} sqft")

        # Convert string backup heat to enum if provided
        backup_heat_enum = None
        if existing_backup_heat:
            backup_heat_enum = BackupHeatType(existing_backup_heat)

        # Create Pydantic model instance
        input_data = ColdClimateInput(
            zip_code=zip_code,
            square_feet=square_feet,
            build_year=build_year,
            heat_pump_model=heat_pump_model,
            existing_backup_heat=backup_heat_enum,
        )

        result = cold_climate_service.analyze_cold_climate_performance(input_data)

        return result.model_dump()
    except Exception as e:
        logger.error(f"Cold climate analysis failed: {str(e)}", exc_info=True)
        raise


async def get_electricity_rate(
    zip_code: str = Field(..., description="5-digit US ZIP code"),
) -> Dict[str, Any]:
    """
    Get the current electricity rate for a specific ZIP code location.

    Fetches residential electricity rates from EIA (Energy Information Administration) API.
    Requires EIA_API_KEY environment variable to be set.

    Returns:
        Dictionary with:
        - zip_code: Input ZIP code
        - electricity_rate: Rate in $/kWh
        - unit: Always "$/kWh"
        - source: Data source information
    """
    try:
        logger.info(f"Fetching electricity rate for ZIP {zip_code}")

        rate = await electricity_rate_service.get_rate_by_zip(zip_code)

        if rate is None:
            raise ValueError(f"Unable to determine electricity rate for ZIP {zip_code}")

        return {
            "zip_code": zip_code,
            "electricity_rate": rate,
            "unit": "$/kWh",
            "source": "EIA (Energy Information Administration)",
        }
    except Exception as e:
        logger.error(f"Electricity rate lookup failed: {str(e)}", exc_info=True)
        raise


async def list_heat_pump_models(
    brand: Optional[str] = Field(None, description="Filter by brand name"),
    min_btu: Optional[int] = Field(None, description="Minimum BTU capacity"),
    max_btu: Optional[int] = Field(None, description="Maximum BTU capacity"),
    min_hspf2: Optional[float] = Field(None, description="Minimum HSPF2 efficiency rating"),
) -> Dict[str, Any]:
    """
    List available heat pump models, optionally filtered by brand, capacity, or efficiency.

    Returns comprehensive database of heat pump models with:
    - Brand and model name
    - BTU capacity (heating/cooling)
    - HSPF2 efficiency rating (higher is more efficient)
    - Estimated price range

    Filters:
    - brand: Case-insensitive partial match (e.g., "Mitsubishi", "Fujitsu")
    - min_btu/max_btu: Capacity range for sizing
    - min_hspf2: Minimum efficiency threshold (typical range: 8.0-12.0)

    Returns:
        Dictionary with:
        - total_models: Count of models matching filters
        - brands: List of available brands
        - models: List of model details
    """
    try:
        logger.info(
            f"Listing heat pump models: brand={brand}, BTU={min_btu}-{max_btu}, HSPF2>={min_hspf2}"
        )

        all_models = heat_pump_models_service.get_all_models()

        # Apply filters
        filtered_models = all_models

        if brand:
            filtered_models = [m for m in filtered_models if brand.lower() in m["brand"].lower()]

        if min_btu is not None:
            filtered_models = [m for m in filtered_models if m["btu_capacity"] >= min_btu]

        if max_btu is not None:
            filtered_models = [m for m in filtered_models if m["btu_capacity"] <= max_btu]

        if min_hspf2 is not None:
            filtered_models = [m for m in filtered_models if m["hspf2"] >= min_hspf2]

        # Get unique brands from filtered results
        brands = sorted(list(set(m["brand"] for m in filtered_models)))

        return {"total_models": len(filtered_models), "brands": brands, "models": filtered_models}
    except Exception as e:
        logger.error(f"Model listing failed: {str(e)}", exc_info=True)
        raise
