import { afterEach, describe, expect, it, vi } from "vitest";
import {
  applyEdits,
  canUse,
  DEFAULT_SETTINGS,
  findRoute,
  freshWorkspace,
  nextGreen,
  PROFILES,
} from "../src/core/model";
import {
  compare,
  pairedTimes,
  simulate,
  sensitivity,
} from "../src/core/simulation";
import {
  parseWorkspace,
  reportCSV,
  reportJSON,
  loadWorkspace,
} from "../src/core/storage";
import { personPosition } from "../src/core/playback";
import type { Edge, MapData, Person } from "../src/core/types";
import rawMap from "../src/data/macau.json";

const actualMap = rawMap as MapData;
const nodes = ["a", "b", "c", "d"].map((id, i) => ({
  id,
  x: i * 10,
  y: 0,
  lon: i / 100,
  lat: 0,
}));
function edge(
  id: string,
  from: string,
  to: string,
  length: number,
  kind: Edge["kind"] = "path",
  capacity = 1,
): Edge {
  return {
    id,
    from,
    to,
    length,
    kind,
    points: nodes.filter((n) => n.id === from || n.id === to),
    name: id,
    width: 2,
    slope: 0,
    capacity,
    cycle: 0,
    green: 0,
    closed: false,
    assumption: true,
  };
}
const fixture: MapData = {
  version: "test-1",
  name: "test",
  timestamp: "2026-10-08",
  source: "test",
  nodes,
  edges: [
    edge("ab", "a", "b", 10),
    edge("stairs", "b", "d", 10, "steps"),
    edge("ac", "a", "c", 30),
    edge("cd", "c", "d", 30),
  ],
  places: [
    { id: "senado", name: "a", en: "a", node: "a", x: 0, y: 0 },
    { id: "ruins", name: "d", en: "d", node: "d", x: 30, y: 0 },
  ],
  buildings: [],
  context: [],
  width: 40,
  height: 40,
  metersPerUnit: 1,
};
const settings = {
  ...DEFAULT_SETTINGS,
  people: 9,
  releaseSeconds: 30,
  repeats: 3,
};
const person = (id: number, profile: Person["profile"] = "walk"): Person => ({
  id,
  profile,
  origin: "a",
  destination: "d",
  departure: 0,
  speedScale: 1,
});

describe("routing and queue mathematics", () => {
  it("uses a stairs shortcut only for profiles that permit it", () => {
    expect(
      findRoute(fixture.edges, "a", "d", PROFILES[0], settings)?.map(
        (s) => s.edge.id,
      ),
    ).toEqual(["ab", "stairs"]);
    for (const p of PROFILES.slice(1))
      expect(
        findRoute(fixture.edges, "a", "d", p, settings)?.map((s) => s.edge.id),
      ).toEqual(["ac", "cd"]);
  });
  it("applies width, slope and closure rules rather than always choosing shortest distance", () => {
    expect(canUse({ ...fixture.edges[0], width: 1 }, PROFILES[1])).toBe(false);
    expect(canUse({ ...fixture.edges[0], slope: 6 }, PROFILES[1])).toBe(false);
    expect(canUse({ ...fixture.edges[0], closed: true }, PROFILES[0])).toBe(
      false,
    );
    expect(findRoute(fixture.edges, "a", "a", PROFILES[0], settings)).toEqual(
      [],
    );
  });
  it("matches hand-calculated FIFO waits and traversal times", () => {
    const map = { ...fixture, edges: [edge("ad", "a", "d", 130, "path", 0.5)] };
    const run = simulate(
      map,
      map.edges,
      settings,
      Array.from({ length: 10 }, (_, i) => person(i)),
    );
    expect(run.journeys.map((j) => j.wait)).toEqual([
      0, 2, 4, 6, 8, 10, 12, 14, 16, 18,
    ]);
    expect(run.profiles.walk.meanWait).toBe(9);
    expect(run.profiles.walk.meanTime).toBe(109);
    expect(run.queues.ad.max).toBe(9);
  });
  it("reports an inaccessible destination as unreachable instead of teleporting", () => {
    const edges = [edge("stairs", "a", "d", 20, "steps")];
    const run = simulate(fixture, edges, settings, [person(0, "wheelchair")]);
    expect(run.journeys[0].status).toBe("unreachable");
    expect(run.journeys[0].segments).toEqual([]);
    expect(run.profiles.wheelchair.meanTime).toBeNull();
  });
  it("keeps unfinished trips separate when the time horizon expires", () => {
    const edges = [edge("long", "a", "d", 1000)];
    const run = simulate(fixture, edges, { ...settings, horizon: 300 }, [
      person(0),
    ]);
    expect(run.profiles.walk).toMatchObject({
      people: 1,
      arrived: 0,
      unfinished: 1,
      unreachable: 0,
      meanTime: null,
    });
  });
  it("respects signal cycles exactly at the green boundary", () => {
    const crossing = { ...fixture.edges[0], cycle: 40, green: 10 };
    expect(nextGreen(9.5, crossing)).toBe(9.5);
    expect(nextGreen(10, crossing)).toBe(40);
    expect(nextGreen(50, crossing)).toBe(80);
  });
  it("reverses curved geometry when a person travels against the stored edge direction", () => {
    const curve = {
      ...edge("curve", "a", "d", 20),
      points: [
        { x: 0, y: 0 },
        { x: 10, y: 0 },
        { x: 10, y: 10 },
      ],
    };
    const run = simulate(fixture, [curve], settings, [
      { ...person(0), origin: "d", destination: "a" },
    ]);
    const halfway = run.journeys[0].segments[0].end / 2;
    expect(
      personPosition(
        run.journeys[0],
        halfway,
        fixture,
        new Map([["curve", curve]]),
      ),
    ).toMatchObject({ x: 10, y: 0 });
  });
});

