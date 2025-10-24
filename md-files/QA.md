# Manual Testing Guide for HeatPump MCP Server

This guide outlines how to manually test the HeatPump MCP Server by actually using it through MCP clients (not automated code testing).

## Prerequisites

Before testing, ensure you have:
- Claude Desktop, Claude Code, or another MCP-compatible client installed
- The MCP server configured in your client's configuration file
- Optional: EIA API key for live electricity rate testing

## Configuration Setup

### Option 1: Install from GitHub (Recommended for Testing Latest)

Add to your MCP client configuration (e.g., `~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": [
        "--refresh",
        "--from",
        "git+https://github.com/subspace-lab/heatpump-mcp-server.git",
        "heatpump-mcp-server"
      ]
    }
  }
}
```

### Option 2: Install from Local Development Directory

For testing local changes before pushing:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": [
        "--from",
        "/Users/weiqi/Documents/projects/HeatPumpHQ/heatpump_mcp_server",
        "heatpump-mcp-server"
      ]
    }
  }
}
```

### Option 3: Direct Python Execution

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "python",
      "args": [
        "-m",
        "heatpump_mcp_server.server"
      ],
      "cwd": "/Users/weiqi/Documents/projects/HeatPumpHQ/heatpump_mcp_server"
    }
  }
}
```

### Verify Server Connection

1. Restart your MCP client after updating configuration
2. Open a new conversation
3. Check that the MCP server appears in the connected servers list
4. Verify available tools are listed (should see 6 tools)

## Test Plan

### Test 1: Quick Single-Zone Sizing

**Objective**: Verify basic BTU calculation functionality works end-to-end.

**Test Cases**:

1. **Warm Climate (Zone 2A - Houston)**
   - Prompt: "I need to size a heat pump for my 1500 sq ft home in ZIP 77001, built in 2010"
   - Expected: ~18,000-24,000 BTU recommendation
   - Verify: Design temp ~22°F, climate zone 2A, multiple model recommendations

2. **Cold Climate (Zone 6A - Boston)**
   - Prompt: "Size a heat pump for 2000 sq ft in ZIP 02101, built in 1985"
   - Expected: ~36,000-48,000 BTU (higher due to old construction + cold climate)
   - Verify: Design temp ~9°F, climate zone 6A, cold climate warnings

3. **Very Cold Climate (Zone 7 - Minneapolis)**
   - Prompt: "What size heat pump for 1800 sq ft in 55401, built in 2018?"
   - Expected: ~28,000-36,000 BTU
   - Verify: Design temp below 0°F, backup heat recommendations

4. **With Humidity Concerns**
   - Prompt: "Size heat pump for 2200 sq ft in 33109 (Miami), built 2015, high humidity issues"
   - Expected: Oversized by 10-15% for dehumidification
   - Verify: Humidity recommendations included

**Pass Criteria**:
- Returns BTU recommendations within expected ranges
- Includes climate zone and design temperature
- Lists 3-5 suitable heat pump models
- Provides calculation notes explaining methodology

---

### Test 2: Heat Pump Model Database

**Objective**: Verify model database filtering and browsing works correctly.

**Test Cases**:

1. **List All Models**
   - Prompt: "Show me all available heat pump models"
   - Expected: 81 models listed with brand, BTU, HSPF2, price
   - Verify: Includes Mitsubishi, Fujitsu, Daikin, etc.

2. **Filter by Brand**
   - Prompt: "Show me Mitsubishi heat pump models"
   - Expected: Only Mitsubishi models returned
   - Verify: Case-insensitive matching works

3. **Filter by BTU Range**
   - Prompt: "What heat pumps are available between 18,000 and 24,000 BTU?"
   - Expected: Models in that capacity range
   - Verify: Both min and max BTU filters work

4. **Filter by Efficiency**
   - Prompt: "Show me heat pumps with HSPF2 rating above 10"
   - Expected: Only high-efficiency models
   - Verify: Efficiency threshold filtering works

5. **Combined Filters**
   - Prompt: "Show Fujitsu models with 12,000 BTU and HSPF2 above 9"
   - Expected: Specific filtered subset
   - Verify: Multiple filters work together

**Pass Criteria**:
- Correct number of models returned
- All returned models match filter criteria
- Model details include all required fields
- Brands list shows available manufacturers

---

### Test 3: Energy Cost Estimation & Payback

**Objective**: Verify bill comparison and ROI calculations are realistic.

**Test Cases**:

1. **Basic Payback Calculation (Gas vs Heat Pump)**
   - Prompt: "Compare energy costs: 1500 sq ft in 60601 (Chicago), built 2005, currently gas heat, considering Mitsubishi MSZ-FH15NA"
   - Expected: Monthly breakdown, annual totals, payback period
   - Verify: Gas costs, electricity costs, savings calculated

