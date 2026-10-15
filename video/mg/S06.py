"""Shot S06 (0:46.0-0:58.0, 12.0 s): "Why does it matter?"

[MEMBER 4] on camera for 4 s (a placeholder slate until the take is filmed) with the arrivals tag,
then voice-over over the zone schematic: illustrative dots pile up on Rua de S. Paulo below the
Ruins while three date chips (the police crowd-control afternoons) stack beside the Ruins. On the
medical sentence the map fades out completely; on a plain navy background a side-view body outline
drawn from shapes appears, two arrows press on the chest from front and back, and the only
annotation is the sourced mechanism, with its citation in the footer slot.

Data sources:
  - docs/video/shotlist.json, shot S06: duration (end_s - start_s), the camera timecode, the
    narration and every on-screen line (card, tag, footers, date chips, body label, citation, badge).
  - docs/video/script.md, section 3, row S06: the same narration and lines (checked verbatim).
  - shared/zones.json (through style.zone_graph / draw_zone_graph): zone positions, names and the
    street links the illustrative dots walk along (uphill to Rua de S. Paulo, below the Ruins).
The dots and the pile are an illustration (badge ILLUSTRATION), not data; the date chips are the
real dates from the police release and Macao Daily News (footer). The body diagram is shapes only,
off the Macau map, and carries no text but the sourced mechanism (Gill & Landi 2004).

Outputs:
  video/build/mg/S06.mp4                    the full shot (camera slate 0-4 s)
  video/build/overlays/S06_cam_overlay.mov  0-4 s card + tag + footer with alpha, for the real camera take
  video/build/mg/stills/S06_*.png           layout checks

Run:  .venv/bin/python video/mg/S06.py            (stills, overlay and render)
      .venv/bin/python video/mg/S06.py --stills   (stills only)
"""
from __future__ import annotations

import bisect
import json
import math
import random
import sys
from collections import deque

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageChops, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S06"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 12.0 s
START_S = _shot["start_s"]
_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} | 0:"))

# Beats in seconds from the shot start. The narration starts 0.2 s into the shot (assemble.py,
# VOICE_START). Keyed to the guide voice (video/build/guide/S06.wav, say -v Daniel, ~147 wpm):
# silencedetect pauses at 1.04-1.35, 5.60-5.84, 6.58-6.81 and 9.08-9.38 s of the wav, word starts
# from synthesising prefixes of the line; + 0.2 s gives the shot times below:
#   "This Golden Week," 0.2-1.25 | "police briefly imposed crowd control" 1.56-3.75 |
#   "at the Ruins" 3.75-4.55 | "on three afternoons." 4.55-5.80 | pause | "In a crush," 6.04-6.78 |
#   "victims" 7.01 | "typically suffocate" 7.65-8.74 | "standing up," 8.74-9.28 |
#   "from chest compression." 9.58-10.84 ("chest" ~10.0) | silence to 12.0.
# The date chips come in fast (0.25 s fades, all three up by "three", ~4.9 s) so the full stack reads
# for over a second before the map leaves on "In a crush" (6.05 s); the map cannot stay longer, since
# assemble.py's medical-sentence caption arrives at about 5.9-6.0 s.
# re-key to the real voice take (the team reads at about 140 wpm, so everything moves ~5% later)
BEATS = {
    "card_in": 0.0,       # chapter card over the camera take (2 s)
    "card_out": 2.0,
    "tag_in": 0.5,        # arrivals tag over the camera (spec: 0.5-4 s)
    "schematic": 4.0,     # cut from camera to the zone schematic, on "...the Ruins"; badge on
    "chip_0": 4.0,        # "Crowd control:" and the first chip, with the cut, as "Ruins" lands
    "chip_1": 4.35,       # end of "Ruins" / "on": second chip
    "chip_2": 4.65,       # "three": third chip (all three fully up by ~4.9 s)
    "pile_full": 5.65,    # end of "afternoons": the pile on Rua de S. Paulo is complete
    "map_out": 6.05,      # "In a crush," starts: map, chips and footer fade out (gone by 6.35)
    "body_in": 6.35,      # map gone; the body outline appears on plain navy ("crush")
    "arrows": 6.95,       # "victims": the two arrows press in, "front-to-back pressure"
    "label_2": 7.6,       # "typically": "→ chest can't fully expand"
    "label_3": 8.15,      # "suffocate": "→ asphyxia"
    "press": 9.95,        # "chest compression": the arrows press once more
}
CHIP_FADE = 0.25          # date-chip fade-in (s): quick, so the stack is readable before map_out

