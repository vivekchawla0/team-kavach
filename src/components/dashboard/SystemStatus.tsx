import React from 'react';
import { Check, ShieldCheck } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const SystemStatus: React.FC = () => {
  const { summary } = useDashboard();
  const statusText = summary?.system_status || 'All Systems Operational';

  const components = [
    { name: 'Sensor Telemetry', status: 'Online', desc: 'Station FW-001' },
    { name: 'Weather API', status: 'Active', desc: 'ECMWF Live' },
    { name: 'Database', status: 'Healthy', desc: 'Store & Ingest' },
    { name: 'Blynk Cloud', status: 'Connected', desc: 'Cloud API' },
    { name: 'Backend', status: 'Running', desc: 'FastAPI v1' },
  ];

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 shadow-xs flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div>
            <h3 className="font-bold text-sm sm:text-base text-slate-900 leading-tight">
              System Status
            </h3>
            <p className="text-[11px] text-slate-500 font-medium">
              Operational Subsystems & Telemetry Engine
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-800">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>{statusText}</span>
        </div>
      </div>

      {/* Component Micro Indicators */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2">
        {components.map((comp) => (
          <div
            key={comp.name}
            className="bg-slate-50/90 p-2.5 rounded-xl border border-slate-100 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10.5px] font-bold text-slate-700 truncate">
                {comp.name}
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
            </div>
            <div className="mt-1 flex items-baseline justify-between text-[10px]">
              <span className="text-emerald-700 font-semibold">{comp.status}</span>
              <span className="text-slate-400 font-medium">{comp.desc}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
