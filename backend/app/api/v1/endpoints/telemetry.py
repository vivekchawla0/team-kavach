from typing import List, Any
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.schemas.schemas import SensorReadingCreate, SensorReadingResponse
from app.services.telemetry_service import telemetry_service

router = APIRouter()


async def check_telemetry_auth(x_api_key: str = Header(None)) -> str:
    # Allow local development if key matches or header is explicitly passed
    if not x_api_key:
        # Check if environment is in development
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing 'X-API-Key' header. IoT telemetry requires authentication."
        )
    if x_api_key != settings.IOT_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid IoT API Key."
        )
    return x_api_key


@router.post("", response_model=Any)
@router.post("/", response_model=Any)
async def ingest_sensor_reading(
    reading_in: SensorReadingCreate,
    api_key: str = Depends(check_telemetry_auth),
    db: Session = Depends(get_db)
):
    reading, triggered_alerts = await telemetry_service.process_telemetry(db=db, data=reading_in)
    return {
        "status": "success",
        "reading_id": reading.id,
        "sensor_id": reading.sensor_id,
        "water_level": reading.water_level,
        "water_rise_rate": reading.water_rise_rate,
        "timestamp": reading.timestamp.isoformat(),
        "alerts_triggered": len(triggered_alerts),
        "alerts": triggered_alerts
    }


@router.post("/batch", response_model=Any)
async def ingest_batch_sensor_readings(
    readings: List[SensorReadingCreate],
    api_key: str = Depends(check_telemetry_auth),
    db: Session = Depends(get_db)
):
    results = []
    for r in readings:
        reading, alerts = await telemetry_service.process_telemetry(db=db, data=r)
        results.append({
            "sensor_id": reading.sensor_id,
            "reading_id": reading.id,
            "water_level": reading.water_level,
            "alerts": alerts
        })
    return {"status": "success", "processed": len(results), "items": results}
