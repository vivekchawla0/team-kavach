# FloodWatch: Physical Hardware Implementation & Testing Checklist

This actionable checklist outlines the exact chronological sequence to transition FloodWatch from the verified software platform to a complete physical working prototype.

---

## Phase 1: Procurement & Bench Preparation

- [ ] **Procure Microcontroller:**
  - [ ] 1x ESP32 DevKit v1 (30-pin or 38-pin NodeMCU ESP-WROOM-32)
  - [ ] 1x Micro-USB data cable (ensure it supports data, not charging-only)
- [ ] **Procure Transducers & Sensors:**
  - [ ] 1x JSN-SR04T v3.0 waterproof ultrasonic distance sensor (or HC-SR04P for indoor benchtop)
  - [ ] 1x Capacitive Soil Moisture Sensor v1.2 (analog output)
  - [ ] 1x Tipping Bucket Rain Gauge Sensor (reed switch pulse output) or capacitive rain board
  - [ ] 1x GY-521 (MPU-6050 6-axis accelerometer & gyroscope)
- [ ] **Procure Circuit & Safety Components:**
  - [ ] 1x Solderless Breadboard (830 tie-points)
  - [ ] 1x Pack Dupont Jumper Wires (M-to-M, M-to-F, F-to-F)
  - [ ] Resistors: 2x $1\,\text{k}\Omega$, 2x $2\,\text{k}\Omega$, 2x $100\,\text{k}\Omega$, 3x $220\,\Omega$
  - [ ] 1x 5V Active Buzzer
  - [ ] 3x 5mm LEDs (Red, Green, Blue)
- [ ] **Procure Demonstration Container:**
  - [ ] 1x Transparent Acrylic or Plastic Storage Container ($40\times30\times20\,\text{cm}$)
  - [ ] 1x 5V USB Submersible Miniature Water Pump ($120\,\text{L/h}$) with flexible silicone tubing
  - [ ] Small sample of natural soil / sand for the moisture testing tray

---

## Phase 2: Software Development Environment Setup

