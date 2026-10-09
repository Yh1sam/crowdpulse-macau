import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SketchFutureCheck } from "@/components/SketchFutureCheck";
import { buildSketchFutureCheck, SKETCHFUTURE_SETTINGS } from "@/lib/sketchfuture";
import type { Intervention, SketchFutureCrosswalk } from "@/lib/types";

const crosswalk: SketchFutureCrosswalk = {
  map_version: "macau-osm-test-v1", model_version: "sf-route-queue-1.0", generated_by: "test", method: "test fixture",
  zones: {
    st_dominic: { node: "2031208643", place: "dominic", name_zh: "板樟堂前地" }, senado_square: { node: "6046966528", place: "senado", name_zh: "議事亭前地" },
    almeida_ribeiro: { node: null, place: null, name_zh: "新馬路" },
  },
  edges: {
    e_dominic_senado: { name: "Largo de S. Domingos link", from: "st_dominic", to: "senado_square", close: ["osm-192573684-4", "osm-713100572-1", "osm-192573684-1"], streets: ["議事亭前地"], direct_m: 125, detour_m: 216, unsupported: null },
    e_senado_almeida: { name: "Senado Square south exit", from: "senado_square", to: "almeida_ribeiro", close: [], streets: [], direct_m: null, detour_m: null, unsupported: "Avenida de Almeida Ribeiro is outside SketchFuture's pedestrian map" },
  },
};
const redirect: Intervention = {
  id: 12, zone_id: "senado_square", created_at: "2026-10-03T06:09:00Z", status: "pending", kind: "redirect_flow", title: "Redirect part of southbound flow around Senado Square",
  recommendation: "…", rationale: [], predicted_class: "CRITICAL", horizon_min: 10, confidence: 0.71, low_confidence: false,
  route: { from: "st_dominic", to: "almeida_ribeiro", via: ["st_dominic", "rua_sao_paulo", "tercena_corridor"], edges: ["Rua de S. Paulo (lower)", "Rua da Tercena west link", "Rua dos Ervanarios descent"], length_m: 610, has_stairs: false, steep: false, min_capacity_per_min: 120, accessibility_penalty: 0, score: 1 },
  route_alternatives: [], accessibility: { note: "Chosen route avoids stairs and steep sections." }, messages: {}, assumed_effect: { inflow_reduction: 0.3 }, projected_after: null,
  prediction_id: null, decided_at: null, decided_by: null, decision_note: null, effect_applied: false,
};
const decode = (url: string) => JSON.parse(Buffer.from(url.split("#plan=")[1], "base64url").toString("utf8"));

describe("SketchFuture plan from a redirect recommendation", () => {
  it("closes the corridor between the flow's source and the congested zone", () => {
    const check = buildSketchFutureCheck(redirect, crosswalk, "http://localhost:4173/");
    expect(check.ok).toBe(true);
    if (!check.ok) return;
    expect(check.plan.corridorId).toBe("e_dominic_senado");
    expect(check.plan.url).toMatch(/^http:\/\/localhost:4173\/#plan=[A-Za-z0-9_-]+$/);
    const payload = decode(check.plan.url);
    expect(payload.workspace).toEqual({
      version: 1, mapVersion: "macau-osm-test-v1", title: "CrowdPulse #12：封閉板樟堂前地↔議事亭前地通道",
      edits: [{ type: "close", edgeId: "osm-192573684-4" }, { type: "close", edgeId: "osm-713100572-1" }, { type: "close", edgeId: "osm-192573684-1" }],
      settings: SKETCHFUTURE_SETTINGS,
    });
    expect(payload.source).toBe("CrowdPulse 建議 #12（Redirect part of southbound flow around Senado Square）");
  });
  it("works whichever way round the corridor is stored", () => {
    const flipped = { ...redirect, zone_id: "st_dominic", route: { ...redirect.route!, from: "senado_square" } };
    const check = buildSketchFutureCheck(flipped, crosswalk);
    expect(check.ok && check.plan.corridorId).toBe("e_dominic_senado");
  });
  it("explains why a corridor outside SketchFuture's map cannot be checked", () => {
    const check = buildSketchFutureCheck({ ...redirect, route: { ...redirect.route!, from: "almeida_ribeiro" } }, crosswalk);
    expect(check).toEqual({ ok: false, reason: "Avenida de Almeida Ribeiro is outside SketchFuture's pedestrian map" });
    expect(buildSketchFutureCheck({ ...redirect, route: { ...redirect.route!, from: "ruins_st_paul" } }, crosswalk)).toEqual({ ok: false, reason: "no zone-graph corridor between ruins_st_paul and senado_square" });
    expect(buildSketchFutureCheck(redirect, undefined).ok).toBe(false);
  });
  it("is only offered for redirects", () => {
    expect(buildSketchFutureCheck({ ...redirect, kind: "deploy_staff", route: null }, crosswalk).ok).toBe(false);
  });
});

describe("SketchFuture card section", () => {
  it("renders the test button with the plan link and the model caveat", () => {
    render(<SketchFutureCheck iv={redirect} crosswalk={crosswalk} />);
    const link = screen.getByTestId("sketchfuture-link");
    expect(link).toHaveTextContent("TEST IN SKETCHFUTURE");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link.getAttribute("href")).toContain("/#plan=");
    expect(screen.getByTestId("sketchfuture-check")).toHaveTextContent("Largo de S. Domingos link corridor closed (議事亭前地, 3 segments)");
    expect(screen.getByTestId("sketchfuture-check")).toHaveTextContent("grows from 125 m to 216 m");
    expect(screen.getByTestId("sketchfuture-check")).toHaveTextContent("extreme case of the assumed 30% diversion");
  });
  it("says why a check is unavailable, and renders nothing for non-redirects", () => {
    const { rerender } = render(<SketchFutureCheck iv={{ ...redirect, route: { ...redirect.route!, from: "almeida_ribeiro" } }} crosswalk={crosswalk} />);
    expect(screen.getByTestId("sketchfuture-unavailable")).toHaveTextContent("outside SketchFuture's pedestrian map");
    rerender(<SketchFutureCheck iv={{ ...redirect, kind: "deploy_staff", route: null }} crosswalk={crosswalk} />);
    expect(screen.queryByTestId("sketchfuture-unavailable")).toBeNull();
    expect(screen.queryByTestId("sketchfuture-link")).toBeNull();
  });
});
