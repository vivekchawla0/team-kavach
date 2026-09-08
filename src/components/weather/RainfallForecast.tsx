import React, { useMemo } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { CloudRain } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip);

export const RainfallForecast: React.FC = () => {
  const { weatherForecast } = useDashboard();

  const labels = useMemo(() => {
    if (!weatherForecast?.hourly || weatherForecast.hourly.length === 0) {
      return ['Now', '3h', '6h', '9h', '12h', '18h', '24h'];
    }
    return weatherForecast.hourly.map((_, i) => (i === 0 ? 'Now' : `${i * 3}h`));
  }, [weatherForecast]);

  const rainData = useMemo(() => {
    if (!weatherForecast?.hourly || weatherForecast.hourly.length === 0) {
      return [12, 24, 48, 36, 22, 14, 8];
    }
    return weatherForecast.hourly.map((h) => h.expected_rainfall_mm);
  }, [weatherForecast]);

  const total24h = weatherForecast?.total_rainfall_24h_mm ?? 120;
  const peakRate = weatherForecast?.peak_rainfall_mm_hr ?? 48;
  const peakWindow = weatherForecast?.peak_time_window ?? '09:00 - 10:00';
  const probability = weatherForecast?.heavy_rain_probability_percent ?? 85;

  const maxVal = Math.max(...rainData, 48);

  const chartData = {
    labels,
    datasets: [
      {
        label: 'Precipitation (mm)',
        data: rainData,
        backgroundColor: (context: any) => {
          const val = context.raw;
          return val === maxVal ? '#2563eb' : '#93c5fd';
        },
        borderRadius: 4,
        borderSkipped: false,
        barPercentage: 0.65,
      },
    ],
  };

  const chartOptions: any = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#0f172a',
        padding: 8,
        cornerRadius: 6,
        callbacks: {
          label: (item: any) => ` Rain: ${item.raw} mm`,
        },
      },
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          font: { size: 9.5 },
          color: '#94a3b8',
        },
      },
      y: {
        min: 0,
        max: 60,
        ticks: {
          stepSize: 20,
          font: { size: 9.5 },
          color: '#94a3b8',
        },
        grid: {
          color: '#f8fafc',
        },
      },
    },
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-slate-900">
          <CloudRain className="w-4 h-4 text-sky-600" />
          <h3 className="font-bold text-sm">
            Rainfall Forecast <span className="text-slate-400 font-normal">(Next 24 Hours)</span>
          </h3>
        </div>
        <span className="text-[10.5px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
          Source: DWD
        </span>
      </div>

      {/* Bar Chart Canvas */}
      <div className="h-36 w-full mb-3">
        <Bar data={chartData} options={chartOptions} />
      </div>

      {/* Summary Subcards */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100">
        <div className="bg-slate-50 rounded-lg p-2.5">
          <span className="text-[10.5px] font-medium text-slate-400 block">Total (24h)</span>
          <strong className="text-sm font-extrabold text-slate-900 block leading-tight">
            {total24h} mm
          </strong>
          <span className="text-[10px] font-semibold text-rose-600">↑ High</span>
        </div>

        <div className="bg-slate-50 rounded-lg p-2.5">
          <span className="text-[10.5px] font-medium text-slate-400 block">Peak (6h)</span>
          <strong className="text-sm font-extrabold text-slate-900 block leading-tight">
            {peakRate} mm/hr
          </strong>
          <span className="text-[10px] font-medium text-slate-400 truncate block">
            {peakWindow}
          </span>
        </div>

        <div className="bg-slate-50 rounded-lg p-2.5">
          <span className="text-[10.5px] font-medium text-slate-400 block">Probability</span>
          <strong className="text-sm font-extrabold text-slate-900 block leading-tight">
            {Math.round(probability)}%
          </strong>
          <span className="text-[10px] font-semibold text-rose-600">Heavy rain</span>
        </div>
      </div>
    </div>
  );
};
