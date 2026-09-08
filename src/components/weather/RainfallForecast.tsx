import React, { useEffect, useState, useMemo, useCallback } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { CloudRain, ChevronRight, ChevronDown } from 'lucide-react';
import { weatherService, LiveWeatherReport } from '@/services/weatherService';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip);

export const RainfallForecast: React.FC = () => {
  const [weatherData, setWeatherData] = useState<LiveWeatherReport | null>(null);

  const loadWeather = useCallback(async (force: boolean = false) => {
    try {
      const data = await weatherService.fetchLiveWeather(force);
      setWeatherData(data);
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    loadWeather();
    const interval = setInterval(() => {
      loadWeather(true);
    }, 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadWeather]);

  // Labels matching reference: Now, 04, 08, 12, 16, 20, 24h
  const labels = ['Now', '04', '08', '12', '16', '20', '24h'];
  const rainData = [0.2, 0.5, 1.0, 1.8, 2.5, 1.2, 0.4];

  const chartData = useMemo(() => {
    return {
      labels,
      datasets: [
        {
          label: 'Precipitation',
          data: rainData,
          backgroundColor: '#0284c7',
          borderRadius: 4,
          borderSkipped: false,
          barPercentage: 0.5,
        },
      ],
    };
  }, [labels, rainData]);

  const chartOptions: any = useMemo(() => {
    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { size: 10, weight: '500' },
            color: '#94a3b8',
          },
        },
        y: {
          min: 0,
          max: 6,
          ticks: {
            stepSize: 2,
            font: { size: 10, weight: '500' },
            color: '#94a3b8',
          },
          grid: { color: '#f8fafc' },
        },
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#0f172a',
          padding: 8,
          cornerRadius: 8,
          callbacks: {
            label: (context: any) => ` ${context.parsed.y} mm/hr`,
          },
        },
      },
    };
  }, []);

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600">
            <CloudRain className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Rainfall Forecast
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Next 24 Hours • Barpeta, Assam
            </p>
          </div>
        </div>

        <div className="w-7 h-7 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      {/* Chart Canvas */}
      <div className="h-[150px] w-full relative my-1">
        <Bar data={chartData} options={chartOptions} />
      </div>

      {/* 3 Metric Boxes matching reference */}
      <div className="grid grid-cols-3 gap-2.5 pt-3 border-t border-slate-100 text-center">
        {/* Total 24h */}
        <div className="bg-slate-50/80 rounded-xl p-2.5 border border-slate-100 flex flex-col items-center">
          <span className="text-[11px] font-medium text-slate-500">Total 24h</span>
          <span className="text-base sm:text-lg font-extrabold text-slate-900 mt-1">3.5 mm</span>
        </div>

        {/* Peak Rainfall */}
        <div className="bg-slate-50/80 rounded-xl p-2.5 border border-slate-100 flex flex-col items-center">
          <span className="text-[11px] font-medium text-slate-500">Peak Rainfall</span>
          <span className="text-base sm:text-lg font-extrabold text-slate-900 mt-1">1 mm/hr</span>
          <span className="text-[9.5px] text-slate-400 mt-0.5">(15:00 - 16:00)</span>
        </div>

        {/* Rain Probability */}
        <div className="bg-slate-50/80 rounded-xl p-2.5 border border-slate-100 flex flex-col items-center">
          <div className="flex items-center gap-0.5 text-[11px] font-medium text-slate-500">
            <span>Rain Probability</span>
            <ChevronDown className="w-3 h-3 text-slate-400" />
          </div>
          <span className="text-base sm:text-lg font-extrabold text-slate-900 mt-1">90%</span>
          <span className="text-[9.5px] text-sky-600 font-semibold mt-0.5">High Chance</span>
        </div>
      </div>
    </div>
  );
};
