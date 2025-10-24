"""Service for fetching electricity rates by ZIP code or state."""

import httpx
import os
import json
import logging
from typing import Optional, Dict
from pathlib import Path
from datetime import datetime, timedelta

from ..config import settings

logger = logging.getLogger(__name__)


class ElectricityRateService:
    """Service to get electricity rates using EIA API or fallback data."""

    def __init__(self):
        self.api_key = settings.eia_api_key or os.getenv("EIA_API_KEY")
        self.base_url = "https://api.eia.gov/v2"

        # Fallback rates by state ($/kWh) - 2024 averages
        self.fallback_rates = {
            "AL": 0.134,
            "AK": 0.234,
            "AZ": 0.132,
            "AR": 0.117,
            "CA": 0.234,
            "CO": 0.135,
            "CT": 0.221,
            "DE": 0.147,
            "FL": 0.127,
            "GA": 0.125,
            "HI": 0.334,
            "ID": 0.106,
            "IL": 0.143,
            "IN": 0.138,
            "IA": 0.135,
            "KS": 0.141,
            "KY": 0.123,
            "LA": 0.104,
            "ME": 0.174,
            "MD": 0.145,
            "MA": 0.234,
            "MI": 0.169,
            "MN": 0.145,
            "MS": 0.123,
            "MO": 0.128,
            "MT": 0.118,
            "NE": 0.115,
            "NV": 0.127,
            "NH": 0.204,
            "NJ": 0.175,
            "NM": 0.141,
            "NY": 0.204,
            "NC": 0.124,
            "ND": 0.115,
            "OH": 0.133,
            "OK": 0.118,
            "OR": 0.119,
            "PA": 0.151,
            "RI": 0.236,
            "SC": 0.139,
            "SD": 0.129,
            "TN": 0.125,
            "TX": 0.137,
            "UT": 0.119,
            "VT": 0.183,
            "VA": 0.132,
            "WA": 0.104,
            "WV": 0.124,
            "WI": 0.154,
            "WY": 0.117,
        }

        # Simple local cache (in-memory)
        self._cache: Dict[str, tuple[float, datetime]] = {}
        self._cache_ttl_hours = 24

    async def get_rate_by_state(self, state_code: str) -> Optional[float]:
        """
        Get electricity rate for a state.

        Tries:
        1. Local in-memory cache
        2. EIA API (if API key available)
        3. Fallback rates
        """
        state_code = state_code.upper()

        # Check cache
        if state_code in self._cache:
            rate, timestamp = self._cache[state_code]
            if datetime.now() - timestamp < timedelta(hours=self._cache_ttl_hours):
                logger.debug(f"Using cached rate for {state_code}: ${rate:.3f}/kWh")
                return rate

        # Try EIA API if we have an API key
        if self.api_key:
            try:
                rate = await self._fetch_eia_rate(state_code)
                if rate:
                    self._cache[state_code] = (rate, datetime.now())
                    logger.info(f"Fetched EIA rate for {state_code}: ${rate:.3f}/kWh")
                    return rate
            except Exception as e:
                logger.warning(f"Failed to fetch EIA rate for {state_code}: {e}")
        else:
            logger.info("No EIA API key set - using fallback rates")

        # Use fallback rate
        fallback_rate = self.fallback_rates.get(state_code)
        if fallback_rate:
            self._cache[state_code] = (fallback_rate, datetime.now())
            logger.info(f"Using fallback rate for {state_code}: ${fallback_rate:.3f}/kWh")
            return fallback_rate

        # Default to national average if state not found
        default_rate = 0.16
        logger.warning(f"State {state_code} not found, using default: ${default_rate:.3f}/kWh")
        return default_rate

    async def get_rate_by_zip(self, zip_code: str) -> Optional[float]:
        """Get electricity rate for a ZIP code by converting to state first."""
        state_code = self._get_state_from_zip(zip_code)
        if state_code:
            return await self.get_rate_by_state(state_code)

        logger.warning(f"Could not determine state for ZIP {zip_code}")
        return None

    def _get_state_from_zip(self, zip_code: str) -> Optional[str]:
        """Convert ZIP code to state abbreviation using pgeocode."""
        try:
            import pgeocode

            nomi = pgeocode.Nominatim("us")
            location = nomi.query_postal_code(zip_code)

            if hasattr(location, "state_code") and location.state_code:
                return location.state_code
        except Exception as e:
            logger.warning(f"Failed to get state from ZIP {zip_code}: {e}")

        return None

    async def _fetch_eia_rate(self, state_code: str) -> Optional[float]:
        """Fetch current electricity rate from EIA API."""
        if not self.api_key:
            return None

        url = f"{self.base_url}/electricity/retail-sales/data/"
        params = {
            "api_key": self.api_key,
            "frequency": "annual",
            "data[0]": "price",
            "facets[sectorid][]": "RES",  # Residential
            "facets[stateid][]": state_code,
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": 1,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()

                data = response.json()

                if "response" in data and "data" in data["response"]:
                    rate_data = data["response"]["data"]
                    if rate_data and len(rate_data) > 0:
                        # EIA returns cents per kWh, convert to $/kWh
                        cents_per_kwh = float(rate_data[0]["price"])
                        dollars_per_kwh = cents_per_kwh / 100
                        return dollars_per_kwh

                logger.warning(f"No rate data found in EIA response for {state_code}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching EIA rate for {state_code}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching EIA rate for {state_code}: {e}")
            return None


# Singleton instance
electricity_rate_service = ElectricityRateService()
