from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from enum import Enum

class BackupHeatType(str, Enum):
    ELECTRIC_STRIP = "electric_strip"
    GAS_FURNACE = "gas_furnace"
    OIL_BOILER = "oil_boiler"
    NONE = "none"

class ColdClimateInput(BaseModel):
    zip_code: str = Field(..., pattern="^[0-9]{5}$", description="US ZIP code")
    square_feet: int = Field(..., ge=100, le=10000, description="Home square footage")
    build_year: int = Field(..., ge=1900, le=2025, description="Year home was built")
    heat_pump_model: str = Field(..., description="Heat pump model to analyze")
    existing_backup_heat: Optional[BackupHeatType] = Field(None, description="Existing backup heating system")
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v):
        if not v.isdigit() or len(v) != 5:
            raise ValueError('ZIP code must be 5 digits')
        return v

class TemperatureCapacityPoint(BaseModel):
    temperature: float  # °F
    capacity_btu: int   # BTU/hr at this temperature
    cop: float          # Coefficient of Performance

class PerformanceAnalysis(BaseModel):
    design_temperature: float
    design_load_btu: int
    heat_pump_capacity_at_design: int
    capacity_coverage_percent: float
    backup_heat_needed_btu: int
    performance_rating: str  # "Excellent", "Good", "Marginal", "Inadequate"

class BackupHeatRecommendation(BaseModel):
    recommended_type: BackupHeatType
    required_capacity_btu: int
    estimated_cost_range: str
    installation_complexity: str  # "Simple", "Moderate", "Complex"
    reasoning: str

class ColdClimateResponse(BaseModel):
    # Input summary
    location_info: Dict[str, str]
    heat_pump_model: str
    design_conditions: Dict[str, float]
    
    # Performance data
    capacity_curve: List[TemperatureCapacityPoint]
    performance_analysis: PerformanceAnalysis
    
    # Recommendations
    backup_heat_recommendation: Optional[BackupHeatRecommendation]
    
    # Analysis details
    temperature_range_analysis: List[Dict]
    key_findings: List[str]
    warnings: List[str]
    calculation_notes: List[str]