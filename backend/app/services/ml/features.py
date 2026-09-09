import os
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.models import SensorReading, WeatherData, WeatherForecast
from app.services.calibration import raw_water_to_cm, raw_rain_to_intensity

logger = logging.getLogger(__name__)

FEATURE_NAMES = [
    "current_water_cm",
    "rise_rate_cm_min",
    "rain_intensity",
    "forecast_1h_mm",
    "forecast_3h_mm",
    "forecast_6h_mm",
    "water_delta_5min",
    "water_delta_10min",
    "rain_mean_5min",
    "rain_mean_10min",
]


def extract_features_for_sensor(
    db: Session,
    sensor_id: str,
    current_reading: Optional[SensorReading] = None,
) -> Dict[str, float]:
    """
    Extracts the 10-dimensional feature vector aligned exactly with the
    trained JAL SUCHAK XGBoost multi-horizon models:
    [
        'current_water_cm',
        'rise_rate_cm_min',
        'rain_intensity',
        'forecast_1h_mm',
        'forecast_3h_mm',
        'forecast_6h_mm',
        'water_delta_5min',
        'water_delta_10min',
        'rain_mean_5min',
        'rain_mean_10min'
    ]
    """
    now = datetime.now(timezone.utc)

    # 1. Obtain current reading if not supplied
    if current_reading is None:
        current_reading = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == sensor_id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

    # Current Water Level (cm)
    if current_reading and getattr(current_reading, "water_level_cm", None) is not None:
        current_water_cm = float(current_reading.water_level_cm)
    elif current_reading and getattr(current_reading, "water_raw", None) is not None:
        current_water_cm = raw_water_to_cm(current_reading.water_raw)
    elif current_reading and getattr(current_reading, "water_level", None) is not None:
        # Fallback if in meters (convert m to cm) or direct cm
        wl = float(current_reading.water_level)
        current_water_cm = wl * 100.0 if wl < 1.0 else wl
    else:
        current_water_cm = 3.00

    # Rain Intensity
    if current_reading and getattr(current_reading, "rain_intensity", None) is not None:
        rain_intensity = float(current_reading.rain_intensity)
    elif current_reading and getattr(current_reading, "rain_raw", None) is not None:
        rain_intensity = raw_rain_to_intensity(current_reading.rain_raw)
    elif current_reading and getattr(current_reading, "rainfall", None) is not None:
        rain_intensity = float(current_reading.rainfall)
    else:
        rain_intensity = 0.0

    reading_time = current_reading.timestamp if current_reading and current_reading.timestamp else now
    if reading_time.tzinfo is None:
        reading_time = reading_time.replace(tzinfo=timezone.utc)

    # 2. Query historical readings in last 15 minutes for delta & rolling stats
    window_start = reading_time - timedelta(minutes=15)
    recent_readings = (
        db.query(SensorReading)
        .filter(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp <= reading_time,
            SensorReading.timestamp >= window_start,
        )
        .order_by(SensorReading.timestamp.desc())
        .limit(60)
        .all()
    )

    # Calculate rise rate (cm/min)
    rise_rate_cm_min = 0.0
    if len(recent_readings) >= 2:
        prev = recent_readings[1]
        prev_time = prev.timestamp if prev.timestamp.tzinfo else prev.timestamp.replace(tzinfo=timezone.utc)
        dt_seconds = (reading_time - prev_time).total_seconds()
        if dt_seconds >= 2:
            prev_cm = (
                float(prev.water_level_cm)
                if getattr(prev, "water_level_cm", None) is not None
                else raw_water_to_cm(prev.water_raw) if getattr(prev, "water_raw", None) is not None
                else float(prev.water_level)
            )
            rise_rate_cm_min = round(((current_water_cm - prev_cm) / dt_seconds) * 60.0, 4)
    elif current_reading and getattr(current_reading, "water_rise_rate", None) is not None:
        rise_rate_cm_min = round(float(current_reading.water_rise_rate), 4)

    # 3. Deltas: water_delta_5min and water_delta_10min
    target_5m = reading_time - timedelta(minutes=5)
    target_10m = reading_time - timedelta(minutes=10)

    reading_5m = None
    reading_10m = None
    best_diff_5m = timedelta(minutes=3)
    best_diff_10m = timedelta(minutes=5)

    readings_5m_window = []
    readings_10m_window = []

    for r in recent_readings:
        r_time = r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc)
        diff_5 = abs(r_time - target_5m)
        if diff_5 < best_diff_5m:
            best_diff_5m = diff_5
            reading_5m = r

        diff_10 = abs(r_time - target_10m)
        if diff_10 < best_diff_10m:
            best_diff_10m = diff_10
            reading_10m = r

        if r_time >= reading_time - timedelta(minutes=5):
            readings_5m_window.append(r)
        if r_time >= reading_time - timedelta(minutes=10):
            readings_10m_window.append(r)

    if reading_5m:
        val_5m = (
            float(reading_5m.water_level_cm)
            if getattr(reading_5m, "water_level_cm", None) is not None
            else raw_water_to_cm(reading_5m.water_raw) if getattr(reading_5m, "water_raw", None) is not None
            else float(reading_5m.water_level)
        )
        water_delta_5min = round(current_water_cm - val_5m, 3)
    else:
        water_delta_5min = round(rise_rate_cm_min * 5.0, 3)

    if reading_10m:
        val_10m = (
            float(reading_10m.water_level_cm)
            if getattr(reading_10m, "water_level_cm", None) is not None
            else raw_water_to_cm(reading_10m.water_raw) if getattr(reading_10m, "water_raw", None) is not None
            else float(reading_10m.water_level)
        )
        water_delta_10min = round(current_water_cm - val_10m, 3)
    else:
        water_delta_10min = round(rise_rate_cm_min * 10.0, 3)

    # 4. Means: rain_mean_5min and rain_mean_10min
    def get_rain_val(r):
        if getattr(r, "rain_intensity", None) is not None:
            return float(r.rain_intensity)
        if getattr(r, "rain_raw", None) is not None:
            return raw_rain_to_intensity(r.rain_raw)
        return float(r.rainfall or 0.0)

    if readings_5m_window:
        vals_5m = [get_rain_val(r) for r in readings_5m_window]
        rain_mean_5min = round(sum(vals_5m) / len(vals_5m), 2)
    else:
        rain_mean_5min = round(rain_intensity, 2)

    if readings_10m_window:
        vals_10m = [get_rain_val(r) for r in readings_10m_window]
        rain_mean_10min = round(sum(vals_10m) / len(vals_10m), 2)
    else:
        rain_mean_10min = round(rain_intensity, 2)

    # 5. Weather forecast values for Barpeta, Assam (forecast_1h_mm, forecast_3h_mm, forecast_6h_mm)
    forecasts = (
        db.query(WeatherForecast)
        .filter(WeatherForecast.forecast_time >= now - timedelta(minutes=30))
        .order_by(WeatherForecast.forecast_time.asc())
        .limit(12)
        .all()
    )

    if forecasts:
        # Calculate rainfall for 1h, 3h, 6h
        f1_list = [f.expected_rainfall_mm for f in forecasts if f.forecast_time <= now + timedelta(hours=1.5)]
        f3_list = [f.expected_rainfall_mm for f in forecasts if f.forecast_time <= now + timedelta(hours=3.5)]
        f6_list = [f.expected_rainfall_mm for f in forecasts if f.forecast_time <= now + timedelta(hours=6.5)]

        forecast_1h_mm = round(f1_list[0] if f1_list else (forecasts[0].expected_rainfall_mm if forecasts else 2.5), 1)
        forecast_3h_mm = round(sum(f3_list) if f3_list else forecast_1h_mm * 2.0, 1)
        forecast_6h_mm = round(sum(f6_list) if f6_list else forecast_3h_mm * 2.2, 1)
    else:
        # Realistic Barpeta monsoon baseline if DB forecast table not populated
        forecast_1h_mm = 2.5
        forecast_3h_mm = 6.0
        forecast_6h_mm = 14.0

    return {
        "current_water_cm": round(current_water_cm, 2),
        "rise_rate_cm_min": round(rise_rate_cm_min, 4),
        "rain_intensity": round(rain_intensity, 2),
        "forecast_1h_mm": float(forecast_1h_mm),
        "forecast_3h_mm": float(forecast_3h_mm),
        "forecast_6h_mm": float(forecast_6h_mm),
        "water_delta_5min": float(water_delta_5min),
        "water_delta_10min": float(water_delta_10min),
        "rain_mean_5min": float(rain_mean_5min),
        "rain_mean_10min": float(rain_mean_10min),
    }
