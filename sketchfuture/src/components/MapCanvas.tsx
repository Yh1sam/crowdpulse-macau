import {
  memo,
  useEffect,
  useMemo,
  useRef,
  useState,
  type KeyboardEvent,
  type PointerEvent,
} from "react";
import type { Edge, MapData, Point, ProfileId, Run } from "../core/types";
import Icon from "./Icon";
import { PROFILES } from "../core/model";
import { personPosition } from "../core/playback";

export type Tool = "inspect" | "link" | "ramp" | "close";
const path = (points: Point[]) =>
  points.map((p, i) => `${i ? "L" : "M"}${p.x},${p.y}`).join(" ");
const BaseMap = memo(function BaseMap({ map }: { map: MapData }) {
  return (
    <g aria-hidden="true">
      <rect
        x={-100}
        y={-100}
        width={map.width + 200}
        height={map.height + 200}
        fill="#eef0e9"
      />
      {map.context
        .filter((c) => c.kind === "square" || c.kind === "park")
        .map((c, i) => (
          <path
            key={`area-${i}`}
            d={`${path(c.points)}Z`}
            fill={c.kind === "park" ? "#d5e6bd" : "#e7e5d5"}
            stroke="#d6d9c7"
            strokeWidth="0.6"
          />
        ))}
      {map.buildings.map((building, i) => (
        <path
          key={i}
          d={`${path(building.points)}Z`}
          fill="#e0e2d9"
          stroke="#ced2c8"
          strokeWidth="0.45"
        />
      ))}
      {map.context
        .filter((c) => c.kind !== "square" && c.kind !== "park")
        .map((c, i) => (
          <path
            key={`road-${i}`}
            d={path(c.points)}
            fill="none"
            stroke="#ffffff"
            strokeWidth={["secondary", "primary"].includes(c.kind) ? 8 : 4}
            strokeLinecap="round"
          />
        ))}
    </g>
  );
});

type Props = {
  map: MapData;
  edges: Edge[];
  run?: Run;
  time: number;
  profile: ProfileId | "all";
  tool: Tool;
  selected?: string;
  editable: boolean;
  onEdge: (edge: Edge) => void;
  onLink: (from: string, to: string) => void;
  title: string;
};

