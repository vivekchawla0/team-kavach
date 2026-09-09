import asyncio
import json
import os
import sys
import threading
from typing import Optional, Callable, Dict, Any

from bleak import BleakScanner, BleakClient

# ==============================================================================
# JAL SUCHAK — ESP32 BLE Telemetry Client & Reusable Collector
# Device Address: 74:4D:BD:75:EA:39
# Characteristic: beb5483e-36e1-4688-b7f5-ea07361b26a8
# ==============================================================================

ESP32_ADDRESS = "74:4D:BD:75:EA:39"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
BACKEND_TELEMETRY_URL = os.environ.get("JAL_SUCHAK_BACKEND_URL", "http://127.0.0.1:8000/api/v1/telemetry/esp32")

# Optional external telemetry callback (for direct in-process integration with FastAPI)
_telemetry_callback: Optional[Callable[[Dict[str, Any]], None]] = None


def set_telemetry_callback(callback: Callable[[Dict[str, Any]], None]):
    """Set an in-process callback when telemetry arrives."""
    global _telemetry_callback
    _telemetry_callback = callback


def parse_telemetry(data_bytes: bytearray) -> Optional[Dict[str, Any]]:
    """Decodes and parses raw JSON bytes from ESP32."""
    try:
        text = data_bytes.decode()
        return json.loads(text)
    except Exception as e:
        print("DATA ERROR:", e)
        return None


def forward_to_backend(payload: Dict[str, Any]):
    """Forwards parsed ESP32 payload to FastAPI backend asynchronously."""
    try:
        import urllib.request
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            BACKEND_TELEMETRY_URL,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "JalSuchak-BLE/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except Exception:
        # Backend not running or unreachable — continue cleanly without failing terminal
        pass


def notification_handler(sender, data):
    payload = parse_telemetry(data)
    if not payload:
        return

    # 1. Exact terminal output matching ble_test.py specification
    print("\nESP32 DATA")
    print("Water Raw       :", payload.get("water_level_raw", payload.get("water_raw")))
    print("Water Percentage:", payload.get("water_percentage"), "%")
    print("Rain Raw        :", payload.get("rain_raw"))
    print("Rain Percentage :", payload.get("rain_percentage"), "%")

    # 2. In-process callback if registered
    if _telemetry_callback:
        try:
            _telemetry_callback(payload)
        except Exception:
            pass

    # 3. Non-blocking forward to FastAPI backend (WebSocket & Dashboard update)
    threading.Thread(target=forward_to_backend, args=(payload,), daemon=True).start()


async def connect_to_esp32(address: str = ESP32_ADDRESS, timeout: float = 10.0) -> Optional[BleakClient]:
    """Scans and connects to the target ESP32 BLE peripheral."""
    print("Scanning for ESP32...")
    devices = await BleakScanner.discover(timeout=timeout)

    target = None
    for device in devices:
        print(device.name, device.address)
        if device.address.upper() == address.upper():
            target = device

    if target is None:
        print("\nESP32 not found!")
        return None

    print("\nFOUND ESP32")
    print("Address:", target.address)
    print("\nConnecting...")

    client = BleakClient(target)
    await client.connect()
    return client


async def receive_telemetry(client: BleakClient, char_uuid: str = CHAR_UUID, handler: Callable = notification_handler):
    """Subscribes to notifications and keeps connection open."""
    await client.start_notify(char_uuid, handler)


async def start_ble_collector(
    address: str = ESP32_ADDRESS,
    char_uuid: str = CHAR_UUID,
    callback: Optional[Callable[[Dict[str, Any]], None]] = None,
):
    """Reusable runner function for FastAPI or background scripts."""
    if callback:
        set_telemetry_callback(callback)

    while True:
        try:
            client = await connect_to_esp32(address)
            if client and client.is_connected:
                print("CONNECTED:", client.is_connected)
                await receive_telemetry(client, char_uuid, notification_handler)
                print("\n======================================")
                print(" ESP32 • BLE • JAL SUCHAK")
                print("======================================")
                print("\nWaiting for sensor data...\n")

                while client.is_connected:
                    await asyncio.sleep(1)
            else:
                await asyncio.sleep(5)
        except Exception as e:
            print(f"BLE Connection Error: {e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


async def main():
    client = await connect_to_esp32(ESP32_ADDRESS)
    if client is None:
        return

    async with client:
        print("CONNECTED:", client.is_connected)
        await receive_telemetry(client, CHAR_UUID, notification_handler)

        print("\n======================================")
        print(" ESP32 • BLE • SECOND LAPTOP")
        print("======================================")
        print("\nWaiting for sensor data...\n")

        while True:
            await asyncio.sleep(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBLE Collector stopped by user.")
