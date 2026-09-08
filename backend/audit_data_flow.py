"""
End-to-end data flow verification script.
Tests:
Sensor Simulator -> FastAPI Ingestion API -> DB Persistence -> Risk Engine -> Alert Engine -> WebSocket
"""
import sys
import json
import asyncio
import requests
import websockets
from datetime import datetime, timezone

HTTP_URL = "http://127.0.0.1:8000/api/v1/telemetry"
WS_URL = "ws://127.0.0.1:8000/ws/telemetry"
API_KEY = "fw_live_sec_99a8b7c6d5e4"

async def test_e2e_flow():
    print("\n=== STEP 1: Connecting to WebSocket ===")
    async with websockets.connect(WS_URL) as ws:
        print("[OK] WebSocket connected successfully to /ws/telemetry")

        # Prepare a critical reading that breaches danger threshold (4.0m) on FW-007
        test_reading = {
            "sensor_id": "FW-007",
            "water_level": 4.25,      # Exceeds danger_threshold (4.0m)
            "water_rise_rate": 0.35,  # Exceeds rapid rise threshold (0.20m/hr)
            "rainfall": 52.0,         # Heavy rainfall
            "soil_moisture": 96.0,
            "temperature": 11.0,
            "battery": 82.0,
            "signal_strength": -68.0,
            "inclination_x": 0.4,
            "inclination_y": 0.3,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        print("\n=== STEP 2: Ingesting Telemetry Reading via REST API ===")
        res = requests.post(
            HTTP_URL,
            json=test_reading,
            headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            timeout=5.0
        )
        print(f"API Response Status: {res.status_code}")
        assert res.status_code == 200, f"API rejected ingestion: {res.text}"
        ingest_data = res.json()
        print(f"Ingest Result: reading_id={ingest_data['reading_id']}, alerts_triggered={ingest_data['alerts_triggered']}")

        print("\n=== STEP 3: Awaiting Real-Time WebSocket Broadcast ===")
        # Wait for WS message with timeout
        ws_msg_raw = await asyncio.wait_for(ws.recv(), timeout=5.0)
        ws_payload = json.loads(ws_msg_raw)
        print(f"WebSocket Message Received: event={ws_payload.get('event')}")
        assert ws_payload.get("event") == "telemetry_update"
        assert ws_payload["sensor"]["sensor_id"] == "FW-007"
        assert ws_payload["sensor"]["water_level"] == 4.25
        assert ws_payload["sensor"]["status"] == "CRITICAL"
        print("[OK] WebSocket payload validated in real-time!")

        print("\n=== STEP 4: Verifying Database Persistence & Engine Records ===")
        from app.core.database import SessionLocal
        from app.models.models import Sensor, SensorReading, FloodRiskAssessment, Alert
        db = SessionLocal()
        try:
            # Check sensor reading persisted
            saved_reading = db.query(SensorReading).filter(SensorReading.id == ingest_data["reading_id"]).first()
            assert saved_reading is not None, "Reading not found in database!"
            print(f"[OK] SensorReading persisted: id={saved_reading.id}, level={saved_reading.water_level}m")

            # Check sensor state updated
            sensor = db.query(Sensor).filter(Sensor.sensor_id == "FW-007").first()
            assert sensor.current_water_level == 4.25
            assert sensor.status == "CRITICAL"
            print(f"[OK] Sensor table updated: level={sensor.current_water_level}m, status={sensor.status}")

            # Check Flood Risk Assessment recorded
            latest_risk = db.query(FloodRiskAssessment).filter(FloodRiskAssessment.sensor_id == "FW-007").order_by(FloodRiskAssessment.created_at.desc()).first()
            assert latest_risk is not None
            print(f"[OK] FloodRiskAssessment persisted: score={latest_risk.risk_score}, level={latest_risk.risk_level}")

            # Check Alert generated
            latest_alert = db.query(Alert).filter(Alert.sensor_id == "FW-007").order_by(Alert.created_at.desc()).first()
            assert latest_alert is not None
            print(f"[OK] Alert persisted: type={latest_alert.type}, severity={latest_alert.severity}, title={latest_alert.title}")

        finally:
            db.close()

        print("\n=== END-TO-END FLOW VERIFICATION SUCCESSFUL! ===")

if __name__ == "__main__":
    asyncio.run(test_e2e_flow())
