/**
 * Central Location & Hydrological Configuration for JAL SUCHAK
 * Region: Barpeta, Assam, India
 */

export interface MonitoringStation {
  id: string;
  name: string;
  river: string;
  lat: number;
  lng: number;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL';
  waterLevel: number;
  dangerLevel: number;
  warningLevel: number;
  riseRate: string;
  lastUpdated: string;
}

export const BARPETA_LOCATION = {
  name: "Barpeta, Assam",
  state: "Assam",
  district: "Barpeta",
  country: "India",
  latitude: 26.3216,
  longitude: 91.0061,
  defaultZoom: 11,
  elevationMeters: 35,
  riverBasin: "Lower Brahmaputra Floodplain Basin",
  
  // Principal rivers flowing through Barpeta district
  rivers: [
    { name: "Brahmaputra River", status: "High Discharge" },
    { name: "Beki River", status: "Active Inundation Watch" },
    { name: "Manas River", status: "Normal Inflow" },
    { name: "Chaulkhowa River", status: "Moderate Surcharge" },
    { name: "Pahumara River", status: "Steady Flow" }
  ],

  // Representative hydrological path coordinates for key river courses in Barpeta
  riverPaths: {
    brahmaputra: [
      [26.2950, 91.1800],
      [26.2620, 91.1100],
      [26.2350, 91.0300],
      [26.2150, 90.9500],
      [26.1950, 90.8700],
      [26.1750, 90.7800],
    ] as [number, number][],
    
    bekiManas: [
      [26.5400, 90.9350],
      [26.4700, 90.9480],
      [26.4050, 90.9620],
      [26.3450, 90.9700],
      [26.2800, 90.9450],
      [26.2150, 90.9300],
    ] as [number, number][],

    chaulkhowa: [
      [26.4200, 91.1100],
      [26.3650, 91.0600],
      [26.3216, 91.0061], // Barpeta town
      [26.2750, 90.9650],
      [26.2300, 90.9400],
    ] as [number, number][],
  },

  // Telemetry monitoring stations located across the Barpeta flood basin
  monitoringStations: [
    {
      id: "AS-BAR-01",
      name: "Chaulkhowa Bridge Station",
      river: "Chaulkhowa River (Barpeta Town)",
      lat: 26.3216,
      lng: 91.0061,
      status: "WARNING",
      waterLevel: 4.15,
      warningLevel: 3.80,
      dangerLevel: 4.50,
      riseRate: "+0.18 m/h",
      lastUpdated: "Just now"
    },
    {
      id: "AS-BAR-02",
      name: "Beki River Gauging Post",
      river: "Beki River Channel",
      lat: 26.3880,
      lng: 90.9620,
      status: "CRITICAL",
      waterLevel: 5.72,
      warningLevel: 4.80,
      dangerLevel: 5.40,
      riseRate: "+0.34 m/h",
      lastUpdated: "1 min ago"
    },
    {
      id: "AS-BAR-03",
      name: "Brahmaputra Baghbar Ghat",
      river: "Brahmaputra Main Stem",
      lat: 26.2120,
      lng: 90.8950,
      status: "WARNING",
      waterLevel: 13.45,
      warningLevel: 12.80,
      dangerLevel: 13.80,
      riseRate: "+0.12 m/h",
      lastUpdated: "2 mins ago"
    },
    {
      id: "AS-BAR-04",
      name: "Manas Confluence Hydro-Post",
      river: "Manas River",
      lat: 26.4650,
      lng: 90.9420,
      status: "NORMAL",
      waterLevel: 3.25,
      warningLevel: 4.20,
      dangerLevel: 4.90,
      riseRate: "+0.03 m/h",
      lastUpdated: "4 mins ago"
    },
    {
      id: "AS-BAR-05",
      name: "Sarthebari Basin Station",
      river: "Pahumara River Drainage",
      lat: 26.3580,
      lng: 91.1450,
      status: "NORMAL",
      waterLevel: 2.68,
      warningLevel: 3.60,
      dangerLevel: 4.20,
      riseRate: "-0.01 m/h",
      lastUpdated: "3 mins ago"
    },
    {
      id: "AS-BAR-06",
      name: "Chenga Embankment Monitor",
      river: "South Barpeta Channel",
      lat: 26.2680,
      lng: 91.0550,
      status: "NORMAL",
      waterLevel: 3.12,
      warningLevel: 4.00,
      dangerLevel: 4.60,
      riseRate: "+0.02 m/h",
      lastUpdated: "Just now"
    }
  ] as MonitoringStation[]
};
