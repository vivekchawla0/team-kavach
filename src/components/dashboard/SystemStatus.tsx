import React from 'react';
import { Check, ChevronRight, Settings } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const SystemStatus: React.FC = () => {
  const { summary } = useDashboard();
  const statusText = summary?.system_status || 'All Systems Operational';

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      <div className="flex items-center gap-2 mb-3 text-slate-900">
        <Settings className="w-4 h-4 text-sky-600" />
        <h3 className="font-bold text-sm">System Status</h3>
      </div>

      <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 hover:bg-emerald-100/70 transition-colors cursor-pointer group">
        <div className="flex items-center gap-3">
          <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center shrink-0">
            <Check className="w-3.5 h-3.5 stroke-[3]" />
          </div>
          <span className="font-bold text-xs text-emerald-900">{statusText}</span>
        </div>
        <ChevronRight className="w-4 h-4 text-emerald-600 group-hover:translate-x-0.5 transition-transform" />
      </div>
    </div>
  );
};
