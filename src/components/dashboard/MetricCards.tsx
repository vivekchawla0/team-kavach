import React from 'react';
import { Radio, Droplets, CloudRain, AlertTriangle, ArrowUp, ArrowRight } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const MetricCards: React.FC = () => {
  const { summary } = useDashboard();

  // Single Real Sensor Prototype deployment: 1 Online, 0 Offline
  const totalSensors = 1;
  const onlineSensors = 1;
  const offlineSensors = 0;

  const currentWaterLevel = summary?.average_water_level_m ?? 3.17;
  const currentRainfall = summary?.current_rainfall_mm_hr ?? 65;
  const floodRiskLevel = summary?.flood_risk_level || 'CRITICAL';
  const floodRiskText = summary?.flood_risk_text || 'Extreme flood conditions';
  const aiProb = summary?.ml_flood_probability ?? 8.5;

  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5" aria-label="Key Hydrological Metrics">
      {/* 1. TOTAL SENSORS (Single Real Prototype Station) */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-sky-50 flex items-center justify-center text-sky-600">
            <Radio className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            TOTAL SENSORS
          </span>
        </div>

        <div className="mt-4">
          <div className="flex items-center gap-2.5">
            <span className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight font-sans">
              {totalSensors}
            </span>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              Prototype
            </span>
          </div>

          <div className="flex items-center gap-1.5 mt-2 text-xs font-semibold text-emerald-600">
            <ArrowUp className="w-3 h-3 text-emerald-600" />
            <span>{onlineSensors} Online • {offlineSensors} Offline</span>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span className="font-medium text-slate-600">Barpeta Station FW-001</span>
          <a
            href="#map-section"
            className="inline-flex items-center gap-1 text-sky-600 hover:text-sky-800 font-semibold transition-colors"
          >
            Active Telemetry <ArrowRight className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* 2. CURRENT WATER LEVEL */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-sky-50 flex items-center justify-center text-sky-600">
            <Droplets className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            CURRENT WATER LEVEL
          </span>
        </div>

        <div className="mt-4 flex items-baseline justify-between">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight font-sans">
                {currentWaterLevel.toFixed(2)}
              </span>
              <span className="text-base font-semibold text-slate-500">m</span>
            </div>

            <div className="flex items-center gap-1 mt-2 text-xs font-semibold text-rose-600">
              <ArrowUp className="w-3 h-3" />
              <span>+0.24 m/hr rise rate</span>
            </div>
          </div>

          {/* Mini Wave Sparkline matching reference */}
          <div className="w-16 h-8 shrink-0 flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 60 25" fill="none">
              <path
                d="M0 20 C10 18, 20 22, 30 15 C40 8, 50 12, 60 5"
                stroke="#0284c7"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path
                d="M0 20 C10 18, 20 22, 30 15 C40 8, 50 12, 60 5 L60 25 L0 25 Z"
                fill="url(#wave-fill)"
                opacity="0.18"
              />
              <defs>
                <linearGradient id="wave-fill" x1="0" y1="0" x2="0" y2="25" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#0284c7" />
                  <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">Warning: 3.00 m</span>
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-600 border border-rose-200">
            Above Warning
          </span>
        </div>
      </div>

      {/* 3. CURRENT RAINFALL */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-sky-50 flex items-center justify-center text-sky-600">
            <CloudRain className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            CURRENT RAINFALL
          </span>
        </div>

        <div className="mt-4 flex items-baseline justify-between">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight font-sans">
                {Math.round(currentRainfall)}
              </span>
              <span className="text-base font-semibold text-slate-500">mm/hr</span>
            </div>

            <div className="flex items-center gap-1 mt-2 text-xs font-semibold text-rose-600">
              <ArrowUp className="w-3 h-3" />
              <span>+40% vs. baseline</span>
            </div>
          </div>

          {/* Mini Bar Chart Graphic matching reference */}
          <div className="flex items-end gap-1 h-8 shrink-0">
            <div className="w-1.5 h-3 rounded-t bg-sky-300" />
            <div className="w-1.5 h-4 rounded-t bg-sky-400" />
            <div className="w-1.5 h-5 rounded-t bg-sky-500" />
            <div className="w-1.5 h-7 rounded-t bg-sky-600" />
            <div className="w-1.5 h-8 rounded-t bg-sky-700" />
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">Threshold: 25 mm/hr</span>
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-600 border border-rose-200">
            Heavy Downpour
          </span>
        </div>
      </div>

      {/* 4. FLOOD RISK LEVEL */}
      <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-rose-50 flex items-center justify-center text-rose-600">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
            FLOOD RISK LEVEL
          </span>
        </div>

        <div className="mt-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl sm:text-3xl font-extrabold tracking-tight text-rose-600 font-sans">
              {floodRiskLevel}
            </span>
            <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              AI {aiProb}%
            </span>
          </div>

          <p className="text-xs font-medium text-slate-500 mt-2 truncate">
            {floodRiskText}
          </p>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">Priority Alert Level 4</span>
          <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-600 border border-rose-200">
            Immediate Action
          </span>
        </div>
      </div>
    </section>
  );
};
