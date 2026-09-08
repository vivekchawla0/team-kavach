import React from 'react';
import { Search, Activity, MoreHorizontal } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { Sensor } from '@/types';

export const LiveSensorTable: React.FC = () => {
  const {
    sensors,
    tableSearch,
    setTableSearch,
    tableStatus,
    setTableStatus,
    selectSensorForTrends,
    setSelectedDetailSensor,
  } = useDashboard();

  const filteredSensors = sensors.filter((s) => {
    const search = tableSearch.toLowerCase();
    const matchesSearch =
      !search ||
      s.name.toLowerCase().includes(search) ||
      s.location_name.toLowerCase().includes(search) ||
      s.sensor_id.toLowerCase().includes(search);
    const matchesStatus = tableStatus === 'ALL' || s.status.toUpperCase() === tableStatus.toUpperCase();
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'CRITICAL':
        return 'bg-rose-500';
      case 'WARNING':
        return 'bg-amber-500';
      case 'OFFLINE':
        return 'bg-slate-400';
      default:
        return 'bg-emerald-500';
    }
  };

  const getBatteryFill = (battery: number) => {
    if (battery > 70) return 'bg-emerald-500';
    if (battery > 30) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      {/* Header with Search & Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2.5">
          <Activity className="w-4 h-4 text-sky-600" />
          <h3 className="font-bold text-sm text-slate-900">Live Sensor Data</h3>
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            Real-time updates
          </span>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Table Search */}
          <div className="relative flex items-center">
            <Search className="absolute left-2.5 w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search sensors..."
              value={tableSearch}
              onChange={(e) => setTableSearch(e.target.value)}
              className="text-xs bg-slate-50 border border-slate-200 pl-8 pr-3 py-1 rounded-lg text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500 w-36 sm:w-44"
            />
          </div>

          {/* Status Filter */}
          <select
            value={tableStatus}
            onChange={(e) => setTableStatus(e.target.value)}
            className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-800 focus:outline-none focus:ring-1 focus:ring-sky-500 cursor-pointer"
          >
            <option value="ALL">All Sensors</option>
            <option value="NORMAL">Normal</option>
            <option value="WARNING">Warning</option>
            <option value="CRITICAL">Critical</option>
            <option value="OFFLINE">Offline</option>
          </select>
        </div>
      </div>

      {/* Table Container */}
      <div className="overflow-x-auto max-h-[290px]">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 sticky top-0 z-10">
            <tr>
              <th className="py-2.5 px-3">#</th>
              <th className="py-2.5 px-3">Location</th>
              <th className="py-2.5 px-3">Water Level (m)</th>
              <th className="py-2.5 px-3">Status</th>
              <th className="py-2.5 px-3">Battery</th>
              <th className="py-2.5 px-3">Last Update</th>
              <th className="py-2.5 px-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filteredSensors.map((s, idx) => {
              const isCritical = s.status === 'CRITICAL';
              return (
                <tr
                  key={s.sensor_id}
                  onClick={() => setSelectedDetailSensor(s)}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                >
                  <td className="py-2.5 px-3 text-slate-400 font-medium">{idx + 1}</td>
                  <td className="py-2.5 px-3">
                    <strong className="font-bold text-slate-900 block">{s.name}</strong>
                    <span className="text-[10.5px] text-slate-400 block">{s.location_name}</span>
                  </td>
                  <td className={`py-2.5 px-3 ${isCritical ? 'text-rose-600 font-bold' : 'text-slate-800 font-semibold'}`}>
                    {s.current_water_level.toFixed(2)}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="inline-flex items-center gap-1.5 font-semibold text-[11px] text-slate-700">
                      <span className={`w-2 h-2 rounded-full ${getStatusColor(s.status)}`} />
                      {s.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-3">
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${getBatteryFill(s.battery)}`}
                          style={{ width: `${Math.round(s.battery)}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-slate-600 font-medium">{Math.round(s.battery)}%</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-3 text-slate-500 font-medium">14:32</td>
                  <td className="py-2.5 px-3 text-right">
                    <div className="flex items-center justify-end gap-1" onClick={(e) => e.stopPropagation()}>
                      <button
                        title="View Trends"
                        onClick={() => selectSensorForTrends(s.sensor_id)}
                        className="p-1 rounded text-slate-400 hover:text-sky-600 hover:bg-sky-50 transition-colors"
                      >
                        <Activity className="w-3.5 h-3.5" />
                      </button>
                      <button
                        title="Inspect Telemetry"
                        onClick={() => setSelectedDetailSensor(s)}
                        className="p-1 rounded text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors"
                      >
                        <MoreHorizontal className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
