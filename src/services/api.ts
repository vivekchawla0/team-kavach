import {
  DashboardSummary,
  Sensor,
  Alert,
  WeatherCurrent,
  WeatherForecastSummary,
  WaterLevelAnalytics,
  TimeRange,
  SimulatorScenario,
  MLSensorForecastResponse,
} from '@/types';

const API_BASE = window.location.origin.includes(':8000')
  ? `${window.location.origin}/api/v1`
  : (import.meta.env.VITE_API_BASE || '/api/v1');

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API error ${res.status}: ${errorText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  getDashboardSummary: async (): Promise<DashboardSummary> => {
    const res = await fetch(`${API_BASE}/dashboard/summary`);
    return handleResponse<DashboardSummary>(res);
  },

  getSensors: async (status?: string, search?: string): Promise<Sensor[]> => {
    const params = new URLSearchParams();
    if (status && status !== 'ALL') params.append('status', status);
    if (search) params.append('search', search);
    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE}/sensors${qs}`);
    return handleResponse<Sensor[]>(res);
  },

  getSensorById: async (sensorId: string): Promise<Sensor> => {
    const res = await fetch(`${API_BASE}/sensors/${sensorId}`);
    return handleResponse<Sensor>(res);
  },

  getWaterLevelTrends: async (sensorId: string, range: TimeRange = '24H'): Promise<WaterLevelAnalytics> => {
    const res = await fetch(`${API_BASE}/analytics/water-level/${sensorId}?range=${range}`);
    return handleResponse<WaterLevelAnalytics>(res);
  },

  getAlerts: async (limit: number = 5, status?: string, severity?: string): Promise<Alert[]> => {
    const params = new URLSearchParams({ limit: String(limit) });
    if (status && status !== 'ALL') params.append('status', status);
    if (severity) params.append('severity', severity);
    const res = await fetch(`${API_BASE}/alerts?${params.toString()}`);
    return handleResponse<Alert[]>(res);
  },

  getWeatherCurrent: async (): Promise<WeatherCurrent> => {
    const res = await fetch(`${API_BASE}/weather/current`);
    return handleResponse<WeatherCurrent>(res);
  },

  getWeatherForecast: async (): Promise<WeatherForecastSummary> => {
    const res = await fetch(`${API_BASE}/weather/forecast`);
    return handleResponse<WeatherForecastSummary>(res);
  },

  triggerScenario: async (scenario: SimulatorScenario): Promise<{ status: string; scenario: string }> => {
    const res = await fetch(`${API_BASE}/simulation/scenario?scenario=${scenario}`, {
      method: 'POST',
    });
    return handleResponse<{ status: string; scenario: string }>(res);
  },

  acknowledgeAlert: async (alertId: number, userName: string = 'Administrator'): Promise<Alert> => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge?user_name=${encodeURIComponent(userName)}`, {
      method: 'POST',
    });
    return handleResponse<Alert>(res);
  },

  resolveAlert: async (alertId: number, resolvedBy: string = 'Administrator', notes?: string): Promise<Alert> => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolved_by: resolvedBy, notes }),
    });
    return handleResponse<Alert>(res);
  },

  getMLForecast: async (sensorId: string): Promise<MLSensorForecastResponse> => {
    const res = await fetch(`${API_BASE}/ml/forecast/${sensorId}`);
    return handleResponse<MLSensorForecastResponse>(res);
  },

  getMLModels: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/ml/models`);
    return handleResponse<any>(res);
  },
};

