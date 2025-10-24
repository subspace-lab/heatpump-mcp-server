# Development Status

## Current Status

Server is functional with 6 tools, 3 resources, 3 prompts. All core services ported from FastAPI backend.

## Testing with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "heatpump": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/heatpump_mcp_server", "heatpump-mcp-server"]
    }
  }
}
```

## Publishing to PyPI

```bash
uv build
uv publish --repository testpypi  # Test first
uv publish  # Production
```

## Known Limitations

- Only 2 bundled weather stations (uses pgeocode + nearest station for all ZIPs)
- Electricity rates use 2024 state averages without EIA API key
