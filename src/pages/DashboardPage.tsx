import React from 'react';
import { MetricCards } from '@/components/dashboard/MetricCards';
import { FloodMonitoringMap } from '@/components/sensors/FloodMonitoringMap';
import { WaterLevelTrends } from '@/components/sensors/WaterLevelTrends';
import { RainfallForecast } from '@/components/weather/RainfallForecast';
import { EnvironmentalData } from '@/components/weather/EnvironmentalData';
import { RecentAlerts } from '@/components/alerts/RecentAlerts';
import { BlynkStatusCard } from '@/components/dashboard/BlynkStatusCard';
import { SensorDetailModal } from '@/components/sensors/SensorDetailModal';
import { ESP32DebugPanel } from '@/components/dashboard/ESP32DebugPanel';
import { ShieldCheck } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const DashboardPage: React.FC = () => {
  const { summary } = useDashboard();

  return (
    <div className="px-5 sm:px-8 lg:px-10 py-5 sm:py-6 flex flex-col gap-6 w-full max-w-[1920px] mx-auto">
      {/* 1. 4 Primary Hydrological & Risk KPI Cards */}
      <MetricCards />

      {/* 2. Primary Operations Grid: Geospatial Map (7 cols) & Water Level Intelligence (5 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <FloodMonitoringMap />
        </div>
        <div className="lg:col-span-5 flex flex-col">
          <WaterLevelTrends />
        </div>
      </div>

      {/* 3. Tertiary Operations Grid: Exactly 3 Balanced Cards (Rainfall, Live Weather, Blynk Connection) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        {/* Rainfall Intelligence */}
        <div className="lg:col-span-4 flex flex-col">
          <RainfallForecast />
        </div>

        {/* Live Weather */}
        <div className="lg:col-span-4 flex flex-col">
          <EnvironmentalData />
        </div>

        {/* Blynk IoT Connection */}
        <div className="lg:col-span-4 flex flex-col">
          <BlynkStatusCard />
        </div>
      </div>

      {/* 4. Full-Width Real-Data Alert Center matching reference */}
      <div className="w-full">
        <RecentAlerts />
      </div>

      {/* 5. Collapsible ESP32 Physical Prototype Live Diagnostics Panel */}
      <div className="w-full">
        <ESP32DebugPanel />
      </div>

      {/* Subtle Operational Telemetry Health Bar */}
      <div className="w-full py-2 px-4 rounded-xl bg-slate-200/50 border border-slate-200/80 flex items-center justify-between text-xs text-slate-500 font-medium">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          <span>Core Subsystems: {summary?.system_status || 'All Systems Nominal'}</span>
        </div>
        <div className="flex items-center gap-3 text-[11px]">
          <span>Station FW-001 (Barpeta)</span>
          <span>•</span>
          <span>FastAPI Backend v1</span>
          <span>•</span>
          <span>Blynk Cloud IoT</span>
        </div>
      </div>

      {/* Interactive Detail Modal */}
      <SensorDetailModal />
    </div>
  );
};
