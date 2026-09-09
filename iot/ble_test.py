import asyncio
import json
import os
import threading
import requests

from bleak import BleakScanner, BleakClient


# ============================================================
# ESP32 BLE SETTINGS
# ============================================================

ESP32_ADDRESS = "74:4D:BD:75:EA:39"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
BACKEND_URL = os.environ.get("JAL_SUCHAK_BACKEND_URL", "http://127.0.0.1:8000/api/v1/telemetry")
BACKEND_FALLBACK_URL = "http://localhost:8000/api/v1/telemetry"


# ============================================================
# BLYNK SETTINGS
# ============================================================

BLYNK_TOKEN = os.getenv("BLYNK_TOKEN", "YOUR_BLYNK_TOKEN_HERE")
BLYNK_UPDATE_URL = "https://blr1.blynk.cloud/external/api/batch/update"
BLYNK_EVENT_URL = "https://blr1.blynk.cloud/external/api/logEvent"


# ============================================================
# FLOOD ALERT THRESHOLDS (TEST VALUES)
# ============================================================

HIGH_THRESHOLD = 20
CRITICAL_THRESHOLD = 25
alert_state = "NORMAL"


# ============================================================
# FORWARD SENSOR DATA TO JAL SUCHAK BACKEND (FASTAPI)
# ============================================================

def forward_to_backend(payload):
    water_raw = payload.get("water_level_raw", payload.get("water_raw", 0))
    rain_raw = payload.get("rain_raw", 0)
    water_pct = payload.get("water_percentage", 0)
    rain_pct = payload.get("rain_percentage", 0)

    post_data = {
        "device_id": "FW-001",
        "water_raw": water_raw,
        "rain_raw": rain_raw,
        "water_percentage": water_pct,
        "rain_percentage": rain_pct,
        "source": "ESP32_BLUETOOTH"
    }

    print("[BRIDGE] Sending telemetry...")
    target_urls = [BACKEND_URL, BACKEND_FALLBACK_URL]
    success = False

    for url in target_urls:
        try:
            resp = requests.post(url, json=post_data, timeout=3.0)
            if resp.status_code == 200:
                resp_json = resp.json()
                calibrated = resp_json.get("calibrated", {})
                water_cm = calibrated.get("water_level_cm", 0.0)
                rain_int = calibrated.get("rain_intensity", 0.0)
                print("[BRIDGE] API SUCCESS")
                print("[Dashboard] Sent successfully")
                print(f"Water: {water_cm:.2f} cm")
                print(f"Rain: {rain_int:.1f} / 10")
                success = True
                break
            else:
                print(f"[Dashboard] Send failed on {url}: HTTP {resp.status_code}")
        except Exception as e:
            # Try next URL or print error
            if url == target_urls[-1]:
                print(f"[Dashboard] Send failed: {e}")


# ============================================================
# SEND SENSOR DATA TO BLYNK
# ============================================================

def send_to_blynk(payload):
    if not BLYNK_TOKEN:
        return

    water_raw = payload.get("water_level_raw", payload.get("water_raw", 0))
    rain_raw = payload.get("rain_raw", 0)

    params = {
        "token": BLYNK_TOKEN,
        "v0": water_raw,
        "v1": rain_raw
    }

    try:
        response = requests.get(BLYNK_UPDATE_URL, params=params, timeout=5)
        print(f"BLYNK DATA: HTTP {response.status_code}")
    except Exception as e:
        print("BLYNK DATA ERROR:", e)


# ============================================================
# TRIGGER BLYNK EVENT
# ============================================================

def trigger_blynk_event(code, description):
    if not BLYNK_TOKEN:
        return

    params = {
        "token": BLYNK_TOKEN,
        "code": code,
        "description": description
    }

    try:
        response = requests.get(BLYNK_EVENT_URL, params=params, timeout=5)
        print(f"BLYNK EVENT: HTTP {response.status_code} {response.text}")
    except Exception as e:
        print("BLYNK EVENT ERROR:", e)


