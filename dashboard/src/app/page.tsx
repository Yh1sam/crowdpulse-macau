"use client";
import dynamic from "next/dynamic";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useApi } from "@/lib/api";
import type { Alert, Config, Sensor, Zone } from "@/lib/types";
import { ZoneCard } from "@/components/ZoneCard";
import { RiskBadge } from "@/components/Badges";
import { localTime, riskOrder } from "@/lib/format";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function Overview() {
  const router = useRouter();
  const { data: zones } = useApi<Zone[]>("/zones", 2000);
  const { data: sensors } = useApi<Sensor[]>("/sensors", 3000);
  const { data: config } = useApi<Config>("/config", 60000);
  const { data: alerts } = useApi<Alert[]>("/alerts?limit=6", 3000);
  const zs = zones ?? [];
  const worst = zs.reduce<Zone | null>((a, z) => (!a || riskOrder(z.risk) > riskOrder(a.risk) ? z : a), null);
  const counts = { CRITICAL: zs.filter((z) => z.risk === "CRITICAL").length, WARNING: zs.filter((z) => z.risk === "WARNING").length, SAFE: zs.filter((z) => z.risk === "SAFE").length };
  const review = zs.flatMap((z) => z.predictions).filter((p) => p.human_review_required).length;
  const online = (sensors ?? []).filter((s) => s.status === "online").length;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <h1 className="text-xl font-bold">Overview</h1>
          <p className="text-sm text-zinc-400">Global crowd state across the historic district. Density is a relative index (0–1), not persons per m².</p>
        </div>
        <div className="flex gap-2 text-xs">
          <Stat label="critical" value={counts.CRITICAL} color="text-red-400" />
          <Stat label="warning" value={counts.WARNING} color="text-amber-300" />
          <Stat label="safe" value={counts.SAFE} color="text-emerald-400" />
          <Stat label="human review" value={review} color="text-amber-200" />
          <Stat label="sensors online" value={`${online}/${sensors?.length ?? 0}`} color="text-sky-300" />
        </div>
      </div>
      {worst && worst.risk !== "SAFE" && (
        <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-3 text-sm">
          Highest risk: <Link className="font-semibold underline" href={`/zones/${worst.id}`}>{worst.name}</Link> <RiskBadge level={worst.risk} /> {worst.active_intervention_id && <Link className="ml-2 text-sky-300 underline" href="/interventions">intervention #{worst.active_intervention_id} awaiting decision</Link>}
        </div>
      )}
      <MapView zones={zs} sensors={sensors ?? []} config={config} onSelect={(id) => router.push(`/zones/${id}`)} height={380} />
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {[...zs].sort((a, b) => riskOrder(b.risk) - riskOrder(a.risk)).map((z) => <ZoneCard key={z.id} z={z} />)}
      </div>
      <section>
        <h2 className="mb-2 text-sm font-semibold text-zinc-300">Latest alerts <Link href="/alerts" className="ml-2 text-xs font-normal text-sky-300 underline">all</Link></h2>
        <ul className="divide-y divide-zinc-800 rounded-lg border border-zinc-800 bg-zinc-900/60 text-sm">
          {(alerts ?? []).map((a) => (
            <li key={a.id} className="flex gap-3 px-3 py-2"><span className="w-16 shrink-0 text-xs text-zinc-500">{localTime(a.created_at)}</span><span className={`w-24 shrink-0 text-xs font-semibold uppercase ${a.level.includes("critical") ? "text-red-400" : a.level === "human_review" ? "text-amber-200" : a.level === "warning" ? "text-amber-300" : "text-zinc-400"}`}>{a.level.replace("_", " ")}</span><span className="truncate">{a.title}</span></li>
          ))}
          {!alerts?.length && <li className="px-3 py-2 text-zinc-500">no alerts yet</li>}
        </ul>
      </section>
    </div>
  );
}

function Stat({ label, value, color }: { label: string; value: number | string; color: string }) {
  return <div className="rounded border border-zinc-800 bg-zinc-900 px-3 py-1.5"><div className={`text-lg font-bold ${color}`}>{value}</div><div className="text-[10px] uppercase tracking-wide text-zinc-500">{label}</div></div>;
}
