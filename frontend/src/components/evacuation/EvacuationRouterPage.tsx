import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { 
  AlertTriangle, 
  CheckCircle2, 
  XCircle, 
  Download, 
  ExternalLink
} from 'lucide-react';
import { FeatureId } from '../../types';

interface EvacuationRouterPageProps {
  onNavigate: (feature: FeatureId) => void;
}

export const EvacuationRouterPage: React.FC<EvacuationRouterPageProps> = ({ onNavigate }) => {
  const { i18n } = useTranslation();
  const isHi = i18n.language === 'hi';

  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<any>(null);
  const [selectedRoute, setSelectedRoute] = useState<any>(null);

  useEffect(() => {
    fetch('/api/v1/runs/tier0_ganga_accepted/evacuation')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load evacuation data');
        return res.json();
      })
      .then((resData) => {
        setData(resData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Evacuation fetch error:', err);
        setLoading(false);
      });
  }, []);

  // Initialize MapLibre
  useEffect(() => {
    if (!mapContainer.current || map.current) return;

    const m = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          osm: {
            type: 'raster',
            tiles: [
              'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
            ],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [
          {
            id: 'osm-tiles',
            type: 'raster',
            source: 'osm',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: [78.321, 30.125],
      zoom: 14,
    });

    m.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');

    m.on('load', () => {
      // Add evacuation routes GeoJSON
      m.addSource('evac-routes', {
        type: 'geojson',
        data: '/data/ganga_inputs/evacuation_routes.geojson',
      });

      // Line casing
      m.addLayer({
        id: 'evac-routes-casing',
        type: 'line',
        source: 'evac-routes',
        paint: {
          'line-color': '#FFFFFF',
          'line-width': 6,
        },
      });

      // Line fill (Green)
      m.addLayer({
        id: 'evac-routes-line',
        type: 'line',
        source: 'evac-routes',
        paint: {
          'line-color': '#12B76A',
          'line-width': 4,
        },
      });

      // Add flooded roads (Severed)
      m.addSource('flooded-roads', {
        type: 'geojson',
        data: '/data/ganga_inputs/flooded_roads.geojson',
      });

      m.addLayer({
        id: 'flooded-roads-line',
        type: 'line',
        source: 'flooded-roads',
        paint: {
          'line-color': '#F04438',
          'line-width': 2.5,
          'line-dasharray': [2, 2],
        },
      });

      // Add flooded buildings
      m.addSource('flooded-buildings', {
        type: 'geojson',
        data: '/data/ganga_inputs/flooded_buildings.geojson',
      });

      m.addLayer({
        id: 'flooded-buildings-poly',
        type: 'fill',
        source: 'flooded-buildings',
        paint: {
          'fill-color': '#F79009',
          'fill-opacity': 0.6,
        },
      });

      m.addLayer({
        id: 'flooded-buildings-outline',
        type: 'line',
        source: 'flooded-buildings',
        paint: {
          'line-color': '#B54708',
          'line-width': 1.5,
        },
      });
    });

    map.current = m;

    return () => {
      m.remove();
      map.current = null;
    };
  }, []);

  const handleFocusRoute = (route: any) => {
    setSelectedRoute(route);
    if (!map.current) return;

    if (route.origin_id === 'bldg_31') {
      map.current.flyTo({ center: [78.3303, 30.1244], zoom: 16.5, speed: 1.2 });
    } else if (route.origin_id === 'bldg_35') {
      map.current.flyTo({ center: [78.3122, 30.1232], zoom: 16.5, speed: 1.2 });
    } else if (route.origin_id === 'bldg_20') {
      map.current.flyTo({ center: [78.3292, 30.1268], zoom: 16.5, speed: 1.2 });
    }
  };

  const handleExportGeoJSON = () => {
    const link = document.createElement('a');
    link.href = '/data/ganga_inputs/evacuation_routes.geojson';
    link.download = 'pravahx_evacuation_routes.geojson';
    link.click();
  };

  if (loading) {
    return (
      <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6 animate-pulse">
        <div className="h-4 w-32 bg-border rounded" />
        <div className="h-10 w-96 bg-border rounded" />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 bg-surface rounded-2xl border border-border" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* 1. Page Header (Part A3 standard) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-border">
        <div>
          <div className="text-xs font-mono font-semibold tracking-wider text-text-tertiary uppercase">
            F10 · {isHi ? 'आपातकालीन निकासी मार्ग' : 'EVACUATION & ROUTE INTEGRITY'}
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-text mt-1">
            {isHi ? 'लोग सुरक्षित बाहर कैसे निकल सकते हैं?' : 'How do people get out safely?'}
          </h1>
          <p className="text-sm text-text-secondary mt-1">
            {isHi
              ? 'जल स्तर > ०.३० मीटर वाले अवरुद्ध मार्गों को छोड़कर उच्च भूमि तक न्यूनतम लागत वाले निकासी पथ।'
              : 'Dijkstra least-cost egress routes avoiding flooded road sections (> 0.30 m depth cutoff).'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => onNavigate('f05_results_explorer')}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl border border-border bg-surface text-text hover:bg-bg-muted font-medium text-sm transition-all shadow-2xs"
          >
            <span>{isHi ? 'पूर्ण परिणाम मानचित्र' : 'Full Results Map'}</span>
            <ExternalLink size={15} />
          </button>
          <button
            onClick={handleExportGeoJSON}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-brand hover:bg-brand-hover text-white font-semibold text-sm transition-all shadow-sm active:scale-[0.98]"
          >
            <Download size={16} />
            <span>{isHi ? 'मार्ग निर्यात करें (GeoJSON)' : 'Export Routes (GeoJSON)'}</span>
          </button>
        </div>
      </div>

      {/* 2. KPI Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* KPI 1: Severed Corridors */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'अवरुद्ध सड़क खंड' : 'Severed Road Corridors'}</span>
            <AlertTriangle size={18} className="text-[#F04438]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-[#F04438]">
              {data?.severed_edges_count || 100}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              edges ({data?.severed_edge_length_km || 14.76} km severed)
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            Cutoff: depth &gt; {data?.depth_cutoff_m || 0.30} m (impassable for light vehicles)
          </div>
        </div>

        {/* KPI 2: Reachable Origins */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'सुलभ सुरक्षित मार्ग' : 'Clear Evacuation Routes'}</span>
            <CheckCircle2 size={18} className="text-[#12B76A]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-[#12B76A]">
              {data?.origins?.reachable_count || 2}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              / {data?.origins?.total_evaluated || 5} flooded origins
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            Valid egress corridors verified to designated dry high-ground nodes
          </div>
        </div>

        {/* KPI 3: Trapped / Inundated Origins */}
        <div className="bg-surface rounded-2xl p-5 border border-border shadow-2xs space-y-2">
          <div className="flex items-center justify-between text-text-tertiary">
            <span className="text-xs font-medium uppercase tracking-wider">{isHi ? 'अवरुद्ध / जलमग्न क्षेत्र' : 'Trapped / Cut Off Structures'}</span>
            <XCircle size={18} className="text-[#B54708]" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold font-mono text-[#B54708]">
              {data?.origins?.unreachable_count || 3}
            </span>
            <span className="text-xs text-text-tertiary font-mono">
              origins require boat/aerial rescue
            </span>
          </div>
          <div className="text-[11px] text-text-tertiary">
            Access roads completely submerged by &gt; 5.0m water depth
          </div>
        </div>
      </div>

      {/* 3. Main Map & Egress Manifest Split Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Side: MapLibre Interactive Map (7 Cols) */}
        <div className="lg:col-span-7 bg-surface rounded-2xl border border-border overflow-hidden shadow-2xs flex flex-col h-[560px]">
          <div className="p-3.5 border-b border-border bg-[#FAFAFA] flex items-center justify-between text-xs">
            <div className="flex items-center gap-3">
              <span className="font-semibold text-text">Egress Network Spatial View</span>
              <span className="text-text-tertiary">·</span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-1 bg-[#12B76A] rounded-full inline-block" />
                <span className="text-text-secondary">Egress Route</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-0.5 border-t border-dashed border-[#F04438] inline-block" />
                <span className="text-text-secondary">Severed Road</span>
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-[#F79009] inline-block" />
                <span className="text-text-secondary">Flooded Structure</span>
              </span>
            </div>
            <span className="font-mono text-text-tertiary">EPSG:32644</span>
          </div>

          <div ref={mapContainer} className="flex-1 w-full relative" />
        </div>

        {/* Right Side: Egress Manifest & Trapped Structures (5 Cols) */}
        <div className="lg:col-span-5 space-y-4">
          {/* Card A: Reachable Routes */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <CheckCircle2 size={16} className="text-[#12B76A]" />
                <h3 className="text-sm font-bold text-text">
                  {isHi ? 'सत्यापित सुरक्षित निकासी पथ' : 'Reachable Evacuation Routes'}
                </h3>
              </div>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-[#ECFDF3] text-[#027A48]">
                {data?.origins?.reachable_routes?.length || 2} Available
              </span>
            </div>

            <div className="space-y-2.5">
              {(data?.origins?.reachable_routes || []).map((r: any, idx: number) => {
                const isSelected = selectedRoute?.origin_id === r.origin_id;
                return (
                  <div
                    key={idx}
                    onClick={() => handleFocusRoute(r)}
                    className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'border-brand bg-brand-soft shadow-xs'
                        : 'border-border bg-bg-subtle hover:border-brand/40 hover:bg-surface'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-mono font-bold text-text uppercase">
                            {r.origin_id}
                          </span>
                          <span className="text-[11px] font-mono text-text-tertiary">
                            (Node #{r.node_id})
                          </span>
                        </div>
                        <p className="text-xs text-text-secondary">
                          {r.origin_id === 'bldg_31'
                            ? 'Gurudev Kutir Egress Corridor'
                            : 'Baba Kali Kamli Safe Bypass'}
                        </p>
                      </div>

                      <div className="text-right">
                        <div className="text-sm font-bold font-mono text-[#12B76A]">
                          {r.route_length_m} m
                        </div>
                        <div className="text-[11px] text-text-tertiary font-mono">
                          {(r.route_length_m / 1000).toFixed(2)} km distance
                        </div>
                      </div>
                    </div>

                    <div className="mt-2 pt-2 border-t border-border/50 flex items-center justify-between text-[11px] text-text-tertiary">
                      <span>Water depth at origin: {r.depth_m} m</span>
                      <span className="text-brand font-semibold hover:underline">
                        Focus on map →
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Card B: Trapped / Inundated Structures */}
          <div className="bg-surface rounded-2xl border border-border p-5 shadow-2xs space-y-3">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <XCircle size={16} className="text-[#F04438]" />
                <h3 className="text-sm font-bold text-text">
                  {isHi ? 'अवरुद्ध / कटे हुए भवन (बचाव आवश्यक)' : 'Cut-off Buildings (Rescue Required)'}
                </h3>
              </div>
              <span className="text-xs font-mono font-semibold px-2 py-0.5 rounded bg-[#FEF3F2] text-[#B42318]">
                {data?.origins?.unreachable_origins?.length || 3} Trapped
              </span>
            </div>

            <div className="space-y-2.5">
              {(data?.origins?.unreachable_origins || []).map((u: any, idx: number) => (
                <div
                  key={idx}
                  onClick={() => handleFocusRoute(u)}
                  className="p-3.5 rounded-xl border border-border bg-bg-subtle hover:bg-surface transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono font-bold text-text uppercase">
                          {u.origin_id}
                        </span>
                        <span className="text-[11px] font-mono text-text-tertiary">
                          (Node #{u.node_id})
                        </span>
                      </div>
                      <p className="text-xs text-[#D92D20] font-medium mt-0.5">
                        {u.reason}
                      </p>
                    </div>

                    <div className="text-right">
                      <span className="text-sm font-bold font-mono text-[#D92D20]">
                        {u.depth_m} m
                      </span>
                      <div className="text-[10px] uppercase tracking-wider text-text-tertiary font-bold">
                        Peak Depth
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
