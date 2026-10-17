"""S05 · Team roll call and title card (0:39.5-0:48.0, 8.5 s).

Storyboard: docs/video/script.md section 3, row S05; section 2 "Team roles" (four members, [MEMBER 3] carries both
Engineering and Business); section 5D and section 6 "team_footage" (what to film); docs/video/shotlist.json, entry
S05. Section 4 has no claims row for S05 (no numbers are spoken or shown).

Data sources:
  - docs/video/shotlist.json: the shot duration (end_s - start_s) and the narration (asserted below, and checked
    against the storyboard row): four one-line cuts, M1 T, M2 S, M3 E and B, M4 M, then all four together.
  - docs/video/script.md, section 2 "Team roles": the STEMB letters each member's tile strip lights (checked).
  - video/build/guide/S05.wav (video/guide.py): the beats are keyed to its word boundaries.
  - shared/zones.json: the 7 zones and 7 street links that collapse into the wordmark, and the step-free route
    (Senado Square -> St. Dominic's -> Rua de S. Paulo -> Company of Jesus Square, no stairs) drawn on M4's map prop.
  - ml/models/metrics.json: bar heights on M2's printed-F1-chart prop (per_horizon.h5/h10/h15, test f1_macro vs
    persistence_baseline test f1_macro). The prop is a pictogram: no numbers are drawn.

The team has not filmed yet, so every member cut and the group shot is an amber "[TEAM FOOTAGE]" slate to swap later.
Outputs:
  - video/build/mg/S05.mp4: the whole shot (slates + title build + silent hold).
  - video/build/overlays/S05_title.mov: the title build alone (band, question, navy scrim, graph -> wordmark), with
    alpha, full shot length, so it can be laid over the real group footage at assembly.
  - video/build/mg/stills/S05_*.png: layout checks at the key beats.
Not drawn here (added at assembly): burned-in captions and the speaker lower-thirds. The storyboard gives S05 no
chapter card, badge or footer.

Run: .venv/bin/python video/mg/S05.py
"""
from __future__ import annotations

import heapq
import json
import math
import re
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F403

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S05"
_entry = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_entry["end_s"] - _entry["start_s"], 3)  # 8.5 s

# The narration, verbatim (shotlist.json and the storyboard row must agree); the slates and BEATS follow it.
NARRATION = ("[M1] Technology. [M2] Science. [M3] Engineering and business. [M4] Medicine. "
             "[ALL] We are CrowdPulse Macau.")
assert _entry["narration"] == NARRATION, "narration changed: re-measure the guide voice and re-key BEATS"
_script = (ROOT / "docs" / "video" / "script.md").read_text()
_row = next(l for l in _script.splitlines() if l.startswith(f"| {SHOT} |"))
assert [c.strip() for c in _row.strip().strip("|").split(" | ")][3] == NARRATION, "storyboard row S05 disagrees"
ROLL = dict(re.findall(r"\[(M\d|ALL)\]\s*([^\[]+?)\s*(?=\[|$)", NARRATION))  # speaker -> line
# STEMB letters per member, from the "Team roles" table (section 2): "| [MEMBER 3] | **E** Engineering · **B** ..."
ROLE_LETTERS = {f"M{n}": "".join(re.findall(r"\*\*([STEMB])\*\*", cell))
                for n, cell in re.findall(r"^\| \[MEMBER (\d)\] \| ([^|]+) \|", _script, re.M)}

# Times in seconds from the shot start, keyed to the guide voice (video/build/guide/S05.wav, from video/guide.py),
# which assemble.py starts 0.2 s into the shot. Word boundaries: its pauses (ffmpeg silencedetect=noise=-35dB:d=0.08)
# and, inside the last line, its 10 ms energy envelope. Speech, in shot time:
#   0.20-1.00 "Technology."  1.25-1.96 "Science."  2.19-3.54 "Engineering and business."  3.78-4.41 "Medicine."
#   4.66-6.23 "We are CrowdPulse Macau." ("are" 4.99, "CrowdPulse" 5.33-5.78, "Macau" 5.83-6.23)
#   6.23-8.5 silence; the title card is complete for the 2 s hold from 6.5.
# Each member cut is a hard cut on the first sound of that member's line (the first one is the shot's first frame).
# The title build (scrim to hold) keeps its timing. re-key to the real voice take
BEATS = {
    "m1": 0.0,          # [M1] "Technology."                (from 0.20)
    "m2": 1.25,         # [M2] "Science."                   (hard cut)
    "m3": 2.19,         # [M3] "Engineering and business."  (hard cut; E and B lit)
    "m4": 3.78,         # [M4] "Medicine."                  (hard cut)
    "group": 4.66,      # [ALL] "We are CrowdPulse Macau."  (hard cut to the group slate, all five letters lit)
    "question": 4.86,   # "We...": the research question rises on a band under the group (on screen 3.6 s to the end)
    "scrim": 5.0,       # "are": navy starts to cover the group shot (fully covered ~0.9 s later)
    "graph_in": 5.1,    # "are": the 7-zone graph draws in
    "collapse": 5.5,    # "CrowdPulse": the graph shrinks into the mark; the wordmark unrolls on "Macau" (5.86-6.46)
    "challenge": 6.1,   # "Responsible AI · Challenge 2(c)" settles as "Macau" ends
    "hold": 6.5,        # silence: title card held to the end of the shot (2 s, never cut, section 6)
}
assert BEATS["hold"] == round(DURATION - 2.0, 3), "the silent title hold is 2 s"

