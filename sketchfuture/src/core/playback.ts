import type { Edge, Journey, MapData, Point } from "./types";

function along(points: Point[], fraction: number): Point {
  const lengths = points
    .slice(1)
    .map((p, i) => Math.hypot(p.x - points[i].x, p.y - points[i].y));
  let remaining =
    lengths.reduce((a, b) => a + b, 0) * Math.max(0, Math.min(1, fraction));
  for (let i = 0; i < lengths.length; i++) {
    if (remaining <= lengths[i]) {
      const f = lengths[i] === 0 ? 0 : remaining / lengths[i];
      return {
        x: points[i].x + (points[i + 1].x - points[i].x) * f,
        y: points[i].y + (points[i + 1].y - points[i].y) * f,
      };
    }
    remaining -= lengths[i];
  }
  return points[points.length - 1];
}
export function personPosition(
  j: Journey,
  time: number,
  map: MapData,
  edges: Map<string, Edge>,
): (Point & { waiting: boolean; unreachable: boolean }) | null {
  if (time < j.departure) return null;
  if (j.status === "unreachable") {
    const node = map.nodes.find((n) => n.id === j.origin)!;
    return { ...node, waiting: true, unreachable: true };
  }
  for (const segment of j.segments) {
    const edge = edges.get(segment.edge);
    if (!edge) continue;
    if (time >= segment.queuedAt && time < segment.start) {
      const node = map.nodes.find((n) => n.id === segment.from)!;
      return { ...node, waiting: true, unreachable: false };
    }
    if (time >= segment.start && time <= segment.end) {
      const points =
        segment.from === edge.from ? edge.points : [...edge.points].reverse();
      return {
        ...along(
          points,
          (time - segment.start) / (segment.end - segment.start),
        ),
        waiting: false,
        unreachable: false,
      };
    }
  }
  if (j.status === "arrived" && time >= j.arrivedAt!) {
    const node = map.nodes.find((n) => n.id === j.destination)!;
    return { ...node, waiting: false, unreachable: false };
  }
  return null;
}
