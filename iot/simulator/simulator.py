#!/usr/bin/env python3
"""
FloodWatch IoT Telemetry Simulator
Simulates 13 river telemetry stations across Bad Münstereifel, Germany,
sending live water levels, rise rates, rainfall, soil moisture, battery,
and accelerometer tilt to the FloodWatch backend API via HTTP.
"""

import sys
import time
import random
import argparse
from datetime import datetime, timezone
import requests

BACKEND_URL = "http://localhost:8000/api/v1/telemetry"
API_KEY = "fw_live_sec_99a8b7c6d5e4"

# 13 Real Sensors along Erft River and tributaries in Bad Münstereifel
SENSORS = [
    {"sensor_id": "FW-001", "name": "Erft - North", "base_level": 1.12, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-002", "name": "Riverbank A", "base_level": 0.98, "warning": 2.8, "danger": 3.8},
    {"sensor_id": "FW-003", "name": "Stream B", "base_level": 2.84, "warning": 2.5, "danger": 3.5},
    {"sensor_id": "FW-004", "name": "Mill Creek", "base_level": 3.21, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-005", "name": "City Center", "base_level": 1.45, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-006", "name": "Erft South", "base_level": 1.30, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-007", "name": "Erft Bridge", "base_level": 3.21, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-008", "name": "Eicherscheid Inflow", "base_level": 1.15, "warning": 2.8, "danger": 3.8},
    {"sensor_id": "FW-009", "name": "Schleebach Gage", "base_level": 1.05, "warning": 2.5, "danger": 3.5},
    {"sensor_id": "FW-010", "name": "Iversheim South", "base_level": 2.75, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-011", "name": "Arloff Bridge", "base_level": 1.40, "warning": 3.0, "danger": 4.0},
    {"sensor_id": "FW-012", "name": "Kalkar Gage", "base_level": 0.00, "warning": 3.0, "danger": 4.0, "offline": True},
    {"sensor_id": "FW-013", "name": "Kirspen Weir", "base_level": 2.65, "warning": 3.0, "danger": 4.0},
]


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def send_reading(sensor: dict, scenario: str = "normal", backend_url: str = BACKEND_URL) -> bool:
    if sensor.get("offline"):
        return False

    base = sensor["base_level"]
    warning = sensor["warning"]
    danger = sensor["danger"]

    if scenario == "normal":
        water_level = round(base + random.uniform(-0.04, 0.04), 2)
        water_rise_rate = round(random.uniform(-0.02, 0.03), 2)
        rainfall = round(random.uniform(0.0, 5.0), 1)
        soil_moisture = round(random.uniform(65.0, 75.0), 1)
        temperature = 14.0
        battery = round(random.uniform(85.0, 98.0), 1)
        tilt_x = round(random.uniform(-0.2, 0.2), 2)
        tilt_y = round(random.uniform(-0.2, 0.2), 2)

    elif scenario == "storm":
        water_level = round(base * 1.35 + random.uniform(0.1, 0.3), 2)
        water_rise_rate = round(random.uniform(0.12, 0.22), 2)
        rainfall = round(random.uniform(28.0, 45.0), 1)
        soil_moisture = round(random.uniform(85.0, 94.0), 1)
        temperature = 11.5
        battery = round(random.uniform(80.0, 92.0), 1)
        tilt_x = round(random.uniform(-0.8, 0.8), 2)
        tilt_y = round(random.uniform(-0.8, 0.8), 2)

    elif scenario == "flash_flood":
        # Simulating July 2021 Erft catastrophe conditions
        if sensor["sensor_id"] in ["FW-004", "FW-007", "FW-003"]:
            water_level = round(danger + random.uniform(0.15, 0.45), 2)
            water_rise_rate = round(random.uniform(0.35, 0.65), 2)
        else:
            water_level = round(warning + random.uniform(0.10, 0.30), 2)
            water_rise_rate = round(random.uniform(0.20, 0.35), 2)
        rainfall = round(random.uniform(55.0, 85.0), 1)
        soil_moisture = 98.5
        temperature = 10.0
        battery = round(random.uniform(70.0, 88.0), 1)
        tilt_x = round(random.uniform(-16.5, 17.2), 2) # Potential pole tilt alert
        tilt_y = round(random.uniform(-5.0, 5.0), 2)

    else:
        water_level = base
        water_rise_rate = 0.0
        rainfall = 18.0
        soil_moisture = 92.0
        temperature = 12.0
        battery = 87.0
        tilt_x = 0.0
        tilt_y = 0.0

    payload = {
        "sensor_id": sensor["sensor_id"],
        "water_level": max(0.0, water_level),
        "water_rise_rate": water_rise_rate,
        "rainfall": rainfall,
        "soil_moisture": soil_moisture,
        "temperature": temperature,
        "battery": battery,
        "signal_strength": round(random.uniform(-75.0, -55.0), 1),
        "inclination_x": tilt_x,
        "inclination_y": tilt_y,
        "timestamp": utcnow_iso()
    }

    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }

    try:
        res = requests.post(backend_url, json=payload, headers=headers, timeout=3.0)
        if res.status_code == 200:
            data = res.json()
            alerts = data.get("alerts", [])
            alert_str = f" [ALERTS: {len(alerts)}]" if alerts else ""
            print(f"[{sensor['sensor_id']}] Level: {water_level:.2f}m | Rise: {water_rise_rate:+.2f}m/h | Rain: {rainfall}mm/h{alert_str}")
            return True
        else:
            print(f"[{sensor['sensor_id']}] Error {res.status_code}: {res.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[{sensor['sensor_id']}] Connection error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="FloodWatch IoT Station Simulator")
    parser.add_argument("--scenario", choices=["normal", "storm", "flash_flood"], default="normal", help="Simulation scenario")
    parser.add_argument("--interval", type=float, default=5.0, help="Interval between sensor broadcasts in seconds")
    parser.add_argument("--burst", action="store_true", help="Send one complete round of readings and exit")
    parser.add_argument("--url", default=BACKEND_URL, help="Backend telemetry URL")
    args = parser.parse_args()

    print(f"==================================================")
    print(f" FloodWatch IoT Telemetry Simulator")
    print(f" Target URL: {args.url}")
    print(f" Scenario:   {args.scenario.upper()}")
    print(f" Sensors:    {len(SENSORS)} telemetry stations")
    print(f" Mode:       {'Burst (1 round)' if args.burst else f'Loop ({args.interval}s interval)'}")
    print(f"==================================================")

    iteration = 1
    while True:
        print(f"\n--- Broadcast Round #{iteration} ({datetime.now().strftime('%H:%M:%S')}) ---")
        for s in SENSORS:
            send_reading(s, scenario=args.scenario, backend_url=args.url)
            time.sleep(0.1)

        if args.burst:
            print("\nBurst simulation completed successfully.")
            break

        iteration += 1
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
