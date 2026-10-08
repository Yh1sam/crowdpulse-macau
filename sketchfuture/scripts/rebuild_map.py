"""Rebuild the OSM-derived snapshot from the included, attributed source extract.

No network access; run from any directory. Road connectivity is based on shared
OSM node IDs, never geometric intersection or proximity. This is not an audited
pedestrian or wheelchair navigation network.
"""
import collections
import gzip
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOX = (113.5372, 22.1923, 113.5426, 22.1984)
M_LON = 111320 * math.cos(math.radians(22.195))
M_LAT = 111320
ALLOWED = {"pedestrian", "footway", "path", "steps", "residential", "living_street", "service", "unclassified", "tertiary"}
LANDMARKS = [
    ("senado", "議事亭前地", "Senado Square", 22.1935, 113.53967),
    ("dominic", "板樟堂前地", "St. Dominic’s Square", 22.19442, 113.54041),
    ("ruins", "大三巴牌坊", "Ruins of St. Paul’s", 22.19744, 113.54084),
    ("museum", "澳門博物館", "Macao Museum", 22.19715, 113.54215),
    ("tercena", "果欄街", "Rua da Tercena", 22.19506, 113.53855),
]


def rebuild():
    raw = json.loads(gzip.decompress((ROOT / "data/macau-osm.json.gz").read_bytes()))
    nodes = {e["id"]: e for e in raw["elements"] if e["type"] == "node"}
    ways = [e for e in raw["elements"] if e["type"] == "way"]
    width, height = (BOX[2] - BOX[0]) * M_LON, (BOX[3] - BOX[1]) * M_LAT

    def inside(n):
        return BOX[0] <= n["lon"] <= BOX[2] and BOX[1] <= n["lat"] <= BOX[3]

    def point(i):
        n = nodes[i]
        return {"x": round((n["lon"] - BOX[0]) * M_LON, 2), "y": round((BOX[3] - n["lat"]) * M_LAT, 2)}

    def name(tags):
        return tags.get("name:zh-Hant", tags.get("name:zh", tags.get("name", "未命名通道").split(" ")[0]))

    walkways = [w for w in ways if w["tags"].get("highway") in ALLOWED
                and w["tags"].get("foot") != "no" and w["tags"].get("access") not in {"private", "no"}]
    adjacent, segments, seen = collections.defaultdict(set), [], set()
    for way in walkways:
        for a, b in zip(way["nodes"], way["nodes"][1:]):
            key = tuple(sorted((a, b)))
            if a == b or key in seen or not inside(nodes[a]) or not inside(nodes[b]):
                continue
            seen.add(key)
            adjacent[a].add(b)
            adjacent[b].add(a)
            segments.append((a, b, way))
    critical = {i for i in adjacent if len(adjacent[i]) != 2}
    for way in walkways:
        critical.update(i for i in [way["nodes"][0], way["nodes"][-1]] if i in adjacent)
    by_way = collections.defaultdict(list)
    for a, b, way in segments:
        by_way[way["id"]].append((a, b, way))
    edges = []
    for way_id, items in by_way.items():
        chunk, part = [], 0
        for a, b, way in items:
            if not chunk or chunk[-1] != a:
                chunk = [a]
            chunk.append(b)
            if b not in critical and b != items[-1][1]:
                continue
            points = [point(i) for i in chunk]
            length = sum(math.hypot(p["x"] - q["x"], p["y"] - q["y"]) for p, q in zip(points, points[1:]))
            if length < 0.1:
                chunk = [b]
                continue
            tags, highway = way["tags"], way["tags"]["highway"]
            try:
                edge_width = float(tags.get("width", "2.0").replace(" m", ""))
            except ValueError:
                edge_width = 2.0
            kind = "steps" if highway == "steps" else "street" if highway in {"residential", "living_street", "service", "unclassified", "tertiary"} else "path"
            slope = None
            try:
                slope = abs(float(tags["incline"].strip("%")))
            except (KeyError, ValueError):
                pass
            edges.append({"id": f"osm-{way_id}-{part}", "from": str(chunk[0]), "to": str(b),
                          "length": round(length, 3), "points": points, "kind": kind, "name": name(tags),
                          "width": max(0.5, min(8, edge_width)), "slope": slope, "capacity": round(edge_width * 0.55, 3),
                          "cycle": 0, "green": 0, "closed": False, "osmId": way_id, "assumption": True})
            chunk, part = [b], part + 1
    graph = collections.defaultdict(set)
    for edge in edges:
        graph[edge["from"]].add(edge["to"])
        graph[edge["to"]].add(edge["from"])
    components, remaining = [], set(graph)
    while remaining:
        start = next(iter(remaining))
        component, stack = {start}, [start]
        while stack:
            for node in graph[stack.pop()]:
                if node not in component:
                    component.add(node)
                    stack.append(node)
        components.append(component)
        remaining -= component
    main = max(components, key=len)
    edges = [e for e in edges if e["from"] in main and e["to"] in main]
    map_nodes = [dict(id=i, lon=nodes[int(i)]["lon"], lat=nodes[int(i)]["lat"], **point(int(i))) for i in sorted(main)]
    places = []
    for ident, label, english, latitude, longitude in LANDMARKS:
        x, y = (longitude - BOX[0]) * M_LON, (BOX[3] - latitude) * M_LAT
        node = min(map_nodes, key=lambda n: math.hypot(n["x"] - x, n["y"] - y))
        places.append(dict(id=ident, name=label, en=english, node=node["id"], x=node["x"], y=node["y"]))
    buildings, context = [], []
    for way in ways:
        if not all(i in nodes for i in way["nodes"]) or not any(inside(nodes[i]) for i in way["nodes"]):
            continue
        points = [point(i) for i in way["nodes"]]
        if any(p["x"] < -100 or p["x"] > width + 100 or p["y"] < -100 or p["y"] > height + 100 for p in points):
            continue
        tags = way["tags"]
        if "building" in tags:
            buildings.append({"points": points, "name": name(tags) if "name" in tags else ""})
        elif "highway" in tags:
            context.append({"points": points, "kind": "square" if tags.get("area") == "yes" else tags["highway"], "name": name(tags)})
        elif tags.get("leisure") == "park":
            context.append({"points": points, "kind": "park", "name": name(tags)})
    result = {"version": "macau-osm-2026-10-08-v1", "name": "議事亭 — 板樟堂 — 大三巴", "timestamp": "2026-10-08",
              "source": raw["source"], "nodes": map_nodes, "edges": edges, "places": places,
              "buildings": buildings, "context": context, "width": round(width, 2), "height": round(height, 2), "metersPerUnit": 1}
    destination = ROOT / "src/data/macau.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    print(f"Rebuilt {len(map_nodes)} nodes, {len(edges)} edges from the source snapshot.")


if __name__ == "__main__":
    rebuild()
