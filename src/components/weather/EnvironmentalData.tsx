import React from 'react';
import { Thermometer, Wind, Sprout, Gauge } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const EnvironmentalData: React.FC = () => {
  const { weatherCurrent, summary } = useDashboard();

  const temp = weatherCurrent ? `${Math.round(weatherCurrent.temperature)}°C` : '12°C';
  const wind = weatherCurrent ? `${Math.round(weatherCurrent.wind_speed)} km/h` : '15 km/h';
  const soil = summary ? `${Math.round(summary.soil_moisture_percent)}%` : '92%';
  const pressure = weatherCurrent ? `${Math.round(weatherCurrent.atmospheric_pressure)} hPa` : '1012 hPa';

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      <div className="flex items-center gap-2 mb-3 text-slate-900">
        <Thermometer className="w-4 h-4 text-sky-600" />
        <h3 className="font-bold text-sm">Environmental Data</h3>
      </div>

      <div className="grid grid-cols-2 gap-2.5">
        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-white shadow-xs flex items-center justify-center text-sky-600">
            <Thermometer className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <strong className="text-sm font-extrabold text-slate-900 leading-tight">{temp}</strong>
            <span className="text-[10px] text-slate-400 font-medium">Temperature</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-white shadow-xs flex items-center justify-center text-cyan-600">
            <Wind className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <strong className="text-sm font-extrabold text-slate-900 leading-tight">{wind}</strong>
            <span className="text-[10px] text-slate-400 font-medium">Wind Speed</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-white shadow-xs flex items-center justify-center text-emerald-600">
            <Sprout className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <strong className="text-sm font-extrabold text-slate-900 leading-tight">{soil}</strong>
            <span className="text-[10px] text-slate-400 font-medium">Soil Moisture</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 p-2.5 rounded-xl bg-slate-50 border border-slate-100">
          <div className="w-8 h-8 rounded-lg bg-white shadow-xs flex items-center justify-center text-teal-600">
            <Gauge className="w-4 h-4" />
          </div>
          <div className="flex flex-col">
            <strong className="text-sm font-extrabold text-slate-900 leading-tight">{pressure}</strong>
            <span className="text-[10px] text-slate-400 font-medium">Air Pressure</span>
          </div>
        </div>
      </div>
    </div>
  );
};
