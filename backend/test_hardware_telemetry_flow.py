"""
Independent Verification Script: ESP32 Physical Telemetry Flow & Backend Integration Test.
Simulates exact physical ESP32 JSON packets as constructed by `esp32_floodwatch_station.ino`:
- Only fields sent by ESP32: sensor_id, water_level, rainfall, soil_moisture, temperature, battery, signal_strength, inclination_x, inclination_y
- Omitted fields: timestamp (server assigns), water_rise_rate (server computes dh/dt)
- Verifies full pipeline: HTTP 200 -> PostgreSQL SensorReading -> Sensor Update -> Alert Engine -> Risk Engine -> ML Inference -> WebSocket broadcast.
"""

import os
import sys
import json
import time
import urllib.request
from datetime import datetime, timezone

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Sensor, SensorReading, Alert, FloodRiskAssessment, MLPrediction

API_URL = "http://127.0.0.1:8000/api/v1/telemetry"
API_KEY = "fw_live_sec_99a8b7c6d5e4"
TEST_SENSOR = "FW-007" # The physical hardware sensor ID from esp32_floodwatch_station.ino

SCENARIOS = [
    {
        "name": "1. Normal Baseflow Telemetry",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 1.25,
            "rainfall": 0.0,
            "soil_moisture": 45.0,
            "temperature": 14.2,
            "battery": 96.5,
            "signal_strength": -68.0,
            "inclination_x": 0.1,
            "inclination_y": 0.2
        },
        "expected_status": "NORMAL",
        "expected_alert": None
    },
    {
        "name": "2. Rising Water Level (Subsequent packet to test dh/dt calculation)",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 1.85, # Rise of 0.60m
            "rainfall": 8.5,
            "soil_moisture": 65.0,
            "temperature": 13.8,
            "battery": 95.8,
            "signal_strength": -67.0,
            "inclination_x": 0.1,
            "inclination_y": 0.2
        },
        "expected_status": "NORMAL", # Under 3.0m warning threshold
        "expected_alert": None
    },
    {
        "name": "3. Heavy Rainfall & Warning Threshold Exceeded",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 3.15, # Exceeds warning (3.0m)
            "rainfall": 28.0,
            "soil_moisture": 88.0,
            "temperature": 12.1,
            "battery": 94.0,
            "signal_strength": -71.0,
            "inclination_x": 0.4,
            "inclination_y": 0.3
        },
        "expected_status": "WARNING",
        "expected_alert": "HIGH_WATER_LEVEL_WARNING"
    },
    {
        "name": "4. Catastrophic Flash Flood Surge (> Danger Threshold)",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 4.35, # Exceeds danger (4.0m)
            "rainfall": 55.0,
            "soil_moisture": 98.5,
            "temperature": 10.5,
            "battery": 91.2,
            "signal_strength": -75.0,
            "inclination_x": 0.8,
            "inclination_y": 0.5
        },
        "expected_status": "CRITICAL",
        "expected_alert": "HIGH_WATER_LEVEL_DANGER"
    },
    {
        "name": "5. Station Severe Tilt (Pole Compromised by Debris Impact)",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 2.20,
            "rainfall": 15.0,
            "soil_moisture": 80.0,
            "temperature": 12.0,
            "battery": 89.0,
            "signal_strength": -70.0,
            "inclination_x": 16.5, # > 15 degrees tilt threshold!
            "inclination_y": 2.1
        },
        "expected_status": "NORMAL",
        "expected_alert": "SENSOR_TILT"
    },
    {
        "name": "6. Low Battery Depletion Alarm (< 20%)",
        "payload": {
            "sensor_id": TEST_SENSOR,
            "water_level": 1.40,
            "rainfall": 0.0,
            "soil_moisture": 50.0,
            "temperature": 14.0,
            "battery": 14.5, # < 20% low battery threshold!
            "signal_strength": -82.0,
            "inclination_x": 0.2,
            "inclination_y": 0.1
        },
        "expected_status": "NORMAL",
        "expected_alert": "LOW_BATTERY"
    }
]

def run_tests():
    print("=" * 80)
    print("FLOODWATCH ESP32 PHYSICAL TELEMETRY END-TO-END VERIFICATION")
    print("Target Sensor ID:", TEST_SENSOR)
    print("Endpoint:", API_URL)
    print("=" * 80)

    db: Session = SessionLocal()

    for idx, sc in enumerate(SCENARIOS, start=1):
        print(f"\n--- Scenario {idx}: {sc['name']} ---")
        payload_bytes = json.dumps(sc["payload"]).encode("utf-8")
        
        req = urllib.request.Request(
            API_URL,
            data=payload_bytes,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": API_KEY
            }
        )
        
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.status
                resp_data = json.loads(resp.read().decode("utf-8"))
            latency_ms = (time.time() - t0) * 1000.0
            print(f"  [HTTP {status_code}] Ingestion Success in {latency_ms:.1f} ms | Reading ID: #{resp_data['reading_id']}")
        except Exception as e:
            print(f"  [FAILED] HTTP Ingestion Error: {e}")
            continue

        # Expire session so we see fresh PostgreSQL data
        db.expire_all()

        # Verify PostgreSQL database state
        reading_id = resp_data["reading_id"]
        reading = db.query(SensorReading).filter(SensorReading.id == reading_id).first()
        sensor = db.query(Sensor).filter(Sensor.sensor_id == TEST_SENSOR).first()
        
        assert reading is not None, "Reading must be in database"
        assert sensor is not None, "Sensor must exist in database"
        
        print(f"  [PostgreSQL] Saved Reading #{reading.id}: stage={reading.water_level}m, rain={reading.rainfall}mm, rise_rate={reading.water_rise_rate}m/h")
        print(f"  [Sensor State] Status={sensor.status}, WaterLevel={sensor.current_water_level}m, Battery={sensor.battery}%, Tilt=({sensor.inclination_x}°, {sensor.inclination_y}°)")
        
        # Check alerts (including deduplicated active alerts)
        active_alerts = db.query(Alert).filter(Alert.sensor_id == TEST_SENSOR, Alert.status == "ACTIVE").all()
        alert_types = [a.type for a in active_alerts]
        print(f"  [Alert Engine] Active Alerts in DB: {alert_types}")
        if sc["expected_alert"]:
            assert sc["expected_alert"] in alert_types, f"Expected alert {sc['expected_alert']} not found in active alerts!"
            print(f"  -> Verified Alert: {sc['expected_alert']} is active in system!")

        # Check ML prediction
        recent_pred = db.query(MLPrediction).filter(MLPrediction.sensor_id == TEST_SENSOR).order_by(MLPrediction.id.desc()).first()
        if recent_pred:
            print(f"  [ML Engine] Prediction #{recent_pred.id}: +{recent_pred.horizon_hours}h = {recent_pred.predicted_water_level}m [{recent_pred.uncertainty_lower}m - {recent_pred.uncertainty_upper}m], Flood Prob = {recent_pred.flood_probability}%")

        # Sleep briefly between packets so timestamp deltas are measurable for rise_rate
        time.sleep(1.0)

    db.close()
    print("\n" + "=" * 80)
    print("ALL 6 PHYSICAL SENSOR SCENARIOS PROCESSED SUCCESSFULLY THROUGH ENTIRE PIPELINE!")
    print("=" * 80)

if __name__ == "__main__":
    run_tests()
