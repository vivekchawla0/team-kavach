from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.models.models import Sensor
from app.schemas.schemas import SensorResponse, SensorCreate, SensorUpdate

router = APIRouter()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.get("", response_model=List[SensorResponse])
@router.get("/", response_model=List[SensorResponse])
def get_sensors(
    status: Optional[str] = Query(None, description="Filter by status: NORMAL, WARNING, CRITICAL, OFFLINE, or ALL"),
    search: Optional[str] = Query(None, description="Search by sensor name, ID or location"),
    db: Session = Depends(get_db)
):
    query = db.query(Sensor)

    if status and status.upper() != "ALL":
        query = query.filter(Sensor.status == status.upper())

    if search:
        term = f"%{search}%"
        query = query.filter(
            or_(
                Sensor.name.ilike(term),
                Sensor.sensor_id.ilike(term),
                Sensor.location_name.ilike(term)
            )
        )

    sensors = query.order_by(Sensor.id.asc()).all()
    return sensors


@router.get("/{sensor_id}", response_model=SensorResponse)
def get_sensor_by_id(sensor_id: str, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(
        or_(Sensor.sensor_id == sensor_id, Sensor.id == int(sensor_id) if sensor_id.isdigit() else False)
    ).first()

    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")
    return sensor


@router.post("/", response_model=SensorResponse, status_code=201)
def create_sensor(sensor_in: SensorCreate, db: Session = Depends(get_db)):
    existing = db.query(Sensor).filter(Sensor.sensor_id == sensor_in.sensor_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Sensor ID '{sensor_in.sensor_id}' already exists")

    now = utcnow()
    sensor = Sensor(
        sensor_id=sensor_in.sensor_id,
        name=sensor_in.name,
        location_name=sensor_in.location_name,
        latitude=sensor_in.latitude,
        longitude=sensor_in.longitude,
        warning_threshold=sensor_in.warning_threshold,
        danger_threshold=sensor_in.danger_threshold,
        status="NORMAL",
        current_water_level=1.0,
        water_rise_rate=0.0,
        battery=100.0,
        signal_strength=-65.0,
        installation_date=now,
        last_seen=now,
        created_at=now,
        updated_at=now
    )
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


@router.put("/{sensor_id}", response_model=SensorResponse)
def update_sensor(sensor_id: str, sensor_in: SensorUpdate, db: Session = Depends(get_db)):
    sensor = db.query(Sensor).filter(
        or_(Sensor.sensor_id == sensor_id, Sensor.id == int(sensor_id) if sensor_id.isdigit() else False)
    ).first()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")

    update_data = sensor_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(sensor, field, val)

    sensor.updated_at = utcnow()
    db.commit()
    db.refresh(sensor)
    return sensor
