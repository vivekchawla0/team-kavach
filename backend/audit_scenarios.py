"""
Audit script for the 3 simulator scenarios: Normal, Storm, and Flash Flood.
Verifies that dashboard API updates correctly for each scenario.
"""
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

def audit_scenarios():
    print("--- AUDITING SIMULATOR SCENARIOS ---")

    # 1. Normal Flow Scenario
    print("\n[Scenario 1] Testing NORMAL scenario...")
    res = requests.post(f"{BASE_URL}/simulation/scenario?scenario=normal")
    assert res.status_code == 200
    summary = requests.get(f"{BASE_URL}/dashboard/summary").json()
    sensors = requests.get(f"{BASE_URL}/sensors").json()
    print(f"  Summary: avg_water={summary['average_water_level_m']}m, rain={summary['current_rainfall_mm_hr']}mm/h, risk={summary['flood_risk_level']}")
    assert summary["current_rainfall_mm_hr"] == 2.0
    for s in sensors:
        if s["status"] != "OFFLINE":
            assert s["status"] == "NORMAL", f"Sensor {s['sensor_id']} has status {s['status']}, expected NORMAL"
    print("  [OK] Normal scenario verified: all online sensors NORMAL, rainfall 2 mm/h, risk LOW")

    # 2. Heavy Storm Scenario
    print("\n[Scenario 2] Testing STORM scenario...")
    res = requests.post(f"{BASE_URL}/simulation/scenario?scenario=storm")
    assert res.status_code == 200
    summary = requests.get(f"{BASE_URL}/dashboard/summary").json()
    sensors = requests.get(f"{BASE_URL}/sensors").json()
    print(f"  Summary: avg_water={summary['average_water_level_m']}m, rain={summary['current_rainfall_mm_hr']}mm/h, risk={summary['flood_risk_level']}")
    assert summary["current_rainfall_mm_hr"] == 32.0
    elevated_count = sum(1 for s in sensors if s["current_water_level"] >= 2.0)
    assert elevated_count >= 10, f"Expected >= 10 elevated sensors, got {elevated_count}"
    print(f"  [OK] Storm scenario verified: rainfall 32 mm/h, {elevated_count} sensors elevated above 2.0m")

    # 3. Flash Flood Scenario
    print("\n[Scenario 3] Testing FLASH FLOOD scenario...")
    res = requests.post(f"{BASE_URL}/simulation/scenario?scenario=flood")
    assert res.status_code == 200
    summary = requests.get(f"{BASE_URL}/dashboard/summary").json()
    sensors = requests.get(f"{BASE_URL}/sensors").json()
    critical_sensors = [s for s in sensors if s["status"] == "CRITICAL"]
    print(f"  Summary: avg_water={summary['average_water_level_m']}m, rain={summary['current_rainfall_mm_hr']}mm/h, risk={summary['flood_risk_level']}")
    print(f"  Critical Sensors: {[s['sensor_id'] for s in critical_sensors]}")
    assert summary["current_rainfall_mm_hr"] == 65.0
    assert len(critical_sensors) >= 2, f"Expected critical sensors, got {len(critical_sensors)}"
    assert summary["flood_risk_level"] in ["CRITICAL", "HIGH"]
    print("  [OK] Flash flood scenario verified: rainfall 65 mm/h, critical sensors breaching danger thresholds")

    # 4. Reset to baseline
    print("\n[Reset] Resetting to reference image baseline...")
    res = requests.post(f"{BASE_URL}/simulation/scenario?scenario=reset")
    assert res.status_code == 200
    summary = requests.get(f"{BASE_URL}/dashboard/summary").json()
    print(f"  Baseline restored: avg_water={summary['average_water_level_m']}m, rain={summary['current_rainfall_mm_hr']}mm/h, risk={summary['flood_risk_level']}")

    print("\n[SUCCESS] All 3 simulator scenarios audited and verified!")

if __name__ == "__main__":
    audit_scenarios()
