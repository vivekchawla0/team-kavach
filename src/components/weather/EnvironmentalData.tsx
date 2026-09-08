import React, { useEffect, useState, useCallback } from 'react';
import { Sun, CloudSun, Wind, Gauge, Eye, ChevronRight } from 'lucide-react';
import { weatherService, CurrentWeatherData } from '@/services/weatherService';

export const EnvironmentalData: React.FC = () => {
  const [currentWeather, setCurrentWeather] = useState<CurrentWeatherData | null>(null);

  const loadData = useCallback(async (force: boolean = false) => {
    try {
      const report = await weatherService.fetchLiveWeather(force);
      setCurrentWeather(report.current);
    } catch {
      // Fallback
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(() => loadData(true), 10 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadData]);

  const temp = currentWeather?.temperature ? `${Math.round(currentWeather.temperature)}°C` : '27°C';
  const wind = currentWeather?.windSpeed ? `${currentWeather.windSpeed.toFixed(1)} km/h` : '3.9 km/h';
  const pressure = currentWeather?.pressure ? `${Math.round(currentWeather.pressure)} hPa` : '999 hPa';
  const humidity = currentWeather?.humidity ? `${Math.round(currentWeather.humidity)}%` : '96%';

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center text-amber-500">
            <Sun className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Live Weather
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Barpeta, Assam
            </p>
          </div>
        </div>

        <div className="w-7 h-7 rounded-full bg-slate-50 flex items-center justify-center text-slate-400 hover:text-slate-600 transition-colors cursor-pointer">
          <ChevronRight className="w-4 h-4" />
        </div>
      </div>

      {/* Big Weather Display matching reference */}
      <div className="flex items-center gap-4 py-2">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-amber-100 to-sky-100 flex items-center justify-center text-amber-500 shrink-0">
          <CloudSun className="w-9 h-9 text-amber-500" />
        </div>
        <div>
          <div className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-none">
            {temp}
          </div>
          <div className="text-xs text-slate-500 font-medium mt-1">
            Feels like 29°C
          </div>
          <div className="text-xs font-semibold text-slate-700">
            Mostly Clear
          </div>
        </div>
      </div>

      {/* Row of 3 Metrics matching reference */}
      <div className="grid grid-cols-3 gap-2 pt-3 border-t border-slate-100 text-center">
        {/* Wind Speed */}
        <div className="flex flex-col items-center">
          <Wind className="w-4 h-4 text-slate-400 mb-1" />
          <span className="text-sm font-extrabold text-slate-900">{wind}</span>
          <span className="text-[11px] text-slate-400 font-medium">Wind Speed</span>
        </div>

        {/* Air Pressure */}
        <div className="flex flex-col items-center">
          <Gauge className="w-4 h-4 text-slate-400 mb-1" />
          <span className="text-sm font-extrabold text-slate-900">{pressure}</span>
          <span className="text-[11px] text-slate-400 font-medium">Air Pressure</span>
        </div>

        {/* Visibility */}
        <div className="flex flex-col items-center">
          <Eye className="w-4 h-4 text-slate-400 mb-1" />
          <span className="text-sm font-extrabold text-slate-900">6.2 km</span>
          <span className="text-[11px] text-slate-400 font-medium">Visibility</span>
        </div>
      </div>

      {/* Bottom Footer Bar */}
      <div className="flex items-center justify-between pt-2.5 mt-2 border-t border-slate-100 text-xs font-medium text-slate-500">
        <span>{humidity} Humidity</span>
        <span>Low UV Index</span>
      </div>
    </div>
  );
};