COL_DUR, COL_STAGGER = 0.6, 0.012   # graph collapse: duration and per-node stagger (s)
WORD_DELAY, WORD_DUR = 0.36, 0.6    # wordmark wipe: starts this long after "collapse", lasts this long (s)
WIPE_FEATHER = 220                  # soft leading edge of the wordmark wipe (px), wider than one frame's travel

SS = 2  # supersampling factor for shapes (drawn at 2x, downsampled with LANCZOS)

# ---------- data ----------

ZG = zone_graph()
ZONES = ZG["zones"]
EDGES = ZG["edges"]
ZONE_IDX = {z["id"]: i for i, z in enumerate(ZONES)}

METRICS = json.loads((ROOT / "ml" / "models" / "metrics.json").read_text())
F1_PAIRS = [(METRICS["per_horizon"][f"h{h}"]["test"]["f1_macro"],
             METRICS["per_horizon"][f"h{h}"]["persistence_baseline"]["test"]["f1_macro"]) for h in METRICS["horizons"]]


def step_free_route(src: str = "senado_square", dst: str = "jesus_square") -> list[tuple[str, str]]:
    """Shortest route by length_m over links without stairs (shared/zones.json); returns its links."""
    adj: dict[str, list[tuple[str, float]]] = {}
    for e in EDGES:
        if e.get("has_stairs"):
            continue
        adj.setdefault(e["from"], []).append((e["to"], e["length_m"]))
        adj.setdefault(e["to"], []).append((e["from"], e["length_m"]))
    dist, prev, pq = {src: 0.0}, {}, [(0.0, src)]
    while pq:
        dd, u = heapq.heappop(pq)
        if u == dst:
            break
        for v, w_ in adj.get(u, []):
            if dd + w_ < dist.get(v, 1e18):
                dist[v], prev[v] = dd + w_, u
                heapq.heappush(pq, (dd + w_, v))
    path, node = [], dst
    while node != src:
        path.append((prev[node], node))
        node = prev[node]
    return path[::-1]


ROUTE = {frozenset(p) for p in step_free_route()}

MEMBERS = [  # roll-call order (storyboard): T, S, E + B, M; "word" is the member's line without its full stop
    dict(beat="m1", tag="[MEMBER 1]", letters="T", word=ROLL["M1"].rstrip("."), prop="phone",
         film="head-and-shoulders, holding a phone on a clamp. Screen off, unless the app was really installed "
              "on that phone (then the Setup tab, no street clip). Nothing that suggests a field run."),
    dict(beat="m2", tag="[MEMBER 2]", letters="S", word=ROLL["M2"].rstrip("."), prop="f1",
         film="head-and-shoulders, holding the printed F1 chart."),
    dict(beat="m3", tag="[MEMBER 3]", letters="EB", word=ROLL["M3"].rstrip("."), prop="laptop",
         film="head-and-shoulders, with a laptop showing the server log."),
    dict(beat="m4", tag="[MEMBER 4]", letters="M", word=ROLL["M4"].rstrip("."), prop="map",
         film="head-and-shoulders, holding the printed step-free route map."),
]
assert [m["beat"].upper() for m in MEMBERS] == [k for k in ROLL if k != "ALL"], "one slate per member line, in order"
assert {m["beat"].upper(): m["letters"] for m in MEMBERS} == ROLE_LETTERS, ROLE_LETTERS
assert {l for m in MEMBERS for l in m["letters"]} == {l for l, _ in STEMB}, "the four members cover all of STEMB"

# ---------- text of the title card (storyboard, verbatim) ----------

TITLE_A, TITLE_B = "CrowdPulse", "Macau"
QUESTION = ("Our question: can ordinary phones, sending only numbers, help forecast crowds "
            "without identifying anyone?")
CHALLENGE = "Responsible AI · Challenge 2(c)"
GROUP_LABEL = "All four"
assert len(MEMBERS) == 4 and GROUP_LABEL.lower().endswith("four"), "the group label names the team size"
GROUP_FILM = f"all four: '{ROLL['ALL'].rstrip('.')}'"   # all four: 'We are CrowdPulse Macau'

# ---------- layout ----------

