import logging
from typing import List, Dict, Optional
import calendar
from ..models.bill_estimator import (
    BillEstimatorInput,
    BillEstimatorResponse,
    MonthlyBillBreakdown,
    AnnualCostSummary,
    TenYearProjection,
)
from .design_temp_service import design_temp_service
from .electricity_rate_service import electricity_rate_service

logger = logging.getLogger("heatpumpiq.service.bill_estimator")


class BillEstimatorService:
    # Heat pump COP curves by temperature (simplified)
    COP_CURVES = {
        "default": {
            47: 3.5,  # 47°F
            32: 3.0,  # 32°F
            17: 2.5,  # 17°F
            5: 2.0,  # 5°F
            -5: 1.5,  # -5°F
        }
    }

    # Monthly average temperatures by climate zone (°F)
    MONTHLY_TEMPS = {
        "1A": [60, 63, 70, 77, 83, 87, 89, 89, 85, 78, 69, 62],  # Hot humid
        "2A": [50, 54, 62, 70, 78, 84, 87, 86, 81, 71, 61, 52],  # Hot humid
        "3A": [42, 46, 55, 65, 74, 81, 85, 83, 77, 66, 55, 44],  # Mixed humid
        "3B": [45, 50, 58, 67, 76, 84, 89, 87, 80, 69, 56, 46],  # Hot dry
        "4A": [35, 38, 47, 58, 68, 77, 82, 80, 73, 61, 50, 39],  # Mixed humid
        "4B": [38, 43, 51, 61, 71, 80, 86, 84, 76, 64, 50, 40],  # Mixed dry
        "4C": [43, 46, 50, 55, 61, 66, 71, 72, 67, 59, 51, 45],  # Marine
        "5A": [28, 32, 42, 54, 65, 74, 79, 77, 69, 57, 45, 33],  # Cold humid
        "5B": [32, 37, 46, 57, 67, 76, 83, 81, 72, 60, 45, 34],  # Cold dry
        "6A": [21, 25, 36, 49, 61, 71, 76, 74, 66, 54, 41, 27],  # Cold humid
        "6B": [25, 30, 40, 52, 63, 72, 79, 77, 68, 56, 41, 28],  # Cold dry
        "7": [15, 20, 32, 46, 59, 69, 74, 72, 63, 50, 35, 21],  # Very cold
        "8": [5, 12, 26, 42, 57, 67, 71, 68, 58, 42, 26, 10],  # Subarctic
    }

    # Gas furnace efficiency (AFUE)
    GAS_FURNACE_EFFICIENCY = 0.90

    # Energy content: 1 therm = 100,000 BTU
    BTU_PER_THERM = 100000

    async def calculate_costs(self, input_data: BillEstimatorInput) -> BillEstimatorResponse:
        try:
            logger.info(
                f"💰 Starting bill calculation for {input_data.square_feet} sqft, ZIP {input_data.zip_code}, model {input_data.heat_pump_model}"
            )

            # Get location and climate data (validates ZIP code)
            temp_data = design_temp_service.get_design_temp(input_data.zip_code)
            logger.info(
                f"🌡️ Found location data: {temp_data['city']}, {temp_data['state']} - Zone {temp_data['climate_zone']}"
            )

            # Get electricity rate
            # Use state from temp_data (which uses pgeocode internally)
            state_code = temp_data.get("state", "NY")
            if not state_code or len(state_code) != 2:
                logger.warning(
                    f"⚠️ Could not determine valid state from ZIP {input_data.zip_code}, using NY as fallback"
                )
                state_code = "NY"

            logger.info(f"🏛️ State determined: {state_code}")

            electricity_rate = input_data.electricity_rate_override or input_data.electricity_rate
            if not electricity_rate:
                logger.info(f"⚡ Fetching electricity rate for {state_code}")
                electricity_rate = await electricity_rate_service.get_rate_by_state(state_code)
                if not electricity_rate:
                    logger.warning(f"⚠️ Could not fetch rate for {state_code}, using default")
                    electricity_rate = 0.16

            logger.info(f"⚡ Electricity rate: ${electricity_rate:.3f}/kWh")

            # Calculate heating load (simplified Manual J)
            logger.info(
                f"🏠 Calculating annual heating load for {input_data.square_feet} sqft home"
            )
            annual_heating_load = self._calculate_annual_heating_load(
                input_data.square_feet,
                input_data.build_year,
                temp_data["climate_zone"],
                temp_data["design_temp"],
            )
            logger.info(f"🔥 Annual heating load calculated: {annual_heating_load:,.0f} BTU")

            # Get monthly temperatures
            climate_zone = temp_data["climate_zone"]
            monthly_temps = self.MONTHLY_TEMPS.get(climate_zone, self.MONTHLY_TEMPS["4A"])
            logger.info(f"🌡️ Using monthly temperature profile for climate zone {climate_zone}")

            # Calculate monthly costs
            logger.info(f"📊 Starting monthly cost calculations...")
            monthly_breakdown = []
            total_hp_kwh = 0
            total_hp_cost = 0
            total_gas_therms = 0
            total_gas_cost = 0

            for month_idx, avg_temp in enumerate(monthly_temps):
                month_name = calendar.month_name[month_idx + 1]

                # Calculate monthly heating load (degree days approach)
                monthly_load = self._calculate_monthly_heating_load(
                    annual_heating_load, avg_temp, climate_zone
                )

                if monthly_load > 0:
                    # Heat pump calculations
                    cop = self._get_cop_at_temperature(avg_temp)
                    hp_kwh = monthly_load / (cop * 3412)  # 3412 BTU/kWh
                    hp_cost = hp_kwh * electricity_rate

                    # Gas furnace calculations (if gas price provided)
                    gas_therms = None
                    gas_cost = None
                    if input_data.gas_price_per_therm:
                        gas_therms = monthly_load / (
                            self.BTU_PER_THERM * self.GAS_FURNACE_EFFICIENCY
                        )
                        gas_cost = gas_therms * input_data.gas_price_per_therm

                    savings = (gas_cost or 0) - hp_cost

                    monthly_breakdown.append(
                        MonthlyBillBreakdown(
                            month=month_name,
                            temperature_avg=avg_temp,
                            heating_load_btu=int(monthly_load),
                            heat_pump_kwh=hp_kwh,
                            heat_pump_cost=hp_cost,
                            gas_furnace_therms=gas_therms,
                            gas_furnace_cost=gas_cost,
                            savings=savings,
                        )
                    )

                    total_hp_kwh += hp_kwh
                    total_hp_cost += hp_cost
                    if gas_therms:
                        total_gas_therms += gas_therms
                        total_gas_cost += gas_cost
                else:
                    # No heating needed this month
                    monthly_breakdown.append(
                        MonthlyBillBreakdown(
                            month=month_name,
                            temperature_avg=avg_temp,
                            heating_load_btu=0,
                            heat_pump_kwh=0,
                            heat_pump_cost=0,
                            gas_furnace_therms=0,
                            gas_furnace_cost=0,
                            savings=0,
                        )
                    )

            logger.info(
                f"💡 Total annual heat pump consumption: {total_hp_kwh:,.0f} kWh, Cost: ${total_hp_cost:.2f}"
            )
            if total_gas_cost > 0:
                logger.info(
                    f"🔥 Total annual gas consumption: {total_gas_therms:.1f} therms, Cost: ${total_gas_cost:.2f}"
                )

            # Annual summary
            annual_savings = total_gas_cost - total_hp_cost if total_gas_cost > 0 else 0
            payback_years = 0  # Would need heat pump vs furnace equipment cost difference

            if annual_savings > 0:
                logger.info(f"💰 Annual savings with heat pump: ${annual_savings:.2f}")
            elif annual_savings < 0:
                logger.info(f"📈 Annual additional cost with heat pump: ${abs(annual_savings):.2f}")
            else:
                logger.info(f"⚖️ No gas comparison data available for savings calculation")

            annual_summary = AnnualCostSummary(
                heat_pump_annual_kwh=total_hp_kwh,
                heat_pump_annual_cost=total_hp_cost,
                gas_furnace_annual_therms=total_gas_therms if total_gas_therms > 0 else None,
                gas_furnace_annual_cost=total_gas_cost if total_gas_cost > 0 else None,
                annual_savings=annual_savings,
                payback_years=payback_years,
            )

            # 10-year projection
            ten_year_projection = []
            cumulative_savings = 0
            for year in range(1, 11):
                # Assume 3% energy price inflation
                year_hp_cost = total_hp_cost * (1.03**year)
                year_gas_cost = total_gas_cost * (1.03**year) if total_gas_cost > 0 else 0
                year_savings = year_gas_cost - year_hp_cost if year_gas_cost > 0 else 0
                cumulative_savings += year_savings

                ten_year_projection.append(
                    TenYearProjection(
                        year=year,
                        heat_pump_cost=year_hp_cost,
                        gas_cost=year_gas_cost if year_gas_cost > 0 else None,
                        cumulative_savings=cumulative_savings,
                    )
                )

            # Calculate break-even year
            break_even_year = 0
            for projection in ten_year_projection:
                if projection.cumulative_savings >= 0:
                    break_even_year = projection.year
                    break

            if break_even_year > 0:
                logger.info(f"📈 Break-even year: {break_even_year}")
            else:
                logger.info(f"📊 No break-even point found within 10-year projection")

            # Calculation notes
            calculation_notes = [
                f"Based on {annual_heating_load:,.0f} BTU annual heating load",
                f"Using electricity rate of ${electricity_rate:.3f}/kWh for {state_code}",
                f"Heat pump efficiency varies from 1.5-3.5 COP based on temperature",
            ]

            if input_data.gas_price_per_therm:
                calculation_notes.append(
                    f"Gas furnace: {self.GAS_FURNACE_EFFICIENCY * 100:.0f}% AFUE at ${input_data.gas_price_per_therm:.2f}/therm"
                )

            logger.info(
                f"✅ Bill calculation completed successfully: Annual HP cost ${total_hp_cost:.2f}"
            )

            return BillEstimatorResponse(
                location_info={
                    "city": temp_data.get("city", "Unknown"),
                    "state": state_code,
                    "climate_zone": climate_zone,
                },
                electricity_rate=electricity_rate,
                gas_rate=input_data.gas_price_per_therm,
                heat_pump_info={"model": input_data.heat_pump_model},
                monthly_breakdown=monthly_breakdown,
                annual_summary=annual_summary,
                ten_year_projection=ten_year_projection,
                break_even_year=break_even_year,
                total_10yr_savings=cumulative_savings,
                avg_monthly_savings=annual_savings / 12 if annual_savings > 0 else 0,
                annual_heat_pump_cost=total_hp_cost,
                annual_current_cost=input_data.current_heating_cost or total_gas_cost,
                calculation_notes=calculation_notes,
            )

        except Exception as e:
            logger.error(
                f"❌ Bill calculation FAILED for {input_data.square_feet} sqft, ZIP {input_data.zip_code}"
            )
            logger.error(f"❌ Input data: {input_data.model_dump()}")
            logger.error(f"❌ Error details: {str(e)}", exc_info=True)
            raise

    def _calculate_annual_heating_load(
        self, sqft: int, build_year: int, climate_zone: str, design_temp: float
    ) -> float:
        """Calculate annual heating load in BTU"""
        # Simplified degree day calculation
        # Base temperature 65°F, heating season varies by climate

        heating_design_temp = design_temp
        degree_days = max(0, 65 - heating_design_temp) * 180  # Approximate heating season days

        # Building heat loss coefficient (BTU/hr-°F)
        # Varies by age and climate zone
        age = 2025 - build_year
        if age > 40:
            ua_factor = 15  # Poor insulation
        elif age > 20:
            ua_factor = 12  # Moderate insulation
        else:
            ua_factor = 8  # Good insulation

        ua_total = sqft * ua_factor
        annual_load = ua_total * degree_days  # Remove the * 24 - already in degree days

        return annual_load

    def _calculate_monthly_heating_load(
        self, annual_load: float, avg_temp: float, climate_zone: str
    ) -> float:
        """Calculate monthly heating load based on temperature"""
        # Simplified: heating needed when temp < 65°F
        if avg_temp >= 65:
            return 0

        # Rough approximation: monthly load proportional to degree days
        monthly_degree_days = max(0, 65 - avg_temp) * 30  # 30 days per month
        annual_degree_days = max(
            1,
            sum(
                max(0, 65 - temp) * 30
                for temp in self.MONTHLY_TEMPS.get(climate_zone, self.MONTHLY_TEMPS["4A"])
            ),
        )

        return annual_load * (monthly_degree_days / annual_degree_days)

    def _get_cop_at_temperature(self, temp: float) -> float:
        """Get heat pump COP at given temperature"""
        cop_curve = self.COP_CURVES["default"]

        # Linear interpolation between known points
        temps = sorted(cop_curve.keys())

        if temp >= max(temps):
            return cop_curve[max(temps)]
        if temp <= min(temps):
            return cop_curve[min(temps)]

        # Find surrounding temperatures
        for i in range(len(temps) - 1):
            if temps[i] <= temp <= temps[i + 1]:
                t1, t2 = temps[i], temps[i + 1]
                cop1, cop2 = cop_curve[t1], cop_curve[t2]
                # Linear interpolation
                return cop1 + (cop2 - cop1) * (temp - t1) / (t2 - t1)

        return 2.5  # Default COP


# Singleton instance
bill_estimator_service = BillEstimatorService()
