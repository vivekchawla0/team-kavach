import React, { useState, useEffect } from 'react';
import { X, Activity, Brain, ShieldAlert, Sparkles, TrendingUp } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { api } from '@/services/api';
import { MLSensorForecastResponse } from '@/types';

export const SensorDetailModal: React.FC = () => {
  const { selectedDetailSensor, setSelectedDetailSensor, selectSensorForTrends } = useDashboard();
  const [mlForecast, setMlForecast] = useState<MLSensorForecastResponse | null>(null);
  const [loadingMl, setLoadingMl] = useState<boolean>(false);

  useEffect(() => {
    if (!selectedDetailSensor) {
      setMlForecast(null);
      return;
    }

    let active = true;
    setLoadingMl(true);
    api.getMLForecast(selectedDetailSensor.sensor_id)
      .then((data) => {
        if (active) setMlForecast(data);
      })
      .catch((err) => {
        console.warn('Could not load ML forecast for modal:', err);
      })
      .finally(() => {
        if (active) setLoadingMl(false);
      });

    return () => {
      active = false;
    };
  }, [selectedDetailSensor]);

  if (!selectedDetailSensor) return null;

  const s = selectedDetailSensor;
  const st = (s.status || 'NORMAL').toLowerCase();

  return (
    <div
      className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in duration-200"
      onClick={() => setSelectedDetailSensor(null)}
    >
      <div
        className="bg-white rounded-3xl w-full max-w-xl shadow-2xl overflow-hidden border border-slate-200 max-h-[90vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <h3 className="font-extrabold text-base text-slate-900">
              {s.name} <span className="text-slate-400 font-normal">({s.sensor_id})</span>
            </h3>
            <span
              className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${
                st === 'critical'
                  ? 'bg-rose-100 text-rose-700'
                  : st === 'warning'
                  ? 'bg-amber-100 text-amber-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
            >
              {s.status}
            </span>
          </div>
          <button
            onClick={() => setSelectedDetailSensor(null)}
            className="text-slate-400 hover:text-slate-700 transition-colors p-1"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          {/* Hydrological & Station Attributes */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Water Level</span>
              <strong className="text-base font-extrabold text-slate-900">{s.current_water_level.toFixed(2)} m</strong>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Rise Rate</span>
              <strong className="text-base font-extrabold text-slate-900">
                {s.water_rise_rate >= 0 ? '+' : ''}{s.water_rise_rate.toFixed(2)} m/hr
              </strong>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Warning Thresh.</span>
              <strong className="text-sm font-bold text-amber-600">{s.warning_threshold.toFixed(2)} m</strong>
            </div>

            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Danger Thresh.</span>
              <strong className="text-sm font-bold text-rose-600">{s.danger_threshold.toFixed(2)} m</strong>
            </div>

            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Station Battery</span>
              <strong className="text-xs font-bold text-slate-800">{Math.round(s.battery)}%</strong>
            </div>

            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Signal (RSSI)</span>
              <strong className="text-xs font-bold text-slate-800">{s.signal_strength.toFixed(1)} dBm</strong>
            </div>

            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Pole Tilt</span>
              <strong className="text-xs font-bold text-slate-800">
                {s.inclination_x}° / {s.inclination_y}°
              </strong>
            </div>

            <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100">
              <span className="text-[10.5px] text-slate-400 font-medium block">Coordinates</span>
              <strong className="text-xs font-bold text-slate-800 block truncate">
                {s.latitude.toFixed(3)}, {s.longitude.toFixed(3)}
              </strong>
            </div>
          </div>

          {/* AI Predictive Intelligence Section (Phase 4B) */}
          <div className="rounded-2xl border border-violet-100 bg-gradient-to-br from-violet-50/50 via-slate-50 to-white p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2 text-violet-900">
                <Brain className="w-4 h-4 text-violet-600" />
                <h4 className="font-bold text-xs uppercase tracking-wider">
                  AI Predictive Intelligence (Multi-Horizon XGBoost)
                </h4>
              </div>
              <span className="text-[10px] font-semibold text-violet-700 bg-violet-100 px-2 py-0.5 rounded-full">
                Dedicated Q05 - Q95 Intervals
              </span>
            </div>

            {loadingMl ? (
              <div className="py-6 text-center text-xs text-slate-400 animate-pulse">
                Running ML inference and dedicated quantile estimators...
              </div>
            ) : mlForecast && mlForecast.forecasts ? (
              <div className="space-y-3">
                {/* 3 Horizon Cards */}
                <div className="grid grid-cols-3 gap-2">
                  {(['1h', '3h', '6h'] as const).map((h) => {
                    const f = mlForecast.forecasts[h];
                    if (!f) return null;
                    return (
                      <div key={h} className="bg-white/80 backdrop-blur rounded-xl border border-violet-100 p-2.5 text-center shadow-2xs">
                        <span className="text-[10px] font-bold text-violet-600 block uppercase">+{h} Forecast</span>
                        <strong className="text-base font-extrabold text-slate-900 block my-0.5">
                          {f.predicted_water_level.toFixed(2)} m
                        </strong>
                        <span className="text-[9.5px] text-slate-500 font-medium block">
                          [{f.uncertainty_lower.toFixed(2)}m – {f.uncertainty_upper.toFixed(2)}m]
                        </span>
                        <span className="text-[9px] font-bold text-slate-400 block mt-1">
                          Flood Prob: {f.flood_probability.toFixed(1)}%
                        </span>
                      </div>
                    );
                  })}
                </div>

                {/* Advisory Notice */}
                <div className="bg-violet-50/80 rounded-xl p-2.5 border border-violet-200/60 flex items-start gap-2 text-[11px] text-violet-950">
                  <Sparkles className="w-3.5 h-3.5 text-violet-600 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold">{mlForecast.advisory_level}:</span> {mlForecast.advisory_message}
                  </div>
                </div>

                {/* Top Features Influence Tiers */}
                {mlForecast.forecasts['6h']?.top_influences && (
                  <div>
                    <span className="text-[10.5px] font-bold text-slate-500 block mb-1.5">
                      Top Hydrological Drivers (Feature Influence):
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {mlForecast.forecasts['6h'].top_influences.slice(0, 4).map((inf, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 flex items-center gap-1 shadow-2xs"
                        >
                          <span className="font-semibold text-slate-900">{inf.feature.replace(/_/g, ' ')}:</span>
                          <span
                            className={
                              inf.tier.includes('High')
                                ? 'text-rose-600 font-bold'
                                : inf.tier.includes('Moderate')
                                ? 'text-amber-600 font-bold'
                                : 'text-slate-500'
                            }
                          >
                            {inf.tier}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-4 text-center text-xs text-slate-400">
                Predictive telemetry model initializing...
              </div>
            )}

            {/* Governance Disclaimer */}
            <div className="mt-3 pt-2.5 border-t border-violet-100 flex items-center gap-1.5 text-[9.5px] text-slate-500">
              <ShieldAlert className="w-3 h-3 text-slate-400 shrink-0" />
              <span>
                Safety Authority: Deterministic Rule-Based Engine. ML predictions remain advisory only.
              </span>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              onClick={() => {
                selectSensorForTrends(s.sensor_id);
                setSelectedDetailSensor(null);
              }}
              className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-xl flex items-center gap-1.5 shadow-sm transition-colors cursor-pointer"
            >
              <Activity className="w-3.5 h-3.5" />
              Open Trends Analytics ↗
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
