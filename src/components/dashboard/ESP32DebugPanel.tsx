import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Cpu, Radio } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';

export const ESP32DebugPanel: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const { realTelemetry } = useDashboard();

  const isOnline = realTelemetry?.bluetooth_status === 'ONLINE';
  const lastPacketTime = realTelemetry?.timestamp
    ? new Date(realTelemetry.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '--:--:--';
  const secondsAgo = realTelemetry?.seconds_ago !== undefined && realTelemetry?.seconds_ago !== null
    ? `${Math.round(realTelemetry.seconds_ago)}s ago`
    : '--';

  return (
    <div className="w-full bg-slate-900 text-slate-200 rounded-xl border border-slate-800 shadow-md overflow-hidden transition-all text-xs">
      {/* Toggle Header */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 flex items-center justify-between hover:bg-slate-800/80 transition-colors cursor-pointer text-left"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2 font-mono">
          <Terminal className="w-3.5 h-3.5 text-sky-400" />
          <span className="font-bold tracking-wider uppercase text-[11px] text-slate-300">
            ESP32 LIVE DEBUG
          </span>
          <span className="text-slate-600">•</span>
          <span className="text-slate-400 text-[11px]">Hardware BLE Stream</span>
          <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
            isOnline ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${isOnline ? 'bg-emerald-400 animate-ping' : 'bg-rose-500'}`} />
            {isOnline ? 'CONNECTED' : 'DISCONNECTED'}
          </span>
        </div>

        <div className="flex items-center gap-3 text-slate-400">
          <span className="font-mono text-[11px] hidden sm:inline">
            Water Raw: <strong className="text-sky-400">{realTelemetry?.water_raw ?? '--'}</strong> | Rain Raw: <strong className="text-sky-400">{realTelemetry?.rain_raw ?? '--'}</strong>
          </span>
          {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
        </div>
      </button>

      {/* Collapsible Diagnostics Grid */}
      {isOpen && (
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/60 font-mono grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3 text-slate-300 animate-in fade-in slide-in-from-top-1">
          {/* Bluetooth */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Bluetooth</span>
            <span className={`font-bold text-[12px] mt-0.5 ${isOnline ? 'text-emerald-400' : 'text-rose-400'}`}>
              {isOnline ? 'CONNECTED' : 'OFFLINE'}
            </span>
          </div>

          {/* Device */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Device</span>
            <span className="font-bold text-[12px] text-slate-200 mt-0.5 truncate">
              {realTelemetry?.device_id || 'ESP32-FW-001'}
            </span>
          </div>

          {/* Last Packet */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Last Packet</span>
            <span className="font-bold text-[12px] text-slate-200 mt-0.5">
              {lastPacketTime}
            </span>
          </div>

          {/* Water Raw */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Water Raw</span>
            <span className="font-bold text-[12px] text-cyan-400 mt-0.5">
              {realTelemetry?.water_raw ?? '--'}
            </span>
          </div>

          {/* Water Level */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Water (Calibrated)</span>
            <span className="font-bold text-[12px] text-cyan-300 mt-0.5">
              {realTelemetry?.water_level_cm !== null && realTelemetry?.water_level_cm !== undefined
                ? `${realTelemetry.water_level_cm.toFixed(2)} cm`
                : '--'}
            </span>
          </div>

          {/* Rain Raw */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Rain Raw</span>
            <span className="font-bold text-[12px] text-sky-400 mt-0.5">
              {realTelemetry?.rain_raw ?? '--'}
            </span>
          </div>

          {/* Rain Intensity */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Rain Intensity</span>
            <span className="font-bold text-[12px] text-sky-300 mt-0.5">
              {realTelemetry?.rain_intensity !== null && realTelemetry?.rain_intensity !== undefined
                ? `${realTelemetry.rain_intensity.toFixed(2)}`
                : '--'}
            </span>
          </div>

          {/* Last Update */}
          <div className="flex flex-col bg-slate-900/90 p-2 rounded-lg border border-slate-800">
            <span className="text-[10px] text-slate-500 uppercase">Last Update</span>
            <span className="font-bold text-[12px] text-amber-400 mt-0.5">
              {secondsAgo}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