export default function MapCanvas({
  map,
  edges,
  run,
  time,
  profile,
  tool,
  selected,
  editable,
  onEdge,
  onLink,
  title,
}: Props) {
  const svg = useRef<SVGSVGElement>(null);
  const [zoom, setZoom] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [from, setFrom] = useState<string | null>(null);
  const [ghost, setGhost] = useState<Point | null>(null);
  const gesture = useRef<{
    x: number;
    y: number;
    offset: Point;
    scale: number;
  } | null>(null);
  const linkDrag = useRef<string | null>(null);
  const skipClick = useRef(false);
  useEffect(() => {
    setFrom(null);
    setGhost(null);
    linkDrag.current = null;
  }, [tool]);
  const edgeIndex = useMemo(
    () => new Map(edges.map((e) => [e.id, e])),
    [edges],
  );
  const nodeIndex = useMemo(
    () => new Map(map.nodes.map((n) => [n.id, n])),
    [map],
  );
  const anchors = useMemo(() => {
    const degree = new Map<string, number>();
    for (const e of map.edges) {
      degree.set(e.from, (degree.get(e.from) ?? 0) + 1);
      degree.set(e.to, (degree.get(e.to) ?? 0) + 1);
    }
    const places = new Set(map.places.map((p) => p.node));
    return map.nodes.filter(
      (n) =>
        (degree.get(n.id) ?? 0) >= 3 ||
        places.has(n.id) ||
        map.edges.some(
          (e) => e.kind === "steps" && (e.from === n.id || e.to === n.id),
        ),
    );
  }, [map]);
  const representative = run?.journeys.find(
    (j) =>
      j.profile === profile &&
      j.origin === map.places.find((p) => p.id === "senado")?.node &&
      j.destination === map.places.find((p) => p.id === "ruins")?.node,
  );
  const highlighted = new Set(representative?.path ?? []);
  const viewWidth = map.width / zoom + 40,
    viewHeight = map.height / zoom + 40;

  function local(event: { clientX: number; clientY: number }): Point {
    const matrix = svg.current?.getScreenCTM();
    if (!matrix) return { x: 0, y: 0 };
    const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(
      matrix.inverse(),
    );
    return { x: point.x, y: point.y };
  }
  function selectNode(id: string) {
    if (!editable || tool !== "link") return;
    if (from && from !== id) {
      onLink(from, id);
      setFrom(null);
      setGhost(null);
    } else {
      setFrom(id);
      setGhost(nodeIndex.get(id)!);
    }
  }
  function finishPointer(event: PointerEvent<SVGSVGElement>) {
    if (linkDrag.current) {
      const point = local(event);
      const nearest = anchors.reduce(
        (best, n) =>
          Math.hypot(n.x - point.x, n.y - point.y) <
          Math.hypot(best.x - point.x, best.y - point.y)
            ? n
            : best,
        anchors[0],
      );
      const start =
        nearest?.id === linkDrag.current && from && from !== linkDrag.current
          ? from
          : linkDrag.current;
      const matrix = svg.current?.getScreenCTM();
      const scale = matrix ? Math.hypot(matrix.a, matrix.b) : 1;
      if (
        nearest &&
        nearest.id !== start &&
        Math.hypot(nearest.x - point.x, nearest.y - point.y) < 28 / scale
      ) {
        onLink(start, nearest.id);
        setFrom(null);
        setGhost(null);
        skipClick.current = true;
      }
      linkDrag.current = null;
    }
    gesture.current = null;
  }
  const activate = (
    event: KeyboardEvent<SVGGElement>,
    callback: () => void,
  ) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      callback();
    }
  };

  return (
    <section className="map-panel" aria-label={`${title}街區地圖`}>
      <div className="map-caption">
        <span>{title}</span>
        <span className="map-badge">真實路網 · 構想模擬</span>
      </div>
      <div className="map-controls">
        <button
          aria-label={`${title}放大地圖`}
          onClick={() => setZoom((z) => Math.min(3, z + 0.35))}
        >
          <Icon name="plus" />
        </button>
        <button
          aria-label={`${title}縮小地圖`}
          onClick={() => setZoom((z) => Math.max(1, z - 0.35))}
        >
          <Icon name="minus" />
        </button>
        <button
          aria-label={`${title}重設視野`}
          onClick={() => {
            setZoom(1);
            setOffset({ x: 0, y: 0 });
          }}
        >
          <Icon name="locate" />
        </button>
      </div>
      <svg
        ref={svg}
        viewBox={`${offset.x - 20} ${offset.y - 20} ${viewWidth} ${viewHeight}`}
        role="group"
        aria-label="澳門議事亭至大三巴街區，彩色點代表模擬使用者。可用滑鼠或鍵盤選取通道。"
        className={`street-map tool-${tool}`}
        onPointerDown={(event) => {
          if (tool === "inspect" && zoom > 1) {
            if ((event.target as Element).closest('g[role="button"]')) return;
            const matrix = svg.current?.getScreenCTM();
            gesture.current = {
              x: event.clientX,
              y: event.clientY,
              offset,
              scale: matrix ? Math.hypot(matrix.a, matrix.b) : 1,
            };
            event.currentTarget.setPointerCapture(event.pointerId);
          }
        }}
        onPointerMove={(event) => {
          if (from) setGhost(local(event));
          if (gesture.current) {
            const g = gesture.current;
            setOffset({
              x: Math.max(
                -30,
                Math.min(
                  map.width - viewWidth + 30,
                  g.offset.x - (event.clientX - g.x) / g.scale,
                ),
              ),
              y: Math.max(
                -30,
                Math.min(
                  map.height - viewHeight + 30,
                  g.offset.y - (event.clientY - g.y) / g.scale,
                ),
              ),
            });
          }
        }}
        onPointerUp={finishPointer}
        onPointerCancel={() => {
          linkDrag.current = null;
          gesture.current = null;
          setFrom(null);
          setGhost(null);
        }}
      >
        <BaseMap map={map} />
        <g>
          {edges.map((edge) => {
            const color = edge.closed
              ? "#e45a51"
              : edge.proposed
                ? "#007aff"
                : edge.kind === "steps"
                  ? "#b68d5b"
                  : "#a9b6b0";
            const active = selected === edge.id || highlighted.has(edge.id);
            return (
              <g
                key={edge.id}
                role="button"
                tabIndex={editable && selected === edge.id ? 0 : -1}
                aria-label={`${edge.name}，${edge.closed ? "已封閉" : edge.kind === "steps" ? "樓梯" : "通道"}，${Math.round(edge.length)} 米`}
                onClick={(event) => {
                  event.stopPropagation();
                  if (editable) onEdge(edge);
                }}
                onKeyDown={(event) =>
                  activate(event, () => {
                    if (editable) onEdge(edge);
                  })
                }
              >
                <path
                  d={path(edge.points)}
                  fill="none"
                  stroke="transparent"
                  strokeWidth="13"
                  className="edge-hit"
                />
                <path
                  d={path(edge.points)}
                  fill="none"
                  stroke={edge.closed ? "#e45a51" : active ? "#007aff" : color}
                  strokeWidth={active ? 3.6 : edge.proposed ? 3 : 1.5}
                  strokeDasharray={
                    edge.closed ? "4 3" : edge.proposed ? "6 3" : undefined
                  }
                  opacity={active || edge.proposed || edge.closed ? 1 : 0.75}
                  strokeLinecap="round"
                  pointerEvents="none"
                />
              </g>
            );
          })}
        </g>
        {run?.journeys
          .filter((j) => profile === "all" || j.profile === profile)
          .map((j) => {
            const point = personPosition(j, time, map, edgeIndex);
            if (!point) return null;
            const p = PROFILES.find((p) => p.id === j.profile)!;
            const jitter = point.waiting
              ? {
                  x: ((j.id % 5) - 2) * 1.8,
                  y: ((Math.floor(j.id / 5) % 5) - 2) * 1.8,
                }
              : { x: 0, y: 0 };
            return (
              <g
                key={`person-${j.id}`}
                transform={`translate(${point.x + jitter.x},${point.y + jitter.y})`}
                pointerEvents="none"
                opacity={
                  j.status === "arrived" && time >= j.arrivedAt! ? 0.28 : 1
                }
              >
                {point.unreachable ? (
                  <path
                    d="M-2.5,-2.5L2.5,2.5M-2.5,2.5L2.5,-2.5"
                    stroke={p.color}
                    strokeWidth="1.7"
                  />
                ) : j.profile === "wheelchair" ? (
                  <rect
                    x="-2.7"
                    y="-2.7"
                    width="5.4"
                    height="5.4"
                    rx="1"
                    fill={p.color}
                    stroke="white"
                    strokeWidth="0.8"
                  />
                ) : j.profile === "stroller" ? (
                  <path
                    d="M0,-3.5L3.4,2.8L-3.4,2.8Z"
                    fill={p.color}
                    stroke="white"
                    strokeWidth="0.8"
                  />
                ) : (
                  <circle
                    r="2.7"
                    fill={p.color}
                    stroke="white"
                    strokeWidth="0.8"
                  />
                )}
                {point.waiting && !point.unreachable ? (
                  <circle
                    r="5"
                    fill="none"
                    stroke={p.color}
                    strokeWidth="0.6"
                  />
                ) : null}
              </g>
            );
          })}
        {map.places.map((place) => (
          <g
            key={place.id}
            data-place={place.id}
            transform={`translate(${place.x},${place.y})`}
            pointerEvents="none"
          >
            <circle r="5.5" fill="white" stroke="#526556" strokeWidth="1.2" />
            <text
              x={place.id === "museum" ? -9 : 9}
              y="-9"
              textAnchor={place.id === "museum" ? "end" : "start"}
              className="place-name"
            >
              {place.name}
            </text>
          </g>
        ))}
        {editable && tool === "link"
          ? anchors.map((node) => (
              <g
                key={node.id}
                role="button"
                tabIndex={0}
                aria-label={`連接點 ${node.id}`}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  linkDrag.current = node.id;
                  if (!from) setFrom(node.id);
                  setGhost(node);
                  svg.current?.setPointerCapture(event.pointerId);
                }}
                onClick={(event) => {
                  event.stopPropagation();
                  if (skipClick.current) {
                    skipClick.current = false;
                    return;
                  }
                  selectNode(node.id);
                }}
                onKeyDown={(event) =>
                  activate(event, () => selectNode(node.id))
                }
              >
                <circle cx={node.x} cy={node.y} r="10" fill="transparent" />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={from === node.id ? 5 : 3.2}
                  fill={from === node.id ? "#007aff" : "white"}
                  stroke="#007aff"
                  strokeWidth="1.1"
                />
              </g>
            ))
          : null}
        <g
          transform={`translate(${offset.x + 10},${offset.y + viewHeight - 55})`}
          pointerEvents="none"
          aria-label="地圖比例尺"
        >
          <path
            d={`M0,-4V0H${zoom >= 2 ? 50 : 100}V-4`}
            stroke="#5c685b"
            strokeWidth="1.2"
            fill="none"
          />
          <text x="0" y="13" fontSize="10" fill="#5c685b">
            {zoom >= 2 ? 50 : 100} m
          </text>
        </g>
        {from && ghost ? (
          <path
            d={`M${nodeIndex.get(from)!.x},${nodeIndex.get(from)!.y}L${ghost.x},${ghost.y}`}
            stroke="#007aff"
            strokeWidth="2.5"
            strokeDasharray="5 3"
            pointerEvents="none"
          />
        ) : null}
      </svg>
      {editable && tool === "link" ? (
        <div className="map-tip">
          {from
            ? "拖曳到另一個圓點，或按第二個端點。"
            : "從圓點畫到另一個圓點，新增一條構想通道。"}
          {from ? (
            <button
              onClick={() => {
                setFrom(null);
                setGhost(null);
              }}
            >
              取消畫線
            </button>
          ) : null}
        </div>
      ) : null}
      <div className="map-footer">
        <span>街道位置依 OSM 資料</span>
        <span>北 ↑</span>
        <a
          href="https://www.openstreetmap.org/copyright"
          target="_blank"
          rel="noreferrer"
        >
          © OpenStreetMap contributors · ODbL
        </a>
      </div>
    </section>
  );
}
