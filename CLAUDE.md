# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HeatPump MCP Server is a Model Context Protocol (MCP) server for residential heat pump sizing, cost estimation, and cold-climate performance verification. It exposes heat pump calculation tools to AI assistants like Claude Desktop, Claude Code, Cursor, and other MCP clients.

**Key Feature**: Works out-of-the-box with bundled data - no API keys required.

## Development Commands

### Package Management
```bash
# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Install from source
uv pip install -e .
```

### Running the Server
```bash
# Run server directly
python -m heatpump_mcp_server.server

# Or use the installed entry point
heatpump-mcp-server

# Using uvx (recommended for end users)
uvx --from . heatpump-mcp-server
```

### Code Quality
```bash
# Lint code
ruff check .

# Format code
ruff format .
```

### Testing
```bash
# Run tests (if test suite exists)
pytest

# Run tests with coverage
pytest --cov=heatpump_mcp_server
```

## Architecture

Built on [FastMCP](https://github.com/jlowin/fastmcp) for easy MCP server development.

### Core Components

1. **`server.py`**: Main MCP server that registers tools, resources, and prompts
2. **`tools.py`**: MCP tool definitions (the calculators exposed to AI assistants)
3. **`resources.py`**: MCP resources for data access (design temps, heat pump models, climate zones)
4. **`prompts.py`**: Guided prompts for common workflows
5. **`config.py`**: Configuration via pydantic-settings (loads from .env or environment)

### Service Layer Architecture

The project follows a **service-based architecture** where business logic is separated into domain-specific services:

- **`services/quick_sizer_service.py`**: Single-zone BTU sizing with climate-zone-specific coefficients
- **`services/multi_zone_service.py`**: Floor-by-floor load calculations
- **`services/bill_estimator_service.py`**: Energy cost comparison and payback analysis
- **`services/cold_climate_service.py`**: Heat pump capacity verification at design temperature
- **`services/electricity_rate_service.py`**: Electricity rate lookups (EIA API or bundled state averages)
- **`services/heat_pump_models_service.py`**: Heat pump model database access
- **`services/design_temp_service.py`**: Climate data and design temperature lookups
- **`services/capacity_curve_service.py`**: Heat pump capacity derating calculations

### Data Layer

All data is **bundled with the package** in `src/heatpump_mcp_server/data/`:

- **`hpmodels.json`**: 81 heat pump models with specs (BTU, HSPF2, prices)
- **`eeweather_stations.json`**: TMY3 weather station data with design temperatures

These files are included in the wheel distribution via `pyproject.toml` configuration.

### Models

Pydantic models in `models/` directory define request/response schemas:
- `quick_sizer.py`: Single-zone sizing inputs/outputs
- `multi_zone.py`: Multi-zone calculation schemas
- `bill_estimator.py`: Cost estimation schemas
- `cold_climate.py`: Cold climate analysis schemas
- `project_cost.py`: Project cost calculation schemas

## Key Technical Details

### BTU Calculation Method

The quick sizer uses **climate-zone-specific BTU/sqft coefficients** based on:
- **Climate zone** (ASHRAE zones 1A-8)
- **Build year** (categorized as old/medium/new for insulation quality)
- **Square footage** (with surface-area-to-volume ratio adjustments)
- **Optional humidity adjustments** (for moisture control needs)

Coefficients are hardcoded in `QuickSizerService.BTU_COEFFICIENTS` and range from 20-65 BTU/sqft.

### Data Access Pattern

Services load data from bundled JSON files using Python's `pkgutil.get_data()` or direct file reads. The data directory is configured in `config.py` and points to the package's installed data files.

### Environment Variables

Optional configuration via `.env` file or environment:

```bash
# Optional: For live electricity rate lookups (falls back to bundled state averages)
EIA_API_KEY=your_eia_api_key_here

# Optional: For future NREL API integration
NREL_API_KEY=your_nrel_api_key_here
```

Without API keys, the server uses bundled 2024 state-average electricity rates.

## Package Distribution

This package is designed to be installed via `uvx` for zero-installation usage:

```json
{
  "mcpServers": {
    "heatpump-calculator": {
      "command": "uvx",
      "args": ["--refresh", "--from", "git+https://github.com/subspace-lab/heatpump-mcp-server.git", "heatpump-mcp-server"]
    }
  }
}
```

The `--refresh` flag ensures users get the latest version on each run.

### Building and Publishing

```bash
# Build wheel
python -m build

# Check package contents
unzip -l dist/heatpump_mcp_server-*.whl

# Publish to PyPI (when ready)
python -m twine upload dist/*
```

**Important**: The `pyproject.toml` includes `[tool.hatch.build.targets.wheel.force-include]` to ensure data files are bundled in the distribution.

## MCP Server Structure

### Tools (Calculators)
- `calculate_heat_pump_sizing`: Single-zone BTU sizing
- `calculate_multi_zone_sizing`: Multi-zone load calculations
- `estimate_energy_costs`: Bill comparison and payback analysis
- `check_cold_climate_performance`: Capacity verification at design temp
- `get_electricity_rate`: Fetch electricity rates by ZIP
- `list_heat_pump_models`: Browse heat pump model database

### Resources (Data Access)
- `design-temps/{zip_code}`: Climate data and design temperatures
- `heat-pump-models`: Complete model database
- `climate-zones`: ASHRAE climate zone reference

### Prompts (Guided Workflows)
- `size-heat-pump`: Step-by-step sizing guidance
- `analyze-costs`: Cost comparison workflow
- `verify-cold-climate`: Cold climate suitability check

## Development Workflow

1. Make changes to service logic in `services/` directory
2. Test locally by running the server and connecting an MCP client
3. Run linting: `ruff check .`
4. Commit changes and push to GitHub
5. Users with `--refresh` in their config will automatically get updates

## Voice Input Notes

This project documentation acknowledges that users often interact via voice input, which may produce:
- Transcription typos or incorrect spellings
- Misinterpreted technical terms
- Incorrect file names or special names

When working with voice-transcribed requests, focus on understanding the overall intent rather than literal transcription accuracy.
