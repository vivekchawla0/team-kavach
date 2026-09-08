import React, { useMemo, useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Plugin,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { TrendingUp, Activity, Sparkles, Brain } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { TimeRange, MLSensorForecastResponse } from '@/types';
import { api } from '@/services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler
);

export const WaterLevelTrends: React.FC = () => {
  const {
    sensors,
    selectedSensorId,
    selectSensorForTrends,
    trendsData,
    trendRange,
    setTrendRange,
  } = useDashboard();

  const [showForecast, setShowForecast] = useState<boolean>(true);
  const [mlForecast, setMlForecast] = useState<MLSensorForecastResponse | null>(null);

  // Fetch ML Forecast for selected sensor
  useEffect(() => {
    if (!selectedSensorId) return;
    let active = true;
    api.getMLForecast(selectedSensorId)
      .then((data) => {
        if (active) setMlForecast(data);
      })
      .catch((err) => {
        console.warn('Could not load ML forecast for trend chart:', err);
      });

    return () => {
      active = false;
    };
  }, [selectedSensorId]);

  const baseLabels = useMemo(() => {
    if (!trendsData?.data_points) return [];
    return trendsData.data_points.map((p) => p.time_label);
  }, [trendsData]);

  const baseValues = useMemo(() => {
    if (!trendsData?.data_points) return [];
    return trendsData.data_points.map((p) => p.water_level);
  }, [trendsData]);

  const currentLevel = trendsData?.current_level ?? 2.84;
  const riseRate = trendsData?.rise_rate ?? 0.12;
  const status = trendsData?.status ?? 'WARNING';

  // Custom plugin to draw the 3 dashed threshold lines (Danger, Warning, Safe)
  const thresholdPlugin: Plugin<'line'> = {
    id: 'thresholdLines',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!scales.y || !chartArea) return;
      const { left, right } = chartArea;
      const { y } = scales;

      const thresholds = [
        { val: 4.0, label: 'Danger Level (4.0 m)', color: '#ef4444' },
        { val: 3.0, label: 'Warning Level (3.0 m)', color: '#f59e0b' },
        { val: 2.0, label: 'Safe Level (2.0 m)', color: '#10b981' },
      ];

      ctx.save();
      thresholds.forEach((t) => {
        const yPos = y.getPixelForValue(t.val);
        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = t.color;
        ctx.moveTo(left, yPos);
        ctx.lineTo(right, yPos);
        ctx.stroke();

        ctx.font = '600 9.5px sans-serif';
        ctx.fillStyle = t.color;
        ctx.textAlign = 'right';
        ctx.fillText(t.label, right - 6, yPos - 4);
      });
      ctx.restore();
    },
  };

  // Build combined chart data with optional ML multi-horizon projection and quantile corridor
  const { chartLabels, datasets } = useMemo(() => {
    if (!baseValues || baseValues.length === 0) {
      return {
        chartLabels: baseLabels.length > 0 ? baseLabels : ['Now'],
        datasets: [
          {
            label: 'Observed Level (m)',
            data: [currentLevel],
            borderColor: '#0284c7',
            backgroundColor: 'rgba(2, 132, 199, 0.15)',
            borderWidth: 2,
            fill: true,
          },
        ],
      };
    }

    if (!showForecast || !mlForecast?.forecasts) {
      return {
        chartLabels: baseLabels,
        datasets: [
          {
            label: 'Observed Level (m)',
            data: baseValues,
            borderColor: '#0284c7',
            backgroundColor: (context: any) => {
              const ctx = context.chart.ctx;
              const gradient = ctx.createLinearGradient(0, 0, 0, 180);
              gradient.addColorStop(0, 'rgba(2, 132, 199, 0.35)');
              gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)');
              return gradient;
            },
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            pointRadius: (ctx: any) => (ctx.dataIndex === baseValues.length - 1 ? 5 : 0),
            pointBackgroundColor: '#0284c7',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
          },
        ],
      };
    }

    const futureLabels = ['+1h', '+3h', '+6h'];
    const combinedLabels = [...baseLabels, ...futureLabels];

    const lastIdx = baseValues.length - 1;
    const lastVal = lastIdx >= 0 ? baseValues[lastIdx] : currentLevel;

    // Pad observed data with nulls for future
    const paddedObserved = [...baseValues, null, null, null];

    // Forecast series starts at last observed point
    const f1 = mlForecast.forecasts['1h'];
    const f3 = mlForecast.forecasts['3h'];
    const f6 = mlForecast.forecasts['6h'];

    const padLength = Math.max(0, baseValues.length - 1);

    const forecastData = new Array(padLength).fill(null);
    forecastData.push(lastVal);
    forecastData.push(f1?.predicted_water_level ?? lastVal);
    forecastData.push(f3?.predicted_water_level ?? lastVal);
    forecastData.push(f6?.predicted_water_level ?? lastVal);

    // Upper quantile corridor (q95)
    const upperCorridorData = new Array(padLength).fill(null);
    upperCorridorData.push(lastVal);
    upperCorridorData.push(f1?.uncertainty_upper ?? lastVal);
    upperCorridorData.push(f3?.uncertainty_upper ?? lastVal);
    upperCorridorData.push(f6?.uncertainty_upper ?? lastVal);

    // Lower quantile corridor (q05)
    const lowerCorridorData = new Array(padLength).fill(null);
    lowerCorridorData.push(lastVal);
    lowerCorridorData.push(f1?.uncertainty_lower ?? lastVal);
    lowerCorridorData.push(f3?.uncertainty_lower ?? lastVal);
    lowerCorridorData.push(f6?.uncertainty_lower ?? lastVal);

    return {
      chartLabels: combinedLabels,
      datasets: [
        {
          label: 'Observed Level (m)',
          data: paddedObserved,
          borderColor: '#0284c7',
          backgroundColor: (context: any) => {
            const ctx = context.chart.ctx;
            const gradient = ctx.createLinearGradient(0, 0, 0, 180);
            gradient.addColorStop(0, 'rgba(2, 132, 199, 0.35)');
            gradient.addColorStop(1, 'rgba(2, 132, 199, 0.0)');
            return gradient;
          },
          borderWidth: 2.5,
          fill: true,
          tension: 0.35,
          pointRadius: (ctx: any) => (ctx.dataIndex === lastIdx ? 5 : 0),
          pointBackgroundColor: '#0284c7',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
        },
        {
          label: 'AI 90% Upper (Q95)',
          data: upperCorridorData,
          borderColor: 'rgba(139, 92, 246, 0.35)',
          borderDash: [3, 3],
          borderWidth: 1,
          pointRadius: 0,
          fill: false,
          tension: 0.35,
        },
        {
          label: 'AI 90% Lower (Q05)',
          data: lowerCorridorData,
          borderColor: 'rgba(139, 92, 246, 0.35)',
          borderDash: [3, 3],
          borderWidth: 1,
          pointRadius: 0,
          fill: '-1', // Fill to previous dataset (upper corridor)
          backgroundColor: 'rgba(139, 92, 246, 0.12)',
          tension: 0.35,
        },
        {
          label: 'AI Point Forecast (m)',
          data: forecastData,
          borderColor: '#8b5cf6',
          borderDash: [6, 4],
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#8b5cf6',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 1.5,
          fill: false,
          tension: 0.35,
        },
      ],
    };
  }, [baseLabels, baseValues, showForecast, mlForecast, currentLevel]);

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        padding: 10,
        cornerRadius: 6,
        callbacks: {
          label: (item: any) => {
            const label = item.dataset.label || 'Level';
            return ` ${label}: ${Number(item.raw).toFixed(2)} m`;
          },
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          font: { size: 10 },
          color: '#94a3b8',
          maxTicksLimit: 10,
        },
      },
      y: {
        min: 0,
        max: 5.0,
        ticks: {
          stepSize: 1,
          font: { size: 10 },
          color: '#94a3b8',
        },
        grid: {
          color: '#f8fafc',
        },
      },
    },
  };

  const f6 = mlForecast?.forecasts?.['6h'];

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      {/* Header with Selector & Time Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2 text-slate-900">
          <Activity className="w-4 h-4 text-sky-600" />
          <h3 className="font-bold text-sm">Water Level Trends & Telemetry</h3>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* AI Forecast Toggle */}
          <button
            onClick={() => setShowForecast((prev) => !prev)}
            className={`text-xs font-semibold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 transition-all cursor-pointer ${
              showForecast
                ? 'bg-violet-50 text-violet-700 border-violet-200 shadow-2xs'
                : 'bg-slate-50 text-slate-500 border-slate-200 hover:text-slate-800'
            }`}
            title="Toggle 6-hour ML forecast and dedicated quantile uncertainty corridors"
          >
            <Sparkles className="w-3.5 h-3.5 text-violet-600" />
            <span>AI Forecast (6h)</span>
          </button>

          {/* Sensor Dropdown */}
          <select
            value={selectedSensorId}
            onChange={(e) => selectSensorForTrends(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
          >
            {sensors.map((s) => (
              <option key={s.sensor_id} value={s.sensor_id}>
                {s.name} {s.status === 'CRITICAL' ? '(Critical)' : ''}
              </option>
            ))}
          </select>

          {/* Time Tabs */}
          <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
            {(['24H', '7D', '30D'] as TimeRange[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setTrendRange(tab)}
                className={`px-2.5 py-0.5 rounded-md transition-all cursor-pointer ${
                  trendRange === tab ? 'bg-blue-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-48 w-full relative">
        <Line data={{ labels: chartLabels, datasets }} options={chartOptions} plugins={[thresholdPlugin]} />
      </div>

      {/* Footer Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4 pt-3 border-t border-slate-100">
        <div>
          <span className="text-[11px] font-medium text-slate-400 block">Current Level</span>
          <strong className="text-lg font-extrabold text-slate-900 leading-tight block">
            {currentLevel.toFixed(2)} m
          </strong>
          <span className="text-[10.5px] font-semibold text-emerald-600">↑ 0.6 m</span>
        </div>

        <div>
          <span className="text-[11px] font-medium text-slate-400 block">Rise Rate</span>
          <strong className="text-lg font-extrabold text-slate-900 leading-tight block">
            {riseRate >= 0 ? '+' : ''}{riseRate.toFixed(2)} m/hr
          </strong>
          <span className="text-[10.5px] font-semibold text-rose-600 flex items-center gap-0.5">
            <TrendingUp className="w-3 h-3 text-rose-600 inline" /> Increasing
          </span>
        </div>

        <div>
          <span className="text-[11px] font-medium text-slate-400 block">Safety Status</span>
          <div className="inline-flex items-center gap-1.5 mt-1 font-bold text-xs">
            <span
              className={`w-2 h-2 rounded-full ${
                status === 'CRITICAL'
                  ? 'bg-rose-500'
                  : status === 'WARNING'
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
            />
            <span
              className={
                status === 'CRITICAL'
                  ? 'text-rose-600'
                  : status === 'WARNING'
                  ? 'text-amber-600'
                  : 'text-emerald-600'
              }
            >
              {status}
            </span>
          </div>
        </div>

        {/* 4th Column: ML 6h Forecast & Dedicated Corridor */}
        <div className="bg-violet-50/60 -m-1 p-2 rounded-xl border border-violet-100">
          <div className="flex items-center gap-1 text-[10.5px] font-bold text-violet-700">
            <Brain className="w-3 h-3 text-violet-600" />
            <span>AI +6h Projection</span>
          </div>
          {f6 ? (
            <>
              <strong className="text-base font-extrabold text-violet-950 block leading-tight mt-0.5">
                {f6.predicted_water_level.toFixed(2)} m
              </strong>
              <span className="text-[10px] text-violet-600 font-medium block">
                90% Corridor: [{f6.uncertainty_lower.toFixed(2)}m – {f6.uncertainty_upper.toFixed(2)}m]
              </span>
            </>
          ) : (
            <span className="text-[10px] text-slate-400 block mt-1">Calibrating...</span>
          )}
        </div>
      </div>
    </div>
  );
};
