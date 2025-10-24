# HeatPump MCP Server

A Model Context Protocol (MCP) server for residential heat pump sizing, cost estimation, and cold-climate performance verification. Use with AI assistants like Claude Desktop, Claude Code, Cursor, and other MCP clients.

**Works out-of-the-box with bundled data - no API keys required!**

## Quick Start

### 1. Installation

```bash
# Run directly (once published to PyPI)
uvx heatpump-mcp-server

# Or install permanently
uv pip install heatpump-mcp-server
```

### 2. Configure Your MCP Client

Choose your preferred AI assistant:

<details>
<summary><b>Claude Desktop</b> (Anthropic)</summary>

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["heatpump-mcp-server"]
    }
  }
}
```

Restart Claude Desktop.
</details>

<details>
<summary><b>Claude Code</b> (VS Code Extension)</summary>

Add to `.claude/mcp.json` in your workspace:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["heatpump-mcp-server"]
    }
  }
}
```

Restart VS Code.
</details>

<details>
<summary><b>Cursor</b> (AI Code Editor)</summary>

Add to Cursor's MCP settings (Settings > MCP):

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["heatpump-mcp-server"]
    }
  }
}
```

Restart Cursor.
</details>

<details>
<summary><b>Other MCP Clients</b></summary>

Any MCP-compatible client can use:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["heatpump-mcp-server"]
    }
  }
}
```

Or if installed locally:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uv",
      "args": ["run", "heatpump-mcp-server"]
    }
  }
}
```
</details>

### 3. Start Using

That's it! The server includes:
- 81 heat pump models from major manufacturers
- 2024 state-average electricity rates for all US states
- TMY3 weather station data for climate zones

No API keys needed to get started.

## Features

### 🔧 Tools (Calculators)
- **`calculate_heat_pump_sizing`**: Single-zone BTU sizing with humidity considerations
- **`calculate_multi_zone_sizing`**: Floor-by-floor load calculations for complex homes
- **`estimate_energy_costs`**: Bill comparison and 10-year payback analysis
- **`check_cold_climate_performance`**: Verify capacity at design temperature
- **`get_electricity_rate`**: Fetch current electricity rates by ZIP code
- **`list_heat_pump_models`**: Browse 81 heat pump models with specs

### 📚 Resources (Data Access)
- **`design-temps/{zip_code}`**: Climate data and design temperatures
- **`heat-pump-models`**: Complete model database with BTU, HSPF2, prices
- **`climate-zones`**: ASHRAE climate zone reference

### 💡 Prompts (Guided Workflows)
- **`size-heat-pump`**: Step-by-step sizing guidance
- **`analyze-costs`**: Cost comparison workflow
- **`verify-cold-climate`**: Cold climate suitability check

## Example Interactions

### Sizing a Heat Pump

```
User: I need help sizing a heat pump for my 2000 sq ft home built in 1995 in ZIP 02138.

AI: [Uses calculate_heat_pump_sizing tool]
Based on your location (Cambridge, MA - Climate Zone 5A) and home characteristics:
- Required BTU: 80,000 BTU
- Recommended range: 72,000 - 88,000 BTU
- Design temperature: 6°F
...
```

### Cost Analysis

```
User: What would a Mitsubishi MXZ-3C30NA cost to operate vs my gas furnace?

AI: [Uses estimate_energy_costs tool]
Annual cost comparison:
- Heat pump: $1,850/year (using bundled state average rate)
- Gas furnace: $2,400/year
- Annual savings: $550
- Payback period: 8.2 years
...
```

### Cold Climate Verification

```
User: Will a Fujitsu AOU24RLXFZ work in Minneapolis?

AI: [Uses check_cold_climate_performance tool]
Cold climate analysis:
- Design temp: -13°F
- Heat pump capacity at design: 18,000 BTU
- Your heating load: 75,000 BTU
- Coverage: 24% (Inadequate)
- Recommendation: You'll need substantial backup heat...
```

## Advanced Configuration

### Optional: Live Electricity Rate Data

For more accurate electricity rates, you can optionally provide an EIA API key:

1. Get a free EIA API key: https://www.eia.gov/opendata/register.php

2. Add to your MCP client config:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["heatpump-mcp-server"],
      "env": {
        "EIA_API_KEY": "your_eia_api_key_here"
      }
    }
  }
}
```

Or create a `.env` file in your working directory:

```bash
# Optional: For live electricity rate lookups
EIA_API_KEY=your_eia_api_key_here
```

**Note**: Without an API key, the server uses 2024 state-average electricity rates, which are generally accurate for cost estimates.

## Installation from Source

For development or customization:

```bash
git clone https://github.com/subspace-lab/heatpump-mcp-server.git
cd heatpump-mcp-server
uv pip install -e .
```

## Architecture

Built on [FastMCP](https://github.com/jlowin/fastmcp) for easy MCP server development.

### Data Sources
- **Heat Pump Models**: Bundled database of 81 models (Mitsubishi, Fujitsu, Daikin, LG, etc.)
- **Climate Data**: TMY3 weather station database with design temperatures
- **Electricity Rates**: Bundled 2024 state averages (EIA API optional for live data)

### Calculation Methods
- **Sizing**: Climate-zone specific BTU/sqft coefficients based on building age and insulation
- **Costs**: Monthly degree-day analysis with heat pump COP curves
- **Cold Climate**: Manufacturer capacity curves with temperature derating

## Development

### Setup Development Environment

```bash
# Clone repo
git clone https://github.com/subspace-lab/heatpump-mcp-server.git
cd heatpump-mcp-server

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
pytest

# Lint code
ruff check .
```

### Project Structure

```
heatpump_mcp_server/
├── src/heatpump_mcp_server/
│   ├── server.py          # Main MCP server
│   ├── tools.py           # Calculator tools
│   ├── resources.py       # Data resources
│   ├── prompts.py         # Guided prompts
│   ├── config.py          # Configuration
│   ├── models/            # Pydantic models
│   └── services/          # Business logic
│       ├── quick_sizer_service.py
│       ├── bill_estimator_service.py
│       ├── cold_climate_service.py
│       └── ...
├── data/                  # Bundled data files
│   ├── hpmodels.json      # 81 heat pump models
│   └── eeweather_stations.json  # Weather data
├── tests/
├── pyproject.toml
└── README.md
```

## Contributing

Contributions welcome! Areas for improvement:
- Additional heat pump models
- More weather stations for better coverage
- Manual J load calculation support
- International climate zone support

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Climate data from [EEWeather](https://github.com/openeemeter/eeweather)
- Heat pump specs compiled from manufacturer data
- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- Electricity rate fallbacks from [EIA](https://www.eia.gov)

## Support

- Issues: https://github.com/subspace-lab/heatpump-mcp-server/issues
- Discussions: https://github.com/subspace-lab/heatpump-mcp-server/discussions
