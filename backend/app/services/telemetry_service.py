import logging
from datetime import datetime, timezone, timedelta
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
                location_name="Chaulkhowa River Basin, Barpeta, Assam",
                latitude=26.3200,
                longitude=91.0050,
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

    @staticmethod
    async def process_real_esp32_telemetry(db: Session, raw_data: dict) -> Tuple[SensorReading, dict, List[dict]]:
        from app.services.ble_collector import ble_collector
        from app.models.models import Alert

        now = utcnow()
        calibrated = ble_collector.ingest_payload(raw_data)
        water_cm = calibrated["water_level_cm"]
        water_raw = calibrated["water_raw"]
        rain_intensity = calibrated["rain_intensity"]
        rain_raw = calibrated["rain_raw"]
        rise_rate = calibrated.get("rise_rate_cm_min", 0.0)
        risk_level = calibrated["flood_risk_level"]

        # 1. Fetch or create Barpeta prototype sensor FW-001
        sensor = db.query(Sensor).filter(Sensor.sensor_id == "FW-001").first()
        if not sensor:
            sensor = Sensor(
                sensor_id="FW-001",
                name="Barpeta Station FW-001",
                location_name="Chaulkhowa River Basin, Barpeta, Assam",
                latitude=26.3200,
                longitude=91.0050,
                status=risk_level,
                warning_threshold=6.0,
                danger_threshold=10.0,
                created_at=now,
            )
            db.add(sensor)
            db.flush()

        # Update sensor live values
        sensor.status = risk_level
        sensor.current_water_level = water_cm
        sensor.water_rise_rate = rise_rate
        sensor.last_seen = now
        sensor.updated_at = now

        # 2. Persist SensorReading with real ESP32 ADC & calibrated values
        reading = SensorReading(
            sensor_id=sensor.sensor_id,
            water_level=water_cm,
            water_level_cm=water_cm,
            water_raw=water_raw,
            water_percentage=calibrated.get("water_percentage", 0.0),
            water_rise_rate=rise_rate,
            rainfall=rain_intensity,
            rain_intensity=rain_intensity,
            rain_raw=rain_raw,
            rain_percentage=calibrated.get("rain_percentage", 0.0),
            soil_moisture=calibrated.get("water_percentage", 0.0),
            temperature=27.0,
            battery=82.0,
            signal_strength=-65.0,
            inclination_x=0.0,
            inclination_y=0.0,
            bluetooth_status="ONLINE",
            calibration_status="CALIBRATED",
            timestamp=now,
            created_at=now,
        )
        db.add(reading)
        db.flush()

        # 3. State-change alert generation (Warning > 6cm, Danger > 10cm, Critical > 13cm)
        triggered_alerts = []
        alert_spec = None
        if water_cm >= 13.0:
            alert_spec = {
                "type": "CRITICAL_FLOOD_LEVEL",
                "severity": "CRITICAL",
                "title": "Critical Prototype Flood Threshold Exceeded",
                "message": f"Real ESP32 water level reached {water_cm:.2f} cm (critical threshold 13.0 cm exceeded)",
            }
        elif water_cm >= 10.0:
            alert_spec = {
                "type": "DANGER_FLOOD_LEVEL",
                "severity": "CRITICAL",
                "title": "Danger Prototype Flood Threshold Exceeded",
                "message": f"Real ESP32 water level reached {water_cm:.2f} cm (danger threshold 10.0 cm exceeded)",
            }
        elif water_cm >= 6.0:
            alert_spec = {
                "type": "WARNING_FLOOD_LEVEL",
                "severity": "WARNING",
                "title": "Warning Prototype Threshold Reached",
                "message": f"Real ESP32 water level reached {water_cm:.2f} cm (warning threshold 6.0 cm reached)",
            }

        if alert_spec:
            # Check if recently triggered within 60s to prevent spamming
            recent_alert = (
                db.query(Alert)
                .filter(
                    Alert.sensor_id == sensor.sensor_id,
                    Alert.type == alert_spec["type"],
                    Alert.status == "ACTIVE",
                    Alert.created_at >= now - timedelta(seconds=60),
                )
                .first()
            )
            if not recent_alert:
                new_alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type=alert_spec["type"],
                    severity=alert_spec["severity"],
                    title=alert_spec["title"],
                    message=alert_spec["message"],
                    status="ACTIVE",
                    is_read=False,
                    created_at=now,
                )
                db.add(new_alert)
                db.flush()
                triggered_alerts.append(new_alert)

        db.commit()
        db.refresh(reading)

        # 4. Generate ML Multi-Horizon Prediction for real ESP32 observation
        ml_data = {}
        try:
            ml_data = ml_predictor.predict_and_store(
                db=db,
                sensor_id=sensor.sensor_id,
                current_reading=reading,
                warning_threshold=sensor.warning_threshold,
                danger_threshold=sensor.danger_threshold,
            )
        except Exception as e:
            logger.warning(f"ML prediction error during real ESP32 processing: {e}")

        # 5. Broadcast live WebSocket event
        alerts_payload = [
            {
                "id": a.id,
                "sensor_id": a.sensor_id,
                "type": a.type,
                "severity": a.severity,
                "title": a.title,
                "message": a.message,
                "created_at": a.created_at.isoformat(),
            }
            for a in triggered_alerts
        ]

        ws_payload = {
            "type": "ESP32_TELEMETRY",
            "event": "telemetry_update",
            "device_id": "FW-001",
            "timestamp": reading.timestamp.isoformat(),
            "water_raw": water_raw,
            "water_level_cm": water_cm,
            "rain_raw": rain_raw,
            "rain_intensity": rain_intensity,
            "source": "ESP32_BLE",
            "sensor": {
                "sensor_id": sensor.sensor_id,
                "name": sensor.name,
                "water_level": water_cm,
                "water_level_cm": water_cm,
                "rise_rate": rise_rate,
                "status": sensor.status,
                "battery": sensor.battery,
                "last_seen": sensor.last_seen.isoformat(),
            },
            "reading": {
                "id": reading.id,
                "water_level": water_cm,
                "water_level_cm": water_cm,
                "water_raw": water_raw,
                "rainfall": rain_intensity,
                "rain_intensity": rain_intensity,
                "rain_raw": rain_raw,
                "timestamp": reading.timestamp.isoformat(),
            },
            "real_telemetry": calibrated,
            "alerts": alerts_payload,
            "risk": {
                "score": calibrated["flood_risk_score"],
                "level": calibrated["flood_risk_level"],
                "text": calibrated["flood_risk_text"],
            },
            "ml": ml_data,
        }

        try:
            await ws_manager.broadcast(ws_payload)
            print("\n[TELEMETRY] Received ESP32 packet")
            print(f"[TELEMETRY] Water: {water_cm:.2f} cm")
            print(f"[TELEMETRY] Rain: {rain_intensity:.1f}/10")
            print("[TELEMETRY] Database saved")
            print("[TELEMETRY] WebSocket broadcast\n")
            logger.info(f"[ESP32 BLE] Packet processed: Water Raw {water_raw} -> {water_cm:.2f} cm, Rain Raw {rain_raw} -> {rain_intensity:.1f}/10")
        except Exception as e:
            logger.warning(f"Failed to broadcast real ESP32 WebSocket payload: {e}")

        return reading, calibrated, alerts_payload


telemetry_service = TelemetryService()
