"use client";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Health, Sensor, Zone } from "@/lib/types";
import { localTime, num, pct } from "@/lib/format";

interface Status { loaded: boolean; version: string; model_types: Record<string, string>; ood_detector: boolean; trained_at: string | null; calibration: Record<string, { calibrated: boolean }> }

export default function Reliability() {
  const { data: sensors } = useApi<Sensor[]>("/sensors", 2000);
  const { data: zones } = useApi<Zone[]>("/zones", 2000);
  const { data: health } = useApi<Health>("/health", 2000);
  const { data: status } = useApi<Status>("/model/status", 30000);
  const preds = (zones ?? []).flatMap((z) => z.predictions);
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Reliability</h1>
      <section className="grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm"><h2 className="font-semibold">Model status</h2>
          <p className="text-xs text-zinc-400">{status?.loaded ? `loaded ${status.version}` : "NOT LOADED — persistence fallback, all predictions flagged"}</p>
          <p className="text-xs text-zinc-400">types: {status ? Object.entries(status.model_types).map(([h, t]) => `+${h}:${t}`).join(" · ") : "–"}</p>
          <p className="text-xs text-zinc-400">OOD detector: {status?.ood_detector ? "isolation forest + range checks" : "none"} · trained {status?.trained_at ? localTime(status.trained_at) : "–"}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm"><h2 className="font-semibold">Pipeline</h2>
          <p className="text-xs text-zinc-400">clock {health?.clock} · last refresh {localTime(health?.last_refresh)} · {health?.stats?.last_refresh_ms} ms</p>
          <p className="text-xs text-zinc-400">observations ingested {health?.stats?.observations_ingested} · refreshes {health?.stats?.refreshes}</p>
        </div>
        <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm"><h2 className="font-semibold">Human-review gate</h2>
          <p className="text-xs text-zinc-400">{preds.filter((p) => p.human_review_required).length} of {preds.length} current predictions flagged · {preds.filter((p) => p.ood_flag).length} flagged as unusual conditions</p>
        </div>
      </section>
      <section>
        <h2 className="mb-2 text-sm font-semibold">Zone reliability</h2>
        <table className="w-full text-sm"><thead className="text-left text-xs uppercase text-zinc-500"><tr><th>zone</th><th>sensors</th><th>reliability</th><th>disagreement</th><th>obstruction</th><th>stale</th><th>confidence (+15)</th></tr></thead>
          <tbody className="divide-y divide-zinc-800">{(zones ?? []).map((z) => { const p = z.predictions.find((x) => x.horizon_min === 15); return (
            <tr key={z.id}><td><Link href={`/zones/${z.id}`} className="underline">{z.name}</Link></td><td>{z.sensors_online}/{z.sensors_expected}</td><td><Bar v={z.state?.reliability ?? 0} /></td><td>{num(z.state?.disagreement)}</td><td>{pct(z.state?.obstructed_fraction)}</td><td>{z.stale ? <span className="text-amber-300">yes</span> : "no"}</td><td>{p ? `${pct(p.effective_confidence)}${p.human_review_required ? " ⚠ review" : ""}` : "–"}</td></tr>); })}</tbody></table>
      </section>
      <section>
        <h2 className="mb-2 text-sm font-semibold">Sensor health</h2>
        <table className="w-full text-sm"><thead className="text-left text-xs uppercase text-zinc-500"><tr><th>node</th><th>zone</th><th>status</th><th>last seen</th><th>stability</th><th>GPS ±m</th><th>vision</th><th>obstructed</th><th>count</th><th>score</th><th>issues</th></tr></thead>
          <tbody className="divide-y divide-zinc-800">{(sensors ?? []).map((s) => (
            <tr key={s.sensor_id} className={s.status !== "online" ? "opacity-60" : ""}><td className="font-mono text-xs">{s.sensor_id}</td><td>{s.zone_id ?? "–"}</td><td><span className={`rounded px-1.5 text-xs ${s.status === "online" ? "bg-emerald-900 text-emerald-200" : s.status === "stale" ? "bg-amber-900 text-amber-200" : "bg-red-900 text-red-200"}`}>{s.status}</span></td><td className="text-xs">{localTime(s.last_seen)} ({Math.round(s.seconds_since_seen)}s)</td><td>{num(s.device_motion_stability)}</td><td>{num(s.location_accuracy_m, 0)}</td><td>{num(s.vision_confidence)}</td><td>{s.camera_obstructed ? <span className="text-red-300">yes</span> : "no"}</td><td>{s.person_count}</td><td><Bar v={s.reliability_score} /></td><td className="text-xs text-amber-200">{s.issues.join(", ")}</td></tr>
          ))}</tbody></table>
      </section>
    </div>
  );
}

function Bar({ v }: { v: number }) {
  return <span className="inline-flex items-center gap-1"><span className="inline-block h-2 w-20 rounded bg-zinc-800"><span className={`block h-2 rounded ${v > 0.75 ? "bg-emerald-500" : v > 0.5 ? "bg-amber-400" : "bg-red-500"}`} style={{ width: `${Math.max(0, Math.min(1, v)) * 100}%` }} /></span><span className="text-xs tabular-nums">{v.toFixed(2)}</span></span>;
}
