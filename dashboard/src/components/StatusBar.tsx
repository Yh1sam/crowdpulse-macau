"use client";
import Link from "next/link";
import { useApi, post } from "@/lib/api";
import type { Health } from "@/lib/types";
import { localTime } from "@/lib/format";

export function StatusBar() {
  const { data: h, error, mutate } = useApi<Health>("/health", 2000);
  const sim = h?.live_sim;
  return (
    <header className="flex flex-wrap items-center gap-3 border-b border-zinc-800 bg-[#151514] px-4 py-2 text-xs">
      <Link href="/" className="text-sm font-bold tracking-tight text-white">CrowdPulse <span className="text-zinc-400">Macau</span></Link>
      <span className={`rounded px-2 py-0.5 ${error ? "bg-red-900 text-red-100" : "bg-emerald-900 text-emerald-100"}`}>{error ? "backend unreachable" : "backend ok"}</span>
      {h && <span className="rounded bg-zinc-800 px-2 py-0.5 text-zinc-200">{h.clock === "simulated" ? "SIM CLOCK" : "LIVE"} {localTime(h.time)} MO</span>}
      {h && <span className={`rounded px-2 py-0.5 ${h.privacy_mode ? "bg-sky-900 text-sky-100" : "bg-red-900 text-red-100"}`}>PRIVACY MODE {h.privacy_mode ? "ON" : "OFF"}</span>}
      {h && <span className={`rounded px-2 py-0.5 ${h.models_loaded ? "bg-zinc-800 text-zinc-200" : "bg-amber-900 text-amber-100"}`}>model {h.models_loaded ? h.model_version : "NOT LOADED (fallback)"}</span>}
      {sim && <span className="text-zinc-400">scenario <b className="text-zinc-200">{sim.scenario}</b> ×{sim.acceleration} · sim +{sim.elapsed_sim_min.toFixed(0)} / {sim.duration_min} min</span>}
      {!sim && h?.sim_ended && <span className="text-zinc-400" data-testid="sim-ended">demo <b className="text-zinc-200">{h.sim_ended.scenario}</b> ended at {localTime(h.sim_ended.ended_at)} (end of scenario)</span>}
      <span className="ml-auto flex gap-2">
        {sim?.running ? (
          <button className="rounded border border-zinc-600 px-2 py-0.5 hover:bg-zinc-800" onClick={async () => { await post("/sim/stop"); mutate(); }}>stop sim</button>
        ) : (
          <button className="rounded border border-zinc-600 px-2 py-0.5 hover:bg-zinc-800" onClick={async () => { await post("/sim/start", { scenario: "golden_week_demo", acceleration: 6 }); mutate(); }}>start demo sim</button>
        )}
        {sim?.running && <button className="rounded border border-zinc-600 px-2 py-0.5 hover:bg-zinc-800" onClick={async () => { await post("/sim/inject", { zone_id: "senado_square", people: 300 }); }}>inject surge (Senado)</button>}
      </span>
    </header>
  );
}
