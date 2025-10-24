"""MCP prompts for guided heat pump calculations."""

import logging

logger = logging.getLogger(__name__)


async def size_heat_pump_prompt() -> str:
    """
    Guide user through heat pump sizing process.

    Prompt name: size-heat-pump
    """
    return """# Heat Pump Sizing Guide

I'll help you determine the right size heat pump for your home. I need some basic information:

## Required Information:
1. **ZIP Code**: Your 5-digit US ZIP code (for climate data)
2. **Square Footage**: Total conditioned space in your home (100-10,000 sq ft)
3. **Build Year**: When was your home built? (1900-2025)

## Optional Considerations:
4. **Humidity Concerns**: Does your home have humidity issues?
   - Basement moisture problems
   - Poor bathroom ventilation
   - General high humidity levels

## What I'll Calculate:
- Required BTU capacity for heating
- Recommended BTU range for equipment selection
- Climate zone and design temperature for your location
- Specific heat pump model recommendations
- Warnings about potential oversizing issues
- Humidity control recommendations (if applicable)

## Next Steps:
Once I calculate your sizing, I can also help you with:
- **Energy Cost Estimates**: Compare heat pump vs your current heating system
- **Cold Climate Analysis**: Verify performance in extreme cold
- **Multi-Zone Sizing**: If you need room-by-room calculations

**Ready to start?** Please provide your ZIP code, square footage, and build year.
"""


async def analyze_costs_prompt() -> str:
    """
    Guide user through cost and payback analysis.

    Prompt name: analyze-costs
    """
    return """# Heat Pump Cost & Payback Analysis

I'll help you understand the financial implications of switching to a heat pump.

## Required Information:
1. **ZIP Code**: Your 5-digit US ZIP code
2. **Square Footage**: Total conditioned space (100-10,000 sq ft)
3. **Build Year**: When was your home built?
4. **Heat Pump Model**: Which model are you considering?
   - Use `list_heat_pump_models` tool to see available options
   - Or provide a specific brand and model

## Optional Information:
5. **Current Heating Fuel**: What do you currently use?
   - Natural gas (default)
   - Oil
   - Propane
   - Electric resistance

6. **Local Fuel Prices** (optional but improves accuracy):
   - Gas price per therm
   - Electricity rate per kWh (we can look this up for you)

## What I'll Analyze:
- Monthly heating costs with heat pump vs current system
- Annual savings estimate
- 10-year cost projection
- Payback period (break-even year)
- Total savings over 10 years

## Additional Considerations:
The analysis includes:
- Location-specific electricity rates
- Climate-adjusted heating loads
- Heat pump efficiency (HSPF2) ratings
- Seasonal performance variations

**Ready?** Let me know your home details and which heat pump model interests you!
"""


async def verify_cold_climate_prompt() -> str:
    """
    Guide user through cold climate performance verification.

    Prompt name: verify-cold-climate
    """
    return """# Cold Climate Heat Pump Verification

I'll help you verify if a heat pump will provide adequate heating in your climate.

## Why This Matters:
Heat pumps lose capacity as outdoor temperature drops. In cold climates, you need to ensure:
1. The heat pump can meet your heating needs at design temperature
2. You have adequate backup heat if needed
3. The system won't over-rely on expensive backup heat

## Required Information:
1. **ZIP Code**: Your 5-digit US ZIP code
2. **Square Footage**: Total conditioned space (100-10,000 sq ft)
3. **Build Year**: When was your home built?
4. **Heat Pump Model**: Which model are you considering?

## Optional Information:
5. **Existing Backup Heat**: Do you have backup heating?
   - Electric resistance strips
   - Gas furnace
   - Oil boiler
   - None

## What I'll Analyze:
- Design temperature for your location (coldest expected day)
- Heat pump capacity at design temperature
- Percentage of heating load covered by heat pump alone
- Required backup heat capacity (if any)
- Temperature ranges where heat pump provides full heating
- COP (efficiency) across temperature range

## Performance Ratings:
- **Excellent**: Heat pump covers 100%+ of load at design temp
- **Good**: Covers 80-100% (minimal backup needed)
- **Marginal**: Covers 60-80% (moderate backup usage)
- **Inadequate**: Covers <60% (heavy backup reliance)

## Recommendations:
Based on the analysis, I'll suggest:
- Whether the model is appropriate for your climate
- If you need backup heat and what type
- Installation considerations for cold climate operation

**Ready?** Provide your location details and the heat pump model you're considering.
"""
