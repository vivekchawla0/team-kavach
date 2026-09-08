import React from 'react';
import { AlertCircle, AlertTriangle, Info, CheckCircle2, ShieldCheck } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { AlertSeverity } from '@/types';
import { formatTimeAgo } from '@/utils/formatters';

export const RecentAlerts: React.FC = () => {
  const { alerts, acknowledgeAlert } = useDashboard();

  const getSeverityBadge = (severity: AlertSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return {
          icon: AlertCircle,
          pillClass: 'bg-rose-100 text-rose-700',
          iconBoxClass: 'bg-rose-100 text-rose-600',
        };
      case 'WARNING':
        return {
          icon: AlertTriangle,
          pillClass: 'bg-amber-100 text-amber-700',
          iconBoxClass: 'bg-amber-100 text-amber-600',
        };
      case 'RESOLVED':
        return {
          icon: CheckCircle2,
          pillClass: 'bg-emerald-100 text-emerald-700',
          iconBoxClass: 'bg-emerald-100 text-emerald-600',
        };
      case 'SYSTEM':
        return {
          icon: ShieldCheck,
          pillClass: 'bg-slate-100 text-slate-700',
          iconBoxClass: 'bg-slate-100 text-slate-600',
        };
      default:
        return {
          icon: Info,
          pillClass: 'bg-sky-100 text-sky-700',
          iconBoxClass: 'bg-sky-100 text-sky-600',
        };
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-slate-900">
          <AlertCircle className="w-4 h-4 text-rose-600 animate-pulse" />
          <h3 className="font-bold text-sm">Recent Alerts</h3>
        </div>
        <a href="#alerts" className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1">
          View All →
        </a>
      </div>

      {/* Alerts Feed */}
      <div className="flex flex-col gap-2.5 overflow-y-auto max-h-[300px] pr-1">
        {alerts.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-400">No active alerts recorded</div>
        ) : (
          alerts.map((alert) => {
            const config = getSeverityBadge(alert.severity);
            const Icon = config.icon;
            return (
              <div
                key={alert.id}
                className="flex items-start gap-3 p-2.5 rounded-xl bg-slate-50 border border-slate-100/80 hover:bg-white hover:shadow-sm transition-all"
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${config.iconBoxClass}`}>
                  <Icon className="w-3.5 h-3.5" />
                </div>
                <div className="flex flex-col flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <span className={`text-[9.5px] font-bold uppercase px-1.5 py-0.2 rounded ${config.pillClass}`}>
                      {alert.severity}
                    </span>
                    <span className="text-[10px] text-slate-400 font-medium">
                      {formatTimeAgo(alert.created_at)}
                    </span>
                  </div>
                  <strong className="text-xs font-bold text-slate-900 leading-snug">
                    {alert.title}
                  </strong>
                  <p className="text-[11px] text-slate-500 leading-tight mt-0.5">
                    {alert.message}
                  </p>
                  {alert.status === 'ACTIVE' && (
                    <button
                      onClick={() => acknowledgeAlert(alert.id)}
                      className="self-end text-[10px] text-sky-600 hover:text-sky-800 font-semibold mt-1"
                    >
                      Acknowledge
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
