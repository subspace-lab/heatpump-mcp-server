from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class InstallationComplexity(str, Enum):
    STANDARD = "standard"
    COMPLEX = "complex"
    DIFFICULT = "difficult"

class ElectricalWork(str, Enum):
    NONE = "none"
    MINOR = "minor"
    PANEL_UPGRADE = "panel_upgrade"
    MAJOR = "major"

class DuctworkWork(str, Enum):
    NONE = "none"
    MINOR_REPAIRS = "minor_repairs"
    MAJOR_MODIFICATIONS = "major_modifications"
    NEW_INSTALLATION = "new_installation"

class ProjectCostInput(BaseModel):
    zip_code: str = Field(..., description="5-digit ZIP code")
    square_feet: int = Field(..., gt=0, description="House square footage")
    build_year: int = Field(..., ge=1900, le=2025, description="Year house was built")
    heat_pump_model: str = Field(..., description="Selected heat pump model")
    heat_pump_brand: Optional[str] = Field(default=None, description="Heat pump brand (for new frontend)")
    existing_heating_type: str = Field(default="gas_furnace", description="Type of existing heating system")
    ductwork_condition: str = Field(default="good", description="Condition of existing ductwork")
    electrical_panel_age: Optional[int] = Field(default=None, description="Age of electrical panel")
    installation_complexity: InstallationComplexity = Field(default=InstallationComplexity.STANDARD)
    
    # Enhanced complexity factors
    roof_access: Optional[str] = Field(default=None, description="Roof access difficulty: easy, moderate, difficult")
    electrical_panel_location: Optional[str] = Field(default=None, description="Panel location: basement, garage, main_floor, outdoor")
    outdoor_unit_placement: Optional[str] = Field(default=None, description="Outdoor unit placement: ground_level, roof, balcony")
    refrigerant_line_distance: Optional[int] = Field(default=None, description="Distance from outdoor to indoor unit in feet")
    home_stories: Optional[int] = Field(default=None, description="Number of stories in home")
    
    # Building envelope factors
    insulation_quality: Optional[str] = Field(default=None, description="Insulation quality: poor, fair, good, excellent")
    window_type: Optional[str] = Field(default=None, description="Window type: single_pane, double_pane, triple_pane")
    air_sealing: Optional[str] = Field(default=None, description="Air sealing quality: poor, fair, good, excellent")
    
    # Site-specific challenges
    hoa_restrictions: Optional[bool] = Field(default=None, description="HOA restrictions on equipment placement")
    permit_complexity: Optional[str] = Field(default=None, description="Local permit complexity: simple, moderate, complex")
    seasonal_access: Optional[str] = Field(default=None, description="Seasonal access issues: none, winter, year_round")
    
    # Advanced site-specific challenges
    property_type: Optional[str] = Field(default=None, description="Property type: single_family, townhome, condo, apartment")
    foundation_type: Optional[str] = Field(default=None, description="Foundation type: basement, crawl_space, slab, pier")
    utility_access: Optional[str] = Field(default=None, description="Utility access: easy, moderate, difficult, underground")
    neighborhood_density: Optional[str] = Field(default=None, description="Neighborhood density: rural, suburban, urban, high_density")
    landscaping_obstacles: Optional[bool] = Field(default=None, description="Significant landscaping obstacles present")
    structural_constraints: Optional[bool] = Field(default=None, description="Structural constraints for equipment placement")
    noise_restrictions: Optional[bool] = Field(default=None, description="Local noise ordinances or restrictions")
    historical_designation: Optional[bool] = Field(default=None, description="Historical building designation restrictions")
    flood_zone: Optional[bool] = Field(default=None, description="Located in flood zone requiring elevated installation")
    seismic_zone: Optional[str] = Field(default=None, description="Seismic zone requirements: none, low, moderate, high")
    extreme_weather_risk: Optional[str] = Field(default=None, description="Extreme weather risk: low, moderate, high, severe")

class CostRange(BaseModel):
    low: float = Field(..., description="Low end of cost range")
    high: float = Field(..., description="High end of cost range")
    average: float = Field(..., description="Average cost")

