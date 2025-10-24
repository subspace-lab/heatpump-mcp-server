from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime

class BillEstimatorInput(BaseModel):
    zip_code: str = Field(..., pattern="^[0-9]{5}$", description="US ZIP code")
    square_feet: int = Field(..., ge=100, le=10000, description="Home square footage")
    build_year: int = Field(..., ge=1900, le=2025, description="Year home was built")
    heat_pump_model: str = Field(..., description="Selected heat pump model")
    gas_price_per_therm: Optional[float] = Field(None, ge=0, le=10, description="Local gas price per therm (optional)")
    current_heating_fuel: str = Field(default="gas", description="Current heating fuel type")
    current_heating_cost: Optional[float] = Field(None, ge=0, description="Current annual heating cost")
    electricity_rate: Optional[float] = Field(None, ge=0, le=1, description="Electricity rate per kWh")
    electricity_rate_override: Optional[float] = Field(None, ge=0, le=1, description="Manual electricity rate per kWh")
    
    @field_validator('zip_code')
    @classmethod
    def validate_zip(cls, v):
        if not v.isdigit() or len(v) != 5:
            raise ValueError('ZIP code must be 5 digits')
        return v

class MonthlyBillBreakdown(BaseModel):
    month: str
    temperature_avg: float
    heating_load_btu: int
    heat_pump_kwh: float
    heat_pump_cost: float
    gas_furnace_therms: Optional[float] = None
    gas_furnace_cost: Optional[float] = None
    savings: float

class AnnualCostSummary(BaseModel):
    heat_pump_annual_kwh: float
    heat_pump_annual_cost: float
    gas_furnace_annual_therms: Optional[float] = None
    gas_furnace_annual_cost: Optional[float] = None
    annual_savings: float
    payback_years: float

class TenYearProjection(BaseModel):
    year: int
    heat_pump_cost: float
    gas_cost: Optional[float] = None
    cumulative_savings: float

class BillEstimatorResponse(BaseModel):
    # Input summary
    location_info: Dict[str, str]
    electricity_rate: float
    gas_rate: Optional[float] = None
    heat_pump_info: Dict[str, str]
    
    # Calculations
    monthly_breakdown: List[MonthlyBillBreakdown]
    annual_summary: AnnualCostSummary
    ten_year_projection: List[TenYearProjection]
    
    # Analysis
    break_even_year: int
    total_10yr_savings: float
    avg_monthly_savings: float
    annual_heat_pump_cost: float
    annual_current_cost: float
    calculation_notes: List[str]