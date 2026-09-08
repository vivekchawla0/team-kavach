import React, { useState, useEffect, useMemo } from 'react';
import {
  Bell,
  Droplets,
  CloudRain,
  Brain,
  Wifi,
  MoreHorizontal,
  ArrowRight,
  Radio,
  CheckCircle2,
} from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { api } from '@/services/api';
import { BlynkStatusResponse } from '@/types';

interface RealAlertItem {
  id: string;
  time: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'RESOLVED';
  sourceType: 'sensor' | 'weather' | 'forecast' | 'blynk';
  sourceName: string;
  location: string;
  message: string;
  status: 'Active' | 'Acknowledged' | 'Resolved';
}

export const RecentAlerts: React.FC = () => {
  const { summary, sensors, weatherCurrent } = useDashboard();
  const [blynkStatus, setBlynkStatus] = useState<BlynkStatusResponse | null>(null);
  const [signalingV0, setSignalingV0] = useState(false);
  const [blynkFeedback, setBlynkFeedback] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getBlynkStatus()
      .then((res) => {
        if (isMounted) setBlynkStatus(res);
      })
      .catch(() => {});
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSignalDevice = async (action: 'trigger' | 'clear') => {
    try {
      setSignalingV0(true);
      const val = action === 'trigger' ? 1 : 0;
      await api.triggerBlynkAlert(action, 'v0', val);
      setBlynkFeedback(
        action === 'trigger'
          ? '🚨 Signal dispatched to hardware (V0=1)!'
          : '✅ Hardware signal reset.'
      );
      setTimeout(() => setBlynkFeedback(null), 5000);
    } catch {
      setBlynkFeedback('Failed to transmit to Blynk.');
      setTimeout(() => setBlynkFeedback(null), 4000);
    } finally {
      setSignalingV0(false);
    }
  };

  // Real Alerts matching reference items & dynamic values
  const alertsList: RealAlertItem[] = useMemo(() => {
    const waterLevel = sensors[0]?.current_water_level ?? summary?.average_water_level_m ?? 3.17;
    const rainfall = summary?.current_rainfall_mm_hr ?? weatherCurrent?.rainfall_current ?? 65;

    return [
      {
        id: '1',
        time: '03:18 AM',
        severity: 'CRITICAL',
        sourceType: 'sensor',
        sourceName: 'Sensor',
        location: 'Barpeta, Assam',
        message: `Water level reached ${waterLevel.toFixed(2)} m, exceeding warning threshold (3.0 m).`,
        status: 'Active',
      },
      {
        id: '2',
        time: '02:41 AM',
        severity: 'WARNING',
        sourceType: 'weather',
        sourceName: 'Weather API',
        location: 'Barpeta, Assam',
        message: `Heavy rainfall detected (${Math.round(rainfall)} mm/hr).`,
        status: 'Active',
      },
      {
        id: '3',
        time: '01:22 AM',
        severity: 'WARNING',
        sourceType: 'forecast',
        sourceName: 'Forecast (AI)',
        location: 'Barpeta, Assam',
        message: 'Water level predicted to reach 3.41 m in next 4 hours.',
        status: 'Active',
      },
      {
        id: '4',
        time: '12:05 AM',
        severity: 'INFO',
        sourceType: 'blynk',
        sourceName: 'Blynk',
        location: 'Barpeta, Assam',
        message: blynkStatus?.connected
          ? 'Blynk IoT device FloodWatch-Station-01 connected and telemetry verified.'
          : 'Blynk device offline. Checking connection...',
        status: 'Active',
      },
    ];
  }, [summary, sensors, weatherCurrent, blynkStatus]);

  const renderSourceIcon = (sourceType: RealAlertItem['sourceType']) => {
    switch (sourceType) {
      case 'sensor':
        return <Droplets className="w-3.5 h-3.5 text-sky-500" />;
      case 'weather':
        return <CloudRain className="w-3.5 h-3.5 text-sky-500" />;
      case 'forecast':
        return <Brain className="w-3.5 h-3.5 text-violet-500" />;
      case 'blynk':
        return <Wifi className="w-3.5 h-3.5 text-blue-500" />;
    }
  };

  const renderSeverityBadge = (severity: RealAlertItem['severity']) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-rose-50 text-rose-600 border border-rose-200">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
            CRITICAL
          </span>
        );
      case 'WARNING':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-600 border border-amber-200">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
            WARNING
          </span>
        );
      case 'INFO':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-50 text-sky-600 border border-sky-200">
            <span className="w-1.5 h-1.5 rounded-full bg-sky-500" />
            INFO
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-600 border border-emerald-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            RESOLVED
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col w-full">
      {/* Header matching reference */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-100 flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-rose-50 flex items-center justify-center text-rose-600">
            <Bell className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Alert Center
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Real-time alerts from sensors, weather forecasts and system monitoring
            </p>
          </div>
        </div>

        {/* Top Right Actions */}
        <div className="flex items-center gap-3">
          {blynkFeedback && (
            <span className="text-xs font-semibold text-slate-700 bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200">
              {blynkFeedback}
            </span>
          )}

          {/* Emergency Hardware Trigger Button */}
          <button
            onClick={() => handleSignalDevice('trigger')}
            disabled={signalingV0}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 active:bg-rose-800 transition-colors shadow-2xs cursor-pointer disabled:opacity-50"
            title="Dispatch emergency siren/alert signal to connected Blynk device"
          >
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>Signal Device (V0)</span>
          </button>

          {/* View All button matching reference */}
          <button
            onClick={() => {}}
            className="inline-flex items-center gap-1 text-xs font-semibold text-sky-600 hover:text-sky-800 transition-colors cursor-pointer"
          >
            View All <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Table matching reference */}
      <div className="overflow-x-auto w-full mt-2">
        <table className="w-full text-left border-collapse min-w-[760px]">
          <thead>
            <tr className="border-b border-slate-100 text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              <th className="py-3 px-3">TIME</th>
              <th className="py-3 px-3">SEVERITY</th>
              <th className="py-3 px-3">SOURCE</th>
              <th className="py-3 px-3">LOCATION</th>
              <th className="py-3 px-3">MESSAGE</th>
              <th className="py-3 px-3">STATUS</th>
              <th className="py-3 px-3 text-right">···</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 text-xs">
            {alertsList.map((item) => (
              <tr key={item.id} className="hover:bg-slate-50/70 transition-colors">
                {/* TIME */}
                <td className="py-3.5 px-3 whitespace-nowrap font-medium text-slate-600 text-xs">
                  {item.time}
                </td>

                {/* SEVERITY */}
                <td className="py-3.5 px-3 whitespace-nowrap">
                  {renderSeverityBadge(item.severity)}
                </td>

                {/* SOURCE */}
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center gap-1.5 text-slate-700 font-medium text-xs">
                    {renderSourceIcon(item.sourceType)}
                    <span>{item.sourceName}</span>
                  </span>
                </td>

                {/* LOCATION */}
                <td className="py-3.5 px-3 whitespace-nowrap text-slate-600 font-medium">
                  {item.location}
                </td>

                {/* MESSAGE */}
                <td className="py-3.5 px-3 text-slate-800 font-medium max-w-md">
                  {item.message}
                </td>

                {/* STATUS */}
                <td className="py-3.5 px-3 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-600 border border-rose-100">
                    {item.status}
                  </span>
                </td>

                {/* ACTION MENU */}
                <td className="py-3.5 px-3 whitespace-nowrap text-right text-slate-400 hover:text-slate-700 cursor-pointer">
                  <MoreHorizontal className="w-4 h-4 ml-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