describe("counterfactuals and actual map", () => {
  it("gives exactly identical results when the proposal is unchanged", () => {
    const result = compare(actualMap, [], { ...settings, people: 60 });
    expect(result.baseline).toEqual(result.proposal);
    for (const p of PROFILES) expect(result.ranges[p.id].delta).toEqual([0, 0]);
  });
  it("can show a genuine model tradeoff: a ramp helps wheels but slows the stair shortcut", () => {
    const edited = applyEdits(fixture, [
      { type: "ramp", edgeId: "stairs", slope: 4 },
    ]);
    const cohort = [person(0), person(1, "wheelchair"), person(2, "stroller")];
    const before = simulate(fixture, fixture.edges, settings, cohort);
    const after = simulate(fixture, edited, settings, cohort);
    expect(after.profiles.walk.meanTime!).toBeGreaterThan(
      before.profiles.walk.meanTime!,
    );
    expect(after.profiles.wheelchair.meanTime!).toBeLessThan(
      before.profiles.wheelchair.meanTime!,
    );
    expect(fixture.edges[1].kind).toBe("steps");
  });
  it("conserves every generated person in each profile across edits and repeated seeds", () => {
    const stairs = actualMap.edges.find((e) => e.osmId === 670357826)!;
    const edits = [{ type: "ramp" as const, edgeId: stairs.id, slope: 4 }];
    const result = compare(actualMap, edits, { ...settings, people: 120 });
    expect(
      result.baseline.journeys.map((j) => [
        j.id,
        j.profile,
        j.origin,
        j.destination,
        j.departure,
        j.speedScale,
      ]),
    ).toEqual(
      result.proposal.journeys.map((j) => [
        j.id,
        j.profile,
        j.origin,
        j.destination,
        j.departure,
        j.speedScale,
      ]),
    );
    for (const run of [result.baseline, result.proposal]) {
      expect(run.journeys).toHaveLength(120);
      for (const p of PROFILES) {
        const m = run.profiles[p.id];
        expect(m.arrived + m.unfinished + m.unreachable).toBe(m.people);
        for (const j of run.journeys.filter((j) => j.profile === p.id)) {
          expect(j.wait).toBeGreaterThanOrEqual(0);
          for (const segment of j.segments)
            expect(segment.start).toBeGreaterThanOrEqual(segment.queuedAt);
          for (const segment of j.segments)
            expect(segment.end).toBeGreaterThan(segment.start);
        }
      }
    }
  });
  it("provides nine reproducible sensitivity scenarios", () => {
    const rows = sensitivity(fixture, [], settings);
    expect(rows).toHaveLength(9);
    expect(rows).toEqual(sensitivity(fixture, [], settings));
    for (const row of rows)
      for (const p of PROFILES) expect(row.profiles[p.id].delta).toBe(0);
  });
  it("uses source coordinates and only connected, positive-length edges", () => {
    const ids = new Set(actualMap.nodes.map((n) => n.id));
    expect(actualMap.nodes.length).toBeGreaterThan(100);
    for (const e of actualMap.edges) {
      expect(ids.has(e.from) && ids.has(e.to)).toBe(true);
      expect(e.length).toBeGreaterThan(0);
      expect(e.capacity).toBeGreaterThan(0);
      expect(e.osmId).toBeTypeOf("number");
    }
    for (const p of actualMap.places) expect(ids.has(p.node)).toBe(true);
  });
  it("does not mistake newly reachable people for a slowdown among existing trips", () => {
    const baselineEdges = [edge("only-stairs", "a", "d", 20, "steps")];
    const afterEdges = [edge("flat", "a", "d", 20)];
    const cohort = [
      person(0, "wheelchair"),
      { ...person(1, "wheelchair"), origin: "d" },
    ];
    const before = simulate(fixture, baselineEdges, settings, cohort);
    const after = simulate(fixture, afterEdges, settings, cohort);
    expect(before.profiles.wheelchair.arrived).toBe(1);
    expect(after.profiles.wheelchair.arrived).toBe(2);
    expect(after.profiles.wheelchair.meanTime!).toBeGreaterThan(
      before.profiles.wheelchair.meanTime!,
    );
    expect(pairedTimes(before, after, "wheelchair")).toMatchObject({
      count: 1,
      delta: 0,
    });
  });
});

describe("saved plans and inspectable reports", () => {
  afterEach(() => vi.unstubAllGlobals());
  it("preserves corrupt browser data while offering a fresh in-memory workspace", () => {
    const raw = "{corrupt";
    const getItem = vi.fn(() => raw),
      setItem = vi.fn();
    vi.stubGlobal("localStorage", { getItem, setItem });
    const loaded = loadWorkspace(fixture);
    expect(loaded.original).toBe(raw);
    expect(loaded.error).toBeTruthy();
    expect(loaded.workspace).toEqual(freshWorkspace(fixture));
    expect(setItem).not.toHaveBeenCalled();
  });
  it("remains usable in memory when browser storage is unavailable", () => {
    vi.stubGlobal("localStorage", {
      getItem() {
        throw new Error("storage unavailable");
      },
    });
    expect(loadWorkspace(fixture)).toMatchObject({
      workspace: freshWorkspace(fixture),
      error: "storage unavailable",
    });
  });
  it("round trips a plan and retains results after export/import/recompute", () => {
    const w = freshWorkspace(fixture);
    w.edits = [{ type: "ramp", edgeId: "stairs", slope: 4 }];
    const restored = parseWorkspace(JSON.stringify(w), fixture);
    expect(restored).toEqual(w);
    expect(compare(fixture, restored.edits, restored.settings)).toEqual(
      compare(fixture, w.edits, w.settings),
    );
  });
  it("rejects corrupt data, wrong map, impossible widths and duplicate connections", () => {
    const w = freshWorkspace(fixture);
    expect(() => parseWorkspace("broken", fixture)).toThrow();
    expect(() =>
      parseWorkspace(JSON.stringify({ ...w, mapVersion: "wrong" }), fixture),
    ).toThrow();
    expect(() =>
      parseWorkspace(
        JSON.stringify({ ...w, settings: { ...w.settings, people: -1 } }),
        fixture,
      ),
    ).toThrow();
    expect(() =>
      parseWorkspace(
        JSON.stringify({
          ...w,
          edits: [
            {
              type: "link",
              id: "link-test",
              from: "a",
              to: "b",
              width: 2,
              slope: 0,
            },
          ],
        }),
        fixture,
      ),
    ).toThrow();
    expect(() =>
      parseWorkspace(
        JSON.stringify({
          ...w,
          edits: [
            {
              type: "link",
              id: "link-test",
              from: "a",
              to: "d",
              width: -2,
              slope: 0,
            },
          ],
        }),
        fixture,
      ),
    ).toThrow();
  });
  it("rejects an arbitrary street becoming a ramp or a repeated ramp multiplier", () => {
    const w = freshWorkspace(fixture);
    expect(() =>
      parseWorkspace(
        JSON.stringify({
          ...w,
          edits: [{ type: "ramp", edgeId: "ab", slope: 4 }],
        }),
        fixture,
      ),
    ).toThrow();
    expect(() =>
      parseWorkspace(
        JSON.stringify({
          ...w,
          edits: [
            { type: "ramp", edgeId: "stairs", slope: 4 },
            { type: "ramp", edgeId: "stairs", slope: 4 },
          ],
        }),
        fixture,
      ),
    ).toThrow();
  });
  it("exports source, assumptions and denominators with real computed values", () => {
    const w = freshWorkspace(fixture),
      result = compare(fixture, [], w.settings);
    const report = JSON.parse(reportJSON(fixture, w, result));
    expect(report.map.source).toBe("test");
    expect(report.results.baseline).toEqual(result.baseline);
    expect(report.assumptions.routing).toContain("改道");
    expect(reportCSV(result).split("\n")).toHaveLength(7);
  });
});
