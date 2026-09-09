"""
JAL SUCHAK — Physical Prototype Sensor Calibration & Telemetry Parsing Engine
Implements piecewise-linear interpolation for water level (cm) and rain sensor intensity
based on physical laboratory calibration curves.
"""
from datetime import datetime, timezone
from typing import List, Tuple, Dict, Any, Optional

# Physical Water Level Calibration Table (Raw ADC -> Centimeters)
# Calibrated for 15 cm physical prototype
WATER_CALIBRATION_TABLE: List[Tuple[float, float]] = [
    (0.0, 0.0),
    (222.0, 1.0),
    (672.0, 2.0),
    (943.0, 3.0),
    (1181.0, 4.0),
    (1396.0, 5.0),
    (1700.0, 6.0),
    (1980.0, 7.0),
    (2100.0, 8.0),
    (2300.0, 9.0),
]

# Rain Sensor Intensity Calibration Table (Raw ADC -> Intensity Level 0..10)
RAIN_CALIBRATION_TABLE: List[Tuple[float, float]] = [
    (0.0, 0.0),
    (298.0, 1.0),
    (392.0, 2.0),
    (600.0, 3.0),
    (800.0, 4.0),
    (1000.0, 5.0),
    (1210.0, 6.0),
    (1510.0, 7.0),
    (1720.0, 8.0),
    (1900.0, 9.0),
]

# Physical Prototype Flood Risk Thresholds (15 cm height)
PROTOTYPE_THRESHOLDS = {
    "SAFE_MAX_CM": 6.0,
    "WARNING_MAX_CM": 10.0,
    "DANGER_MAX_CM": 13.0,
    "CRITICAL_MAX_CM": 15.0,
}


def raw_water_to_cm(raw: float) -> float:
    """
    Converts raw ADC reading to calibrated water depth in centimeters
    using piecewise-linear interpolation between measured calibration points.
    """
    if raw <= 0.0:
        return 0.0

    table = WATER_CALIBRATION_TABLE
    # If smaller than first point
    if raw <= table[0][0]:
        return table[0][1]

    # Piecewise interpolation between table points
    for i in range(len(table) - 1):
        r1, cm1 = table[i]
        r2, cm2 = table[i + 1]
        if r1 <= raw <= r2:
            if r2 == r1:
                return cm1
            fraction = (raw - r1) / (r2 - r1)
            cm = cm1 + fraction * (cm2 - cm1)
            return round(cm, 2)

    # Extrapolate linearly beyond the last calibration point (2300 -> 9.0 cm)
    # Using slope of last segment (2100 -> 8cm to 2300 -> 9cm => 1cm / 200 raw = 0.005 cm/unit)
    last_r, last_cm = table[-1]
    prev_r, prev_cm = table[-2]
    slope = (last_cm - prev_cm) / (last_r - prev_r)
    extrapolated_cm = last_cm + (raw - last_r) * slope
    # Cap at maximum physical prototype container depth of 15.0 cm
    return round(min(15.0, max(0.0, extrapolated_cm)), 2)


def raw_rain_to_intensity(raw: float) -> float:
    """
    Converts raw rain ADC reading to Rain Sensor Intensity (Level 0..10)
    using piecewise-linear interpolation.
    NOTE: Stated as Rain Intensity, not mm/hr, to preserve physical sensor accuracy.
    """
    if raw <= 0.0:
        return 0.0

    table = RAIN_CALIBRATION_TABLE
    if raw <= table[0][0]:
        return table[0][1]

    for i in range(len(table) - 1):
        r1, int1 = table[i]
        r2, int2 = table[i + 1]
        if r1 <= raw <= r2:
            if r2 == r1:
                return int1
            fraction = (raw - r1) / (r2 - r1)
            intensity = int1 + fraction * (int2 - int1)
            return round(intensity, 2)

    # Extrapolate linearly beyond last point (1900 -> 9.0)
    last_r, last_int = table[-1]
    prev_r, prev_int = table[-2]
    slope = (last_int - prev_int) / (last_r - prev_r)
    extrapolated = last_int + (raw - last_r) * slope
    return round(min(10.0, max(0.0, extrapolated)), 2)


def calculate_rise_rate(current_cm: float, prev_cm: Optional[float], dt_seconds: float) -> float:
    """
    Calculates water rise rate in cm/min based on actual timestamps.
    """
    if prev_cm is None or dt_seconds <= 0.5:
        return 0.0
    dt_minutes = dt_seconds / 60.0
    rate = (current_cm - prev_cm) / dt_minutes
    return round(rate, 2)


def evaluate_prototype_risk(water_cm: float) -> Dict[str, Any]:
    """
    Evaluates flood risk for the 15 cm physical prototype:
    SAFE: 0-6 cm
    WARNING: >6-10 cm
    DANGER: >10-13 cm
    CRITICAL: >13-15 cm
    """
    if water_cm >= PROTOTYPE_THRESHOLDS["DANGER_MAX_CM"]:
        return {
            "level": "CRITICAL",
            "score": 95.0,
            "text": "Critical flood danger — Immediate evacuation advisory",
            "color": "#e11d48",
        }
    elif water_cm >= PROTOTYPE_THRESHOLDS["WARNING_MAX_CM"]:
        return {
            "level": "DANGER",
            "score": 80.0,
            "text": "Danger threshold exceeded — High flood risk",
            "color": "#ea580c",
        }
    elif water_cm >= PROTOTYPE_THRESHOLDS["SAFE_MAX_CM"]:
        return {
            "level": "WARNING",
            "score": 60.0,
            "text": "Warning threshold reached — Elevated river level",
            "color": "#f59e0b",
        }
    else:
        return {
            "level": "SAFE",
            "score": 20.0,
            "text": "Nominal prototype level — Normal river conditions",
            "color": "#10b981",
        }


def parse_esp32_payload(raw_data: Dict[str, Any], device_id: str = "ESP32-FW-001") -> Dict[str, Any]:
    """
    Parses raw incoming ESP32 JSON payload from ble_test.py and applies calibration.
    Input keys from ESP32:
      - water_level_raw (or water_raw)
      - water_percentage
      - rain_raw
      - rain_percentage
    """
    water_raw = int(raw_data.get("water_level_raw", raw_data.get("water_raw", 0)))
    water_pct = float(raw_data.get("water_percentage", 0.0))
    rain_raw = int(raw_data.get("rain_raw", 0))
    rain_pct = float(raw_data.get("rain_percentage", 0.0))

    water_cm = raw_water_to_cm(water_raw)
    rain_intensity = raw_rain_to_intensity(rain_raw)
    risk_info = evaluate_prototype_risk(water_cm)

    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "device_id": device_id,
        "timestamp": now_iso,
        "water_raw": water_raw,
        "water_percentage": water_pct,
        "water_level_cm": water_cm,
        "rain_raw": rain_raw,
        "rain_percentage": rain_pct,
        "rain_intensity": rain_intensity,
        "flood_risk_level": risk_info["level"],
        "flood_risk_text": risk_info["text"],
        "flood_risk_score": risk_info["score"],
        "bluetooth_status": "ONLINE",
        "calibration_status": "CALIBRATED",
    }
