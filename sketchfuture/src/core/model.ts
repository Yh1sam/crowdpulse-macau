import type {
  Edge,
  Edit,
  MapData,
  Person,
  Profile,
  ProfileId,
  Settings,
  Workspace,
} from "./types";

export const MODEL_VERSION = "sf-route-queue-1.0";
export const PROFILES: Profile[] = [
  {
    id: "walk",
    name: "一般行人",
    short: "步行",
    color: "#247c76",
    speed: 1.3,
    minWidth: 0.7,
    maxSlope: 18,
    steps: true,
  },
  {
    id: "wheelchair",
    name: "輪椅使用者",
    short: "輪椅",
    color: "#7658b5",
    speed: 0.9,
    minWidth: 1.2,
    maxSlope: 5,
    steps: false,
  },
  {
    id: "stroller",
    name: "推嬰兒車者",
    short: "嬰兒車",
    color: "#ce6744",
    speed: 1.05,
    minWidth: 1,
    maxSlope: 8,
    steps: false,
  },
];
export const DEFAULT_SETTINGS: Settings = {
  people: 120,
  releaseSeconds: 120,
  speedFactor: 1,
  capacityFactor: 1,
  seed: 42,
  repeats: 5,
  horizon: 1800,
};
export function freshWorkspace(map: MapData): Workspace {
  return {
    version: 1,
    mapVersion: map.version,
    title: "我的街區方案",
    edits: [],
    settings: { ...DEFAULT_SETTINGS },
  };
}

export function applyEdits(map: MapData, edits: Edit[]): Edge[] {
  const edges = map.edges.map((e) => ({ ...e }));
  for (const edit of edits) {
    if (edit.type === "link") {
      const a = map.nodes.find((n) => n.id === edit.from);
      const b = map.nodes.find((n) => n.id === edit.to);
      if (!a || !b || a.id === b.id) continue;
      edges.push({
        id: edit.id,
        from: a.id,
        to: b.id,
        length: Math.hypot(a.x - b.x, a.y - b.y) * map.metersPerUnit,
        points: [
          { x: a.x, y: a.y },
          { x: b.x, y: b.y },
        ],
        kind: "path",
        name: "構想步行連接",
        width: edit.width,
        slope: edit.slope,
        capacity: edit.width * 0.55,
        cycle: 0,
        green: 0,
        closed: false,
        proposed: true,
        assumption: true,
      });
    } else {
      const edge = edges.find((e) => e.id === edit.edgeId);
      if (!edge) continue;
      if (edit.type === "close") edge.closed = !edge.closed;
      else {
        edge.kind = "ramp";
        edge.slope = edit.slope;
        edge.width = Math.max(1.5, edit.width ?? edge.width);
        edge.length *= 1.8;
        edge.capacity = edge.width * 0.55;
        edge.proposed = true;
        edge.assumption = true;
      }
    }
  }
  return edges;
}

export function canUse(edge: Edge, profile: Profile): boolean {
  return (
    !edge.closed &&
    (profile.steps || edge.kind !== "steps") &&
    edge.width >= profile.minWidth &&
    (edge.slope ?? 0) <= profile.maxSlope
  );
}
export function travelSeconds(
  edge: Edge,
  profile: Profile,
  speedScale: number,
  settings: Settings,
): number {
  const terrain =
    edge.kind === "steps"
      ? 0.65
      : Math.max(0.55, 1 - (edge.slope ?? 0) * 0.035);
  return (
    edge.length / (profile.speed * speedScale * settings.speedFactor * terrain)
  );
}
export function nextGreen(time: number, edge: Edge): number {
  if (edge.cycle <= 0 || edge.green >= edge.cycle) return time;
  const phase = ((time % edge.cycle) + edge.cycle) % edge.cycle;
  return phase < edge.green ? time : time + edge.cycle - phase;
}

