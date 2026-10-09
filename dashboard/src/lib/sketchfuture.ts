import type { Intervention, SketchFutureCorridor, SketchFutureCrosswalk } from "./types";

/** Where the SketchFuture app is served (its Vite dev server or preview, port 4173 by default). */
export const SKETCHFUTURE_URL = process.env.NEXT_PUBLIC_SKETCHFUTURE_URL ?? "http://localhost:4173";
/** SketchFuture's own default cohort and conditions, so the comparison is the one its examples use. */
export const SKETCHFUTURE_SETTINGS = { people: 120, releaseSeconds: 120, speedFactor: 1, capacityFactor: 1, seed: 42, repeats: 5, horizon: 1800 };

export interface SketchFutureWorkspace {
  version: 1; mapVersion: string; title: string; edits: { type: "close"; edgeId: string }[]; settings: typeof SKETCHFUTURE_SETTINGS;
}
export interface SketchFuturePlan {
  url: string; corridorId: string; corridor: SketchFutureCorridor; source: string; zone: string; workspace: SketchFutureWorkspace;
}
export type SketchFutureCheck = { ok: true; plan: SketchFuturePlan } | { ok: false; reason: string };

/** base64url of the UTF-8 JSON, the encoding SketchFuture's `decodePlan` reads from `#plan=`. */
export function encodePlan(payload: { workspace: SketchFutureWorkspace; source?: string }): string {
  const bytes = new TextEncoder().encode(JSON.stringify(payload));
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x2000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x2000));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/**
 * Turn a redirect recommendation into a SketchFuture plan: close the zone-graph corridor between the
 * flow's source zone and the congested zone, so SketchFuture's route + queue model shows the detour
 * every walker, wheelchair user and stroller user would take on Macau's OSM streets. A full closure
 * is the extreme case (100% diversion) of CrowdPulse's assumed partial redirect.
 */
export function buildSketchFutureCheck(iv: Intervention, crosswalk: SketchFutureCrosswalk | undefined, baseUrl = SKETCHFUTURE_URL): SketchFutureCheck {
  if (iv.kind !== "redirect_flow" || !iv.route) return { ok: false, reason: "only redirect recommendations change routes" };
  if (!crosswalk) return { ok: false, reason: "SketchFuture crosswalk not loaded from /config" };
  const source = iv.route.from, zone = iv.zone_id;
  const match = Object.entries(crosswalk.edges).find(([, e]) => (e.from === source && e.to === zone) || (e.from === zone && e.to === source));
  if (!match) return { ok: false, reason: `no zone-graph corridor between ${source} and ${zone}` };
  const [corridorId, corridor] = match;
  if (corridor.unsupported || corridor.close.length === 0) return { ok: false, reason: corridor.unsupported ?? "no closure recorded for this corridor" };
  const zh = (id: string) => crosswalk.zones[id]?.name_zh ?? id;
  const workspace: SketchFutureWorkspace = {
    version: 1, mapVersion: crosswalk.map_version, title: `CrowdPulse #${iv.id}：封閉${zh(source)}↔${zh(zone)}通道`.slice(0, 80),
    edits: corridor.close.map((edgeId) => ({ type: "close", edgeId })), settings: { ...SKETCHFUTURE_SETTINGS },
  };
  const label = `CrowdPulse 建議 #${iv.id}（${iv.title}）`;
  const url = `${baseUrl.replace(/\/+$/, "")}/#plan=${encodePlan({ workspace, source: label })}`;
  return { ok: true, plan: { url, corridorId, corridor, source: label, zone, workspace } };
}
