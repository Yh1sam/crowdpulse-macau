"""Shared map, icons and crowd silhouettes for the Mrs Chan bookend shots S01 and S18.

Data sources (read, never retyped):
- shared/zones.json: zone lat/lon (linear projection from style.project), the 7 links, has_stairs / steep,
  Chinese place names and the street names of the approved detour.
- shared/config.json: the dashboard's SAFE / WARNING / CRITICAL thresholds (congestion_thresholds).
- experiments/results/simulation_run/A_timeline.csv: senado_square true_density (run A), which alone drives
  Senado's colour. A_events.json: run A's approval time and end time.
- The approved detour is run A's card (A07_intervention_evidence.png): "Rua dos Ervanarios descent ->
  Rua da Tercena west link -> Rua de S. Paulo (lower)"; its edges are looked up by name in zones.json.
- backend/app/services/intervention.py: the public-notice wording (zh / en / pt) for that card.
Everything else (Mrs Chan, the staff member, the dots, the walkers, the silhouettes) is illustrative
choreography drawn from plain Pillow shapes.
"""
from __future__ import annotations

import csv
import heapq
import json
import math
import random
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from style import *  # noqa: E402,F401,F403
from style import ROOT, W, H, NAVY, NAVY_2, NAVY_3, INK, INK_2, INK_3, SAFE, WARNING, CRITICAL, GREY, STATE_COLOUR  # noqa: E402
from style import font, text_font, clamp, ease, lerp, project, zone_graph, wheelchair_icon, staff_icon  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

NAME = "Mrs Chan"                        # the fictional visitor of the bookend shots (her tag; shotlist S01)
SS = 2                                   # supersampling factor for the map (drawn at 2x, reduced with a box filter)
MAP_BOX = (610, 150, 1410, 850)          # 1x box the zone graph is fitted into (height-limited; north up)
PROJ = project(MAP_BOX)
GRAPH = zone_graph()
ZONES = {z["id"]: z for z in GRAPH["zones"]}
POS = {zid: PROJ(z["lat"], z["lon"]) for zid, z in ZONES.items()}
EDGES = GRAPH["edges"]
CONFIG = json.loads((ROOT / "shared" / "config.json").read_text())
WARN_AT = CONFIG["congestion_thresholds"]["warning"]
CRIT_AT = CONFIG["congestion_thresholds"]["critical"]
RUN_A = ROOT / "experiments" / "results" / "simulation_run"

DISC_R = 19          # zone disc radius (1x)
SENADO_R = 22
PEOPLE_DOT = (150, 160, 175)
STAIRS_PINK = (232, 121, 249)
VEST = (214, 255, 61)
STREET_CASING = (24, 37, 62)
STREET_CORE = (44, 62, 95)
GRID_DOT = (24, 36, 58)

# labels from the storyboard (zh from zones.json name_zh, en as written in the storyboard)
LABEL_EN = {"ruins_st_paul": "Ruins of St. Paul's", "senado_square": "Senado Square", "almeida_ribeiro": "Av. de Almeida Ribeiro"}
# gap between a zone disc and its label (1x px): Senado's clears its crowd ring, Almeida's clears Mrs Chan's path
LABEL_DX = {"senado_square": 58, "almeida_ribeiro": 40}


# ---------------------------------------------------------------- routes

def step_free_route(src: str, dst: str) -> list[str]:
    """Shortest route in metres over links with no stairs and no steep section (zones.json)."""
    nbrs: dict[str, list[tuple[str, float]]] = {}
    for e in EDGES:
        if e["has_stairs"] or e["steep"]:
            continue
        nbrs.setdefault(e["from"], []).append((e["to"], e["length_m"]))
        nbrs.setdefault(e["to"], []).append((e["from"], e["length_m"]))
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        d, n = heapq.heappop(pq)
        if n == dst:
            break
        if d > dist.get(n, 1e18):
            continue
        for m, w_ in nbrs.get(n, []):
            if d + w_ < dist.get(m, 1e18):
                dist[m], prev[m] = d + w_, n
                heapq.heappush(pq, (d + w_, m))
    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return path[::-1]


def chain_by_names(start: str, names: list[str]) -> list[str]:
    """Zone ids visited when following zones.json links by their names, starting at `start`."""
    nodes = [start]
    for nm in names:
        e = next(e for e in EDGES if e["name"] == nm)
        assert nodes[-1] in (e["from"], e["to"]), (nm, nodes)
        nodes.append(e["to"] if e["from"] == nodes[-1] else e["from"])
    return nodes


MAIN_ROUTE = step_free_route("almeida_ribeiro", "jesus_square")      # Almeida -> Senado -> St. Dominic's -> Rua de S. Paulo -> Jesus Sq.
CARD_ROUTE_NAMES = ["Rua dos Ervanarios descent", "Rua da Tercena west link", "Rua de S. Paulo (lower)"]  # run A card (A07)
DETOUR = chain_by_names("almeida_ribeiro", CARD_ROUTE_NAMES)
assert "ruins_st_paul" not in MAIN_ROUTE and "senado_square" not in DETOUR