PANEL = (60, 48, 1860, 780)          # slate panel; ends above the lower-third (y 795) and caption (y 900) slots
VF = (1000, 176, 1800, 626)          # 16:9 viewfinder inside the slate
LX = 124                             # left column x
LOCK_Y = 372                         # vertical centre of the mark + wordmark lockup
Q_Y = 516                            # top of the question's first line
Q_SIZE, Q_W = 44, 1320
BAND = (458, 512, 646, 698)          # band ramp-in top, flat top, flat bottom, ramp-out bottom
CH_Y = 690                           # top of the challenge pill
GRAPH_BIG = (900, 96, 1300, 436)     # where the zone graph draws in (right of the group slate's STEMB strip)
R_BIG, R_SMALL = 18.0, 10.0          # node radii, big graph -> mark
EW_BIG, EW_SMALL = 6.0, 4.4          # link widths
MARK_H = 150                         # height of the mark (zone graph) in the lockup
WORD_SIZE = 118
GREG = (300, 56, 1420, 520)          # region the graph animation is drawn in
PINK = (232, 121, 249)               # stairs links (as in style.draw_zone_graph)
LINK = (112, 128, 156)               # zone links (a touch lighter than INK_3 so the small mark reads)
SIL = (46, 64, 98)                   # silhouette colour in the viewfinder
PAPER = (236, 241, 248)


def S(v: float) -> int:
    return int(round(v * SS))


def SB(box) -> tuple[int, int, int, int]:
    return tuple(S(v) for v in box)


# ---------- small drawing helpers (own, not in style.py) ----------

def dashed_line(d: ImageDraw.ImageDraw, p0, p1, colour, width: int, dash: float, gap: float) -> None:
    (x0, y0), (x1, y1) = p0, p1
    length = math.hypot(x1 - x0, y1 - y0)
    if length < 1:
        return
    n = max(1, round((length + gap) / (dash + gap)))
    dl = max(1.0, (length - (n - 1) * gap) / n)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    for i in range(n):
        s0 = i * (dl + gap)
        s1 = min(length, s0 + dl)
        d.line([(x0 + ux * s0, y0 + uy * s0), (x0 + ux * s1, y0 + uy * s1)], fill=colour, width=width)


def dashed_rrect(d: ImageDraw.ImageDraw, box, r: int, colour, width: int, dash: float, gap: float) -> None:
    """Rounded rectangle with dashes on all four sides (style.rounded's dash only does top and bottom)."""
    x0, y0, x1, y1 = box
    h = width / 2
    d.arc((x0, y0, x0 + 2 * r, y0 + 2 * r), 180, 270, fill=colour, width=width)
    d.arc((x1 - 2 * r, y0, x1, y0 + 2 * r), 270, 360, fill=colour, width=width)
    d.arc((x1 - 2 * r, y1 - 2 * r, x1, y1), 0, 90, fill=colour, width=width)
    d.arc((x0, y1 - 2 * r, x0 + 2 * r, y1), 90, 180, fill=colour, width=width)
    g = gap + dash * 0.25
    if x1 - x0 > 2 * (r + g):   # straight sides only where there is room (a pill has none on its ends)
        dashed_line(d, (x0 + r + g, y0 + h), (x1 - r - g, y0 + h), colour, width, dash, gap)
        dashed_line(d, (x0 + r + g, y1 - h), (x1 - r - g, y1 - h), colour, width, dash, gap)
    if y1 - y0 > 2 * (r + g):
        dashed_line(d, (x0 + h, y0 + r + g), (x0 + h, y1 - r - g), colour, width, dash, gap)
        dashed_line(d, (x1 - h, y0 + r + g), (x1 - h, y1 - r - g), colour, width, dash, gap)


def alpha_mul(img: Image.Image, k: float) -> Image.Image:
    if k >= 0.999:
        return img
    a = np.array(img)
    a[..., 3] = (a[..., 3].astype(np.float32) * clamp(k)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def text_layer(draw) -> tuple[Image.Image, tuple[int, int]]:
    """Runs draw(img) on a transparent frame and returns the cropped result and its offset."""
    img = transparent()
    draw(img)
    bbox = img.getbbox()
    return img.crop(bbox), (bbox[0], bbox[1])


def down(layer: Image.Image) -> Image.Image:
    return layer.resize((layer.width // SS, layer.height // SS), Image.LANCZOS)


# ---------- zone-graph geometry ----------

def graph_positions(box) -> list[tuple[float, float]]:
    proj = project(box)
    return [proj(z["lat"], z["lon"]) for z in ZONES]


def _graph_extent() -> tuple[float, float]:
    pts = graph_positions((0, 0, 100000, MARK_H))
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def lockup_layout() -> dict:
    fa = text_font(TITLE_A, WORD_SIZE, 700)
    fb = text_font(TITLE_B, WORD_SIZE, 600)
    wa = fa.getlength(TITLE_A + " ")
    wb = fb.getlength(TITLE_B)
    mark_w, _ = _graph_extent()
    gap = 52
    total = mark_w + gap + wa + wb
    x0 = (W - total) / 2
    mark_box = (x0, LOCK_Y - MARK_H / 2, x0 + mark_w, LOCK_Y + MARK_H / 2)
    tx = x0 + mark_w + gap
    return dict(mark_box=mark_box, tx=tx, wa=wa, wb=wb, text_end=tx + wa + wb)


LOCK = lockup_layout()
POS_BIG = graph_positions(GRAPH_BIG)
POS_SMALL = graph_positions(LOCK["mark_box"])
ORDER = sorted(range(len(ZONES)), key=lambda i: POS_BIG[i][1])  # stagger top (Ruins) to bottom


def draw_graph(d: ImageDraw.ImageDraw, pos, radii, alphas, edge_k, ew: float, dash: float, origin=(0, 0)) -> None:
    """Zone graph at SS scale; pos in frame pixels; links grow with edge_k (0..1)."""
    ox, oy = origin

    def P(p):
        return (S(p[0] - ox), S(p[1] - oy))

    for e in EDGES:
        i, j = ZONE_IDX[e["from"]], ZONE_IDX[e["to"]]
        a = min(alphas[i], alphas[j])
        if a <= 0 or edge_k <= 0:
            continue
        p0 = pos[i]
        p1 = lerp(pos[i], pos[j], edge_k)
        if e.get("has_stairs"):
            dashed_line(d, P(p0), P(p1), (*PINK, int(255 * a)), S(ew * 0.9), S(dash), S(dash))
        else:
            d.line([P(p0), P(p1)], fill=(*LINK, int(255 * a)), width=S(ew))
    for i in range(len(ZONES)):
        if alphas[i] <= 0 or radii[i] <= 0.2:
            continue
        x, y = P(pos[i])
        r = S(radii[i])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*CYAN, int(255 * alphas[i])))


def graph_state(t: float):
    """Node positions, radii, alphas and link growth of the graph at time t (None before it appears)."""
    if t < BEATS["graph_in"]:
        return None
    n = len(ZONES)
    pos, radii, alphas = [None] * n, [0.0] * n, [0.0] * n
    ks = []
    for rank, i in enumerate(ORDER):
        p_in = progress(t, BEATS["graph_in"] + rank * 0.025, 0.3)
        p_col = progress(t, BEATS["collapse"] + rank * COL_STAGGER, COL_DUR)
        ks.append(p_col)
        pos[i] = lerp(POS_BIG[i], POS_SMALL[i], p_col)
        radii[i] = lerp(R_BIG, R_SMALL, p_col) * (0.35 + 0.65 * p_in)
        alphas[i] = p_in
    k = sum(ks) / n
    edge_k = progress(t, BEATS["graph_in"] + 0.08, 0.34)
    return pos, radii, alphas, edge_k, lerp(EW_BIG, EW_SMALL, k), lerp(9.0, 4.0, k)


def graph_patch(t: float):
    st = graph_state(t)
    if st is None:
        return None
    pos, radii, alphas, edge_k, ew, dash = st
    gx0, gy0, gx1, gy1 = GREG
    layer = Image.new("RGBA", (S(gx1 - gx0), S(gy1 - gy0)), (0, 0, 0, 0))
    draw_graph(ImageDraw.Draw(layer), pos, radii, alphas, edge_k, ew, dash, origin=(gx0, gy0))
    return down(layer), (gx0, gy0)


# ---------- props (pictograms at SS scale, in viewfinder-local pixels) ----------

def prop_phone(d, cx, cy):
    """Phone on a clamp, screen off."""
    d.rounded_rectangle(SB((cx - 9, cy + 40, cx + 9, cy + 200)), S(5), fill=GREY)                 # clamp rod
    d.rounded_rectangle(SB((cx - 66, cy - 16, cx + 66, cy + 16)), S(8), fill=GREY)                 # clamp bar
    pw, ph = 86, 160
    d.rounded_rectangle(SB((cx - pw / 2, cy - ph / 2, cx + pw / 2, cy + ph / 2)), S(16), fill=INK_2)
    d.rounded_rectangle(SB((cx - pw / 2 + 6, cy - ph / 2 + 14, cx + pw / 2 - 6, cy + ph / 2 - 14)), S(9), fill=NAVY)
    for sx in (-1, 1):                                                                              # clamp jaws
        x_in = cx + sx * (pw / 2 - 4)
        x_out = cx + sx * (pw / 2 + 14)
        d.rounded_rectangle(SB((min(x_in, x_out), cy - 30, max(x_in, x_out), cy + 30)), S(6), fill=INK_3)


def prop_f1(d, cx, cy):
    """Printed F1 bar chart: model vs 'no change' per horizon (heights from ml/models/metrics.json, no numbers)."""
    w_, h_ = 270, 184
    x0, y0 = cx - w_ / 2, cy - h_ / 2
    d.rounded_rectangle(SB((x0, y0, x0 + w_, y0 + h_)), S(8), fill=PAPER)
    d.rounded_rectangle(SB((x0 + 20, y0 + 18, x0 + 150, y0 + 28)), S(4), fill=INK_3)                # title line
    base = y0 + h_ - 24
    top = y0 + 46
    d.line(SB((x0 + 18, base, x0 + w_ - 18, base)), fill=INK_3, width=S(2))
    gw = (w_ - 60) / len(F1_PAIRS)
    for gi, (model, persist) in enumerate(F1_PAIRS):
        gx = x0 + 30 + gi * gw + gw / 2
        for bi, (v, col) in enumerate(((model, BLUE), (persist, GREY))):
            bx = gx - 26 + bi * 28
            d.rectangle(SB((bx, base - (base - top) * v, bx + 22, base)), fill=col)


def prop_laptop(d, cx, cy):
    """Laptop showing a server log (abstract lines, no readable figures)."""
    sx0, sy0, sx1, sy1 = cx - 150, cy - 112, cx + 150, cy + 70
    d.rounded_rectangle(SB((sx0, sy0, sx1, sy1)), S(12), fill=(70, 82, 104))
    d.rounded_rectangle(SB((sx0 + 10, sy0 + 10, sx1 - 10, sy1 - 8)), S(6), fill=(6, 10, 20))
    widths = [150, 196, 120, 176, 208, 140, 184, 104]
    for i, wl in enumerate(widths):
        y = sy0 + 26 + i * 18
        d.rounded_rectangle(SB((sx0 + 24, y, sx0 + 46, y + 7)), S(3), fill=SAFE)
        d.rounded_rectangle(SB((sx0 + 54, y, sx0 + 54 + wl, y + 7)), S(3), fill=(78, 94, 120) if i % 3 else CYAN)
    d.polygon([(S(cx - 176), S(sy1)), (S(cx + 176), S(sy1)), (S(cx + 196), S(sy1 + 22)), (S(cx - 196), S(sy1 + 22))],
              fill=INK_3)


def prop_map(d, cx, cy):
    """Printed step-free route map: the zone graph with the no-stairs route (shared/zones.json) in green."""
    w_, h_ = 250, 210
    x0, y0 = cx - w_ / 2, cy - h_ / 2
    d.rounded_rectangle(SB((x0, y0, x0 + w_, y0 + h_)), S(8), fill=PAPER)
    pts = graph_positions((x0 + 40, y0 + 22, x0 + 140, y0 + h_ - 22))
    for e in EDGES:
        i, j = ZONE_IDX[e["from"]], ZONE_IDX[e["to"]]
        p0, p1 = (S(pts[i][0]), S(pts[i][1])), (S(pts[j][0]), S(pts[j][1]))
        if e.get("has_stairs"):
            dashed_line(d, p0, p1, PINK, S(5), S(4), S(3))
        elif frozenset((e["from"], e["to"])) in ROUTE:
            d.line([p0, p1], fill=SAFE, width=S(8))
        else:
            d.line([p0, p1], fill=(168, 178, 194), width=S(4))
    for x, y in pts:   # small dots, so the short stairs link (Ruins -> Company of Jesus Square) stays visible
        d.ellipse(SB((x - 5, y - 5, x + 5, y + 5)), fill=NAVY_3)
    wheelchair_icon(d, S(x0 + 196), S(y0 + 112), s=SS * 1.25, colour=SAFE, width=4)


PROPS = {"phone": prop_phone, "f1": prop_f1, "laptop": prop_laptop, "map": prop_map}


def silhouette(d, cx, top, s=1.0, col=SIL, outline=None, sw=215):
    """Head-and-shoulders framing guide (viewfinder-local pixels, drawn at SS scale)."""
    grow = 4 if outline else 0
    c = outline or col
    d.ellipse(SB((cx - 60 * s - grow, top - grow, cx + 60 * s + grow, top + 138 * s + grow)), fill=c)
    d.rectangle(SB((cx - 30 * s - grow, top + 110 * s, cx + 30 * s + grow, top + 180 * s)), fill=c)
    d.rounded_rectangle(SB((cx - sw * s - grow, top + 168 * s - grow, cx + sw * s + grow, top + 620 * s)),
                        S(min(150, sw * 0.7) * s), fill=c)


def viewfinder(member: dict | None) -> Image.Image:
    vw, vh = VF[2] - VF[0], VF[3] - VF[1]
    img = Image.new("RGBA", (S(vw), S(vh)), (*NAVY, 255))
    d = ImageDraw.Draw(img)
    if member:
        silhouette(d, vw / 2, 52)
        PROPS[member["prop"]](d, vw / 2, 340 if member["prop"] == "laptop" else 330)
    else:  # the group: one silhouette per member, centred, alternate ones a step back
        step = 168
        xs = [vw / 2 + (k - (len(MEMBERS) - 1) / 2) * step for k in range(len(MEMBERS))]
        for k, x in enumerate(xs):
            kw = dict(col=SIL if k % 2 else (56, 77, 114), sw=185)
            silhouette(d, x, 118 if k % 2 else 100, 0.6, outline=NAVY, **kw)
            silhouette(d, x, 118 if k % 2 else 100, 0.6, **kw)
    L, inset, wdt = 40, 22, 4                                                                       # corner brackets
    for (x, y, sx, sy) in ((inset, inset, 1, 1), (vw - inset, inset, -1, 1), (inset, vh - inset, 1, -1), (vw - inset, vh - inset, -1, -1)):
        d.line(SB((x, y, x + sx * L, y)), fill=INK_3, width=S(wdt))
        d.line(SB((x, y, x, y + sy * L)), fill=INK_3, width=S(wdt))
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, img.width - 1, img.height - 1), S(16), fill=255)
    img.putalpha(mask)
    return img


def camera_glyph(d, x, y, colour=WARNING):
    d.rounded_rectangle(SB((x, y, x + 34, y + 26)), S(6), fill=colour)
    d.polygon([(S(x + 36), S(y + 13)), (S(x + 50), S(y + 3)), (S(x + 50), S(y + 23))], fill=colour)


# ---------- slates (static, built once) ----------

WORD_SIZE, WORD_TOP, WORD_W = 112, 432, 836   # a member's line on the slate: size, top (one line), left column width
WORD_BAND = (432, 568)                        # a two-line word's glyphs: 30 px under the tag pill (402) and over
                                              # the tiles (598)


def word_layout(word: str) -> list[tuple[str, int, float]]:
    """[(text, size, baseline y)] for a member's line: one line at WORD_SIZE, or, when it is too long for the left
    column (M3's "Engineering and business"), two balanced lines at the largest size whose glyphs fit WORD_BAND,
    centred in it."""
    f = text_font(word, WORD_SIZE, 700)
    base = WORD_TOP + f.getmetrics()[0]                       # the baseline of a one-line word drawn from WORD_TOP
    if f.getlength(word) <= WORD_W:
        return [(word, WORD_SIZE, base)]
    words = word.split()
    a, b = min(((" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))),
               key=lambda p: max(text_size(p[0], WORD_SIZE, 700)[0], text_size(p[1], WORD_SIZE, 700)[0]))
    for size in range(WORD_SIZE, 40, -2):
        fa, fb = text_font(a, size, 700), text_font(b, size, 700)
        pitch = round(size * 1.08)
        top, bottom = fa.getbbox(a, anchor="ls")[1], pitch + fb.getbbox(b, anchor="ls")[3]
        if bottom - top <= WORD_BAND[1] - WORD_BAND[0] and max(fa.getlength(a), fb.getlength(b)) <= WORD_W:
            b1 = (WORD_BAND[0] + WORD_BAND[1]) / 2 - (top + bottom) / 2
            return [(a, size, b1), (b, size, b1 + pitch)]
    raise ValueError(f"no size fits {word!r}")


def build_slate(member: dict | None, index: int = 0) -> Image.Image:
    img = canvas(NAVY)
    shapes = Image.new("RGBA", (S(W), S(H)), (0, 0, 0, 0))
    d = ImageDraw.Draw(shapes)
    d.rounded_rectangle(SB(PANEL), S(26), fill=NAVY_2)
    dashed_rrect(d, SB(PANEL), S(26), WARNING, S(3), S(18), S(11))
    camera_glyph(d, LX, 121)
    shapes.alpha_composite(viewfinder(member), dest=(S(VF[0]), S(VF[1])))
    tile, gap = (84, 14) if member else (70, 12)
    strip_y = 598 if member else 300
    strip_x = LX if member else LX + text_size(GROUP_LABEL, 104, 700)[0] + 44
    lit = set(member["letters"]) if member else {l for l, _ in STEMB}   # M3 lights E and B; the group all five
    for i, (l, _) in enumerate(STEMB):
        x = strip_x + i * (tile + gap)
        d.rounded_rectangle(SB((x, strip_y, x + tile, strip_y + tile)), S(14), fill=CYAN if l in lit else NAVY_3)
    pill = None
    if member:
        tw, _ = text_size(member["tag"], 34, 700)
        pill = (LX, 342, LX + tw + 48, 402)
        d.rounded_rectangle(SB(pill), S(30), fill=NAVY)
        dashed_rrect(d, SB(pill), S(30), WARNING, S(3), S(10), S(7))
    img.alpha_composite(down(shapes))

    head = "[TEAM FOOTAGE]"
    draw_text(img, (LX + 64, 116), head, 30, 700, WARNING)
    hw, _ = text_size(head, 30, 700)
    sub = f"·  cut {index + 1} of {len(MEMBERS)}" if member else "·  group shot"
    draw_text(img, (LX + 64 + hw + 16, 120), sub, 26, 500, INK_3)
    if member:
        draw_text(img, (LX, 184), member["film"], 28, 500, INK, max_width=836, line_gap=1.3)
        draw_text(img, (pill[0] + 24, (pill[1] + pill[3]) / 2), member["tag"], 34, 700, WARNING, anchor="lm")
        for text, size, baseline in word_layout(member["word"]):
            draw_text(img, (LX - 4 * size / WORD_SIZE, baseline), text, size, 700, INK, anchor="ls")
    else:
        draw_text(img, (LX, 184), GROUP_FILM, 34, 600, INK, max_width=800)
        draw_text(img, (LX, 236), "same background as S19", 26, 500, INK_2)
        draw_text(img, (LX - 3, strip_y + tile / 2), GROUP_LABEL, 104, 700, INK, anchor="lm")
    for i, (l, _) in enumerate(STEMB):
        x = strip_x + i * (tile + gap)
        on = l in lit
        draw_text(img, (x + tile / 2, strip_y + tile / 2), l, 44 if member else 36, 800, NAVY if on else INK_3, anchor="mm")
    if member:  # (the group slate has no label: the question band covers that area from the "question" beat)
        draw_text(img, ((VF[0] + VF[2]) / 2, VF[3] + 22), "head-and-shoulders · identical framing · plain background",
                  22, 500, INK_3, anchor="ma")
    return img


SLATES = [build_slate(m, i) for i, m in enumerate(MEMBERS)]
GROUP_SLATE = build_slate(None)
NAVY_FULL = canvas(NAVY)


def base_at(t: float) -> Image.Image:
    if t >= BEATS["group"]:
        return GROUP_SLATE
    idx = 0
    for i, m in enumerate(MEMBERS):
        if t >= BEATS[m["beat"]]:
            idx = i
    return SLATES[idx]


# ---------- title layers (static pieces, built once) ----------

def _band() -> Image.Image:
    a0, a1, b0, b1 = BAND
    ys = np.arange(H, dtype=np.float32)
    up = np.clip((ys - a0) / (a1 - a0), 0, 1)
    dn = np.clip((b1 - ys) / (b1 - b0), 0, 1)
    prof = np.minimum(up, dn)
    prof = prof * prof * (3 - 2 * prof) * 0.9
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = NAVY
    arr[..., 3] = (prof[:, None] * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


BAND_IMG = _band()


def _glow() -> Image.Image:
    """Soft navy pool behind the big zone graph, so it reads over the group shot before the scrim closes."""
    xs, ys = [p[0] for p in POS_BIG], [p[1] for p in POS_BIG]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    rx, ry = (max(xs) - min(xs)) / 2 + 190, (max(ys) - min(ys)) / 2 + 120
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)
    k = np.clip((1.0 - r) / 0.55, 0, 1)
    k = k * k * (3 - 2 * k) * 0.82
    arr = np.zeros((H, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = NAVY
    arr[..., 3] = (k * 255).astype(np.uint8)
    return Image.fromarray(arr, "RGBA")


GLOW_IMG = _glow()
QUESTION_L = text_layer(lambda im: draw_text(im, (W / 2, Q_Y), QUESTION, Q_SIZE, 500, INK, anchor="ma",
                                             max_width=Q_W, line_gap=1.32))


def _challenge(im):
    tw, _ = text_size(CHALLENGE, 28, 600)
    box = (W / 2 - tw / 2 - 30, CH_Y, W / 2 + tw / 2 + 30, CH_Y + 52)
    rounded(im, box, 26, outline=NAVY_3, width=3)
    draw_text(im, (W / 2, CH_Y + 26), CHALLENGE, 28, 600, CYAN, anchor="mm")


CHALLENGE_L = text_layer(_challenge)


def _wordmark(im):
    draw_text(im, (LOCK["tx"], LOCK_Y), TITLE_A, WORD_SIZE, 700, INK, anchor="lm")
    draw_text(im, (LOCK["tx"] + LOCK["wa"], LOCK_Y), TITLE_B, WORD_SIZE, 600, CYAN, anchor="lm")


WORD_L = text_layer(_wordmark)
FINAL_GRAPH = graph_patch(DURATION + 10)  # the settled mark


def paste(dst: Image.Image, layer, k: float = 1.0, dy: float = 0.0) -> None:
    img, (x, y) = layer
    if k <= 0:
        return
    dst.alpha_composite(alpha_mul(img, k), dest=(int(x), int(round(y + dy))))


def wipe(dst: Image.Image, layer, reveal_x: float, feather: float = 90.0, k: float = 1.0, dy: float = 0.0) -> None:
    """Left-to-right reveal of a layer with a soft leading edge."""
    img, (x, y) = layer
    if reveal_x <= x - feather or k <= 0:
        return
    a = np.array(img)
    cols = x + np.arange(img.width, dtype=np.float32)
    m = np.clip((reveal_x - cols) / feather, 0, 1) * clamp(k)
    a[..., 3] = (a[..., 3].astype(np.float32) * m[None, :]).astype(np.uint8)
    dst.alpha_composite(Image.fromarray(a, "RGBA"), dest=(int(x), int(round(y + dy))))


def halos(dst: Image.Image, t: float) -> None:
    """One faint pulse at the start of the hold: each node of the mark sends out a small ring, top to bottom."""
    t0 = BEATS["hold"] + 0.1
    if t < t0 or t > t0 + 0.08 * len(ZONES) + 1.0:
        return
    gx0, gy0, gx1, gy1 = GREG
    patch = Image.new("RGBA", (S(gx1 - gx0), S(gy1 - gy0)), (0, 0, 0, 0))
    d = ImageDraw.Draw(patch)
    for rank, i in enumerate(ORDER):
        p = clamp((t - t0 - rank * 0.08) / 0.9)
        if p <= 0 or p >= 1:
            continue
        r = lerp(R_SMALL + 2, R_SMALL + 16, 1 - (1 - p) ** 2)
        a = 0.55 * ease(p / 0.25) * (1 - p)   # eased in over the first quarter, so the ring never pops on
        x, y = POS_SMALL[i]
        cx, cy = S(x - gx0), S(y - gy0)
        d.ellipse((cx - S(r), cy - S(r), cx + S(r), cy + S(r)), outline=(*CYAN, int(255 * a)), width=S(2.5))
    dst.alpha_composite(down(patch), dest=(gx0, gy0))


def title_layer(t: float) -> Image.Image:
    """Everything that lies over the group footage: transparent until the question beat."""
    L = transparent()
    if t < BEATS["question"]:
        return L
    L.alpha_composite(alpha_mul(BAND_IMG, progress(t, BEATS["question"], 0.45)))
    scrim = progress(t, BEATS["scrim"], 0.9)
    glow = progress(t, BEATS["graph_in"] - 0.1, 0.4)  # under the scrim, so the total cover only ever grows
    if glow > 0.004 and scrim < 0.999:
        L.alpha_composite(alpha_mul(GLOW_IMG, glow))
    if scrim > 0:
        L.alpha_composite(alpha_mul(NAVY_FULL, scrim))
    qk = progress(t, BEATS["question"] + 0.05, 0.5)
    paste(L, QUESTION_L, qk, dy=(1 - qk) * 14)
    if t >= BEATS["graph_in"]:
        settled = t >= BEATS["collapse"] + COL_STAGGER * len(ZONES) + COL_DUR + 0.02
        g = FINAL_GRAPH if settled else graph_patch(t)
        paste(L, g)
    wk = progress(t, BEATS["collapse"] + WORD_DELAY, WORD_DUR)
    if wk > 0:
        x0 = LOCK["tx"]
        wipe(L, WORD_L, lerp(x0, LOCK["text_end"] + WIPE_FEATHER, wk), feather=WIPE_FEATHER, k=min(1.0, wk * 2.5))
    paste(L, CHALLENGE_L, progress(t, BEATS["challenge"], 0.45), dy=(1 - progress(t, BEATS["challenge"], 0.45)) * 10)
    halos(L, t)
    return L


def frame(t: float) -> Image.Image:
    img = base_at(t).copy()
    img.alpha_composite(title_layer(t))
    return img


STILLS = {  # name: time (s)
    "m1_technology": BEATS["m1"] + 0.4,
    "m3_engineering_business": BEATS["m3"] + 0.4,
    "m4_medicine": BEATS["m4"] + 0.4,
    "group_all_four": BEATS["group"] + 0.1,
    "group_question": BEATS["graph_in"] - 0.1,
    "collapse": BEATS["collapse"] + 0.25,
    "wordmark": BEATS["collapse"] + WORD_DELAY + WORD_DUR * 0.55,
    "hold": BEATS["hold"] + 1.75,
}

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--stills-only", action="store_true")
    ap.add_argument("--check", nargs="*", type=float, help="only write check frames at these times (s)")
    ap.add_argument("--out", default=str(BUILD / "mg" / "stills" / "check"), help="folder for --check frames")
    args = ap.parse_args()
    if args.check is not None:
        out = Path(args.out)
        for tt in args.check:
            still(f"S05_t{tt:05.2f}", frame(tt), out_dir=out)
        sys.exit(0)
    for name, tt in STILLS.items():
        print("still", still(f"{SHOT}_{name}", frame(tt)))
    if not args.stills_only:
        print("video", render(SHOT, DURATION, frame))
        print("overlay", render_overlay(f"{SHOT}_title", DURATION, title_layer))
