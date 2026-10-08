import type {
  Comparison,
  Edge,
  Edit,
  Journey,
  MapData,
  Metrics,
  Person,
  ProfileId,
  Run,
  Settings,
  SensitivityRow,
} from "./types";
import {
  applyEdits,
  findRoute,
  generatePeople,
  MinHeap,
  nextGreen,
  profileById,
  PROFILES,
  travelSeconds,
  type RouteStep,
} from "./model";

export function median(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b),
    middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}
const mean = (values: number[]) =>
  values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;

function summarize(journeys: Journey[]): Metrics {
  const arrived = journeys.filter((j) => j.status === "arrived");
  return {
    people: journeys.length,
    arrived: arrived.length,
    unreachable: journeys.filter((j) => j.status === "unreachable").length,
    unfinished: journeys.filter((j) => j.status === "unfinished").length,
    meanTime: mean(arrived.map((j) => j.arrivedAt! - j.departure)),
    medianTime: median(arrived.map((j) => j.arrivedAt! - j.departure)),
    meanWait: mean(arrived.map((j) => j.wait)),
    meanDistance: mean(arrived.map((j) => j.distance)),
  };
}

/** Event-driven FIFO entrance queues. No collision dynamics, vehicle model or adaptive rerouting. */
export function simulate(
  map: MapData,
  edges: Edge[],
  settings: Settings,
  people?: Person[],
  seed = settings.seed,
): Run {
  const cohort = people ?? generatePeople(map, settings, seed);
  const routes = new Map<string, RouteStep[] | null>();
  const journeys: Journey[] = cohort.map((person) => ({
    ...person,
    status: "unfinished",
    path: [],
    distance: 0,
    wait: 0,
    arrivedAt: null,
    segments: [],
  }));
  const assigned = new Map<number, RouteStep[]>();
  const pending = new MinHeap<{
    at: number;
    person: number;
    step: number;
    serial: number;
  }>((a, b) => a.at - b.at || a.serial - b.serial);
  let serial = 0;
  journeys.forEach((j, index) => {
    const key = `${j.profile}:${j.origin}:${j.destination}`;
    if (!routes.has(key))
      routes.set(
        key,
        findRoute(
          edges,
          j.origin,
          j.destination,
          profileById(j.profile),
          settings,
        ),
      );
    const route = routes.get(key)!;
    if (route === null) {
      j.status = "unreachable";
      return;
    }
    assigned.set(index, route);
    j.path = route.map((step) => step.edge.id);
    pending.push({ at: j.departure, person: index, step: 0, serial: serial++ });
  });
  const nextEntry = new Map<string, number>();
  const queueIntervals = new Map<string, [number, number][]>();
  while (pending.size) {
    const event = pending.pop()!;
    if (event.at > settings.horizon) break;
    const j = journeys[event.person],
      route = assigned.get(event.person)!;
    if (event.step === route.length) {
      j.status = "arrived";
      j.arrivedAt = event.at;
      continue;
    }
    const step = route[event.step],
      edge = step.edge;
    const start = nextGreen(
      Math.max(event.at, nextEntry.get(edge.id) ?? 0),
      edge,
    );
    const end =
      start +
      travelSeconds(edge, profileById(j.profile), j.speedScale, settings);
    nextEntry.set(
      edge.id,
      start + 1 / (edge.capacity * settings.capacityFactor),
    );
    j.segments.push({
      edge: edge.id,
      from: step.from,
      to: step.to,
      queuedAt: event.at,
      start,
      end,
    });
    j.wait += Math.max(0, Math.min(start, settings.horizon) - event.at);
    j.distance += edge.length;
    if (start > event.at) {
      const list = queueIntervals.get(edge.id) ?? [];
      list.push([event.at, Math.min(start, settings.horizon)]);
      queueIntervals.set(edge.id, list);
    }
    if (end <= settings.horizon)
      pending.push({
        at: end,
        person: event.person,
        step: event.step + 1,
        serial: serial++,
      });
  }
  const queues: Run["queues"] = {};
  for (const edge of edges) {
    const points = (queueIntervals.get(edge.id) ?? [])
      .flatMap(([a, b]) => [
        { at: a, change: 1 },
        { at: b, change: -1 },
      ])
      .sort((a, b) => a.at - b.at || a.change - b.change);
    let count = 0,
      peak = 0;
    for (const point of points) {
      count += point.change;
      peak = Math.max(peak, count);
    }
    queues[edge.id] = {
      max: peak,
      entries: journeys.reduce(
        (n, j) => n + j.segments.filter((s) => s.edge === edge.id).length,
        0,
      ),
    };
  }
  const profiles = Object.fromEntries(
    PROFILES.map((p) => [
      p.id,
      summarize(journeys.filter((j) => j.profile === p.id)),
    ]),
  ) as Record<ProfileId, Metrics>;
  const duration = journeys.some((j) => j.status === "unfinished")
    ? settings.horizon
    : Math.max(1, ...journeys.map((j) => j.arrivedAt ?? j.departure));
  return { seed, duration, journeys, profiles, queues };
}

