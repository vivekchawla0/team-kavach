import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, ExternalLink } from 'lucide-react';
import { useDashboard } from '@/context/DashboardContext';
import { BARPETA_LOCATION } from '@/config/location';

export const SensorMap: React.FC = () => {
  const { sensors, summary, mapFilter, setMapFilter, setSelectedDetailSensor } = useDashboard();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersRef = useRef<{ [key: string]: L.Marker }>({});

  const filterBreakdown = summary?.sensors_breakdown || { normal: 8, warning: 3, critical: 1, offline: 1 };
  const totalSensors = summary?.total_sensors || 13;

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      zoomControl: true,
      attributionControl: false,
      scrollWheelZoom: false,
    }).setView([BARPETA_LOCATION.latitude, BARPETA_LOCATION.longitude], BARPETA_LOCATION.defaultZoom);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    // River Polylines for Barpeta
    L.polyline(BARPETA_LOCATION.riverPaths.brahmaputra, {
      color: '#0284c7',
      weight: 5.5,
      opacity: 0.85,
      smoothFactor: 1.2,
    }).addTo(map).bindTooltip('Brahmaputra River Corridor');

    L.polyline(BARPETA_LOCATION.riverPaths.chaulkhowa, {
      color: '#38bdf8',
      weight: 3.5,
      opacity: 0.85,
      smoothFactor: 1.2,
    }).addTo(map).bindTooltip('Chaulkhowa River (Barpeta)');

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Update Markers when sensors or filter changes
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    // Clear old markers
    Object.values(markersRef.current).forEach((m) => m.remove());
    markersRef.current = {};

    sensors.forEach((sensor) => {
      if (mapFilter !== 'ALL' && sensor.status.toUpperCase() !== mapFilter.toUpperCase()) {
        return;
      }

      const st = (sensor.status || 'NORMAL').toLowerCase();
      const isCritical = st === 'critical';

      const markerHtml = `
        <div class="w-5 h-5 rounded-full border-2 border-white shadow-md flex items-center justify-center cursor-pointer transition-transform hover:scale-125 ${
          st === 'normal'
            ? 'bg-emerald-500'
            : st === 'warning'
            ? 'bg-amber-500'
            : st === 'critical'
            ? 'bg-rose-500 ring-4 ring-rose-400/50 animate-pulse'
            : 'bg-slate-400'
        }">
        </div>
      `;

      const customIcon = L.divIcon({
        className: 'custom-sensor-icon',
        html: markerHtml,
        iconSize: [20, 20],
        iconAnchor: [10, 10],
      });

      const markerLat = sensor.latitude > 40
        ? BARPETA_LOCATION.latitude + (sensor.latitude - 50.5539) * 0.5
        : sensor.latitude;
      const markerLng = sensor.longitude < 20
        ? BARPETA_LOCATION.longitude + (sensor.longitude - 6.7633) * 0.5
        : sensor.longitude;

      const marker = L.marker([markerLat, markerLng], { icon: customIcon }).addTo(map);

      // Popup Content
      const popupDiv = document.createElement('div');
      popupDiv.className = 'p-1 font-sans min-w-[170px]';
      popupDiv.innerHTML = `
        <div class="flex items-center justify-between border-b border-slate-100 pb-1.5 mb-1.5">
          <strong class="text-xs text-slate-900 font-bold flex items-center gap-1.5">
            <span class="w-2 h-2 rounded-full ${
              st === 'normal' ? 'bg-emerald-500' : st === 'warning' ? 'bg-amber-500' : st === 'critical' ? 'bg-rose-500' : 'bg-slate-400'
            }"></span>
            ${sensor.name}
          </strong>
          <span class="text-[9px] font-bold uppercase px-1.5 py-0.5 rounded ${
            st === 'critical' ? 'bg-rose-100 text-rose-700' : st === 'warning' ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'
          }">${sensor.status}</span>
        </div>
        <div class="flex justify-between text-[11px] my-0.5 text-slate-500">
          <span>Water Level</span>
          <strong class="text-slate-900 font-bold">${sensor.current_water_level.toFixed(2)} m</strong>
        </div>
        <div class="flex justify-between text-[11px] my-0.5 text-slate-500">
          <span>Battery</span>
          <strong class="text-slate-900 font-bold">${Math.round(sensor.battery)}%</strong>
        </div>
        <button id="view-det-${sensor.sensor_id}" class="mt-2 text-right w-full text-[11px] font-bold text-sky-600 hover:text-sky-800 hover:underline">
          View Details →
        </button>
      `;

      // Attach click listener for "View Details"
      setTimeout(() => {
        const btn = document.getElementById(`view-det-${sensor.sensor_id}`);
        if (btn) {
          btn.onclick = () => setSelectedDetailSensor(sensor);
        }
      }, 100);

      marker.bindPopup(popupDiv);
      markersRef.current[sensor.sensor_id] = marker;

      // Auto-open critical sensor popup initially
      if (sensor.sensor_id === 'FW-007' || isCritical) {
        setTimeout(() => marker.openPopup(), 400);
      }
    });
  }, [sensors, mapFilter, setSelectedDetailSensor]);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2 text-slate-900">
          <MapPin className="w-4 h-4 text-sky-600" />
          <h3 className="font-bold text-sm">Sensor Network</h3>
        </div>
        <a href="#map" className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1">
          View Map <ExternalLink className="w-3 h-3" />
        </a>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1 text-xs">
        <button
          onClick={() => setMapFilter('ALL')}
          className={`px-3 py-1 rounded-full font-semibold transition-all shrink-0 ${
            mapFilter === 'ALL'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          All Sensors ({totalSensors})
        </button>
        <button
          onClick={() => setMapFilter('NORMAL')}
          className={`px-2.5 py-1 rounded-full font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
            mapFilter === 'NORMAL'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-emerald-500" /> Normal ({filterBreakdown.normal || 8})
        </button>
        <button
          onClick={() => setMapFilter('WARNING')}
          className={`px-2.5 py-1 rounded-full font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
            mapFilter === 'WARNING'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-amber-500" /> Warning ({filterBreakdown.warning || 3})
        </button>
        <button
          onClick={() => setMapFilter('CRITICAL')}
          className={`px-2.5 py-1 rounded-full font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
            mapFilter === 'CRITICAL'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-rose-500" /> Critical ({filterBreakdown.critical || 1})
        </button>
        <button
          onClick={() => setMapFilter('OFFLINE')}
          className={`px-2.5 py-1 rounded-full font-semibold transition-all flex items-center gap-1.5 shrink-0 ${
            mapFilter === 'OFFLINE'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
          }`}
        >
          <span className="w-2 h-2 rounded-full bg-slate-400" /> Offline ({filterBreakdown.offline || 1})
        </button>
      </div>

      {/* Map View */}
      <div className="relative h-64 rounded-xl overflow-hidden border border-slate-200">
        <div ref={mapContainerRef} className="w-full h-full" />

        {/* Legend */}
        <div className="absolute bottom-2.5 left-2.5 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-200/80 shadow-sm flex items-center gap-3 text-[11px] font-semibold text-slate-700 z-[400]">
          <span className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 bg-sky-600 rounded-full" /> River
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" /> Sensor
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 border border-dashed border-slate-400 rounded-sm" /> City Area
          </span>
        </div>
      </div>
    </div>
  );
};
