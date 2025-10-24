"""Configuration for HeatPump MCP Server."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    # API Keys (optional - fetched on-demand or use bundled data)
    eia_api_key: Optional[str] = None
    nrel_api_key: Optional[str] = None

    # Data paths
    data_dir: Path = Path(__file__).parent.parent.parent.parent / "data"

    # Caching (local file system)
    enable_local_cache: bool = True
    cache_dir: Path = Path.home() / ".heatpump_mcp_server" / "cache"

    # Logging
    log_level: str = "INFO"


# Global settings instance
settings = Settings()

# Ensure cache directory exists if caching is enabled
if settings.enable_local_cache:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
