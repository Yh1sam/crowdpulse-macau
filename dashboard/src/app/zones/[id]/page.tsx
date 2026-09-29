"use client";
import { use } from "react";
import Link from "next/link";
import { useApi } from "@/lib/api";
import type { Config, Intervention, Zone, ZoneState } from "@/lib/types";
import { RiskBadge, StaleBadge } from "@/components/Badges";
import { Contributions, PredictionRow, Reasons } from "@/components/PredictionCard";
import { DensityChart, ReliabilityArea } from "@/components/DensityChart";
import { compass, localTime, num, pct } from "@/lib/format";

export default function ZoneDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: z, error } = useApi<Zone>(`/zones/${id}`, 2000);
  const { data: hist } = useApi<ZoneState[]>(`/zones/${id}/history?minutes=90`, 5000);
  const { data: config } = useApi<Config>("/config", 60000);
  const { data: activeIv } = useApi<Intervention>(z?.active_intervention_id ? `/interventions/${z.active_intervention_id}` : null, 3000);
  if (error) return <p className="text-red-300">{String(error)}</p>;
  if (!z) return <p className="text-zinc-500">loading…</p>;
  const s = z.state;
  const iv = activeIv && activeIv.id === z.active_intervention_id ? activeIv : undefined;
  const p15 = z.predictions.find((p) => p.horizon_min === 15) ?? z.predictions[0];
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-bold">{z.name}</h1>
        <RiskBadge level={z.risk} size="lg" />
        <StaleBadge stale={z.stale} seconds={z.seconds_since_update} />
        <span className="text-xs text-zinc-500">{z.kind} · capacity index base {z.capacity} · neighbours: {z.neighbours.map((n) => <Link key={n} href={`/zones/${n}`} className="ml-1 underline">{n}</Link>)}</span>
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        <Tile label="density index (relative, 0–1)" value={num(s?.density)} sub={s?.congestion_state ?? "–"} />
        <Tile label="people in view (all sensors)" value={num(s?.person_count_visible, 0)} sub={`${z.sensors_online}/${z.sensors_expected} sensors online`} />
        <Tile label="flow" value={compass(s?.flow_direction_deg)} sub={`${num(s?.flow_speed_mps)} m/s · coherence ${num(s?.flow_coherence)}`} />
        <Tile label="inflow / outflow proxy" value={`${num(s?.inflow_proxy)} / ${num(s?.outflow_proxy)}`} sub={`reliability ${num(s?.reliability)} · disagreement ${num(s?.disagreement)}`} />
      </div>
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
        <h2 className="mb-2 text-sm font-semibold">History and forecast <span className="text-xs font-normal text-zinc-500">last 90 min, Macau time</span></h2>
        <DensityChart history={hist ?? []} predictions={z.predictions} config={config} />
      </section>
      <div className="grid gap-3 lg:grid-cols-2">
        <section className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
          <h2 className="mb-2 text-sm font-semibold">Prediction <span className="text-xs font-normal text-zinc-500">updated {localTime(z.predictions[0]?.created_at)}</span></h2>
          <div className="space-y-1">{z.predictions.map((p) => <PredictionRow key={p.horizon_min} p={p} />)}</div>
          {p15 && (
            <div className="mt-3 space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-zinc-400">Why (+{p15.horizon_min} min → {p15.predicted_class ?? "no prediction"})</h3>
              <Reasons p={p15} />
              <Contributions p={p15} />
              {p15.ood_flag && <p className="text-xs text-violet-200">{p15.ood_message} {p15.ood_reasons.join("; ")}</p>}
              <p className="text-[11px] text-zinc-500">model {p15.model_type || "–"} {p15.model_version} · model confidence {pct(p15.model_confidence)} × reliability factor → effective {pct(p15.effective_confidence)}</p>
            </div>
          )}
        </section>
        <section className="space-y-3">
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
            <h2 className="mb-2 text-sm font-semibold">Sensor reliability</h2>
            <ReliabilityArea history={hist ?? []} />
            <p className="text-xs text-zinc-500">obstruction {pct(s?.obstructed_fraction)} · stability {num(s?.mean_stability)} · GPS ±{num(s?.mean_gps_accuracy_m, 0)} m · vision conf {num(s?.mean_vision_confidence)}</p>
          </div>
          <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
            <h2 className="mb-2 text-sm font-semibold">Intervention</h2>
            {iv ? (
              <div className="text-sm"><span className="rounded bg-sky-900 px-1.5 text-xs text-sky-200">{iv.status}</span> <b>{iv.title}</b><p className="mt-1 text-zinc-300">{iv.recommendation}</p><Link href="/interventions" className="text-sky-300 underline">review on the interventions page →</Link></div>
            ) : <p className="text-sm text-zinc-500">no active recommendation for this zone</p>}
          </div>
        </section>
      </div>
    </div>
  );
}

function Tile({ label, value, sub }: { label: string; value: string; sub: string }) {
  return <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3"><div className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</div><div className="text-xl font-bold">{value}</div><div className="text-xs text-zinc-400">{sub}</div></div>;
}
