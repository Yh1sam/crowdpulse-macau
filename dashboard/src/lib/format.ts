import type { CongestionClass } from "./types";

export const RISK_COLORS: Record<string, string> = { SAFE: "#0ca30c", WARNING: "#fab219", CRITICAL: "#d03b3b", UNKNOWN: "#9a9891" };
export const RISK_BG: Record<string, string> = { SAFE: "bg-emerald-600", WARNING: "bg-amber-500", CRITICAL: "bg-red-600", UNKNOWN: "bg-zinc-600" };

export function pct(x: number | null | undefined, digits = 0): string { return x == null ? "–" : `${(x * 100).toFixed(digits)}%`; }
export function num(x: number | null | undefined, digits = 2): string { return x == null || Number.isNaN(x) ? "–" : x.toFixed(digits); }
export function localTime(iso: string | null | undefined): string {
  if (!iso) return "–";
  const d = new Date(iso);
  return d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "Asia/Macau" });
}
export function localDateTime(iso: string | null | undefined): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("en-GB", { timeZone: "Asia/Macau", hour12: false });
}
export function compass(deg: number | null | undefined): string {
  if (deg == null || Number.isNaN(deg)) return "–";
  const dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"];
  return `${dirs[Math.round((deg % 360) / 45) % 8]} (${Math.round(deg)}°)`;
}
export function riskOrder(c: CongestionClass | "UNKNOWN" | null): number { return c === "CRITICAL" ? 3 : c === "WARNING" ? 2 : c === "SAFE" ? 1 : 0; }