class Polyline:
    def __init__(self, pts):
        self.pts = [(float(x), float(y)) for x, y in pts]
        self.cum = [0.0]
        for a, b in zip(self.pts, self.pts[1:]):
            self.cum.append(self.cum[-1] + math.dist(a, b))
        self.length = self.cum[-1]

    def _seg(self, s):
        s = clamp(s, 0.0, self.length)
        for i in range(1, len(self.cum)):
            if s <= self.cum[i] or i == len(self.cum) - 1:
                seg = self.cum[i] - self.cum[i - 1]
                return i, (s - self.cum[i - 1]) / seg if seg else 0.0
        return len(self.cum) - 1, 1.0

    def at(self, s):
        i, k = self._seg(s)
        return lerp(self.pts[i - 1], self.pts[i], k)

    def direction(self, s):
        i, _ = self._seg(s)
        (x0, y0), (x1, y1) = self.pts[i - 1], self.pts[i]
        n = math.hypot(x1 - x0, y1 - y0) or 1.0
        return (x1 - x0) / n, (y1 - y0) / n

    def points(self, s0, s1):
        s0, s1 = clamp(s0, 0, self.length), clamp(s1, 0, self.length)
        out = [self.at(s0)]
        for c, p in zip(self.cum, self.pts):
            if s0 < c < s1:
                out.append(p)
        out.append(self.at(s1))
        return out


MAIN_PATH = Polyline([POS[z] for z in MAIN_ROUTE])


def _detour_points(offset: float = 12.0) -> list[tuple[float, float]]:
    """The detour's zone centres; where it shares a link with her main route (Rua de S. Paulo (lower)),
    it runs in a parallel lane `offset` px to the west so both lines stay visible."""
    main_links = {frozenset(p) for p in zip(MAIN_ROUTE, MAIN_ROUTE[1:])}
    pts = [POS[DETOUR[0]]]
    for a, b in zip(DETOUR, DETOUR[1:]):
        pa, pb = POS[a], POS[b]
        if frozenset((a, b)) in main_links:
            L = math.dist(pa, pb)
            nx, ny = -(pb[1] - pa[1]) / L, (pb[0] - pa[0]) / L
            if nx > 0:                                   # west = smaller x
                nx, ny = -nx, -ny
            pts[-1] = (pts[-1][0] + nx * offset, pts[-1][1] + ny * offset)
            pts.append((pb[0] + nx * offset, pb[1] + ny * offset))
        else:
            pts.append(pb)
    return pts


DETOUR_PATH = Polyline(_detour_points())
FIRST_LEG = math.dist(POS["almeida_ribeiro"], POS["senado_square"])
AHPO_S01_END = 0.55 * FIRST_LEG          # where Mrs Chan stops in S01 (short of Senado's crowd); S18 starts here


# ---------------------------------------------------------------- Senado's recorded density (run A)

def hms(s: str) -> int:
    parts = [int(x) for x in s.split(":")]
    parts += [0] * (3 - len(parts))
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def clock(sim_s: float) -> str:
    s = int(sim_s)
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


@lru_cache(maxsize=1)
def senado_series() -> list[tuple[int, float]]:
    pts: dict[int, float] = {}
    with open(RUN_A / "A_timeline.csv", newline="") as f:
        for r in csv.DictReader(f):
            if r["zone"] == "senado_square":
                pts[hms(r["sim_time"])] = float(r["true_density"])
    return sorted(pts.items())


@lru_cache(maxsize=1)
def run_a_events() -> list[dict]:
    return json.loads((RUN_A / "A_events.json").read_text())


def approve_sim() -> int:
    return hms(next(e for e in run_a_events() if e.get("event") == "ui" and e.get("action") == "approve")["sim_time"])


def end_sim() -> int:
    return hms(next(e for e in run_a_events() if e.get("event") == "end")["sim_time"])


def senado_density(sim_s: float) -> float:
    """Recorded true density, sample-and-hold (the value shown until the next recorded sample)."""
    ser = senado_series()
    val = ser[0][1]
    for s, v in ser:
        if s <= sim_s:
            val = v
        else:
            break
    return val


@lru_cache(maxsize=1)
def _change_points() -> list[tuple[int, float]]:
    """(sim s, value) at each time the recorded true_density takes a new value."""
    out: list[tuple[int, float]] = []
    for s, v in senado_series():
        if not out or v != out[-1][1]:
            out.append((s, v))
    return out


def senado_density_smooth(sim_s: float) -> float:
    """Linear interpolation between the recorded values' change points. Used only for how many
    illustrative dots mill in the square (so they never pop); the colour uses the recorded values as held."""
    pts = _change_points()
    if sim_s <= pts[0][0]:
        return pts[0][1]
    for (s0, v0), (s1, v1) in zip(pts, pts[1:]):
        if sim_s <= s1:
            return v0 + (v1 - v0) * (sim_s - s0) / (s1 - s0)
    return pts[-1][1]


def sim_clock(t: float, keys: list[tuple[float, int]]) -> float:
    """Piecewise-linear map from shot time (s) to simulation time (s since midnight), held at both ends."""
    if t <= keys[0][0]:
        return float(keys[0][1])
    for (t0, s0), (t1, s1) in zip(keys, keys[1:]):
        if t <= t1:
            return s0 + (s1 - s0) * (t - t0) / (t1 - t0)
    return float(keys[-1][1])


