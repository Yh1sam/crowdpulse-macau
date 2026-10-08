import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import ts from "typescript";

const root = path.resolve(import.meta.dirname, "..");
const temporary = await fs.mkdtemp(
  path.join(os.tmpdir(), "sketchfuture-core-"),
);
try {
  for (const file of ["model", "simulation"]) {
    const source = await fs.readFile(
      path.join(root, "src/core", `${file}.ts`),
      "utf8",
    );
    const code = ts
      .transpileModule(source, {
        compilerOptions: {
          target: ts.ScriptTarget.ES2022,
          module: ts.ModuleKind.ESNext,
        },
      })
      .outputText.replace(/from ["']\.\/model["']/g, 'from "./model.mjs"');
    await fs.writeFile(path.join(temporary, `${file}.mjs`), code);
  }
  const { DEFAULT_SETTINGS, applyEdits, findRoute, PROFILES } = await import(
    pathToFileURL(path.join(temporary, "model.mjs"))
  );
  const { compare, sensitivity } = await import(
    pathToFileURL(path.join(temporary, "simulation.mjs"))
  );
  const map = JSON.parse(
    await fs.readFile(path.join(root, "src/data/macau.json"), "utf8"),
  );
  const stairs = map.edges.find((e) => e.osmId === 670357826);
  const reference = compare(map, [], {...DEFAULT_SETTINGS, repeats: 1});
  const cases = {
    unchanged: [],
    ramp: [{ type: "ramp", edgeId: stairs.id, slope: 4 }],
    shortcut: [
      {
        type: "link",
        id: "link-benchmark",
        from: stairs.from,
        to: map.places.find((p) => p.id === "ruins").node,
        width: 2,
        slope: 4,
      },
    ],
    closure: [
      {
        type: "close",
        edgeId: map.edges
          .filter((e) => e.name === "大三巴街")
          .sort((a, b) => reference.baseline.queues[b.id].entries - reference.baseline.queues[a.id].entries || b.length - a.length)[0].id,
      },
    ],
  };
  const measurements = [];
  for (const people of [30, 120, 300])
    for (const [name, edits] of Object.entries(cases)) {
      const start = performance.now();
      const result = compare(map, edits, {
        ...DEFAULT_SETTINGS,
        people,
        repeats: 5,
      });
      for (const run of [result.baseline, result.proposal])
        for (const profile of PROFILES) {
          const metric = run.profiles[profile.id];
          if (
            metric.people !==
            metric.arrived + metric.unfinished + metric.unreachable
          )
            throw new Error("Person conservation failed");
        }
      if (
        name === "unchanged" &&
        JSON.stringify(result.baseline) !== JSON.stringify(result.proposal)
      )
        throw new Error("Unchanged proposal differs");
      measurements.push({
        people,
        name,
        milliseconds: Math.round(performance.now() - start),
        profiles: result.proposal.profiles,
        paired: result.paired,
      });
    }
  const start = performance.now();
  const sensitivityResults = sensitivity(map, cases.ramp, DEFAULT_SETTINGS);
  const source = map.places.find((p) => p.id === "senado").node;
  const target = map.places.find((p) => p.id === "ruins").node;
  const route = findRoute(
    map.edges,
    source,
    target,
    PROFILES[0],
    DEFAULT_SETTINGS,
  );
  const report = {
    generatedAt: new Date().toISOString(),
    mapVersion: map.version,
    assumptions:
      "Model verification only; no measured Macau pedestrian demand or accessibility survey.",
    measurements,
    sensitivityMilliseconds: Math.round(performance.now() - start),
    sensitivityResults,
    exampleRouteRestrictions: route
      .filter(
        (step) =>
          !PROFILES.every(
            (p) =>
              !(!p.steps && step.edge.kind === "steps") &&
              step.edge.width >= p.minWidth,
          ),
      )
      .map((step) => ({
        id: step.edge.id,
        name: step.edge.name,
        kind: step.edge.kind,
        width: step.edge.width,
      })),
    proposalEdgeCount: applyEdits(map, cases.ramp).length,
    debugRoutes: PROFILES.map((p) => ({
      profile: p.id,
      before: findRoute(map.edges, source, target, p, DEFAULT_SETTINGS)?.map(
        (s) => ({ id: s.edge.id, kind: s.edge.kind, width: s.edge.width }),
      ),
      after: findRoute(
        applyEdits(map, cases.ramp),
        source,
        target,
        p,
        DEFAULT_SETTINGS,
      )?.map((s) => ({
        id: s.edge.id,
        kind: s.edge.kind,
        width: s.edge.width,
      })),
    })),
  };
  await fs.mkdir(path.join(root, "artifacts"), { recursive: true });
  await fs.writeFile(
    path.join(root, "artifacts/benchmark.json"),
    JSON.stringify(report, null, 2),
  );
  console.log(
    JSON.stringify(
      {
        cases: measurements.length,
        maxMilliseconds: Math.max(...measurements.map((m) => m.milliseconds)),
        sensitivityMilliseconds: report.sensitivityMilliseconds,
        restrictions: report.exampleRouteRestrictions,
      },
      null,
      2,
    ),
  );
} finally {
  await fs.rm(temporary, { recursive: true, force: true });
}
