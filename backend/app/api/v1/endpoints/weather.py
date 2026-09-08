from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.schemas import WeatherCurrentResponse, WeatherForecastSummary
from app.services.weather_service import weather_service

router = APIRouter()


@router.get("/current", response_model=WeatherCurrentResponse)
def get_current_weather(db: Session = Depends(get_db)):
    return weather_service.get_current_weather(db)


@router.get("/forecast", response_model=WeatherForecastSummary)
def get_weather_forecast(db: Session = Depends(get_db)):
    return weather_service.get_forecast_summary(db)
