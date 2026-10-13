"""Shot S06 (0:46.0-0:58.0, 12.0 s): "Why does it matter?"

[MEMBER 4] on camera for 4 s (a placeholder slate until the take is filmed), then voice-over over
the zone schematic with illustrative dots piling up at Senado Square, then, during the medical
sentence, a plain body-outline diagram whose only annotation is the research placeholder.

Data sources:
  - docs/video/shotlist.json, shot S06: duration (end_s - start_s) and the camera timecode.
  - shared/zones.json (through style.zone_graph / draw_zone_graph): zone positions, names, street
    links and which zones are entry points (where the illustrative dots come in).
  - docs/video/script.md, section 3, row S06: card, badge, footer and citation text (verbatim,
    checked against shotlist.json); the medical placeholder is read from the shotlist narration.
The dots are an illustration (badge ILLUSTRATION), not data. No medical mechanism is drawn or
written: the body diagram carries only the [TEAM TO RESEARCH - MEDICINE ...] placeholder.

Outputs:
  video/build/mg/S06.mp4                  the full shot (camera slate 0-4 s)
  video/build/overlays/S06_cam_overlay.mov  0-4 s card + footer with alpha, for the real camera take
  video/build/mg/stills/S06_*.png          layout checks

Run:  .venv/bin/python video/mg/S06.py            (stills, overlay and render)
      .venv/bin/python video/mg/S06.py --stills   (stills only)
"""
from __future__ import annotations

import bisect
import json
import math
import random
import re
import sys
from collections import deque

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S06"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 12.0 s
START_S = _shot["start_s"]

# Beats in seconds from the shot start, keyed to the narration at about 140 wpm (0.43 s a word),
# voice from 0.3 s: "Every Golden Week, the Ruins of St. Paul's and Senado | Square become
# dangerously crowded." then the medical sentence (placeholder, at most 12 words) from about 7 s.
# re-key to the real voice take
BEATS = {
    "card_in": 0.0,       # chapter card over the camera take (shown about 2 s)
    "voice_in": 0.3,      # "Every Golden Week" (source footer appears)
    "card_out": 2.3,      # card gone
    "schematic": 4.0,     # "...Senado Square": cut from camera to the zone schematic, badge on
    "pile_start": 4.2,    # "Square become": dots start to pile up at Senado
    "pile_full": 6.6,     # end of "dangerously crowded": the pile is complete
    "map_left": 6.55,     # pause after "crowded": the map slides left (done just after "medical")
    "medical": 7.0,       # medical sentence starts: body diagram comes in
    "annotation": 7.9,    # placeholder annotation lands (early in the medical sentence)
    "citation": 8.3,      # citation placeholder lands
}

# Text, verbatim from the storyboard (script.md section 3, S06; the same text is in shotlist.json).
CARD = "Why does it matter?"
FOOTER = "[TEAM TO RESEARCH: cited source for Golden Week crowding at the Ruins / Senado Square]"
CITATION = "[TEAM TO RESEARCH: medical source, year]"
for _txt in (CARD, FOOTER, CITATION):
    assert _txt in _shot["on_screen_text"], _txt
# The medical slot is the storyboard narration's own placeholder, read from the shot list so it
# stays word for word what the storyboard says.
MECHANISM = re.search(r"\[TEAM TO RESEARCH - MEDICINE:[^\]]*\]", _shot["narration"]).group(0)
SLATE_TAG = "[TEAM FOOTAGE]"
SLATE_WHAT = "[MEMBER 4], medium shot, eye level"
# Once the sourced sentence names a body region, set this to a point on the body (canvas pixels)
# and the annotation's leader line will point there; while it is None the bracket spans the whole
# body, so the diagram implies no mechanism.
MECH_TARGET: tuple[int, int] | None = None

SS = 3  # supersampling factor for shapes drawn smooth


# ---------- small helpers (local to this shot) ----------

