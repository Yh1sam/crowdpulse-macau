"use client";
import type { Intervention, SketchFutureCrosswalk } from "@/lib/types";
import { buildSketchFutureCheck } from "@/lib/sketchfuture";

/**
 * "Test in SketchFuture" for a redirect recommendation: opens SketchFuture with the corridor the
 * recommendation diverts people away from closed, so its route + queue model shows the detour for
 * walkers, wheelchair users and stroller users on real streets. Renders nothing for other kinds.
 */
export function SketchFutureCheck({ iv, crosswalk, compact = false }: { iv: Intervention; crosswalk?: SketchFutureCrosswalk; compact?: boolean }) {
  if (iv.kind !== "redirect_flow" || !iv.route) return null;
  const check = buildSketchFutureCheck(iv, crosswalk);
  if (!check.ok) {
    if (compact) return null;
    return <p className="mt-2 text-xs text-zinc-500" data-testid="sketchfuture-unavailable">Scenario simulation unavailable: {check.reason.replace(/SketchFuture's/g, "the scenario model's").replace(/\.$/, "")}.</p>;
  }
  const { plan } = check;
  const { corridor } = plan;
  const zh = (id: string) => crosswalk?.zones[id]?.name_zh ?? id;
  if (compact) return <a href={plan.url} target="_blank" rel="noreferrer" className="text-xs text-violet-300 underline" data-testid="sketchfuture-link">scenario simulation ↗</a>;
  return (
    <div className="mt-3 rounded border border-violet-800/60 bg-violet-950/30 p-3 text-xs" data-testid="sketchfuture-check">
      <div className="flex flex-wrap items-center gap-3">
        <span className="font-semibold text-violet-200">CrowdPulse · Scenario simulation</span>
        <a href={plan.url} target="_blank" rel="noreferrer" data-testid="sketchfuture-link" className="rounded bg-violet-700 px-3 py-1 text-sm font-semibold text-white hover:bg-violet-600">OPEN SCENARIO SIMULATION ↗</a>
      </div>
      <p className="mt-1 text-zinc-300">
        Tests the <b>{corridor.name}</b> corridor closed ({corridor.streets.join("、")}, {corridor.close.length} segment{corridor.close.length === 1 ? "" : "s"}) and compares the same walkers, wheelchair users and stroller users on Macau&apos;s OSM streets, with queues.
        {corridor.direct_m != null && corridor.detour_m != null && <> In this street model the shortest walking route {zh(corridor.from)} ↔ {zh(corridor.to)} grows from {corridor.direct_m} m to {corridor.detour_m} m.</>}
      </p>
      <p className="mt-1 text-zinc-500">
        A full closure is a stress test of the proposed partial diversion. These are modelled journeys, not verification of the actual alternative route{crosswalk?.model_version ? ` (model ${crosswalk.model_version})` : ""}. An on-site check is still required; opening this model does not enable approval.
      </p>
    </div>
  );
}
