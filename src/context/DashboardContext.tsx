import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import {
  Sensor,
  DashboardSummary,
  Alert,
  WeatherCurrent,
  WeatherForecastSummary,
  WaterLevelAnalytics,
  TimeRange,
  SimulatorScenario,
  WebSocketTelemetryEvent,
  RealTelemetry,
} from '@/types';
import { api } from '@/services/api';
import { wsClient } from '@/services/websocket';

interface DashboardContextType {
  summary: DashboardSummary | null;
  sensors: Sensor[];
  selectedSensorId: string;
  trendsData: WaterLevelAnalytics | null;
  trendRange: TimeRange;
  alerts: Alert[];
  weatherCurrent: WeatherCurrent | null;
  weatherForecast: WeatherForecastSummary | null;
  mapFilter: string;
  tableSearch: string;
  tableStatus: string;
  selectedDetailSensor: Sensor | null;
  activeScenario: SimulatorScenario | null;
  isLoading: boolean;
  realTelemetry: RealTelemetry | null;
  telemetryHistory: any[];
  setMapFilter: (filter: string) => void;
  setTableSearch: (term: string) => void;
  setTableStatus: (status: string) => void;
  setTrendRange: (range: TimeRange) => void;
  selectSensorForTrends: (sensorId: string) => void;
  setSelectedDetailSensor: (sensor: Sensor | null) => void;
  triggerScenario: (scenario: SimulatorScenario) => Promise<void>;
  refreshDashboard: () => Promise<void>;
  acknowledgeAlert: (alertId: number) => Promise<void>;
  resolveAlert: (alertId: number) => Promise<void>;
}

const DashboardContext = createContext<DashboardContextType | undefined>(undefined);

