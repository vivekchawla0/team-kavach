from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ==========================================
# SENSOR SCHEMAS
# ==========================================

class SensorBase(BaseModel):
    sensor_id: str = Field(..., example="FW-001")
    name: str = Field(..., example="Barpeta Station FW-001")
    location_name: str = Field(..., example="Barpeta Station, Assam")
    latitude: float = Field(..., example=26.3200)
    longitude: float = Field(..., example=91.0050)
    warning_threshold: float = Field(default=3.0, example=3.0)
    danger_threshold: float = Field(default=4.0, example=4.0)


class SensorCreate(SensorBase):
    pass


class SensorUpdate(BaseModel):
    name: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    warning_threshold: Optional[float] = None
    danger_threshold: Optional[float] = None
    status: Optional[str] = None


class SensorResponse(SensorBase):
    id: int
    status: str
    current_water_level: float
    water_rise_rate: float
    battery: float
    signal_strength: float
    inclination_x: float
    inclination_y: float
    installation_date: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# TELEMETRY & READING SCHEMAS (Unified ESP32 / Simulator contract)
# ==========================================

class SensorReadingCreate(BaseModel):
    sensor_id: str = Field(..., example="FW-007")
    water_level: float = Field(..., example=2.84)
    water_rise_rate: Optional[float] = Field(default=None, example=0.12)
    rainfall: float = Field(..., example=18.0)
    soil_moisture: float = Field(..., example=92.0)
    temperature: float = Field(..., example=12.0)
    battery: float = Field(..., example=87.0)
    signal_strength: float = Field(..., example=-65.0)
    inclination_x: float = Field(default=0.0, example=0.2)
    inclination_y: float = Field(default=0.0, example=0.4)
    timestamp: Optional[datetime] = Field(default=None, example="2026-09-06T14:32:00Z")


class SensorReadingResponse(SensorReadingCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# ALERT SCHEMAS
# ==========================================

class AlertResponse(BaseModel):
    id: int
    sensor_id: Optional[str]
    type: str
    severity: str  # CRITICAL, WARNING, INFO, RESOLVED
    title: str
    message: str
    status: str    # ACTIVE, ACKNOWLEDGED, RESOLVED
    is_read: bool
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AlertResolveRequest(BaseModel):
    resolved_by: str = Field(default="Administrator")
    notes: Optional[str] = None


# ==========================================
# FLOOD RISK SCHEMAS
# ==========================================

class RiskFactorItem(BaseModel):
    factor_name: str
    score: float       # 0 - 100
    contribution: str  # Low, Moderate, High, Very High
    weight: float
    description: str


class FloodRiskResponse(BaseModel):
    overall_score: float              # 0 to 100
    overall_level: str                # LOW, MODERATE, HIGH, CRITICAL
    status_label: str
    status_description: str
    factors: Dict[str, RiskFactorItem]
    assessed_at: datetime
    sensor_id: Optional[str] = None


class FloodRiskHistoryItem(BaseModel):
    timestamp: datetime
    risk_score: float
    risk_level: str


# ==========================================
# WEATHER SCHEMAS
# ==========================================

class WeatherCurrentResponse(BaseModel):
    location_name: str
    temperature: float
    humidity: float
    wind_speed: float
    rainfall_current: float
    atmospheric_pressure: float
    weather_condition: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WeatherForecastItem(BaseModel):
    forecast_time: datetime
    expected_rainfall_mm: float
    probability_percent: float
    temperature: float
    condition: str

    model_config = ConfigDict(from_attributes=True)


class WeatherForecastSummary(BaseModel):
    total_rainfall_24h_mm: float
    peak_rainfall_mm_hr: float
    peak_time_window: str
    heavy_rain_probability_percent: float
    hourly: List[WeatherForecastItem]


# ==========================================
# DASHBOARD SUMMARY & ANALYTICS SCHEMAS
# ==========================================

class MetricTrend(BaseModel):
    value: Any
    unit: str
    trend_percent: Optional[float] = None
    trend_direction: Optional[str] = None  # up, down, neutral
    comparison_text: Optional[str] = None


class DashboardSummaryResponse(BaseModel):
    total_sensors: int
    online_sensors: int
    offline_sensors: int
    sensors_breakdown: Dict[str, int]  # normal, warning, critical, offline
    average_water_level_m: float
    water_level_change_percent: float
    current_rainfall_mm_hr: float
    rainfall_change_percent: float
    flood_risk_level: str             # LOW, MODERATE, HIGH, CRITICAL
    flood_risk_score: float
    flood_risk_text: str
    soil_moisture_percent: float
    soil_moisture_change_percent: float
    system_status: str                # All Systems Operational
    last_updated: datetime
    # Optional ML Decision-Support Fields (Phase 4B)
    ml_flood_probability: Optional[float] = None
    ml_advisory_level: Optional[str] = None
    ml_forecast_6h_m: Optional[float] = None
    ml_confidence_corridor: Optional[str] = None



class WaterLevelTrendPoint(BaseModel):
    timestamp: datetime
    time_label: str
    water_level: float
    water_rise_rate: float
    safe_level: float
    warning_level: float
    danger_level: float


class WaterLevelAnalyticsResponse(BaseModel):
    sensor_id: str
    sensor_name: str
    time_range: str
    current_level: float
    rise_rate: float
    status: str
    safe_threshold: float
    warning_threshold: float
    danger_threshold: float
    data_points: List[WaterLevelTrendPoint]
