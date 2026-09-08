import React from 'react';
import { useDashboard } from '@/context/DashboardContext';
import { SimulatorScenario } from '@/types';

export const SimulatorToolbar: React.FC = () => {
  const { triggerScenario, activeScenario } = useDashboard();

  const scenarios: { id: SimulatorScenario; label: string; isDanger?: boolean; isSubtle?: boolean }[] = [
    { id: 'normal', label: 'Normal Flow' },
    { id: 'storm', label: 'Heavy Storm' },
    { id: 'flood', label: 'Flash Flood Event', isDanger: true },
    { id: 'reset', label: 'Reset', isSubtle: true },
  ];

  return (
    <div className="fixed bottom-4 right-6 bg-slate-900/90 backdrop-blur-md border border-white/15 rounded-full px-4 py-2 flex items-center gap-3 shadow-2xl z-50 text-white">
      {/* Title */}
      <div className="flex items-center gap-2 pr-3 border-r border-white/20">
        <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
        <span className="text-[11px] font-bold tracking-wider uppercase">Interactive Simulator</span>
      </div>

      {/* Buttons */}
      <div className="flex items-center gap-1.5">
        {scenarios.map((sc) => (
          <button
            key={sc.id}
            onClick={() => triggerScenario(sc.id)}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
              activeScenario === sc.id
                ? 'bg-blue-600 text-white shadow-md'
                : sc.isDanger
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-600 hover:text-white'
                : sc.isSubtle
                ? 'bg-transparent text-slate-400 border border-dashed border-white/30 hover:bg-white/10 hover:text-white'
                : 'bg-white/10 text-slate-200 border border-white/20 hover:bg-white hover:text-slate-900'
            }`}
          >
            {sc.label}
          </button>
        ))}
      </div>
    </div>
  );
};
