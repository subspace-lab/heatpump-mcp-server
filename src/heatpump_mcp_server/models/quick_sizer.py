from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union
from .multi_zone import Zone


class QuickSizerInput(BaseModel):
    zip_code: str = Field(..., pattern="^[0-9]{5}$", description="US ZIP code")
    square_feet: Optional[int] = Field(
        None, ge=100, le=10000, description="Home square footage (for single-zone)"
    )
    build_year: int = Field(..., ge=1900, le=2025, description="Year home was built")
    zones: Optional[List[Zone]] = Field(None, description="Zone configuration (for multi-zone)")

    # Humidity-aware sizing parameters
    humidity_concerns: Optional[bool] = Field(False, description="Does home have humidity issues?")
    humidity_level: Optional[str] = Field(
        "normal", description="Humidity level: low, normal, high, extreme"
    )
    dehumidification_priority: Optional[bool] = Field(
        False, description="Prioritize dehumidification capability"
    )
    basement_moisture: Optional[bool] = Field(False, description="Basement moisture issues")
    bathroom_ventilation: Optional[str] = Field(
        "adequate", description="Bathroom ventilation: poor, adequate, excellent"
    )

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v):
        if not v.isdigit() or len(v) != 5:
            raise ValueError("ZIP code must be 5 digits")
        return v

    @field_validator("square_feet")
    @classmethod
    def validate_single_zone_fields(cls, v, info):
        values = info.data if info else {}
        zones = values.get("zones")
        if zones is None and v is None:
            raise ValueError(
                "Either square_feet (single-zone) or zones (multi-zone) must be provided"
            )
        if zones is not None and v is not None:
            raise ValueError(
                "Cannot specify both square_feet and zones - choose single or multi-zone mode"
            )
        return v

    @field_validator("humidity_level")
    @classmethod
    def validate_humidity_level(cls, v):
        valid_levels = ["low", "normal", "high", "extreme"]
        if v not in valid_levels:
            raise ValueError(f"Humidity level must be one of: {valid_levels}")
        return v

    @field_validator("bathroom_ventilation")
    @classmethod
    def validate_bathroom_ventilation(cls, v):
        valid_levels = ["poor", "adequate", "excellent"]
        if v not in valid_levels:
            raise ValueError(f"Bathroom ventilation must be one of: {valid_levels}")
        return v


class HeatPumpModel(BaseModel):
    brand: str
    model: str
    btu_capacity: int
    hspf2: float
    price_range: str


class QuickSizerResponse(BaseModel):
    required_btu: Optional[int] = None  # For single-zone
    btu_range_min: Optional[int] = None  # For single-zone
    btu_range_max: Optional[int] = None  # For single-zone
    design_temperature: Optional[float] = None
    climate_zone: Optional[str] = None
    recommended_models: Optional[List[HeatPumpModel]] = None  # For single-zone
    calculation_notes: Optional[str] = None  # For single-zone

    # Multi-zone fields
    total_cooling_load: Optional[int] = None
    total_heating_load: Optional[int] = None
    zone_results: Optional[List] = None
    system_options: Optional[List] = None
    recommendations: Optional[dict] = None

    # Humidity-aware fields
    humidity_recommendations: Optional[dict] = None
    dehumidification_capacity: Optional[float] = None
    humidity_adjustments: Optional[dict] = None

    # Oversizing warnings
    oversizing_warnings: Optional[List[str]] = None

    is_multi_zone: bool = False