# Text, verbatim from the shot list (on_screen_text, narration), checked against the storyboard row.
NARRATION = ("This Golden Week, police briefly imposed crowd control at the Ruins on three afternoons. "
             "In a crush, victims typically suffocate standing up, from chest compression.")
CARD = "Why does it matter?"
TAG = "Macau, 4 Oct: 210,000 visitor arrivals, a National Day holiday record (preliminary)"
FOOTER_CAM = "Macao Government Tourism Office via gov.mo, 8 Oct 2026"
CHIPS_TEXT = "Crowd control: 2 Oct pm · 3 Oct pm · 4 Oct 13:50-15:10"
FOOTER_MAP = "Public Security Police Force via gcs.gov.mo, 8 Oct 2026 · Macao Daily News, 5 Oct 2026"
BODY_LABEL = "front-to-back pressure → chest can't fully expand → asphyxia"
CITATION = "Gill & Landi, Am J Forensic Med Pathol, 2004 · case report, New York, 1991"
BADGE = "ILLUSTRATION"
_ost = dict(item.split(": ", 1) for item in _shot["on_screen_text"].split(" | "))
assert _shot["narration"] == NARRATION, _shot["narration"]
assert NARRATION in _row
for _key, _txt in (("Chapter card (top-left, 2 s)", CARD), ("Tag (0.5-4 s, over the camera)", TAG),
                   ("Footer (0-4 s)", FOOTER_CAM), ("Date chips (4-6.5 s, beside the Ruins)", CHIPS_TEXT),
                   ("Footer (4-6.5 s)", FOOTER_MAP), ("Body label (6.5-12 s)", BODY_LABEL),
                   ("Citation (6.5-12 s, footer slot)", CITATION),
                   ("Badge (top-right, from 4 s, over the schematic and the body diagram)", BADGE)):
    assert _ost.get(_key) == _txt, (_key, _ost.get(_key))
    assert _txt in _row, _txt
assert BADGE in BADGES
# Layout splits (the same words, broken into lines / chips; checked to rejoin exactly).
TAG_LINES = ["Macau, 4 Oct: 210,000 visitor arrivals,", "a National Day holiday record (preliminary)"]
CHIP_HEAD, CHIPS = "Crowd control:", ["2 Oct pm", "3 Oct pm", "4 Oct 13:50-15:10"]
LABEL_LINES = ["front-to-back pressure", "→ chest can't fully expand", "→ asphyxia"]
assert " ".join(TAG_LINES) == TAG
assert f"{CHIP_HEAD} {' · '.join(CHIPS)}" == CHIPS_TEXT
assert " ".join(LABEL_LINES) == BODY_LABEL
SLATE_TAG = "[TEAM FOOTAGE]"
SLATE_WHAT = "[MEMBER 4], medium shot, eye level"

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


def smooth_shapes(size, draw_fn) -> Image.Image:
    """Draws with draw_fn(d, s) on an SS-times larger RGBA canvas and downsamples (anti-aliased shapes)."""
    big = Image.new("RGBA", (size[0] * SS, size[1] * SS), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), SS)
    return big.resize(size, Image.LANCZOS)


