"use client";
import { useEffect, useRef } from "react";
// maplibre-gl 4.x: the UMD build embeds its web worker as a blob, which works with the Next
// bundlers; 5.x/6.x load a separate worker module that Turbopack does not emit.
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Config, Sensor, Zone } from "@/lib/types";
import { RISK_COLORS } from "@/lib/format";

// No symbol layers (they need a remote glyph server): labels and flow arrows are DOM markers,
// so the map still works offline apart from the background tiles.
const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap contributors" } },
  layers: [{ id: "bg", type: "background", paint: { "background-color": "#1a1a19" } }, { id: "osm", type: "raster", source: "osm", paint: { "raster-opacity": 0.55, "raster-saturation": -0.6, "raster-brightness-max": 0.7 } }],
};

function zoneFeatures(zones: Zone[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: zones.map((z) => ({
      type: "Feature",
      properties: { id: z.id, name: z.name, risk: z.risk, color: RISK_COLORS[z.risk], density: z.state?.density ?? 0, stale: z.stale },
      geometry: { type: "Point", coordinates: [z.lon, z.lat] },
    })),
  };
}

function edgeFeatures(cfg: Config | undefined, zones: Zone[]): GeoJSON.FeatureCollection {
  if (!cfg) return { type: "FeatureCollection", features: [] };
  const byId = Object.fromEntries(zones.map((z) => [z.id, z]));
  return {
    type: "FeatureCollection",
    features: cfg.zone_graph.edges.filter((e) => byId[e.from] && byId[e.to]).map((e) => ({
      type: "Feature",
      properties: { id: e.id, name: e.name, stairs: e.has_stairs },
      geometry: { type: "LineString", coordinates: [[byId[e.from].lon, byId[e.from].lat], [byId[e.to].lon, byId[e.to].lat]] },
    })),
  };
}

function sensorFeatures(sensors: Sensor[]): GeoJSON.FeatureCollection {
  return {
    type: "FeatureCollection",
    features: sensors.map((s) => ({
      type: "Feature",
      properties: { id: s.sensor_id, status: s.status, heading: s.heading_deg, count: s.person_count, issues: s.issues.join(", "), color: s.status === "online" ? (s.issues.length ? "#fab219" : "#2a78d6") : "#9a9891" },
      geometry: { type: "Point", coordinates: [s.longitude, s.latitude] },
    })),
  };
}

function zoneMarkerElement(z: Zone, onSelect?: (id: string) => void): HTMLDivElement {
  const el = document.createElement("div");
  el.className = "cp-zone-marker";
  el.style.cssText = "display:flex;flex-direction:column;align-items:center;pointer-events:auto;cursor:pointer;transform:translateY(18px)";
  el.onclick = () => onSelect?.(z.id);
  updateZoneMarker(el, z);
  return el;
}

function updateZoneMarker(el: HTMLDivElement, z: Zone) {
  const s = z.state;
  const dir = s?.flow_direction_deg ?? 0;
  const coh = s?.flow_coherence ?? 0;
  const speed = s?.flow_speed_mps ?? 0;
  const size = 12 + Math.min(1.5, speed) * 10;
  el.innerHTML = `<div style="font-size:${size}px;line-height:1;color:#fff;opacity:${(0.15 + 0.8 * coh).toFixed(2)};transform:rotate(${(dir - 90).toFixed(0)}deg);text-shadow:0 0 3px #000">➤</div>
    <div style="margin-top:2px;font:600 11px system-ui,sans-serif;color:#fff;text-shadow:0 0 3px #000,0 0 3px #000;white-space:nowrap;text-align:center">${z.name.split(" (")[0]}<br/><span style="font-weight:400">${s ? Math.round(s.density * 100) : "–"}%${z.stale ? " · stale" : ""}</span></div>`;
}

