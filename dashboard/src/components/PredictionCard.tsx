import type { Prediction } from "@/lib/types";
import { ConfidenceBadge, OodBadge, RiskBadge } from "./Badges";
import { localTime, num, pct } from "@/lib/format";

export function PredictionRow({ p }: { p: Prediction }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded border border-zinc-800 bg-zinc-900/60 px-3 py-2">
      <span className="w-16 text-sm text-zinc-400">+{p.horizon_min} min</span>
      <span className="w-14 text-xs text-zinc-500">{localTime(p.target_time)}</span>
      <RiskBadge level={p.predicted_class ?? "UNKNOWN"} />
      <ConfidenceBadge prediction={p} compact />
      {p.status === "ok" && (
        <span className="text-xs text-zinc-400" title="P(SAFE) / P(WARNING) / P(CRITICAL)">
          {pct(p.probabilities.SAFE)} / {pct(p.probabilities.WARNING)} / {pct(p.probabilities.CRITICAL)}
        </span>
      )}
      {p.predicted_density != null && <span className="text-xs text-zinc-400">density → {num(p.predicted_density)}</span>}
      {p.status === "fallback" && <span className="text-xs text-amber-300">fallback (no model)</span>}
      <OodBadge prediction={p} />
    </div>
  );
}

export function Reasons({ p }: { p: Prediction }) {
  return (
    <ul className="list-disc space-y-0.5 pl-5 text-sm text-zinc-300">
      {p.reasons.map((r, i) => <li key={i}>{r}</li>)}
    </ul>
  );
}

export function Contributions({ p }: { p: Prediction }) {
  if (!p.contributions?.length) return null;
  const max = Math.max(...p.contributions.map((c) => Math.abs(c.delta)), 1e-6);
  return (
    <div className="space-y-1">
      {p.contributions.map((c) => (
        <div key={c.feature} className="flex items-center gap-2 text-xs">
          <span className="w-44 truncate text-zinc-400" title={c.feature}>{c.label}</span>
          <div className="relative h-2 w-40 rounded bg-zinc-800">
            <div className={`absolute top-0 h-2 rounded ${c.delta >= 0 ? "bg-red-500" : "bg-sky-500"}`} style={{ left: c.delta >= 0 ? "50%" : `${50 - (Math.abs(c.delta) / max) * 50}%`, width: `${(Math.abs(c.delta) / max) * 50}%` }} />
          </div>
          <span className="w-16 text-right tabular-nums text-zinc-300">{c.delta >= 0 ? "+" : ""}{(c.delta * 100).toFixed(1)} pp</span>
          <span className="text-zinc-500">value {c.value == null ? "–" : c.value.toFixed(2)} vs typical {c.reference == null ? "–" : c.reference.toFixed(2)}</span>
        </div>
      ))}
      <p className="text-[11px] text-zinc-500">Local sensitivity analysis: change in P(predicted class) when the feature is replaced by its training median. Not SHAP.</p>
    </div>
  );
}