2. **Cold Climate with High Electricity Rates**
   - Prompt: "Energy costs for 2000 sq ft in 02101 (Boston), built 1990, gas furnace, looking at Fujitsu AOU24RLXFZH"
   - Expected: May show longer payback due to cold climate + high electricity
   - Verify: Realistic COP degradation in winter months

3. **Warm Climate Advantage**
   - Prompt: "Bill comparison for 1800 sq ft in 85001 (Phoenix), built 2015, gas heat, Daikin DZ18SA"
   - Expected: Shorter payback, lower heating costs overall
   - Verify: Minimal heating load in warm climate

4. **Custom Utility Rates**
   - Prompt: "Energy costs in 98101 (Seattle), 1600 sq ft, built 2010, Mitsubishi MUZ-FH09NA, electricity is $0.12/kWh, gas is $1.50/therm"
   - Expected: Uses provided rates instead of defaults
   - Verify: Override rates are applied correctly

5. **10-Year Projection**
   - Prompt: "Long-term savings for heat pump vs gas furnace over 10 years in ZIP 30301"
   - Expected: Year-by-year costs, cumulative savings
   - Verify: Accounts for efficiency over time

**Pass Criteria**:
- Monthly breakdown shows realistic heating loads
- Electricity costs match local rates (or defaults)
- Payback period is calculated correctly
- 10-year projection shows cumulative savings
- Calculation notes explain assumptions

---

### Test 4: Cold Climate Performance Verification

**Objective**: Verify heat pump capacity derating and backup heat calculations.

**Test Cases**:

1. **Adequate Coverage (No Backup Needed)**
   - Prompt: "Will Mitsubishi MUZ-FH15NA work in 40202 (Louisville) for 1200 sq ft, built 2010?"
   - Expected: 100% coverage at design temp, no backup required
   - Verify: Capacity curve shows sufficient BTU at design temp

2. **Backup Heat Required (Very Cold Climate)**
   - Prompt: "Check if Fujitsu AOU12RLXFZH can heat 1500 sq ft in 55401 (Minneapolis), built 2000"
   - Expected: Coverage drops below 100% at design temp, backup heat recommended
   - Verify: Calculates backup heat BTU needed

3. **Marginal Performance**
   - Prompt: "Verify Daikin DZ24SA for 2000 sq ft in 60601 (Chicago), built 1985"
   - Expected: May need backup for old, leaky home in cold climate
   - Verify: Shows temperature range where heat pump covers 100%

4. **With Existing Backup System**
   - Prompt: "I have electric strip backup. Check Mitsubishi SVZ-KP30NA for 2500 sq ft in 02101, built 1995"
   - Expected: Evaluates if existing backup is sufficient
   - Verify: Accounts for existing backup heat

5. **Extreme Cold (Zone 7-8)**
   - Prompt: "Will Fujitsu AOU18RLXFZH work in Fairbanks, AK (99701) for 1800 sq ft?"
   - Expected: Severe derating warnings, significant backup heat needed
   - Verify: Shows capacity at -20°F to -40°F

**Pass Criteria**:
- Capacity curve shows BTU at multiple outdoor temperatures
- Design temperature performance clearly stated
- Backup heat recommendations are specific (BTU amount)
- Warnings for oversizing or undersizing
- Temperature range where 100% coverage occurs

---

### Test 5: Multi-Zone Calculations

**Objective**: Verify floor-by-floor load calculations for complex homes.

**Test Cases**:

1. **Simple Two-Zone Home**
   - Prompt: "Multi-zone sizing for ZIP 90001, built 2010:
     - Zone 1: Living area, 1000 sq ft, south exposure, 15% windows, medium occupancy
     - Zone 2: Bedrooms, 800 sq ft, north exposure, 10% windows, low occupancy"
   - Expected: Individual zone loads + total system recommendation
   - Verify: Different loads per zone based on exposure

2. **Complex Home with Basement**
   - Prompt: "Calculate multi-zone loads for 60601, built 1990:
     - Main floor: 1200 sq ft, living area, west exposure, high occupancy, leaky air sealing
     - Upper floor: 1000 sq ft, bedrooms, east exposure, low occupancy, average sealing
     - Basement: 800 sq ft, below grade, minimal windows, home office"
   - Expected: Lower basement load (ground contact), higher main floor
   - Verify: Below-grade zone has reduced load