export class MinHeap<T> {
  private items: T[] = [];
  constructor(private compare: (a: T, b: T) => number) {}
  get size() {
    return this.items.length;
  }
  push(item: T) {
    this.items.push(item);
    let index = this.items.length - 1;
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(this.items[parent], item) <= 0) break;
      this.items[index] = this.items[parent];
      index = parent;
    }
    this.items[index] = item;
  }
  pop(): T | undefined {
    const first = this.items[0];
    const last = this.items.pop();
    if (!this.items.length || last === undefined) return first;
    let index = 0;
    while (index * 2 + 1 < this.items.length) {
      let child = index * 2 + 1;
      if (
        child + 1 < this.items.length &&
        this.compare(this.items[child + 1], this.items[child]) < 0
      )
        child++;
      if (this.compare(last, this.items[child]) <= 0) break;
      this.items[index] = this.items[child];
      index = child;
    }
    this.items[index] = last;
    return first;
  }
}

export type RouteStep = { edge: Edge; from: string; to: string };
export function findRoute(
  edges: Edge[],
  from: string,
  to: string,
  profile: Profile,
  settings: Settings,
): RouteStep[] | null {
  if (from === to) return [];
  const adjacency = new Map<string, RouteStep[]>();
  for (const edge of edges) {
    if (!canUse(edge, profile)) continue;
    for (const [a, b] of [
      [edge.from, edge.to],
      [edge.to, edge.from],
    ]) {
      const list = adjacency.get(a) ?? [];
      list.push({ edge, from: a, to: b });
      adjacency.set(a, list);
    }
  }
  const distances = new Map([[from, 0]]);
  const previous = new Map<string, RouteStep>();
  const pending = new MinHeap<{ node: string; cost: number }>(
    (a, b) => a.cost - b.cost,
  );
  pending.push({ node: from, cost: 0 });
  while (pending.size) {
    const current = pending.pop()!;
    if (current.cost !== distances.get(current.node)) continue;
    if (current.node === to) {
      const steps: RouteStep[] = [];
      let node = to;
      while (node !== from) {
        const step = previous.get(node)!;
        steps.unshift(step);
        node = step.from;
      }
      return steps;
    }
    for (const step of adjacency.get(current.node) ?? []) {
      const closedSeconds = Math.max(0, step.edge.cycle - step.edge.green);
      const expectedWait =
        step.edge.cycle > 0 ? closedSeconds ** 2 / (2 * step.edge.cycle) : 0;
      const cost =
        current.cost +
        travelSeconds(step.edge, profile, 1, settings) +
        expectedWait;
      if (cost < (distances.get(step.to) ?? Infinity)) {
        distances.set(step.to, cost);
        previous.set(step.to, step);
        pending.push({ node: step.to, cost });
      }
    }
  }
  return null;
}

export function random(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state += 0x6d2b79f5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export function generatePeople(
  map: MapData,
  settings: Settings,
  seed = settings.seed,
): Person[] {
  const rng = random(seed);
  const sources = map.places.filter((p) =>
    ["senado", "dominic", "tercena"].includes(p.id),
  );
  const targets = map.places.filter((p) =>
    ["ruins", "museum", "senado"].includes(p.id),
  );
  if (!sources.length || !targets.length)
    throw new Error("街區缺少出發地或目的地。");
  return Array.from({ length: settings.people }, (_, id) => {
    const origin = sources[Math.floor(rng() * sources.length)];
    const candidates = targets.filter((p) => p.node !== origin.node);
    const destination = candidates[Math.floor(rng() * candidates.length)];
    return {
      id,
      profile: PROFILES[id % 3].id,
      origin: origin.node,
      destination: destination.node,
      departure: rng() * settings.releaseSeconds,
      speedScale: 0.9 + rng() * 0.2,
    };
  }).sort((a, b) => a.departure - b.departure);
}

export function profileById(id: ProfileId): Profile {
  return PROFILES.find((p) => p.id === id)!;
}
