import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Sensor, WeatherData, Alert, SensorReading
from app.services.alert_service import alert_service
from app.core.websocket import ws_manager

router = APIRouter()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/scenario")
async def trigger_scenario(
    scenario: str = Query("normal", description="Scenario type: normal, storm, flood, reset"),
    db: Session = Depends(get_db)
):
    now = utcnow()
    sensors = db.query(Sensor).all()
    weather = db.query(WeatherData).order_by(WeatherData.recorded_at.desc()).first()

    scenario = scenario.lower()

    if scenario == "normal":
        if weather:
            weather.rainfall_current = 2.0
            weather.weather_condition = "Partly Cloudy"
            weather.temperature = 14.0
            weather.recorded_at = now

        for s in sensors:
            if s.status != "OFFLINE":
                s.current_water_level = round(random.uniform(0.80, 1.45), 2)
                s.water_rise_rate = round(random.uniform(-0.02, 0.02), 2)
                s.status = "NORMAL"
                s.last_seen = now

    elif scenario == "storm":
        if weather:
            weather.rainfall_current = 32.0
            weather.weather_condition = "Heavy Rain"
            weather.temperature = 11.0
            weather.recorded_at = now

        for s in sensors:
            if s.status != "OFFLINE":
                s.current_water_level = round(random.uniform(2.20, 2.95), 2)
                s.water_rise_rate = round(random.uniform(0.10, 0.18), 2)
                s.status = "WARNING" if s.current_water_level >= s.warning_threshold else "NORMAL"
                s.last_seen = now

    elif scenario == "flood":
        if weather:
            weather.rainfall_current = 65.0
            weather.weather_condition = "Severe Torrential Rain"
            weather.temperature = 10.0
            weather.recorded_at = now

        for s in sensors:
            if s.status != "OFFLINE":
                if s.sensor_id in ["FW-004", "FW-007", "FW-003"]:
                    s.current_water_level = round(random.uniform(4.05, 4.40), 2)
                    s.water_rise_rate = round(random.uniform(0.35, 0.55), 2)
                    s.status = "CRITICAL"
                else:
                    s.current_water_level = round(random.uniform(2.85, 3.45), 2)
                    s.water_rise_rate = round(random.uniform(0.20, 0.30), 2)
                    s.status = "WARNING"
                s.last_seen = now

                # Evaluate alerts
                alert_service.evaluate_reading_for_alerts(
                    db=db,
                    sensor=s,
                    water_level=s.current_water_level,
                    rise_rate=s.water_rise_rate,
                    battery=s.battery,
                    tilt_x=s.inclination_x,
                    tilt_y=s.inclination_y
                )

    elif scenario == "reset":
        # Restore reference image baseline
        baseline = {
            "FW-001": (1.12, 0.02, "NORMAL"),
            "FW-002": (0.98, 0.01, "NORMAL"),
            "FW-003": (2.84, 0.12, "WARNING"),
            "FW-004": (3.21, 0.18, "CRITICAL"),
            "FW-005": (1.45, 0.04, "NORMAL"),
            "FW-006": (1.30, 0.02, "NORMAL"),
            "FW-007": (3.21, 0.15, "CRITICAL"),
            "FW-008": (1.15, 0.01, "NORMAL"),
            "FW-009": (1.05, 0.00, "NORMAL"),
            "FW-010": (2.75, 0.10, "WARNING"),
            "FW-011": (1.40, 0.03, "NORMAL"),
            "FW-012": (0.00, 0.00, "OFFLINE"),
            "FW-013": (2.65, 0.08, "WARNING"),
        }
        for s in sensors:
            if s.sensor_id in baseline:
                lvl, rr, st = baseline[s.sensor_id]
                s.current_water_level = lvl
                s.water_rise_rate = rr
                s.status = st
                s.last_seen = now

        if weather:
            weather.rainfall_current = 18.0
            weather.weather_condition = "Light Rain"
            weather.temperature = 12.0
            weather.recorded_at = now

    db.commit()

    # Broadcast scenario change
    await ws_manager.broadcast({
        "event": "scenario_changed",
        "scenario": scenario,
        "timestamp": now.isoformat()
    })

    return {"status": "success", "scenario": scenario, "applied_to_sensors": len(sensors)}
