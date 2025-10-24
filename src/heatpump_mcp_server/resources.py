"""MCP resources for heat pump data access."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Import services
from .services.design_temp_service import design_temp_service
from .services.heat_pump_models_service import heat_pump_models_service


async def get_design_temp_resource(zip_code: str) -> str:
    """
    Get design temperature and climate data for a ZIP code.

    Resource URI: design-temps/{zip_code}
    """
    try:
        data = design_temp_service.get_design_temp(zip_code)

        # Format as readable text
        result = f"""# Design Temperature Data for ZIP {zip_code}

**Location**: {data["city"]}, {data["state"]}
**Climate Zone**: {data["climate_zone"]}
**Heating Design Temperature (99%)**: {data["design_temp"]}°F
**Cooling Design Temperature (1%)**: {data.get("cooling_design_temp", "N/A")}°F
**Heating Degree Days**: {data.get("heating_degree_days", "N/A")}
**Cooling Degree Days**: {data.get("cooling_degree_days", "N/A")}

{"*Note: Using data from nearby station*" if data.get("approximate") else ""}
"""
        return result
    except Exception as e:
        logger.error(f"Failed to get design temp resource: {str(e)}")
        raise


async def get_heat_pump_models_resource() -> str:
    """
    Get catalog of available heat pump models.

    Resource URI: heat-pump-models
    """
    try:
        models_by_brand = heat_pump_models_service.get_models_by_brand()
        brands = heat_pump_models_service.get_brands()

        # Format as readable text
        result = f"""# Heat Pump Models Database

**Total Models**: {len(heat_pump_models_service.get_all_models())}
**Brands**: {len(brands)}

"""
        for brand in brands:
            models = models_by_brand[brand]
            result += f"\n## {brand} ({len(models)} models)\n\n"

            for model in models:
                result += f"- **{model['model']}**: {model['btu_capacity']:,} BTU, HSPF2 {model['hspf2']}, {model['price_range']}\n"

        return result
    except Exception as e:
        logger.error(f"Failed to get heat pump models resource: {str(e)}")
        raise


async def get_climate_zones_resource() -> str:
    """
    Get information about ASHRAE climate zones.

    Resource URI: climate-zones
    """
    return """# ASHRAE Climate Zones

Climate zones used for heating and cooling load calculations:

## Zone 1: Very Hot
- **1A**: Very Hot - Humid (Miami, Houston)
- **1B**: Very Hot - Dry (Phoenix, Las Vegas)

## Zone 2: Hot
- **2A**: Hot - Humid (Atlanta, New Orleans)
- **2B**: Hot - Dry (Tucson, El Paso)

## Zone 3: Warm
- **3A**: Warm - Humid (Memphis, Birmingham)
- **3B**: Warm - Dry (Los Angeles, San Diego)
- **3C**: Warm - Marine (San Francisco)

## Zone 4: Mixed
- **4A**: Mixed - Humid (New York, Philadelphia, Washington DC)
- **4B**: Mixed - Dry (Albuquerque, Salt Lake City)
- **4C**: Mixed - Marine (Seattle, Portland)

## Zone 5: Cool
- **5A**: Cool - Humid (Chicago, Boston, Detroit)
- **5B**: Cool - Dry (Denver, Helena)

## Zone 6: Cold
- **6A**: Cold - Humid (Minneapolis, Burlington VT)
- **6B**: Cold - Dry (Great Falls MT)

## Zone 7: Very Cold
- **7**: Very Cold (Duluth MN, Fargo ND)

## Zone 8: Subarctic
- **8**: Subarctic (Fairbanks AK)

**Note**: Climate zones determine heating/cooling loads, design temperatures, and equipment sizing requirements.
"""
