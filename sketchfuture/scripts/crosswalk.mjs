// Derives shared/sketchfuture_crosswalk.json: for each corridor of CrowdPulse's zone graph
// (shared/zones.json), the smallest set of SketchFuture street segments whose closure forces
// a detour between the two zones. CrowdPulse's intervention cards use it to open a
// SketchFuture plan that closes the corridor a recommendation redirects people away from.
//
// Method: both zones are pinned to an OSM node of SketchFuture's map; the shortest walking
// route between them (the model's own findRoute) is cut by closing, one at a time, the route
// segment nearest to a hand-picked boundary junction (longest first on ties), until the walking route is at least
// 30% longer than the direct one. Corridors that leave SketchFuture's pedestrian map
// (Avenida de Almeida Ribeiro) are recorded as unsupported.
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";
import ts from "typescript";

const root = path.resolve(import.meta.dirname, "..");
const map = JSON.parse(
  await fs.readFile(path.join(root, "src/data/macau.json"), "utf8"),
);
const zoneGraph = JSON.parse(
  await fs.readFile(path.join(root, "../shared/zones.json"), "utf8"),
);
const temporary = await fs.mkdtemp(
  path.join(os.tmpdir(), "sketchfuture-core-"),
);
const output = path.join(root, "../shared/sketchfuture_crosswalk.json");

// CrowdPulse zone -> SketchFuture node (and the landmark SketchFuture's cohort uses, if any).
const ZONES = {
  ruins_st_paul: { node: "7621468858", place: "ruins", name_zh: "大三巴牌坊" },
  jesus_square: { node: "4533665334", place: null, name_zh: "耶穌會紀念廣場" },
  rua_sao_paulo: { node: "8995121711", place: null, name_zh: "大三巴街" },
  st_dominic: { node: "2031208643", place: "dominic", name_zh: "板樟堂前地" },
  senado_square: { node: "6046966528", place: "senado", name_zh: "議事亭前地" },
  almeida_ribeiro: { node: null, place: null, name_zh: "新馬路（亞美打利庇盧大馬路）" },
  tercena_corridor: { node: "5685822408", place: "tercena", name_zh: "果欄街一帶" },
};
// Boundary junction between the two zones of each CrowdPulse corridor, and how far from it
// (metres) a route segment may be to count as part of the corridor.
const BOUNDARIES = {
  e_ruins_jesus: { node: "6277726350", reach: 45 }, // top of St. Paul's steps
  e_jesus_ruasp: { node: "2027483940", reach: 45 }, // top of Rua de S. Paulo at Travessa de S. Paulo
  e_ruasp_dominic: { node: "3120822020", reach: 45 }, // Rua de S. Domingos enters Largo de S. Domingos
  e_dominic_senado: { node: "2027483937", reach: 45 }, // Largo de S. Domingos meets Largo do Senado
  e_ruasp_tercena: { node: "8988059606", reach: 45 }, // Rua de Pedro Nolasco da Silva lane at Rua da Tercena
};
const UNSUPPORTED = "Avenida de Almeida Ribeiro is outside SketchFuture's pedestrian map (no crossing of the avenue is mapped).";
const DETOUR_FACTOR = 1.3;