3. **High Heat Gain Zone (Kitchen)**
   - Prompt: "Multi-zone for 33109 (Miami), built 2015:
     - Kitchen: 400 sq ft, south exposure, kitchen appliances heat source
     - Living: 1000 sq ft, north exposure, electronics
     - Bedrooms: 800 sq ft, east exposure, minimal heat sources"
   - Expected: Kitchen has higher cooling load than heating
   - Verify: Heat sources increase cooling requirements

4. **Tight vs Leaky Zones**
   - Prompt: "Multi-zone for 02101, built mix:
     - New addition: 600 sq ft, tight air sealing, 2020 construction
     - Original house: 1400 sq ft, leaky, 1950 construction"
   - Expected: Leaky zone has significantly higher load
   - Verify: Air sealing quality impacts calculations

5. **Variable Ceiling Heights**
   - Prompt: "Calculate loads for 98101, built 2018:
     - Living room: 800 sq ft, 12 ft ceilings, high windows
     - Bedrooms: 1200 sq ft, 8 ft ceilings, normal windows"
   - Expected: Higher load for high-ceiling room
   - Verify: Ceiling height affects volume calculations

**Pass Criteria**:
- Individual zone loads calculated correctly
- Total heating/cooling loads aggregated
- Multi-zone system configurations recommended
- Climate info and design temp included
- Recommendations consider zone diversity

---

### Test 6: Electricity Rate Lookups

**Objective**: Verify electricity rate fetching (API or fallback).

**Test Cases**:

1. **With EIA API Key (If Available)**
   - Prompt: "What's the electricity rate in ZIP 02101?"
   - Expected: Live rate from EIA API
   - Verify: Shows source as "EIA API"

2. **Without API Key (Fallback to State Averages)**
   - Prompt: "Get electricity rate for 90001 (California)"
   - Expected: State average rate (~$0.25/kWh for CA)
   - Verify: Shows source as "State Average (2024)"

3. **Different States**
   - Test multiple ZIPs: 10001 (NY), 77001 (TX), 98101 (WA), 33109 (FL)
   - Expected: Different rates per state
   - Verify: Rates match known state averages

**Pass Criteria**:
- Returns rate in $/kWh
- Indicates data source (API vs state average)
- Falls back gracefully when API unavailable
- Rates are realistic (0.08-0.35 $/kWh range)

---

### Test 7: Error Handling & Edge Cases

**Objective**: Verify graceful handling of invalid inputs.

**Test Cases**:

1. **Invalid ZIP Code**
   - Prompt: "Size heat pump for ZIP 00000"
   - Expected: Error message about invalid ZIP
   - Verify: Clear error message, no crash

2. **Extreme Square Footage**
   - Prompt: "Size for 50,000 sq ft" or "Size for 50 sq ft"
   - Expected: Out-of-range error or warning
   - Verify: Validates input ranges

3. **Invalid Build Year**
   - Prompt: "Built in 1850" or "Built in 2030"
   - Expected: Error or boundary handling
   - Verify: Year validation works

4. **Non-Existent Model Name**
   - Prompt: "Energy costs for model XYZ-FAKE-123"
   - Expected: Error about model not found
   - Verify: Lists available models or suggests alternatives

5. **Missing Required Parameters**
   - Prompt: "Size a heat pump" (no ZIP, sqft, or year)
   - Expected: Requests missing information
   - Verify: MCP client or server prompts for required data

**Pass Criteria**:
- Errors are descriptive and actionable
- No server crashes or unhandled exceptions
- Invalid data is rejected with clear messages
- Suggestions provided when applicable

---

### Test 8: Resources & Prompts

**Objective**: Verify MCP resources and guided prompts work.

**Test Cases**:

1. **Access Design Temperature Resource**
   - In MCP client: Access resource `design-temps/60601`
   - Expected: Climate data and design temp for Chicago
   - Verify: JSON data with climate zone, design temps, location

2. **Access Heat Pump Models Resource**
   - In MCP client: Access resource `heat-pump-models`
   - Expected: Full database of 81 models
   - Verify: JSON array with all model specifications

3. **Access Climate Zones Resource**
   - In MCP client: Access resource `climate-zones`
   - Expected: ASHRAE climate zone reference data
   - Verify: Zone definitions and characteristics

4. **Use "Size Heat Pump" Prompt**
   - In MCP client: Invoke prompt `size-heat-pump`
   - Expected: Step-by-step guided sizing workflow
   - Verify: Prompts for ZIP, sqft, build year, then calculates

5. **Use "Analyze Costs" Prompt**
   - In MCP client: Invoke prompt `analyze-costs`
   - Expected: Guided cost comparison workflow
   - Verify: Walks through model selection and comparison

6. **Use "Verify Cold Climate" Prompt**
   - In MCP client: Invoke prompt `verify-cold-climate`
   - Expected: Cold climate suitability check workflow
   - Verify: Guides through capacity verification

