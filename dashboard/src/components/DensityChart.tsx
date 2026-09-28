"use client";
import { Area, AreaChart, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend } from "recharts";
import type { Config, Prediction, ZoneState } from "@/lib/types";
import { localTime } from "@/lib/format";

export function DensityChart({ history, predictions, config, height = 260 }: { history: ZoneState[]; predictions?: Prediction[]; config?: Config; height?: number }) {
  const data = history.map((h) => ({ t: new Date(h.bin_start).getTime(), density: +h.density.toFixed(3), reliability: +h.reliability.toFixed(2), speed: +h.flow_speed_mps.toFixed(2) }));
  const last = data[data.length - 1];
  const fut = (predictions ?? []).filter((p) => p.status === "ok" && p.predicted_density != null).map((p) => ({ t: new Date(p.target_time).getTime(), forecast: +(p.predicted_density as number).toFixed(3) }));
  const merged = [...data.map((d) => ({ ...d, forecast: undefined as number | undefined })), ...(last ? [{ t: last.t, forecast: last.density, density: undefined as number | undefined }] : []), ...fut].sort((a, b) => a.t - b.t);
  const th = config?.congestion_thresholds;
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={merged} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="#2a2a29" strokeDasharray="2 4" />
        <XAxis dataKey="t" type="number" domain={["dataMin", "dataMax"]} tickFormatter={(v) => localTime(new Date(v).toISOString())} stroke="#8a8984" fontSize={11} />
        <YAxis domain={[0, 1]} stroke="#8a8984" fontSize={11} />
        <Tooltip labelFormatter={(v) => localTime(new Date(Number(v)).toISOString())} contentStyle={{ background: "#1a1a19", border: "1px solid #3a3a38", fontSize: 12 }} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {th && <ReferenceLine y={th.warning} stroke="#fab219" strokeDasharray="3 3" label={{ value: "WARNING", fill: "#fab219", fontSize: 10, position: "insideTopLeft" }} />}
        {th && <ReferenceLine y={th.critical} stroke="#d03b3b" strokeDasharray="3 3" label={{ value: "CRITICAL", fill: "#d03b3b", fontSize: 10, position: "insideTopLeft" }} />}
        <Line type="monotone" dataKey="density" name="observed density index" stroke="#2a78d6" strokeWidth={2} dot={false} isAnimationActive={false} connectNulls={false} />
        <Line type="monotone" dataKey="forecast" name="model forecast (+5/+10/+15)" stroke="#eb6834" strokeWidth={2} strokeDasharray="6 4" dot={{ r: 4 }} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="reliability" name="sensor reliability" stroke="#1baf7a" strokeWidth={1} dot={false} isAnimationActive={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function ReliabilityArea({ history, height = 160 }: { history: ZoneState[]; height?: number }) {
  const data = history.map((h) => ({ t: new Date(h.bin_start).getTime(), reliability: +h.reliability.toFixed(2), obstructed: +h.obstructed_fraction.toFixed(2), sensors: h.n_sensors }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="#2a2a29" strokeDasharray="2 4" />
        <XAxis dataKey="t" type="number" domain={["dataMin", "dataMax"]} tickFormatter={(v) => localTime(new Date(v).toISOString())} stroke="#8a8984" fontSize={11} />
        <YAxis domain={[0, 1]} stroke="#8a8984" fontSize={11} />
        <Tooltip labelFormatter={(v) => localTime(new Date(Number(v)).toISOString())} contentStyle={{ background: "#1a1a19", border: "1px solid #3a3a38", fontSize: 12 }} />
        <Area type="monotone" dataKey="reliability" name="reliability" stroke="#1baf7a" fill="#1baf7a33" isAnimationActive={false} />
        <Area type="monotone" dataKey="obstructed" name="obstructed fraction" stroke="#e34948" fill="#e3494833" isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
