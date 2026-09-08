import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.services.risk_engine.base import RiskAssessmentOutput, RiskEngine


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuleBasedRiskEngine(RiskEngine):
    """
    Hydrological rule-based risk calculation engine.
    Calculates weighted factor scores:
    1. Water Level Ratio (relative to Warning and Danger thresholds) - 35%
    2. Water Rise Rate (m/hr) - 25%
    3. Current Rainfall (mm/hr) - 15%
    4. Soil Moisture Saturation (%) - 15%
    5. 24h Rainfall Forecast (mm) - 10%
    """

    def calculate_sensor_risk(
        self,
        water_level: float,
        water_rise_rate: float,
        rainfall: float,
        soil_moisture: float,
        warning_threshold: float,
        danger_threshold: float,
        forecast_rain_mm: float = 0.0,
        sensor_id: Optional[str] = None
    ) -> RiskAssessmentOutput:
        # 1. Water Level Factor (0-100)
        # 0 at 0m, 50 at warning_threshold, 100 at danger_threshold
        if danger_threshold > warning_threshold:
            if water_level <= warning_threshold:
                # Scaled 0 to 50
                water_ratio = max(0.0, water_level / max(warning_threshold, 0.1))
                water_score = min(50.0, water_ratio * 50.0)
            else:
                # Scaled 50 to 100
                excess = (water_level - warning_threshold) / (danger_threshold - warning_threshold)
                water_score = min(100.0, 50.0 + excess * 50.0)
        else:
            water_score = 50.0

        # 2. Rise Rate Factor (0-100)
        # <= 0.0 m/hr -> 0; 0.10 m/hr -> 40; 0.25 m/hr -> 75; >= 0.50 m/hr -> 100
        if water_rise_rate <= 0:
            rise_score = 0.0
        elif water_rise_rate < 0.10:
            rise_score = (water_rise_rate / 0.10) * 40.0
        elif water_rise_rate < 0.25:
            rise_score = 40.0 + ((water_rise_rate - 0.10) / 0.15) * 35.0
        else:
            rise_score = min(100.0, 75.0 + ((water_rise_rate - 0.25) / 0.25) * 25.0)

        # 3. Rainfall Factor (0-100)
        # 0 mm/hr -> 0; 10 mm/hr -> 30; 25 mm/hr (Heavy) -> 65; >= 50 mm/hr (Violent) -> 100
        if rainfall <= 0:
            rain_score = 0.0
        elif rainfall < 10.0:
            rain_score = (rainfall / 10.0) * 30.0
        elif rainfall < 25.0:
            rain_score = 30.0 + ((rainfall - 10.0) / 15.0) * 35.0
        else:
            rain_score = min(100.0, 65.0 + ((rainfall - 25.0) / 25.0) * 35.0)

        # 4. Soil Moisture Factor (0-100)
        # < 60% -> low (0-20), 60-80% -> moderate (20-60), 80-100% -> saturated (60-100)
        if soil_moisture < 60.0:
            soil_score = max(0.0, (soil_moisture / 60.0) * 20.0)
        elif soil_moisture < 80.0:
            soil_score = 20.0 + ((soil_moisture - 60.0) / 20.0) * 40.0
        else:
            soil_score = min(100.0, 60.0 + ((soil_moisture - 80.0) / 20.0) * 40.0)

        # 5. Forecast Factor (0-100)
        # < 20mm -> 0-20, 20-60mm -> 20-60, >= 100mm -> 100
        forecast_score = min(100.0, max(0.0, (forecast_rain_mm / 100.0) * 100.0))

        # Weights
        w_water = 0.35
        w_rise = 0.25
        w_rain = 0.15
        w_soil = 0.15
        w_forecast = 0.10

        overall_score = round(
            (water_score * w_water) +
            (rise_score * w_rise) +
            (rain_score * w_rain) +
            (soil_score * w_soil) +
            (forecast_score * w_forecast),
            1
        )

        # Determine level
        if overall_score >= 80.0 or water_level >= danger_threshold:
            overall_level = "CRITICAL"
            status_label = "Critical Flood Risk"
            status_description = "Extreme danger of overflowing. Evacuation protocols and emergency services alerted."
        elif overall_score >= 60.0 or water_level >= warning_threshold:
            overall_level = "HIGH"
            status_label = "High Flood Risk"
            status_description = "River levels near or exceeding warning threshold. Continuous monitoring required."
        elif overall_score >= 35.0:
            overall_level = "MODERATE"
            status_label = "Moderate Risk"
            status_description = "Elevated moisture and rainfall conditions. Catchment capacity decreasing."
        else:
            overall_level = "LOW"
            status_label = "Low Risk"
            status_description = "No immediate flood risk. All hydrological indicators within safe operating parameters."

        def get_contribution(score: float) -> str:
            if score >= 75.0:
                return "Very High"
            elif score >= 50.0:
                return "High"
            elif score >= 25.0:
                return "Moderate"
            return "Low"

        factors = {
            "water_level": {
                "factor_name": "Water Level vs Threshold",
                "score": round(water_score, 1),
                "contribution": get_contribution(water_score),
                "weight": w_water,
                "description": f"Level at {water_level:.2f}m (Warning: {warning_threshold:.1f}m, Danger: {danger_threshold:.1f}m)"
            },
            "rise_rate": {
                "factor_name": "Surge / Rise Rate",
                "score": round(rise_score, 1),
                "contribution": get_contribution(rise_score),
                "weight": w_rise,
                "description": f"Current rate {water_rise_rate:+.2f} m/hr"
            },
            "rainfall": {
                "factor_name": "Current Precipitation",
                "score": round(rain_score, 1),
                "contribution": get_contribution(rain_score),
                "weight": w_rain,
                "description": f"Rainfall rate {rainfall:.1f} mm/hr"
            },
            "soil_moisture": {
                "factor_name": "Catchment Soil Moisture",
                "score": round(soil_score, 1),
                "contribution": get_contribution(soil_score),
                "weight": w_soil,
                "description": f"Saturation at {soil_moisture:.1f}%"
            },
            "forecast": {
                "factor_name": "24h Rain Forecast",
                "score": round(forecast_score, 1),
                "contribution": get_contribution(forecast_score),
                "weight": w_forecast,
                "description": f"Projected 24h accumulation {forecast_rain_mm:.1f} mm"
            }
        }

        return RiskAssessmentOutput(
            sensor_id=sensor_id,
            overall_score=overall_score,
            overall_level=overall_level,
            status_label=status_label,
            status_description=status_description,
            factors=factors,
            assessed_at=utcnow()
        )

    def calculate_basin_risk(
        self,
        avg_water_level: float,
        max_water_level: float,
        avg_rise_rate: float,
        current_rainfall: float,
        soil_moisture: float,
        forecast_24h_rainfall: float
    ) -> RiskAssessmentOutput:
        # Basin-wide composite
        return self.calculate_sensor_risk(
            water_level=(avg_water_level * 0.4 + max_water_level * 0.6),
            water_rise_rate=avg_rise_rate,
            rainfall=current_rainfall,
            soil_moisture=soil_moisture,
            warning_threshold=3.0,
            danger_threshold=4.0,
            forecast_rain_mm=forecast_24h_rainfall,
            sensor_id="BASIN-WIDE"
        )


# Singleton instance
risk_engine = RuleBasedRiskEngine()