- [ ] **Install Arduino IDE 2.x:**
  - [ ] Download and install latest Arduino IDE from [arduino.cc](https://www.arduino.cc).
  - [ ] Add ESP32 Board URL in Preferences: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  - [ ] Install `esp32 by Espressif Systems` via Boards Manager.
  - [ ] Select Board: `DOIT ESP32 DEVKIT V1` and select the active COM port.
- [ ] **Install Required Arduino Libraries:**
  - [ ] `ArduinoJson` (by Benoit Blanchon - version 6.x or 7.x)
  - [ ] `Adafruit MPU6050` (by Adafruit)
  - [ ] `Adafruit Unified Sensor` (by Adafruit)
- [ ] **Verify ESP32 Communication:**
  - [ ] Upload standard `Blink` sketch to test onboard LED (GPIO 2).
  - [ ] Open Serial Monitor at 115200 baud; confirm clean bootloader messages.

---

## Phase 3: Individual Sensor Bench Testing

- [ ] **Test 1: Ultrasonic Distance Gauge (JSN-SR04T / HC-SR04)**
  - [ ] Wire VCC $\to$ 5V, GND $\to$ GND, TRIG $\to$ GPIO 5.
  - [ ] **CRITICAL:** Place $1\,\text{k}\Omega / 2\,\text{k}\Omega$ voltage divider on Echo pin; connect midpoint to GPIO 18.
  - [ ] Point transducer at flat wall; move from 30cm to 100cm; verify measured distance accuracy within $\pm 5\,\text{mm}$.
- [ ] **Test 2: Tipping Bucket Rain Gauge**
  - [ ] Wire Terminal 1 $\to$ GPIO 19, Terminal 2 $\to$ GND.
  - [ ] Configure GPIO 19 as `INPUT_PULLUP`.
  - [ ] Manually tip the seesaw bucket; verify Serial Monitor registers falling-edge interrupt pulse.
- [ ] **Test 3: Capacitive Soil Moisture Sensor**
  - [ ] Wire VCC $\to$ 3.3V, GND $\to$ GND, AOUT $\to$ GPIO 34 (ADC1_CH6).
  - [ ] Measure dry air raw ADC count (expect $\approx 3200$); record as `AIR_VALUE`.
  - [ ] Submerge sensor blade in glass of water (keep top electronics dry); record raw ADC (expect $\approx 1400$) as `WATER_VALUE`.
- [ ] **Test 4: MPU-6050 Accelerometer**
  - [ ] Wire VCC $\to$ 3.3V, GND $\to$ GND, SDA $\to$ GPIO 21, SCL $\to$ GPIO 22.
  - [ ] Run I2C Scanner sketch; confirm device detected at address `0x68`.
  - [ ] Tilt breadboard; verify X and Y inclination angles calculate accurately from $-90^{\circ}$ to $+90^{\circ}$.

---

## Phase 4: Full Integrated Assembly & Enclosure Mounting

- [ ] **Mount Overhead Sensor Gantry:**
  - [ ] Secure crossbar above the acrylic river channel at a fixed height ($H_{\text{datum}} = 30.0\,\text{cm}$ above dry floor).
  - [ ] Mount JSN-SR04T transducer facing vertically down with zero tilt.
- [ ] **Install Soil Basin & Rain Collector:**
  - [ ] Position soil tray adjacent to channel. Insert capacitive probe firmly into soil.
  - [ ] Mount tipping bucket above or beside soil tray.
- [ ] **Partition Dry Electronics Bay:**
  - [ ] Position breadboard, ESP32, and voltage divider in isolated dry corner of box.
  - [ ] Secure status LED and active buzzer.
  - [ ] Check all ground wires share a single common ground bus rail.

---

## Phase 5: Network Configuration & Firmware Flashing

- [ ] **Configure Station Firmware (`iot/esp32_firmware/esp32_floodwatch_station.ino`):**
  - [ ] Set `WIFI_SSID` and `WIFI_PASS` to your local 2.4GHz Wi-Fi network.
  - [ ] Find your laptop's local IPv4 address (e.g. `ipconfig` $\to$ `192.168.1.50`).
  - [ ] Set `SERVER_URL = "http://192.168.1.50:8000/api/v1/telemetry";`
  - [ ] Confirm `IOT_API_KEY = "fw_live_sec_99a8b7c6d5e4";`
  - [ ] Configure `RIVERBED_DISTANCE_M = 0.30;` (matches gantry height).
- [ ] **Compile and Upload:**
  - [ ] Flash firmware to ESP32.
  - [ ] Open Serial Monitor at 115200 baud.
  - [ ] Confirm Wi-Fi connection succeeds and prints `WiFi Connected! IP: 192.168.1.XXX`.

---

## Phase 6: End-to-End Live System Verification

- [ ] **Verify Backend Acceptance:**
  - [ ] Ensure FastAPI backend server is running (`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`).
  - [ ] Inspect backend terminal: Confirm incoming `POST /api/v1/telemetry HTTP/1.1 200 OK`.
- [ ] **Verify Database Ingestion:**
  - [ ] Query PostgreSQL: `SELECT * FROM sensor_readings ORDER BY id DESC LIMIT 1;`.
  - [ ] Confirm new reading row is written with timestamp matching current second.
  - [ ] Confirm `sensors` table updates `current_water_level` for station `FW-007`.
  - [ ] Confirm `ml_predictions` persists 1h, 3h, 6h records with non-crossing quantile bounds.
- [ ] **Verify Dashboard Real-Time Visuals:**
  - [ ] Open `http://localhost:5173` (or `http://localhost:8000`) in browser.
  - [ ] Look at Station `FW-007` on Leaflet map: Marker shows live water level.
  - [ ] Open Water Level Trends chart for `FW-007`: Curve reflects physical water height.
  - [ ] Click `FW-007` row in Live Sensor Table: Modal displays live readings + ML Predictive Intelligence.

---

## Phase 7: Live Physical Scenario Demonstrations

- [ ] **Demonstration 1: Normal Dry Flow**
  - [ ] Maintain shallow water in channel ($5\,\text{cm}$ physical depth).
  - [ ] Verify Dashboard shows **LOW** risk with green status indicators.
- [ ] **Demonstration 2: Infiltration Storm**
  - [ ] Pour water into rain gauge; moisten soil tray.
  - [ ] Verify Dashboard updates rain rate ($> 20\,\text{mm/hr}$) and soil moisture ($> 85\%$).
  - [ ] Verify Risk Engine elevates to **HIGH** risk.
- [ ] **Demonstration 3: Catastrophic Surge & Overtopping**
  - [ ] Rapidly add water to river channel past the $26.6\,\text{cm}$ physical mark.
  - [ ] Verify system immediately triggers **CRITICAL Danger Alarm**.
  - [ ] Confirm hardware buzzer sounds and red emergency banner displays on dashboard.
  - [ ] Confirm ML predictions remain advisory while deterministic safety alerts protect the site.
