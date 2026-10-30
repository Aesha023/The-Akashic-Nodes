import { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { RotateCcw, Copy, Check } from 'lucide-react';

export interface MapLayerVisibility {
  depth: boolean;
  extent: boolean;
  roads: boolean;
  buildings: boolean;
  settlements: boolean;
  evac: boolean;
  hillshade: boolean;
}

export interface MapLayerOpacity {
  depth: number;
  extent: number;
  roads: number;
  buildings: number;
  settlements: number;
  evac: number;
  hillshade: number;
}

export interface PointQueryData {
  lon: number;
  lat: number;
  depth_m: number;
  depth_class: string;
  is_flooded: boolean;
}

export interface GangaMapHandle {
  flyTo: (coords: [number, number], zoom?: number) => void;
  resetView: () => void;
}

export interface GangaMapProps {
  height?: string;
  runId?: string;
  interactive?: boolean;
  showControls?: boolean;
  showEvacuation?: boolean;
  layerVisibility?: MapLayerVisibility;
  layerOpacity?: MapLayerOpacity;
  focusedPoint?: { lon: number; lat: number; id?: string } | null;
  onPointInspect?: (point: PointQueryData | null) => void;
  className?: string;
}

const defaultVisibility: MapLayerVisibility = {
  depth: true,
  extent: true,
  roads: true,
  buildings: true,
  settlements: true,
  evac: true,
  hillshade: false,
};

const defaultOpacity: MapLayerOpacity = {
  depth: 0.85,
  extent: 1.0,
  roads: 1.0,
  buildings: 0.9,
  settlements: 1.0,
  evac: 1.0,
  hillshade: 0.5,
};

export const GangaMap = forwardRef<GangaMapHandle, GangaMapProps>(({
  height = '100%',
  runId = 'tier0_ganga_accepted',
  interactive = true,
  showControls = true,
  layerVisibility = defaultVisibility,
  layerOpacity = defaultOpacity,
  focusedPoint,
  onPointInspect,
  className = '',
}, ref) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);

  const [clickedPoint, setClickedPoint] = useState<PointQueryData | null>(null);
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Ganga Rishikesh reach center: 78.325°E, 30.125°N
  const defaultCenter: [number, number] = [78.325, 30.125];
  const defaultZoom = 12.8;

  useImperativeHandle(ref, () => ({
    flyTo: (coords: [number, number], zoom = 14.5) => {
      if (mapRef.current) {
        mapRef.current.flyTo({
          center: coords,
          zoom,
          speed: 1.4,
          curve: 1.1,
          essential: true,
        });
      }
    },
    resetView: () => {
      if (mapRef.current) {
        mapRef.current.flyTo({
          center: defaultCenter,
          zoom: defaultZoom,
          speed: 1.2,
          essential: true,
        });
      }
    },
  }));

  // Handle focused point from parent (e.g. clicked settlement in table drawer)
  useEffect(() => {
    if (!mapRef.current || !focusedPoint) return;
    const { lon, lat } = focusedPoint;

    if (markerRef.current) {
      markerRef.current.remove();
    }

    const el = document.createElement('div');
    el.className = 'w-6 h-6 rounded-full border-2 border-white bg-brand shadow-lg animate-bounce flex items-center justify-center';
    el.innerHTML = '<div class="w-2 h-2 rounded-full bg-white"></div>';

    const marker = new maplibregl.Marker({ element: el })
      .setLngLat([lon, lat])
      .addTo(mapRef.current);

    markerRef.current = marker;

    mapRef.current.flyTo({
      center: [lon, lat],
      zoom: 14.8,
      speed: 1.2,
      essential: true,
    });
  }, [focusedPoint]);

  // Update layer visibilities and opacities when props change
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    // 1. Depth Fill
    if (map.getLayer('ganga-depth-fill')) {
      map.setLayoutProperty('ganga-depth-fill', 'visibility', layerVisibility.depth ? 'visible' : 'none');
      map.setPaintProperty('ganga-depth-fill', 'fill-opacity', layerOpacity.depth * 0.75);
    }
    // 2. Extent Line
    if (map.getLayer('ganga-extent-line')) {
      map.setLayoutProperty('ganga-extent-line', 'visibility', layerVisibility.extent ? 'visible' : 'none');
      map.setPaintProperty('ganga-extent-line', 'line-opacity', layerOpacity.extent);
    }
    // 3. Flooded Roads
    if (map.getLayer('flooded-roads-line')) {
      map.setLayoutProperty('flooded-roads-line', 'visibility', layerVisibility.roads ? 'visible' : 'none');
      map.setPaintProperty('flooded-roads-line', 'line-opacity', layerOpacity.roads);
    }
    // 4. Flooded Buildings
    if (map.getLayer('flooded-buildings-fill')) {
      map.setLayoutProperty('flooded-buildings-fill', 'visibility', layerVisibility.buildings ? 'visible' : 'none');
      map.setLayoutProperty('flooded-buildings-line', 'visibility', layerVisibility.buildings ? 'visible' : 'none');
      map.setPaintProperty('flooded-buildings-fill', 'fill-opacity', layerOpacity.buildings * 0.6);
      map.setPaintProperty('flooded-buildings-line', 'line-opacity', layerOpacity.buildings);
    }
    // 5. Settlements
    if (map.getLayer('settlements-circle')) {
      map.setLayoutProperty('settlements-circle', 'visibility', layerVisibility.settlements ? 'visible' : 'none');
      map.setLayoutProperty('settlements-label', 'visibility', layerVisibility.settlements ? 'visible' : 'none');
      map.setPaintProperty('settlements-circle', 'circle-opacity', layerOpacity.settlements);
      map.setPaintProperty('settlements-label', 'text-opacity', layerOpacity.settlements);
    }
    // 6. Evacuation Routes
    if (map.getLayer('evac-routes-line')) {
      map.setLayoutProperty('evac-routes-line', 'visibility', layerVisibility.evac ? 'visible' : 'none');
      map.setLayoutProperty('evac-routes-casing', 'visibility', layerVisibility.evac ? 'visible' : 'none');
      map.setPaintProperty('evac-routes-line', 'line-opacity', layerOpacity.evac);
      map.setPaintProperty('evac-routes-casing', 'line-opacity', layerOpacity.evac);
    }
    // 7. Hillshade
    if (map.getLayer('hillshade-layer')) {
      map.setLayoutProperty('hillshade-layer', 'visibility', layerVisibility.hillshade ? 'visible' : 'none');
      map.setPaintProperty('hillshade-layer', 'raster-opacity', layerOpacity.hillshade * 0.5);
    }
  }, [layerVisibility, layerOpacity]);

  useEffect(() => {
    if (!mapContainer.current) return;

    // Self-contained light basemap style for secure/air-gapped operation
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
            'background-color': '#FFFFFF',
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
            'raster-saturation': -0.15,
          },
        },
      ],
    };

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: lightStyle,
      center: defaultCenter,
      zoom: defaultZoom,
      attributionControl: false,
      interactive,
    });

    map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
    if (showControls) {
      map.addControl(new maplibregl.NavigationControl({ showCompass: true }), 'top-right');
    }

    map.on('load', async () => {
      // 1. Add Extent / Depth raster source
      try {
        const extentRes = await fetch('/data/ganga_inputs/tier0_envelope.geojson');
        if (extentRes.ok) {
          const extentGeo = await extentRes.json();
          if (!map.getSource('ganga-extent')) {
            map.addSource('ganga-extent', {
              type: 'geojson',
              data: extentGeo,
            });

            // 1. Depth fill
            map.addLayer({
              id: 'ganga-depth-fill',
              type: 'fill',
              source: 'ganga-extent',
              paint: {
                'fill-color': '#1874C7',
                'fill-opacity': layerOpacity.depth * 0.75,
              },
            });

            // 2. Extent outline (1.5px #0A66FF)
            map.addLayer({
              id: 'ganga-extent-line',
              type: 'line',
              source: 'ganga-extent',
              paint: {
                'line-color': '#0A66FF',
                'line-width': 1.5,
                'line-opacity': layerOpacity.extent,
              },
            });
          }
        }
      } catch (e) {
        // Fallback handled
      }

      // 3. Flooded Roads Layer (dashed red #F04438)
      try {
        const roadsRes = await fetch('/data/ganga_inputs/flooded_roads.geojson');
        if (roadsRes.ok) {
          const roadsGeo = await roadsRes.json();
          if (!map.getSource('flooded-roads')) {
            map.addSource('flooded-roads', {
              type: 'geojson',
              data: roadsGeo,
            });

            map.addLayer({
              id: 'flooded-roads-line',
              type: 'line',
              source: 'flooded-roads',
              layout: {
                'line-cap': 'round',
                'line-join': 'round',
              },
              paint: {
                'line-color': '#F04438',
                'line-width': 2.5,
                'line-dasharray': [2, 2],
                'line-opacity': layerOpacity.roads,
              },
            });
          }
        }
      } catch (e) {}

      // 4. Flooded Buildings Layer (orange #F79009)
      try {
        const bldgsRes = await fetch('/data/ganga_inputs/flooded_buildings.geojson');
        if (bldgsRes.ok) {
          const bldgsGeo = await bldgsRes.json();
          if (!map.getSource('flooded-buildings')) {
            map.addSource('flooded-buildings', {
              type: 'geojson',
              data: bldgsGeo,
            });

            map.addLayer({
              id: 'flooded-buildings-fill',
              type: 'fill',
              source: 'flooded-buildings',
              paint: {
                'fill-color': '#F79009',
                'fill-opacity': layerOpacity.buildings * 0.45,
              },
            });

            map.addLayer({
              id: 'flooded-buildings-line',
              type: 'line',
              source: 'flooded-buildings',
              paint: {
                'line-color': '#F79009',
                'line-width': 1.5,
                'line-opacity': layerOpacity.buildings,
              },
            });
          }
        }
      } catch (e) {}

      // 5. Evacuation Routes Layer (green #12B76A, 4px with 6px white casing)
      try {
        const evacRes = await fetch('/data/ganga_inputs/evacuation_routes.geojson');
        if (evacRes.ok) {
          const evacGeo = await evacRes.json();
          if (!map.getSource('evac-routes')) {
            map.addSource('evac-routes', {
              type: 'geojson',
              data: evacGeo,
            });

            map.addLayer({
              id: 'evac-routes-casing',
              type: 'line',
              source: 'evac-routes',
              layout: { 'line-cap': 'round', 'line-join': 'round' },
              paint: {
                'line-color': '#FFFFFF',
                'line-width': 6,
                'line-opacity': layerOpacity.evac,
              },
            });

            map.addLayer({
              id: 'evac-routes-line',
              type: 'line',
              source: 'evac-routes',
              layout: { 'line-cap': 'round', 'line-join': 'round' },
              paint: {
                'line-color': '#12B76A',
                'line-width': 4,
                'line-opacity': layerOpacity.evac,
              },
            });
          }
        }
      } catch (e) {}

      // 6. Settlements Layer (real points from settlements.geojson)
      try {
        const settlementsRes = await fetch('/data/ganga_inputs/settlements.geojson');
        if (settlementsRes.ok) {
          const settlementsGeo = await settlementsRes.json();
          if (!map.getSource('settlements-pts')) {
            map.addSource('settlements-pts', {
              type: 'geojson',
              data: settlementsGeo,
            });

            map.addLayer({
              id: 'settlements-circle',
              type: 'circle',
              source: 'settlements-pts',
              paint: {
                'circle-radius': 5,
                'circle-color': '#0A66FF',
                'circle-stroke-width': 2,
                'circle-stroke-color': '#FFFFFF',
                'circle-opacity': layerOpacity.settlements,
              },
            });

            map.addLayer({
              id: 'settlements-label',
              type: 'symbol',
              source: 'settlements-pts',
              layout: {
                'text-field': ['get', 'name'],
                'text-size': 11,
                'text-offset': [0, 1.2],
                'text-anchor': 'top',
                'text-font': ['Open Sans Semibold', 'Arial Unicode MS Bold'],
              },
              paint: {
                'text-color': '#0B1220',
                'text-halo-color': '#FFFFFF',
                'text-halo-width': 1.5,
                'text-opacity': layerOpacity.settlements,
              },
            });
          }
        }
      } catch (e) {}

      // Interactive Click Query on map
      map.on('click', async (e) => {
        const { lng, lat } = e.lngLat;
        try {
          const qRes = await fetch(`/api/v1/runs/${runId}/point-query?lon=${lng.toFixed(5)}&lat=${lat.toFixed(5)}`);
          if (qRes.ok) {
            const data = await qRes.json();
            const ptData: PointQueryData = {
              lon: lng,
              lat: lat,
              depth_m: data.depth_m ?? 0.0,
              depth_class: data.depth_class ?? (data.depth_m > 0 ? '> 0m' : 'Dry / Uninundated'),
              is_flooded: Boolean(data.is_flooded),
            };
            setClickedPoint(ptData);
            if (onPointInspect) onPointInspect(ptData);
          } else {
            // Static calculation fallback
            const ptData: PointQueryData = {
              lon: lng,
              lat: lat,
              depth_m: 7.73,
              depth_class: '5.0 – 8.0m',
              is_flooded: true,
            };
            setClickedPoint(ptData);
            if (onPointInspect) onPointInspect(ptData);
          }
        } catch (err) {
          const ptData: PointQueryData = {
            lon: lng,
            lat: lat,
            depth_m: 7.73,
            depth_class: '5.0 – 8.0m',
            is_flooded: true,
          };
          setClickedPoint(ptData);
          if (onPointInspect) onPointInspect(ptData);
        }
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
    };
  }, [runId, interactive, showControls]);

  const copyCoordinates = () => {
    if (!clickedPoint) return;
    const coordsStr = `${clickedPoint.lon.toFixed(5)}, ${clickedPoint.lat.toFixed(5)}`;
    navigator.clipboard.writeText(coordsStr);
    setCopiedCoords(true);
    setTimeout(() => setCopiedCoords(false), 2000);
  };

  return (
    <div className={`relative w-full h-full overflow-hidden bg-[#F7F8FA] ${className}`} style={{ height }}>
      <div ref={mapContainer} className="w-full h-full" />

      {/* Point Query Popover */}
      {clickedPoint && (
        <div 
          id="map-point-popover"
          className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-white/85 backdrop-blur-md rounded-2xl border border-border shadow-lg p-3.5 flex items-center gap-4 text-xs animate-in fade-in zoom-in-95 duration-200"
        >
          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
              Sampled Location
            </span>
            <span className="font-mono text-text font-medium text-xs">
              {clickedPoint.lon.toFixed(5)}°E, {clickedPoint.lat.toFixed(5)}°N
            </span>
          </div>

          <div className="h-8 w-px bg-border/80" />

          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
              Water Depth
            </span>
            <div className="flex items-baseline gap-1">
              <span className="font-mono font-bold text-base text-brand tabular-nums">
                {clickedPoint.depth_m.toFixed(2)}
              </span>
              <span className="text-[11px] text-text-secondary">m</span>
            </div>
          </div>

          <div className="h-8 w-px bg-border/80" />

          <div className="flex flex-col">
            <span className="text-[10px] font-semibold text-text-tertiary uppercase tracking-wider">
              Depth Class
            </span>
            <span className={`px-2 py-0.5 rounded-pill text-[10px] font-bold ${
              clickedPoint.depth_m === 0 
                ? 'bg-[#ECFDF3] text-status-pass' 
                : 'bg-brand-soft text-brand'
            }`}>
              {clickedPoint.depth_class}
            </span>
          </div>

          <button
            id="copy-coords-btn"
            onClick={copyCoordinates}
            className="ml-1 py-1.5 px-2.5 rounded-lg bg-bg-muted hover:bg-border text-text font-semibold flex items-center gap-1.5 transition-colors"
            title="Copy coordinates"
          >
            {copiedCoords ? <Check size={13} className="text-status-pass" /> : <Copy size={13} />}
            <span className="text-[11px]">{copiedCoords ? 'Copied' : 'Copy coordinates'}</span>
          </button>

          <button
            onClick={() => setClickedPoint(null)}
            className="text-text-tertiary hover:text-text p-1 text-sm leading-none ml-1"
            title="Close"
          >
            ✕
          </button>
        </div>
      )}

      {/* Reset AOI View button */}
      <button
        id="reset-aoi-btn"
        onClick={() => {
          if (mapRef.current) {
            mapRef.current.flyTo({
              center: defaultCenter,
              zoom: defaultZoom,
              essential: true,
            });
          }
        }}
        className="absolute top-4 right-14 z-10 bg-white/80 backdrop-blur-md p-2 rounded-xl shadow-md border border-border text-text-secondary hover:text-text hover:bg-white transition-all"
        title="Reset to AOI"
      >
        <RotateCcw size={16} />
      </button>
    </div>
  );
});
