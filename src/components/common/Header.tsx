import React, { useState, useEffect } from 'react';
import {
  Droplets,
  CloudRain,
  Thermometer,
  Radio,
  MapPin,
  Activity,
  Brain,
  Shield,
  CloudSun,
} from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { weatherService, CurrentWeatherData } from '@/services/weatherService';

export const Header: React.FC = () => {
  const { summary } = useDashboard();
  const [liveWeather, setLiveWeather] = useState<CurrentWeatherData | null>(null);
  const [timeStr, setTimeStr] = useState('04:06 AM');
  const [dateStr, setDateStr] = useState('Wed, 9 Sep 2026');

  const waterLevel = summary?.average_water_level_m ?? 3.17;
  const rainfall = summary?.current_rainfall_mm_hr ?? 65;

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      let hours = now.getHours();
      const minutes = String(now.getMinutes()).padStart(2, '0');
      const ampm = hours >= 12 ? 'PM' : 'AM';
      hours = hours % 12 || 12;
      const hoursStr = String(hours).padStart(2, '0');
      setTimeStr(`${hoursStr}:${minutes} ${ampm}`);

      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      setDateStr(`${days[now.getDay()]}, ${now.getDate()} ${months[now.getMonth()]} ${now.getFullYear()}`);
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    weatherService
      .fetchLiveWeather()
      .then((report) => {
        if (report?.current) {
          setLiveWeather(report.current);
        }
      })
      .catch(() => {});
  }, []);

  const temperature = liveWeather ? `${liveWeather.temperature.toFixed(1)}°C` : '26.9°C';
  const weatherDesc = liveWeather?.weatherCondition || 'Mostly Clear';

  return (
    <header className="relative w-full overflow-hidden bg-gradient-to-b from-sky-50/50 via-white to-slate-50/80 border-b border-slate-200/80">
      {/* Scenic Assam River Landscape Background - Aligned Right with Soft Left Fade */}
      <div
        className="absolute inset-y-0 right-0 w-full lg:w-[68%] bg-cover bg-[center_35%] pointer-events-none opacity-85 transition-opacity duration-700"
        style={{ backgroundImage: "url('/assets/hero.jpg')" }}
      />

      {/* Atmospheric Soft Gradient Fade (Smooth transition so left text is 100% readable) */}
      <div className="absolute inset-0 bg-gradient-to-r from-white via-white/95 to-transparent pointer-events-none hidden sm:block lg:w-[48%]" />
      <div className="absolute inset-0 bg-gradient-to-t from-white/90 via-transparent to-white/40 pointer-events-none" />

      {/* Subtle Assam Topographic Silhouette Graphic on far right */}
      <div className="absolute top-4 right-10 pointer-events-none hidden xl:flex flex-col items-center opacity-40">
        <svg className="w-28 h-20 text-sky-800" viewBox="0 0 120 80" fill="currentColor">
          <path d="M10,40 Q25,25 45,35 T75,20 T105,30 Q115,45 100,60 T60,65 T20,55 Z" opacity="0.15" />
          <circle cx="85" cy="35" r="3" fill="#0284c7" />
        </svg>
        <span className="text-[10px] font-bold tracking-widest uppercase text-sky-900/60 -mt-2">
          Assam
        </span>
      </div>

      {/* Decorative Handwritten Environmental Script over the scenic landscape */}
      <div className="absolute top-7 left-[45%] lg:left-[48%] xl:left-[50%] hidden md:block pointer-events-none z-10">
        <div className="font-script text-slate-700/80 text-xl lg:text-2xl font-bold leading-tight -rotate-3 select-none drop-shadow-xs">
          Safer Rivers
          <br />
          <span className="ml-3">Stronger Communities</span>
          <br />
          <span className="ml-7">A Resilient Assam</span>
        </div>
      </div>

      {/* Main Container */}
      <div className="relative z-20 px-5 sm:px-8 lg:px-10 py-5 sm:py-6 max-w-[1920px] mx-auto flex flex-col gap-6">
        {/* Top Branding Bar */}
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Logo & Brand Identity */}
          <div className="flex items-center gap-3.5">
            {/* Custom 3-Wave Hydrodynamic Brand Mark */}
            <div className="w-12 h-12 flex items-center justify-center shrink-0">
              <svg className="w-11 h-11" viewBox="0 0 44 44" fill="none">
                {/* 3 Fluid Curved Waves Stacked Vertically */}
                <path
                  d="M6 15C11 11 16 11 22 15C28 19 33 19 38 15"
                  stroke="#38bdf8"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                />
                <path
                  d="M6 22C11 18 16 18 22 22C28 26 33 26 38 22"
                  stroke="#0284c7"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                />
                <path
                  d="M7 29C12 25 17 25 22 29C27 33 32 33 37 29"
                  stroke="#0369a1"
                  strokeWidth="3.2"
                  strokeLinecap="round"
                />
              </svg>
            </div>

            <div className="flex flex-col">
              <div className="flex items-center gap-2.5">
                <span className="font-extrabold text-2xl tracking-tight text-slate-900 font-sans">
                  Jal Suchak
                </span>
                <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-200/80 tracking-wider uppercase">
                  EARLY WARNING SYSTEM
                </span>
              </div>
              <span className="text-[11.5px] font-medium text-slate-500 tracking-wide">
                जल सूचक • Real-Time River Intelligence & Flood Early Warning
              </span>
            </div>
          </div>

          {/* Minimal Location Badge (Top-Right) */}
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/95 backdrop-blur-sm border border-slate-200 text-xs font-semibold text-slate-700 shadow-2xs">
            <MapPin className="w-3.5 h-3.5 text-sky-600" />
            <span>Barpeta Station FW-001</span>
            <span className="text-slate-300">•</span>
            <span className="text-slate-500 font-medium">Assam, India</span>
          </div>
        </div>

        {/* Hero Body: Left Typography + Right Floating LIVE TELEMETRY Card */}
        <div className="flex items-end justify-between flex-wrap lg:flex-nowrap gap-6 pt-2 pb-1">
          {/* Left Column: Heading, Tagline & 3 Capability Badges */}
          <div className="flex flex-col max-w-xl">
            <h1 className="text-3xl sm:text-4xl lg:text-[44px] font-extrabold tracking-tight text-slate-900 leading-[1.12]">
              Real-Time
              <br />
              <span className="text-sky-600">Flood Intelligence</span>
            </h1>
            <p className="text-sm sm:text-base text-slate-500 font-normal mt-2.5 leading-relaxed">
              Monitoring rivers. Predicting floods. Protecting communities.
            </p>

            {/* 3 Capability Pills */}
            <div className="flex items-center flex-wrap gap-2.5 mt-5">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/95 border border-slate-200/90 text-xs font-bold text-slate-700 shadow-2xs">
                <div className="w-5 h-5 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
                  <Activity className="w-3 h-3" />
                </div>
                <span>Real-Time Monitoring</span>
              </div>

              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/95 border border-slate-200/90 text-xs font-bold text-slate-700 shadow-2xs">
                <div className="w-5 h-5 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
                  <Brain className="w-3 h-3" />
                </div>
                <span>AI-Powered Forecasts</span>
              </div>

              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/95 border border-slate-200/90 text-xs font-bold text-slate-700 shadow-2xs">
                <div className="w-5 h-5 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
                  <Shield className="w-3 h-3" />
                </div>
                <span>Disaster Resilience</span>
              </div>
            </div>
          </div>

          {/* Right Column: Floating LIVE TELEMETRY Card matching reference image */}
          <div className="bg-white/95 backdrop-blur-md rounded-2xl border border-slate-200 shadow-md shadow-slate-200/60 p-4 sm:p-5 w-full sm:w-[340px] shrink-0 transition-all">
            {/* Top Row: Title & Online Badge */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Radio className="w-4 h-4 text-sky-600 animate-pulse" />
                <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-800">
                  LIVE TELEMETRY
                </span>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[11px] font-bold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                ONLINE
              </div>
            </div>

            {/* Middle Row: Time/Date & Temperature */}
            <div className="flex items-center justify-between py-3">
              <div>
                <div className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight font-sans">
                  {timeStr}
                </div>
                <div className="text-xs text-slate-400 font-medium mt-0.5">
                  {dateStr}
                </div>
              </div>

              <div className="flex items-center gap-2 text-right">
                <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center text-sky-500">
                  <CloudSun className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-xl font-extrabold text-slate-900 tracking-tight">
                    {temperature}
                  </div>
                  <div className="text-[11px] text-slate-400 font-medium">
                    {weatherDesc}
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom Row: 3 Metrics Horizontal Bar */}
            <div className="pt-3 border-t border-slate-100 grid grid-cols-3 gap-2 text-center">
              {/* Water Level */}
              <div className="flex flex-col items-center">
                <div className="flex items-center gap-1 text-slate-400 text-[11px] font-medium">
                  <Droplets className="w-3 h-3 text-sky-500" />
                  <span>Water Level</span>
                </div>
                <span className="text-sm sm:text-base font-extrabold text-slate-900 mt-0.5">
                  {waterLevel.toFixed(2)} m
                </span>
              </div>

              {/* Rainfall */}
              <div className="flex flex-col items-center">
                <div className="flex items-center gap-1 text-slate-400 text-[11px] font-medium">
                  <CloudRain className="w-3 h-3 text-sky-500" />
                  <span>Rainfall</span>
                </div>
                <span className="text-sm sm:text-base font-extrabold text-slate-900 mt-0.5">
                  {Math.round(rainfall)} mm/hr
                </span>
              </div>

              {/* Temperature */}
              <div className="flex flex-col items-center">
                <div className="flex items-center gap-1 text-slate-400 text-[11px] font-medium">
                  <Thermometer className="w-3 h-3 text-rose-500" />
                  <span>Temperature</span>
                </div>
                <span className="text-sm sm:text-base font-extrabold text-slate-900 mt-0.5">
                  {temperature}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