export const DashboardProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [selectedSensorId, setSelectedSensorId] = useState<string>('FW-001');
  const [trendsData, setTrendsData] = useState<WaterLevelAnalytics | null>(null);
  const [trendRange, setTrendRange] = useState<TimeRange>('24H');
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [weatherCurrent, setWeatherCurrent] = useState<WeatherCurrent | null>(null);
  const [weatherForecast, setWeatherForecast] = useState<WeatherForecastSummary | null>(null);
  const [realTelemetry, setRealTelemetry] = useState<RealTelemetry | null>(null);
  const [telemetryHistory, setTelemetryHistory] = useState<any[]>([]);

  const [mapFilter, setMapFilter] = useState<string>('ALL');
  const [tableSearch, setTableSearch] = useState<string>('');
  const [tableStatus, setTableStatus] = useState<string>('ALL');
  const [selectedDetailSensor, setSelectedDetailSensor] = useState<Sensor | null>(null);
  const [activeScenario, setActiveScenario] = useState<SimulatorScenario | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Load trends for a sensor
  const loadTrends = useCallback(async (sensorId: string, range: TimeRange) => {
    try {
      const data = await api.getWaterLevelTrends(sensorId, range);
      setTrendsData(data);
    } catch (err) {
      console.warn('Failed to load water trends:', err);
    }
  }, []);

  // Main refresh routine
  const refreshDashboard = useCallback(async () => {
    try {
      const [sum, sList, al, wCurr, wFore, realTelem, telemHist] = await Promise.all([
        api.getDashboardSummary(),
        api.getSensors(),
        api.getAlerts(5),
        api.getWeatherCurrent().catch(() => null),
        api.getWeatherForecast().catch(() => null),
        api.getLatestTelemetry().catch(() => null),
        api.getTelemetryHistory(50).catch(() => null),
      ]);

      setSummary(sum);
      setSensors(sList);
      setAlerts(al);
      if (wCurr) setWeatherCurrent(wCurr);
      if (wFore) setWeatherForecast(wFore);
      if (realTelem) setRealTelemetry(realTelem);
      if (telemHist?.readings) setTelemetryHistory(telemHist.readings);

      await loadTrends(selectedSensorId, trendRange);
    } catch (err) {
      console.warn('Error refreshing dashboard:', err);
    } finally {
      setIsLoading(false);
    }
  }, [selectedSensorId, trendRange, loadTrends]);

  // Initial load
  useEffect(() => {
    refreshDashboard();
  }, [refreshDashboard]);

  // Periodic 5-second polling for real ESP32 telemetry & offline heartbeat
  useEffect(() => {
    const timer = setInterval(() => {
      api.getLatestTelemetry()
        .then((rt) => {
          if (rt) setRealTelemetry(rt);
        })
        .catch(() => {});
      api.getTelemetryHistory(50)
        .then((hist) => {
          if (hist?.readings) setTelemetryHistory(hist.readings);
        })
        .catch(() => {});
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  // Handle range or sensor change
  useEffect(() => {
    loadTrends(selectedSensorId, trendRange);
  }, [selectedSensorId, trendRange, loadTrends]);

  // WebSocket subscription for zero-refresh real-time updates
  useEffect(() => {
    const handleWs = (evt: WebSocketTelemetryEvent) => {
      // Ingest live real ESP32 telemetry
      if (evt.real_telemetry) {
        setRealTelemetry(evt.real_telemetry);
      }

      if (evt.event === 'telemetry_update' && evt.sensor) {
        setSensors((prev) =>
          prev.map((s) =>
            s.sensor_id === evt.sensor!.sensor_id
              ? {
                  ...s,
                  current_water_level: evt.sensor!.water_level,
                  water_rise_rate: evt.sensor!.rise_rate,
                  status: evt.sensor!.status,
                  battery: evt.sensor!.battery,
                  last_seen: evt.sensor!.last_seen,
                }
              : s
          )
        );

        // If active sensor in trends chart, update trends curve
        if (evt.sensor.sensor_id === selectedSensorId) {
          loadTrends(selectedSensorId, trendRange);
        }

        // Prepend new alerts if any
        if (evt.alerts && evt.alerts.length > 0) {
          setAlerts((prev) => [...evt.alerts!, ...prev].slice(0, 10));
        }

        // Update dashboard summary metrics softly
        api.getDashboardSummary().then(setSummary).catch(() => {});
      } else if (evt.event === 'scenario_changed') {
        refreshDashboard();
      }
    };

    const unsubscribe = wsClient.subscribe(handleWs);
    return () => unsubscribe();
  }, [selectedSensorId, trendRange, loadTrends, refreshDashboard]);

  const selectSensorForTrends = (sensorId: string) => {
    setSelectedSensorId(sensorId);
  };

  const triggerScenario = async (scenario: SimulatorScenario) => {
    setActiveScenario(scenario);
    await api.triggerScenario(scenario);
    await refreshDashboard();
  };

  const acknowledgeAlert = async (alertId: number) => {
    await api.acknowledgeAlert(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: 'ACKNOWLEDGED', is_read: true } : a))
    );
  };

  const resolveAlert = async (alertId: number) => {
    await api.resolveAlert(alertId);
    setAlerts((prev) =>
      prev.map((a) => (a.id === alertId ? { ...a, status: 'RESOLVED', is_read: true } : a))
    );
  };

  return (
    <DashboardContext.Provider
      value={{
        summary,
        sensors,
        selectedSensorId,
        trendsData,
        trendRange,
        alerts,
        weatherCurrent,
        weatherForecast,
        mapFilter,
        tableSearch,
        tableStatus,
        selectedDetailSensor,
        activeScenario,
        isLoading,
        realTelemetry,
        telemetryHistory,
        setMapFilter,
        setTableSearch,
        setTableStatus,
        setTrendRange,
        selectSensorForTrends,
        setSelectedDetailSensor,
        triggerScenario,
        refreshDashboard,
        acknowledgeAlert,
        resolveAlert,
      }}
    >
      {children}
    </DashboardContext.Provider>
  );
};

export const useDashboard = () => {
  const context = useContext(DashboardContext);
  if (!context) {
    throw new Error('useDashboard must be used within a DashboardProvider');
  }
  return context;
};