@lru_cache(maxsize=1)
def _intervention_module():
    """backend/app/services/intervention.py, loaded by path (it imports shared.geo, so the repo root goes on sys.path)."""
    import importlib.util
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("_intervention", ROOT / "backend" / "app" / "services" / "intervention.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def card_notice() -> dict[str, str]:
    """Run A's approved card (#5, redirect_flow at Senado via the detour edges): the full public notice that
    backend/app/services/intervention.py writes, per language (it ends with the AI clause, AI_NOTICE)."""
    by_name = {e["name"]: e for e in EDGES}
    return _intervention_module().public_messages("redirect_flow", ZONES["senado_square"], [by_name[n] for n in CARD_ROUTE_NAMES])


@lru_cache(maxsize=1)
def notice_first_sentences() -> dict[str, str]:
    """The card's notice, first sentence of each language (the place name and the 'very crowded' line); the
    full notice continues with the route, the staff sentence and the AI clause."""
    out = {}
    for lang, text in card_notice().items():
        cut = text.index("。") + 1 if lang == "zh" else text.index(". ") + 1
        out[lang] = text[:cut]
    return out


@lru_cache(maxsize=1)
def notice_excerpts() -> dict[str, str]:
    """The same first sentences as excerpts: the closing stop becomes '…', as on S04's gloss panel
    (video/recipes.py, gloss_panel), so a board that shows only them never reads as a whole notice.
    Checks that the AI clause (AI_NOTICE) still closes every language's full notice, so the '…' stands for it."""
    ai = _intervention_module().AI_NOTICE
    out = {}
    for lang, first in notice_first_sentences().items():
        full = card_notice()[lang]
        assert full.startswith(first) and full.endswith(ai[lang]) and len(full) > len(first) + len(ai[lang]), (lang, full)
        assert first[-1] in ".。", first
        out[lang] = first[:-1] + "…"
    return out


def state_of(d: float) -> str:
    return "CRITICAL" if d >= CRIT_AT else "WARNING" if d >= WARN_AT else "SAFE"


def window_states(s0: float, s1: float) -> set[str]:
    ser = senado_series()
    vals = [senado_density(s0)] + [v for s, v in ser if s0 <= s <= s1]
    return {state_of(v) for v in vals}


def senado_colour(t: float, sim_of, window: float = 0.4, n: int = 15) -> tuple[int, int, int]:
    """State colour of Senado at shot time t, cross-faded over `window` s of shot time (no popping)."""
    cols = [STATE_COLOUR[state_of(senado_density(sim_of(t - window * i / (n - 1))))] for i in range(n)]
    return tuple(int(round(sum(c[k] for c in cols) / n)) for k in range(3))


# ---------------------------------------------------------------- camera

class Cam:
    """Map camera: a point p (1x home coordinates) is drawn at anchor + (p - focus) * zoom."""

    def __init__(self, zoom: float = 1.0, focus=(960.0, 540.0), anchor=None):
        self.zoom = zoom
        self.focus = focus
        self.anchor = anchor if anchor is not None else focus

    def __call__(self, p):
        return (self.anchor[0] + (p[0] - self.focus[0]) * self.zoom, self.anchor[1] + (p[1] - self.focus[1]) * self.zoom)

    @property
    def home(self) -> bool:
        return abs(self.zoom - 1) < 1e-6 and self.focus == self.anchor


HOME = Cam()


# ---------------------------------------------------------------- small drawing helpers (2x canvas)

def _s(p):
    return (p[0] * SS, p[1] * SS)


def _rgba(c, a=1.0):
    return (int(c[0]), int(c[1]), int(c[2]), int(round(255 * clamp(a))))


def disc(d, p, r, fill, alpha=1.0, outline=None, width=0):
    x, y = _s(p)
    r *= SS
    d.ellipse((x - r, y - r, x + r, y + r), fill=_rgba(fill, alpha) if fill else None,
              outline=_rgba(outline, alpha) if outline else None, width=int(width * SS))


def seg_line(d, a, b, colour, width, alpha=1.0, caps=True):
    d.line([_s(a), _s(b)], fill=_rgba(colour, alpha), width=int(round(width * SS)))
    if caps:
        for p in (a, b):
            disc(d, p, width / 2, colour, alpha)


def poly_line(d, pts, colour, width, alpha=1.0):
    if len(pts) < 2:
        return
    d.line([_s(p) for p in pts], fill=_rgba(colour, alpha), width=int(round(width * SS)), joint="curve")
    for p in (pts[0], pts[-1]):
        disc(d, p, width / 2, colour, alpha)


def dashed(d, path: Polyline, s0, s1, colour, width, dash=18.0, gap=11.0, phase=0.0, alpha=1.0, cam=HOME):
    period = dash + gap
    s = s0 - ((s0 + phase) % period)
    while s < s1:
        a, b = max(s, s0), min(s + dash, s1)
        if b > a:
            pa, pb = cam(path.at(a)), cam(path.at(b))
            seg_line(d, pa, pb, colour, width, alpha)
        s += period


def text2x(img, xy, text, size, weight=400, fill=INK, alpha=1.0, anchor="la", stroke=0, stroke_fill=NAVY):
    """Text on the 2x canvas with real opacity. Pillow's ImageDraw.text ignores the fill's alpha on an RGB
    image (labels would pop in at full strength), so the text is drawn opaque into a small sprite and
    pasted through its alpha scaled by `alpha`."""
    if alpha <= 0.003:
        return
    f = text_font(text, size * SS, weight)
    x, y = _s(xy)
    sw = int(stroke * SS)
    l, t, r, b = ImageDraw.Draw(img).textbbox((x, y), text, font=f, anchor=anchor, stroke_width=sw)
    l, t = int(math.floor(l)) - 2, int(math.floor(t)) - 2
    r, b = int(math.ceil(r)) + 2, int(math.ceil(b)) + 2
    spr = Image.new("RGBA", (r - l, b - t), (0, 0, 0, 0))
    ImageDraw.Draw(spr).text((x - l, y - t), text, font=f, fill=_rgba(fill), anchor=anchor,
                             stroke_width=sw, stroke_fill=_rgba(stroke_fill))
    spr = with_alpha(spr, alpha)
    img.paste(spr, (l, t), spr)


def text_sprite(text: str, size: int, weight: int = 400, fill=INK, max_width: int | None = None,
                line_gap: float = 1.25, align: str = "left") -> Image.Image:
    """Crisp text rendered once into a tight RGBA sprite (pasted per frame)."""
    from style import wrap
    lines = wrap(text, size, weight, max_width) if max_width else [text]
    fonts = [text_font(ln, size, weight) for ln in lines]
    widths = [int(math.ceil(f.getlength(ln))) for f, ln in zip(fonts, lines)]
    asc = max(f.getmetrics()[0] for f in fonts)
    desc = max(f.getmetrics()[1] for f in fonts)
    step = size * line_gap
    w_ = max(widths) + 4
    h_ = int(math.ceil(step * (len(lines) - 1) + asc + desc)) + 4
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, (ln, f, wd) in enumerate(zip(lines, fonts, widths)):
        x = 2 if align == "left" else (w_ - wd - 2 if align == "right" else (w_ - wd) / 2)
        d.text((x, 2 + i * step), ln, font=f, fill=(*fill[:3], 255))
    return img


def with_alpha(sprite: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return sprite
    s = sprite.copy()
    s.putalpha(sprite.getchannel("A").point(lambda v: int(v * clamp(a))))
    return s


def paste(base: Image.Image, sprite: Image.Image, xy, alpha: float = 1.0) -> None:
    """Pastes an RGBA sprite onto an RGB or RGBA frame with opacity (clipped at the frame edges)."""
    if alpha <= 0.003:
        return
    s = with_alpha(sprite, alpha)
    x, y = int(round(xy[0])), int(round(xy[1]))
    if base.mode == "RGBA":
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
        layer.paste(s, (x, y), s)
        base.alpha_composite(layer)
    else:
        base.paste(s, (x, y), s)


# ---------------------------------------------------------------- marker sprites (drawn at 4x, reduced)

@lru_cache(maxsize=256)
def marker_sprite(kind: str, r2: int) -> Image.Image:
    """Round marker of radius r2 px at the map's 2x scale: 'ahpo' (amber wheelchair) or 'staff' (hi-vis vest).
    Drawn at twice that size and reduced, so the outline glyphs are anti-aliased."""
    q = 2
    R = r2 * q
    size = int(2 * R + 16 * q)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    ring = WARNING if kind == "ahpo" else VEST
    g = 3.5 * q * r2 / (21 * SS)
    d.ellipse((c - R - g, c - R - g, c + R + g, c + R + g), fill=(*ring, 60))
    d.ellipse((c - R, c - R, c + R, c + R), fill=(*NAVY_2, 255), outline=(*ring, 255), width=max(2, int(R * 0.12)))
    if kind == "ahpo":
        s = R * 1.26 / 54
        wheelchair_icon(d, c + 4 * s, c + 3 * s, s, colour=WARNING, width=4)
    else:
        s = R * 1.22 / 56
        staff_icon(d, c, c + 6 * s, s)
    return img.resize((size // q, size // q), Image.LANCZOS)


@lru_cache(maxsize=8)
def tag_sprite(text: str, colour=WARNING) -> Image.Image:
    """Small pill tag (her name) at 2x."""
    f = font(22 * SS, 700)
    tw = f.getlength(text)
    pad_x, hgt = 12 * SS, 34 * SS
    img = Image.new("RGBA", (int(tw + 2 * pad_x), hgt), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, hgt - 1), hgt // 2, fill=(*colour, 255))
    d.text((img.width / 2, hgt / 2 + SS), text, font=f, fill=(*NAVY, 255), anchor="mm")
    return img


def pin_shape(d, tip, alpha=1.0, lean_deg=25.0, scale=1.0):
    """Map pin with its tip at `tip`, leaning left so it never covers the St. Paul's steps."""
    a = math.radians(lean_deg)
    L, R = 40 * scale, 14 * scale
    ux, uy = -math.sin(a), -math.cos(a)                  # tip -> head direction
    head = (tip[0] + ux * L, tip[1] + uy * L)
    # tangent points from the tip to the head circle
    dist = L
    beta = math.asin(min(1.0, R / dist))
    base_ang = math.atan2(-uy, -ux)                         # head -> tip angle
    pts = [tip]
    for sgn in (-1, 1):
        ang = base_ang + sgn * (math.pi / 2 + beta)
        pts.append((head[0] + R * math.cos(ang), head[1] + R * math.sin(ang)))
    # shadow
    x, y = _s(tip)
    d.ellipse((x - 11 * SS, y - 4 * SS, x + 11 * SS, y + 4 * SS), fill=(0, 0, 0, int(120 * alpha)))
    d.polygon([_s(p) for p in pts], fill=_rgba(INK, alpha))
    disc(d, head, R, INK, alpha)
    disc(d, head, R * 0.42, NAVY, alpha)


def stair_glyph(d, c, alpha=1.0):
    disc(d, c, 15, NAVY_2, alpha, outline=STAIRS_PINK, width=2.5)
    x, y = c
    pts = [(x - 8, y + 6), (x - 8, y + 2), (x - 3, y + 2), (x - 3, y - 2), (x + 2, y - 2), (x + 2, y - 6), (x + 8, y - 6)]
    d.line([_s(p) for p in pts], fill=_rgba(STAIRS_PINK, alpha), width=int(2.6 * SS), joint="curve")


# ---------------------------------------------------------------- illustrative people dots

class Dots:
    """Grey dots drifting along the streets plus a cluster milling in Senado Square (illustrative)."""

    def __init__(self, seed: int = 5):
        rng = random.Random(seed)
        self.street = []
        for e in EDGES:
            a, b = POS[e["from"]], POS[e["to"]]
            L = math.dist(a, b)
            n = max(2, int(L / (46 if e["has_stairs"] else 26)))
            for _ in range(n):
                self.street.append((e["id"], rng.random(), rng.uniform(9, 20) * rng.choice((-1, 1)), rng.uniform(-4.5, 4.5)))
        self.edge_ends = {e["id"]: (POS[e["from"]], POS[e["to"]]) for e in EDGES}
        self.cluster = []
        for i in range(84):
            r = 29 + 33 * math.sqrt(rng.random())
            th = rng.uniform(0, 2 * math.pi)
            self.cluster.append((r, th, rng.random(), rng.uniform(0.2, 0.5), rng.uniform(0, 6.3)))
        self.cluster.sort(key=lambda c: c[0])                 # inner dots appear first
        self.cluster = [(r, th, (i + rng.random()) / len(self.cluster), f, ph) for i, (r, th, _, f, ph) in enumerate(self.cluster)]

    def street_positions(self, t):
        for eid, u0, v, off in self.street:
            a, b = self.edge_ends[eid]
            L = math.dist(a, b)
            s = (u0 * L + v * t) % L
            k = s / L
            nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            p = (a[0] + (b[0] - a[0]) * k + nx * off, a[1] + (b[1] - a[1]) * k + ny * off)
            edge_fade = clamp(min(s, L - s) / 14.0 - 1.0)        # never on top of a disc
            yield p, edge_fade

    def cluster_positions(self, t, density, lane=None, lane_k=0.0, lane_w=17.0):
        """Visible share grows with Senado's recorded density; `lane` (a Polyline) is kept clear, lane_w px each side."""
        frac = clamp((density - 0.33) / 0.57)
        cx, cy = POS["senado_square"]
        for r, th, u, f, ph in self.cluster:
            a = clamp((frac - u) / 0.06)
            if a <= 0:
                continue
            x = cx + r * math.cos(th) + 2.6 * math.sin(2 * math.pi * f * t + ph)
            y = cy + r * math.sin(th) + 2.6 * math.cos(2 * math.pi * f * 0.8 * t + ph)
            if lane is not None and lane_k > 0:
                x, y = _push_from_lane((x, y), lane, lane_k * (lane_w + 12.0 * ph / 6.3))   # ragged edge, not a ruled line
            yield (x, y), a


def _push_from_lane(p, path: Polyline, clear: float):
    best = None
    for (ax, ay), (bx, by) in zip(path.pts, path.pts[1:]):
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        k = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / L2) if L2 else 0
        qx, qy = ax + dx * k, ay + dy * k
        dd = math.hypot(p[0] - qx, p[1] - qy)
        if best is None or dd < best[0]:
            best = (dd, qx, qy, dx, dy)
    dd, qx, qy, dx, dy = best
    if dd >= clear:
        return p
    if dd < 1e-6:
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
    else:
        nx, ny = (p[0] - qx) / dd, (p[1] - qy) / dd
    return (qx + nx * clear, qy + ny * clear)


# ---------------------------------------------------------------- the map scene

class MapScene:
    """Top-down schematic of the zone model, drawn at 2x and reduced. Static parts are cached for the home camera."""

    def __init__(self):
        self._static = None
        self.dots = Dots()

    # static: background grid, streets, steps, plain zone discs
    def _draw_static(self, img, cam: Cam, draw_in: dict | None = None):
        d = ImageDraw.Draw(img, "RGBA")
        z = cam.zoom
        # dot grid (map paper), anchored to the home frame so it zooms with the map
        step = 40.0
        x0h, y0h = (0 - cam.anchor[0]) / z + cam.focus[0], (0 - cam.anchor[1]) / z + cam.focus[1]
        x1h, y1h = (W - cam.anchor[0]) / z + cam.focus[0], (H - cam.anchor[1]) / z + cam.focus[1]
        gx = math.floor(x0h / step) * step
        rr = 1.4 * min(z, 3) ** 0.5
        while gx <= x1h:
            gy = math.floor(y0h / step) * step
            while gy <= y1h:
                x, y = cam((gx, gy))
                d.ellipse(((x - rr) * SS, (y - rr) * SS, (x + rr) * SS, (y + rr) * SS), fill=GRID_DOT)
                gy += step
            gx += step
        wz = z ** 0.6
        for e in EDGES:
            a, b = POS[e["from"]], POS[e["to"]]
            k = 1.0 if draw_in is None else draw_in.get(e["id"], 1.0)
            if k <= 0:
                continue
            a, b = cam(a), cam(lerp(a, b, k))
            if e["has_stairs"]:
                self._steps(d, a, b, wz)
            else:
                seg_line(d, a, b, STREET_CASING, 24 * wz)
                seg_line(d, a, b, STREET_CORE, 11 * wz)
        if draw_in is None or draw_in.get("e_ruins_jesus", 1.0) >= 1:
            a, b = cam(POS["ruins_st_paul"]), cam(POS["jesus_square"])
            mid = lerp(a, b, 0.5)
            stair_glyph(d, (mid[0] + 34 * wz, mid[1] + 8 * wz), 1.0 if draw_in is None else draw_in.get("stairs_icon", 1.0))
        for zid, p in POS.items():
            if zid == "senado_square":
                continue
            k = 1.0 if draw_in is None else draw_in.get(zid, 1.0)
            if k <= 0:
                continue
            disc(d, cam(p), DISC_R * wz * (0.4 + 0.6 * k), (36, 52, 82), k, outline=INK_3, width=2)

    def _steps(self, d, a, b, wz):
        """St. Paul's steps: hatched band (rails + rungs) in the dashboard's stairs pink."""
        L = math.dist(a, b)
        if L < 1:
            return
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -uy, ux
        hw = 8 * wz
        seg_line(d, a, b, STREET_CASING, 24 * wz)
        for sgn in (-1, 1):
            seg_line(d, (a[0] + nx * hw * sgn, a[1] + ny * hw * sgn), (b[0] + nx * hw * sgn, b[1] + ny * hw * sgn), STAIRS_PINK, 2.6 * wz, caps=False)
        s = 5 * wz
        while s < L - 2:
            p = (a[0] + ux * s, a[1] + uy * s)
            seg_line(d, (p[0] - nx * hw, p[1] - ny * hw), (p[0] + nx * hw, p[1] + ny * hw), STAIRS_PINK, 2.6 * wz, caps=False)
            s += 7.5 * wz

    def base(self, cam: Cam, draw_in: dict | None = None) -> Image.Image:
        if cam.home and draw_in is None:
            if self._static is None:
                img = Image.new("RGB", (W * SS, H * SS), NAVY)
                self._draw_static(img, cam)
                self._static = img
            return self._static.copy()
        img = Image.new("RGB", (W * SS, H * SS), NAVY)
        self._draw_static(img, cam, draw_in)
        return img

    def render(self, t: float, cam: Cam = HOME, *, draw_in: dict | None = None, senado_col=WARNING, senado_dens=0.5,
               senado_alpha=1.0, dots_alpha=1.0, labels: dict | None = None, pin: tuple | None = None,
               pin_label_alpha=0.0, ahpo: dict | None = None, staff: dict | None = None,
               route: dict | list | None = None, detour: dict | None = None, walkers=(), lane_k: float = 0.0, lane_w: float = 17.0, lane=None,
               label_fade: float = 1.0) -> Image.Image:
        img = self.base(cam, draw_in)
        d = ImageDraw.Draw(img, "RGBA")
        z = cam.zoom
        wz = z ** 0.6
        # approved detour (dashed, step-free)
        if detour:
            s1 = DETOUR_PATH.length * detour["k"]
            if s1 > 1:
                path_c = Polyline([cam(p) for p in DETOUR_PATH.pts])
                dashed(d, path_c, 0, s1 * z, SAFE, 6 * wz, phase=-detour.get("phase", 0.0), alpha=detour.get("alpha", 1.0))
        # her main route: dotted while it is only her plan (S01); in S18 dashed in the vest colour while staff check
        # it (the dashes run along it); solid otherwise. `route` is one dict or a list of them (S18 draws both).
        for rt in ([route] if isinstance(route, dict) else route or []):
            s0, s1 = rt["s0"], rt["s1"]
            if s1 > s0 + 1:
                if rt.get("style") in ("dotted", "dashed"):
                    path_c = Polyline([cam(p) for p in MAIN_PATH.points(s0, s1)])
                    if rt["style"] == "dotted":
                        dashed(d, path_c, 0, path_c.length, INK, 4.5 * wz, dash=0.01, gap=13.0 * wz,
                               phase=-rt.get("phase", 0.0), alpha=rt.get("alpha", 1.0))
                    else:
                        dashed(d, path_c, 0, path_c.length, rt.get("colour", INK), 5 * wz, dash=16.0 * wz, gap=10.0 * wz,
                               phase=-rt.get("phase", 0.0), alpha=rt.get("alpha", 1.0))
                else:
                    pts = [cam(p) for p in MAIN_PATH.points(s0, s1)]
                    poly_line(d, pts, INK, 5 * wz, rt.get("alpha", 1.0) * 0.9)
        # people dots
        r_dot = 4.6 * wz
        if dots_alpha > 0:
            for p, a in self.dots.street_positions(t):
                if a > 0:
                    disc(d, cam(p), r_dot, PEOPLE_DOT, a * dots_alpha * 0.85)
            for p, a in self.dots.cluster_positions(t, senado_dens, (lane or MAIN_PATH) if lane_k > 0 else None, lane_k, lane_w):
                disc(d, cam(p), r_dot, PEOPLE_DOT, a * dots_alpha * 0.9)
        for p, a in walkers:
            disc(d, cam(p), r_dot, PEOPLE_DOT, a)
        # Senado: the only data-driven colour on the map
        if senado_alpha > 0:
            sp = cam(POS["senado_square"])
            crit = clamp((sum(senado_col) - sum(WARNING)) / max(1, (sum(CRITICAL) - sum(WARNING))))
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 0.9 * t)
            halo_r = (SENADO_R + 10 + 8 * pulse * crit) * wz
            disc(d, sp, halo_r, senado_col, senado_alpha * (0.16 + 0.10 * crit))
            disc(d, sp, SENADO_R * wz, senado_col, senado_alpha, outline=INK, width=2)
        # destination pin (Company of Jesus Square)
        if pin:
            alpha, dy = pin
            if alpha > 0:
                tip = cam(POS["jesus_square"])
                pin_shape(d, (tip[0], tip[1] + dy), alpha, scale=wz)
        # labels: zh over en, with a navy halo for legibility over dots and streets
        for zid, a in (labels or {}).items():
            a *= label_fade
            if a <= 0:
                continue
            x, y = cam(POS[zid])
            r = (SENADO_R if zid == "senado_square" else DISC_R) * wz
            lx = x + r + LABEL_DX.get(zid, 16)
            rise = (1 - a) * 8
            text2x(img, (lx, y - 3 + rise), ZONES[zid]["name_zh"], 24, 700, INK, a, anchor="ls", stroke=3)
            text2x(img, (lx, y + 23 + rise), LABEL_EN[zid], 22, 500, INK_2, a, anchor="ls", stroke=3)
        if pin_label_alpha > 0 and pin:
            tip = cam(POS["jesus_square"])
            a = pin_label_alpha * label_fade
            text2x(img, (tip[0] - 50, tip[1] - 46), "view of the Ruins", 22, 500, INK, a, anchor="rs", stroke=3)
            text2x(img, (tip[0] - 50, tip[1] - 20), "from the square below", 22, 500, INK, a, anchor="rs", stroke=3)
        # Mrs Chan, her tag, and the staff member
        if staff and staff.get("alpha", 0) > 0:
            self._marker(img, "staff", cam(staff["p"]), 18 * wz * staff.get("scale", 1.0), staff["alpha"])
        if ahpo and ahpo.get("alpha", 0) > 0:
            p = cam(ahpo["p"])
            r = 21 * wz * ahpo.get("scale", 1.0)
            if ahpo.get("ring", 0) > 0:
                k = ahpo["ring"]
                rr = r + 6 + 26 * k
                x, y = _s(p)
                d.ellipse((x - rr * SS, y - rr * SS, x + rr * SS, y + rr * SS), outline=_rgba(WARNING, (1 - k) * 0.8), width=3 * SS)
            self._marker(img, "ahpo", p, r, ahpo["alpha"])
            ta = ahpo.get("tag", 0.0) * label_fade
            if ta > 0:
                tg = tag_sprite(NAME)
                tx = p[0] * SS - r * SS - 10 * SS - tg.width + (1 - ta) * 10 * SS
                ty = p[1] * SS - tg.height / 2
                paste(img, tg, (tx, ty), ta)
        return img.reduce(SS)

    @staticmethod
    def _marker(img, kind, p, r, alpha):
        spr = marker_sprite(kind, max(4, int(round(r * SS))))
        paste(img, spr, (p[0] * SS - spr.width / 2, p[1] * SS - spr.height / 2), alpha)


# ---------------------------------------------------------------- eye level: a wall of backs, from a wheelchair

class EyeLevel:
    """Mrs Chan's seated view: grey silhouettes (rounded rectangles + circles) swaying ahead, armrests in front."""
    MARGIN = 280

    def __init__(self, seed: int = 11):
        rng = random.Random(seed)
        self.H2 = H + 2 * self.MARGIN
        self.bg = self._background(rng)
        self.people = []
        bottom = H + self.MARGIN + 80          # frame y the bodies extend to (pivot of the sway)
        rows = [  # (count, S range, head-top range, colour, rim, sway deg, spacing jitter)
            (20, (96, 124), (262, 312), (128, 138, 154), (156, 166, 182), (0.35, 0.6)),
            (12, (188, 236), (150, 214), (104, 113, 130), (138, 148, 166), (0.45, 0.75)),
            (6, (400, 470), (34, 120), (80, 88, 104), (118, 128, 146), (0.55, 0.85)),
        ]
        kinds_pool = ["plain", "plain", "backpack", "long", "bun", "hat", "plain", "backpack", "long"]
        for ri, (n, srange, trange, col, rim, sway) in enumerate(rows):
            span = W + 220
            for i in range(n):
                S = rng.uniform(*srange)
                cx = -110 + span * (i + 0.5) / n + rng.uniform(-0.18, 0.18) * span / n
                top = rng.uniform(*trange)
                kind = rng.choice(kinds_pool)
                if ri == 1 and i in (3, 8):
                    kind = "phone"
                if ri == 2 and i == 1:
                    kind = "backpack"
                tint = rng.uniform(-7, 7)
                c = tuple(int(clamp(v + tint, 0, 255)) for v in col)
                rc = tuple(int(clamp(v + tint, 0, 255)) for v in rim)
                spr, pivot = self._person(S, bottom - top, c, rc, kind, rim_px=(1.2, 2.0, 3.0)[ri])
                self.people.append(dict(spr=spr, pivot=pivot, x=cx, top=top, amp=rng.uniform(*sway) * rng.choice((-1, 1)),
                                        f=rng.uniform(0.22, 0.42), ph=rng.uniform(0, 6.28), dx=rng.uniform(2, 6) * (ri + 1) / 3,
                                        fdx=rng.uniform(0.08, 0.16)))
        self.arm = self._armrests()
        self.vignette = self._vignette()

    # --- static layers
    def _background(self, rng) -> Image.Image:
        m = self.MARGIN
        ys = np.arange(self.H2, dtype=np.float32)[:, None]
        top, mid = np.array((32, 46, 74), np.float32), np.array((16, 25, 44), np.float32)
        k = np.clip((ys - 0) / (m + 620), 0, 1)
        col = top * (1 - k) + mid * k
        k2 = np.clip((ys - (m + 620)) / 400, 0, 1)
        col = col * (1 - k2) + np.array(NAVY, np.float32) * k2
        arr = np.repeat(col[:, None, :], W, axis=1).reshape(self.H2, W, 3)
        img = Image.fromarray(arr.astype(np.uint8), "RGB")
        # a row of old facades above the crowd (only glimpsed between heads)
        d = ImageDraw.Draw(img, "RGBA")
        x = -40
        while x < W + 40:
            bw = rng.uniform(170, 300)
            ty = m + rng.uniform(30, 150)
            d.rectangle((x, ty, x + bw - 6, m + 620), fill=(27, 40, 66, 255))
            d.rectangle((x - 4, ty, x + bw - 2, ty + 9), fill=(44, 60, 92, 255))           # cornice
            ncol = max(2, int(bw // 64))
            for row in range(3):
                for j in range(ncol):
                    wx = x + 18 + j * (bw - 36) / ncol
                    wy = ty + 34 + row * 92
                    ww, wh = (bw - 36) / ncol - 22, 58
                    d.rounded_rectangle((wx, wy, wx + ww, wy + wh), radius=int(min(ww / 2, 16)), fill=(38, 55, 88, 255))
            x += bw
        return img

    @staticmethod
    def _person(S, total_h, col, rim, kind, rim_px=2.0):
        q = 2
        pad = int(S * 0.36)
        topm = int(S * (0.62 if kind == "phone" else 0.16))
        w_, h_ = int(S + 2 * pad), int(total_h + topm)
        img = Image.new("RGBA", (w_ * q, h_ * q), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx = w_ / 2
        hw, hh = 0.40 * S, 0.50 * S
        sy = topm + hh * 0.93

        def shape(oy, base, dark):
            def R(b):
                return [v * q for v in (b[0], b[1] + oy, b[2], b[3] + oy)]
            d.rounded_rectangle(R((pad, sy, pad + S, h_ + 40)), radius=int(0.30 * S * q), fill=base)
            d.rectangle(R((cx - 0.09 * S, topm + hh * 0.6, cx + 0.09 * S, sy + 0.12 * S)), fill=base)
            if kind == "long":
                d.rounded_rectangle(R((cx - 0.215 * S, topm + 0.18 * S, cx + 0.215 * S, sy + 0.30 * S)), radius=int(0.12 * S * q), fill=dark)
            d.ellipse(R((cx - hw / 2, topm, cx + hw / 2, topm + hh)), fill=base if kind != "long" else dark)
            if kind == "bun":
                d.ellipse(R((cx - 0.09 * S, topm - 0.10 * S, cx + 0.09 * S, topm + 0.08 * S)), fill=dark)
            if kind == "hat":
                d.ellipse(R((cx - 0.34 * S, topm + 0.13 * S, cx + 0.34 * S, topm + 0.25 * S)), fill=dark)
                d.rounded_rectangle(R((cx - 0.17 * S, topm - 0.04 * S, cx + 0.17 * S, topm + 0.2 * S)), radius=int(0.08 * S * q), fill=dark)
            if kind == "backpack":
                d.rounded_rectangle(R((cx - 0.30 * S, sy + 0.14 * S, cx + 0.30 * S, sy + 0.80 * S)), radius=int(0.12 * S * q), fill=dark)
            if kind == "phone":
                ax = pad + 0.86 * S
                d.rounded_rectangle(R((ax - 0.055 * S, topm - 0.40 * S, ax + 0.055 * S, sy + 0.25 * S)), radius=int(0.05 * S * q), fill=base)
                d.rounded_rectangle(R((ax - 0.11 * S, topm - 0.60 * S, ax + 0.11 * S, topm - 0.32 * S)), radius=int(0.03 * S * q), fill=dark)

        dark = tuple(max(0, v - 16) for v in col)
        shape(0, (*rim, 255), (*rim, 255))
        shape(rim_px, (*col, 255), (*dark, 255))
        img = img.resize((w_, h_), Image.LANCZOS)
        return img, (w_ / 2, h_ - 1)

    def _armrests(self) -> Image.Image:
        q = 2
        img = Image.new("RGBA", (W * q, H * q), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        def P(pts):
            return [(x * q, y * q) for x, y in pts]

        for mirror in (False, True):
            def M(pts):
                return [((W - x) if mirror else x, y) for x, y in pts]
            fx = 1642
            # support tube (outside the caption box, x > 1660 / < 260)
            d.line(P(M([(fx + 40, 830), (fx + 62, 1090)])), fill=(92, 100, 116, 255), width=22 * q)
            d.line(P(M([(fx + 34, 832), (fx + 55, 1090)])), fill=(150, 158, 172, 255), width=4 * q)
            # side face, top face, rounded front end
            d.polygon(P(M([(fx, 790), (1990, 862), (1990, 968), (fx, 834)])), fill=(29, 32, 41, 255))
            d.polygon(P(M([(fx, 768), (1990, 812), (1990, 866), (fx, 792)])), fill=(58, 64, 79, 255))
            ex = fx if not mirror else W - fx
            d.ellipse(P([(ex - 15, 768), (ex + 15, 834)]), fill=(34, 38, 48, 255))
            d.line(P(M([(fx + 6, 769), (1990, 813)])), fill=(96, 104, 122, 255), width=3 * q)
        img = img.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.8))
        return img

    @staticmethod
    def _vignette() -> Image.Image:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.46) / (H * 0.70)) ** 2)
        a = np.clip((r - 0.62) / 0.55, 0, 1) ** 1.6 * 150
        arr = np.zeros((H, W, 4), np.uint8)
        arr[..., 3] = a.astype(np.uint8)
        return Image.fromarray(arr, "RGBA")

    # --- per frame
    def crowd(self, t: float) -> Image.Image:
        canvas = self.bg.copy()
        m = self.MARGIN
        for p in self.people:
            ang = p["amp"] * math.sin(2 * math.pi * p["f"] * t + p["ph"])
            dx = p["dx"] * math.sin(2 * math.pi * p["fdx"] * t + p["ph"] * 1.7)
            spr = p["spr"].rotate(ang, resample=Image.BICUBIC, center=p["pivot"], translate=(dx, 0))
            x = p["x"] - spr.width / 2
            y = m + p["top"] - (spr.height - (H + m + 80 - p["top"]))
            canvas.paste(spr, (int(round(x)), int(round(y))), spr)
        return canvas

    def frame(self, t: float, crowd_dy: float = 0.0, arm_dy: float = 0.0, push: float = 1.0) -> Image.Image:
        canvas = self.crowd(t)
        m = self.MARGIN
        top = m - crowd_dy
        cx, cy = W / 2, top + H * 0.40
        bw, bh = W / push, H / push
        box = (cx - bw / 2, cy - bh * 0.40, cx + bw / 2, cy + bh * 0.60)
        view = canvas.resize((W, H), Image.BICUBIC, box=box)
        view.paste(self.vignette, (0, 0), self.vignette)
        view.paste(self.arm, (0, int(round(arm_dy))), self.arm)
        return view
