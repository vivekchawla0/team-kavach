"""
Blynk Cloud Integration Service for JAL SUCHAK
Communicates securely with Blynk Cloud REST API (Blynk IoT 2.0).
Strict Security Rule: NEVER log or expose BLYNK_AUTH_TOKEN in responses or logs.
"""

import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger("floodwatch.blynk")


class BlynkService:
    """Service to manage connectivity and status with Blynk Cloud."""

    def __init__(self):
        self.template_id = settings.BLYNK_TEMPLATE_ID
        self.template_name = settings.BLYNK_TEMPLATE_NAME
        self.device_name = settings.BLYNK_DEVICE_NAME
        self.base_url = settings.BLYNK_SERVER_URL.rstrip("/")
        self.timeout = 5.0  # 5 seconds timeout for cloud calls

    @property
    def auth_token(self) -> str:
        return settings.BLYNK_AUTH_TOKEN.strip()

    @property
    def is_token_configured(self) -> bool:
        token = self.auth_token
        # Check that token exists and is not a placeholder
        return bool(token and token not in ("<AUTH_TOKEN>", "<AUTH_TOKEN_FROM_ENV>", "your_blynk_token_here"))

    async def get_device_status(self) -> Dict[str, Any]:
        """
        Query Blynk Cloud for device online status.
        Uses: GET /isHardwareConnected?token={token}
        """
        if not self.is_token_configured:
            return {
                "success": False,
                "connected": False,
                "device": self.device_name,
                "template": self.template_name,
                "status": "NOT_CONFIGURED",
                "message": "Blynk Auth Token is not configured in backend environment",
                "cloud_reachable": False,
            }

        url = f"{self.base_url}/isHardwareConnected"
        params = {"token": self.auth_token}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params)

                is_connected = False
                if response.status_code == 200:
                    is_connected = response.text.strip().lower() == "true"

                # Check if device is actively transmitting datastreams on Blynk Cloud (/getAll)
                if not is_connected and response.status_code == 200:
                    try:
                        all_resp = await client.get(f"{self.base_url}/getAll", params=params)
                        if all_resp.status_code == 200:
                            data = all_resp.json()
                            if isinstance(data, dict) and len(data) > 0:
                                is_connected = True
                    except Exception as ex:
                        logger.debug("Blynk datastream check: %s", ex)

            if response.status_code == 200:
                return {
                    "success": True,
                    "connected": is_connected,
                    "device": self.device_name,
                    "template": self.template_name,
                    "status": "ONLINE" if is_connected else "OFFLINE",
                    "message": (
                        "Blynk device is online and connected"
                        if is_connected
                        else "Blynk Cloud reached, but device is currently offline"
                    ),
                    "cloud_reachable": True,
                }
            elif response.status_code in (400, 401, 403):
                logger.warning("Blynk authentication rejected by cloud (HTTP %s)", response.status_code)
                return {
                    "success": False,
                    "connected": False,
                    "device": self.device_name,
                    "template": self.template_name,
                    "status": "INVALID_TOKEN",
                    "message": "Blynk Auth Token is invalid or expired",
                    "cloud_reachable": True,
                }
            else:
                logger.warning("Blynk returned unexpected HTTP %s", response.status_code)
                return {
                    "success": False,
                    "connected": False,
                    "device": self.device_name,
                    "template": self.template_name,
                    "status": "API_ERROR",
                    "message": f"Blynk Cloud returned HTTP {response.status_code}",
                    "cloud_reachable": True,
                }

        except httpx.TimeoutException:
            logger.warning("Timeout while connecting to Blynk Cloud API")
            return {
                "success": False,
                "connected": False,
                "device": self.device_name,
                "template": self.template_name,
                "status": "TIMEOUT",
                "message": "Unable to connect to Blynk Cloud: Request timed out",
                "cloud_reachable": False,
            }
        except Exception as e:
            logger.warning("Network exception communicating with Blynk Cloud: %s", type(e).__name__)
            return {
                "success": False,
                "connected": False,
                "device": self.device_name,
                "template": self.template_name,
                "status": "UNREACHABLE",
                "message": "Unable to connect to Blynk Cloud: Network error",
                "cloud_reachable": False,
            }

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test whether the backend can communicate with Blynk Cloud using the configured credentials.
        """
        if not self.is_token_configured:
            return {
                "success": False,
                "message": "Blynk connection failed: Auth Token not configured in backend .env",
                "device": self.device_name,
            }

        status_result = await self.get_device_status()

        if status_result.get("cloud_reachable") and status_result.get("status") not in ("INVALID_TOKEN", "NOT_CONFIGURED"):
            is_conn = status_result.get("connected", False)
            return {
                "success": True,
                "message": "Blynk connection successful - Device online" if is_conn else "Blynk connection successful",
                "device": self.device_name,
                "connected": is_conn,
            }
        else:
            msg = status_result.get("message", "Blynk connection failed")
            return {
                "success": False,
                "message": f"Blynk connection failed: {msg}" if "failed" not in msg.lower() else msg,
                "device": self.device_name,
            }

    async def update_virtual_pin(self, pin: str, value: Any) -> Dict[str, Any]:
        """
        Update a Virtual Pin on Blynk Cloud.
        Calls: GET /update?token={token}&{pin}={value}
        """
        if not self.is_token_configured:
            return {
                "success": False,
                "message": "Blynk Auth Token not configured in backend .env",
                "device": self.device_name,
            }

        pin_clean = pin.lower()
        if not pin_clean.startswith("v"):
            pin_clean = f"v{pin_clean}"

        url = f"{self.base_url}/update"
        params = {"token": self.auth_token, pin_clean: value}

        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params)

            if response.status_code == 200:
                logger.info("Successfully updated Blynk pin %s to value %s", pin_clean, value)
                return {
                    "success": True,
                    "message": f"Signal sent to {self.device_name} (Pin {pin_clean.upper()} = {value})",
                    "device": self.device_name,
                    "pin": pin_clean.upper(),
                    "value": value,
                }
            elif response.status_code in (400, 401, 403):
                return {
                    "success": False,
                    "message": f"Blynk rejected update for pin {pin_clean.upper()}",
                    "device": self.device_name,
                }
            else:
                return {
                    "success": False,
                    "message": f"Blynk Cloud returned HTTP {response.status_code}",
                    "device": self.device_name,
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "message": "Connection timed out sending alert to Blynk",
                "device": self.device_name,
            }
        except Exception as e:
            logger.warning("Error updating Blynk virtual pin: %s", type(e).__name__)
            return {
                "success": False,
                "message": "Network error sending alert to Blynk",
                "device": self.device_name,
            }

    async def trigger_device_alert(self, pin: str = "v0", value: int = 1) -> Dict[str, Any]:
        """
        Trigger emergency alert signal on the connected hardware device.
        """
        res = await self.update_virtual_pin(pin=pin, value=value)
        if res.get("success"):
            res["alert_active"] = (value != 0)
            res["message"] = (
                f"🚨 Emergency alert sent to {self.device_name} ({pin.upper()}={value})"
                if value != 0
                else f"Alert cleared on {self.device_name} ({pin.upper()}=0)"
            )
        return res

    async def get_virtual_pin(self, pin: str) -> Dict[str, Any]:
        """Read virtual pin from Blynk."""
        pin_clean = pin.lower()
        if not pin_clean.startswith("v"):
            pin_clean = f"v{pin_clean}"

        url = f"{self.base_url}/get"
        params = {"token": self.auth_token, pin_clean: ""}
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url, params=params)
            if response.status_code == 200:
                return {"success": True, "pin": pin_clean.upper(), "value": response.text.strip()}
            return {"success": False, "pin": pin_clean.upper(), "message": "Failed reading pin"}
        except Exception:
            return {"success": False, "pin": pin_clean.upper(), "message": "Error reading pin"}


blynk_service = BlynkService()

