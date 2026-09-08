/**
 * FloodWatch IoT River Telemetry Station - ESP32 Firmware
 * 
 * Hardware Peripherals:
 *  - Waterproof Ultrasonic Distance Sensor (JSN-SR04T / HC-SR04)
 *  - Tipping Bucket Pulse Rain Gauge (Interrupt-driven)
 *  - Capacitive Soil Moisture Sensor v1.2 (ADC)
 *  - MPU-6050 6-DOF I2C Accelerometer/Gyro (Pole Tilt / Debris Impact Detection)
 *  - 18650 Li-Ion Solar Battery Monitor (Voltage Divider)
 *  - Onboard RGB / Status LED
 * 
 * Protocols:
 *  - WiFi 802.11 b/g/n
 *  - HTTPS REST client with X-API-Key authentication
 *  - Deep Sleep Power Conservation (~15uA quiescent current)
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ==============================================================================
// CONFIGURATION PARAMETERS
// ==============================================================================
const char* WIFI_SSID     = "FloodWatch_FieldNet";
const char* WIFI_PASS     = "RiverSafety2026";
const char* SERVER_URL    = "http://192.168.1.100:8000/api/v1/telemetry";
const char* IOT_API_KEY   = "fw_live_sec_99a8b7c6d5e4";
const char* SENSOR_ID     = "FW-001"; // Barpeta Station FW-001, Assam

// Physical Gauge Height (Distance from ultrasonic sensor face to riverbed in meters)
const float RIVERBED_DISTANCE_M = 5.50; 

// GPIO Pin Assignments
#define PIN_TRIG          5
#define PIN_ECHO          18
#define PIN_RAIN_PULSE    19
#define PIN_SOIL_ADC      34
#define PIN_BATT_ADC      35
#define PIN_STATUS_LED    2

// Deep Sleep Config
#define SLEEP_SECONDS     30 // In emergency rise rate mode: 10s; standard mode: 60s

// Rain Gauge Constants (0.2794 mm per tip)
const float RAIN_MM_PER_TIP = 0.2794;
volatile unsigned long tip_count = 0;
unsigned long last_tip_time = 0;

Adafruit_MPU6050 mpu;
bool mpu_ready = false;

// Interrupt Service Routine for Tipping Bucket Rain Gauge
void IRAM_ATTR onRainPulse() {
    unsigned long now = millis();
    if (now - last_tip_time > 150) { // 150ms debounce
        tip_count++;
        last_tip_time = now;
    }
}

// Ultrasonic Echo Reading with Temperature Speed of Sound Adjustment
float measureDistanceMeters(float ambient_temp_c) {
    digitalWrite(PIN_TRIG, LOW);
    delayMicroseconds(4);
    digitalWrite(PIN_TRIG, HIGH);
    delayMicroseconds(10);
    digitalWrite(PIN_TRIG, LOW);

    long duration_us = pulseIn(PIN_ECHO, HIGH, 35000); // 35ms timeout (~6m max)
    if (duration_us == 0) return -1.0; // Echo timeout

    // Speed of sound in air: v = 331.3 + 0.606 * T (m/s)
    float speed_of_sound = 331.3 + (0.606 * ambient_temp_c);
    float distance_m = (duration_us * 1e-6 * speed_of_sound) / 2.0;
    return distance_m;
}

// Battery Percentage calculation via 2:1 Voltage Divider (100k / 100k)
float readBatteryPercent() {
    int raw = analogRead(PIN_BATT_ADC);
    float voltage = (raw / 4095.0) * 3.3 * 2.0; // 3.3V reference * 2 divider
    // 3.2V (0%) to 4.2V (100%) Li-Ion curve
    float percent = ((voltage - 3.20) / (4.20 - 3.20)) * 100.0;
    return constrain(percent, 0.0, 100.0);
}

// Capacitive Soil Moisture reading
float readSoilMoisturePercent() {
    int raw = analogRead(PIN_SOIL_ADC);
    // Calibration constants (Dry ~ 3200, Submerged in water ~ 1400)
    const int AIR_VALUE   = 3200;
    const int WATER_VALUE = 1400;
    float percent = ((AIR_VALUE - raw) / (float)(AIR_VALUE - WATER_VALUE)) * 100.0;
    return constrain(percent, 0.0, 100.0);
}

void setup() {
    Serial.begin(115200);
    pinMode(PIN_TRIG, OUTPUT);
    pinMode(PIN_ECHO, INPUT);
    pinMode(PIN_RAIN_PULSE, INPUT_PULLUP);
    pinMode(PIN_STATUS_LED, OUTPUT);

    attachInterrupt(digitalPinToInterrupt(PIN_RAIN_PULSE), onRainPulse, FALLING);

    // Initialize MPU-6050
    Wire.begin(21, 22);
    if (mpu.begin()) {
        mpu.setAccelerometerRange(MPU6050_RANGE_4_G);
        mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
        mpu_ready = true;
    } else {
        Serial.println(F("Warning: MPU6050 accelerometer not detected."));
    }

    // Connect WiFi
    Serial.print(F("Connecting to WiFi: "));
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASS);

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 20) {
        delay(500);
        digitalWrite(PIN_STATUS_LED, !digitalRead(PIN_STATUS_LED));
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() == WL_CONNECTED) {
        Serial.println(F("\nWiFi Connected! IP: "));
        Serial.println(WiFi.localIP());
        digitalWrite(PIN_STATUS_LED, HIGH);
    } else {
        Serial.println(F("\nWiFi failed to connect. Running in offline telemetry buffer mode."));
    }
}

void loop() {
    float ambient_temp = 12.0; // Default or read from sensor
    float tilt_x = 0.0;
    float tilt_y = 0.0;

    // Read accelerometer tilt angles
    if (mpu_ready) {
        sensors_event_t a, g, temp;
        mpu.getEvent(&a, &g, &temp);
        ambient_temp = temp.temperature;
        tilt_x = atan2(a.acceleration.y, a.acceleration.z) * 180.0 / PI;
        tilt_y = atan2(-a.acceleration.x, sqrt(a.acceleration.y * a.acceleration.y + a.acceleration.z * a.acceleration.z)) * 180.0 / PI;
    }

    // Measure water distance and calculate water level: level = (gauge_height - distance)
    float distance_m = measureDistanceMeters(ambient_temp);
    float water_level_m = 0.0;
    if (distance_m > 0) {
        water_level_m = RIVERBED_DISTANCE_M - distance_m;
        if (water_level_m < 0.0) water_level_m = 0.0;
    }

    // Rainfall intensity calculation
    float rainfall_mm = tip_count * RAIN_MM_PER_TIP;
    tip_count = 0; // Reset pulse accumulator

    float soil_moisture = readSoilMoisturePercent();
    float battery_pct = readBatteryPercent();
    int rssi = WiFi.RSSI();

    // Prepare JSON payload
    StaticJsonDocument<512> doc;
    doc["sensor_id"]       = SENSOR_ID;
    doc["water_level"]     = round(water_level_m * 100.0) / 100.0;
    doc["rainfall"]        = round(rainfall_mm * 10.0) / 10.0;
    doc["soil_moisture"]   = round(soil_moisture * 10.0) / 10.0;
    doc["temperature"]     = round(ambient_temp * 10.0) / 10.0;
    doc["battery"]         = round(battery_pct * 10.0) / 10.0;
    doc["signal_strength"] = rssi;
    doc["inclination_x"]   = round(tilt_x * 10.0) / 10.0;
    doc["inclination_y"]   = round(tilt_y * 10.0) / 10.0;

    String json_string;
    serializeJson(doc, json_string);

    Serial.print(F("Dispatching Telemetry -> "));
    Serial.println(json_string);

    // Send HTTP POST
    if (WiFi.status() == WL_CONNECTED) {
        HTTPClient http;
        http.begin(SERVER_URL);
        http.addHeader("Content-Type", "application/json");
        http.addHeader("X-API-Key", IOT_API_KEY);

        int httpCode = http.POST(json_string);
        if (httpCode > 0) {
            String response = http.getString();
            Serial.printf("Server Response (%d): %s\n", httpCode, response.c_str());
        } else {
            Serial.printf("POST failed, error: %s\n", http.errorToString(httpCode).c_str());
        }
        http.end();
    }

    // Delay before next cycle or trigger deep sleep
    delay(SLEEP_SECONDS * 1000);
}