class Sprite:
    """An RGBA image cropped to its content, with its canvas position."""

    def __init__(self, full: Image.Image | None = None, img: Image.Image | None = None, x: int = 0, y: int = 0):
        if full is not None:
            bb = full.getbbox() or (0, 0, 1, 1)
            self.img, self.x, self.y = full.crop(bb), bb[0], bb[1]
        else:
            self.img, self.x, self.y = img, x, y

    @property
    def box(self):
        return (self.x, self.y, self.x + self.img.width, self.y + self.img.height)


def with_alpha(im: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 0.999:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return out


def put(dst: Image.Image, im: Image.Image, x: float, y: float, alpha: float = 1.0) -> None:
    """Alpha-composites `im` at (x, y), clipped to the canvas, with extra opacity."""
    if alpha <= 0.001:
        return
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, dst.width - x), min(im.height, dst.height - y)
    if r <= l or b <= t:
        return
    src = im.crop((l, t, r, b)) if (l, t, r, b) != (0, 0, im.width, im.height) else im
    dst.alpha_composite(with_alpha(src, alpha), (x + l, y + t))


def put_sprite(dst, spr: Sprite, alpha=1.0, dx=0.0, dy=0.0):
    put(dst, spr.img, spr.x + dx, spr.y + dy, alpha)


def dashed_box(d: ImageDraw.ImageDraw, box, colour, width=3, dash=14, gap=9, radius=12, fill=None):
    """Rounded box with a dashed outline on all four sides (style.rounded dashes only top and bottom)."""
    x0, y0, x1, y1 = box
    if fill is not None:
        d.rounded_rectangle(box, radius, fill=fill)

    def run(a, b, fn):
        p = a
        while p < b:
            fn(p, min(p + dash, b))
            p += dash + gap

    run(x0 + radius, x1 - radius, lambda a, b: d.line([(a, y0), (b, y0)], fill=colour, width=width))
    run(x0 + radius, x1 - radius, lambda a, b: d.line([(a, y1), (b, y1)], fill=colour, width=width))
    run(y0 + radius, y1 - radius, lambda a, b: d.line([(x0, a), (x0, b)], fill=colour, width=width))
    run(y0 + radius, y1 - radius, lambda a, b: d.line([(x1, a), (x1, b)], fill=colour, width=width))
    hw = width / 2
    for (cx, cy, a0) in ((x0 + radius, y0 + radius, 180), (x1 - radius, y0 + radius, 270),
                         (x1 - radius, y1 - radius, 0), (x0 + radius, y1 - radius, 90)):
        d.arc((cx - radius + hw - width / 2, cy - radius + hw - width / 2, cx + radius - hw + width / 2,
               cy + radius - hw + width / 2), a0, a0 + 90, fill=colour, width=width)


def placeholder_box(text: str, size: int, max_w: int, pad_x: int = 22, pad_y: int = 16, weight: int = 600,
                    border: int = 3, radius: int = 14, full_width: bool = False) -> Image.Image:
    """A bracketed research placeholder, verbatim, in amber text inside an amber dashed box."""
    lines = wrap(text, size, weight, max_w - 2 * pad_x)
    lh = int(size * 1.32)
    tw = max(text_size(l, size, weight)[0] for l in lines)
    w_, h_ = (max_w if full_width else tw + 2 * pad_x), lh * len(lines) + 2 * pad_y
    im = Image.new("RGBA", (w_ + 2, h_ + 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dashed_box(d, (1, 1, w_, h_), (*WARNING, 255), width=border, radius=radius, fill=(*NAVY_2, 240))
    for i, l in enumerate(lines):
        draw_text(im, (1 + pad_x, 1 + pad_y + i * lh + lh / 2), l, size, weight, WARNING, anchor="lm")
    return im


def smooth_shapes(size, draw_fn) -> Image.Image:
    """Draws with draw_fn(d, s) on an SS-times larger RGBA canvas and downsamples (anti-aliased shapes)."""
    big = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), SS)
    return big.resize(size, Image.LANCZOS)


# ---------- the zone schematic and the illustrative dots ----------

