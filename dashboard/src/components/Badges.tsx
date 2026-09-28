import type { CongestionClass, Prediction } from "@/lib/types";
import { RISK_BG, pct } from "@/lib/format";

export function RiskBadge({ level, size = "md" }: { level: CongestionClass | "UNKNOWN" | null | undefined; size?: "sm" | "md" | "lg" }) {
  const l = level ?? "UNKNOWN";
  const cls = size === "lg" ? "px-3 py-1 text-base" : size === "sm" ? "px-1.5 py-0 text-[10px]" : "px-2 py-0.5 text-xs";
  return <span data-testid="risk-badge" className={`inline-flex items-center rounded font-semibold tracking-wide text-white ${RISK_BG[l]} ${cls}`}>{l}</span>;
}

/** Confidence display with the responsible-AI gate: low confidence => HUMAN REVIEW REQUIRED. */
export function ConfidenceBadge({ prediction, compact = false }: { prediction: Prediction; compact?: boolean }) {
  if (prediction.status === "insufficient_data") {
    return <span data-testid="confidence" className="inline-flex items-center gap-1 rounded border border-zinc-500 px-2 py-0.5 text-xs text-zinc-300">NO DATA — HUMAN REVIEW REQUIRED</span>;
  }
  if (prediction.human_review_required) {
    return (
      <span data-testid="confidence" className="inline-flex items-center gap-1 rounded border border-amber-400 bg-amber-950/60 px-2 py-0.5 text-xs font-semibold text-amber-200">
        ⚠ LOW CONFIDENCE — HUMAN REVIEW REQUIRED {compact ? "" : `(${pct(prediction.effective_confidence)})`}
      </span>
    );
  }
  return <span data-testid="confidence" className="inline-flex items-center rounded bg-zinc-700 px-2 py-0.5 text-xs text-zinc-100">{pct(prediction.effective_confidence)} confidence</span>;
}

export function OodBadge({ prediction }: { prediction: Prediction }) {
  if (!prediction.ood_flag) return null;
  return <span data-testid="ood" title={prediction.ood_reasons.join("; ")} className="inline-flex items-center rounded border border-violet-400 bg-violet-950/60 px-2 py-0.5 text-xs text-violet-200">⚠ {prediction.ood_message ?? "Conditions differ from training data."}</span>;
}

export function StaleBadge({ stale, seconds }: { stale: boolean; seconds: number | null }) {
  if (!stale) return null;
  return <span className="inline-flex items-center rounded border border-zinc-500 px-2 py-0.5 text-xs text-zinc-300">STALE {seconds != null ? `(${Math.round(seconds)}s)` : ""}</span>;
}
