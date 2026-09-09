import React, { useState, useEffect, useCallback, useRef } from 'react';
import { BrainCircuit, Waves, CloudRain, TrendingUp, Radio } from 'lucide-react';
import { api } from '@/services/api';
import { MLPredictionResponse } from '@/types';
import { useDashboard } from '@/context/DashboardContext';

type PredictionStatus = 'LIVE' | 'UPDATING' | 'UNAVAILABLE';

export const AIFloodPredictionCard: React.FC = () => {
  const { realTelemetry, isTelemetryLive, telemetryAgeSeconds } = useDashboard();
  
  // State management as required
  const [currentPrediction, setCurrentPrediction] = useState<MLPredictionResponse | null>(null);
  const [lastValidPrediction, setLastValidPrediction] = useState<MLPredictionResponse | null>(null);
  const [predictionStatus, setPredictionStatus] = useState<PredictionStatus>('LIVE');
  const [predictionUpdatedAt, setPredictionUpdatedAt] = useState<Date | null>(null);
  const [secondsAgo, setSecondsAgo] = useState<number>(0);

  const isFetchingRef = useRef<boolean>(false);

  const fetchPrediction = useCallback(async () => {
    if (isFetchingRef.current) return;
    isFetchingRef.current = true;

    // Transition to UPDATING state while keeping previous prediction visible
    setPredictionStatus((prev) => (lastValidPrediction || currentPrediction ? 'UPDATING' : prev));

    try {
      const data = await api.getMLPrediction('ESP32-FW-001');
      if (data && data.available && data.prediction) {
        // Valid model result arrived
        setCurrentPrediction(data);
        setLastValidPrediction(data);
        setPredictionStatus('LIVE');
        setPredictionUpdatedAt(new Date());
        setSecondsAgo(0);
      } else {
        // Server returned unavailable status
        if (lastValidPrediction) {
          setPredictionStatus('UNAVAILABLE');
        } else {
          setCurrentPrediction(data);
          setPredictionStatus('UNAVAILABLE');
        }
      }
    } catch (err) {
      console.warn('[ML] Prediction fetch error:', err);
      // Keep lastValidPrediction visible on network/server error
      setPredictionStatus('UNAVAILABLE');
    } finally {
      isFetchingRef.current = false;
    }
  }, [lastValidPrediction, currentPrediction]);

  // Fetch on mount
  useEffect(() => {
    fetchPrediction();
  }, [fetchPrediction]);

  // Re-fetch whenever real ESP32 telemetry updates
  useEffect(() => {
    if (realTelemetry) {
      fetchPrediction();
    }
  }, [realTelemetry, fetchPrediction]);

  // Periodic fallback refresh (every 5 seconds)
  useEffect(() => {
    const timer = setInterval(() => {
      fetchPrediction();
    }, 5000);
    return () => clearInterval(timer);
  }, [fetchPrediction]);

  // Track relative seconds since last fetch
  useEffect(() => {
    const secondTicker = setInterval(() => {
      setSecondsAgo((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(secondTicker);
  }, []);

  const getRiskBadge = (risk?: string) => {
    switch (risk) {
      case 'CRITICAL':
        return {
          bg: 'bg-rose-50 border-rose-200 text-rose-700',
          dot: 'bg-rose-500',
          label: 'CRITICAL',
        };
      case 'DANGER':
        return {
          bg: 'bg-orange-50 border-orange-200 text-orange-700',
          dot: 'bg-orange-500',
          label: 'DANGER',
        };
      case 'WARNING':
        return {
          bg: 'bg-amber-50 border-amber-200 text-amber-700',
          dot: 'bg-amber-500',
          label: 'WARNING',
        };
      case 'SAFE':
      default:
        return {
          bg: 'bg-emerald-50 border-emerald-200 text-emerald-700',
          dot: 'bg-emerald-500',
          label: 'SAFE',
        };
    }
  };

  // Prediction to render: use currentPrediction if live/available, otherwise maintain lastValidPrediction
  const displayData = (currentPrediction?.available && currentPrediction?.prediction) 
    ? currentPrediction 
    : lastValidPrediction;

  const hasValidPrediction = Boolean(displayData && displayData.prediction);

  const formatAge = (s: number) => {
    if (s < 60) return `${s}s`;
    const m = Math.floor(s / 60);
    const rem = s % 60;
    return `${m}m ${rem}s`;
  };

  return (
    <div className="w-full bg-white rounded-2xl border border-slate-200/80 shadow-sm p-5 sm:p-6 overflow-hidden transition-all">
      {/* 1. Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                AI FLOOD PREDICTION
              </h3>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/60 uppercase tracking-wide">
                XGBoost ML
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              XGBoost Multi-Horizon Forecast • Barpeta Station
            </p>
          </div>
        </div>

        {/* Live Indicator & Relative Timestamp */}
        <div className="flex items-center gap-2.5 self-start sm:self-center">
          {predictionStatus === 'UPDATING' && hasValidPrediction ? (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700 text-xs font-semibold animate-pulse">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500" />
              </span>
              <span>Updating...</span>
              {predictionUpdatedAt && (
                <>
                  <span className="text-slate-300">•</span>
                  <span className="text-[11px] font-normal text-slate-500">
                    {secondsAgo === 0 ? 'just now' : `${secondsAgo}s ago`}
                  </span>
                </>
              )}
            </div>
          ) : isTelemetryLive && hasValidPrediction && predictionStatus === 'LIVE' ? (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
              </span>
              <span>LIVE</span>
              <span className="text-slate-300">•</span>
              <span className="text-[11px] font-normal text-slate-500">
                {secondsAgo === 0 ? 'just now' : `${secondsAgo}s ago`}
              </span>
            </div>
          ) : hasValidPrediction ? (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-700 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              <span>Last valid prediction shown</span>
              <span className="text-slate-300">•</span>
              <span className="text-[11px] font-normal text-slate-500">
                {formatAge(telemetryAgeSeconds)} ago
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 text-slate-600 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-slate-400" />
              <span>OFFLINE</span>
              <span className="text-slate-300">•</span>
              <span className="text-[11px] font-normal text-slate-500">
                last seen {formatAge(telemetryAgeSeconds)} ago
              </span>
            </div>
          )}
        </div>
      </div>

      {/* 2. Content Body: Live Prediction Horizons vs. Offline State */}
      {hasValidPrediction && displayData ? (
        <div className="mt-4 flex flex-col gap-4">
          {/* A. Small Current-Condition Row */}
          <div className="bg-slate-50/80 border border-slate-200/70 rounded-xl px-4 py-2.5 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-700 font-medium">
            <div className="flex items-center gap-2">
              <Waves className="w-4 h-4 text-sky-600" />
              <span>Current Water:</span>
              <strong className="text-slate-900 font-bold">
                {displayData.current_water_cm !== undefined ? `${displayData.current_water_cm.toFixed(2)} cm` : '--'}
              </strong>
            </div>

            <div className="hidden sm:block w-px h-4 bg-slate-200" />

            <div className="flex items-center gap-2">
              <CloudRain className="w-4 h-4 text-indigo-600" />
              <span>Rain Intensity:</span>
              <strong className="text-slate-900 font-bold">
                {displayData.rain_intensity !== undefined ? displayData.rain_intensity.toFixed(1) : '--'}
              </strong>
            </div>

            <div className="hidden sm:block w-px h-4 bg-slate-200" />

            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-emerald-600" />
              <span>Rise Rate:</span>
              <strong className="text-slate-900 font-bold">
                {displayData.water_rise_cm_min !== undefined
                  ? `${displayData.water_rise_cm_min >= 0 ? '+' : ''}${displayData.water_rise_cm_min.toFixed(3)} cm/min`
                  : '--'}
              </strong>
            </div>
          </div>

          {/* B. Three Prediction Horizons (+1H, +3H, +6H) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Horizon 1: +1 HOUR */}
            {(() => {
              const h = displayData.prediction?.one_hour;
              const badge = getRiskBadge(h?.risk);
              return (
                <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                      +1 HOUR
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                      {badge.label}
                    </span>
                  </div>

                  <div className="mt-4">
                    <span className="text-[11px] text-slate-500 font-medium block">
                      Predicted Water Level
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                        {h ? h.water_cm.toFixed(2) : '--'}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">cm</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Flood Probability</span>
                      <span className="font-bold text-slate-800">
                        {h ? `${h.flood_probability.toFixed(1)}%` : '--%'}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          (h?.flood_probability ?? 0) > 70
                            ? 'bg-rose-500'
                            : (h?.flood_probability ?? 0) > 35
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, h?.flood_probability ?? 0))}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Horizon 2: +3 HOURS */}
            {(() => {
              const h = displayData.prediction?.three_hours;
              const badge = getRiskBadge(h?.risk);
              return (
                <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                      +3 HOURS
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                      {badge.label}
                    </span>
                  </div>

                  <div className="mt-4">
                    <span className="text-[11px] text-slate-500 font-medium block">
                      Predicted Water Level
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                        {h ? h.water_cm.toFixed(2) : '--'}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">cm</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Flood Probability</span>
                      <span className="font-bold text-slate-800">
                        {h ? `${h.flood_probability.toFixed(1)}%` : '--%'}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          (h?.flood_probability ?? 0) > 70
                            ? 'bg-rose-500'
                            : (h?.flood_probability ?? 0) > 35
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, h?.flood_probability ?? 0))}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })()}

            {/* Horizon 3: +6 HOURS */}
            {(() => {
              const h = displayData.prediction?.six_hours;
              const badge = getRiskBadge(h?.risk);
              return (
                <div className="rounded-xl border border-slate-200/80 bg-white p-4 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-indigo-600 bg-indigo-50 px-2.5 py-0.5 rounded-md border border-indigo-100">
                      +6 HOURS
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-bold border ${badge.bg}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${badge.dot}`} />
                      {badge.label}
                    </span>
                  </div>

                  <div className="mt-4">
                    <span className="text-[11px] text-slate-500 font-medium block">
                      Predicted Water Level
                    </span>
                    <div className="flex items-baseline gap-1 mt-0.5">
                      <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
                        {h ? h.water_cm.toFixed(2) : '--'}
                      </span>
                      <span className="text-xs font-semibold text-slate-500">cm</span>
                    </div>
                  </div>

                  <div className="mt-3 pt-3 border-t border-slate-100">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500 font-medium">Flood Probability</span>
                      <span className="font-bold text-slate-800">
                        {h ? `${h.flood_probability.toFixed(1)}%` : '--%'}
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-1.5 rounded-full mt-1.5 overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all duration-500 ${
                          (h?.flood_probability ?? 0) > 70
                            ? 'bg-rose-500'
                            : (h?.flood_probability ?? 0) > 35
                            ? 'bg-amber-500'
                            : 'bg-emerald-500'
                        }`}
                        style={{ width: `${Math.min(100, Math.max(0, h?.flood_probability ?? 0))}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      ) : (
        /* OFFLINE / INITIAL TELEMETRY COLLECTION STATE */
        <div className="mt-4 py-8 px-4 rounded-xl bg-slate-50/70 border border-dashed border-slate-200 flex flex-col items-center justify-center text-center">
          <div className="w-12 h-12 rounded-full bg-amber-50 border border-amber-200/80 flex items-center justify-center text-amber-600 mb-3">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <h4 className="text-sm font-bold text-slate-800">
            AI Flood Prediction
          </h4>
          <p className="text-xs text-slate-500 mt-1 max-w-md">
            Collecting telemetry for prediction...
          </p>
          <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-md bg-white border border-slate-200 text-[11px] text-slate-600 font-medium">
            <span className="w-2 h-2 rounded-full bg-amber-500" />
            <span>Connect ESP32 via Desktop Bluetooth (ble_test.py)</span>
          </div>
        </div>
      )}
    </div>
  );
};