G = zone_graph()
ZONES = {z["id"]: z for z in G["zones"]}
PROJ = project()                                  # the S01 schematic projection (style default box)
POS = {zid: PROJ(z["lat"], z["lon"]) for zid, z in ZONES.items()}
NODE_R = 26
SEN = "senado_square"
ADJ: dict[str, list[str]] = {zid: [] for zid in ZONES}
for e in G["edges"]:
    ADJ[e["from"]].append(e["to"])
    ADJ[e["to"]].append(e["from"])


def path_to_senado(src: str) -> list[str]:
    """Shortest path (by number of street links) from a zone to Senado, through zones.json edges."""
    prev, q = {src: None}, deque([src])
    while q:
        u = q.popleft()
        if u == SEN:
            break
        for v in ADJ[u]:
            if v not in prev:
                prev[v] = u
                q.append(v)
    out, u = [], SEN
    while u is not None:
        out.append(u)
        u = prev[u]
    return out[::-1]


def short_name(zid: str) -> str:  # same short names as style.draw_zone_graph
    return {"tercena_corridor": "Rua da Tercena", "rua_sao_paulo": "Rua de S. Paulo",
            "almeida_ribeiro": "Av. de Almeida Ribeiro"}.get(zid, ZONES[zid]["name"])


rng = random.Random(606)
DOT_R = 4.6
PILE_N, PILE_C = 84, 6.3                     # Vogel-spiral pile around Senado (radius ~ PILE_C*sqrt(N))
PILE_R = PILE_C * math.sqrt(PILE_N)
GOLD = math.pi * (3 - math.sqrt(5))
sx, sy = POS[SEN]
pile_slots = []
for i in range(PILE_N):
    r, th = PILE_C * math.sqrt(i + 0.5), i * GOLD
    pile_slots.append((sx + r * math.cos(th) + rng.uniform(-1.2, 1.2), sy + r * math.sin(th) + rng.uniform(-1.2, 1.2)))


