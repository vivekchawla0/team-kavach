export type SensorStatus = 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE';
export type RiskLevel = 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL';
export type AlertSeverity = 'CRITICAL' | 'WARNING' | 'INFO' | 'RESOLVED' | 'SYSTEM';
export type AlertStatus = 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
export type TimeRange = '24H' | '7D' | '30D';
export type SimulatorScenario = 'normal' | 'storm' | 'flood' | 'reset';

export interface Sensor {
  id: number;
  sensor_id: string;
  name: string;
  location_name: string;
  latitude: number;
  longitude: number;
  status: SensorStatus;
  warning_threshold: number;
  danger_threshold: number;
  current_water_level: number;
  water_rise_rate: number;
  battery: number;
  signal_strength: number;
  inclination_x: number;
  inclination_y: number;
  installation_date: string;
  last_seen: string;
  created_at: string;
  updated_at: string;
}

export interface SensorReading {
  id: number;
  sensor_id: string;
  water_level: number;
  water_rise_rate: number;
  rainfall: number;
  soil_moisture: number;
  temperature: number;
  battery: number;
  signal_strength: number;
  inclination_x: number;
  inclination_y: number;
  timestamp: string;
  created_at: string;
}

export interface DashboardSummary {
  total_sensors: number;
  online_sensors: number;
  offline_sensors: number;
  sensors_breakdown: {
    normal: number;
    warning: number;
    critical: number;
    offline: number;
  };
  average_water_level_m: number;
  water_level_change_percent: number;
  current_rainfall_mm_hr: number;
  rainfall_change_percent: number;
  flood_risk_level: RiskLevel;
  flood_risk_score: number;
  flood_risk_text: string;
  soil_moisture_percent: number;
  soil_moisture_change_percent: number;
  system_status: string;
  last_updated: string;
  ml_flood_probability?: number;
  ml_advisory_level?: string;
  ml_forecast_6h_m?: number;
  ml_confidence_corridor?: string;
}

export interface Alert {
  id: number;
  sensor_id: string | null;
  type: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  status: AlertStatus;
  is_read: boolean;
  created_at: string;
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface WaterLevelTrendPoint {
  timestamp: string;
  time_label: string;
  water_level: number;
  water_rise_rate: number;
  safe_level: number;
  warning_level: number;
  danger_level: number;
  ml_forecast?: number;
  ml_lower?: number;
  ml_upper?: number;
}

export interface WaterLevelAnalytics {
  sensor_id: string;
  sensor_name: string;
  time_range: string;
  current_level: number;
  rise_rate: number;
  status: SensorStatus;
  safe_threshold: number;
  warning_threshold: number;
  danger_threshold: number;
  data_points: WaterLevelTrendPoint[];
}

export interface WeatherCurrent {
  location_name: string;
  temperature: number;
  humidity: number;
  wind_speed: number;
  rainfall_current: number;
  atmospheric_pressure: number;
  weather_condition: string;
  recorded_at: string;
}

export interface WeatherForecastItem {
  forecast_time: string;
  expected_rainfall_mm: number;
  probability_percent: number;
  temperature: number;
  condition: string;
}

export interface WeatherForecastSummary {
  total_rainfall_24h_mm: number;
  peak_rainfall_mm_hr: number;
  peak_time_window: string;
  heavy_rain_probability_percent: number;
  hourly: WeatherForecastItem[];
}

export interface MLInfluenceItem {
  feature: string;
  tier: string;
  importance: number;
  current_value: number;
}

export interface MLHorizonForecast {
  horizon_hours: number;
  predicted_water_level: number;
  uncertainty_lower: number;
  uncertainty_upper: number;
  interval_width: number;
  confidence_interval_level: string;
  flood_probability: number;
  top_influences: MLInfluenceItem[];
}

export interface MLSensorForecastResponse {
  sensor_id: string;
  timestamp: string;
  current_water_level: number;
  forecasts: {
    '1h': MLHorizonForecast;
    '3h': MLHorizonForecast;
    '6h': MLHorizonForecast;
  };
  overall_flood_probability: number;
  advisory_level: string;
  advisory_message: string;
  disclaimer: string;
}

export interface WebSocketTelemetryEvent {
  event: 'telemetry_update' | 'scenario_changed';
  sensor?: {
    sensor_id: string;
    name: string;
    water_level: number;
    rise_rate: number;
    status: SensorStatus;
    battery: number;
    last_seen: string;
  };
  reading?: {
    id: number;
    water_level: number;
    rainfall: number;
    soil_moisture: number;
    timestamp: string;
  };
  alerts?: Alert[];
  risk?: {
    score: number;
    level: RiskLevel;
  };
  ml?: {
    advisory_level?: string;
    advisory_message?: string;
    overall_flood_probability?: number;
    forecasts?: Record<string, MLHorizonForecast>;
  };
  scenario?: string;
  timestamp?: string;
}

export interface BlynkStatusResponse {
  success: boolean;
  connected: boolean;
  device: string;
  template?: string;
  status?: string;
  message?: string;
  cloud_reachable?: boolean;
}

export interface BlynkTestResponse {
  success: boolean;
  message: string;
  device?: string;
  connected?: boolean;
}

export interface BlynkAlertResponse {
  success: boolean;
  message: string;
  device?: string;
  pin?: string;
  value?: number;
  alert_active?: boolean;
}


