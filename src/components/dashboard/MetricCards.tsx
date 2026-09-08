import React from 'react';
import { Waves, Droplets, CloudRain, AlertTriangle, Sprout, ArrowUp, ArrowDown } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const MetricCards: React.FC = () => {
  const { summary } = useDashboard();

  const totalSensors = summary?.total_sensors ?? 13;
  const onlineSensors = summary?.online_sensors ?? 12;
  const offlineSensors = summary?.offline_sensors ?? 1;
  const avgWater = summary?.average_water_level_m ?? 1.42;
  const rainfall = summary?.current_rainfall_mm_hr ?? 18;
  const riskLevel = summary?.flood_risk_level ?? 'LOW';
  const riskText = summary?.flood_risk_text ?? 'No immediate risk';
  const soilMoisture = summary?.soil_moisture_percent ?? 92;

  const riskBadgeStyles: Record<string, string> = {
    LOW: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    MODERATE: 'bg-amber-50 text-amber-700 border-amber-200',
    HIGH: 'bg-orange-50 text-orange-700 border-orange-200',
    CRITICAL: 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse',
  };

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4" aria-label="Key Hydrological Metrics">
      {/* 1. Total Sensors */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex items-start gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-sky-100 flex items-center justify-center shrink-0 text-sky-700">
          <Waves className="w-5 h-5 text-sky-600" />
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-500">Total Sensors</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {totalSensors}
            </span>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
              ↑ 0
            </span>
          </div>
          <span className="text-[11.5px] text-slate-500 font-medium mt-1">
            {onlineSensors} Online | {offlineSensors} Offline
          </span>
        </div>
      </div>

      {/* 2. Average Water Level */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex items-start gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-cyan-100 flex items-center justify-center shrink-0 text-cyan-700">
          <Droplets className="w-5 h-5 text-cyan-600" />
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-500">Average Water Level</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {avgWater.toFixed(2)} m
            </span>
          </div>
          <span className="text-[11.5px] font-medium text-emerald-600 flex items-center gap-1 mt-1">
            <ArrowDown className="w-3 h-3 text-emerald-600" />
            <span>12%</span> vs. last hour
          </span>
        </div>
      </div>

      {/* 3. Current Rainfall */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex items-start gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-indigo-100 flex items-center justify-center shrink-0 text-indigo-700">
          <CloudRain className="w-5 h-5 text-indigo-600" />
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-500">Current Rainfall</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {Math.round(rainfall)} mm/hr
            </span>
          </div>
          <span className="text-[11.5px] font-medium text-rose-600 flex items-center gap-1 mt-1">
            <ArrowUp className="w-3 h-3 text-rose-600" />
            <span>40%</span> vs. last hour
          </span>
        </div>
      </div>

      {/* 4. Flood Risk Level */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex items-start gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-rose-100 flex items-center justify-center shrink-0 text-rose-700">
          <AlertTriangle className="w-5 h-5 text-rose-600" />
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500">Flood Risk Level</span>
            {summary?.ml_flood_probability !== undefined && (
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-blue-50 text-blue-700 border border-blue-200" title="ML Multi-Horizon Early Warning">
                ML {summary.ml_flood_probability}%
              </span>
            )}
          </div>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span
              className={`text-sm font-extrabold tracking-wider px-2.5 py-0.5 rounded-md border ${
                riskBadgeStyles[riskLevel] || riskBadgeStyles.LOW
              }`}
            >
              {riskLevel}
            </span>
          </div>
          <span className="text-[11.5px] text-slate-500 font-medium mt-1 truncate">
            {riskText}
          </span>
        </div>
      </div>

      {/* 5. Soil Moisture */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm hover:shadow-md transition-shadow flex items-start gap-3.5">
        <div className="w-11 h-11 rounded-xl bg-emerald-100 flex items-center justify-center shrink-0 text-emerald-700">
          <Sprout className="w-5 h-5 text-emerald-600" />
        </div>
        <div className="flex flex-col flex-1 min-w-0">
          <span className="text-xs font-semibold text-slate-500">Soil Moisture</span>
          <div className="flex items-baseline gap-2 mt-0.5">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight leading-tight">
              {Math.round(soilMoisture)}%
            </span>
          </div>
          <span className="text-[11.5px] font-medium text-rose-600 flex items-center gap-1 mt-1">
            <ArrowUp className="w-3 h-3 text-rose-600" />
            <span>6%</span> vs. yesterday
          </span>
        </div>
      </div>
    </section>
  );
};
