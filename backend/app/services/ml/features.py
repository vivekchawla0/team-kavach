import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import SensorReading, WeatherData

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "water_level",
    "water_level_lag1",
    "water_level_lag2",
    "water_level_lag3",
    "water_rise_rate_1h",
    "water_rise_rate_3h",
    "rain_1h",
    "rain_3h_sum",
    "rain_6h_sum",
    "rain_12h_sum",
    "rain_24h_sum",
    "api_index",
    "soil_moisture_pct",
    "temperature_2m",
    "relative_humidity_2m",
    "surface_pressure",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos"
]


def extract_features_for_sensor(
    db: Session,
    sensor_id: str,
    current_reading: SensorReading
) -> Dict[str, float]:
    """
    Extracts the 20-dimensional feature vector aligned exactly with the trained
    Phase 4B XGBoost models.
    """
    now = current_reading.timestamp or datetime.now(timezone.utc)
    wl = float(current_reading.water_level)
    rain = float(current_reading.rainfall)
    soil = float(current_reading.soil_moisture) if current_reading.soil_moisture else 45.0
    temp = float(current_reading.temperature) if current_reading.temperature else 12.0

    # 1. Fetch recent readings for lag and rolling sums (last 24 hours)
    past_24h = now - timedelta(hours=25)
    recent_readings: List[SensorReading] = (
        db.query(SensorReading)
        .filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp <= now,
            SensorReading.timestamp >= past_24h
        )
        .order_by(SensorReading.timestamp.desc())
        .all()
    )

    # Lags calculation
    # If insufficient history exists (cold start), estimate from current water level and rise rate
    rise_rate = float(current_reading.water_rise_rate) if current_reading.water_rise_rate is not None else 0.0

    lag1 = wl - (rise_rate * 1.0)
    lag2 = wl - (rise_rate * 2.0)
    lag3 = wl - (rise_rate * 3.0)

    # Search for actual historical readings closest to 1h, 2h, 3h ago
    target_1h = now - timedelta(hours=1)
    target_2h = now - timedelta(hours=2)
    target_3h = now - timedelta(hours=3)

    best_diff_1h = timedelta(minutes=45)
    best_diff_2h = timedelta(minutes=45)
    best_diff_3h = timedelta(minutes=45)

    for r in recent_readings:
        diff_1h = abs(r.timestamp - target_1h)
        if diff_1h < best_diff_1h:
            best_diff_1h = diff_1h
            lag1 = float(r.water_level)

        diff_2h = abs(r.timestamp - target_2h)
        if diff_2h < best_diff_2h:
            best_diff_2h = diff_2h
            lag2 = float(r.water_level)

        diff_3h = abs(r.timestamp - target_3h)
        if diff_3h < best_diff_3h:
            best_diff_3h = diff_3h
            lag3 = float(r.water_level)

    # Ensure physical floor
    lag1 = max(0.05, lag1)
    lag2 = max(0.05, lag2)
    lag3 = max(0.05, lag3)

    rise_1h = wl - lag1
    rise_3h = wl - lag3

    # Rolling rainfall sums
    rain_3h = rain
    rain_6h = rain
    rain_12h = rain
    rain_24h = rain

    t_3h = now - timedelta(hours=3)
    t_6h = now - timedelta(hours=6)
    t_12h = now - timedelta(hours=12)
    t_24h = now - timedelta(hours=24)

    if len(recent_readings) > 1:
        # Sum readings within windows
        sum_3 = sum(float(r.rainfall) for r in recent_readings if r.timestamp >= t_3h)
        sum_6 = sum(float(r.rainfall) for r in recent_readings if r.timestamp >= t_6h)
        sum_12 = sum(float(r.rainfall) for r in recent_readings if r.timestamp >= t_12h)
        sum_24 = sum(float(r.rainfall) for r in recent_readings if r.timestamp >= t_24h)
        
        rain_3h = max(rain, sum_3)
        rain_6h = max(rain_3h, sum_6)
        rain_12h = max(rain_6h, sum_12)
        rain_24h = max(rain_12h, sum_24)
    else:
        # Cold-start fallback estimate
        rain_3h = rain * 2.5
        rain_6h = rain * 4.5
        rain_12h = rain * 8.0
        rain_24h = rain * 12.0

    # Antecedent Precipitation Index (API): API_t = API_{t-1} * 0.90 + P_t
    # Approximated by exponentially weighted rainfall decay
    api_index = (rain * 1.0) + (rain_3h * 0.85) + (rain_6h * 0.70) + (rain_24h * 0.40)

    # 2. Weather context from WeatherData table if available
    latest_weather = db.query(WeatherData).order_by(WeatherData.recorded_at.desc()).first()
    if latest_weather:
        rel_humidity = float(latest_weather.humidity)
        surface_pressure = float(latest_weather.atmospheric_pressure)
    else:
        rel_humidity = 80.0
        surface_pressure = 1013.25

    # 3. Cyclical temporal features
    hour = now.hour + (now.minute / 60.0)
    month = now.month

    hour_sin = math.sin(2.0 * math.pi * hour / 24.0)
    hour_cos = math.cos(2.0 * math.pi * hour / 24.0)
    month_sin = math.sin(2.0 * math.pi * (month - 1) / 12.0)
    month_cos = math.cos(2.0 * math.pi * (month - 1) / 12.0)

    features = {
        "water_level": wl,
        "water_level_lag1": lag1,
        "water_level_lag2": lag2,
        "water_level_lag3": lag3,
        "water_rise_rate_1h": rise_1h,
        "water_rise_rate_3h": rise_3h,
        "rain_1h": rain,
        "rain_3h_sum": rain_3h,
        "rain_6h_sum": rain_6h,
        "rain_12h_sum": rain_12h,
        "rain_24h_sum": rain_24h,
        "api_index": api_index,
        "soil_moisture_pct": soil,
        "temperature_2m": temp,
        "relative_humidity_2m": rel_humidity,
        "surface_pressure": surface_pressure,
        "hour_sin": hour_sin,
        "hour_cos": hour_cos,
        "month_sin": month_sin,
        "month_cos": month_cos
    }

    return features
