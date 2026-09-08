import React, { useMemo } from 'react';
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
import { Waves, ArrowUpRight, Brain, ArrowUp } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { TimeRange } from '@/types';

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
    trendRange,
    setTrendRange,
    summary,
  } = useDashboard();

  const currentLevel = summary?.average_water_level_m ?? 3.17;
  const riseRate = 0.24; // m/hr
  const aiForecastLevel = 3.41; // m

  // Custom plugin to draw the 3 dashed horizontal threshold lines (Danger, Warning, Safe)
  const thresholdPlugin: Plugin<'line'> = {
    id: 'thresholdLines',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!scales.y || !chartArea) return;
      const { left, right } = chartArea;
      const { y } = scales;

      const thresholds = [
        { val: 4.0, label: 'Danger (4.0 m)', color: '#ef4444' },
        { val: 3.0, label: 'Warning (3.0 m)', color: '#f59e0b' },
        { val: 2.0, label: 'Safe (2.0 m)', color: '#10b981' },
      ];

      ctx.save();
      thresholds.forEach((t) => {
        const yPos = y.getPixelForValue(t.val);
        if (yPos < chartArea.top || yPos > chartArea.bottom) return;

        ctx.beginPath();
        ctx.setLineDash([4, 4]);
        ctx.lineWidth = 1.2;
        ctx.strokeStyle = t.color;
        ctx.moveTo(left, yPos);
        ctx.lineTo(right, yPos);
        ctx.stroke();

        ctx.font = '600 10px sans-serif';
        ctx.fillStyle = t.color;
        ctx.textAlign = 'right';
        ctx.fillText(t.label, right - 6, yPos - 5);
      });
      ctx.restore();
    },
  };

  // Fixed 24H intervals matching reference image: 00:00, 04:00, 08:00, 12:00, 16:00, 20:00, 24:00
  const chartLabels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00'];

  // Observed line from 1.8m rising to 3.17m (crosses warning at ~18:00)
  const observedData = [1.80, 2.05, 2.32, 2.60, 2.85, 3.05, 3.17];

  // AI Forecast continuation projecting further to 3.41m
  const forecastData = [null, null, null, null, null, 3.05, 3.41];

  const datasets: any[] = [
    // 1. Observed Water Level (Solid Blue line)
    {
      label: 'Observed',
      data: observedData,
      borderColor: '#0284c7',
      backgroundColor: 'transparent',
      borderWidth: 2.5,
      pointRadius: 3.5,
      pointHoverRadius: 6,
      pointBackgroundColor: '#0284c7',
      tension: 0.35,
    },
    // 2. AI Forecast (Dashed Violet/Purple Line)
    {
      label: 'AI Forecast',
      data: forecastData,
      borderColor: '#7c3aed',
      borderWidth: 2.5,
      borderDash: [5, 4],
      pointRadius: 3.5,
      pointHoverRadius: 6,
      pointBackgroundColor: '#7c3aed',
      tension: 0.3,
    },
  ];

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    scales: {
      x: {
        grid: {
          color: '#f8fafc',
        },
        ticks: {
          font: { size: 10, weight: '500' },
          color: '#94a3b8',
          maxRotation: 0,
        },
      },
      y: {
        min: 1.5,
        max: 4.5,
        grid: {
          color: '#f1f5f9',
        },
        ticks: {
          stepSize: 0.5,
          font: { size: 10, weight: '500' },
          color: '#94a3b8',
          callback: (val: any) => `${val.toFixed(1)} m`,
        },
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: '#0f172a',
        titleFont: { size: 11, weight: 'bold' },
        bodyFont: { size: 11 },
        padding: 8,
        cornerRadius: 8,
        callbacks: {
          label: (context: any) => {
            const val = context.parsed.y;
            return ` ${context.dataset.label}: ${val ? val.toFixed(2) : '--'} m`;
          },
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600">
            <Waves className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Water Level Intelligence
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Real-Time Hydrograph & AI Hydrology Projection
            </p>
          </div>
        </div>

        {/* Time Tabs */}
        <div className="flex bg-slate-100 p-0.5 rounded-lg text-xs font-semibold">
          {(['24H', '7D', '30D'] as TimeRange[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setTrendRange(tab)}
              className={`px-3 py-1 rounded-md transition-all cursor-pointer ${
                trendRange === tab
                  ? 'bg-sky-600 text-white shadow-xs'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Chart Legend Row matching reference */}
      <div className="flex items-center flex-wrap gap-4 py-2 text-[11px] font-medium text-slate-600">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-[#0284c7] inline-block" />
          <span className="w-1.5 h-1.5 rounded-full bg-[#0284c7] -ml-2" />
          <span>Observed</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#7c3aed] inline-block" />
          <span className="w-1.5 h-1.5 rounded-full bg-[#7c3aed] -ml-2" />
          <span>AI Forecast</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#10b981] inline-block" />
          <span>Safe Level (2.0 m)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#f59e0b] inline-block" />
          <span>Warning (3.0 m)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#ef4444] inline-block" />
          <span>Danger (4.0 m)</span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-[210px] w-full relative my-1">
        <Line data={{ labels: chartLabels, datasets }} options={chartOptions} plugins={[thresholdPlugin]} />
      </div>

      {/* 3 Bottom Insight Cards matching reference image */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-100">
        {/* 1. CURRENT LEVEL */}
        <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">
            <Waves className="w-3.5 h-3.5 text-sky-600" />
            <span>CURRENT LEVEL</span>
          </div>
          <div className="my-1">
            <span className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
              {currentLevel.toFixed(2)} m
            </span>
          </div>
          <div className="text-[11px] font-semibold text-rose-600">
            <span>↑ +{riseRate.toFixed(2)} m/hr</span>
            <span className="block text-[10px] text-rose-600 font-bold">Above Warning</span>
          </div>
        </div>

        {/* 2. RISE RATE */}
        <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">
            <ArrowUpRight className="w-3.5 h-3.5 text-rose-600" />
            <span>RISE RATE</span>
          </div>
          <div className="my-1">
            <span className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
              +{riseRate.toFixed(2)} m/hr
            </span>
          </div>
          <div className="text-[11px] font-semibold text-slate-600">
            <span className="text-rose-600 font-bold">Increasing</span>
            <span className="block text-[10px] text-slate-400 font-medium">Rapid rise detected</span>
          </div>
        </div>

        {/* 3. AI FORECAST (6H) */}
        <div className="bg-violet-50/60 rounded-xl p-3 border border-violet-100/70 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-violet-700 uppercase tracking-wider">
            <Brain className="w-3.5 h-3.5 text-violet-600" />
            <span>AI FORECAST (6H)</span>
          </div>
          <div className="my-1">
            <span className="text-xl sm:text-2xl font-extrabold text-violet-950 leading-tight">
              {aiForecastLevel.toFixed(2)} m
            </span>
          </div>
          <div className="text-[10px] font-medium text-violet-700 leading-tight">
            Likely to cross warning level in ~4 hours
          </div>
        </div>
      </div>
    </div>
  );
};
