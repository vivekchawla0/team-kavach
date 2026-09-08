import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Radio,
  CloudRain,
  ShieldAlert,
  Bell,
  FileText,
  Map as MapIcon,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const Sidebar: React.FC = () => {
  const { alerts } = useDashboard();
  const activeAlertCount = alerts.filter((a) => a.status === 'ACTIVE').length;

  const navItems = [
    { label: 'Dashboard', icon: LayoutDashboard, active: true, href: '#' },
    { label: 'Live Monitoring', icon: Activity, active: false, href: '#live' },
    { label: 'Sensors', icon: Radio, active: false, href: '#sensors' },
    { label: 'Weather & Forecast', icon: CloudRain, active: false, href: '#weather' },
    { label: 'AI Risk Analysis', icon: ShieldAlert, active: false, href: '#risk' },
    { label: 'Alerts', icon: Bell, active: false, href: '#alerts', badge: activeAlertCount || 3 },
    { label: 'Reports', icon: FileText, active: false, href: '#reports' },
    { label: 'Map View', icon: MapIcon, active: false, href: '#map' },
    { label: 'Settings', icon: Settings, active: false, href: '#settings' },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 p-5 sticky top-0 h-screen overflow-y-auto z-40">
      {/* Brand Header */}
      <div className="pb-5 border-b border-slate-100 flex items-center gap-3">
        <svg className="w-9 h-7" viewBox="0 0 36 28" fill="none">
          <path d="M2 14C6 8 10 8 14 14C18 20 22 20 26 14C30 8 34 8 34 8" stroke="#0284c7" strokeWidth="3.5" strokeLinecap="round" />
          <path d="M2 20C6 14 10 14 14 20C18 26 22 26 26 20C30 14 34 14 34 14" stroke="#38bdf8" strokeWidth="3.5" strokeLinecap="round" />
          <path d="M2 8C6 2 10 2 14 8C18 14 22 14 26 8C30 2 34 2 34 2" stroke="#0369a1" strokeWidth="3.5" strokeLinecap="round" />
        </svg>
        <div>
          <span className="font-extrabold text-xl text-slate-900 tracking-tight block leading-none">
            FloodWatch
          </span>
          <span className="text-[10px] font-semibold text-slate-400 tracking-wider lowercase">
            monitor predict protect
          </span>
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-5 flex flex-col gap-1 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <a
              key={item.label}
              href={item.href}
              className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-[13.5px] font-medium transition-all ${
                item.active
                  ? 'bg-blue-600 text-white font-semibold shadow-md shadow-blue-500/20'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
              {item.badge !== undefined && (
                <span className="ml-auto bg-red-500 text-white text-[11px] font-bold px-2 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </a>
          );
        })}
      </nav>

      {/* Resilient Future Footer Card */}
      <div className="mt-auto bg-gradient-to-br from-sky-50 via-blue-50 to-indigo-50 border border-sky-100/80 rounded-2xl p-4 relative overflow-hidden">
        <h4 className="font-bold text-sm text-sky-900 leading-snug mb-3">
          Safer Communities Stronger Tomorrows.
        </h4>
        <div className="flex items-center gap-2.5 text-sky-700">
          <ShieldCheck className="w-5 h-5 text-sky-600 shrink-0" />
          <div>
            <strong className="text-xs block text-slate-800 font-semibold">FloodWatch v1.0</strong>
            <p className="text-[10.5px] text-sky-700">Built for a resilient future.</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
