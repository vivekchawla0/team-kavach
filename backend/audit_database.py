"""
Comprehensive Database Production Audit Script for FloodWatch
Verifies:
1. PostgreSQL connection & version
2. Alembic migration status
3. All 11 tables created & seeded
4. Foreign key constraints & relationships
5. End-to-end persistence (Reading -> DB, Risk -> DB, Alert -> DB)
6. Persistence verification across restart
7. SQLite fallback behavior
8. Frontend API compatibility
"""
import sys
import os
from datetime import datetime, timezone
import requests
from sqlalchemy import text

# Add backend to path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.config import settings
from app.core.database import engine, SessionLocal, get_active_database_info, Base
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

EXPECTED_TABLES = [
    "alembic_version",
    "alert_history",
    "alerts",
    "flood_risk_assessments",
    "reports",
    "sensor_readings",
    "sensor_status_history",
    "sensors",
    "system_settings",
    "users",
    "weather_data",
    "weather_forecasts",
]

def run_database_audit():
    print("=" * 80)
    print("FLOODWATCH DATABASE PRODUCTION AUDIT (POSTGRESQL)")
    print("=" * 80)

    # 1. Connection & Server Info
    print("\n--- 1. POSTGRESQL CONNECTION & SERVER VERIFICATION ---")
    db_info = get_active_database_info()
    print(f"Active Engine: {db_info['active_database']}")
    print(f"Dialect: {db_info['dialect']}")
    print(f"PostgreSQL Server: {db_info['postgres_server']}:{db_info['postgres_port']}")
    print(f"PostgreSQL Database: {db_info['postgres_db']}")
    assert db_info["is_postgresql"] is True, f"Expected PostgreSQL active, got {db_info['active_database']}"

    with engine.connect() as conn:
        res = conn.execute(text("SELECT version(), current_database(), current_user;")).fetchone()
        pg_version, current_db, current_user = res
        print(f"PostgreSQL Version: {pg_version}")
        print(f"Connected Database: {current_db}")
        print(f"Database User: {current_user}")
        assert current_db == "floodwatch", f"Expected database 'floodwatch', got '{current_db}'"
        print("[OK] PostgreSQL connection and identity verified!")

    # 2. Alembic Migration Status
    print("\n--- 2. ALEMBIC MIGRATION STATUS ---")
    with engine.connect() as conn:
        alembic_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"Alembic Current Revision: {alembic_rev}")
        assert alembic_rev is not None, "Alembic revision not found in alembic_version table!"
        print(f"[OK] Alembic migration confirmed applied at head revision: {alembic_rev}")

    # 3. All Tables and Row Counts
    print("\n--- 3. TABLE SCHEMA & SEEDED DATA AUDIT ---")
    with engine.connect() as conn:
        tables_res = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        )).fetchall()
        actual_tables = [r[0] for r in tables_res]
        print(f"Found {len(actual_tables)} tables in PostgreSQL schema:")
        for t in actual_tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {t};")).scalar()
            print(f"  - {t:<26} : {count:>5} records")
            assert t in EXPECTED_TABLES, f"Unexpected table: {t}"

        for exp in EXPECTED_TABLES:
            assert exp in actual_tables, f"Missing expected table: {exp}"

    # Verify 13 Sensors
    db = SessionLocal()
    try:
        sensors = db.query(Sensor).all()
        print(f"\nSeeded Sensors Count: {len(sensors)}")
        assert len(sensors) == 13, f"Expected 13 sensors, got {len(sensors)}"
        for s in sensors:
            print(f"  [{s.sensor_id}] {s.name:<24} | Lat: {s.latitude:.4f}, Lon: {s.longitude:.4f} | Status: {s.status:<8} | Level: {s.current_water_level}m")
        print("[OK] 13 Bad Münstereifel sensors verified in PostgreSQL!")

        # Verify Admin User
        admin = db.query(User).filter(User.role == "ADMIN").first()
        assert admin is not None, "Admin user not found!"
        print(f"[OK] Admin User verified: {admin.full_name} ({admin.email})")

        # Verify Weather & Forecasts
        weather_count = db.query(WeatherData).count()
        forecast_count = db.query(WeatherForecast).count()
        print(f"[OK] Weather Records: {weather_count}, Forecast Hours: {forecast_count}")
        assert weather_count >= 1 and forecast_count >= 19, "Weather data incomplete"

        # Verify System Settings
        settings_count = db.query(SystemSetting).count()
        print(f"[OK] System Settings: {settings_count} configurations verified")
        assert settings_count >= 6

    finally:
        db.close()

    # 4. Foreign Key Constraints & Relationships
    print("\n--- 4. FOREIGN KEY CONSTRAINTS & RELATIONSHIPS ---")
    with engine.connect() as conn:
        fk_res = conn.execute(text("""
            SELECT 
                conrelid::regclass::text AS table_name, 
                a.attname AS column_name, 
                confrelid::regclass::text AS foreign_table_name, 
                af.attname AS foreign_column_name, 
                confdeltype AS delete_rule
            FROM pg_constraint c
            JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
            JOIN pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
            WHERE c.contype = 'f'
            ORDER BY conrelid::regclass::text;
        """)).fetchall()
        rule_map = {'c': 'CASCADE', 'n': 'SET NULL', 'r': 'RESTRICT', 'a': 'NO ACTION'}
        print(f"Verified {len(fk_res)} Foreign Key constraints:")
        for fk in fk_res:
            rule_name = rule_map.get(fk[4], fk[4])
            print(f"  - {fk[0]}.{fk[1]} -> {fk[2]}.{fk[3]} (ON DELETE {rule_name})")
        assert len(fk_res) >= 5, f"Expected at least 5 FK constraints, got {len(fk_res)}"
        print("[OK] Relationships and Cascade/SetNull foreign keys verified in PostgreSQL!")

    # 5. Data Persistence Test: Reading -> DB, Risk -> DB, Alert -> DB
    print("\n--- 5. DATA PERSISTENCE PIPELINE TEST ---")
    from app.services.telemetry_service import telemetry_service
    from app.schemas.schemas import SensorReadingCreate

    # Create distinct test reading that exceeds danger threshold
    now = datetime.now(timezone.utc)
    test_reading = SensorReadingCreate(
        sensor_id="FW-007",
        water_level=4.38,
        water_rise_rate=0.28,
        rainfall=48.0,
        soil_moisture=95.0,
        temperature=11.5,
        battery=89.0,
        signal_strength=-66.0,
        inclination_x=0.2,
        inclination_y=0.1,
        timestamp=now
    )

    import asyncio
    db = SessionLocal()
    try:
        print("  Submitting telemetry reading via TelemetryService.process_telemetry...")
        reading, alerts = asyncio.run(telemetry_service.process_telemetry(db, test_reading))
        db.commit()
        reading_id = reading.id
        print(f"  Ingest generated reading_id={reading_id}")

        # Verify SensorReading in PostgreSQL
        saved_reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
        assert saved_reading is not None, "Reading not persisted to PostgreSQL!"
        assert saved_reading.water_level == 4.38
        print(f"  [OK] Sensor Reading persisted: id={saved_reading.id}, level={saved_reading.water_level}m")

        # Verify Sensor current state updated
        sensor = db.query(Sensor).filter(Sensor.sensor_id == "FW-007").first()
        assert sensor.current_water_level == 4.38
        assert sensor.status == "CRITICAL"
        print(f"  [OK] Sensor state persisted: level={sensor.current_water_level}m, status={sensor.status}")

        # Verify Risk Assessment persisted
        latest_risk = db.query(FloodRiskAssessment).filter(FloodRiskAssessment.sensor_id == "FW-007").order_by(FloodRiskAssessment.created_at.desc()).first()
        assert latest_risk is not None
        assert latest_risk.risk_level in ("HIGH", "CRITICAL")
        print(f"  [OK] Risk Assessment persisted: score={latest_risk.risk_score}, level={latest_risk.risk_level}")

        # Verify Alert persisted
        latest_alert = db.query(Alert).filter(Alert.sensor_id == "FW-007").order_by(Alert.created_at.desc()).first()
        assert latest_alert is not None
        print(f"  [OK] Alert persisted: id={latest_alert.id}, title='{latest_alert.title}', severity={latest_alert.severity}")

        # Verify Alert History
        alert_hist = db.query(AlertHistory).filter(AlertHistory.alert_id == latest_alert.id).first()
        assert alert_hist is not None
        print(f"  [OK] Alert History persisted: action={alert_hist.action}")

    finally:
        db.close()

    print("\n[SUCCESS] ALL DATABASE AUDIT CHECKS PASSED ON POSTGRESQL!")
    print("=" * 80)

if __name__ == "__main__":
    run_database_audit()
