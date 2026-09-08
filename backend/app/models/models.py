import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="VIEWER", nullable=False)  # ADMIN, OPERATOR, VIEWER
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class Sensor(Base):
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "FW-007"
    name = Column(String(255), nullable=False)                               # e.g., "Erft Bridge"
    location_name = Column(String(255), nullable=False)                      # e.g., "Bad Münstereifel Center"
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(50), default="NORMAL", index=True, nullable=False) # NORMAL, WARNING, CRITICAL, OFFLINE
    warning_threshold = Column(Float, default=3.0, nullable=False)
    danger_threshold = Column(Float, default=4.0, nullable=False)
    current_water_level = Column(Float, default=1.20)
    water_rise_rate = Column(Float, default=0.00)
    battery = Column(Float, default=100.0)
    signal_strength = Column(Float, default=-65.0)
    inclination_x = Column(Float, default=0.0)
    inclination_y = Column(Float, default=0.0)
    installation_date = Column(DateTime(timezone=True), default=utcnow)
    last_seen = Column(DateTime(timezone=True), default=utcnow, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    readings = relationship("SensorReading", back_populates="sensor", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="sensor", cascade="all, delete-orphan")
    status_history = relationship("SensorStatusHistory", back_populates="sensor", cascade="all, delete-orphan")
    risk_assessments = relationship("FloodRiskAssessment", back_populates="sensor", cascade="all, delete-orphan")
    ml_predictions = relationship("MLPrediction", back_populates="sensor", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensors.sensor_id", ondelete="CASCADE"), nullable=False, index=True)
    water_level = Column(Float, nullable=False)
    water_rise_rate = Column(Float, default=0.0, nullable=False)
    rainfall = Column(Float, default=0.0, nullable=False)
    soil_moisture = Column(Float, default=0.0, nullable=False)
    temperature = Column(Float, default=0.0, nullable=False)
    battery = Column(Float, default=100.0, nullable=False)
    signal_strength = Column(Float, default=-65.0, nullable=False)
    inclination_x = Column(Float, default=0.0, nullable=False)
    inclination_y = Column(Float, default=0.0, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sensor = relationship("Sensor", back_populates="readings")

    __table_args__ = (
        Index("idx_readings_sensor_timestamp", "sensor_id", "timestamp"),
    )


class SensorStatusHistory(Base):
    __tablename__ = "sensor_status_history"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensors.sensor_id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(String(255), nullable=True)
    changed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sensor = relationship("Sensor", back_populates="status_history")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensors.sensor_id", ondelete="SET NULL"), nullable=True, index=True)
    type = Column(String(100), nullable=False)         # HIGH_WATER_LEVEL, RAPID_WATER_RISE, etc.
    severity = Column(String(50), nullable=False, index=True) # CRITICAL, WARNING, INFO, RESOLVED
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(50), default="ACTIVE", index=True, nullable=False) # ACTIVE, ACKNOWLEDGED, RESOLVED
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(255), nullable=True)

    sensor = relationship("Sensor", back_populates="alerts")
    history = relationship("AlertHistory", back_populates="alert", cascade="all, delete-orphan")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False)  # CREATED, ACKNOWLEDGED, RESOLVED
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    alert = relationship("Alert", back_populates="history")


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    location_name = Column(String(255), default="Bad Münstereifel, Germany", nullable=False)
    temperature = Column(Float, default=12.0, nullable=False)
    humidity = Column(Float, default=78.0, nullable=False)
    wind_speed = Column(Float, default=15.0, nullable=False)
    rainfall_current = Column(Float, default=18.0, nullable=False)
    atmospheric_pressure = Column(Float, default=1012.0, nullable=False)
    weather_condition = Column(String(100), default="Light Rain", nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


class WeatherForecast(Base):
    __tablename__ = "weather_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_time = Column(DateTime(timezone=True), nullable=False, index=True)
    expected_rainfall_mm = Column(Float, nullable=False)
    probability_percent = Column(Float, default=0.0, nullable=False)
    temperature = Column(Float, default=12.0, nullable=False)
    condition = Column(String(100), default="Rain", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class FloodRiskAssessment(Base):
    __tablename__ = "flood_risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensors.sensor_id", ondelete="SET NULL"), nullable=True, index=True)
    risk_score = Column(Float, nullable=False)             # 0 to 100
    risk_level = Column(String(50), nullable=False)        # LOW, MODERATE, HIGH, CRITICAL
    water_level_score = Column(Float, default=0.0)
    rainfall_score = Column(Float, default=0.0)
    soil_moisture_score = Column(Float, default=0.0)
    rise_rate_score = Column(Float, default=0.0)
    forecast_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)

    sensor = relationship("Sensor", back_populates="risk_assessments")


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(String(255), nullable=False)
    category = Column(String(100), default="GENERAL", nullable=False)
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), nullable=False)  # 24H, 7D, 30D, CUSTOM
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    summary_data = Column(Text, nullable=False)       # JSON serialized metrics
    generated_by = Column(String(255), default="System", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String(50), ForeignKey("sensors.sensor_id", ondelete="CASCADE"), nullable=False, index=True)
    prediction_timestamp = Column(DateTime(timezone=True), default=utcnow, index=True, nullable=False)
    horizon_hours = Column(Integer, nullable=False)                         # 1, 3, or 6
    predicted_water_level = Column(Float, nullable=False)                  # Point prediction (m)
    uncertainty_lower = Column(Float, nullable=False)                      # Dedicated 5th percentile (m)
    uncertainty_upper = Column(Float, nullable=False)                      # Dedicated 95th percentile (m)
    flood_probability = Column(Float, nullable=False)                      # Calibrated flood probability % (0 - 100)
    model_version = Column(String(50), default="xgb_direct_v1", nullable=False)
    feature_importance = Column(Text, nullable=True)                       # JSON dict of feature contributions
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    sensor = relationship("Sensor", back_populates="ml_predictions")

    __table_args__ = (
        Index("idx_ml_sensor_horizon_time", "sensor_id", "horizon_hours", "prediction_timestamp"),
    )


class MLModelRegistry(Base):
    __tablename__ = "ml_model_registry"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)
    horizon_hours = Column(Integer, nullable=False)
    model_type = Column(String(50), nullable=False)                        # POINT_REGRESSOR, QUANTILE_05, QUANTILE_95
    algorithm = Column(String(100), default="XGBoost", nullable=False)
    objective = Column(String(100), nullable=False)                        # reg:squarederror or reg:quantileerror
    quantile_alpha = Column(Float, nullable=True)                          # 0.05, 0.95, or null
    evaluation_metrics = Column(Text, nullable=True)                       # JSON metrics dict (MAE, RMSE, R2, coverage)
    features_used = Column(Text, nullable=True)                            # JSON list of feature names
    training_date = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    status = Column(String(50), default="ACTIVE", nullable=False)          # ACTIVE, RETIRED
    filepath = Column(String(255), nullable=False)

