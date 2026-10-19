"""Shot S07, "But how is ours different?" (24 s), team voice-over.

Three sequential beats preserve the police-system comparison and its sourced wording. The existing
system appears first. A large central spoken question then holds over dimmed, frozen context, with
the proposal hidden. Event staff and their temporary sensing kit are introduced before the four-station
operating loop. The proposal explicitly supports the existing system; no moral comparison is made.

Wording comes from docs/video/shotlist.json and is checked against the S07 storyboard row. Zone geometry
comes from shared/zones.json. BEATS follow the 19 Oct guide and must be re-keyed to the team's real take.

Output: video/build/mg/S07.mp4 and video/build/mg/stills/S07_<beat>.png.
Run: .venv/bin/python video/mg/S07.py [--stills]
     .venv/bin/python video/mg/S07.py --preview 1.5 12.0 --out DIR
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import deque
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S07"

# ---------------------------------------------------------------- spec (read, never retyped)

_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)
assert DURATION == 24.0, DURATION
NARRATION = _shot["narration"]

_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
_cols = [c.strip() for c in _row.strip().strip("|").split(" | ")]
assert len(_cols) == 7 and _cols[3] == NARRATION, "storyboard row S07 and shotlist.json disagree on the narration"

_KEYS = ["Central question", "Left column", "Under it", "Map band label", "Operator introduction", "Proposal framing", "Right column", "Phone detail", "Footer"]
_spec = {}
for _part in _shot["on_screen_text"].split(" | "):
    _m = re.match(r"^([A-Z][a-z ]+?)(?: \(([^)]*)\))?: (.*)$", _part.strip())
    assert _m and _m.group(1) in _KEYS, f"unexpected on-screen part: {_part!r}"
    _spec[_m.group(1)] = _m.group(3)
assert list(_spec) == _KEYS, list(_spec)                          # 19 Oct declutter: nothing else on screen
QUESTION, POLICY, BAND_LABEL, FOOTER = _spec["Central question"], _spec["Under it"], _spec["Map band label"], _spec["Footer"]
assert QUESTION == "But how is ours different?", QUESTION
LEFT_HEAD, *LEFT_ITEMS = _spec["Left column"].split(" · ")
OPERATOR, KIT = _spec["Operator introduction"].split(" · ")
FRAMING = _spec["Proposal framing"]
RIGHT_HEAD, *RIGHT_ITEMS = _spec["Right column"].split(" · ")
PHONE_DETAIL = _spec["Phone detail"]
assert LEFT_HEAD == "Police system (public information)" and RIGHT_HEAD == "What we propose", (LEFT_HEAD, RIGHT_HEAD)
assert len(LEFT_ITEMS) == 2 and len(RIGHT_ITEMS) == 4
for _txt in (QUESTION, LEFT_HEAD, *LEFT_ITEMS, POLICY, BAND_LABEL, OPERATOR, KIT, FRAMING, RIGHT_HEAD, *RIGHT_ITEMS, PHONE_DETAIL, FOOTER):
    assert _txt in _cols[5], f"not in the storyboard row: {_txt!r}"
assert not any(c.isdigit() for c in "".join(RIGHT_ITEMS)), "the proposal labels carry no numbers"
assert "We believe" not in NARRATION and "No one left behind" not in _cols[5]
# never set the two systems against each other in words (script.md section 6, "Never say or show")
_all = " ".join([LEFT_HEAD, *LEFT_ITEMS, POLICY, RIGHT_HEAD, *RIGHT_ITEMS]).lower()
assert not any(w in _all for w in ("better", "replace", "lack", "we'd add", "instead")), _all
# 19 Oct declutter: labels of at most 6 words, a short source footer that fits one line of the footer slot
assert all(len(t.split()) <= 6 for t in (*LEFT_ITEMS, POLICY, BAND_LABEL, OPERATOR, KIT, FRAMING, *RIGHT_ITEMS, PHONE_DETAIL)), "a label is too long"
assert len(FOOTER.replace(" · ", " ").split()) <= 7 and text_size(FOOTER, 20, 500)[0] <= 1150, FOOTER

# The narration, clause by clause as the guide voice pauses (BEATS are keyed to these).
CLAUSES = ["Macau's police already run a crowd warning system here.",
           QUESTION,
           "We propose a temporary sensing kit for event staff,", "to support the existing system.",
           "Staff place the phones;", "the phones count on-device and send only numbers.",
           "On the dashboard, staff review forecasts and suggested detours before acting."]
assert " ".join(CLAUSES) == NARRATION, "narration changed: re-measure the guide voice and re-key BEATS"
# each right-column item arrives on the voice's own words for it
_LOOP_WORDS = [("event staff", "temporary sensing kit"), ("Staff place", "phones"),
               ("on-device", "only numbers"), ("dashboard", "staff review")]
assert all(a in NARRATION and b in NARRATION for a, b in _LOOP_WORDS)
assert [it.split()[0].lower() for it in RIGHT_ITEMS] == ["staff", "on-device", "dashboard", "staff"], RIGHT_ITEMS

# ---------------------------------------------------------------- zone model

ZONES = zone_graph()["zones"]
EDGES = zone_graph()["edges"]


def street_path(a: str, b: str) -> list[str]:
    """Shortest street path (fewest links) between two zones."""
    nbr: dict[str, list[str]] = {}
    for e in EDGES:
        nbr.setdefault(e["from"], []).append(e["to"])
        nbr.setdefault(e["to"], []).append(e["from"])
    prev, q = {a: None}, deque([a])
    while q:
        u = q.popleft()
        for v in nbr.get(u, []):
            if v not in prev:
                prev[v] = u
                q.append(v)
    path, u = [], b
    while u is not None:
        path.append(u)
        u = prev[u]
    return path[::-1]


CORRIDOR = street_path("ruins_st_paul", "senado_square")
# the storyboard's corridor, in order (Company of Jesus Square sits on it, between the Ruins and Rua de S. Paulo)
assert [z for z in CORRIDOR if z != "jesus_square"] == ["ruins_st_paul", "rua_sao_paulo", "st_dominic", "senado_square"], CORRIDOR
assert "jesus_square" in CORRIDOR
assert BAND_LABEL == "Ruins to Senado"                             # the band's two ends, as the corridor runs

# ---------------------------------------------------------------- timing
# Guide voice S07.wav re-keyed on 19 Oct (20.00 s; placed at 0.2 s by assembly).
# Clause boundaries, ffmpeg silencedetect at -35 dB /0.08 s:
# police:0.20-3.49; question:3.73-5.18; intended user/kit:5.41-8.53; support:8.76-10.62;
# staff placement:10.87-12.38; on-device counting/numerical hand-over:12.61-15.31;
# dashboard:15.54-16.41; staff review:16.63-20.20. Re-key to the team's recorded take.
QUESTION_START, QUESTION_END = 3.48, 6.0
QUESTION_IN, QUESTION_OUT = 0.2, 0.3
BEATS = {
    "map": 0.0,           # the zone graph, on the right
    "band": 0.15,         # "Macau's police": the band sweeps Ruins -> Senado
    "left": 0.85,         # "police": the police column and its header
    "band_label": 1.4,    # "Ruins to Senado", as the band reaches St. Dominic's
    "left_1": 1.88,       # "crowd warning system": "Real-time monitoring and alerts"
    "left_2": 2.6,        # "system here": "Zone forecasts planned"
    "here": 3.13,         # "here": the band brightens once
    "policy": 2.95,       # complete the sourced police context before the question
    "map_out": QUESTION_END,
    "right": 6.05,        # first introduce the intended operator and temporary kit
    "right_head": 6.1,
    "operator": 6.25,
    "framing": 8.75,
    "stations": 10.45,
    "loop": 10.7,
    "item_0": 10.9,
    "item_1": 12.6,
    "phone_detail": 14.0,
    "item_2": 15.8,
    "needle": 16.5,
    "item_3": 17.4,
    "close": 19.7,
}
FADE = 0.35
# every right-column item reads for at least 0.3 s per word + 0.5 s (19 Oct declutter, rule 5)
for _i, _it in enumerate(RIGHT_ITEMS):
    assert DURATION - BEATS[f"item_{_i}"] >= 0.3 * len(_it.split()) + 0.5, _it
assert QUESTION_START - BEATS["band_label"] >= 0.3 * len(BAND_LABEL.split()) + 0.5
assert QUESTION_END - QUESTION_START - QUESTION_IN - QUESTION_OUT >= 0.3 * len(QUESTION.split()) + 0.5
assert min(BEATS[k] for k in ("operator", "right", "loop")) >= QUESTION_END
assert BEATS["item_0"] - BEATS["operator"] >= 0.3 * len(f"{OPERATOR} {KIT}".split()) + 0.5
assert DURATION - 20.2 >= 2.0, "the finished comparison holds for 2 s after the guide voice"

# ---------------------------------------------------------------- layout and colours

GRAPH_BOX = (1200, 200, 1700, 820)                  # the map, on the right (where the right column comes later)
PROJ = project(GRAPH_BOX)
ZPOS = {z["id"]: PROJ(z["lat"], z["lon"]) for z in ZONES}
R = 26
BAND_HW = 64                                        # half-width of the police band (px)
BAND = tuple(int(c) for c in lerp(BLUE, INK, 0.30))

COL_Y0 = 200                                        # both comparison cards stay below the central-question stage
L_BOX = (60, COL_Y0, 900)                           # left card x0, y0, x1
R_BOX = (1020, COL_Y0, 1860)                        # right card x0, y0, x1
PAD = 36
HEAD_SIZE, ITEM_SIZE, POLICY_SIZE = 34, 31, 27
L_ITEM_Y = [COL_Y0 + 108, COL_Y0 + 166]             # left items: top of the text line
L_RULE_Y = COL_Y0 + 230                             # thin rule above the Policy Address line
L_POLICY_Y = COL_Y0 + 252
L_Y1 = COL_Y0 + 318
ST_X = R_BOX[0] + 112                               # right column: station centres
ST_Y = [COL_Y0 + 150 + 100 * i for i in range(4)]   # 350, 450, 550, 650
ST_R = 34
LOOP_X = R_BOX[0] + 50                              # the return arrow runs up this x, left of the stations
R_TEXT_X = ST_X + ST_R + 28
R_Y1 = ST_Y[-1] + ST_R + 44
assert R_Y1 <= 800, "the right column must stay clear of the lower area and the caption band (y 920-990)"
QUESTION_SIZE, QUESTION_CX, QUESTION_CY = 84, W / 2, 475
assert text_size(QUESTION, QUESTION_SIZE, 700)[0] <= W - 240


def ease_out_back(t: float, k: float = 1.25) -> float:
    t = clamp(t)
    return 1 + (k + 1) * (t - 1) ** 3 + k * (t - 1) ** 2


# ---------------------------------------------------------------- sprites (supersampled, cached)

SS = 4


def _down(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.Resampling.LANCZOS)


@lru_cache(maxsize=None)
def text_spr(text: str, size: int, weight: int = 400, fill=INK):
    """Text sprite cropped to its ink box; returns (sprite, dx, dy), the box's offset from the
    'la' origin used by style.draw_text."""
    f = text_font(text, size, weight)
    l, t, r, b = f.getbbox(text, anchor="la")
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=f, fill=(*fill[:3], 255), anchor="la")
    return im, l - 2, t - 2


def text_w(text: str, size: int, weight: int = 400) -> float:
    return text_font(text, size, weight).getlength(text)


def with_alpha(spr: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 0.999:
        return spr
    out = spr.copy()
    out.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    return out


def paste(img: Image.Image, spr: Image.Image, x: float, y: float, alpha: float = 1.0, scale: float = 1.0,
          anchor: str = "lt") -> None:
    """Composites a sprite with opacity and scale; anchor = horizontal (l/m/r) + vertical (t/m/b)."""
    if alpha <= 0.004 or scale <= 0.01:
        return
    if abs(scale - 1.0) > 1e-3:
        spr = spr.resize((max(1, round(spr.width * scale)), max(1, round(spr.height * scale))), Image.Resampling.BICUBIC)
    spr = with_alpha(spr, alpha)
    ox = x - (spr.width / 2 if anchor[0] == "m" else spr.width if anchor[0] == "r" else 0)
    oy = y - (spr.height / 2 if anchor[1] == "m" else spr.height if anchor[1] == "b" else 0)
    ox, oy = int(round(ox)), int(round(oy))
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(spr.width, W - ox), min(spr.height, H - oy)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    img.alpha_composite(spr, dest=(ox + sx0, oy + sy0), source=(sx0, sy0, sx1, sy1))


def put_text(img: Image.Image, x: float, y: float, text: str, size: int, weight: int = 400, fill=INK,
             alpha: float = 1.0, align: str = "l") -> None:
    """Text at the 'la'-style origin (x = left / centre / right edge by align, y = ascender line)."""
    spr, dx, dy = text_spr(text, size, weight, tuple(fill[:3]))
    adv = text_w(text, size, weight)
    x0 = x - (adv / 2 if align == "m" else adv if align == "r" else 0)
    paste(img, spr, x0 + dx, y + dy, alpha)


def put_text_mid(img: Image.Image, x: float, cy: float, text: str, size: int, weight: int = 400, fill=INK,
                 alpha: float = 1.0) -> None:
    """Left-aligned text whose ink is centred vertically on cy."""
    _, t_, _, b = text_font(text, size, weight).getbbox(text, anchor="la")
    put_text(img, x, cy - (t_ + b) / 2, text, size, weight, fill, alpha)


# ---------------------------------------------------------------- the police band

CORRIDOR_PTS = [ZPOS[z] for z in CORRIDOR]


def _seg_dist(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    k = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1))
    return math.hypot(p[0] - ax - k * dx, p[1] - ay - k * dy)


def _partial(pts, k: float):
    """The first fraction k (by length) of a polyline."""
    segs = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    goal, out = k * sum(segs), [pts[0]]
    for (a, b), L in zip(zip(pts, pts[1:]), segs):
        if goal >= L:
            out.append(b)
            goal -= L
        else:
            if goal > 0:
                out.append((lerp(a[0], b[0], goal / L), lerp(a[1], b[1], goal / L)))
            break
    return out


BAND_BLUR = 9
_BM = BAND_HW + 3 * BAND_BLUR + 4
BAND_BOX = (int(min(x for x, _ in CORRIDOR_PTS) - _BM), int(min(y for _, y in CORRIDOR_PTS) - _BM),
            int(max(x for x, _ in CORRIDOR_PTS) + _BM), int(max(y for _, y in CORRIDOR_PTS) + _BM))

# The source says "Ruins to Senado": the band stops just past Senado's disc with a flat (blurred) end
# instead of a full round cap, so it never reaches into Av. de Almeida Ribeiro below.
BAND_EXT = 24
_sx, _sy = CORRIDOR_PTS[-1]
_ux, _uy = _sx - CORRIDOR_PTS[-2][0], _sy - CORRIDOR_PTS[-2][1]
_ul = math.hypot(_ux, _uy)
BAND_PTS = CORRIDOR_PTS + [(_sx + BAND_EXT * _ux / _ul, _sy + BAND_EXT * _uy / _ul)]


@lru_cache(maxsize=64)
def band_spr(k_q: int = 60) -> Image.Image:
    """The soft band over the corridor, revealed to k_q/60 of its length (sprite at BAND_BOX). Round
    cap at the Ruins; the leading cap shrinks over the last stretch so the band ends flat at Senado."""
    x0, y0, x1, y1 = BAND_BOX
    msk = Image.new("L", (x1 - x0, y1 - y0), 0)
    d = ImageDraw.Draw(msk)
    pts = [(x - x0, y - y0) for x, y in _partial(BAND_PTS, k_q / 60)]
    if len(pts) >= 2:
        d.line(pts, fill=255, width=2 * BAND_HW, joint="curve")
    for (x, y), r in ((pts[0], BAND_HW), (pts[-1], BAND_HW * clamp((1 - k_q / 60) / 0.15))):
        if r > 0.5:
            d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    im = Image.new("RGBA", msk.size, (*BAND, 0))
    im.putalpha(msk.filter(ImageFilter.GaussianBlur(BAND_BLUR)))
    return im


def _band_clear_of(zid: str, pad: int = 6, max_a: int = 40) -> bool:
    """True when the full band's alpha stays faint over that zone's disc (plus `pad` px)."""
    a = band_spr(60).getchannel("A")
    x, y = ZPOS[zid]
    for deg in range(0, 360, 5):
        for rr in range(0, R + pad + 1, 4):
            px = int(round(x + rr * math.cos(math.radians(deg)) - BAND_BOX[0]))
            py = int(round(y + rr * math.sin(math.radians(deg)) - BAND_BOX[1]))
            if 0 <= px < a.width and 0 <= py < a.height and a.getpixel((px, py)) > max_a:
                return False
    return True


assert all(_band_clear_of(z["id"]) for z in ZONES if z["id"] not in CORRIDOR), "the band reaches a zone off the corridor"

# "Ruins to Senado": a small label right of the band, level with Rua de S. Paulo (clear of every disc)
_rsp = ZPOS["rua_sao_paulo"]
BAND_LABEL_XY = (_rsp[0] + BAND_HW + 24, _rsp[1] - 16)
assert BAND_LABEL_XY[0] + text_w(BAND_LABEL, 26, 600) <= 1860


# ---------------------------------------------------------------- static layers (cropped sprites)

def _crop(layer: Image.Image):
    bb = layer.getbbox()
    return layer.crop(bb), bb[0], bb[1]


@lru_cache(maxsize=1)
def streets_layer():
    lay = transparent()
    draw_zone_graph(lay, PROJ, labels=False, radius=R)
    return _crop(lay)


@lru_cache(maxsize=1)
def discs_layer():
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for z in ZONES:
        x, y = ZPOS[z["id"]]
        d.ellipse((x - R, y - R, x + R, y + R), fill=(*NAVY_3, 255), outline=(*INK_3, 255), width=2)
    return _crop(lay)


def card_bg(img: Image.Image, box, bar, alpha: float) -> None:
    rounded(img, box, 18, fill=NAVY_2, alpha=0.94 * alpha)
    rounded(img, (box[0], box[1], box[0] + 7, box[3]), 3, fill=bar, alpha=alpha)


# ---------------------------------------------------------------- icons (drawn at SS scale)

def gauge_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float, needle: float) -> None:
    """A dial (three arc segments) with a needle at `needle` (0 = left, 1 = right): how sure a forecast is."""
    r = 22 * s
    box = (cx - r, cy - r + 8 * s, cx + r, cy + r + 8 * s)
    for a0, a1 in ((182, 236), (242, 298), (304, 358)):
        d.arc(box, a0, a1, fill=(*INK, 255), width=int(5 * s))
    ang = math.radians(180 + 180 * needle)
    ox, oy = cx, cy + 8 * s
    d.line([(ox, oy), (ox + 17 * s * math.cos(ang), oy + 17 * s * math.sin(ang))], fill=(*CYAN, 255), width=int(4 * s))
    d.ellipse((ox - 5 * s, oy - 5 * s, ox + 5 * s, oy + 5 * s), fill=(*INK, 255))


def person_glyph(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float) -> None:
    """A person (head and shoulders): the one who approves."""
    d.ellipse((cx - 9 * s, cy - 22 * s, cx + 9 * s, cy - 4 * s), fill=(*INK, 255))
    d.rounded_rectangle((cx - 17 * s, cy + 1 * s, cx + 17 * s, cy + 24 * s), int(11 * s), fill=(*INK, 255))


ICON_BOX = 64                                       # icon sprites are ICON_BOX x ICON_BOX (1x px), centred


@lru_cache(maxsize=None)
def icon_spr(kind: str, needle_q: int = 0) -> Image.Image:
    big = Image.new("RGBA", (ICON_BOX * SS, ICON_BOX * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = ICON_BOX * SS / 2
    if kind == "phone":
        d.rounded_rectangle((c - 16 * SS, c - 25 * SS, c + 16 * SS, c + 25 * SS),
                            5 * SS, outline=(*INK, 255), width=3 * SS)
        d.line([(c - 6 * SS, c + 18 * SS), (c + 6 * SS, c + 18 * SS)], fill=(*CYAN, 255), width=3 * SS)
    elif kind == "counts":
        for x, y in ((c - 16 * SS, c + 3 * SS), (c, c - 4 * SS), (c + 16 * SS, c + 3 * SS)):
            person_glyph(d, x, y, 0.45 * SS)
    elif kind == "gauge":
        gauge_icon(d, c, c, SS, needle_q / 20)
    else:
        person_glyph(d, c, c, SS)
    return _down(big, ICON_BOX, ICON_BOX)


STATION_ICONS = ["phone", "counts", "gauge", "person"]


@lru_cache(maxsize=1)
def event_staff_spr() -> Image.Image:
    """The same hi-vis staff figures used elsewhere in the video, without official insignia."""
    big = Image.new("RGBA", (140 * SS, 120 * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    for x in (36, 104):
        staff_icon(d, x * SS, 68 * SS, 1.5 * SS)
    return _down(big, 140, 120)


# layout checks: every line fits its card, and the right column's items are left-aligned past the stations
assert PAD + 10 + text_w(LEFT_HEAD, HEAD_SIZE, 700) <= L_BOX[2] - L_BOX[0] - PAD, LEFT_HEAD
assert all(PAD + 40 + text_w(t, ITEM_SIZE, 500) <= L_BOX[2] - L_BOX[0] - PAD for t in LEFT_ITEMS), LEFT_ITEMS
assert PAD + 10 + text_w(POLICY, POLICY_SIZE, 600) <= L_BOX[2] - L_BOX[0] - PAD, POLICY
assert all(R_TEXT_X + text_w(t, ITEM_SIZE, 600) <= R_BOX[2] - PAD for t in RIGHT_ITEMS), RIGHT_ITEMS
assert R_TEXT_X + text_w(PHONE_DETAIL, 24, 500) <= R_BOX[2] - PAD
assert R_BOX[0] + PAD + 10 + text_w(FRAMING, 24, 500) <= R_BOX[2] - PAD
assert R_BOX[0] + 220 + text_w(KIT, 34, 600) <= R_BOX[2] - PAD


# ---------------------------------------------------------------- drawing

def band_alpha(t: float) -> float:
    base = 0.34 * progress(t, BEATS["band"], 0.5)
    here = 0.22 * math.sin(math.pi * clamp((t - BEATS["here"]) / 0.7))
    return clamp(base + here)


def draw_map(img: Image.Image, t: float) -> None:
    a = progress(t, BEATS["map"], 0.3) * (1 - progress(t, BEATS["map_out"], 0.5))
    if a <= 0:
        return
    k = progress(t, BEATS["band"], 0.9)
    if k > 0:
        spr = band_spr(max(1, int(round(k * 60))))
        paste(img, spr, BAND_BOX[0], BAND_BOX[1], band_alpha(t) * a)
    for spr, x0, y0 in (streets_layer(), discs_layer()):
        paste(img, spr, x0, y0, a)
    kl = progress(t, BEATS["band_label"], 0.4)
    put_text(img, BAND_LABEL_XY[0] - (1 - kl) * 12, BAND_LABEL_XY[1], BAND_LABEL, 26, 600, INK_2, kl * a)


def draw_left(img: Image.Image, t: float) -> None:
    """The police column: header, its two items, then the Policy Address line under a thin rule."""
    a = progress(t, BEATS["left"], FADE)
    if a <= 0:
        return
    x0, y0, x1 = L_BOX
    k_pol = progress(t, BEATS["policy"], 0.4)
    y1 = lerp(L_RULE_Y - 8, L_Y1, k_pol)               # the card grows to take the Policy Address line
    card_bg(img, (x0 - (1 - a) * 18, y0, x1 - (1 - a) * 18, y1), BAND, a)
    put_text(img, x0 + PAD + 10, y0 + 30, LEFT_HEAD, HEAD_SIZE, 700, INK, a)
    for i, txt in enumerate(LEFT_ITEMS):
        k = progress(t, BEATS[f"left_{i + 1}"], 0.4)
        if k <= 0:
            continue
        y = L_ITEM_Y[i] + (1 - k) * 10
        rounded(img, (x0 + PAD + 12, y + 12, x0 + PAD + 24, y + 24), 3, fill=BAND, alpha=k)
        put_text(img, x0 + PAD + 40, y, txt, ITEM_SIZE, 500, INK, k)
    if k_pol > 0:
        rounded(img, (x0 + PAD + 10, L_RULE_Y, x1 - PAD, L_RULE_Y + 2), 1, fill=NAVY_3, alpha=k_pol)
        put_text(img, x0 + PAD + 10, L_POLICY_Y + (1 - k_pol) * 10, POLICY, POLICY_SIZE, 600, INK_2, k_pol)


def _arrow_head(d: ImageDraw.ImageDraw, tip, direction, colour, size=9.0) -> None:
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    d.polygon([tip, (tip[0] - ux * size * 1.5 + px * size, tip[1] - uy * size * 1.5 + py * size),
               (tip[0] - ux * size * 1.5 - px * size, tip[1] - uy * size * 1.5 - py * size)], fill=colour)


def draw_loop(img: Image.Image, t: float) -> None:
    """The loop: a link down between each pair of stations, and a return arrow up the left back to the top.
    It follows the operator introduction; the return arrow lights as staff review before acting."""
    k = progress(t, BEATS["loop"], 0.6)
    if k <= 0:
        return
    lay = transparent()
    d = ImageDraw.Draw(lay)
    base = (*INK_3, int(255 * k))
    for i in range(3):                                # links grow top to bottom
        kk = clamp(k * 3 - i)
        if kk <= 0:
            continue
        ya, yb = ST_Y[i] + ST_R + 6, ST_Y[i + 1] - ST_R - 6
        yy = lerp(ya, yb, kk)
        d.line([(ST_X, ya), (ST_X, yy)], fill=base, width=3)
        if kk >= 1:
            _arrow_head(d, (ST_X, yb + 1), (0, 1), base, 7)
    kr = clamp(k * 1.6 - 0.6)                         # then the return arrow, up the left
    c = tuple(int(v) for v in lerp(INK_3, CYAN, progress(t, BEATS["close"], 0.5)))
    if kr > 0:
        ra = (*c, int(255 * kr))
        xs, xr = ST_X - ST_R - 6, LOOP_X
        y_bot, y_top = ST_Y[-1], ST_Y[0]
        pts = [(xs, y_bot), (xr + 14, y_bot), (xr, y_bot - 14), (xr, y_top + 14), (xr + 14, y_top), (xs - 2, y_top)]
        segs = [math.dist(a_, b_) for a_, b_ in zip(pts, pts[1:])]
        goal, path = kr * sum(segs), [pts[0]]
        for (a_, b_), L in zip(zip(pts, pts[1:]), segs):
            if goal >= L:
                path.append(b_)
                goal -= L
            else:
                path.append(lerp(a_, b_, goal / L))
                break
        w_ = 3 + int(round(progress(t, BEATS["close"], 0.5)))
        d.line(path, fill=ra, width=w_, joint="curve")
        if kr >= 1:
            _arrow_head(d, (xs, y_top), (1, 0), ra, 8)
    img.alpha_composite(lay)


def draw_right(img: Image.Image, t: float) -> None:
    """Introduce the intended event staff and kit first, then reveal their operating loop."""
    a = progress(t, BEATS["right"], FADE)
    if a <= 0:
        return
    x0, y0, x1 = R_BOX
    card_bg(img, (x0 + (1 - a) * 18, y0, x1 + (1 - a) * 18, R_Y1), CYAN, a)
    kh = progress(t, BEATS["right_head"], 0.4)
    put_text(img, x0 + PAD + 10, y0 + 30 + (1 - kh) * 10, RIGHT_HEAD, HEAD_SIZE, 700, CYAN, kh)
    framing = progress(t, BEATS["framing"], 0.4)
    put_text(img, x0 + PAD + 10, y0 + 80, FRAMING, 24, 500, INK_2, framing)

    intro = progress(t, BEATS["operator"], 0.35) * (1 - progress(t, BEATS["stations"] - 0.25, 0.35))
    if intro > 0:
        paste(img, event_staff_spr(), x0 + 56, y0 + 180, intro)
        put_text_mid(img, x0 + 220, y0 + 210, OPERATOR, 44, 700, INK, intro)
        put_text_mid(img, x0 + 220, y0 + 270, KIT, 34, 600, INK_2, intro)

    stations = progress(t, BEATS["stations"], 0.35)
    if stations <= 0:
        return
    draw_loop(img, t)
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for i in range(4):                                # station discs: grey while waiting, cyan rim once named
        lit = progress(t, BEATS[f"item_{i}"], 0.4)
        rim = tuple(int(v) for v in lerp(INK_3, CYAN, lit))
        d.ellipse((ST_X - ST_R, ST_Y[i] - ST_R, ST_X + ST_R, ST_Y[i] + ST_R), fill=(*NAVY_3, int(255 * a * stations)),
                  outline=(*rim, int(255 * a * stations)), width=3)
    img.alpha_composite(lay)
    for i, txt in enumerate(RIGHT_ITEMS):
        k = progress(t, BEATS[f"item_{i}"], 0.4)
        kind = STATION_ICONS[i]
        if k > 0:
            needle_q = 4 + round(10 * progress(t, BEATS["needle"], 0.6)) if kind == "gauge" else 0
            paste(img, icon_spr(kind, needle_q), ST_X, ST_Y[i], clamp(k / 0.5), scale=lerp(0.6, 1.0, ease_out_back(k)), anchor="mm")
        if k > 0:
            detail = progress(t, BEATS["phone_detail"], 0.4) if i == 0 else 0.0
            put_text_mid(img, R_TEXT_X + (1 - k) * 14, ST_Y[i] - 12 * detail, txt, ITEM_SIZE, 600, INK, k)
            if i == 0:
                put_text_mid(img, R_TEXT_X, ST_Y[i] + 25, PHONE_DETAIL, 24, 500, INK_2, detail)


# ---------------------------------------------------------------- frame

BASE = canvas()
QUESTION_SCRIM = Image.new("RGBA", (W, H), (*NAVY, 235))


def question_alpha(t: float) -> float:
    if t < QUESTION_START or t >= QUESTION_END:
        return 0.0
    return min(
        progress(t, QUESTION_START, QUESTION_IN),
        1 - progress(t, QUESTION_END - QUESTION_OUT, QUESTION_OUT),
    )


def draw_question(img: Image.Image, t: float) -> None:
    """A single dominant question over static, dimmed context; no other animation runs here."""
    alpha = question_alpha(t)
    if alpha <= 0:
        return
    paste(img, QUESTION_SCRIM, 0, 0, alpha)
    spr, _, _ = text_spr(QUESTION, QUESTION_SIZE, 700, INK)
    paste(img, spr, QUESTION_CX, QUESTION_CY, alpha, anchor="mm")
    rounded(img, (QUESTION_CX - 84, QUESTION_CY + 75,
                  QUESTION_CX + 84, QUESTION_CY + 80), 2, fill=CYAN, alpha=alpha)


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    # The existing-system context settles before the question. Keep its pixels
    # fixed throughout the focused question, then fade only the map away.
    context_time = min(t, QUESTION_START)
    map_layer = transparent()
    draw_map(map_layer, context_time)
    paste(img, map_layer, 0, 0, 1 - progress(t, BEATS["map_out"], 0.5))
    draw_left(img, context_time)
    if t >= QUESTION_END:
        draw_right(img, t)
    draw_question(img, t)
    footer(img, FOOTER)
    return img


STILLS = {  # beat name -> time (s) for the layout stills
    "band": 1.6,
    "here": 3.35,
    "question": 4.0,
    "question_hold": 5.3,
    "question_exit": 5.85,
    "operator": 7.5,
    "support": 9.8,
    "phones": 11.8,
    "counts": 14.5,
    "forecasts": 16.6,
    "review": 19.2,
    "end": DURATION - 1 / FPS,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, nargs="*")
    ap.add_argument("--stills", action="store_true")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.preview:
        args.out.mkdir(parents=True, exist_ok=True)
        for t in args.preview:
            draw_frame(t).convert("RGB").save(args.out / f"{SHOT}_t{t:05.2f}.png")
        return
    if not args.stills:
        print(render(SHOT, DURATION, draw_frame))
    for name, t in STILLS.items():
        print(still(f"{SHOT}_{name}", draw_frame(t)))


if __name__ == "__main__":
    main()
