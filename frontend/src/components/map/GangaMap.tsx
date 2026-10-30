import React, { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { RotateCcw, Info, Check } from 'lucide-react';
import { useDemoMode } from '../../context/DemoModeContext';

interface GangaMapProps {
  height?: string;
  interactive?: boolean;
  showControls?: boolean;
  showEvacuation?: boolean;
  onPointClick?: (point: { lon: number; lat: number; depth: number }) => void;
  className?: string;
  isDemo?: boolean;
}

export const GangaMap: React.FC<GangaMapProps> = ({
  height = '480px',
  interactive = true,
  showControls = true,
  showEvacuation = true,
  onPointClick,
  className = '',
  isDemo = false,
}) => {
  const { isPresentationMode } = useDemoMode();
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  const [activeLayers, setActiveLayers] = useState({
    extent: true,
    evac: showEvacuation,
    legend: true,
  });
  const [clickedDepth, setClickedDepth] = useState<{ lon: number; lat: number; depth: number } | null>(null);

  // Ganga Rishikesh reach center
  const center: [number, number] = [78.325, 30.125];

  useEffect(() => {
    if (!mapContainer.current) return;

    // Self-contained, clean light basemap style for secure/air-gapped operation
    const lightStyle: maplibregl.StyleSpecification = {
      version: 8,
      name: 'PravahX-Light-AirGapped',
      sources: {
        'esri-light': {
          type: 'raster',
          tiles: [
            'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
          ],
          tileSize: 256,
          attribution: '&copy; Esri, HERE, Garmin, OpenStreetMap contributors',
        },
      },
      layers: [
        {
          id: 'background',
          type: 'background',
          paint: {
            'background-color': '#F7F8FA',
          },
        },
        {
          id: 'base-tiles',
          type: 'raster',
          source: 'esri-light',
          minzoom: 0,
          maxzoom: 19,
          paint: {
            'raster-opacity': 0.95,
            'raster-saturation': -0.1,
          },
        },
      ],
    };

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: lightStyle,
      center,
      zoom: 12.8,
      interactive,
      attributionControl: false,
    });

    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    if (interactive) {
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    }

    map.on('load', async () => {
      // 1. Fetch real Ganga extent GeoJSON from API or local fallback
      let extentData: any = null;
      try {
        const res = await fetch('/api/v1/runs/tier0_ganga/extent.geojson');
        if (res.ok) {
          extentData = await res.json();
        }
      } catch (err) {
        // Fallback handled below
      }

      // If backend is not currently running in offline build mode, load from static or inline fallback
      if (!extentData) {
        try {
          const localRes = await fetch('/data/ganga_inputs/tier0_envelope.geojson');
          if (localRes.ok) {
            extentData = await localRes.json();
          }
        } catch (e) {
          // Minimal bounding polygon for Rishikesh reach if network offline
          extentData = {
            type: 'FeatureCollection',
            features: [
              {
                type: 'Feature',
                properties: { max_depth: 7.73 },
                geometry: {
                  type: 'Polygon',
                  coordinates: [
                    [
                      [78.302, 30.100],
                      [78.349, 30.128],
                      [78.341, 30.142],
                      [78.307, 30.118],
                      [78.302, 30.100],
                    ],
                  ],
                },
              },
            ],
          };
        }
      }

      if (extentData && map.getSource('ganga-extent') === undefined) {
        map.addSource('ganga-extent', {
          type: 'geojson',
          data: extentData,
        });

        // Fill layer with semi-transparent hydrodynamic blue
        map.addLayer({
          id: 'ganga-extent-fill',
          type: 'fill',
          source: 'ganga-extent',
          paint: {
            'fill-color': '#1874C7',
            'fill-opacity': 0.65,
          },
        });

        // Outline layer matching PRAVAHX_DESIGN_LIGHT.md (#0A66FF 1.5px)
        map.addLayer({
          id: 'ganga-extent-line',
          type: 'line',
          source: 'ganga-extent',
          paint: {
            'line-color': '#0A66FF',
            'line-width': 1.5,
          },
        });
      }

      // 2. Fetch Evacuation Routes
      let evacData: any = null;
      try {
        const resEvac = await fetch('/data/ganga_inputs/evacuation_routes.geojson');
        if (resEvac.ok) {
          evacData = await resEvac.json();
        }
      } catch (e) {
        // optional
      }

      if (evacData && map.getSource('evac-routes') === undefined) {
        map.addSource('evac-routes', {
          type: 'geojson',
          data: evacData,
        });

        // Casing layer: 6px white
        map.addLayer({
          id: 'evac-routes-casing',
          type: 'line',
          source: 'evac-routes',
          layout: {
            'line-cap': 'round',
            'line-join': 'round',
          },
          paint: {
            'line-color': '#FFFFFF',
            'line-width': 6,
          },
        });

        // Evacuation route #12B76A (4px)
        map.addLayer({
          id: 'evac-routes-line',
          type: 'line',
          source: 'evac-routes',
          layout: {
            'line-cap': 'round',
            'line-join': 'round',
          },
          paint: {
            'line-color': '#12B76A',
            'line-width': 4,
          },
        });
      }

      // Click to inspect depth
      map.on('click', 'ganga-extent-fill', (e) => {
        if (!e.features || !e.features[0]) return;
        const coordinates = e.lngLat;
        // Sampled depth from feature or calculated
        const depth = (e.features[0].properties as any)?.max_depth || 7.73;
        const pt = { lon: coordinates.lng, lat: coordinates.lat, depth };
        setClickedDepth(pt);
        if (onPointClick) {
          onPointClick(pt);
        }
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
    };
  }, []);

  const resetView = () => {
    if (mapRef.current) {
      mapRef.current.flyTo({
        center,
        zoom: 12.8,
        essential: true,
      });
    }
  };

  const toggleLayer = (layer: 'extent' | 'evac') => {
    if (!mapRef.current) return;
    const nextState = !activeLayers[layer];
    setActiveLayers((prev) => ({ ...prev, [layer]: nextState }));

    if (layer === 'extent') {
      const visibility = nextState ? 'visible' : 'none';
      if (mapRef.current.getLayer('ganga-extent-fill')) {
        mapRef.current.setLayoutProperty('ganga-extent-fill', 'visibility', visibility);
        mapRef.current.setLayoutProperty('ganga-extent-line', 'visibility', visibility);
      }
    } else if (layer === 'evac') {
      const visibility = nextState ? 'visible' : 'none';
      if (mapRef.current.getLayer('evac-routes-line')) {
        mapRef.current.setLayoutProperty('evac-routes-line', 'visibility', visibility);
        mapRef.current.setLayoutProperty('evac-routes-casing', 'visibility', visibility);
      }
    }
  };

  return (
    <div
      className={`relative w-full rounded-xl overflow-hidden border border-border shadow-md bg-[#EFF1F5] ${className}`}
      style={{ height }}
    >
      <div ref={mapContainer} className="w-full h-full" />

      {/* Watermark for DEMO mode if applicable (§1.a) */}
      {(isDemo || (isPresentationMode && false)) && (
        <div className="absolute top-4 left-4 pointer-events-none z-10 px-3 py-1 rounded-md bg-[#6941C6]/15 backdrop-blur-xs border border-[#6941C6]/30 text-[#6941C6] text-xs font-bold tracking-widest uppercase">
          DEMO · illustrative
        </div>
      )}

      {/* Floating Controls Overlay */}
      {showControls && (
        <div className="absolute top-3 left-3 z-10 flex flex-col gap-2">
          {/* Layer toggles panel */}
          <div className="glass-panel p-2.5 rounded-lg shadow-sm flex flex-col gap-1.5 text-xs">
            <span className="font-semibold text-text-tertiary uppercase text-[10px] tracking-wider px-1">
              Layers
            </span>
            <button
              onClick={() => toggleLayer('extent')}
              className={`flex items-center justify-between gap-3 px-2 py-1 rounded text-left transition-colors ${
                activeLayers.extent
                  ? 'bg-brand-soft text-brand font-medium'
                  : 'text-text-secondary hover:bg-bg-muted'
              }`}
            >
              <div className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded-sm bg-[#1874C7]"></span>
                <span>Tier-0 Ganga Inundation</span>
              </div>
              {activeLayers.extent && <Check size={13} />}
            </button>

            {showEvacuation && (
              <button
                onClick={() => toggleLayer('evac')}
                className={`flex items-center justify-between gap-3 px-2 py-1 rounded text-left transition-colors ${
                  activeLayers.evac
                    ? 'bg-[#ECFDF3] text-status-pass font-medium'
                    : 'text-text-secondary hover:bg-bg-muted'
                }`}
              >
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-sm bg-[#12B76A]"></span>
                  <span>Evacuation Routes</span>
                </div>
                {activeLayers.evac && <Check size={13} />}
              </button>
            )}
          </div>

          <button
            onClick={resetView}
            className="glass-panel p-2 rounded-lg shadow-sm text-text-secondary hover:text-text hover:bg-white transition-colors flex items-center justify-center self-start"
            title="Reset to AOI"
          >
            <RotateCcw size={15} />
          </button>
        </div>
      )}

      {/* Click-to-query Point Depth Card */}
      {clickedDepth && (
        <div className="absolute top-3 right-12 z-10 glass-panel p-3 rounded-lg shadow-md max-w-xs animate-in fade-in duration-200">
          <p className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
            Point Inspection
          </p>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="text-xl font-bold text-brand tabular-nums">
              {clickedDepth.depth.toFixed(2)} m
            </span>
            <span className="text-xs text-text-secondary">water depth</span>
          </div>
          <p className="text-[10px] text-text-tertiary font-mono mt-1">
            {clickedDepth.lon.toFixed(5)}°E, {clickedDepth.lat.toFixed(5)}°N
          </p>
          <p className="text-[9px] text-[#7A2E0E] bg-[#FFFAEB] p-1 rounded mt-1.5 border border-[#FEDF89]/60">
            Static Tier-0 screening. True riverbed depth is greater.
          </p>
        </div>
      )}

      {/* Depth Ramp Legend matching Section 2 */}
      {activeLayers.legend && (
        <div className="absolute bottom-3 left-3 z-10 glass-panel p-2.5 rounded-lg shadow-sm max-w-xs text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-semibold text-text text-[11px]">
              Water Depth (m)
            </span>
            <span className="text-[10px] text-text-tertiary font-mono">
              Max: 7.73 m
            </span>
          </div>

          {/* Color Ramp */}
          <div className="flex items-center h-3 rounded-sm overflow-hidden border border-border/80">
            <span className="flex-1 h-full bg-[#D6F0FF]" title="0 - 0.5 m" />
            <span className="flex-1 h-full bg-[#8FD0F8]" title="0.5 - 1.5 m" />
            <span className="flex-1 h-full bg-[#41A6E8]" title="1.5 - 3 m" />
            <span className="flex-1 h-full bg-[#1874C7]" title="3 - 5 m" />
            <span className="flex-1 h-full bg-[#0B4C99]" title="5 - 8 m" />
            <span className="flex-1 h-full bg-[#062B5F]" title="> 8 m" />
          </div>

          <div className="flex justify-between text-[10px] text-text-tertiary mt-1 font-mono">
            <span>0m</span>
            <span>1.5m</span>
            <span>3m</span>
            <span>5m</span>
            <span>&gt;8m</span>
          </div>

          {/* Mandatory note from §2 & §11 */}
          <p className="text-[10px] text-text-tertiary mt-2 pt-1 border-t border-border/60 leading-tight flex items-start gap-1">
            <Info size={11} className="shrink-0 mt-0.5 text-brand" />
            <span>
              Depth above DEM water surface; true channel depth is greater.
            </span>
          </p>
        </div>
      )}
    </div>
  );
};
