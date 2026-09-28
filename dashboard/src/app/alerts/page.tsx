"use client";
import Link from "next/link";
import { useApi, post } from "@/lib/api";
import type { Alert } from "@/lib/types";
import { localDateTime, pct } from "@/lib/format";

const LEVEL_STYLE: Record<string, string> = { critical: "text-red-400", critical_now: "text-red-300", human_review: "text-amber-200", warning: "text-amber-300", ood: "text-violet-300", sensor: "text-sky-300" };

export default function Alerts() {
  const { data: alerts, mutate } = useApi<Alert[]>("/alerts?limit=200", 3000);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-bold">Alerts</h1>
      <p className="text-sm text-zinc-400">Chronological congestion, human-review, unusual-condition and sensor alerts. Alerts repeat at most every 5 minutes per zone and level.</p>
      <table className="w-full text-sm">
        <thead className="text-left text-xs uppercase tracking-wide text-zinc-500"><tr><th className="py-1">time (MO)</th><th>level</th><th>zone</th><th>message</th><th>conf.</th><th></th></tr></thead>
        <tbody className="divide-y divide-zinc-800">
          {(alerts ?? []).map((a) => (
            <tr key={a.id} className={a.acknowledged ? "opacity-50" : ""}>
              <td className="whitespace-nowrap py-2 pr-2 text-xs text-zinc-400">{localDateTime(a.created_at)}</td>
              <td className={`pr-2 text-xs font-semibold uppercase ${LEVEL_STYLE[a.level] ?? "text-zinc-300"}`}>{a.level.replace("_", " ")}</td>
              <td className="pr-2"><Link href={`/zones/${a.zone_id}`} className="underline">{a.zone_id}</Link></td>
              <td className="pr-2 text-zinc-300"><b className="text-zinc-100">{a.title}</b><br />{a.message}</td>
              <td className="pr-2 text-xs">{pct(a.confidence)}</td>
              <td>{!a.acknowledged && <button className="rounded border border-zinc-600 px-2 py-0.5 text-xs hover:bg-zinc-800" onClick={async () => { await post(`/alerts/${a.id}/ack`, { operator: "operator" }); mutate(); }}>ack</button>}</td>
            </tr>
          ))}
          {!alerts?.length && <tr><td colSpan={6} className="py-4 text-zinc-500">no alerts yet</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
