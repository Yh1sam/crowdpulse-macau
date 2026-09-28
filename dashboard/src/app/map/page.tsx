"use client";
import dynamic from "next/dynamic";
import { useState } from "react";
import { useApi } from "@/lib/api";
import type { Config, Sensor, Zone } from "@/lib/types";
import { RiskBadge, StaleBadge } from "@/components/Badges";
import { PredictionRow, Reasons } from "@/components/PredictionCard";
import { compass, num } from "@/lib/format";
import Link from "next/link";

const MapView = dynamic(() => import("@/components/MapView"), { ssr: false });

export default function LiveMap() {
  const { data: zones } = useApi<Zone[]>("/zones", 2000);
  const { data: sensors } = useApi<Sensor[]>("/sensors", 3000);
  const { data: config } = useApi<Config>("/config", 60000);
  const [sel, setSel] = useState<string | null>(null);
  const z = zones?.find((x) => x.id === sel) ?? null;
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-bold">Live map</h1>
      <p className="text-sm text-zinc-400">Circles = zones coloured by risk (current state or a confident forecast, whichever is worse). Arrows = dominant flow direction, sized by speed, faded when flow is incoherent. Dots = sensor nodes (blue ok, yellow issues, grey offline). Dashed pink edge = stairs.</p>
      <div className="grid gap-3 lg:grid-cols-[2fr_1fr]">
        <MapView zones={zones ?? []} sensors={sensors ?? []} config={config} onSelect={setSel} height={560} />
        <aside className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3 text-sm">
          {!z && <p className="text-zinc-500">Click a zone for details.</p>}
          {z && (
            <div className="space-y-3">
              <div className="flex items-center justify-between"><h2 className="font-semibold">{z.name}</h2><RiskBadge level={z.risk} /></div>
              <StaleBadge stale={z.stale} seconds={z.seconds_since_update} />
              <dl className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs text-zinc-300">
                <dt className="text-zinc-500">density index</dt><dd>{num(z.state?.density)} ({z.state?.congestion_state ?? "–"})</dd>
                <dt className="text-zinc-500">people in view</dt><dd>{num(z.state?.person_count_visible, 0)}</dd>
                <dt className="text-zinc-500">flow</dt><dd>{compass(z.state?.flow_direction_deg)} · {num(z.state?.flow_speed_mps)} m/s</dd>
                <dt className="text-zinc-500">inflow / outflow proxy</dt><dd>{num(z.state?.inflow_proxy)} / {num(z.state?.outflow_proxy)}</dd>
                <dt className="text-zinc-500">reliability</dt><dd>{num(z.state?.reliability)} · {z.sensors_online}/{z.sensors_expected} sensors</dd>
              </dl>
              <div className="space-y-1">{z.predictions.map((p) => <PredictionRow key={p.horizon_min} p={p} />)}</div>
              {z.predictions[0] && <Reasons p={z.predictions[0]} />}
              <Link href={`/zones/${z.id}`} className="text-sky-300 underline">open zone detail →</Link>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
