from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.blynk_service import blynk_service

router = APIRouter()


class BlynkStatusResponse(BaseModel):
    success: bool
    connected: bool
    device: str
    template: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    cloud_reachable: Optional[bool] = None


class BlynkTestResponse(BaseModel):
    success: bool
    message: str
    device: Optional[str] = None
    connected: Optional[bool] = None


class BlynkAlertRequest(BaseModel):
    action: Optional[str] = "trigger"  # "trigger" or "clear"
    pin: Optional[str] = "v0"
    value: Optional[int] = 1


class BlynkAlertResponse(BaseModel):
    success: bool
    message: str
    device: Optional[str] = None
    pin: Optional[str] = None
    value: Optional[int] = None
    alert_active: Optional[bool] = None


@router.get("/status", response_model=BlynkStatusResponse, summary="Get Blynk device connectivity status")
async def get_blynk_status():
    """
    Check connectivity status of FloodWatch-Station-01 with Blynk Cloud.
    Does not expose sensitive credentials.
    """
    result = await blynk_service.get_device_status()
    return result


@router.post("/test", response_model=BlynkTestResponse, summary="Test Blynk Cloud connection")
async def test_blynk_connection():
    """
    Test connectivity between backend and Blynk Cloud for FloodWatch-Station-01.
    """
    result = await blynk_service.test_connection()
    return result


@router.post("/alert", response_model=BlynkAlertResponse, summary="Trigger or clear alert on connected Blynk hardware")
async def trigger_blynk_alert(payload: Optional[BlynkAlertRequest] = None):
    """
    Transmit emergency alert signal to FloodWatch-Station-01 via Blynk Cloud.
    Updates Virtual Pin (default V0) to value 1 (trigger) or 0 (clear).
    """
    req = payload or BlynkAlertRequest()
    target_value = 1 if req.action == "trigger" else 0
    if req.value is not None:
        target_value = req.value

    result = await blynk_service.trigger_device_alert(pin=req.pin or "v0", value=target_value)
    return result