def queue_slots(nb: str, n: int) -> list[tuple[float, float]]:
    """Dots backing up along the street from Senado towards neighbour `nb` (two loose lanes)."""
    bx, by = POS[nb]
    L = math.hypot(bx - sx, by - sy)
    ux, uy = (bx - sx) / L, (by - sy) / L
    vx, vy = -uy, ux
    out = []
    for k in range(n):
        dist = PILE_R + 7 + (k // 2) * 10.5
        lane = (-5.6 if k % 2 == 0 else 5.6) + rng.uniform(-1.3, 1.3)
        out.append((sx + ux * dist + vx * lane, sy + uy * dist + vy * lane))
    return out


Q_DOM = queue_slots("st_dominic", 10)
Q_ALM = queue_slots("almeida_ribeiro", 8)

# Dots that walk to Senado: entry zones of zones.json (Almeida Ribeiro; the Ruins side, which
# reaches Senado through Rua de S. Paulo and St. Dominic's) plus the squares on the way.
entry = [zid for zid, z in ZONES.items() if z.get("entry")]
north_sources = ["st_dominic", "st_dominic", "rua_sao_paulo", "jesus_square"]
south_sources = [z for z in entry if path_to_senado(z)[-2] == "almeida_ribeiro"]


def dot_path(src: str, slot) -> list[tuple[float, float]]:
    nodes = path_to_senado(src)[:-1]                     # drop Senado itself: the slot is the end
    lat = rng.uniform(-4.0, 4.0)
    pts = []
    for j, zid in enumerate(nodes):
        x, y = POS[zid]
        if j == 0:
            a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(4, 20)
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        else:
            pts.append((x + lat, y + lat * 0.6))
    pts.append(slot)
    return pts


movers = []  # each: path, cumulative lengths, start, end, phase
slots = [(s, None) for s in pile_slots] + [(s, "dom") for s in Q_DOM] + [(s, "alm") for s in Q_ALM]
n_all = len(slots)
p0, p1 = BEATS["pile_start"], BEATS["pile_full"]
for i, (slot, q) in enumerate(slots):          # inner slots fill first, queues last
    arrive = p0 + 0.55 + (p1 - p0 - 0.55) * (i / (n_all - 1)) ** 0.9 + rng.uniform(-0.06, 0.06)
    if q == "dom":
        src = rng.choice(north_sources)
    elif q == "alm":
        src = "almeida_ribeiro"
    else:
        src = rng.choice(north_sources + south_sources * 3)
    pts = dot_path(src, slot)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    dur = max(0.75, cum[-1] / 270.0)
    movers.append(dict(pts=pts, cum=cum, t0=arrive - dur, t1=arrive, ph=rng.uniform(0, 6.3), ph2=rng.uniform(0, 6.3)))

def seg_dist(p, a, b) -> float:
    """Distance from point p to the segment a-b."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    u = clamp(((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / (vx * vx + vy * vy))
    return math.hypot(p[0] - a[0] - u * vx, p[1] - a[1] - u * vy)


# Ambient people elsewhere (more at the Ruins, which the line names too); kept off the pile/queues.
taken = [s for s, _ in slots]
ambient = []
for zid, n, rad in (("ruins_st_paul", 26, 42), ("jesus_square", 10, 34), ("rua_sao_paulo", 6, 28),
                    ("st_dominic", 8, 32), ("almeida_ribeiro", 9, 34), ("tercena_corridor", 4, 26)):
    x, y = POS[zid]
    placed, tries = 0, 0
    while placed < n and tries < 4000:
        tries += 1
        a, rr = rng.uniform(0, 2 * math.pi), rad * math.sqrt(rng.random())
        p = (x + rr * math.cos(a), y + rr * math.sin(a))
        in_label = p[0] > x + NODE_R + 2 and abs(p[1] - y) < 22
        on_stairs = any(seg_dist(p, POS[e["from"]], POS[e["to"]]) < 10 for e in G["edges"] if e.get("has_stairs"))
        if not in_label and not on_stairs and all(math.hypot(p[0] - q[0], p[1] - q[1]) >= 11 for q in taken):
            taken.append(p)
            ambient.append(dict(p=p, ph=rng.uniform(0, 6.3), ph2=rng.uniform(0, 6.3)))
            placed += 1


def mover_pos(m, t):
    if t < m["t0"]:
        return None, 0.0
    k = ease((t - m["t0"]) / (m["t1"] - m["t0"]))
    s = k * m["cum"][-1]
    pts, cum = m["pts"], m["cum"]
    j = min(len(cum) - 2, max(0, bisect.bisect_left(cum, s) - 1))
    seg = cum[j + 1] - cum[j]
    u = 0 if seg <= 0 else (s - cum[j]) / seg
    x = pts[j][0] + (pts[j + 1][0] - pts[j][0]) * u
    y = pts[j][1] + (pts[j + 1][1] - pts[j][1]) * u
    if t > m["t1"]:  # settled: a slow sway, about a pixel
        x += 1.0 * math.sin(2 * math.pi * 0.42 * t + m["ph"])
        y += 0.8 * math.cos(2 * math.pi * 0.35 * t + m["ph2"])
    return (x, y), clamp((t - m["t0"]) / 0.25)


# Dot layer region (graph-local pixels), covering every dot position over the shot.
_all = [p for m in movers for p in m["pts"]] + [a["p"] for a in ambient]
DX0 = int(min(p[0] for p in _all) - 16)
DY0 = int(min(p[1] for p in _all) - 16)
DX1 = int(max(p[0] for p in _all) + 16)
DY1 = int(max(p[1] for p in _all) + 16)
DOT_RGB = Image.new("RGBA", (DX1 - DX0, DY1 - DY0), (*INK, 0))


def dots_layer(t: float) -> Image.Image:
    mask = Image.new("L", ((DX1 - DX0) * SS, (DY1 - DY0) * SS), 0)
    d = ImageDraw.Draw(mask)
    r = DOT_R * SS

    def dot(x, y, a):
        cx, cy = (x - DX0) * SS, (y - DY0) * SS
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=int(235 * a))

    for a in ambient:
        x = a["p"][0] + 1.8 * math.sin(2 * math.pi * 0.23 * t + a["ph"])
        y = a["p"][1] + 1.4 * math.cos(2 * math.pi * 0.19 * t + a["ph2"])
        dot(x, y, 0.62)
    for m in movers:
        p, a = mover_pos(m, t)
        if p:
            dot(p[0], p[1], a)
    out = DOT_RGB.copy()
    out.putalpha(mask.resize(DOT_RGB.size, Image.BOX))
    return out


def arrived_fraction(t: float) -> float:
    return sum(1 for m in movers if t >= m["t1"]) / len(movers)


# ---------- static layers (drawn once) ----------

def build_static():
    S = {}
    # zone graph (no labels: the labels go on top of the dots, with a backing pill)
    g = transparent()
    draw_zone_graph(g, PROJ, labels=False, radius=NODE_R)
    S["graph"] = Sprite(g)

    lab = transparent()
    for zid, z in ZONES.items():
        x, y = POS[zid]
        text = f'{z["name_zh"]} {short_name(zid)}'
        wt = 700 if zid == SEN else 600
        tx = x + (PILE_R + 16 if zid == SEN else NODE_R + 12)
        tw, _ = text_size(text, 22, wt)
        rounded(lab, (tx - 8, y - 19, tx + tw + 8, y + 17), 10, fill=NAVY, alpha=0.82)
        draw_text(lab, (tx, y - 1), text, 22, wt, INK, anchor="lm")
    S["labels"] = Sprite(lab)

    # warm glow under the Senado pile (illustrative emphasis, grows with the pile)
    gr = int(PILE_R * 2.1)
    glow = Image.new("L", (gr * 2, gr * 2), 0)
    ImageDraw.Draw(glow).ellipse((gr - PILE_R * 1.15, gr - PILE_R * 1.15, gr + PILE_R * 1.15, gr + PILE_R * 1.15), fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(PILE_R * 0.45))
    gim = Image.new("RGBA", glow.size, (*CRITICAL, 0))
    gim.putalpha(glow.point(lambda v: int(v * 0.55)))
    S["glow"] = Sprite(img=gim, x=int(sx - gr), y=int(sy - gr))

    # group extents -> the centred position (4-7 s) and the left position (from the medical line)
    boxes = [S["graph"].box, S["labels"].box, (DX0, DY0, DX1, DY1)]
    gx0, gx1 = min(b[0] for b in boxes), max(b[2] for b in boxes)
    S["dx_centre"] = round(W / 2 - (gx0 + gx1) / 2)
    S["dx_left"] = round(100 - gx0)
    S["group_right_left"] = gx1 + S["dx_left"]

    # camera slate (0-4 s): stands in for the [MEMBER 4] take
    sl = canvas()
    box = (240, 150, 1680, 770)
    d = ImageDraw.Draw(sl)
    dashed_box(d, box, WARNING, width=4, dash=20, gap=12, radius=26, fill=NAVY_2)

    def cam(dd, s):
        cx, cy = 960 * s, 360 * s
        dd.rounded_rectangle((cx - 74 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s), int(14 * s), outline=(*WARNING, 255), width=int(6 * s))
        dd.polygon([(cx + 56 * s, cy - 10 * s), (cx + 96 * s, cy - 36 * s), (cx + 96 * s, cy + 36 * s), (cx + 56 * s, cy + 10 * s)], fill=(*WARNING, 255))
        dd.ellipse((cx - 50 * s, cy - 24 * s, cx - 30 * s, cy - 4 * s), fill=(*CRITICAL, 255))
    sl.alpha_composite(smooth_shapes((W, H), cam))
    full = f"{SLATE_TAG} {SLATE_WHAT}"
    fw, _ = text_size(full, 46, 700)
    tag_w = text_size(SLATE_TAG + " ", 46, 700)[0]
    x0 = (W - fw) / 2
    draw_text(sl, (x0, 500), SLATE_TAG, 46, 700, WARNING, anchor="lm")
    draw_text(sl, (x0 + tag_w, 500), SLATE_WHAT, 46, 700, INK, anchor="lm")
    t_in, t_out = START_S, START_S + BEATS["schematic"]
    sub = f"{SHOT} · {int(t_in // 60)}:{t_in % 60:04.1f}-{int(t_out // 60)}:{t_out % 60:04.1f} · on camera, then voice-over · replace this slate with the take"
    draw_text(sl, (W / 2, 580), sub, 26, 500, INK_2, anchor="mm")
    S["slate"] = sl

    # footer: the source placeholder, verbatim, in an amber dashed box in the footer slot
    fb = placeholder_box(FOOTER, 20, 1150, pad_x=14, pad_y=5, border=2, radius=9)
    S["footer"] = Sprite(img=fb, x=60, y=1062 - fb.height)

    # body-outline diagram panel (from the medical sentence)
    S.update(build_body(S["group_right_left"]))
    return S


def build_body(left_edge: int):
    out = {}
    px0 = max(left_edge + 70, 980)
    panel = (px0, 150, 1860, 862)
    pnl = transparent()
    rounded(pnl, panel, 22, fill=NAVY_2, alpha=0.96)
    out["panel"] = Sprite(pnl)

    cx = px0 + 190
    top, foot = 212, 806
    head_r = 38

    def silhouette(d, s, fill):
        def S_(v):
            return v * s
        d.ellipse((S_(cx - head_r), S_(top), S_(cx + head_r), S_(top + 2 * head_r)), fill=fill)          # head
        d.rounded_rectangle((S_(cx - 16), S_(top + 2 * head_r - 8), S_(cx + 16), S_(top + 2 * head_r + 26)), int(S_(6)), fill=fill)  # neck
        sh = top + 2 * head_r + 18
        d.rounded_rectangle((S_(cx - 102), S_(sh), S_(cx + 102), S_(sh + 110)), int(S_(48)), fill=fill)    # shoulders
        d.polygon([(S_(cx - 84), S_(sh + 44)), (S_(cx + 84), S_(sh + 44)), (S_(cx + 64), S_(sh + 262)), (S_(cx - 64), S_(sh + 262))], fill=fill)  # torso
        d.rounded_rectangle((S_(cx - 66), S_(sh + 230), S_(cx + 66), S_(sh + 286)), int(S_(24)), fill=fill)  # hips
        for sgn in (-1, 1):                                                                             # arms
            ax0, ay0, ax1, ay1 = cx + sgn * 84, sh + 52, cx + sgn * 120, sh + 266
            d.line([(S_(ax0), S_(ay0)), (S_(ax1), S_(ay1))], fill=fill, width=int(S_(34)))
            for (qx, qy, rr) in ((ax0, ay0, 17), (ax1, ay1, 17), (ax1 + sgn * 2, ay1 + 22, 19)):
                d.ellipse((S_(qx - rr), S_(qy - rr), S_(qx + rr), S_(qy + rr)), fill=fill)
            lx0, ly0, lx1, ly1 = cx + sgn * 34, sh + 270, cx + sgn * 44, foot - 26               # legs
            d.line([(S_(lx0), S_(ly0)), (S_(lx1), S_(ly1))], fill=fill, width=int(S_(46)))
            for (qx, qy) in ((lx0, ly0), (lx1, ly1)):
                d.ellipse((S_(qx - 23), S_(qy - 23), S_(qx + 23), S_(qy + 23)), fill=fill)
            d.ellipse((S_(lx1 - 22 + sgn * 10), S_(foot - 26), S_(lx1 + 22 + sgn * 10), S_(foot)), fill=fill)  # feet

    # silhouette mask at SS, then an outline band around its edge (no inner seams)
    big = Image.new("L", (W * SS, H * SS), 0)
    silhouette(ImageDraw.Draw(big), SS, 255)
    bb = big.getbbox()
    pad = 12 * SS
    crop = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
    m = big.crop(crop).filter(ImageFilter.GaussianBlur(5 * SS)).point(lambda v: 255 if v > 110 else 0)  # rounds joints
    blur = m.filter(ImageFilter.GaussianBlur(2.2 * SS))
    outer = blur.point(lambda v: 255 if v > 18 else 0)
    inner = blur.point(lambda v: 255 if v > 237 else 0)
    band = ImageChops.subtract(outer, inner)
    size = ((crop[2] - crop[0]) // SS, (crop[3] - crop[1]) // SS)
    band_s = band.resize(size, Image.LANCZOS)
    fill_s = inner.resize(size, Image.LANCZOS)
    body = Image.new("RGBA", size, (*NAVY_3, 0))
    body.putalpha(fill_s.point(lambda v: int(v * 0.85)))
    line = Image.new("RGBA", size, (*INK_2, 0))
    line.putalpha(band_s)
    body.alpha_composite(line)
    out["body"] = Sprite(img=body, x=crop[0] // SS, y=crop[1] // SS)
    out["body_top"], out["body_bottom"] = top, foot

    # annotation: the research placeholder only, joined to the body by a bracket over its full height
    ax0 = cx + 196
    ann = placeholder_box(MECHANISM, 26, 1830 - ax0, pad_x=24, pad_y=18, full_width=True)
    ay = int((top + foot) / 2 - ann.height / 2) - 40
    out["ann"] = Sprite(img=ann, x=ax0, y=ay)
    cit = placeholder_box(CITATION, 20, 1830 - ax0, pad_x=14, pad_y=9, border=2, radius=10, full_width=True)
    out["cit"] = Sprite(img=cit, x=ax0, y=ay + ann.height + 22)

    bx = cx + 168
    mid = ay + ann.height // 2

    def bracket(dd, s, k):
        """Bracket along the body, grown from its middle (k = 0..1), with a link to the annotation."""
        col = (*INK_3, 255)
        wdt = int(3 * s)
        half = (foot - top) / 2 * k
        c = (top + foot) / 2
        if MECH_TARGET is None:
            y0, y1 = c - half, c + half
            dd.line([(bx * s, y0 * s), (bx * s, y1 * s)], fill=col, width=wdt)
            tick = 14 * clamp((k - 0.8) / 0.2)       # end ticks grow in over the last steps (no pop)
            if tick > 0.5:
                dd.line([((bx - tick) * s, y0 * s), (bx * s, y0 * s)], fill=col, width=wdt)
                dd.line([((bx - tick) * s, y1 * s), (bx * s, y1 * s)], fill=col, width=wdt)
            dd.line([(bx * s, mid * s), ((bx + (ax0 - bx) * k) * s, mid * s)], fill=col, width=wdt)
        else:
            tx, ty = MECH_TARGET
            ex, ey = lerp(ax0, tx, k), lerp(mid, ty, k)
            dd.line([(ax0 * s, mid * s), (ex * s, ey * s)], fill=col, width=wdt)
            dd.ellipse(((ex - 7) * s, (ey - 7) * s, (ex + 7) * s, (ey + 7) * s), outline=col, width=wdt)

    reg = (bx - 30, top - 10, ax0 + 4, foot + 10) if MECH_TARGET is None else (min(MECH_TARGET[0], ax0) - 20, min(MECH_TARGET[1], mid) - 20, ax0 + 4, max(MECH_TARGET[1], mid) + 20)
    reg = tuple(int(v) for v in reg)
    out["bracket_frames"] = []
    for k in [i / 15 for i in range(16)]:
        def draw_k(dd, s, k=k):
            bracket(_Shift(dd, -reg[0] * s, -reg[1] * s), s, k)
        im = smooth_shapes((reg[2] - reg[0], reg[3] - reg[1]), draw_k)
        out["bracket_frames"].append(Sprite(img=im, x=reg[0], y=reg[1]))
    return out


class _Shift:
    """ImageDraw proxy that offsets every coordinate (to draw canvas-space shapes into a sub-image)."""

    def __init__(self, d, ox, oy):
        self.d, self.ox, self.oy = d, ox, oy

    def _p(self, pts):
        out = []
        for p in pts:
            out.append((p[0] + self.ox, p[1] + self.oy))
        return out

    def line(self, pts, **kw):
        self.d.line(self._p(pts), **kw)

    def ellipse(self, box, **kw):
        self.d.ellipse((box[0] + self.ox, box[1] + self.oy, box[2] + self.ox, box[3] + self.oy), **kw)


STATIC = build_static()
WIPE = Image.linear_gradient("L").resize((1, 90))  # 0 at top -> 255 at bottom: soft wipe edge


def wipe_mask(h: int, k: float) -> Image.Image:
    """Alpha mask revealing the top k of a sprite of height h with a soft 90 px edge."""
    edge = 90
    y = int(-edge + (h + edge) * k)
    m = Image.new("L", (1, h), 0)
    if y > 0:
        m.paste(255, (0, 0, 1, min(h, y)))
    grad = WIPE.transpose(Image.FLIP_TOP_BOTTOM)  # 255 at top -> 0 at bottom
    m.paste(grad, (0, y))
    return m


# ---------- frame ----------

def chrome(img: Image.Image, t: float, on_camera: bool) -> None:
    """Card, badge and footer (the overlay slots)."""
    chapter_card(img, CARD, fade(t, BEATS["card_in"], BEATS["card_out"], 0.3))
    if not on_camera:
        badge(img, "ILLUSTRATION", alpha=progress(t, BEATS["schematic"], 0.3))
    put_sprite(img, STATIC["footer"], progress(t, BEATS["voice_in"], 0.35))


def draw_frame(t: float) -> Image.Image:
    if t < BEATS["schematic"]:                       # 0-4 s: [MEMBER 4] on camera (slate for now)
        img = STATIC["slate"].copy()
        chrome(img, t, on_camera=True)
        return img

    img = canvas()
    med = BEATS["medical"]
    k_move = progress(t, BEATS["map_left"], 0.75)
    dx = lerp(STATIC["dx_centre"], STATIC["dx_left"], k_move)
    a_in = 1 - (1 - clamp((t - BEATS["schematic"]) / 0.4)) ** 3   # ease-out: no near-empty frames after the cut
    a_panel = progress(t, med, 0.5)
    rise = (1 - a_panel) * 28
    put_sprite(img, STATIC["panel"], a_panel, 0, rise)     # under the map while it finishes moving

    put_sprite(img, STATIC["graph"], a_in, dx)
    glow_k = ease(arrived_fraction(t))
    put_sprite(img, STATIC["glow"], a_in * glow_k, dx)
    put(img, dots_layer(t), DX0 + dx, DY0, a_in)
    put_sprite(img, STATIC["labels"], a_in, dx)

    # body diagram, from the medical sentence
    if a_panel > 0:
        k_body = progress(t, med + 0.1, 0.9)
        if k_body > 0:
            b = STATIC["body"]
            im = b.img.copy()
            im.putalpha(ImageChops.multiply(im.getchannel("A"), wipe_mask(im.height, k_body).resize(im.size)))
            put(img, im, b.x, b.y + rise, a_panel)
        k_br = progress(t, BEATS["annotation"] - 0.2, 0.45)
        if k_br > 0:
            frames = STATIC["bracket_frames"]
            put_sprite(img, frames[min(len(frames) - 1, int(round(k_br * (len(frames) - 1))))], a_panel)
        a_ann = progress(t, BEATS["annotation"], 0.4)
        put_sprite(img, STATIC["ann"], a_ann, (1 - a_ann) * 18)
        a_cit = progress(t, BEATS["citation"], 0.4)
        put_sprite(img, STATIC["cit"], a_cit, (1 - a_cit) * 18)

    chrome(img, t, on_camera=False)
    return img


def cam_overlay(t: float) -> Image.Image:
    """0-4 s overlay (card + footer) to lay over the real camera take."""
    img = transparent()
    chrome(img, t, on_camera=True)
    return img


STILLS = {"card": 1.0, "pile": 5.4, "crowded": 6.5, "move": 7.15, "body": 8.6, "end": DURATION - 1 / FPS}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        print(still(f"{SHOT}_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render_overlay(f"{SHOT}_cam_overlay", BEATS["schematic"], cam_overlay))
        print(render(SHOT, DURATION, draw_frame))
