import React from 'react';
import { Radio, Droplets, CloudRain, AlertTriangle, ArrowUp, ArrowDown, ArrowRight } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const MetricCards: React.FC = () => {
  const { realTelemetry, isTelemetryLive, telemetryAgeSeconds } = useDashboard();

  const isOnline = isTelemetryLive;
  const hasData = realTelemetry && realTelemetry.water_level_cm !== null && realTelemetry.water_level_cm !== undefined;

  const formatAge = (secs: number) => {
    if (secs < 60) return `${secs}s ago`;
    const mins = Math.floor(secs / 60);
    const remSecs = secs % 60;
    if (mins < 60) return `${mins}m ${remSecs}s ago`;
    const hours = Math.floor(mins / 60);
    return `${hours}h ${mins % 60}m ago`;
  };

  // Single Real Sensor Prototype deployment
  const totalSensors = 1;
  const onlineSensors = isOnline ? 1 : 0;
  const offlineSensors = isOnline ? 0 : 1;

  const waterLevelCm = realTelemetry?.water_level_cm;
  const waterRaw = realTelemetry?.water_raw;
  const riseRate = realTelemetry?.rise_rate_cm_min ?? 0.0;

  const rainIntensity = realTelemetry?.rain_intensity;
  const rainRaw = realTelemetry?.rain_raw;
  const rainPct = realTelemetry?.rain_percentage;

  const floodRiskLevel: string = (realTelemetry?.flood_risk_level as string) || (isOnline ? 'SAFE' : 'OFFLINE');
  const floodRiskText = isOnline
    ? (realTelemetry?.flood_risk_text || 'Nominal prototype level')
    : `Last known status (${formatAge(telemetryAgeSeconds)})`;
  const riskScore = realTelemetry?.flood_risk_score ?? 20.0;

  // Determine Risk Badge styling
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-rose-600 bg-rose-50 border-rose-200';
      case 'DANGER':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'WARNING':
        return 'text-amber-600 bg-amber-50 border-amber-200';
      case 'SAFE':
        return 'text-emerald-600 bg-emerald-50 border-emerald-200';
      default:
        return 'text-slate-500 bg-slate-50 border-slate-200';
    }
  };

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

          <div className="flex items-center gap-1.5 mt-2 text-xs font-semibold">
            {isOnline ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-emerald-600">{onlineSensors} Online • {offlineSensors} Offline</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-rose-600">0 Online • 1 Offline</span>
              </>
            )}
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
          <span className="font-medium text-slate-600">Barpeta Station FW-001</span>
          <span className="inline-flex items-center gap-1 text-sky-600 font-semibold">
            {isOnline ? 'Active Telemetry' : `BLE Offline (${formatAge(telemetryAgeSeconds)})`}
          </span>
        </div>
      </div>

      {/* 2. CURRENT WATER LEVEL (Calibrated Centimeters) */}
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
            {hasData ? (
              <>
                <div className="flex items-baseline gap-1.5">
                  <span className={`text-3xl sm:text-4xl font-extrabold tracking-tight font-sans ${isOnline ? 'text-slate-900' : 'text-slate-500'}`}>
                    {waterLevelCm?.toFixed(2)}
                  </span>
                  <span className="text-base font-semibold text-slate-500">cm</span>
                </div>

                <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${isOnline && riseRate > 0 ? 'text-rose-600' : 'text-slate-500'}`}>
                  {riseRate > 0 ? <ArrowUp className="w-3 h-3 text-rose-600" /> : <ArrowDown className="w-3 h-3 text-slate-400" />}
                  <span>{riseRate >= 0 ? '+' : ''}{riseRate.toFixed(2)} cm/min rise rate</span>
                </div>
              </>
            ) : (
              <>
                <div className="text-2xl sm:text-3xl font-extrabold text-slate-400 tracking-tight font-sans">
                  OFFLINE
                </div>
                <div className="text-xs font-medium text-slate-400 mt-2">
                  Waiting for real telemetry...
                </div>
              </>
            )}
          </div>

          {/* Mini Wave Sparkline */}
          <div className="w-16 h-8 shrink-0 flex items-end">
            <svg className="w-full h-full overflow-visible" viewBox="0 0 60 25" fill="none">
              <path
                d="M0 20 C10 18, 20 22, 30 15 C40 8, 50 12, 60 5"
                stroke={isOnline ? "#0284c7" : "#94a3b8"}
                strokeWidth="2.5"
                strokeLinecap="round"
              />
              <path
                d="M0 20 C10 18, 20 22, 30 15 C40 8, 50 12, 60 5 L60 25 L0 25 Z"
                fill="url(#wave-fill)"
                opacity={isOnline ? "0.18" : "0.08"}
              />
              <defs>
                <linearGradient id="wave-fill" x1="0" y1="0" x2="0" y2="25" gradientUnits="userSpaceOnUse">
                  <stop stopColor={isOnline ? "#0284c7" : "#94a3b8"} />
                  <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium truncate max-w-[200px]">
            {hasData ? (isOnline ? `Raw ADC: ${waterRaw} • Live ESP32` : `Raw ADC: ${waterRaw} • Last Known Value`) : 'Warning: 6.00 cm'}
          </span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
            !isOnline
              ? 'bg-slate-100 text-slate-600 border-slate-200'
              : (waterLevelCm ?? 0) >= 6.0
              ? 'bg-rose-50 text-rose-600 border-rose-200'
              : 'bg-emerald-50 text-emerald-600 border-emerald-200'
          }`}>
            {isOnline
              ? ((waterLevelCm ?? 0) >= 6.0 ? 'Above Warning' : 'Safe Depth')
              : `Offline (${formatAge(telemetryAgeSeconds)})`}
          </span>
        </div>
      </div>

      {/* 3. CURRENT RAINFALL (Calibrated Rain Sensor Intensity) */}
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
            {hasData ? (
              <>
                <div className="flex items-baseline gap-1.5">
                  <span className={`text-3xl sm:text-4xl font-extrabold tracking-tight font-sans ${isOnline ? 'text-slate-900' : 'text-slate-500'}`}>
                    {rainIntensity?.toFixed(1)}
                  </span>
                  <span className="text-base font-semibold text-slate-500">/ 10</span>
                </div>

                <div className={`flex items-center gap-1 mt-2 text-xs font-semibold ${isOnline ? 'text-sky-600' : 'text-slate-500'}`}>
                  <span>{rainPct?.toFixed(0) ?? 0}% surface moisture</span>
                </div>
              </>
            ) : (
              <>
                <div className="text-2xl sm:text-3xl font-extrabold text-slate-400 tracking-tight font-sans">
                  OFFLINE
                </div>
                <div className="text-xs font-medium text-slate-400 mt-2">
                  Waiting for real telemetry...
                </div>
              </>
            )}
          </div>

          {/* Mini Bar Chart Graphic */}
          <div className="flex items-end gap-1 h-8 shrink-0">
            <div className={`w-1.5 h-3 rounded-t ${hasData && (rainIntensity ?? 0) >= 2 ? (isOnline ? 'bg-sky-500' : 'bg-slate-400') : 'bg-slate-200'}`} />
            <div className={`w-1.5 h-4 rounded-t ${hasData && (rainIntensity ?? 0) >= 4 ? (isOnline ? 'bg-sky-500' : 'bg-slate-400') : 'bg-slate-200'}`} />
            <div className={`w-1.5 h-5 rounded-t ${hasData && (rainIntensity ?? 0) >= 6 ? (isOnline ? 'bg-sky-600' : 'bg-slate-500') : 'bg-slate-200'}`} />
            <div className={`w-1.5 h-7 rounded-t ${hasData && (rainIntensity ?? 0) >= 8 ? (isOnline ? 'bg-sky-700' : 'bg-slate-500') : 'bg-slate-200'}`} />
            <div className={`w-1.5 h-8 rounded-t ${hasData && (rainIntensity ?? 0) >= 9 ? (isOnline ? 'bg-sky-800' : 'bg-slate-600') : 'bg-slate-200'}`} />
          </div>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium truncate max-w-[200px]">
            {hasData ? (isOnline ? `Raw ADC: ${rainRaw} • Rain Intensity` : `Raw ADC: ${rainRaw} • Last Known Value`) : 'Threshold: Level 6.0'}
          </span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${
            !isOnline
              ? 'bg-slate-100 text-slate-600 border-slate-200'
              : (rainIntensity ?? 0) >= 6.0
              ? 'bg-rose-50 text-rose-600 border-rose-200'
              : 'bg-sky-50 text-sky-600 border-sky-200'
          }`}>
            {isOnline
              ? ((rainIntensity ?? 0) >= 6.0 ? 'Active Downpour' : 'Light / Clear')
              : `Offline (${formatAge(telemetryAgeSeconds)})`}
          </span>
        </div>
      </div>

      {/* 4. FLOOD RISK LEVEL (Calculated from Real Calibrated Water Level) */}
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
            <span className={`text-2xl sm:text-3xl font-extrabold tracking-tight font-sans ${
              !isOnline ? 'text-slate-500' :
              floodRiskLevel === 'CRITICAL' ? 'text-rose-600' :
              floodRiskLevel === 'DANGER' ? 'text-orange-600' :
              floodRiskLevel === 'WARNING' ? 'text-amber-600' :
              floodRiskLevel === 'SAFE' ? 'text-emerald-600' : 'text-slate-400'
            }`}>
              {floodRiskLevel}
            </span>
            {hasData && (
              <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${isOnline ? getRiskColor(floodRiskLevel) : 'bg-slate-100 text-slate-600 border-slate-200'}`}>
                Score {riskScore.toFixed(0)}
              </span>
            )}
          </div>

          <p className="text-xs font-medium text-slate-500 mt-2 truncate">
            {floodRiskText}
          </p>
        </div>

        <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">Safe: &lt;6cm • Danger: &gt;10cm</span>
          <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${isOnline ? getRiskColor(floodRiskLevel) : 'bg-slate-100 text-slate-600 border-slate-200'}`}>
            {isOnline ? 'Live Calibrated' : `ESP32 Offline (${formatAge(telemetryAgeSeconds)})`}
          </span>
        </div>
      </div>
    </section>
  );
};

