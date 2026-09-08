from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import Alert, AlertHistory, Sensor
from app.core.config import settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AlertService:
    @staticmethod
    def evaluate_reading_for_alerts(db: Session, sensor: Sensor, water_level: float, rise_rate: float, battery: float, tilt_x: float, tilt_y: float) -> List[Alert]:
        new_alerts = []
        now = utcnow()

        # Helper to check if active alert of this type already exists for this sensor
        def has_active_alert(alert_type: str) -> bool:
            return db.query(Alert).filter(
                Alert.sensor_id == sensor.sensor_id,
                Alert.type == alert_type,
                Alert.status.in_(["ACTIVE", "ACKNOWLEDGED"])
            ).first() is not None

        # 1. Critical Danger Level Breached
        if water_level >= sensor.danger_threshold:
            if not has_active_alert("HIGH_WATER_LEVEL_DANGER"):
                alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type="HIGH_WATER_LEVEL_DANGER",
                    severity="CRITICAL",
                    title=f"Critical high water level at {sensor.name}",
                    message=f"Water level reached {water_level:.2f} m, exceeding danger threshold ({sensor.danger_threshold:.1f} m).",
                    status="ACTIVE",
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                db.flush()
                db.add(AlertHistory(alert_id=alert.id, action="CREATED", details="Automatic threshold breach detection", timestamp=now))
                new_alerts.append(alert)

        # 2. Warning Level Breached (only if not already in danger)
        elif water_level >= sensor.warning_threshold:
            if not has_active_alert("HIGH_WATER_LEVEL_WARNING"):
                alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type="HIGH_WATER_LEVEL_WARNING",
                    severity="WARNING",
                    title=f"Warning water level at {sensor.name}",
                    message=f"Water level reached {water_level:.2f} m, exceeding warning threshold ({sensor.warning_threshold:.1f} m).",
                    status="ACTIVE",
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                db.flush()
                db.add(AlertHistory(alert_id=alert.id, action="CREATED", details="Automatic warning threshold breach", timestamp=now))
                new_alerts.append(alert)

        # 3. Rapid Water Rise Rate (> 0.20 m/hr)
        if rise_rate >= settings.RAPID_RISE_THRESHOLD_M_PER_HR:
            if not has_active_alert("RAPID_WATER_RISE"):
                alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type="RAPID_WATER_RISE",
                    severity="WARNING",
                    title=f"Rapid rise detected ({sensor.name})",
                    message=f"Water level increased by {rise_rate:+.2f} m/hr exceeding safe surge velocity.",
                    status="ACTIVE",
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                db.flush()
                db.add(AlertHistory(alert_id=alert.id, action="CREATED", details="Fast surge velocity triggered", timestamp=now))
                new_alerts.append(alert)

        # 4. Low Battery (< 20%)
        if battery <= settings.LOW_BATTERY_PERCENT:
            if not has_active_alert("LOW_BATTERY"):
                alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type="LOW_BATTERY",
                    severity="INFO",
                    title=f"Low battery at {sensor.name}",
                    message=f"Telemetry unit battery at {battery:.1f}%. Maintenance dispatch advised.",
                    status="ACTIVE",
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                db.flush()
                db.add(AlertHistory(alert_id=alert.id, action="CREATED", details="Battery telemetry depleted", timestamp=now))
                new_alerts.append(alert)

        # 5. Sensor Post Tilt (> 15 deg)
        tilt_magnitude = (tilt_x**2 + tilt_y**2)**0.5
        if tilt_magnitude >= settings.SENSOR_TILT_THRESHOLD_DEG:
            if not has_active_alert("SENSOR_TILT"):
                alert = Alert(
                    sensor_id=sensor.sensor_id,
                    type="SENSOR_TILT",
                    severity="WARNING",
                    title=f"Structural tilt at {sensor.name}",
                    message=f"Mounting pole inclination measured at {tilt_magnitude:.1f}°. Possible debris impact or soil displacement.",
                    status="ACTIVE",
                    is_read=False,
                    created_at=now
                )
                db.add(alert)
                db.flush()
                db.add(AlertHistory(alert_id=alert.id, action="CREATED", details="Accelerometer inclination threshold exceeded", timestamp=now))
                new_alerts.append(alert)

        return new_alerts

    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_name: str = "Operator") -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        now = utcnow()
        alert.status = "ACKNOWLEDGED"
        alert.is_read = True
        db.add(AlertHistory(alert_id=alert.id, action="ACKNOWLEDGED", details=f"Acknowledged by {user_name}", timestamp=now))
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def resolve_alert(db: Session, alert_id: int, resolved_by: str = "Administrator", notes: Optional[str] = None) -> Optional[Alert]:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            return None
        now = utcnow()
        alert.status = "RESOLVED"
        alert.is_read = True
        alert.resolved_at = now
        alert.resolved_by = resolved_by
        details = f"Resolved by {resolved_by}. {notes or ''}".strip()
        db.add(AlertHistory(alert_id=alert.id, action="RESOLVED", details=details, timestamp=now))
        db.commit()
        db.refresh(alert)
        return alert


alert_service = AlertService()
