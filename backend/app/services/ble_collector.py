"""
JAL SUCHAK — Reusable BLE Telemetry Collector for ESP32 Physical Prototype
Uses Bleak library matching Desktop/ble_test.py source of truth.
Device Address: 74:4D:BD:75:EA:39
Notify Characteristic: beb5483e-36e1-4688-b7f5-ea07361b26a8
"""
import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from collections import deque

from app.services.calibration import parse_esp32_payload, calculate_rise_rate

logger = logging.getLogger(__name__)

ESP32_ADDRESS = "74:4D:BD:75:EA:39"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
TIMEOUT_STALE_SECONDS = 15.0


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BLECollector:
    def __init__(self, target_address: str = ESP32_ADDRESS, char_uuid: str = CHAR_UUID):
        self.target_address = target_address.upper()
        self.char_uuid = char_uuid
        self.is_connected = False
        self.is_running = False
        self.client = None
        self._task: Optional[asyncio.Task] = None

        # Telemetry State
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        self.last_received_at: Optional[datetime] = None
        self.recent_history: deque = deque(maxlen=100)  # in-memory buffer of latest 100 points
        self.subscribers: List[Any] = []

    def get_status(self) -> str:
        if not self.last_received_at:
            return "OFFLINE"
        age = (utcnow() - self.last_received_at).total_seconds()
        if age <= TIMEOUT_STALE_SECONDS:
            return "ONLINE"
        return "STALE"

    def get_seconds_since_last_telemetry(self) -> Optional[float]:
        if not self.last_received_at:
            return None
        return round((utcnow() - self.last_received_at).total_seconds(), 1)

    def get_latest_telemetry_payload(self) -> Dict[str, Any]:
        status = self.get_status()
        sec_ago = self.get_seconds_since_last_telemetry()

        if not self.latest_telemetry:
            return {
                "device_id": "ESP32-FW-001",
                "bluetooth_status": "OFFLINE",
                "calibration_status": "PENDING",
                "message": "ESP32 OFFLINE — Waiting for real telemetry...",
                "water_raw": None,
                "water_level_cm": None,
                "water_percentage": None,
                "rain_raw": None,
                "rain_percentage": None,
                "rain_intensity": None,
                "rise_rate_cm_min": 0.0,
                "timestamp": None,
                "seconds_ago": None,
            }

        data = dict(self.latest_telemetry)
        data["bluetooth_status"] = status
        data["seconds_ago"] = sec_ago
        if status != "ONLINE":
            data["message"] = f"ESP32 OFFLINE — Last telemetry {int(sec_ago)}s ago"
        else:
            data["message"] = "ESP32 ONLINE — Live Telemetry Active"
        return data

    def ingest_payload(self, raw_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main ingestion entrypoint. Parses raw ESP32 dict (from ble_test.py or direct BLE),
        applies calibration, computes rise rate, records in history, and notifies subscribers.
        """
        now = utcnow()
        calibrated = parse_esp32_payload(raw_json, device_id="ESP32-FW-001")

        # Calculate actual rise rate from previous reading
        prev_cm = self.latest_telemetry.get("water_level_cm") if self.latest_telemetry else None
        prev_time = self.last_received_at
        dt = (now - prev_time).total_seconds() if prev_time else 0.0
        rise_rate = calculate_rise_rate(calibrated["water_level_cm"], prev_cm, dt)
        calibrated["rise_rate_cm_min"] = rise_rate

        self.latest_telemetry = calibrated
        self.last_received_at = now
        self.recent_history.append(dict(calibrated))

        logger.info(
            f"REAL ESP32 Telemetry Ingested: WaterRaw={calibrated['water_raw']} ({calibrated['water_level_cm']} cm), "
            f"RainRaw={calibrated['rain_raw']} (Intensity {calibrated['rain_intensity']})"
        )

        return calibrated

    async def _async_handle_notification(self, payload: Dict[str, Any]):
        """Persists direct BLE notification to database and broadcasts WebSocket."""
        from app.core.database import SessionLocal
        from app.services.telemetry_service import telemetry_service
        db = SessionLocal()
        try:
            await telemetry_service.process_real_esp32_telemetry(db=db, raw_data=payload)
        except Exception as e:
            logger.warning(f"Error persisting direct BLE telemetry: {e}")
        finally:
            db.close()

    def notification_handler(self, sender: Any, data: bytearray):
        """
        Direct Bleak notification handler matching ble_test.py logic.
        """
        try:
            text = data.decode()
            payload = json.loads(text)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._async_handle_notification(payload))
            except RuntimeError:
                self.ingest_payload(payload)
        except Exception as e:
            logger.warning(f"BLE notification parse error: {e}")

    async def _run_loop(self):
        """
        Background resilient BLE runner using Bleak.
        """
        from bleak import BleakScanner, BleakClient

        self.is_running = True
        logger.info(f"BLE Collector background loop started for ESP32: {self.target_address}")

        while self.is_running:
            try:
                logger.info("Scanning for ESP32 BLE peripheral...")
                devices = await BleakScanner.discover(timeout=5.0)
                target = None
                for d in devices:
                    if d.address.upper() == self.target_address:
                        target = d
                        break

                if not target:
                    logger.debug("ESP32 not found in current scan window. Retrying in 4s...")
                    await asyncio.sleep(4.0)
                    continue

                logger.info(f"FOUND ESP32 at {target.address}. Establishing BleakClient connection...")
                async with BleakClient(target) as client:
                    self.client = client
                    self.is_connected = client.is_connected
                    logger.info(f"BLE CONNECTED to ESP32: {client.is_connected}")

                    await client.start_notify(self.char_uuid, self.notification_handler)
                    logger.info(f"Subscribed to notify characteristic {self.char_uuid}")

                    while client.is_connected and self.is_running:
                        await asyncio.sleep(1.0)

            except Exception as e:
                self.is_connected = False
                logger.warning(f"BLE connection loop error: {e}. Retrying in 5s...")
                await asyncio.sleep(5.0)

        self.is_connected = False
        logger.info("BLE Collector loop stopped.")

    def start(self):
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()


ble_collector = BLECollector()
