"use client";
import useSWR from "swr";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { ...init, headers: { "content-type": "application/json", ...(init?.headers ?? {}) } });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail ?? detail; } catch { /* ignore */ }
    throw new Error(`${res.status}: ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
  }
  return res.json() as Promise<T>;
}

const fetcher = <T,>(path: string) => apiFetch<T>(path);

/** Poll an endpoint; near-real-time updates without websockets. */
export function useApi<T>(path: string | null, refreshMs = 3000) {
  return useSWR<T>(path, fetcher, { refreshInterval: refreshMs, revalidateOnFocus: false, keepPreviousData: true });
}

export const post = <T,>(path: string, body?: unknown) => apiFetch<T>(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });
