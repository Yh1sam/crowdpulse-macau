import { describe, expect, it } from "vitest";
import { decodePlan, encodePlan } from "../src/core/plan";
import {
  applyEdits,
  DEFAULT_SETTINGS,
  findRoute,
  freshWorkspace,
  generatePeople,
  MODEL_VERSION,
  profileById,
} from "../src/core/model";
import type { Edit, MapData, Profile } from "../src/core/types";
import rawMap from "../src/data/macau.json";
import rawCrosswalk from "../../shared/sketchfuture_crosswalk.json";

const map = rawMap as MapData;
const crosswalk = rawCrosswalk as unknown as {
  map_version: string;
  model_version: string;
  zones: Record<string, { node: string | null }>;
  edges: Record<
    string,
    {
      from: string;
      to: string;
      close: string[];
      streets: string[];
      direct_m: number | null;
      detour_m: number | null;
      unsupported: string | null;
    }
  >;
};
const walk = profileById("walk");
const metres = (route: ReturnType<typeof findRoute>) =>
  route ? route.reduce((sum, step) => sum + step.edge.length, 0) : null;
const closures = (ids: string[]): Edit[] =>
  ids.map((edgeId) => ({ type: "close", edgeId }));
const routeBetween = (
  edits: Edit[],
  from: string,
  to: string,
  profile: Profile = walk,
) => findRoute(applyEdits(map, edits), from, to, profile, DEFAULT_SETTINGS);

describe("plans shared through the URL fragment", () => {
  const plan = {
    workspace: {
      ...freshWorkspace(map),
      title: "CrowdPulse #12：封閉板樟堂前地↔議事亭前地通道",
      edits: closures(["osm-192573684-4", "osm-713100572-1"]),
    },
    source: "CrowdPulse 建議 #12（Redirect part of southbound flow around Senado Square）",
  };
  it("round-trips a plan with Chinese text and shows its source", () => {
    const hash = `#plan=${encodePlan(plan)}`;
    expect(hash).toMatch(/^#plan=[A-Za-z0-9_-]+$/);
    expect(decodePlan(hash, map)).toEqual(plan);
    expect(decodePlan(`#x=1&plan=${encodePlan(plan)}`, map)).toEqual(plan);
  });
  it("ignores fragments without a plan", () => {
    expect(decodePlan("", map)).toBeNull();
    expect(decodePlan("#other=1", map)).toBeNull();
  });
  it("validates the plan like an imported file and leaves the saved plan alone", () => {
    expect(() => decodePlan("#plan=not-base64-json", map)).toThrow(
      /原有方案未被替換/,
    );
    expect(() =>
      decodePlan(`#plan=${encodePlan({ title: "x" } as never)}`, map),
    ).toThrow(/原有方案未被替換/);
    const otherMap = {
      ...plan,
      workspace: { ...plan.workspace, mapVersion: "another-map" },
    };
    expect(() => decodePlan(`#plan=${encodePlan(otherMap)}`, map)).toThrow(
      /街區不符/,
    );
    const unknownEdge = {
      ...plan,
      workspace: { ...plan.workspace, edits: closures(["osm-does-not-exist"]) },
    };
    expect(() => decodePlan(`#plan=${encodePlan(unknownEdge)}`, map)).toThrow(
      /通道不存在/,
    );
    expect(() => decodePlan(`#plan=${"A".repeat(20_001)}`, map)).toThrow(
      /太長/,
    );
  });
  it("trims and bounds the source label", () => {
    const long = { ...plan, source: `  x\u0000${"字".repeat(200)}` };
    const decoded = decodePlan(`#plan=${encodePlan(long)}`, map)!;
    expect(decoded.source).toHaveLength(120);
    expect(decoded.source!.startsWith("x ")).toBe(true);
    const unlabeled = decodePlan(
      `#plan=${encodePlan({ workspace: plan.workspace, source: 7 as never })}`,
      map,
    )!;
    expect(unlabeled).toEqual({ workspace: plan.workspace });
  });
});

describe("CrowdPulse crosswalk (shared/sketchfuture_crosswalk.json)", () => {
  const supported = Object.entries(crosswalk.edges).filter(
    ([, e]) => !e.unsupported,
  );
  it("is generated for this map and model", () => {
    expect(crosswalk.map_version).toBe(map.version);
    expect(crosswalk.model_version).toBe(MODEL_VERSION);
    expect(supported.length).toBeGreaterThanOrEqual(5);
    for (const [, e] of Object.entries(crosswalk.edges))
      if (e.unsupported) expect(e.close).toEqual([]);
  });
  it("names existing segments whose closure is a valid plan", () => {
    for (const [id, e] of supported) {
      const workspace = { ...freshWorkspace(map), title: id, edits: closures(e.close) };
      expect(decodePlan(`#plan=${encodePlan({ workspace })}`, map)).toEqual({
        workspace,
      });
      const names = e.close.map((c) => map.edges.find((x) => x.id === c)!.name);
      expect([...new Set(names)]).toEqual(e.streets);
    }
  });
  it("records the model's own direct and detour walking routes between the zones", () => {
    for (const [id, e] of supported) {
      const a = crosswalk.zones[e.from].node!,
        b = crosswalk.zones[e.to].node!;
      const direct = metres(routeBetween([], a, b))!;
      const detour = metres(routeBetween(closures(e.close), a, b))!;
      expect(Math.round(direct), id).toBe(e.direct_m);
      expect(Math.round(detour), id).toBe(e.detour_m);
      expect(detour, id).toBeGreaterThanOrEqual(direct * 1.3);
    }
  });
  it("changes at least one cohort route without stranding any walker", () => {
    const people = generatePeople(map, DEFAULT_SETTINGS);
    const pairs = [
      ...new Set(people.map((p) => `${p.origin}>${p.destination}`)),
    ].map((k) => k.split(">") as [string, string]);
    for (const [id, e] of supported) {
      let changed = 0;
      for (const [o, d] of pairs) {
        const before = routeBetween([], o, d)!.map((s) => s.edge.id);
        const after = routeBetween(closures(e.close), o, d);
        expect(after, `${id}: walkers ${o}→${d}`).not.toBeNull();
        if (after!.map((s) => s.edge.id).join() !== before.join()) changed++;
      }
      expect(changed, id).toBeGreaterThan(0);
    }
  });
});
