export type ProfileId = "walk" | "wheelchair" | "stroller";
export type Point = { x: number; y: number };
export type Node = Point & { id: string; lon: number; lat: number };
export type EdgeKind = "path" | "street" | "steps" | "crossing" | "ramp";
export type Edge = {
  id: string;
  from: string;
  to: string;
  length: number;
  points: Point[];
  kind: EdgeKind;
  name: string;
  width: number;
  slope: number | null;
  capacity: number;
  cycle: number;
  green: number;
  closed: boolean;
  osmId?: number;
  proposed?: boolean;
  assumption: boolean;
};
export type Place = Point & {
  id: string;
  name: string;
  en: string;
  node: string;
};
export type MapData = {
  version: string;
  name: string;
  timestamp: string;
  source: string;
  nodes: Node[];
  edges: Edge[];
  places: Place[];
  buildings: { points: Point[]; name?: string }[];
  context: { points: Point[]; kind: string; name?: string }[];
  width: number;
  height: number;
  metersPerUnit: number;
};
export type Profile = {
  id: ProfileId;
  name: string;
  short: string;
  color: string;
  speed: number;
  minWidth: number;
  maxSlope: number;
  steps: boolean;
};
export type Settings = {
  people: number;
  releaseSeconds: number;
  speedFactor: number;
  capacityFactor: number;
  seed: number;
  repeats: number;
  horizon: number;
};
export type Edit =
  | {
      type: "link";
      id: string;
      from: string;
      to: string;
      width: number;
      slope: number;
    }
  | { type: "ramp"; edgeId: string; slope: number; width?: number }
  | { type: "close"; edgeId: string };
export type Workspace = {
  version: 1;
  mapVersion: string;
  title: string;
  edits: Edit[];
  settings: Settings;
};
export type Person = {
  id: number;
  profile: ProfileId;
  origin: string;
  destination: string;
  departure: number;
  speedScale: number;
};
export type Segment = {
  edge: string;
  from: string;
  to: string;
  queuedAt: number;
  start: number;
  end: number;
};
export type Journey = Person & {
  status: "arrived" | "unfinished" | "unreachable";
  path: string[];
  distance: number;
  wait: number;
  arrivedAt: number | null;
  segments: Segment[];
};
export type Metrics = {
  people: number;
  arrived: number;
  unreachable: number;
  unfinished: number;
  meanTime: number | null;
  medianTime: number | null;
  meanWait: number | null;
  meanDistance: number | null;
};
export type Run = {
  seed: number;
  duration: number;
  journeys: Journey[];
  profiles: Record<ProfileId, Metrics>;
  queues: Record<string, { max: number; entries: number }>;
};
export type Comparison = {
  baseline: Run;
  proposal: Run;
  replicates: {
    seed: number;
    before: Record<ProfileId, Metrics>;
    after: Record<ProfileId, Metrics>;
    paired: Comparison["paired"];
  }[];
  paired: Record<
    ProfileId,
    {
      count: number;
      before: number | null;
      after: number | null;
      delta: number | null;
    }
  >;
  ranges: Record<
    ProfileId,
    {
      before: [number, number] | null;
      after: [number, number] | null;
      delta: [number, number] | null;
    }
  >;
  repeats: number;
  settings: Settings;
  edits: Edit[];
};
export type SensitivityRow = {
  label: string;
  people: number;
  speedFactor: number;
  profiles: Record<
    ProfileId,
    { delta: number | null; beforeArrived: number; afterArrived: number }
  >;
};
