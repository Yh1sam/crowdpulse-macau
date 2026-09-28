"use client";
import { useApi } from "@/lib/api";
import type { Zone } from "@/lib/types";
import { RiskBadge } from "@/components/Badges";
import { Contributions, PredictionRow, Reasons } from "@/components/PredictionCard";

interface Metrics { status: { model_types: Record<string, string>; version: string; features: string[] }; metrics: { per_horizon?: Record<string, { feature_importances: Record<string, number> | null; chosen_model: string }> } }

export default function Explain() {
  const { data: zones } = useApi<Zone[]>("/zones", 3000);
  const { data: m } = useApi<Metrics>("/model/metrics", 60000);
  const imp = m?.metrics?.per_horizon?.h15?.feature_importances;
  const top = imp ? Object.entries(imp).slice(0, 10) : [];
  const max = top.length ? top[0][1] : 1;
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">AI explanation</h1>
      <p className="text-sm text-zinc-400">Every prediction ships with plain-language reasons derived from the observed features, plus a local sensitivity analysis showing which inputs pushed the prediction. Global feature importance comes from the trained model.</p>
      <section className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
        <h2 className="text-sm font-semibold">Global feature importance (+15 min model: {m?.metrics?.per_horizon?.h15?.chosen_model ?? "–"})</h2>
        <div className="mt-2 space-y-1">
          {top.map(([f, v]) => <div key={f} className="flex items-center gap-2 text-xs"><span className="w-56 text-zinc-400">{f}</span><div className="h-2 flex-1 rounded bg-zinc-800"><div className="h-2 rounded bg-sky-500" style={{ width: `${(v / max) * 100}%` }} /></div><span className="w-12 text-right tabular-nums">{(v * 100).toFixed(1)}%</span></div>)}
          {!top.length && <p className="text-xs text-zinc-500">model metrics not available</p>}
        </div>
      </section>
      <div className="grid gap-3 lg:grid-cols-2">
        {(zones ?? []).map((z) => {
          const p = z.predictions.find((x) => x.horizon_min === 15) ?? z.predictions[0];
          return (
            <section key={z.id} className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
              <div className="flex items-center justify-between"><h2 className="font-semibold">{z.name}</h2><RiskBadge level={z.risk} /></div>
              {p ? (<div className="mt-2 space-y-2"><PredictionRow p={p} /><Reasons p={p} /><Contributions p={p} /></div>) : <p className="text-sm text-zinc-500">no prediction</p>}
            </section>
          );
        })}
      </div>
    </div>
  );
}
