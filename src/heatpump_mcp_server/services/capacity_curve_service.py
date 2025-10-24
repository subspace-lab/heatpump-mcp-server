from typing import Dict, List, Optional
import math
from ..models.cold_climate import TemperatureCapacityPoint

class CapacityCurveService:
    
    # Sample heat pump capacity data (in production, this would come from manufacturer specs)
    # Format: {model_name: {temp: (capacity_btu, cop)}}
    HEAT_PUMP_SPECS = {
        "Mitsubishi MXZ-3C24NA": {
            47: (24000, 3.8),   # Rated capacity at 47°F
            17: (22800, 3.2),   # 95% capacity at 17°F
            5: (20400, 2.7),    # 85% capacity at 5°F
            -5: (18000, 2.2),   # 75% capacity at -5°F
            -13: (15600, 1.8),  # 65% capacity at -13°F
        },
        "Mitsubishi MXZ-3C30NA": {
            47: (30000, 3.6),
            17: (28500, 3.0),
            5: (25500, 2.5),
            -5: (22500, 2.0),
            -13: (19500, 1.6),
        },
        "Mitsubishi MXZ-4C36NA": {
            47: (36000, 3.4),
            17: (34200, 2.9),
            5: (30600, 2.4),
            -5: (27000, 1.9),
            -13: (23400, 1.5),
        },
        "Daikin 2MXS18NMVJU": {
            47: (18000, 4.0),
            17: (17100, 3.4),
            5: (15300, 2.9),
            -5: (13500, 2.4),
            -13: (11700, 2.0),
        },
        "Daikin 3MXS24NMVJU": {
            47: (24000, 3.8),
            17: (22800, 3.2),
            5: (20400, 2.7),
            -5: (18000, 2.2),
            -13: (15600, 1.8),
        },
        "Fujitsu AOU24RLXFZ": {
            47: (24000, 4.2),
            17: (23040, 3.6),
            5: (21120, 3.0),
            -5: (18720, 2.5),
            -13: (16320, 2.1),
        },
        "Fujitsu AOU36RLXFZ": {
            47: (36000, 4.0),
            17: (34560, 3.4),
            5: (31680, 2.8),
            -5: (28080, 2.3),
            -13: (24480, 1.9),
        },
        "LG LMU240HHV": {
            47: (24000, 3.2),
            17: (21600, 2.7),
            5: (18720, 2.2),
            -5: (15840, 1.8),
            -13: (12960, 1.4),
        },
        "LG LMU360HHV": {
            47: (36000, 3.0),
            17: (32400, 2.5),
            5: (28080, 2.0),
            -5: (23760, 1.6),
            -13: (19440, 1.2),
        }
    }
    
    def get_capacity_curve(self, model_name: str, temp_range: Optional[tuple] = None) -> List[TemperatureCapacityPoint]:
        """Get capacity curve for a heat pump model"""
        
        # Default temperature range from -15°F to 50°F
        if temp_range is None:
            temp_range = (-15, 50)
        
        min_temp, max_temp = temp_range
        
        # Get model specs or use default
        model_specs = self.HEAT_PUMP_SPECS.get(model_name)
        if not model_specs:
            # Use a generic 24,000 BTU model as default
            model_specs = self.HEAT_PUMP_SPECS["Mitsubishi MXZ-3C24NA"]
        
        # Generate curve points every 5 degrees
        curve_points = []
        for temp in range(min_temp, max_temp + 1, 5):
            capacity, cop = self._interpolate_capacity(model_specs, temp)
            curve_points.append(TemperatureCapacityPoint(
                temperature=temp,
                capacity_btu=int(capacity),
                cop=round(cop, 2)
            ))
        
        return curve_points
    
    def get_capacity_at_temperature(self, model_name: str, temperature: float) -> tuple:
        """Get capacity and COP at specific temperature"""
        
        model_specs = self.HEAT_PUMP_SPECS.get(model_name)
        if not model_specs:
            model_specs = self.HEAT_PUMP_SPECS["Mitsubishi MXZ-3C24NA"]
        
        return self._interpolate_capacity(model_specs, temperature)
    
    def _interpolate_capacity(self, model_specs: Dict[float, tuple], target_temp: float) -> tuple:
        """Interpolate capacity and COP at target temperature"""
        
        temps = sorted(model_specs.keys())
        
        # If temperature is outside range, extrapolate from closest points
        if target_temp <= min(temps):
            temp = min(temps)
            capacity, cop = model_specs[temp]
            # Linear extrapolation for very cold temperatures (capacity decreases)
            if target_temp < temp:
                temp_diff = temp - target_temp
                capacity_loss = capacity * 0.02 * temp_diff  # 2% per degree below
                cop_loss = cop * 0.03 * temp_diff  # 3% per degree below
                capacity = max(capacity - capacity_loss, capacity * 0.3)  # Don't go below 30%
                cop = max(cop - cop_loss, 1.0)  # Don't go below 1.0 COP
            return capacity, cop
        
        if target_temp >= max(temps):
            temp = max(temps)
            capacity, cop = model_specs[temp]
            # Slight increase for warmer temperatures
            if target_temp > temp:
                temp_diff = target_temp - temp
                capacity_gain = capacity * 0.005 * temp_diff  # 0.5% per degree above
                cop_gain = cop * 0.01 * temp_diff  # 1% per degree above
                capacity = min(capacity + capacity_gain, capacity * 1.1)  # Don't exceed 110%
                cop = min(cop + cop_gain, cop * 1.2)  # Don't exceed 120%
            return capacity, cop
        
        # Find surrounding temperatures for interpolation
        for i in range(len(temps) - 1):
            if temps[i] <= target_temp <= temps[i + 1]:
                t1, t2 = temps[i], temps[i + 1]
                cap1, cop1 = model_specs[t1]
                cap2, cop2 = model_specs[t2]
                
                # Linear interpolation
                factor = (target_temp - t1) / (t2 - t1)
                capacity = cap1 + (cap2 - cap1) * factor
                cop = cop1 + (cop2 - cop1) * factor
                
                return capacity, cop
        
        # Fallback (shouldn't reach here)
        return model_specs[temps[0]]
    
    def get_model_rated_capacity(self, model_name: str) -> int:
        """Get the rated capacity (at 47°F) for a model"""
        
        model_specs = self.HEAT_PUMP_SPECS.get(model_name)
        if not model_specs:
            return 24000  # Default
        
        if 47 in model_specs:
            return model_specs[47][0]
        
        # Find closest temperature to 47°F
        closest_temp = min(model_specs.keys(), key=lambda x: abs(x - 47))
        return model_specs[closest_temp][0]
    
    def get_available_models(self) -> List[str]:
        """Get list of available heat pump models"""
        return list(self.HEAT_PUMP_SPECS.keys())

# Singleton instance
capacity_curve_service = CapacityCurveService()