# ============================================================
# FLOOD ALERT CHECK
# ============================================================

def check_flood_alert(water_percentage):
    global alert_state

    if water_percentage is None:
        return

    if water_percentage >= CRITICAL_THRESHOLD:
        if alert_state != "CRITICAL":
            trigger_blynk_event(
                "critical_flood_risk",
                f"Critical flood risk! Water level is {water_percentage}%."
            )
            print(f"\n[!] CRITICAL FLOOD ALERT! Water Level: {water_percentage}%\n")
            alert_state = "CRITICAL"
    elif water_percentage >= HIGH_THRESHOLD:
        if alert_state != "HIGH":
            trigger_blynk_event(
                "high_flood_risk",
                f"High flood risk! Water level is {water_percentage}%."
            )
            print(f"\n[!] HIGH FLOOD WARNING! Water Level: {water_percentage}%\n")
            alert_state = "HIGH"
    else:
        if alert_state != "NORMAL":
            print("[i] Water level returned to NORMAL")
        alert_state = "NORMAL"


# ============================================================
# BLE DATA RECEIVER
# ============================================================

def notification_handler(sender, data):
    try:
        text = data.decode("utf-8")
        payload = json.loads(text)
    except Exception as e:
        print("DATA ERROR:", e)
        return

    water_raw = payload.get("water_level_raw", payload.get("water_raw", 0))
    water_percentage = payload.get("water_percentage")
    rain_raw = payload.get("rain_raw", 0)
    rain_percentage = payload.get("rain_percentage")

    print()
    print("======================================")
    print("ESP32 DATA")
    print("======================================")
    print("Water Raw       :", water_raw)
    print("Water Percentage:", water_percentage, "%")
    print("Rain Raw        :", rain_raw)
    print("Rain Percentage :", rain_percentage, "%")
    print("======================================")
    print(f"[ESP32] Packet received")
    print(f"[ESP32] Water Raw: {water_raw}")
    print(f"[ESP32] Rain Raw: {rain_raw}")

    # 1. Forward to JAL SUCHAK backend (FastAPI -> DB -> WebSocket -> Dashboard)
    threading.Thread(target=forward_to_backend, args=(payload,), daemon=True).start()

    # 2. Send to Blynk Cloud
    threading.Thread(target=send_to_blynk, args=(payload,), daemon=True).start()

    # 3. Check flood alerts
    check_flood_alert(water_percentage)


# ============================================================
# CONNECT TO ESP32
# ============================================================

async def connect_to_esp32():
    print("\nScanning for ESP32...")
    devices = await BleakScanner.discover(timeout=10)

    target = None
    for device in devices:
        print(device.name, device.address)
        if device.address.upper() == ESP32_ADDRESS.upper():
            target = device
            break

    if target is None:
        print("\nESP32 NOT FOUND! Check that ESP32 is powered ON and BLE is running.\n")
        return None

    print("\nFOUND ESP32")
    print("Address:", target.address)
    print("\nConnecting...")

    client = BleakClient(target)
    await client.connect()

    if client.is_connected:
        print("\nCONNECTED:", client.is_connected)

    return client


# ============================================================
# MAIN
# ============================================================

async def main():
    client = await connect_to_esp32()
    if client is None:
        return

    try:
        await client.start_notify(CHAR_UUID, notification_handler)
        print()
        print("======================================")
        print(" ESP32 -> BLE -> JAL SUCHAK + BLYNK")
        print("======================================")
        print("Waiting for sensor data...\n")

        while client.is_connected:
            await asyncio.sleep(1)

    except Exception as e:
        print("\nBLE ERROR:", e)
    finally:
        try:
            await client.stop_notify(CHAR_UUID)
        except Exception:
            pass
        if client.is_connected:
            await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBLE Collector stopped by user.")
