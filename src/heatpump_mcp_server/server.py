"""Main MCP server implementation for HeatPumpHQ calculators."""

import logging
from typing import Optional
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP("HeatPumpHQ Calculator")

# Import tools and resources
from .tools import (
    calculate_heat_pump_sizing,
    calculate_multi_zone_sizing,
    estimate_energy_costs,
    check_cold_climate_performance,
    get_electricity_rate,
    list_heat_pump_models,
)

from .resources import (
    get_design_temp_resource,
    get_heat_pump_models_resource,
    get_climate_zones_resource,
)

from .prompts import (
    size_heat_pump_prompt,
    analyze_costs_prompt,
    verify_cold_climate_prompt,
)

# Register tools
mcp.tool()(calculate_heat_pump_sizing)
mcp.tool()(calculate_multi_zone_sizing)
mcp.tool()(estimate_energy_costs)
mcp.tool()(check_cold_climate_performance)
mcp.tool()(get_electricity_rate)
mcp.tool()(list_heat_pump_models)

# Register resources
mcp.resource("resource://design-temps/{zip_code}")(get_design_temp_resource)
mcp.resource("resource://heat-pump-models")(get_heat_pump_models_resource)
mcp.resource("resource://climate-zones")(get_climate_zones_resource)

# Register prompts
mcp.prompt()(size_heat_pump_prompt)
mcp.prompt()(analyze_costs_prompt)
mcp.prompt()(verify_cold_climate_prompt)


def main():
    """Entry point for the MCP server."""
    logger.info("Starting HeatPumpHQ MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
