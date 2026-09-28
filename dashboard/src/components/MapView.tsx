"use client";
import { useEffect, useRef } from "react";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { Config, Sensor, Zone } from "@/lib/types";
import { RISK_COLORS } from "@/lib/format";

const STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap contributors" } },
  layers: [{ id: "bg", type: "background", paint: { "background-color": "#1a1a19" } }, { id: "osm", type: "raster", source: "osm", paint: { "raster-opacity": 0.55, "raster-saturation": -0.6, "raster-brightness-max": 0.7 } }],
};

function zoneFeatures(zones: Zone[]) {
  return {
    type: "FeatureCollection" as const,
    features: zones.map((z) => ({
      type: "Feature" as const,
      properties: { id: z.id, name: z.name, risk: z.risk, color: RISK_COLORS[z.risk], density: z.state?.density ?? 0, radius: z.polygon_radius_m, stale: z.stale, dir: z.state?.flow_direction_deg ?? 0, speed: z.state?.flow_speed_mps ?? 0, coherence: z.state?.flow_coherence ?? 0 },
      geometry: { type: "Point" as const, coordinates: [z.lon, z.lat] },
    })),
  };
}

function edgeFeatures(cfg: Config | undefined, zones: Zone[]) {
  if (!cfg) return { type: "FeatureCollection" as const, features: [] };
  const byId = Object.fromEntries(zones.map((z) => [z.id, z]));
  return {
    type: "FeatureCollection" as const,
    features: cfg.zone_graph.edges.filter((e) => byId[e.from] && byId[e.to]).map((e) => ({
      type: "Feature" as const,
      properties: { id: e.id, name: e.name, stairs: e.has_stairs },
      geometry: { type: "LineString" as const, coordinates: [[byId[e.from].lon, byId[e.from].lat], [byId[e.to].lon, byId[e.to].lat]] },
    })),
  };
}

function sensorFeatures(sensors: Sensor[]) {
  return {
    type: "FeatureCollection" as const,
    features: sensors.map((s) => ({
      type: "Feature" as const,
      properties: { id: s.sensor_id, status: s.status, heading: s.heading_deg, count: s.person_count, issues: s.issues.join(", "), color: s.status === "online" ? (s.issues.length ? "#fab219" : "#2a78d6") : "#9a9891" },
      geometry: { type: "Point" as const, coordinates: [s.longitude, s.latitude] },
    })),
  };
}

export default function MapView({ zones, sensors, config, onSelect, height = 420 }: { zones: Zone[]; sensors: Sensor[]; config?: Config; onSelect?: (id: string) => void; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const ready = useRef(false);
  const pendingUpdate = useRef<(() => void) | null>(null);

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
      map.addLayer({ id: "zones-label", type: "symbol", source: "zones", layout: { "text-field": ["concat", ["get", "name"], "\n", ["to-string", ["round", ["*", ["get", "density"], 100]]], "%"], "text-size": 11, "text-offset": [0, 2.2], "text-anchor": "top", "text-font": ["Open Sans Regular"] }, paint: { "text-color": "#ffffff", "text-halo-color": "#000000", "text-halo-width": 1.2 } });
      map.addLayer({ id: "zones-flow", type: "symbol", source: "zones", layout: { "text-field": "➤", "text-size": ["interpolate", ["linear"], ["get", "speed"], 0, 12, 1.3, 26], "text-rotate": ["-", ["get", "dir"], 90], "text-allow-overlap": true, "text-font": ["Open Sans Regular"] }, paint: { "text-color": "#ffffff", "text-opacity": ["interpolate", ["linear"], ["get", "coherence"], 0, 0.15, 1, 0.95] } });
      map.addSource("sensors", { type: "geojson", data: sensorFeatures([]) });
      map.addLayer({ id: "sensors", type: "circle", source: "sensors", paint: { "circle-radius": 5, "circle-color": ["get", "color"], "circle-stroke-color": "#000", "circle-stroke-width": 1 } });
      type LayerEvt = maplibregl.MapMouseEvent & { features?: { properties?: Record<string, unknown>; geometry: { coordinates: number[] } }[] };
      map.on("click", "zones-fill", (e: LayerEvt) => { const id = e.features?.[0]?.properties?.id; if (id && onSelect) onSelect(String(id)); });
      map.on("mouseenter", "zones-fill", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "zones-fill", () => { map.getCanvas().style.cursor = ""; });
      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });
      map.on("mouseenter", "sensors", (e: LayerEvt) => { const f = e.features?.[0]; const p = f?.properties; if (!f || !p) return; popup.setLngLat(f.geometry.coordinates as [number, number]).setHTML(`<b>${p.id}</b><br/>${p.status} · ${p.count} people in view<br/>${p.issues || "no issues"}`).addTo(map); });
      map.on("mouseleave", "sensors", () => popup.remove());
      ready.current = true;
      pendingUpdate.current?.();
    });
    mapRef.current = map;
    return () => { map.remove(); mapRef.current = null; ready.current = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      (map.getSource("zones") as maplibregl.GeoJSONSource | undefined)?.setData(zoneFeatures(zones));
      (map.getSource("sensors") as maplibregl.GeoJSONSource | undefined)?.setData(sensorFeatures(sensors));
      (map.getSource("edges") as maplibregl.GeoJSONSource | undefined)?.setData(edgeFeatures(config, zones));
    };
    if (ready.current) update(); else pendingUpdate.current = update;
  }, [zones, sensors, config]);

  return <div ref={ref} style={{ height }} className="w-full overflow-hidden rounded-lg border border-zinc-800" />;
}
