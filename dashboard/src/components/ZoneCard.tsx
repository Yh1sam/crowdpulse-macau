import Link from "next/link";
import type { Zone } from "@/lib/types";
import { RiskBadge, StaleBadge } from "./Badges";
import { compass, num } from "@/lib/format";

export function ZoneCard({ z }: { z: Zone }) {
  const s = z.state;
  const p15 = z.predictions.find((p) => p.horizon_min === 15);
  return (
    <Link href={`/zones/${z.id}`} className="block rounded-lg border border-zinc-800 bg-zinc-900/70 p-3 transition hover:border-zinc-600">
      <div className="flex items-center justify-between gap-2">
        <h3 className="truncate text-sm font-semibold text-zinc-100">{z.name}</h3>
        <RiskBadge level={z.risk} />
      </div>
      <div className="mt-2 grid grid-cols-3 gap-2 text-xs text-zinc-400">
        <div><div className="text-[10px] uppercase tracking-wide text-zinc-500">density</div><div className="text-base font-semibold text-zinc-100">{num(s?.density)}</div></div>
        <div><div className="text-[10px] uppercase tracking-wide text-zinc-500">speed</div><div className="text-base font-semibold text-zinc-100">{num(s?.flow_speed_mps)} <span className="text-xs font-normal">m/s</span></div></div>
        <div><div className="text-[10px] uppercase tracking-wide text-zinc-500">flow</div><div className="text-sm font-semibold text-zinc-100">{compass(s?.flow_direction_deg)}</div></div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-zinc-400">
        <span>now <RiskBadge level={s?.congestion_state ?? "UNKNOWN"} size="sm" /></span>
        {p15 && <span>+15 min <RiskBadge level={p15.predicted_class ?? "UNKNOWN"} size="sm" /> {p15.status === "ok" ? `${Math.round(p15.effective_confidence * 100)}%` : ""}{p15.human_review_required ? " ⚠ review" : ""}</span>}
        <span className="ml-auto">{z.sensors_online}/{z.sensors_expected} sensors · rel {num(s?.reliability)}</span>
        <StaleBadge stale={z.stale} seconds={z.seconds_since_update} />
        {z.active_intervention_id && <span className="rounded bg-sky-900 px-1.5 text-sky-200">intervention #{z.active_intervention_id}</span>}
      </div>
    </Link>
  );
}
