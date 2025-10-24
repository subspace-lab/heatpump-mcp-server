from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from enum import Enum

class ZoneType(str, Enum):
    LIVING_AREA = "living_area"
    BEDROOMS = "bedrooms"
    KITCHEN = "kitchen"
    BASEMENT = "basement"
    ATTIC = "attic"
    GARAGE = "garage"
    OTHER = "other"

class SunExposure(str, Enum):
    NORTH = "north"
    SOUTH = "south" 
    EAST = "east"
    WEST = "west"
    MINIMAL = "minimal"

class OccupancyLevel(str, Enum):
    HIGH = "high"      # Living rooms, family rooms
    MEDIUM = "medium"  # Bedrooms, offices
    LOW = "low"        # Storage, utility areas

class AirSealing(str, Enum):
    TIGHT = "tight"
    AVERAGE = "average"
    LEAKY = "leaky"

class HeatSource(str, Enum):
    KITCHEN_APPLIANCES = "kitchen_appliances"
    ELECTRONICS = "electronics"
    HOME_OFFICE = "home_office"
    LAUNDRY = "laundry"
    FIREPLACE = "fireplace"

class Zone(BaseModel):
    name: str = Field(..., description="User-defined zone name")
    square_feet: int = Field(..., ge=50, le=5000, description="Zone area in square feet")
    ceiling_height: float = Field(8.0, ge=7.0, le=20.0, description="Ceiling height in feet")
    zone_type: ZoneType = Field(..., description="Type of zone for load calculations")
    sun_exposure: SunExposure = Field(..., description="Primary sun exposure direction")
    window_coverage: float = Field(0.15, ge=0.0, le=0.5, description="Percentage of wall area that's windows")
    occupancy: OccupancyLevel = Field(OccupancyLevel.MEDIUM, description="Expected occupancy level")
    heat_sources: List[HeatSource] = Field(default=[], description="Additional heat sources in zone")
    air_sealing: AirSealing = Field(AirSealing.AVERAGE, description="Air sealing quality")
    is_above_grade: bool = Field(True, description="True if above ground level")
    
class MultiZoneRequest(BaseModel):
    zip_code: str = Field(..., pattern=r"^\d{5}$", description="5-digit ZIP code")
    build_year: int = Field(..., ge=1900, le=2025, description="Year home was built")
    zones: List[Zone] = Field(..., min_length=1, max_length=10, description="List of zones to calculate")

class ZoneResult(BaseModel):
    zone_name: str
    cooling_load_btu: int
    heating_load_btu: int
    recommended_capacity_tons: float
    load_factors: dict = Field(description="Breakdown of factors affecting load")
    equipment_recommendations: List[dict]

class SystemOption(BaseModel):
    option_name: str
    description: str
    total_equipment_cost: int
    installation_complexity: Literal["simple", "moderate", "complex"]
    energy_efficiency_rating: float
    zones_served: List[str]
    equipment_list: List[dict]

class MultiZoneResponse(BaseModel):
    total_cooling_load: int
    total_heating_load: int
    zone_results: List[ZoneResult]
    system_options: List[SystemOption]
    climate_info: dict
    recommendations: dict = Field(description="General recommendations and considerations")