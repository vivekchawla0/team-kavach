from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.models import Sensor, WeatherData, FloodRiskAssessment
from app.schemas.schemas import FloodRiskResponse
from app.services.risk_engine.engine import risk_engine

router = APIRouter()


@router.get("/basin", response_model=FloodRiskResponse)
def get_basin_risk(db: Session = Depends(get_db)):
    sensors = db.query(Sensor).all()
    if not sensors:
        raise HTTPException(status_code=404, detail="No sensors registered")

    water_levels = [s.current_water_level for s in sensors if s.status != "OFFLINE"]
    rise_rates = [s.water_rise_rate for s in sensors if s.status != "OFFLINE"]

    avg_water = sum(water_levels) / len(water_levels) if water_levels else 1.42
    max_water = max(water_levels) if water_levels else 2.84
    avg_rise = sum(rise_rates) / len(rise_rates) if rise_rates else 0.05

    weather = db.query(WeatherData).order_by(WeatherData.recorded_at.desc()).first()
    rainfall = weather.rainfall_current if weather else 18.0

    risk_output = risk_engine.calculate_basin_risk(
        avg_water_level=avg_water,
        max_water_level=max_water,
        avg_rise_rate=avg_rise,
        current_rainfall=rainfall,
        soil_moisture=92.0,
        forecast_24h_rainfall=120.0
    )

    return risk_output


@router.get("/sensor/{sensor_id}", response_model=FloodRiskResponse)
def get_sensor_risk(sensor_id: str, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")

    weather = db.query(WeatherData).order_by(WeatherData.recorded_at.desc()).first()
    rainfall = weather.rainfall_current if weather else 18.0

    risk_output = risk_engine.calculate_sensor_risk(
        water_level=sensor.current_water_level,
        water_rise_rate=sensor.water_rise_rate,
        rainfall=rainfall,
        soil_moisture=92.0,
        warning_threshold=sensor.warning_threshold,
        danger_threshold=sensor.danger_threshold,
        forecast_rain_mm=120.0,
        sensor_id=sensor.sensor_id
    )

    return risk_output
