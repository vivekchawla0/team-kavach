import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, X, ArrowRight, ExternalLink } from 'lucide-react';
import { BARPETA_LOCATION } from '@/config/location';
import { useDashboard } from '@/context/DashboardContext';

export const FloodMonitoringMap: React.FC = () => {
  const { summary, setSelectedDetailSensor, sensors } = useDashboard();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const [isStationModalOpen, setIsStationModalOpen] = useState<boolean>(true);

  const waterLevel = summary?.average_water_level_m ?? 3.17;
  const rainfall = summary?.current_rainfall_mm_hr ?? 65;
  const riskStatus = summary?.flood_risk_level || 'CRITICAL';

  // Primary prototype sensor coordinates at Barpeta, Assam
  const sensorLat = BARPETA_LOCATION.latitude;
  const sensorLng = BARPETA_LOCATION.longitude;

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return;

    const map = L.map(mapContainerRef.current, {
      zoomControl: false,
      attributionControl: false,
      scrollWheelZoom: false,
    }).setView([sensorLat, sensorLng], 12);

    // Clean light cartographic tiles (CartoDB Positron)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 18,
      subdomains: 'abcd',
    }).addTo(map);

    // Top-left zoom control
    L.control.zoom({ position: 'topleft' }).addTo(map);

    // Draw Inundation / Flood Risk Concentric Zones (matching reference)
    L.circle([sensorLat, sensorLng], {
      radius: 4500,
      color: '#38bdf8',
      fillColor: '#38bdf8',
      fillOpacity: 0.12,
      weight: 1,
      dashArray: '4, 4',
    }).addTo(map);

    L.circle([sensorLat, sensorLng], {
      radius: 2800,
      color: '#0ea5e9',
      fillColor: '#0ea5e9',
      fillOpacity: 0.18,
      weight: 1.5,
    }).addTo(map);

    L.circle([sensorLat, sensorLng], {
      radius: 1200,
      color: '#0284c7',
      fillColor: '#0284c7',
      fillOpacity: 0.25,
      weight: 1.5,
    }).addTo(map);

    // 1. Draw Brahmaputra River Corridor
    L.polyline(BARPETA_LOCATION.riverPaths.brahmaputra, {
      color: '#0284c7',
      weight: 8,
      opacity: 0.85,
      lineCap: 'round',
      lineJoin: 'round',
    }).addTo(map).bindTooltip('Brahmaputra River', { permanent: true, direction: 'center', className: 'river-label' });

    // 2. Surrounding town markers/labels
    const towns = [
      { name: 'Barpeta', coords: [26.3200, 91.0050] as [number, number] },
      { name: 'Kalagachia', coords: [26.2600, 90.8700] as [number, number] },
      { name: 'Bajali', coords: [26.3800, 91.1200] as [number, number] },
      { name: 'Pathshala', coords: [26.4950, 91.1750] as [number, number] },
    ];

    towns.forEach((town) => {
      const townIcon = L.divIcon({
        className: 'town-label-icon',
        html: `<div class="flex items-center gap-1 text-[11px] font-bold text-slate-700 bg-white/90 px-1.5 py-0.5 rounded shadow-2xs border border-slate-200/60 whitespace-nowrap">
          <span class="w-1.5 h-1.5 rounded-full bg-slate-500"></span>
          <span>${town.name}</span>
        </div>`,
        iconAnchor: [30, 10],
      });
      L.marker(town.coords, { icon: townIcon, interactive: false }).addTo(map);
    });

    // Single Real Sensor Marker with Radar Ripple
    const markerHtml = `
      <div class="relative flex items-center justify-center cursor-pointer group" id="single-station-marker">
        <!-- Radar Waves -->
        <div class="absolute w-16 h-16 rounded-full bg-sky-500/25 animate-radar-ripple pointer-events-none"></div>
        <div class="absolute w-10 h-10 rounded-full bg-cyan-400/35 animate-ping pointer-events-none"></div>
        
        <!-- Central Sensor Core Beacon -->
        <div class="relative z-10 w-8 h-8 rounded-full bg-gradient-to-tr from-sky-600 to-cyan-500 border-2 border-white shadow-lg flex items-center justify-center text-white transition-transform group-hover:scale-110">
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>

        <!-- + LIVE badge below marker -->
        <div class="absolute -bottom-4 left-1/2 -translate-x-1/2 bg-slate-900 text-white text-[9px] font-bold px-2 py-0.5 rounded-full shadow-md whitespace-nowrap tracking-wider flex items-center gap-1">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span>+ LIVE</span>
        </div>
      </div>
    `;

    const customIcon = L.divIcon({
      className: 'custom-sensor-icon',
      html: markerHtml,
      iconSize: [64, 64],
      iconAnchor: [32, 32],
    });

    const marker = L.marker([sensorLat, sensorLng], { icon: customIcon }).addTo(map);
    marker.on('click', () => {
      setIsStationModalOpen(true);
    });

    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, [sensorLat, sensorLng]);

  return (
    <div id="map-section" className="bg-white rounded-2xl border border-slate-200/90 p-5 sm:p-6 shadow-xs flex flex-col relative overflow-hidden h-full justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-sky-50 flex items-center justify-center text-sky-600">
            <MapPin className="w-5 h-5 text-sky-600" />
          </div>
          <div>
            <h3 className="font-bold text-base text-slate-900 leading-tight">
              Flood Monitoring Map
            </h3>
            <p className="text-xs text-slate-500 font-medium mt-0.5">
              Geospatial River Corridor & Inundation Basin • Barpeta, Assam
            </p>
          </div>
        </div>

        {/* View Full Map button */}
        <button
          onClick={() => {
            if (mapInstanceRef.current) {
              mapInstanceRef.current.setView([sensorLat, sensorLng], 12);
              setIsStationModalOpen(true);
            }
          }}
          className="inline-flex items-center gap-1 text-xs font-semibold text-sky-600 hover:text-sky-800 bg-sky-50 hover:bg-sky-100 px-3 py-1.5 rounded-xl border border-sky-100 transition-colors cursor-pointer"
        >
          View Full Map <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Map Canvas Container */}
      <div className="relative w-full flex-1 min-h-[360px] sm:min-h-[400px] rounded-xl overflow-hidden border border-slate-200 shadow-inner">
        <div ref={mapContainerRef} className="w-full h-full z-0" />

        {/* Floating Station Telemetry Card matching reference */}
        {isStationModalOpen && (
          <div className="absolute top-4 right-4 z-[400] w-64 sm:w-72 bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-2xl p-4 shadow-lg flex flex-col gap-2.5 transition-all animate-in fade-in slide-in-from-top-2">
            {/* Station Header */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-100">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-sky-600" />
                <h4 className="font-bold text-xs sm:text-sm text-slate-900 leading-tight">
                  Barpeta Station FW-001
                </h4>
              </div>
              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                  Online
                </span>
                <button
                  onClick={() => setIsStationModalOpen(false)}
                  className="text-slate-400 hover:text-slate-600 p-0.5 rounded transition-colors"
                  aria-label="Close"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Metrics List matching reference */}
            <div className="flex flex-col divide-y divide-slate-100 text-xs">
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500 font-medium">Water Level</span>
                <span className="font-extrabold text-slate-900">{waterLevel.toFixed(2)} m</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500 font-medium">Rainfall</span>
                <span className="font-extrabold text-slate-900">{Math.round(rainfall)} mm/hr</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500 font-medium">Battery</span>
                <span className="font-bold text-slate-800">82%</span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500 font-medium">Status</span>
                <span className="font-bold text-rose-600 flex items-center gap-1">
                  <span>◆</span> {riskStatus}
                </span>
              </div>
              <div className="flex items-center justify-between py-1.5">
                <span className="text-slate-500 font-medium">Last Updated</span>
                <span className="font-mono text-slate-700 text-[11px]">04:06 AM</span>
              </div>
            </div>

            {/* View Details Link */}
            <div className="pt-2 border-t border-slate-100">
              <button
                onClick={() => {
                  if (sensors && sensors.length > 0) {
                    setSelectedDetailSensor(sensors[0]);
                  }
                }}
                className="text-xs font-semibold text-sky-600 hover:text-sky-800 flex items-center gap-1 transition-colors cursor-pointer"
              >
                View Details <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          </div>
        )}

        {/* Map Legend at Bottom matching reference */}
        <div className="absolute bottom-3 left-3 z-[400] bg-white/95 backdrop-blur-md border border-slate-200/90 rounded-xl px-3 py-1.5 shadow-sm flex items-center gap-4 text-[11px] font-medium text-slate-700">
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-sky-500" />
            <span>Sensor (Online)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-1 rounded bg-[#0284c7]" />
            <span>River</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-xs bg-sky-200 border border-sky-400" />
            <span>Flood Risk Zone</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            <span>City / Town</span>
          </div>
        </div>
      </div>
    </div>
  );
};
