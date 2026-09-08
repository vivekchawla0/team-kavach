"""
Automated verification test suite for FloodWatch FastAPI backend.
"""
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    print("[OK] Health check passed")


def test_dashboard_summary():
    res = client.get("/api/v1/dashboard/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_sensors"] >= 13
    assert data["average_water_level_m"] > 0
    assert data["current_rainfall_mm_hr"] > 0
    assert "flood_risk_level" in data
    assert "soil_moisture_percent" in data
    print(f"[OK] Dashboard summary passed: {data['total_sensors']} sensors, {data['average_water_level_m']}m avg water level, risk: {data['flood_risk_level']}")


def test_sensors_list():
    res = client.get("/api/v1/sensors")
    assert res.status_code == 200
    sensors = res.json()
    assert len(sensors) >= 13
    sensor_ids = [s["sensor_id"] for s in sensors]
    assert "FW-001" in sensor_ids
    assert "FW-007" in sensor_ids
    print(f"[OK] Sensors list passed: {len(sensors)} sensors found")


def test_water_level_trends():
    res = client.get("/api/v1/analytics/water-level/FW-005?range=24H")
    assert res.status_code == 200
    data = res.json()
    assert "data_points" in data
    assert len(data["data_points"]) > 0
    assert data["safe_threshold"] == 2.0
    print(f"[OK] Water level analytics passed: {len(data['data_points'])} trend points for {data['sensor_name']}")


def test_alerts():
    res = client.get("/api/v1/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) > 0
    print(f"[OK] Alerts passed: {len(alerts)} alerts retrieved")


def test_weather():
    res_curr = client.get("/api/v1/weather/current")
    assert res_curr.status_code == 200
    curr = res_curr.json()
    assert curr["temperature"] == 12.0

    res_fc = client.get("/api/v1/weather/forecast")
    assert res_fc.status_code == 200
    fc = res_fc.json()
    assert fc["total_rainfall_24h_mm"] > 0
    print(f"[OK] Weather passed: {curr['weather_condition']}, forecast 24h total: {fc['total_rainfall_24h_mm']}mm")


def test_ai_risk_engine():
    res = client.get("/api/v1/risk/basin")
    assert res.status_code == 200
    risk = res.json()
    assert "overall_score" in risk
    assert "factors" in risk
    print(f"[OK] AI Risk Engine passed: Basin risk score {risk['overall_score']} ({risk['overall_level']})")


def test_telemetry_ingestion():
    payload = {
        "sensor_id": "FW-001",
        "water_level": 1.15,
        "water_rise_rate": 0.03,
        "rainfall": 2.0,
        "soil_moisture": 70.0,
        "temperature": 13.0,
        "battery": 95.0,
        "signal_strength": -62.0,
        "inclination_x": 0.1,
        "inclination_y": 0.2
    }
    # Test unauthorized without API key
    res_unauth = client.post("/api/v1/telemetry/", json=payload)
    assert res_unauth.status_code == 401

    # Test with valid API key
    res_auth = client.post("/api/v1/telemetry/", json=payload, headers={"X-API-Key": settings.IOT_API_KEY})
    assert res_auth.status_code == 200
    data = res_auth.json()
    assert data["status"] == "success"
    print("[OK] Telemetry ingestion and X-API-Key authentication passed")


def test_scenario_simulation():
    res = client.post("/api/v1/simulation/scenario?scenario=normal")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    print("[OK] Scenario simulation toggle passed")


if __name__ == "__main__":
    print("\n--- Running FloodWatch Automated Verification Test Suite ---")
    test_health()
    test_dashboard_summary()
    test_sensors_list()
    test_water_level_trends()
    test_alerts()
    test_weather()
    test_ai_risk_engine()
    test_telemetry_ingestion()
    test_scenario_simulation()
    print("\n[SUCCESS] ALL 9 AUTOMATED TESTS PASSED SUCCESSFULLY!\n")
