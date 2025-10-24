"""Service for looking up design temperatures and climate zones by ZIP code."""

import json
import math
import logging
from typing import Optional, Dict, List
from functools import lru_cache
from dataclasses import dataclass
from pathlib import Path

try:
    import pgeocode
    import pandas as pd
except ImportError:
    pgeocode = None
    pd = None


class ZipCodeValidationError(Exception):
    """Exception raised for invalid ZIP codes."""

    pass


logger = logging.getLogger(__name__)


@dataclass
class TMY3Station:
    """Weather station data."""

    id: str
    name: str
    state: str
    latitude: float
    longitude: float
    elevation: float
    climate_zone: str
    heating_design_temp_99: float
    cooling_design_temp_1: float
    heating_degree_days: int
    cooling_degree_days: int


class DesignTempService:
    """Service to get design temperatures and climate data for ZIP codes."""

    def __init__(self):
        self._stations: List[TMY3Station] = []
        self._zip_search = None
        self._load_eeweather_stations()
        self._init_zip_search()

    def _load_eeweather_stations(self):
        """Load weather stations from bundled JSON data."""
        try:
            # Path: services -> heatpump_mcp_server -> src -> heatpump_mcp_server (package root) -> data
            data_file = (
                Path(__file__).parent.parent.parent.parent / "data" / "eeweather_stations.json"
            )

            logger.info(f"Loading eeweather stations from: {data_file}")

            if not data_file.exists():
                logger.warning(f"Weather stations file not found: {data_file}")
                return

            with open(data_file, "r") as f:
                data = json.load(f)

            for station_data in data.get("stations", []):
                station = TMY3Station(
                    id=station_data["station_id"],
                    name=station_data["name"],
                    state=station_data["state"],
                    latitude=station_data["latitude"],
                    longitude=station_data["longitude"],
                    elevation=station_data["elevation"],
                    climate_zone=station_data["climate_zone"],
                    heating_design_temp_99=station_data["heating_design_temp_99"],
                    cooling_design_temp_1=station_data["cooling_design_temp_1"],
                    heating_degree_days=station_data["heating_degree_days"],
                    cooling_degree_days=station_data["cooling_degree_days"],
                )
                self._stations.append(station)

            logger.info(f"✅ Loaded {len(self._stations)} eeweather stations")

        except Exception as e:
            logger.error(f"❌ Failed to load eeweather stations: {str(e)}", exc_info=True)

    def _init_zip_search(self):
        """Initialize pgeocode for ZIP code lookups."""
        if pgeocode is None:
            logger.warning("pgeocode not available - ZIP code lookup will be limited")
            return

        try:
            self._zip_search = pgeocode.Nominatim("us")
            logger.info("✅ ZIP code lookup initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ZIP code lookup: {e}")
            self._zip_search = None

    @lru_cache(maxsize=1000)
    def get_design_temp(self, zip_code: str) -> Dict:
        """
        Get design temperature and climate data for a ZIP code.

        Returns dict with:
        - design_temp: 99% heating design temperature (°F)
        - climate_zone: ASHRAE climate zone
        - city: City name
        - state: State abbreviation
        - approximate: True if using nearby station
        """
        # Validate ZIP code format
        if not zip_code or len(zip_code) != 5 or not zip_code.isdigit():
            raise ZipCodeValidationError(f"Invalid ZIP code format: {zip_code}")

        # Get ZIP code location
        if self._zip_search is None:
            raise ZipCodeValidationError("ZIP code lookup not available - install pgeocode")

        try:
            location = self._zip_search.query_postal_code(zip_code)

            if pd.isna(location.latitude) or pd.isna(location.longitude):
                raise ZipCodeValidationError(f"ZIP code not found: {zip_code}")

            zip_lat = location.latitude
            zip_lon = location.longitude

            # Find nearest weather station
            nearest_station = self._find_nearest_station(zip_lat, zip_lon)

            if nearest_station is None:
                raise ZipCodeValidationError(f"No weather data available for ZIP code: {zip_code}")

            # Calculate distance to station
            distance_miles = self._haversine_distance(
                zip_lat, zip_lon, nearest_station.latitude, nearest_station.longitude
            )

            return {
                "design_temp": nearest_station.heating_design_temp_99,
                "climate_zone": nearest_station.climate_zone,
                "city": location.place_name
                if hasattr(location, "place_name")
                else nearest_station.name,
                "state": location.state_code
                if hasattr(location, "state_code")
                else nearest_station.state,
                "approximate": distance_miles > 30,
                "station_distance_miles": round(distance_miles, 1),
                "cooling_design_temp": nearest_station.cooling_design_temp_1,
                "heating_degree_days": nearest_station.heating_degree_days,
                "cooling_degree_days": nearest_station.cooling_degree_days,
            }

        except ZipCodeValidationError:
            raise
        except Exception as e:
            logger.error(f"❌ Error looking up ZIP code {zip_code}: {str(e)}", exc_info=True)
            raise ZipCodeValidationError(f"Failed to lookup ZIP code {zip_code}: {str(e)}")

    def _find_nearest_station(self, lat: float, lon: float) -> Optional[TMY3Station]:
        """Find the nearest weather station to given coordinates."""
        if not self._stations:
            return None

        min_distance = float("inf")
        nearest = None

        for station in self._stations:
            distance = self._haversine_distance(lat, lon, station.latitude, station.longitude)
            if distance < min_distance:
                min_distance = distance
                nearest = station

        return nearest

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance in miles between two lat/lon points."""
        R = 3959  # Earth radius in miles

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c


# Singleton instance
design_temp_service = DesignTempService()
