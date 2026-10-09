import type { MapData, Workspace } from "./types";
import { parseWorkspace } from "./storage";

/**
 * A plan handed over by another app in the URL fragment, `#plan=<base64url JSON>`.
 * CrowdPulse's intervention cards use it to open the corridor closure a recommendation
 * implies. The workspace is validated exactly like an imported file; `source` is only shown.
 */
export type SharedPlan = { workspace: Workspace; source?: string };
export const PLAN_PARAM = "plan";
const MAX_PLAN_CHARS = 20_000;
const MAX_SOURCE_CHARS = 120;
const UNREADABLE = "連結中的方案無法讀取，原有方案未被替換。";

function toBase64Url(bytes: Uint8Array): string {
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x2000)
    binary += String.fromCharCode(...bytes.subarray(i, i + 0x2000));
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}
function fromBase64Url(text: string): Uint8Array {
  const padded = text
    .replace(/-/g, "+")
    .replace(/_/g, "/")
    .padEnd(Math.ceil(text.length / 4) * 4, "=");
  return Uint8Array.from(atob(padded), (c) => c.charCodeAt(0));
}

export function encodePlan(plan: SharedPlan): string {
  return toBase64Url(new TextEncoder().encode(JSON.stringify(plan)));
}

/** Returns null when the fragment carries no plan; throws when it carries an invalid one. */
export function decodePlan(hash: string, map: MapData): SharedPlan | null {
  const encoded = new URLSearchParams(hash.replace(/^#/, "")).get(PLAN_PARAM);
  if (!encoded) return null;
  if (encoded.length > MAX_PLAN_CHARS)
    throw new Error("連結中的方案太長，未被載入。");
  let value: Record<string, unknown>;
  try {
    value = JSON.parse(
      new TextDecoder().decode(fromBase64Url(encoded)),
    ) as Record<string, unknown>;
  } catch {
    throw new Error(UNREADABLE);
  }
  if (!value || typeof value !== "object" || !value.workspace)
    throw new Error(UNREADABLE);
  const workspace = parseWorkspace(JSON.stringify(value.workspace), map);
  const source =
    typeof value.source === "string"
      ? value.source
          .replace(/[\u0000-\u001f\u007f]/g, " ")
          .trim()
          .slice(0, MAX_SOURCE_CHARS)
      : "";
  return source ? { workspace, source } : { workspace };
}
