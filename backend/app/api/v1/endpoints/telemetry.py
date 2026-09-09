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


@router.post("/esp32", response_model=Any)
async def ingest_real_esp32_reading(
    payload: dict,
    db: Session = Depends(get_db)
):
    """
    Direct ingestion endpoint for Real Physical ESP32 BLE telemetry.
    Accepts raw output from ble_test.py or direct BLE listener.
    """
    reading, calibrated, alerts = await telemetry_service.process_real_esp32_telemetry(db=db, raw_data=payload)
    return {
        "status": "success",
        "device_id": "ESP32-FW-001",
        "reading_id": reading.id,
        "calibrated": calibrated,
        "alerts_triggered": len(alerts),
        "alerts": alerts
    }


@router.get("/latest", response_model=Any)
async def get_latest_esp32_telemetry(db: Session = Depends(get_db)):
    """
    Returns latest real ESP32 BLE telemetry with calibration and live connectivity status.
    If no packet in > 15s, returns STALE/OFFLINE.
    """
    from app.services.ble_collector import ble_collector
    from app.models.models import SensorReading

    live_state = ble_collector.get_latest_telemetry_payload()

    # If in-memory state is empty (e.g. server restarted), check latest DB reading
    if live_state.get("water_raw") is None:
        last_reading = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == "FW-001", SensorReading.water_raw.isnot(None))
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        if last_reading:
            live_state["water_raw"] = last_reading.water_raw
            live_state["water_level_cm"] = last_reading.water_level_cm
            live_state["water_percentage"] = last_reading.water_percentage
            live_state["rain_raw"] = last_reading.rain_raw
            live_state["rain_percentage"] = last_reading.rain_percentage
            live_state["rain_intensity"] = last_reading.rain_intensity
            live_state["timestamp"] = last_reading.timestamp.isoformat() if last_reading.timestamp else None
            live_state["calibration_status"] = "CALIBRATED"
            live_state["message"] = "ESP32 OFFLINE — Historical baseline loaded"

    return live_state


@router.get("/history", response_model=Any)
async def get_esp32_telemetry_history(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Returns real calibrated ESP32 readings for charting.
    """
    from app.models.models import SensorReading

    readings = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == "FW-001")
        .order_by(SensorReading.timestamp.desc())
        .limit(limit)
        .all()
    )

    items = []
    for r in reversed(readings):
        items.append({
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "water_raw": r.water_raw,
            "water_level_cm": r.water_level_cm if r.water_level_cm is not None else r.water_level,
            "water_percentage": r.water_percentage,
            "rain_raw": r.rain_raw,
            "rain_intensity": r.rain_intensity if r.rain_intensity is not None else r.rainfall,
            "rain_percentage": r.rain_percentage,
            "rise_rate_cm_min": r.water_rise_rate,
            "bluetooth_status": r.bluetooth_status or "ONLINE",
            "calibration_status": r.calibration_status or "CALIBRATED"
        })

    return {"status": "success", "count": len(items), "readings": items}