function range(values: number[]): [number, number] | null {
  return values.length ? [Math.min(...values), Math.max(...values)] : null;
}
export function pairedTimes(before: Run, after: Run, profile: ProfileId) {
  const proposed = new Map(
    after.journeys.filter((j) => j.status === "arrived").map((j) => [j.id, j]),
  );
  const times = before.journeys
    .filter(
      (j) =>
        j.profile === profile && j.status === "arrived" && proposed.has(j.id),
    )
    .map((j) => ({
      b: j.arrivedAt! - j.departure,
      a: proposed.get(j.id)!.arrivedAt! - proposed.get(j.id)!.departure,
    }));
  return {
    count: times.length,
    before: mean(times.map((t) => t.b)),
    after: mean(times.map((t) => t.a)),
    delta: mean(times.map((t) => t.a - t.b)),
  };
}
export function compare(
  map: MapData,
  edits: Edit[],
  settings: Settings,
): Comparison {
  const proposed = applyEdits(map, edits);
  const runs = Array.from({ length: settings.repeats }, (_, i) => {
    const seed = settings.seed + i;
    const people = generatePeople(map, settings, seed);
    return {
      baseline: simulate(map, map.edges, settings, people, seed),
      proposal: simulate(map, proposed, settings, people, seed),
    };
  });
  const ranges = Object.fromEntries(
    PROFILES.map((p) => {
      const values = runs.map((r) => {
        const paired = pairedTimes(r.baseline, r.proposal, p.id);
        return { b: paired.before, a: paired.after, delta: paired.delta };
      });
      return [
        p.id,
        {
          before: range(values.flatMap((v) => (v.b === null ? [] : [v.b]))),
          after: range(values.flatMap((v) => (v.a === null ? [] : [v.a]))),
          delta: range(
            values.flatMap((v) => (v.delta === null ? [] : [v.delta])),
          ),
        },
      ];
    }),
  ) as Comparison["ranges"];
  const paired = Object.fromEntries(
    PROFILES.map((p) => [
      p.id,
      pairedTimes(runs[0].baseline, runs[0].proposal, p.id),
    ]),
  ) as Comparison["paired"];
  return {
    ...runs[0],
    replicates: runs.map((run) => ({
      seed: run.baseline.seed,
      before: run.baseline.profiles,
      after: run.proposal.profiles,
      paired: Object.fromEntries(
        PROFILES.map((p) => [
          p.id,
          pairedTimes(run.baseline, run.proposal, p.id),
        ]),
      ) as Comparison["paired"],
    })),
    paired,
    ranges,
    repeats: settings.repeats,
    settings: { ...settings },
    edits: [...edits],
  };
}

export function sensitivity(
  map: MapData,
  edits: Edit[],
  settings: Settings,
): SensitivityRow[] {
  return [0.7, 1, 1.4].flatMap((demand) =>
    [0.85, 1, 1.15].map((speed) => {
      const s = {
        ...settings,
        people: Math.max(3, Math.round(settings.people * demand)),
        speedFactor: settings.speedFactor * speed,
        repeats: 1,
      };
      const result = compare(map, edits, s);
      return {
        label: `人流 ${Math.round(demand * 100)}% · 速度 ${Math.round(speed * 100)}%`,
        people: s.people,
        speedFactor: s.speedFactor,
        profiles: Object.fromEntries(
          PROFILES.map((p) => {
            const b = result.baseline.profiles[p.id],
              a = result.proposal.profiles[p.id];
            return [
              p.id,
              {
                delta: result.paired[p.id].delta,
                beforeArrived: b.arrived,
                afterArrived: a.arrived,
              },
            ];
          }),
        ) as SensitivityRow["profiles"],
      };
    }),
  );
}
