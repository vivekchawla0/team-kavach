import React from 'react';
import { MetricCards } from '@/components/dashboard/MetricCards';
import { SensorMap } from '@/components/sensors/SensorMap';
import { WaterLevelTrends } from '@/components/sensors/WaterLevelTrends';
import { RecentAlerts } from '@/components/alerts/RecentAlerts';
import { LiveSensorTable } from '@/components/sensors/LiveSensorTable';
import { RainfallForecast } from '@/components/weather/RainfallForecast';
import { EnvironmentalData } from '@/components/weather/EnvironmentalData';
import { SystemStatus } from '@/components/dashboard/SystemStatus';
import { SimulatorToolbar } from '@/components/dashboard/SimulatorToolbar';
import { SensorDetailModal } from '@/components/sensors/SensorDetailModal';

export const DashboardPage: React.FC = () => {
  return (
    <div className="p-6 sm:p-8 flex flex-col gap-6 max-w-[1680px] w-full mx-auto">
      {/* 5 Top KPI Cards */}
      <MetricCards />

      {/* Primary Grid: Map, Trends, Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-5">
          <SensorMap />
        </div>
        <div className="lg:col-span-4">
          <WaterLevelTrends />
        </div>
        <div className="lg:col-span-3">
          <RecentAlerts />
        </div>
      </div>

      {/* Secondary Grid: Live Table, Forecast, Environmental & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        <div className="lg:col-span-5">
          <LiveSensorTable />
        </div>
        <div className="lg:col-span-4">
          <RainfallForecast />
        </div>
        <div className="lg:col-span-3 flex flex-col gap-4">
          <EnvironmentalData />
          <SystemStatus />
        </div>
      </div>

      {/* Interactive Simulator Toolbar & Detail Modal */}
      <SimulatorToolbar />
      <SensorDetailModal />
    </div>
  );
};