export default function MapView({ zones, sensors, config, onSelect, height = 420 }: { zones: Zone[]; sensors: Sensor[]; config?: Config; onSelect?: (id: string) => void; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const ready = useRef(false);
  const pendingUpdate = useRef<(() => void) | null>(null);
  const markers = useRef<Map<string, maplibregl.Marker>>(new Map());
  const onSelectRef = useRef(onSelect);
  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({ container: ref.current, style: STYLE, center: [113.5398, 22.1952], zoom: 16.2, attributionControl: false });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }));
    map.on("load", () => {
      map.addSource("edges", { type: "geojson", data: edgeFeatures(undefined, []) });
      map.addLayer({ id: "edges", type: "line", source: "edges", paint: { "line-color": "#7c7b75", "line-width": 3, "line-opacity": 0.8 } });
      map.addLayer({ id: "edges-stairs", type: "line", source: "edges", filter: ["==", ["get", "stairs"], true], paint: { "line-color": "#e87ba4", "line-width": 3, "line-dasharray": [1, 1.5] } });
      map.addSource("zones", { type: "geojson", data: zoneFeatures([]) });
      map.addLayer({ id: "zones-fill", type: "circle", source: "zones", paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 14, 10, 16, 22, 18, 60], "circle-color": ["get", "color"], "circle-opacity": ["case", ["get", "stale"], 0.25, 0.45], "circle-stroke-color": ["get", "color"], "circle-stroke-width": 2 } });
      map.addSource("sensors", { type: "geojson", data: sensorFeatures([]) });
      map.addLayer({ id: "sensors", type: "circle", source: "sensors", paint: { "circle-radius": 5, "circle-color": ["get", "color"], "circle-stroke-color": "#000", "circle-stroke-width": 1 } });
      map.on("click", "zones-fill", (e: maplibregl.MapLayerMouseEvent) => { const id = e.features?.[0]?.properties?.id; if (id) onSelectRef.current?.(String(id)); });
      map.on("mouseenter", "zones-fill", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "zones-fill", () => { map.getCanvas().style.cursor = ""; });
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });
      map.on("mouseenter", "sensors", (e: maplibregl.MapLayerMouseEvent) => {
        const f = e.features?.[0]; const p = f?.properties; if (!f || !p) return;
        popup.setLngLat((f.geometry as unknown as { coordinates: [number, number] }).coordinates).setHTML(`<b>${p.id}</b><br/>${p.status} · ${p.count} people in view<br/>${p.issues || "no issues"}`).addTo(map);
      });
      map.on("mouseleave", "sensors", () => popup.remove());
      ready.current = true;
      pendingUpdate.current?.();
    });
    mapRef.current = map;
    const markerStore = markers.current;
    if (process.env.NODE_ENV !== "production") (window as unknown as { __cpMap?: maplibregl.Map }).__cpMap = map;
    return () => { map.remove(); mapRef.current = null; ready.current = false; markerStore.clear(); };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      (map.getSource("zones") as maplibregl.GeoJSONSource | undefined)?.setData(zoneFeatures(zones));
      (map.getSource("sensors") as maplibregl.GeoJSONSource | undefined)?.setData(sensorFeatures(sensors));
      (map.getSource("edges") as maplibregl.GeoJSONSource | undefined)?.setData(edgeFeatures(config, zones));
      const seen = new Set<string>();
      for (const z of zones) {
        seen.add(z.id);
        let mk = markers.current.get(z.id);
        if (!mk) {
          mk = new maplibregl.Marker({ element: zoneMarkerElement(z, (id) => onSelectRef.current?.(id)), anchor: "top" }).setLngLat([z.lon, z.lat]).addTo(map);
          markers.current.set(z.id, mk);
        } else {
          updateZoneMarker(mk.getElement() as HTMLDivElement, z);
        }
      }
      for (const [id, mk] of markers.current) if (!seen.has(id)) { mk.remove(); markers.current.delete(id); }
    };
    if (ready.current) update(); else pendingUpdate.current = update;
  }, [zones, sensors, config]);

  return <div ref={ref} style={{ height }} className="w-full overflow-hidden rounded-lg border border-zinc-800" />;
}
