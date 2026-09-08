# FloodWatch ESP32 Telemetry Station Documentation

## 1. Hardware Architecture & Pinout

| Peripheral | Component | ESP32 GPIO | Notes |
|---|---|---|---|
| **Ultrasonic Distance** | JSN-SR04T / HC-SR04 | TRIG: GPIO 5, ECHO: GPIO 18 | Waterproof transducer mounted above river cross-section |
| **Rain Gauge** | Tipping Bucket (0.28 mm/pulse)| GPIO 19 | Hardware interrupt with debouncing |
| **Soil Moisture** | Capacitive Soil Probe v1.2 | GPIO 34 (ADC1_CH6) | Corrosion-resistant capacitive sensing |
| **Tilt / Impact** | MPU-6050 (6-DOF Accelerometer) | SDA: GPIO 21, SCL: GPIO 22 | Detects pole bending or floating debris strikes |
| **Battery Monitor** | 18650 Li-Ion + Solar Charger | GPIO 35 (ADC1_CH7) | 100kΩ / 100kΩ voltage divider |
| **Status LED** | Onboard LED | GPIO 2 | Blinks on transmission / WiFi state |

---

## 2. Ultrasonic Level Calculation Formula

The sensor is mounted securely on a bridge girder or mast at a known calibrated height $H_{\text{bed}}$ above the lowest riverbed profile.

$$\text{Water Level} = H_{\text{bed}} - \left( \frac{t_{\text{echo}} \times v_{\text{sound}}(T)}{2} \right)$$

where:
$$v_{\text{sound}}(T) = 331.3 + (0.606 \times T_{^\circ\text{C}}) \quad (\text{m/s})$$

---

## 3. Telemetry Payload Contract

Each telemetry packet is dispatched via HTTP POST to `/api/v1/telemetry` with header `X-API-Key: fw_live_sec_99a8b7c6d5e4`:

```json
{
  "sensor_id": "FW-007",
  "water_level": 2.84,
  "rainfall": 18.0,
  "soil_moisture": 92.0,
  "temperature": 12.0,
  "battery": 87.0,
  "signal_strength": -65.0,
  "inclination_x": 0.2,
  "inclination_y": 0.4
}
```

---

## 4. Flashing Instructions

1. Install the Arduino IDE or PlatformIO.
2. Install the required libraries:
   - `ArduinoJson` (v6 or v7)
   - `Adafruit MPU6050`
   - `Adafruit Unified Sensor`
3. Select board `ESP32 Dev Module`.
4. Update `WIFI_SSID`, `WIFI_PASS`, and `SERVER_URL`.
5. Connect your ESP32 via USB and upload.