try {
  for (const file of ["model"]) {
    const source = await fs.readFile(
      path.join(root, "src/core", `${file}.ts`),
      "utf8",
    );
    const code = ts.transpileModule(source, {
      compilerOptions: {
        target: ts.ScriptTarget.ES2022,
        module: ts.ModuleKind.ESNext,
      },
    }).outputText;
    await fs.writeFile(path.join(temporary, `${file}.mjs`), code);
  }
  const { DEFAULT_SETTINGS, applyEdits, findRoute, PROFILES } = await import(
    pathToFileURL(path.join(temporary, "model.mjs"))
  );
  const walk = PROFILES.find((p) => p.id === "walk");
  const nodes = new Map(map.nodes.map((n) => [n.id, n]));
  const metres = (route) =>
    route ? route.reduce((sum, step) => sum + step.edge.length, 0) : null;
  // distance (m) from a point to a segment of the edge's polyline
  const distance = (edge, p) => {
    let best = Infinity;
    const pts = edge.points.length >= 2 ? edge.points : [nodes.get(edge.from), nodes.get(edge.to)];
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
      const dx = b.x - a.x, dy = b.y - a.y, l2 = dx * dx + dy * dy;
      const t = l2 ? Math.max(0, Math.min(1, ((p.x - a.x) * dx + (p.y - a.y) * dy) / l2)) : 0;
      best = Math.min(best, Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy)));
    }
    return best * map.metersPerUnit;
  };

  const edges = {};
  for (const corridor of zoneGraph.edges) {
    const entry = {
      name: corridor.name,
      from: corridor.from,
      to: corridor.to,
      close: [],
      streets: [],
      direct_m: null,
      detour_m: null,
      unsupported: null,
    };
    edges[corridor.id] = entry;
    const a = ZONES[corridor.from].node,
      b = ZONES[corridor.to].node,
      boundary = BOUNDARIES[corridor.id];
    if (!a || !b || !boundary) {
      entry.unsupported = UNSUPPORTED;
      continue;
    }
    const anchor = nodes.get(boundary.node);
    const direct = findRoute(applyEdits(map, []), a, b, walk, DEFAULT_SETTINGS);
    entry.direct_m = Math.round(metres(direct));
    const edits = [];
    for (;;) {
      const route = findRoute(applyEdits(map, edits), a, b, walk, DEFAULT_SETTINGS);
      if (!route) {
        entry.unsupported = `closing the corridor would leave no walking route between the zones (${edits.map((e) => e.edgeId).join(", ")})`;
        break;
      }
      if (metres(route) >= entry.direct_m * DETOUR_FACTOR) {
        entry.close = edits.map((e) => e.edgeId);
        entry.streets = [...new Set(edits.map((e) => map.edges.find((x) => x.id === e.edgeId).name))];
        entry.detour_m = Math.round(metres(route));
        break;
      }
      const candidate = route
        .map((step) => ({ edge: step.edge, d: distance(step.edge, anchor) }))
        .filter((c) => c.d <= boundary.reach && !edits.some((e) => e.edgeId === c.edge.id))
        .sort((x, y) => x.d - y.d || y.edge.length - x.edge.length)[0];
      if (!candidate || edits.length >= 8) {
        entry.unsupported = `no compact closure near the boundary junction (${edits.map((e) => e.edgeId).join(", ")})`;
        break;
      }
      edits.push({ type: "close", edgeId: candidate.edge.id });
    }
    if (entry.unsupported) {
      entry.close = [];
      entry.streets = [];
    }
    console.log(
      `${corridor.id} (${corridor.name}): ${entry.unsupported ? "unsupported — " + entry.unsupported : `direct ${entry.direct_m} m → detour ${entry.detour_m} m, close ${entry.close.length}: ${entry.close.join(", ")} [${entry.streets.join("、")}]`}`,
    );
  }
  const crosswalk = {
    map_version: map.version,
    model_version: (await import(pathToFileURL(path.join(temporary, "model.mjs")))).MODEL_VERSION,
    generated_by: "sketchfuture/scripts/crosswalk.mjs",
    method:
      "Each CrowdPulse corridor is cut by closing the SketchFuture street segments nearest to a hand-picked boundary junction, one at a time along the current shortest walking route, until that route is at least 30% longer than the direct one. direct_m and detour_m are the model's shortest walking routes between the two zones' representative nodes before and after the closure. Closing a corridor is the extreme case (100% diversion) of CrowdPulse's assumed partial redirect.",
    zones: ZONES,
    edges,
  };
  await fs.writeFile(output, JSON.stringify(crosswalk, null, 2) + "\n");
  console.log(`wrote ${path.relative(process.cwd(), output)}`);
} finally {
  await fs.rm(temporary, { recursive: true, force: true });
}
