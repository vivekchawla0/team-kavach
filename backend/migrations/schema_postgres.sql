-- ====================================================================
-- FLOODWATCH: PostgreSQL Production Database Schema
-- Location: Bad Münstereifel, Germany (Erft River Basin)
-- ====================================================================

-- 1. USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- 2. SENSORS TABLE
CREATE TABLE IF NOT EXISTS sensors (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'NORMAL',
    warning_threshold DOUBLE PRECISION NOT NULL DEFAULT 3.0,
    danger_threshold DOUBLE PRECISION NOT NULL DEFAULT 4.0,
    current_water_level DOUBLE PRECISION NOT NULL DEFAULT 1.20,
    water_rise_rate DOUBLE PRECISION NOT NULL DEFAULT 0.00,
    battery DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    signal_strength DOUBLE PRECISION NOT NULL DEFAULT -65.0,
    inclination_x DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    inclination_y DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    installation_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sensors_sensor_id ON sensors(sensor_id);
CREATE INDEX IF NOT EXISTS idx_sensors_status ON sensors(status);
CREATE INDEX IF NOT EXISTS idx_sensors_last_seen ON sensors(last_seen);

-- 3. SENSOR READINGS TABLE (High frequency time series)
CREATE TABLE IF NOT EXISTS sensor_readings (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    water_level DOUBLE PRECISION NOT NULL,
    water_rise_rate DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    rainfall DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    soil_moisture DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    temperature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    battery DOUBLE PRECISION NOT NULL DEFAULT 100.0,
    signal_strength DOUBLE PRECISION NOT NULL DEFAULT -65.0,
    inclination_x DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    inclination_y DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_readings_sensor_timestamp ON sensor_readings(sensor_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON sensor_readings(timestamp DESC);

-- 4. SENSOR STATUS HISTORY TABLE
CREATE TABLE IF NOT EXISTS sensor_status_history (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) NOT NULL REFERENCES sensors(sensor_id) ON DELETE CASCADE,
    previous_status VARCHAR(50) NOT NULL,
    new_status VARCHAR(50) NOT NULL,
    reason VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_status_history_sensor ON sensor_status_history(sensor_id);

-- 5. ALERTS TABLE
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id) ON DELETE SET NULL,
    type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by VARCHAR(255)
);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts(status, severity);
CREATE INDEX IF NOT EXISTS idx_alerts_created_at ON alerts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_sensor_id ON alerts(sensor_id);

-- 6. ALERT HISTORY TABLE
CREATE TABLE IF NOT EXISTS alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_alert_history_alert_id ON alert_history(alert_id);

-- 7. WEATHER DATA TABLE
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    location_name VARCHAR(255) NOT NULL DEFAULT 'Bad Münstereifel, Germany',
    temperature DOUBLE PRECISION NOT NULL DEFAULT 12.0,
    humidity DOUBLE PRECISION NOT NULL DEFAULT 78.0,
    wind_speed DOUBLE PRECISION NOT NULL DEFAULT 15.0,
    rainfall_current DOUBLE PRECISION NOT NULL DEFAULT 18.0,
    atmospheric_pressure DOUBLE PRECISION NOT NULL DEFAULT 1012.0,
    weather_condition VARCHAR(100) NOT NULL DEFAULT 'Light Rain',
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_weather_recorded_at ON weather_data(recorded_at DESC);

-- 8. WEATHER FORECASTS TABLE
CREATE TABLE IF NOT EXISTS weather_forecasts (
    id SERIAL PRIMARY KEY,
    forecast_time TIMESTAMP WITH TIME ZONE NOT NULL,
    expected_rainfall_mm DOUBLE PRECISION NOT NULL,
    probability_percent DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    temperature DOUBLE PRECISION NOT NULL DEFAULT 12.0,
    condition VARCHAR(100) NOT NULL DEFAULT 'Rain',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_forecast_time ON weather_forecasts(forecast_time);

-- 9. FLOOD RISK ASSESSMENTS TABLE
CREATE TABLE IF NOT EXISTS flood_risk_assessments (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES sensors(sensor_id) ON DELETE SET NULL,
    risk_score DOUBLE PRECISION NOT NULL,
    risk_level VARCHAR(50) NOT NULL,
    water_level_score DOUBLE PRECISION DEFAULT 0.0,
    rainfall_score DOUBLE PRECISION DEFAULT 0.0,
    soil_moisture_score DOUBLE PRECISION DEFAULT 0.0,
    rise_rate_score DOUBLE PRECISION DEFAULT 0.0,
    forecast_score DOUBLE PRECISION DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_risk_sensor_created ON flood_risk_assessments(sensor_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_risk_created ON flood_risk_assessments(created_at DESC);

-- 10. SYSTEM SETTINGS TABLE
CREATE TABLE IF NOT EXISTS system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) NOT NULL UNIQUE,
    value VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'GENERAL',
    description VARCHAR(255),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_settings_key ON system_settings(key);

-- 11. REPORTS TABLE
CREATE TABLE IF NOT EXISTS reports (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    start_date TIMESTAMP WITH TIME ZONE NOT NULL,
    end_date TIMESTAMP WITH TIME ZONE NOT NULL,
    summary_data TEXT NOT NULL,
    generated_by VARCHAR(255) NOT NULL DEFAULT 'System',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_reports_created ON reports(created_at DESC);
