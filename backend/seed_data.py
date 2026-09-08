import math
import random
from datetime import datetime, timedelta, timezone
from app.core.database import SessionLocal, engine, Base
from app.models.models import (
    User,
    Sensor,
    SensorReading,
    SensorStatusHistory,
    Alert,
    AlertHistory,
    WeatherData,
    WeatherForecast,
    FloodRiskAssessment,
    SystemSetting,
    Report,
)
from app.core.security import get_password_hash


def utcnow():
    return datetime.now(timezone.utc)


def seed_database():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        existing_count = db.query(Sensor).count()
        if existing_count >= 13:
            print(f"Database already contains {existing_count} sensors. Re-verifying baseline...")
            return

        print("Seeding FLOODWATCH database with 13 Bad Münstereifel river sensors and realistic telemetry...")

        # 1. Admin User
        admin_user = db.query(User).filter(User.email == "admin@floodwatch.gov.de").first()
        if not admin_user:
            admin_user = User(
                email="admin@floodwatch.gov.de",
                hashed_password=get_password_hash("Admin@FloodWatch2026"),
                full_name="Vivek Chawla",
                role="ADMIN",
                is_active=True,
                created_at=utcnow(),
            )
            db.add(admin_user)

        # 2. Single Physical Prototype Station at Barpeta, Assam
        sensor_configs = [
            {
                "sensor_id": "FW-001",
                "name": "Barpeta Station FW-001",
                "location_name": "Chaulkhowa River Basin, Barpeta, Assam",
                "latitude": 26.3200,
                "longitude": 91.0050,
                "status": "CRITICAL",
                "current_water_level": 3.17,
                "water_rise_rate": 0.24,
                "battery": 82.0,
                "signal_strength": -68.0,
                "warning_threshold": 3.0,
                "danger_threshold": 4.0,
            },
        ]

        # Prototype summary: 1 Online • 0 Offline
        # Barpeta Station FW-001 (Assam, India)

        now = utcnow()
        for conf in sensor_configs:
            last_seen_time = now - timedelta(hours=3) if conf["status"] == "OFFLINE" else now - timedelta(minutes=random.randint(1, 4))
            sensor = Sensor(
                sensor_id=conf["sensor_id"],
                name=conf["name"],
                location_name=conf["location_name"],
                latitude=conf["latitude"],
                longitude=conf["longitude"],
                status=conf["status"],
                warning_threshold=conf["warning_threshold"],
                danger_threshold=conf["danger_threshold"],
                current_water_level=conf["current_water_level"],
                water_rise_rate=conf["water_rise_rate"],
                battery=conf["battery"],
                signal_strength=conf["signal_strength"],
                inclination_x=0.2 if conf["status"] == "CRITICAL" else 0.0,
                inclination_y=0.4 if conf["status"] == "CRITICAL" else 0.0,
                installation_date=now - timedelta(days=180),
                last_seen=last_seen_time,
                created_at=now - timedelta(days=180),
                updated_at=last_seen_time,
            )
            db.add(sensor)

        db.commit()

        # 3. Historical Telemetry for all sensors (especially FW-005, FW-007, FW-003)
        print("Generating 30-day realistic hydrologic telemetry time series...")
        readings = []
        for s in sensor_configs:
            sid = s["sensor_id"]
            base_level = s["current_water_level"]
            is_critical = s["status"] == "CRITICAL"
            is_warning = s["status"] == "WARNING"

            # Generate 48 hourly readings for the last 48 hours for high-res 24H view
            for hours_ago in range(48, -1, -1):
                pt_time = now - timedelta(hours=hours_ago)
                
                # Hydrological surge simulation leading up to current time
                t_factor = (48 - hours_ago) / 48.0
                if is_critical:
                    # Rises from 1.2m up to 3.21m
                    level = 1.0 + (base_level - 1.0) * math.pow(t_factor, 1.6) + random.uniform(-0.03, 0.03)
                    rise_rate = 0.08 + (0.24 - 0.08) * t_factor
                    rain = 12.0 + 16.0 * t_factor + random.uniform(-2, 2)
                    soil = 75.0 + 17.0 * t_factor
                elif is_warning:
                    level = 0.9 + (base_level - 0.9) * math.pow(t_factor, 1.4) + random.uniform(-0.03, 0.03)
                    rise_rate = 0.04 + (0.12 - 0.04) * t_factor
                    rain = 8.0 + 10.0 * t_factor + random.uniform(-1, 1)
                    soil = 70.0 + 15.0 * t_factor
                else:
                    # Normal diurnal variation around 1.1 - 1.5m
                    level = base_level + 0.15 * math.sin(hours_ago / 4.0) + random.uniform(-0.02, 0.02)
                    rise_rate = 0.02 * math.cos(hours_ago / 4.0)
                    rain = max(0.0, 4.0 + random.uniform(-2, 4))
                    soil = min(90.0, 65.0 + 10.0 * math.sin(hours_ago / 8.0))

                readings.append(
                    SensorReading(
                        sensor_id=sid,
                        water_level=round(max(0.2, level), 2),
                        water_rise_rate=round(rise_rate, 3),
                        rainfall=round(max(0.0, rain), 1),
                        soil_moisture=round(min(100.0, max(20.0, soil)), 1),
                        temperature=round(12.0 + random.uniform(-1.5, 1.5), 1),
                        battery=round(max(10.0, s["battery"] - (hours_ago * 0.05)), 1),
                        signal_strength=round(s["signal_strength"] + random.uniform(-2, 2), 1),
                        inclination_x=0.2 if is_critical else 0.0,
                        inclination_y=0.4 if is_critical else 0.0,
                        timestamp=pt_time,
                        created_at=pt_time,
                    )
                )

        db.bulk_save_objects(readings)
        db.commit()

        # 4. Alerts matching the reference dashboard
        print("Seeding alerts matching reference UI...")
        alerts_data = [
            {
                "sensor_id": "FW-007",
                "type": "HIGH_WATER_LEVEL",
                "severity": "CRITICAL",
                "title": "High water level at Sensor 7",
                "message": "Water level reached 3.21m (danger threshold 3.2m exceeded)",
                "status": "ACTIVE",
                "is_read": False,
                "created_at": now - timedelta(minutes=2),
            },
            {
                "sensor_id": "FW-004",
                "type": "RAPID_WATER_RISE",
                "severity": "WARNING",
                "title": "Rapid rise detected (Sensor 4)",
                "message": "Water level increased by 0.8m over last 2 hours",
                "status": "ACTIVE",
                "is_read": False,
                "created_at": now - timedelta(minutes=18),
            },
            {
                "sensor_id": None,
                "type": "HEAVY_RAINFALL",
                "severity": "INFO",
                "title": "Heavy rainfall expected",
                "message": "80 mm in next 3 hours (DWD German Weather Service)",
                "status": "ACTIVE",
                "is_read": True,
                "created_at": now - timedelta(hours=1),
            },
            {
                "sensor_id": "FW-012",
                "type": "SENSOR_RECOVERY",
                "severity": "RESOLVED",
                "title": "Sensor 12 back online",
                "message": "Telemetry link restored after maintenance",
                "status": "RESOLVED",
                "is_read": True,
                "created_at": now - timedelta(hours=2),
                "resolved_at": now - timedelta(hours=1, minutes=55),
                "resolved_by": "Operator Schmidt",
            },
            {
                "sensor_id": None,
                "type": "SYSTEM_CHECK",
                "severity": "INFO",
                "title": "Routine check completed",
                "message": "All diagnostic health pings and database telemetry verified operational",
                "status": "RESOLVED",
                "is_read": True,
                "created_at": now - timedelta(hours=3),
                "resolved_at": now - timedelta(hours=2, minutes=58),
                "resolved_by": "System Daemon",
            },
        ]

        for a in alerts_data:
            alert = Alert(
                sensor_id=a["sensor_id"],
                type=a["type"],
                severity=a["severity"],
                title=a["title"],
                message=a["message"],
                status=a["status"],
                is_read=a["is_read"],
                created_at=a["created_at"],
                resolved_at=a.get("resolved_at"),
                resolved_by=a.get("resolved_by"),
            )
            db.add(alert)
        db.commit()

        # 5. Current Weather Data & 24h Hourly Forecast
        print("Seeding current weather and 24-hour rainfall forecast for Barpeta, Assam...")
        weather = WeatherData(
            location_name="Barpeta, Assam, India",
            temperature=27.0,
            humidity=85.0,
            wind_speed=3.9,
            rainfall_current=65.0,
            atmospheric_pressure=999.0,
            weather_condition="Mostly Clear",
            recorded_at=now,
        )
        db.add(weather)

        # 24-hour precipitation forecast matching the bar chart in reference image:
        # Now: 15mm, 3h: 22mm, 6h: 48mm (Peak), 9h: 38mm, 12h: 24mm, 18h: 15mm, 24h: 8mm -> Total ~120mm!
        forecast_distribution = [
            (0, 15.0, 80, 12.0, "Light Rain"),
            (1, 18.0, 85, 12.0, "Rain"),
            (2, 22.0, 90, 11.5, "Moderate Rain"),
            (3, 26.0, 92, 11.0, "Moderate Rain"),
            (4, 34.0, 95, 10.8, "Heavy Rain"),
            (5, 42.0, 95, 10.5, "Heavy Rain"),
            (6, 48.0, 98, 10.2, "Torrential Rain"),  # Peak
            (7, 44.0, 95, 10.4, "Heavy Rain"),
            (8, 38.0, 90, 10.6, "Heavy Rain"),
            (9, 32.0, 85, 11.0, "Moderate Rain"),
            (10, 26.0, 80, 11.2, "Moderate Rain"),
            (11, 22.0, 75, 11.5, "Rain"),
            (12, 18.0, 70, 11.8, "Rain"),
            (14, 14.0, 65, 12.0, "Light Rain"),
            (16, 12.0, 60, 12.2, "Light Rain"),
            (18, 9.0, 50, 12.5, "Overcast"),
            (20, 6.0, 40, 13.0, "Cloudy"),
            (22, 4.0, 30, 13.2, "Partly Cloudy"),
            (24, 2.0, 20, 13.5, "Clear"),
        ]

        for offset_hr, rain_mm, prob, temp, cond in forecast_distribution:
            forecast_item = WeatherForecast(
                forecast_time=now + timedelta(hours=offset_hr),
                expected_rainfall_mm=rain_mm,
                probability_percent=prob,
                temperature=temp,
                condition=cond,
                created_at=now,
            )
            db.add(forecast_item)

        # 6. Global Flood Risk Assessment
        print("Seeding initial Flood Risk Assessment...")
        risk = FloodRiskAssessment(
            sensor_id=None,
            risk_score=28.0,  # LOW baseline or MODERATE
            risk_level="LOW",
            water_level_score=35.0,
            rainfall_score=40.0,
            soil_moisture_score=85.0,
            rise_rate_score=20.0,
            forecast_score=60.0,
            created_at=now,
        )
        db.add(risk)

        # 7. System Settings
        settings_defaults = [
            ("SAFE_WATER_LEVEL", "2.00", "THRESHOLDS", "Baseline safe river depth in meters"),
            ("WARNING_WATER_LEVEL", "3.00", "THRESHOLDS", "Warning threshold river depth in meters"),
            ("DANGER_WATER_LEVEL", "4.00", "THRESHOLDS", "Critical danger threshold river depth in meters"),
            ("RAPID_RISE_THRESHOLD", "0.20", "THRESHOLDS", "Water rate of rise threshold in m/hr"),
            ("OFFLINE_TIMEOUT_MINUTES", "15", "MONITORING", "Minutes without telemetry before marking sensor offline"),
            ("LOW_BATTERY_THRESHOLD", "20.0", "HARDWARE", "Battery percentage trigger for low battery alert"),
            ("TILT_THRESHOLD_DEGREES", "15.0", "HARDWARE", "Tilt deviation angle indicating physical tampering"),
            ("SMS_ALERTS_ENABLED", "true", "NOTIFICATIONS", "Send instant SMS on CRITICAL flood level"),
            ("EMAIL_ALERTS_ENABLED", "true", "NOTIFICATIONS", "Send email summaries on WARNING and CRITICAL"),
        ]
        for k, v, cat, desc in settings_defaults:
            setting = SystemSetting(key=k, value=v, category=cat, description=desc, updated_at=now)
            db.add(setting)

        # 8. Initial Report
        report = Report(
            title="Barpeta Catchment 24-Hour Hydrologic Summary",
            report_type="24H",
            start_date=now - timedelta(hours=24),
            end_date=now,
            summary_data="""{
                "average_water_level": 3.17,
                "maximum_water_level": 3.41,
                "total_rainfall_mm": 65.0,
                "active_alerts": 1,
                "offline_sensors": 0,
                "critical_events": ["Barpeta Station FW-001 Warning Threshold Exceeded"]
            }""",
            generated_by="Automated Hydrological Engine",
            created_at=now,
        )
        db.add(report)

        db.commit()
        print("Successfully seeded all JAL SUCHAK database tables!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