def outlined(mask_big: Image.Image, fill=NAVY_3, line=INK_2, fill_alpha=0.85, round_px=5, band_px=2.2):
    """Outline drawing from an SS-scale silhouette mask: rounded joints, a soft line band around the
    edge (no inner seams) and a translucent fill. Returns (rgba sprite, fill mask, crop box / SS)."""
    bb = mask_big.getbbox()
    pad = 12 * SS
    crop = (bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad)
    m = mask_big.crop(crop).filter(ImageFilter.GaussianBlur(round_px * SS)).point(lambda v: 255 if v > 110 else 0)
    blur = m.filter(ImageFilter.GaussianBlur(band_px * SS))
    outer = blur.point(lambda v: 255 if v > 18 else 0)
    inner = blur.point(lambda v: 255 if v > 237 else 0)
    band = ImageChops.subtract(outer, inner)
    size = ((crop[2] - crop[0]) // SS, (crop[3] - crop[1]) // SS)
    band_s = band.resize(size, Image.LANCZOS)
    fill_s = inner.resize(size, Image.LANCZOS)
    im = Image.new("RGBA", size, (*fill, 0))
    im.putalpha(fill_s.point(lambda v: int(v * fill_alpha)))
    ln = Image.new("RGBA", size, (*line, 0))
    ln.putalpha(band_s)
    im.alpha_composite(ln)
    return im, fill_s, (crop[0] // SS, crop[1] // SS)


# ---------- the zone schematic and the illustrative dots ----------

G = zone_graph()
ZONES = {z["id"]: z for z in G["zones"]}
PROJ = project()                                  # the S01 schematic projection (style default box)
POS = {zid: PROJ(z["lat"], z["lon"]) for zid, z in ZONES.items()}
NODE_R = 26
RUINS, JESUS, RSP, DOM = "ruins_st_paul", "jesus_square", "rua_sao_paulo", "st_dominic"
ADJ: dict[str, list[str]] = {zid: [] for zid in ZONES}
for e in G["edges"]:
    ADJ[e["from"]].append(e["to"])
    ADJ[e["to"]].append(e["from"])
STAIRS = [(POS[e["from"]], POS[e["to"]]) for e in G["edges"] if e.get("has_stairs")]


def route(src: str, dst: str) -> list[str]:
    """Shortest path (by number of street links) between two zones, through zones.json edges."""
    prev, q = {src: None}, deque([src])
    while q:
        u = q.popleft()
        if u == dst:
            break
        for v in ADJ[u]:
            if v not in prev:
                prev[v] = u
                q.append(v)
    out, u = [], dst
    while u is not None:
        out.append(u)
        u = prev[u]
    return out[::-1]


def short_name(zid: str) -> str:  # same short names as style.draw_zone_graph
    return {"tercena_corridor": "Rua da Tercena", "rua_sao_paulo": "Rua de S. Paulo",
            "almeida_ribeiro": "Av. de Almeida Ribeiro"}.get(zid, ZONES[zid]["name"])


def seg_dist(p, a, b) -> float:
    """Distance from point p to the segment a-b."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    u = clamp(((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / (vx * vx + vy * vy))
    return math.hypot(p[0] - a[0] - u * vx, p[1] - a[1] - u * vy)


rng = random.Random(606)
DOT_R = 4.6
GOLD = math.pi * (3 - math.sqrt(5))


def spiral(centre, n, c=6.2):
    cx, cy = centre
    return [(cx + c * math.sqrt(i + 0.5) * math.cos(i * GOLD) + rng.uniform(-1.1, 1.1),
             cy + c * math.sqrt(i + 0.5) * math.sin(i * GOLD) + rng.uniform(-1.1, 1.1)) for i in range(n)]


# The pile (illustration): people walking uphill to the Ruins back up on Rua de S. Paulo below them:
# Company of Jesus Square at the foot of the steps fills first, then the upper street, the Rua de
# S. Paulo node, and a queue down the lower street towards St. Dominic's.
PILE_J_N, PILE_R_N = 18, 34
PILE_J_R, PILE_R_R = 6.2 * math.sqrt(PILE_J_N), 6.2 * math.sqrt(PILE_R_N)
jx, jy = POS[JESUS]
rx_, ry_ = POS[RSP]
dxs, dys = POS[DOM]
slots_j = [p for p in spiral(POS[JESUS], PILE_J_N + 6) if all(seg_dist(p, a, b) > 9 for a, b in STAIRS)][:PILE_J_N]
L_up = math.hypot(rx_ - jx, ry_ - jy)
ux, uy = (rx_ - jx) / L_up, (ry_ - jy) / L_up         # down the upper street, Jesus -> Rua de S. Paulo
vx, vy = -uy, ux
slots_up = []
d_ = PILE_J_R + 6
while d_ < L_up - PILE_R_R - 2:
    for lane in (-15.0, -5.0, 5.0, 15.0):
        if rng.random() < 0.9:
            ln = lane + rng.uniform(-1.4, 1.4)
            slots_up.append((jx + ux * d_ + vx * ln, jy + uy * d_ + vy * ln, d_))
    d_ += 10.2
slots_up = [(x, y) for x, y, _ in sorted(slots_up, key=lambda s: s[2])]
slots_r = sorted(spiral(POS[RSP], PILE_R_N), key=lambda p: p[1])            # top of the node pile first
L_lo = math.hypot(dxs - rx_, dys - ry_)
wx, wy = (dxs - rx_) / L_lo, (dys - ry_) / L_lo
slots_q = []
for k in range(14):
    dist = PILE_R_R + 6 + (k // 2) * 10.5
    lane = (-5.6 if k % 2 == 0 else 5.6) + rng.uniform(-1.2, 1.2)
    slots_q.append((rx_ + wx * dist - wy * lane, ry_ + wy * dist + wx * lane))

# Where each slot's walkers come from: the Avenida de Almeida Ribeiro entry (zones.json "entry")
# and the squares on the way up, plus Rua da Tercena, which joins Rua de S. Paulo.
SOUTH = ["almeida_ribeiro", "almeida_ribeiro", "senado_square", DOM]


def walk_points(src: str, via_rsp_to: tuple[float, float] | None, slot) -> list[tuple[float, float]]:
    nodes = route(src, RSP)
    lat = rng.uniform(-4.0, 4.0)
    pts = []
    for j, zid in enumerate(nodes):
        x, y = POS[zid]
        if j == 0:
            a, rr = rng.uniform(0, 2 * math.pi), rng.uniform(4, 20)
            pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
        elif zid == RSP:
            pts.append((x + lat, y + lat * 0.4))
        else:
            pts.append((x + lat, y + lat * 0.6))
    if via_rsp_to:
        pts.append(via_rsp_to)
    pts.append(slot)
    return pts


def queue_points(src: str, slot) -> list[tuple[float, float]]:
    nodes = route(src, DOM)
    pts = []
    for j, zid in enumerate(nodes):
        x, y = POS[zid]
        jitter = rng.uniform(4, 18) if j == 0 else 0
        a = rng.uniform(0, 2 * math.pi)
        pts.append((x + jitter * math.cos(a), y + jitter * math.sin(a)))
    pts.append(slot)
    return pts


movers = []  # each: path, cumulative lengths, start, end, phases
ordered = [("j", s) for s in slots_j] + [("up", s) for s in slots_up] + [("r", s) for s in slots_r] + [("q", s) for s in slots_q]
n_all = len(ordered)
a0, a1 = BEATS["schematic"] + 0.3, BEATS["pile_full"]
for i, (kind, slot) in enumerate(ordered):          # the top fills first, the queue last
    arrive = a0 + (a1 - a0) * (i / (n_all - 1)) ** 0.85 + rng.uniform(-0.05, 0.05)
    if kind == "q":
        pts = queue_points(rng.choice(["almeida_ribeiro", "senado_square", "senado_square"]), slot)
    else:
        src = rng.choice(SOUTH * 3 + ["tercena_corridor"])
        via = None
        if kind == "j":   # up the street to the foot of the steps
            via = (jx + ux * (PILE_J_R + 4), jy + uy * (PILE_J_R + 4))
        pts = walk_points(src, via, slot)
    cum = [0.0]
    for a, b in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    dur = max(0.9, cum[-1] / 250.0)
    movers.append(dict(pts=pts, cum=cum, t0=arrive - dur, t1=arrive, ph=rng.uniform(0, 6.3), ph2=rng.uniform(0, 6.3)))

# Ambient people elsewhere (more at the Ruins); kept off the pile, the stairs and the label rows.
taken = [s for _, s in ordered]
ambient = []
for zid, n, rad in ((RUINS, 24, 42), ("st_dominic", 7, 32), ("senado_square", 10, 36), ("almeida_ribeiro", 8, 34),
                    ("tercena_corridor", 4, 26)):
    x, y = POS[zid]
    placed, tries = 0, 0
    while placed < n and tries < 4000:
        tries += 1
        a, rr = rng.uniform(0, 2 * math.pi), rad * math.sqrt(rng.random())
        p = (x + rr * math.cos(a), y + rr * math.sin(a))
        in_label = p[0] > x + NODE_R + 2 and abs(p[1] - y) < 22
        on_stairs = any(seg_dist(p, a_, b_) < 10 for a_, b_ in STAIRS)
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

def build_map():
    S = {}
    # zone graph (no labels: the labels go on top of the dots, with a backing pill)
    g = transparent()
    draw_zone_graph(g, PROJ, labels=False, radius=NODE_R)
    S["graph"] = Sprite(g)

    lab = transparent()
    offset = {JESUS: PILE_J_R + 14, RSP: PILE_R_R + 14}
    for zid, z in ZONES.items():
        x, y = POS[zid]
        text = f'{z["name_zh"]} {short_name(zid)}'
        wt = 700 if zid == RSP else 600
        tx = x + offset.get(zid, NODE_R + 12)
        tw, _ = text_size(text, 22, wt)
        rounded(lab, (tx - 8, y - 19, tx + tw + 8, y + 17), 10, fill=NAVY, alpha=0.82)
        draw_text(lab, (tx, y - 1), text, 22, wt, INK, anchor="lm")
    S["labels"] = Sprite(lab)

    # soft neutral glow under the pile (illustrative emphasis, grows with the pile; no state colour)
    gl = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(gl)
    for _, (x, y) in ordered:
        gd.ellipse((x - 16, y - 16, x + 16, y + 16), fill=255)
    gl = gl.filter(ImageFilter.GaussianBlur(16))
    gim = Image.new("RGBA", (W, H), (*INK_2, 0))
    gim.putalpha(gl.point(lambda v: int(v * 0.22)))
    S["glow"] = Sprite(gim)

    # date chips beside the Ruins: "Crowd control:" then three chips stacked, joined to the Ruins
    ruins_x, ruins_y = POS[RUINS]
    chip_h, chip_gap, fs = 50, 10, 30
    widths = [text_size(c, fs, 600)[0] + 40 for c in CHIPS]
    col_r = ruins_x - NODE_R - 92                         # right edge of the widest chip
    col_l = col_r - max(widths)
    chips = []
    for i, (c, w_) in enumerate(zip(CHIPS, widths)):
        y0 = ruins_y - chip_h / 2 + i * (chip_h + chip_gap)
        im = transparent()
        rounded(im, (col_l, y0, col_l + w_, y0 + chip_h), 12, fill=NAVY_3, outline=INK_3, width=2)
        draw_text(im, (col_l + 20, y0 + chip_h / 2 + 1), c, fs, 600, INK, anchor="lm")
        chips.append(Sprite(im))
    S["chips"] = chips
    hd = transparent()
    hw_, _ = text_size(CHIP_HEAD, fs, 700)
    draw_text(hd, (col_l - 16, ruins_y + 1), CHIP_HEAD, fs, 700, INK_2, anchor="rm")
    S["chip_head"] = Sprite(hd)

    def conn(d, s):
        x0 = col_l + widths[0] + 8
        d.line([(x0 * s, ruins_y * s), ((ruins_x - NODE_R - 8) * s, ruins_y * s)], fill=(*INK_3, 255), width=int(3 * s))
        d.ellipse(((ruins_x - NODE_R - 13) * s, (ruins_y - 5) * s, (ruins_x - NODE_R - 3) * s, (ruins_y + 5) * s), fill=(*INK_3, 255))
    S["conn"] = Sprite(smooth_shapes((W, H), conn))
    S["conn_x0"] = col_l + widths[0] + 8
    S["conn_x1"] = ruins_x - NODE_R - 3

    # centre the whole group (graph, labels, dots, chips) horizontally
    boxes = [S["graph"].box, S["labels"].box, (DX0, DY0, DX1, DY1), S["chip_head"].box] + [c.box for c in chips]
    gx0, gx1 = min(b[0] for b in boxes), max(b[2] for b in boxes)
    S["dx"] = round(W / 2 - (gx0 + gx1) / 2)
    S["extent"] = (gx0 + S["dx"], min(b[1] for b in boxes), gx1 + S["dx"], max(b[3] for b in boxes))
    return S


def build_slate():
    """Camera slate (0-4 s): stands in for the [MEMBER 4] take."""
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
    return sl


def build_tag() -> Sprite:
    """The small scale tag over the camera (lower-left, in the lower-third slot, y 800-890)."""
    im = transparent()
    w1, _ = text_size(TAG_LINES[0], 32, 700)
    w2, _ = text_size(TAG_LINES[1], 28, 500)
    x0, y0, y1 = 60, 798, 892
    rounded(im, (x0, y0, x0 + 28 + max(w1, w2) + 28, y1), 14, fill=NAVY_2, alpha=0.92)
    rounded(im, (x0, y0, x0 + 6, y1), 3, fill=CYAN)
    draw_text(im, (x0 + 28, y0 + 28), TAG_LINES[0], 32, 700, INK, anchor="lm")
    draw_text(im, (x0 + 28, y0 + 67), TAG_LINES[1], 28, 500, INK_2, anchor="lm")
    return Sprite(im)


def build_body():
    """Side-view body outline (facing right) from shapes, the two chest arrows and the label."""
    out = {}
    cx, top, foot = 600, 158, 872
    sh = top + 112                                    # shoulder line
    chest_y = sh + 74
    knee_y = (sh + 300 + foot) // 2
    out["chest_y"] = chest_y

    def torso_head_legs(d, s, fill):
        P = lambda pts: [(x * s, y * s) for x, y in pts]  # noqa: E731
        d.ellipse(((cx - 34) * s, top * s, (cx + 48) * s, (top + 92) * s), fill=fill)                       # head
        d.polygon(P([(cx + 44, top + 34), (cx + 62, top + 58), (cx + 42, top + 64)]), fill=fill)          # nose
        d.rounded_rectangle(((cx - 10) * s, (top + 74) * s, (cx + 22) * s, (sh + 16) * s), int(8 * s), fill=fill)  # neck
        d.polygon(P([(cx - 48, sh + 4), (cx + 30, sh), (cx + 58, sh + 36), (cx + 68, sh + 84), (cx + 58, sh + 160),
                     (cx + 52, sh + 210), (cx + 58, sh + 256), (cx + 50, sh + 304), (cx - 56, sh + 304),
                     (cx - 64, sh + 262), (cx - 48, sh + 196), (cx - 56, sh + 120), (cx - 60, sh + 56)]), fill=fill)  # torso
        d.polygon(P([(cx + 46, sh + 290), (cx + 34, knee_y), (cx + 22, foot - 30), (cx - 20, foot - 30),
                     (cx - 34, knee_y + 80), (cx - 30, knee_y), (cx - 54, sh + 290)]), fill=fill)          # legs
        d.rounded_rectangle(((cx - 30) * s, (foot - 34) * s, (cx + 70) * s, foot * s), int(14 * s), fill=fill)  # foot

    def arm(d, s, fill):
        d.line([((cx - 4) * s, (sh + 34) * s), ((cx + 14) * s, (sh + 262) * s)], fill=fill, width=int(36 * s))
        for (qx, qy, rr) in ((cx - 4, sh + 34, 19), (cx + 14, sh + 262, 18), (cx + 17, sh + 284, 19)):
            d.ellipse(((qx - rr) * s, (qy - rr) * s, (qx + rr) * s, (qy + rr) * s), fill=fill)

    big = Image.new("L", (W * SS, H * SS), 0)
    torso_head_legs(ImageDraw.Draw(big), SS, 255)
    body, body_fill, (bx, by) = outlined(big)
    big_arm = Image.new("L", (W * SS, H * SS), 0)
    arm(ImageDraw.Draw(big_arm), SS, 255)
    arm_im, _, (ax, ay) = outlined(big_arm, round_px=3, band_px=1.8, fill_alpha=1.0)
    body.alpha_composite(arm_im, (ax - bx, ay - by))
    out["body"] = Sprite(img=body, x=bx, y=by)

    # chest tint (shown while pressed), clipped to the body fill
    ch = Image.new("L", body.size, 0)
    ImageDraw.Draw(ch).ellipse((cx - 56 - bx, chest_y - 64 - by, cx + 64 - bx, chest_y + 70 - by), fill=255)
    ch = ch.filter(ImageFilter.GaussianBlur(14))
    tint = Image.new("RGBA", body.size, (*WARNING, 0))
    tint.putalpha(ImageChops.multiply(ch, body_fill).point(lambda v: int(v * 0.30)))
    out["chest"] = Sprite(img=tint, x=bx, y=by)

    # the chest's front and back edges at chest height (from the fill mask)
    row = [body_fill.getpixel((x, chest_y - by)) for x in range(body.width)]
    inside = [x for x, v in enumerate(row) if v > 128]
    out["back_x"], out["front_x"] = bx + inside[0], bx + inside[-1]

    # arrows: shaft + head, pointing at the chest (drawn once, moved per frame)
    def arrow(direction: int):
        length, shaft, head_w, head_l = 168, 20, 54, 46
        w_, h_ = length + 8, head_w + 8

        def draw(d, s):
            y = h_ / 2
            if direction > 0:   # pointing right: tip at the right end
                tip = length + 4
                d.rectangle((4 * s, (y - shaft / 2) * s, (tip - head_l + 2) * s, (y + shaft / 2) * s), fill=(*WARNING, 255))
                d.polygon([((tip - head_l) * s, (y - head_w / 2) * s), (tip * s, y * s), ((tip - head_l) * s, (y + head_w / 2) * s)], fill=(*WARNING, 255))
            else:               # pointing left: tip at the left end
                tip = 4
                d.rectangle(((tip + head_l - 2) * s, (y - shaft / 2) * s, (length + 4) * s, (y + shaft / 2) * s), fill=(*WARNING, 255))
                d.polygon([((tip + head_l) * s, (y - head_w / 2) * s), (tip * s, y * s), ((tip + head_l) * s, (y + head_w / 2) * s)], fill=(*WARNING, 255))
        return smooth_shapes((int(w_), int(h_)), draw)

    out["arrow_r"], out["arrow_l"] = arrow(+1), arrow(-1)

    # label: the sourced mechanism, one line per step, line 1 level with the arrows
    lx = out["front_x"] + 14 + 168 + 84
    out["label_x"] = lx
    lines = []
    for i, ln in enumerate(LABEL_LINES):
        im = transparent()
        y = chest_y + i * 74
        if ln.startswith("→ "):
            aw, _ = text_size("→ ", 46, 600)
            draw_text(im, (lx, y), "→ ", 46, 600, INK_2, anchor="lm")
            draw_text(im, (lx + aw, y), ln[2:], 46, 600, INK, anchor="lm")
        else:
            draw_text(im, (lx, y), ln, 46, 700, WARNING, anchor="lm")
        lines.append(Sprite(im))
    out["label"] = lines
    return out


STATIC = build_map()
SLATE = build_slate()
TAG_SPRITE = build_tag()
BODY = build_body()
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

_fl, _ft, _fr, _fb = text_font(FOOTER_CAM, 20, 500).getbbox(FOOTER_CAM)
FOOTER_CAM_SCRIM = (60 + _fl - 12, 1034 + _ft - 5, 60 + _fr + 12, 1034 + _fb + 5)   # where style.footer draws it


def camera_chrome(img: Image.Image, t: float) -> None:
    """0-4 s, over the camera: card (2 s), the arrivals tag (from 0.5 s) and its source footer. The
    footer gets a dark scrim (as in S17's camera overlay) so it stays legible over the real take."""
    chapter_card(img, CARD, fade(t, BEATS["card_in"], BEATS["card_out"], 0.25))
    k_tag = progress(t, BEATS["tag_in"], 0.15)      # quick fade-in: the 12-word tag gets the whole 0.5-4 s window
    put_sprite(img, TAG_SPRITE, k_tag, 0, (1 - k_tag) * 14)
    a_f = progress(t, 0.0, 0.3)
    if a_f > 0:
        rounded(img, FOOTER_CAM_SCRIM, 8, fill=NAVY, alpha=0.92 * a_f)
        footer(img, FOOTER_CAM, a_f)


def draw_frame(t: float) -> Image.Image:
    if t < BEATS["schematic"]:                       # 0-4 s: [MEMBER 4] on camera (slate for now)
        img = SLATE.copy()
        camera_chrome(img, t)
        return img

    img = canvas()
    dx = STATIC["dx"]
    a_in = 0.45 + 0.55 * (1 - (1 - clamp((t - BEATS["schematic"]) / 0.3)) ** 3)   # quick ease-out: no empty frame at the cut
    a_map = a_in * (1 - progress(t, BEATS["map_out"], 0.3))

    if a_map > 0:                                    # 4-6.35 s: the schematic, the pile and the date chips
        put_sprite(img, STATIC["graph"], a_map, dx)
        put_sprite(img, STATIC["glow"], a_map * ease(arrived_fraction(t)), dx)
        put(img, dots_layer(t), DX0 + dx, DY0, a_map)
        put_sprite(img, STATIC["labels"], a_map, dx)
        k_head = progress(t, BEATS["chip_0"], CHIP_FADE)
        put_sprite(img, STATIC["chip_head"], a_map * k_head, dx)
        # connector to the Ruins grows from the chips
        k_conn = progress(t, BEATS["chip_0"] + 0.05, 0.3)
        if k_conn > 0:
            c = STATIC["conn"]
            x_cut = STATIC["conn_x0"] + (STATIC["conn_x1"] - STATIC["conn_x0"]) * k_conn - c.x
            im = c.img.crop((0, 0, max(1, int(x_cut)), c.img.height))
            put(img, im, c.x + dx, c.y, a_map)
        for i, chip in enumerate(STATIC["chips"]):
            k = progress(t, BEATS[f"chip_{i}"], CHIP_FADE)
            put_sprite(img, chip, a_map * k, dx, -(1 - k) * 16)
        footer(img, FOOTER_MAP, a_map)

    u_body = clamp((t - BEATS["body_in"]) / 0.55)     # from 6.35 s: the body diagram on plain navy (never over the map)
    k_body = 1 - (1 - u_body) ** 2 if t >= BEATS["body_in"] else 0.0   # ease-out wipe: no empty beat after the map
    if k_body > 0:
        b = BODY["body"]
        im = b.img.copy()
        im.putalpha(ImageChops.multiply(im.getchannel("A"), wipe_mask(im.height, k_body).resize(im.size)))
        put(img, im, b.x, b.y, clamp((t - BEATS["body_in"]) / 0.2))
        k_ar = progress(t, BEATS["arrows"], 0.5)
        if k_ar > 0:
            pulse = 0.0
            if t >= BEATS["press"]:                  # one more press on "chest compression"
                u = (t - BEATS["press"]) / 0.7
                pulse = 8 * math.sin(math.pi * clamp(u)) if u < 1 else 0.0
            gap = 10 + (1 - k_ar) * 110 - pulse
            cy = BODY["chest_y"]
            ar, al = BODY["arrow_r"], BODY["arrow_l"]
            put(img, ar, BODY["back_x"] - gap - ar.width + 4, cy - ar.height / 2, k_ar)
            put(img, al, BODY["front_x"] + gap - 4, cy - al.height / 2, k_ar)
            k_tint = progress(t, BEATS["arrows"] + 0.3, 0.4) * (0.75 + 0.25 * (pulse / 8))
            put_sprite(img, BODY["chest"], k_tint)
        for i, key in enumerate(("arrows", "label_2", "label_3")):
            k = progress(t, BEATS[key] + (0.1 if i == 0 else 0.0), 0.4)
            put_sprite(img, BODY["label"][i], k, (1 - k) * 20)
        footer(img, CITATION, progress(t, BEATS["body_in"], 0.3))

    badge(img, BADGE, alpha=progress(t, BEATS["schematic"], 0.3))
    return img


def cam_overlay(t: float) -> Image.Image:
    """0-4 s overlay (card + tag + footer) to lay over the real camera take."""
    img = transparent()
    camera_chrome(img, t)
    return img


STILLS = {"card": 1.0, "tag_in": 0.65, "tag": 3.0, "cut": 4.1, "chips": 4.5, "chips_full": 4.95, "pile": 5.5,
          "map_full": 6.0, "fade": 6.2, "body": 6.6,
          "arrows": 7.7, "label": 8.8, "press": 10.3, "end": DURATION - 1 / FPS}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        print(still(f"{SHOT}_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render_overlay(f"{SHOT}_cam_overlay", BEATS["schematic"], cam_overlay))
        print(render(SHOT, DURATION, draw_frame))
