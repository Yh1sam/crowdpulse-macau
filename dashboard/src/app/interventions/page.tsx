"use client";
import { useState } from "react";
import Link from "next/link";
import { useApi, post } from "@/lib/api";
import type { AuditEntry, Intervention, Prediction } from "@/lib/types";
import { RiskBadge } from "@/components/Badges";
import { auditDetails, localDateTime, localTime, pct } from "@/lib/format";

export default function Interventions() {
  const { data: ivs, mutate } = useApi<Intervention[]>("/interventions?limit=100", 3000);
  const { data: audit } = useApi<AuditEntry[]>("/audit?limit=50", 5000);
  const [evidence, setEvidence] = useState<Intervention | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const pending = (ivs ?? []).filter((i) => i.status === "pending");
  const others = (ivs ?? []).filter((i) => i.status !== "pending");
  const decide = async (iv: Intervention, approve: boolean) => {
    setBusy(iv.id);
    try { await post(`/interventions/${iv.id}/${approve ? "approve" : "reject"}`, { operator: "operator", note: approve ? "approved from dashboard" : "rejected from dashboard" }); await mutate(); }
    catch (e) { alert(String(e)); } finally { setBusy(null); }
  };
  return (
    <div className="space-y-4">
      <h1 className="text-xl font-bold">Interventions</h1>
      <p className="text-sm text-zinc-400">The system recommends; you decide. Approvals and rejections are written to the audit log. In the live simulation an approved redirect/inflow reduction is applied to the crowd model so the forecast is recalculated.</p>
      <section className="space-y-3">
        <h2 className="text-sm font-semibold text-zinc-300">Awaiting decision ({pending.length})</h2>
        {pending.length === 0 && <p className="text-sm text-zinc-500">No pending recommendations.</p>}
        {pending.map((iv) => (
          <div key={iv.id} className="rounded-lg border border-amber-700/60 bg-zinc-900 p-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-zinc-500">#{iv.id} · {localTime(iv.created_at)}</span>
              <RiskBadge level={iv.predicted_class ?? "UNKNOWN"} />
              {iv.horizon_min && <span className="text-xs text-zinc-400">+{iv.horizon_min} min · {pct(iv.confidence)} confidence</span>}
              {iv.low_confidence && <span className="rounded border border-amber-400 px-2 text-xs text-amber-200">LOW CONFIDENCE — HUMAN REVIEW REQUIRED</span>}
              <span className="rounded bg-zinc-800 px-2 text-xs">{iv.kind.replace("_", " ")}</span>
              <Link href={`/zones/${iv.zone_id}`} className="ml-auto text-xs text-sky-300 underline">{iv.zone_id}</Link>
            </div>
            <h3 className="mt-2 text-base font-semibold">{iv.title}</h3>
            <p className="mt-1 text-sm text-zinc-200">{iv.recommendation}</p>
            {iv.route && <p className="mt-1 text-xs text-zinc-400">Route: {iv.route.edges.join(" → ")} · {iv.route.length_m} m · {iv.route.has_stairs ? "has stairs" : "no stairs"} · accessibility penalty {iv.route.accessibility_penalty}</p>}
            {iv.accessibility?.note && <p className="mt-1 text-xs text-emerald-200">♿ {String(iv.accessibility.note)}</p>}
            {Object.keys(iv.messages).length > 0 && (
              <details className="mt-2 text-xs text-zinc-300"><summary className="cursor-pointer text-zinc-400">Public notice (中文 / English / Português)</summary>
                <ul className="mt-1 space-y-1"><li>ZH: {iv.messages.zh}</li><li>EN: {iv.messages.en}</li><li>PT: {iv.messages.pt}</li></ul></details>
            )}
            <div className="mt-3 flex gap-2">
              <button disabled={busy === iv.id} className="rounded bg-emerald-700 px-3 py-1 text-sm font-semibold hover:bg-emerald-600 disabled:opacity-50" onClick={() => decide(iv, true)}>APPROVE</button>
              <button disabled={busy === iv.id} className="rounded bg-red-800 px-3 py-1 text-sm font-semibold hover:bg-red-700 disabled:opacity-50" onClick={() => decide(iv, false)}>REJECT</button>
              <button className="rounded border border-zinc-600 px-3 py-1 text-sm hover:bg-zinc-800" onClick={() => setEvidence(evidence?.id === iv.id ? null : iv)}>VIEW EVIDENCE</button>
            </div>
            {evidence?.id === iv.id && <Evidence iv={iv} />}
          </div>
        ))}
      </section>
      <section>
        <h2 className="mb-2 text-sm font-semibold text-zinc-300">Decided / expired</h2>
        <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800 bg-zinc-900/60 text-sm">
          {others.map((iv) => (
            <li key={iv.id} className="px-3 py-2">
              <div className="flex flex-wrap items-center gap-2"><span className="text-xs text-zinc-500">#{iv.id} {localTime(iv.created_at)}</span><span className={`rounded px-1.5 text-xs ${iv.status === "approved" ? "bg-emerald-900 text-emerald-200" : iv.status === "rejected" ? "bg-red-900 text-red-200" : "bg-zinc-800 text-zinc-300"}`}>{iv.status}</span><span>{iv.title}</span><span className="text-xs text-zinc-500">{iv.decided_by ? `by ${iv.decided_by}` : ""} {iv.effect_applied ? "· effect applied to simulation" : ""}</span></div>
              {iv.projected_after && (
                <p className="mt-1 text-xs text-zinc-400">Recalculated forecast (what-if, inflow ×{iv.projected_after.inflow_multiplier}): {Object.entries(iv.projected_after.horizons).map(([h, v]) => <span key={h} className="mr-2">+{h} min <RiskBadge level={v.predicted_class} size="sm" /> {pct(v.confidence)}</span>)} <i>{iv.projected_after.note}</i></p>
              )}
            </li>
          ))}
          {!others.length && <li className="px-3 py-2 text-zinc-500">none yet</li>}
        </ul>
      </section>
      <section>
        <h2 className="mb-2 text-sm font-semibold text-zinc-300">Audit log</h2>
        <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800 bg-zinc-900/60 text-xs">
          {(audit ?? []).map((a) => <li key={a.id} className="flex flex-wrap gap-x-3 gap-y-0.5 px-3 py-1.5"><span className="w-36 shrink-0 text-zinc-500">{localDateTime(a.timestamp)}</span><span className="w-16 shrink-0 font-semibold">{a.actor}</span><span className="w-60 min-w-0 shrink break-words">{a.action}</span><span className="min-w-0 flex-1 basis-64 break-words text-zinc-400">{a.target_type} #{a.target_id} · {auditDetails(a.details)}</span></li>)}
        </ul>
      </section>
    </div>
  );
}

function Evidence({ iv }: { iv: Intervention }) {
  const { data: preds } = useApi<Prediction[]>(`/zones/${iv.zone_id}/prediction`, 3000);
  return (
    <div className="mt-3 rounded border border-zinc-700 bg-zinc-950 p-3 text-xs">
      <h4 className="mb-1 font-semibold text-zinc-300">Evidence</h4>
      <ul className="list-disc space-y-0.5 pl-5 text-zinc-300">{iv.rationale.map((r, i) => <li key={i}>{r}</li>)}</ul>
      {preds && <p className="mt-2 text-zinc-400">Current forecast: {preds.map((p) => <span key={p.horizon_min} className="mr-2">+{p.horizon_min} <RiskBadge level={p.predicted_class ?? "UNKNOWN"} size="sm" /> {pct(p.effective_confidence)}{p.human_review_required ? " ⚠" : ""}</span>)}</p>}
      {iv.route_alternatives.length > 0 && <p className="mt-2 text-zinc-400">Alternatives considered: {iv.route_alternatives.map((r, i) => <span key={i} className="mr-2">[{r.edges.join(" → ")} · {r.length_m} m{r.has_stairs ? " · stairs" : ""} · penalty {r.accessibility_penalty}]</span>)}</p>}
      <p className="mt-1 text-zinc-500">Assumed effect: {JSON.stringify(iv.assumed_effect)}</p>
      <Link href={`/zones/${iv.zone_id}`} className="text-sky-300 underline">open zone detail →</Link>
    </div>
  );
}
