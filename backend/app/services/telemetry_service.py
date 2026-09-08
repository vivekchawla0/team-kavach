import logging
from datetime import datetime, timezone
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.models.models import Sensor, SensorReading, FloodRiskAssessment
from app.schemas.schemas import SensorReadingCreate
from app.services.alert_service import alert_service
from app.services.risk_engine.engine import risk_engine
from app.services.ml.predictor import ml_predictor
from app.core.websocket import ws_manager

logger = logging.getLogger(__name__)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TelemetryService:
    @staticmethod
    async def process_telemetry(db: Session, data: SensorReadingCreate) -> Tuple[SensorReading, List[dict]]:
        now = data.timestamp or utcnow()

        # 1. Fetch sensor
        sensor = db.query(Sensor).filter(Sensor.sensor_id == data.sensor_id).first()
        if not sensor:
            # Auto-register sensor if new
            sensor = Sensor(
                sensor_id=data.sensor_id,
                name=f"Sensor {data.sensor_id}",
                location_name="Erft River Basin",
                latitude=50.5539,
                longitude=6.7633,
                status="NORMAL",
                warning_threshold=3.0,
                danger_threshold=4.0,
                created_at=now
            )
            db.add(sensor)
            db.flush()

        # 2. Compute dynamic rise rate if omitted
        rise_rate = data.water_rise_rate
        if rise_rate is None:
            prev_reading = (
                db.query(SensorReading)
                .filter(SensorReading.sensor_id == sensor.sensor_id)
                .order_by(SensorReading.timestamp.desc())
                .first()
            )
            if prev_reading and prev_reading.timestamp:
                dt_hours = (now - prev_reading.timestamp).total_seconds() / 3600.0
                if dt_hours > 0.005:  # at least ~18 seconds
                    raw_rate = (data.water_level - prev_reading.water_level) / dt_hours
                    rise_rate = round(max(-2.0, min(2.0, raw_rate)), 2)
                else:
                    rise_rate = sensor.water_rise_rate or 0.0
            else:
                rise_rate = 0.0

        # 3. Determine status
        old_status = sensor.status
        if data.water_level >= sensor.danger_threshold:
            new_status = "CRITICAL"
        elif data.water_level >= sensor.warning_threshold or rise_rate >= 0.20:
            new_status = "WARNING"
        else:
            new_status = "NORMAL"

        # Update sensor attributes
        sensor.status = new_status
        sensor.current_water_level = round(data.water_level, 2)
        sensor.water_rise_rate = rise_rate
        sensor.battery = round(data.battery, 1)
        sensor.signal_strength = round(data.signal_strength, 1)
        sensor.inclination_x = round(data.inclination_x, 2)
        sensor.inclination_y = round(data.inclination_y, 2)
        sensor.last_seen = now
        sensor.updated_at = now

        # 4. Save SensorReading record
        reading = SensorReading(
            sensor_id=sensor.sensor_id,
            water_level=round(data.water_level, 2),
            water_rise_rate=rise_rate,
            rainfall=round(data.rainfall, 1),
            soil_moisture=round(data.soil_moisture, 1),
            temperature=round(data.temperature, 1),
            battery=round(data.battery, 1),
            signal_strength=round(data.signal_strength, 1),
            inclination_x=round(data.inclination_x, 2),
            inclination_y=round(data.inclination_y, 2),
            timestamp=now,
            created_at=now
        )
        db.add(reading)
        db.flush()

        # 5. Evaluate Alerts
        triggered_alerts = alert_service.evaluate_reading_for_alerts(
            db=db,
            sensor=sensor,
            water_level=data.water_level,
            rise_rate=rise_rate,
            battery=data.battery,
            tilt_x=data.inclination_x,
            tilt_y=data.inclination_y
        )

        # 6. Run Risk Assessment
        risk_output = risk_engine.calculate_sensor_risk(
            water_level=data.water_level,
            water_rise_rate=rise_rate,
            rainfall=data.rainfall,
            soil_moisture=data.soil_moisture,
            warning_threshold=sensor.warning_threshold,
            danger_threshold=sensor.danger_threshold,
            sensor_id=sensor.sensor_id
        )

        risk_record = FloodRiskAssessment(
            sensor_id=sensor.sensor_id,
            risk_score=risk_output.overall_score,
            risk_level=risk_output.overall_level,
            water_level_score=risk_output.factors["water_level"]["score"],
            rainfall_score=risk_output.factors["rainfall"]["score"],
            soil_moisture_score=risk_output.factors["soil_moisture"]["score"],
            rise_rate_score=risk_output.factors["rise_rate"]["score"],
            forecast_score=risk_output.factors["forecast"]["score"],
            created_at=now
        )
        db.add(risk_record)
        db.commit()
        db.refresh(reading)

        # 7. Run ML Multi-Horizon Predictive Engine (Advisory Only)
        ml_data = {}
        try:
            ml_data = ml_predictor.predict_and_store(
                db=db,
                sensor_id=sensor.sensor_id,
                current_reading=reading,
                warning_threshold=sensor.warning_threshold,
                danger_threshold=sensor.danger_threshold
            )
        except Exception as e:
            logger.warning(f"ML prediction error for sensor {sensor.sensor_id}: {e}")

        # 8. Broadcast update over WebSocket
        alerts_payload = [
            {
                "id": a.id,
                "sensor_id": a.sensor_id,
                "type": a.type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "created_at": a.created_at.isoformat()
            }
            for a in triggered_alerts
        ]

        ws_payload = {
            "event": "telemetry_update",
            "sensor": {
                "sensor_id": sensor.sensor_id,
                "name": sensor.name,
                "water_level": sensor.current_water_level,
                "rise_rate": sensor.water_rise_rate,
                "status": sensor.status,
                "battery": sensor.battery,
                "last_seen": sensor.last_seen.isoformat(),
            },
            "reading": {
                "id": reading.id,
                "water_level": reading.water_level,
                "rainfall": reading.rainfall,
                "soil_moisture": reading.soil_moisture,
                "timestamp": reading.timestamp.isoformat()
            },
            "alerts": alerts_payload,
            "risk": {
                "score": risk_output.overall_score,
                "level": risk_output.overall_level
            },
            "ml": ml_data
        }

        try:
            await ws_manager.broadcast(ws_payload)
        except Exception as e:
            logger.warning(f"Failed to broadcast WebSocket payload: {e}")

        return reading, alerts_payload


telemetry_service = TelemetryService()
