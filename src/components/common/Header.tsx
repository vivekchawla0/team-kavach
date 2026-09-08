import React, { useState, useEffect } from 'react';
import { Search, Bell, ChevronDown, CloudRain } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const Header: React.FC = () => {
  const { weatherCurrent, alerts } = useDashboard();
  const [timeStr, setTimeStr] = useState('14:32');
  const [dateStr, setDateStr] = useState('Mon, 8 Sep 2025');

  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const hours = String(now.getHours()).padStart(2, '0');
      const mins = String(now.getMinutes()).padStart(2, '0');
      setTimeStr(`${hours}:${mins}`);

      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      setDateStr(`${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="relative min-h-[240px] px-6 sm:px-10 lg:px-12 py-6 flex flex-col justify-between overflow-hidden text-white">
      {/* Background Image & Gradient Overlay */}
      <div
        className="absolute inset-0 bg-cover bg-[center_38%] scale-[1.02] brightness-90 z-0"
        style={{ backgroundImage: "url('/assets/hero.jpg')" }}
      />
      <div className="absolute inset-0 bg-gradient-to-b from-slate-950/60 via-slate-900/75 to-slate-900/90 z-0" />

      {/* Top Utility Bar */}
      <div className="relative z-10 flex items-center justify-between flex-wrap gap-4">
        {/* Project Branding: JAL SUCHAK */}
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 via-cyan-400 to-teal-400 p-[1.5px] shadow-lg shadow-sky-500/20 flex items-center justify-center shrink-0">
            <div className="w-full h-full bg-slate-950/75 backdrop-blur-sm rounded-[10px] flex items-center justify-center">
              <svg className="w-6 h-5" viewBox="0 0 36 28" fill="none">
                <path d="M2 14C6 8 10 8 14 14C18 20 22 20 26 14C30 8 34 8 34 8" stroke="#38bdf8" strokeWidth="3" strokeLinecap="round" />
                <path d="M2 20C6 14 10 14 14 20C18 26 22 26 26 20C30 14 34 14 34 14" stroke="#7dd3fc" strokeWidth="3" strokeLinecap="round" />
                <path d="M2 8C6 2 10 2 14 8C18 14 22 14 26 8C30 2 34 2 34 2" stroke="#0284c7" strokeWidth="3" strokeLinecap="round" />
              </svg>
            </div>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2.5">
              <span className="font-extrabold text-xl tracking-wider text-white uppercase drop-shadow">
                JAL SUCHAK
              </span>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-sky-500/25 text-sky-300 border border-sky-400/35 tracking-widest uppercase">
                Early Warning System
              </span>
            </div>
            <span className="text-[10.5px] font-medium text-slate-300 tracking-wide">
              जल सूचक • Real-Time River Telemetry & Flood Early Warning Platform
            </span>
          </div>
        </div>

        {/* Search, Notifications & User */}
        <div className="flex items-center gap-3.5">
          {/* Search Box */}
          <div className="relative flex items-center">
            <Search className="absolute left-3 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              type="text"
              placeholder="Search sensors, locations..."
              className="bg-white text-slate-800 text-xs pl-9 pr-14 py-2 rounded-full border border-slate-200 shadow-sm focus:outline-none focus:ring-2 focus:ring-sky-500 w-60 focus:w-72 transition-all placeholder:text-slate-400"
            />
            <kbd className="absolute right-3 bg-slate-100 border border-slate-200 text-slate-500 text-[10px] font-semibold px-1.5 py-0.5 rounded">
              ⌘ K
            </kbd>
          </div>

          {/* Notifications */}
          <button
            className="w-9 h-9 rounded-full bg-white/90 hover:bg-white text-slate-700 flex items-center justify-center relative shadow-sm transition-transform hover:-translate-y-0.5"
            title="View Alerts"
          >
            <Bell className="w-4 h-4" />
            {activeAlertCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[9.5px] font-bold w-4 h-4 rounded-full flex items-center justify-center border-2 border-white">
                {activeAlertCount}
              </span>
            )}
          </button>

          {/* User Badge */}
          <div className="flex items-center gap-2.5 bg-white/90 hover:bg-white text-slate-900 px-2.5 py-1 rounded-full shadow-sm cursor-pointer transition-colors">
            <div className="w-7 h-7 rounded-full bg-slate-800 text-white font-bold text-xs flex items-center justify-center">
              VC
            </div>
            <div className="flex flex-col text-left">
              <span className="text-xs font-bold leading-tight">Vivek Chawla</span>
              <span className="text-[9.5px] text-slate-500 leading-none">Administrator</span>
            </div>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
          </div>
        </div>
      </div>

      {/* Hero Content & Weather Widget */}
      <div className="relative z-10 flex items-end justify-between mt-auto pt-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white drop-shadow-md">
            Real-Time Flood Monitoring
          </h1>
          <p className="text-sm text-slate-200/90 font-normal mt-1 drop-shadow">
            Early insights. Faster response. Safer communities.
          </p>
        </div>

        {/* Live Clock & Glass Weather Pill */}
        <div className="flex items-center gap-4">
          <div className="text-right flex flex-col items-end">
            <span className="text-[11.5px] font-medium text-slate-300">{dateStr}</span>
            <span className="text-2xl font-extrabold text-white tracking-tight leading-none mt-0.5">
              {timeStr}
            </span>
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-emerald-400 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live Data
            </span>
          </div>

          {/* Glass Weather Widget */}
          <div className="flex items-center gap-4 bg-slate-900/65 backdrop-blur-md border border-white/15 rounded-2xl px-4 py-2.5 shadow-xl">
            <div className="flex items-center gap-3 pr-3.5 border-r border-white/15">
              <CloudRain className="w-7 h-7 text-sky-400" />
              <div>
                <span className="text-lg font-extrabold text-white leading-none block">
                  {weatherCurrent ? `${Math.round(weatherCurrent.temperature)}°C` : '12°C'}
                </span>
                <span className="text-[11px] text-slate-300 font-medium">
                  {weatherCurrent?.weather_condition || 'Light Rain'}
                </span>
              </div>
            </div>
            <div className="flex flex-col gap-0.5 text-xs">
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-400 text-[11px]">Humidity</span>
                <strong className="font-semibold text-white">
                  {weatherCurrent ? `${Math.round(weatherCurrent.humidity)}%` : '78%'}
                </strong>
              </div>
              <div className="flex items-center justify-between gap-4">
                <span className="text-slate-400 text-[11px]">Wind</span>
                <strong className="font-semibold text-white">
                  {weatherCurrent ? `${Math.round(weatherCurrent.wind_speed)} km/h` : '15 km/h'}
                </strong>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