class EquipmentCost(BaseModel):
    heat_pump_unit: float = Field(..., description="Heat pump equipment cost")
    installation_materials: float = Field(..., description="Installation materials cost")
    total_equipment: float = Field(..., description="Total equipment cost")

class InstallationCost(BaseModel):
    labor_hours: float = Field(..., description="Estimated labor hours")
    hourly_rate: float = Field(..., description="Regional hourly rate")
    base_installation: float = Field(..., description="Base installation cost")
    complexity_multiplier: float = Field(..., description="Complexity adjustment factor")
    total_installation: float = Field(..., description="Total installation cost")

class ElectricalCost(BaseModel):
    assessment: ElectricalWork = Field(..., description="Type of electrical work needed")
    panel_upgrade: float = Field(default=0, description="Panel upgrade cost")
    wiring: float = Field(default=0, description="New wiring cost")
    disconnect: float = Field(default=0, description="Disconnect installation cost")
    permits: float = Field(default=0, description="Electrical permit cost")
    total_electrical: float = Field(..., description="Total electrical cost")

class DuctworkCost(BaseModel):
    assessment: DuctworkWork = Field(..., description="Type of ductwork needed")
    repairs: float = Field(default=0, description="Ductwork repair cost")
    modifications: float = Field(default=0, description="Ductwork modification cost")
    new_ducts: float = Field(default=0, description="New ductwork cost")
    total_ductwork: float = Field(..., description="Total ductwork cost")

class PermitCost(BaseModel):
    hvac_permit: float = Field(..., description="HVAC permit cost")
    electrical_permit: float = Field(default=0, description="Electrical permit cost")
    building_permit: float = Field(default=0, description="Building permit cost")
    total_permits: float = Field(..., description="Total permit cost")

class RegionalFactors(BaseModel):
    zip_code: str = Field(..., description="ZIP code")
    labor_multiplier: float = Field(..., description="Regional labor cost multiplier")
    permit_base_cost: float = Field(..., description="Base permit cost for region")
    market_conditions: float = Field(default=1.0, description="Current market conditions multiplier")
    cost_of_living_index: float = Field(default=1.0, description="Cost of living adjustment")

class ProjectCostBreakdown(BaseModel):
    equipment: EquipmentCost = Field(..., description="Equipment cost breakdown")
    installation: InstallationCost = Field(..., description="Installation cost breakdown")
    electrical: ElectricalCost = Field(..., description="Electrical work cost breakdown")
    ductwork: DuctworkCost = Field(..., description="Ductwork cost breakdown")
    permits: PermitCost = Field(..., description="Permit cost breakdown")
    regional_factors: RegionalFactors = Field(..., description="Regional cost factors")

class ProjectCostEstimate(BaseModel):
    input_summary: ProjectCostInput = Field(..., description="Input parameters used")
    cost_breakdown: ProjectCostBreakdown = Field(..., description="Detailed cost breakdown")
    total_cost: CostRange = Field(..., description="Total project cost range")
    confidence_level: str = Field(..., description="Confidence level of estimate")
    assumptions: List[str] = Field(..., description="Key assumptions made in estimate")
    cost_comparison: Dict[str, Any] = Field(..., description="Cost comparison with alternatives")
    financing_options: List[Dict[str, Any]] = Field(default=[], description="Available financing options")
    disclaimers: List[str] = Field(..., description="Important disclaimers about estimate")

class RegionalCostData(BaseModel):
    zip_code: str = Field(..., description="5-digit ZIP code")
    metro_area: str = Field(..., description="Metropolitan area name")
    labor_rate_hvac: float = Field(..., description="HVAC labor rate $/hour")
    labor_rate_electrical: float = Field(..., description="Electrical labor rate $/hour")
    permit_cost_base: float = Field(..., description="Base permit cost")
    cost_of_living_multiplier: float = Field(..., description="Cost of living multiplier")
    market_conditions: float = Field(default=1.0, description="Current market conditions")
    last_updated: str = Field(..., description="Last update timestamp")