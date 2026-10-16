"use client";
import { useSyncExternalStore } from "react";

/**
 * The name of the person using this console ("Deciding as"). Every approve / reject / acknowledge sends it, and the
 * backend writes it to the audit log as the actor, so the log says who decided. The prototype has no login: the
 * name is self-declared and kept in this browser's localStorage (shared by the Alerts and Interventions pages and
 * across tabs). Every storage access is wrapped: when storage is unavailable (private window, blocked site data)
 * the name is kept in memory for this tab instead.
 */
export const OPERATOR_STORAGE_KEY = "crowdpulse.operatorName";
/** The backend's limit (DecisionIn.operator max_length). */
export const OPERATOR_NAME_MAX = 64;

// The name typed in this tab when it could not be written to storage; null while storage holds it.
let unsaved: string | null = null;
const listeners = new Set<() => void>();

function readStored(): string {
  try {
    return window.localStorage.getItem(OPERATOR_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

export function getOperatorName(): string {
  return unsaved ?? readStored();
}

export function setOperatorName(name: string): void {
  const value = name.slice(0, OPERATOR_NAME_MAX);
  try {
    window.localStorage.setItem(OPERATOR_STORAGE_KEY, value);
    unsaved = null;
  } catch {
    unsaved = value;
  }
  listeners.forEach((notify) => notify());
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  // another tab (or a capture script) changed the stored name
  const onStorage = (e: StorageEvent) => {
    if (e.key === null || e.key === OPERATOR_STORAGE_KEY) {
      unsaved = null;
      onChange();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(onChange);
    window.removeEventListener("storage", onStorage);
  };
}

/** Why this name cannot sign a decision, or null when it can. Mirrors the backend (DecisionIn), which refuses an
 * empty name, the old generic default "operator" and "system" (the actor of automatic audit entries) with HTTP 422,
 * in any case and with surrounding spaces ignored. */
export function operatorNameProblem(name: string): string | null {
  const n = name.trim();
  if (!n) return "Enter your name in “Deciding as” to decide.";
  if (n.toLowerCase() === "operator") return "“operator” is not a name: enter your own.";
  if (n.toLowerCase() === "system") return "“system” marks automatic log entries: enter your own name.";
  return null;
}

/** The current name, a setter, the trimmed name to send (null until a usable name is set) and the reason why not. */
export function useOperatorName() {
  // server render and hydration see no name; the stored one appears on the client right after
  const name = useSyncExternalStore(subscribe, getOperatorName, () => "");
  const problem = operatorNameProblem(name);
  return { name, setName: setOperatorName, signer: problem ? null : name.trim(), problem };
}