**Pass Criteria**:
- Resources return valid JSON data
- Resources contain expected data structure
- Prompts guide user through workflows
- Prompts call appropriate tools in sequence

---

## Integration Testing

### Test 9: End-to-End User Journeys

**Objective**: Simulate realistic user workflows from start to finish.

**Scenario 1: New Homeowner Sizing a System**
1. "I just bought a 1950 sq ft home in Boston (02101), built in 1978. Help me size a heat pump."
2. [Server recommends BTU range]
3. "What Mitsubishi models fit that range?"
4. [Server lists models]
5. "Compare energy costs for the Mitsubishi MUZ-FH18NA vs my current gas furnace"
6. [Server shows payback]
7. "Will that model work in Boston winters?"
8. [Server verifies cold climate performance]

**Scenario 2: Multi-Zone Home**
1. "I need multi-zone for my home in ZIP 98101, built 2005"
2. [Prompts for zone details]
3. Provide zone details for 3 zones
4. [Server calculates loads per zone]
5. "What multi-zone systems can handle these loads?"
6. [Server recommends configurations]

**Scenario 3: High-Efficiency Comparison**
1. "Show me the most efficient heat pumps available"
2. [Filters by HSPF2 > 10]
3. "For 1800 sq ft in Denver (80201), built 2010, which is best value?"
4. [Size recommendation + cost analysis for top models]
5. "Compare 3 models side-by-side"
6. [Energy cost comparison for multiple models]

**Pass Criteria**:
- Workflows complete without errors
- Responses are coherent and build on previous context
- Data remains consistent across multiple tool calls
- User gets actionable recommendations

---

## Performance & Reliability Testing

### Test 10: Server Stability

**Test Cases**:

1. **Rapid Sequential Requests**
   - Make 10 sizing calculations in quick succession
   - Expected: All complete successfully without timeout
   - Verify: No memory leaks or performance degradation

2. **Large Multi-Zone Calculation**
   - Create home with 8-10 zones
   - Expected: Completes within reasonable time (<5 seconds)
   - Verify: All zones calculated correctly

3. **Server Restart Recovery**
   - Force restart MCP client
   - Make new request
   - Expected: Server reconnects and responds
   - Verify: No state corruption

**Pass Criteria**:
- Consistent response times (<2 seconds for simple queries)
- No crashes or timeouts
- Reliable reconnection after client restart

---

## Regression Testing Checklist

After any code changes, verify:

- [ ] All 6 tools are registered and callable
- [ ] Bundled data files load correctly (hpmodels.json, eeweather_stations.json)
- [ ] BTU calculations match expected ranges for test ZIPs
- [ ] Energy cost estimates are realistic
- [ ] Cold climate derating follows capacity curves
- [ ] Multi-zone aggregates individual loads correctly
- [ ] Resources are accessible via MCP client
- [ ] Prompts guide users through workflows
- [ ] Error messages are clear and actionable
- [ ] No unhandled exceptions in server logs

---

## Test Environment Variations

Test across different MCP clients to ensure compatibility:

1. **Claude Desktop (macOS)**
   - Primary target platform
   - Test all features

2. **Claude Code (VS Code Extension)**
   - Verify tools appear in tool palette
   - Test inline usage during coding

3. **Cursor IDE**
   - Test if available
   - Verify tool invocation works

4. **Other MCP Clients**
   - As available
   - Document any compatibility issues

---

## Known Limitations to Verify

During testing, confirm these known limitations are handled:

1. **ZIP Code Coverage**: Not all ZIPs have weather stations - verify fallback to nearest station
2. **Model Database**: 81 models as of 2024 - verify filtering doesn't break with updates
3. **Electricity Rates**: Without API key, uses 2024 state averages - verify fallback works
4. **Climate Zones**: Some ZIPs span multiple zones - verify reasonable assignment

---

## Bug Reporting Template

When issues are found during manual testing:

```markdown
**Issue**: [Brief description]

**Steps to Reproduce**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior**: [What should happen]

**Actual Behavior**: [What actually happened]

**Environment**:
- MCP Client: [Claude Desktop / Claude Code / Other]
- OS: [macOS / Windows / Linux]
- Server Version: [Git commit or release]

**Logs**: [Relevant error messages or logs]

**Screenshots**: [If applicable]
```

---

## Conclusion

This manual testing plan covers:
- Core functionality of all 6 tools
- Data access via resources
- Guided workflows via prompts
- Error handling and edge cases
- End-to-end user journeys
- Performance and stability

Execute tests systematically and document results to ensure the HeatPump MCP Server delivers reliable, accurate heat pump sizing and cost estimation to AI assistants and their users.
