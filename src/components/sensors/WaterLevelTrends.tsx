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
import { Waves, ArrowUpRight, Brain, ShieldAlert } from 'lucide-react';
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
    realTelemetry,
    telemetryHistory,
    isTelemetryLive,
    telemetryAgeSeconds,
  } = useDashboard();

  const isOnline = isTelemetryLive;
  const currentCm = realTelemetry?.water_level_cm;
  const currentRaw = realTelemetry?.water_raw;
  const riseRate = realTelemetry?.rise_rate_cm_min ?? 0.0;

  // Custom plugin to draw the 3 dashed horizontal threshold lines for 15 cm physical prototype:
  // Danger: 10.0 cm, Warning: 6.0 cm, Safe: 2.0 cm
  const thresholdPlugin: Plugin<'line'> = {
    id: 'prototypeThresholdLines',
    afterDraw(chart) {
      const { ctx, chartArea, scales } = chart;
      if (!scales.y || !chartArea) return;
      const { left, right } = chartArea;
      const { y } = scales;

      const thresholds = [
        { val: 10.0, label: 'Danger (10.0 cm)', color: '#ef4444' },
        { val: 6.0, label: 'Warning (6.0 cm)', color: '#f59e0b' },
        { val: 2.0, label: 'Safe (2.0 cm)', color: '#10b981' },
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

  // Build real observed time series points from real telemetry history
  const { chartLabels, observedData } = useMemo(() => {
    if (telemetryHistory && telemetryHistory.length > 0) {
      // Filter out points that have valid water_level_cm
      const validPoints = telemetryHistory.filter((r) => r.water_level_cm !== null && r.water_level_cm !== undefined);
      if (validPoints.length > 0) {
        const labels = validPoints.map((p) => {
          if (!p.timestamp) return '';
          const d = new Date(p.timestamp);
          return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        });
        const vals = validPoints.map((p) => p.water_level_cm);
        return { chartLabels: labels, observedData: vals };
      }
    }

    // Single active live point fallback if history not yet accumulated
    if (currentCm !== null && currentCm !== undefined) {
      return {
        chartLabels: ['Live'],
        observedData: [currentCm],
      };
    }

    return {
      chartLabels: ['Waiting for stream...'],
      observedData: [null],
    };
  }, [telemetryHistory, currentCm]);

  const datasets: any[] = [
    {
      label: 'Observed (ESP32)',
      data: observedData,
      borderColor: '#0284c7',
      backgroundColor: 'rgba(2, 132, 199, 0.08)',
      borderWidth: 2.5,
      pointRadius: observedData.length <= 15 ? 4 : 2,
      pointHoverRadius: 6,
      pointBackgroundColor: '#0284c7',
      fill: true,
      tension: 0.2,
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
          display: false,
        },
        ticks: {
          font: { size: 10, weight: '500' },
          color: '#94a3b8',
          maxTicksLimit: 8,
        },
      },
      y: {
        min: 0.0,
        max: 15.0, // 15 cm physical prototype container
        grid: {
          color: '#f1f5f9',
        },
        ticks: {
          stepSize: 3.0,
          font: { size: 10, weight: '500' },
          color: '#94a3b8',
          callback: (val: any) => `${val.toFixed(1)} cm`,
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
            return ` Observed Water Level: ${val ? val.toFixed(2) : '--'} cm`;
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
              Real-Time Hydrograph • 15 cm Physical Prototype Calibration
            </p>
          </div>
        </div>

        {/* Live Indicator */}
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-bold border ${
            isOnline ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-600 border-slate-200'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
            {isOnline ? 'Live Telemetry Active' : 'ESP32 Offline'}
          </span>
        </div>
      </div>

      {/* Chart Legend Row */}
      <div className="flex items-center flex-wrap gap-4 py-2 text-[11px] font-medium text-slate-600">
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 bg-[#0284c7] inline-block" />
          <span className="w-1.5 h-1.5 rounded-full bg-[#0284c7] -ml-2" />
          <span>Observed (cm)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#10b981] inline-block" />
          <span>Safe (2.0 cm)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#f59e0b] inline-block" />
          <span>Warning (6.0 cm)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-4 h-0.5 border-t border-dashed border-[#ef4444] inline-block" />
          <span>Danger (10.0 cm)</span>
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-[210px] w-full relative my-1">
        <Line data={{ labels: chartLabels, datasets }} options={chartOptions} plugins={[thresholdPlugin]} />
      </div>

      {/* 3 Bottom Insight Cards */}
      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-100">
        {/* 1. CURRENT LEVEL */}
        <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">
            <Waves className="w-3.5 h-3.5 text-sky-600" />
            <span>CALIBRATED DEPTH</span>
          </div>
          <div className="my-1">
            <span className={`text-xl sm:text-2xl font-extrabold leading-tight ${isOnline ? 'text-slate-900' : 'text-slate-500'}`}>
              {currentCm !== null && currentCm !== undefined ? `${currentCm.toFixed(2)} cm` : '--'}
            </span>
          </div>
          <div className="text-[11px] font-semibold text-slate-500">
            <span>{isOnline ? `Raw ADC: ${currentRaw ?? '--'} • Live ESP32` : `Last Known (Raw ADC: ${currentRaw ?? '--'})`}</span>
          </div>
        </div>

        {/* 2. RISE RATE */}
        <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-slate-500 uppercase tracking-wider">
            <ArrowUpRight className="w-3.5 h-3.5 text-sky-600" />
            <span>RISE RATE</span>
          </div>
          <div className="my-1">
            <span className="text-xl sm:text-2xl font-extrabold text-slate-900 leading-tight">
              {riseRate >= 0 ? '+' : ''}{riseRate.toFixed(2)} cm/min
            </span>
          </div>
          <div className="text-[11px] font-semibold text-slate-500">
            <span>{Math.abs(riseRate) > 0.05 ? 'Active Water Flow' : 'Steady Water Level'}</span>
          </div>
        </div>

        {/* 3. FLOOD RISK STATUS */}
        <div className="bg-slate-50/80 rounded-xl p-3 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center gap-1.5 text-[10.5px] font-bold text-slate-600 uppercase tracking-wider">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
            <span>PROTOTYPE RISK</span>
          </div>
          <div className="my-1">
            <span className={`text-xl sm:text-2xl font-extrabold leading-tight ${
              (realTelemetry?.flood_risk_level as string) === 'CRITICAL' ? 'text-rose-600' :
              (realTelemetry?.flood_risk_level as string) === 'DANGER' ? 'text-orange-600' :
              (realTelemetry?.flood_risk_level as string) === 'WARNING' ? 'text-amber-600' :
              (realTelemetry?.flood_risk_level as string) === 'SAFE' ? 'text-emerald-600' : 'text-slate-500'
            }`}>
              {realTelemetry?.flood_risk_level ?? (isOnline ? 'SAFE' : 'OFFLINE')}
            </span>
          </div>
          <div className="text-[10px] font-medium text-slate-500 leading-tight">
            {realTelemetry?.flood_risk_text ?? (isOnline ? 'Safe container depth' : 'Awaiting sensor stream')}
          </div>
        </div>
      </div>
    </div>
  );
};
