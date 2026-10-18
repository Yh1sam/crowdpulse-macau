"""Shot S07, "How is ours different?" (0:39.5-1:00.0, 20.5 s), [MEMBER 4] voice-over. Motion graphic.

The WHY -> HOW hinge. Credits the police crowd warning system and its planned expansion (on screen),
states the team's two aims (privacy, no one left behind), then claims only what CrowdPulse proposes, as
one loop: movable phones that send only numbers, forecasts that say how sure they are, and detours
checked for stairs that a person must approve. Since 19 Oct the shot ends on ONE clean two-column
comparison (a judge asked for the difference from the existing system to be explained more directly):
"Police system (public information)" on the left, "What we propose" on the right. It replaces the dense
police panel and the "What we propose" keyword line, and the phones / packets / forecast chips on the map.

Beats (keyed to the guide voice, see BEATS):
  "Macau's police already run a crowd warning system here."
        The 7-zone graph on the right. A soft shaded band lights up over the zone model's whole corridor
        (Ruins -> Company of Jesus Square -> Rua de S. Paulo -> St. Dominic's -> Senado), labelled
        "Ruins to Senado", and brightens once on "here". The band is an area only: no camera positions
        are drawn. It ends flat just past Senado's disc, short of Av. de Almeida Ribeiro. On the left the
        police column builds on the voice (header, its two items, then the Policy Address line under it)
        and stays to the end of the shot.
  "We believe crowd safety shouldn't cost anyone their privacy, or leave anyone behind."
        The map fades out; two principle chips build on the right, "Privacy" (a crossed-out picture) on
        "privacy" and "No one left behind" (a wheelchair) on "leave anyone behind". No numbers, no claims:
        the team's aims, as the voice says.
  "So we propose one loop: movable phones that send only numbers, forecasts that say how sure they are,
   and detours checked for stairs that a person must approve."
        The chips' words fade and their two icons move into the right column, onto its first and third
        stations; "What we propose" comes in on "propose"; the loop draws on "one loop" (four stations
        linked downwards, a return arrow back to the top); the items arrive on "movable", "forecasts"
        (a gauge whose needle settles on "how sure"), "detours" and "a person"; the return arrow lights on
        "approve" and both columns hold for the last 2.1 s. The two columns are never aligned row by row
        and carry no ticks or crosses, so nothing reads as a feature the police system lacks.

Data sources (nothing below is retyped):
- docs/video/shotlist.json, S07: duration, narration and every on-screen line (only the timing labels are
  stripped), each checked word for word against the S07 storyboard row in docs/video/script.md section 3.
- shared/zones.json: the 7 zones and 7 streets (style.draw_zone_graph). The band's corridor is the
  shortest street path from the Ruins to Senado Square.

Output: video/build/mg/S07.mp4 and video/build/mg/stills/S07_<beat>.png.
Run:    .venv/bin/python video/mg/S07.py                          full render + stills
        .venv/bin/python video/mg/S07.py --stills                 stills only
        .venv/bin/python video/mg/S07.py --preview 1.5 9.0 --out DIR   single frames for checks
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
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 20.5 s
NARRATION = _shot["narration"]

_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
_cols = [c.strip() for c in _row.strip().strip("|").split(" | ")]
assert len(_cols) == 7 and _cols[3] == NARRATION, "storyboard row S07 and shotlist.json disagree on the narration"

_KEYS = ["Chapter card", "Left column", "Under it", "Band label", "Two principle chips", "Right column", "Footer"]
_spec = {}
for _part in _shot["on_screen_text"].split(" | "):
    _m = re.match(r"^([A-Z][a-z ]+?)(?: \(([^)]*)\))?: (.*)$", _part.strip())
    assert _m and _m.group(1) in _KEYS, f"unexpected on-screen part: {_part!r}"
    _spec[_m.group(1)] = _m.group(3)
assert list(_spec) == _KEYS, list(_spec)                          # 19 Oct declutter: nothing else on screen
CARD, POLICY, BAND_LABEL, FOOTER = _spec["Chapter card"], _spec["Under it"], _spec["Band label"], _spec["Footer"]
LEFT_HEAD, *LEFT_ITEMS = _spec["Left column"].split(" · ")
PRINCIPLES = _spec["Two principle chips"].split(" · ")            # ["Privacy", "No one left behind"]
RIGHT_HEAD, *RIGHT_ITEMS = _spec["Right column"].split(" · ")
assert LEFT_HEAD == "Police system (public information)" and RIGHT_HEAD == "What we propose", (LEFT_HEAD, RIGHT_HEAD)
assert len(LEFT_ITEMS) == 2 and len(RIGHT_ITEMS) == 4 and len(PRINCIPLES) == 2
for _txt in (CARD, LEFT_HEAD, *LEFT_ITEMS, POLICY, BAND_LABEL, *PRINCIPLES, RIGHT_HEAD, *RIGHT_ITEMS, FOOTER):
    assert f'"{_txt}"' in _cols[5], f"not in the storyboard row: {_txt!r}"
assert not any(c.isdigit() for c in "".join(PRINCIPLES + RIGHT_ITEMS)), "the team's aims and proposal carry no numbers"
# never set the two systems against each other in words (script.md section 6, "Never say or show")
_all = " ".join([LEFT_HEAD, *LEFT_ITEMS, POLICY, RIGHT_HEAD, *RIGHT_ITEMS]).lower()
assert not any(w in _all for w in ("better", "replace", "lack", "we'd add", "instead")), _all
# 19 Oct declutter: labels of at most 6 words, a short source footer that fits one line of the footer slot
assert all(len(t.split()) <= 6 for t in (*LEFT_ITEMS, POLICY, BAND_LABEL, *PRINCIPLES, *RIGHT_ITEMS)), "a label is too long"
assert len(FOOTER.replace(" · ", " ").split()) <= 7 and text_size(FOOTER, 20, 500)[0] <= 1150, FOOTER

# The narration, clause by clause as the guide voice pauses (BEATS are keyed to these).
CLAUSES = ["Macau's police already run a crowd warning system here.",
           "We believe crowd safety shouldn't cost anyone their privacy,", "or leave anyone behind.",
           "So we propose one loop:", "movable phones that send only numbers,", "forecasts that say how sure they are,",
           "and detours checked for stairs that a person must approve."]
assert " ".join(CLAUSES) == NARRATION, "narration changed: re-measure the guide voice and re-key BEATS"
# each right-column item arrives on the voice's own words for it
_LOOP_WORDS = [("movable phones", "only numbers"), ("forecasts", "how sure"), ("detours", "stairs"), ("a person", "approve")]
assert all(a in NARRATION and b in NARRATION for a, b in _LOOP_WORDS)
assert [it.split()[0].lower() for it in RIGHT_ITEMS] == ["movable", "forecasts", "detours", "a"], RIGHT_ITEMS

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
# Guide voice video/build/guide/S07.wav (say -v Daniel -r 155), laid at 0.2 s into the shot.
# Clause boundaries from `ffmpeg -af silencedetect=noise=-35dB:d=0.08` on the wav, plus 0.2 s:
#   0.20-3.49   "Macau's police already run a crowd warning system here."
#   3.73-7.04   "We believe crowd safety shouldn't cost anyone their privacy,"
#   7.25-8.68   "or leave anyone behind."
#   8.94-10.32  "So we propose one loop:"
#   10.59-12.80 "movable phones that send only numbers,"
#   13.03-15.16 "forecasts that say how sure they are,"
#   15.36-18.41 "and detours checked for stairs that a person must approve."   (then 2.1 s without voice)
# Word times inside a clause from the speech end of `say` on the words before them (guide.spoken_text
# applied), plus 0.2 s: "police" 0.85, "crowd warning system" 1.88, "here" 3.13, "privacy" 6.63,
# "leave" 7.59, "behind" 8.16, "propose" 9.56, "one loop" 10.0, "movable" 10.59, "phones" 11.13,
# "only numbers" 12.07, "forecasts" 13.03, "how sure" 14.29, "detours" 15.71, "stairs" 16.82,
# "a person" 17.32, "approve" 18.04.
# re-key to the real voice take (the team speaks at about 140 wpm)
BEATS = {
    "card": 0.0,          # chapter card in (out after about 2 s)
    "map": 0.0,           # the zone graph, on the right
    "band": 0.15,         # "Macau's police": the band sweeps Ruins -> Senado
    "left": 0.85,         # "police": the police column and its header
    "band_label": 1.4,    # "Ruins to Senado", as the band reaches St. Dominic's
    "left_1": 1.88,       # "crowd warning system": "Real-time monitoring and alerts"
    "left_2": 2.6,        # "system here": "Zone forecasts planned"
    "here": 3.13,         # "here": the band brightens once
    "policy": 3.75,       # sentence ends: the 2026 Policy Address line under the column (on screen only)
    "map_out": 4.6,       # "crowd safety": the map and its label fade (gone by 5.1); the column reads alone
    "privacy": 6.63,      # "privacy": first principle chip
    "behind": 7.59,       # "leave anyone behind": second principle chip
    "fold": 9.1,          # "So we propose": the chips' words fade, their icons move into the right column
    "right": 9.3,         # the right column's card and its four empty stations
    "right_head": 9.56,   # "propose": "What we propose"
    "loop": 10.0,         # "one loop": the loop draws (links down, return arrow up)
    "item_0": 10.65,      # "movable phones": "Movable phones, numbers only"
    "item_1": 13.05,      # "forecasts": "Forecasts that state their confidence" (gauge icon)
    "needle": 14.3,       # "how sure": the gauge's needle settles
    "item_2": 15.75,      # "detours": "Detours checked for stairs"
    "item_3": 17.35,      # "a person": "A person must approve" (person icon)
    "close": 18.05,       # "approve": the return arrow lights; the loop is closed
}
CARD_HOLD = 2.0
FADE = 0.35
# every right-column item reads for at least 0.3 s per word + 0.5 s (19 Oct declutter, rule 5)
for _i, _it in enumerate(RIGHT_ITEMS):
    assert DURATION - BEATS[f"item_{_i}"] >= 0.3 * len(_it.split()) + 0.5, _it
assert BEATS["map_out"] - BEATS["band_label"] >= 0.3 * len(BAND_LABEL.split()) + 0.5
assert DURATION - (18.41) >= 2.0, "the finished comparison holds for 2 s after the voice"

# ---------------------------------------------------------------- layout and colours

GRAPH_BOX = (1200, 200, 1700, 820)                  # the map, on the right (where the right column comes later)
PROJ = project(GRAPH_BOX)
ZPOS = {z["id"]: PROJ(z["lat"], z["lon"]) for z in ZONES}
R = 26
BAND_HW = 64                                        # half-width of the police band (px)
BAND = tuple(int(c) for c in lerp(BLUE, INK, 0.30))

COL_Y0 = 200                                        # both column cards start here (chapter card: y 48-112)
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
PRINCIPLE_H, PRINCIPLE_GAP, PRINCIPLE_SIZE = 84, 16, 36   # principle chips, stacked on the right
PRINCIPLE_CX = (R_BOX[0] + R_BOX[2]) / 2
PRINCIPLE_Y0 = 400


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

def no_image_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float) -> None:
    """A picture (frame, hills, sun) struck through: no images. The strike cuts a clear gap."""
    w, h = 52 * s, 40 * s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), int(7 * s), outline=(*INK, 255), width=int(4 * s))
    d.polygon([(cx - w / 2 + 7 * s, cy + h / 2 - 7 * s), (cx - 7 * s, cy - 3 * s), (cx + 3 * s, cy + 7 * s),
               (cx + 10 * s, cy + 1 * s), (cx + w / 2 - 7 * s, cy + h / 2 - 7 * s)], fill=(*INK, 255))
    d.ellipse((cx + 8 * s, cy - h / 2 + 8 * s, cx + 17 * s, cy - h / 2 + 17 * s), fill=(*INK, 255))
    a, b = (cx - w / 2 - 4 * s, cy - h / 2 - 7 * s), (cx + w / 2 + 4 * s, cy + h / 2 + 7 * s)
    d.line([a, b], fill=(0, 0, 0, 0), width=int(13 * s))         # ImageDraw replaces pixels: a transparent gap
    d.line([a, b], fill=(*INK, 255), width=int(4 * s))


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
    if kind == "privacy":
        no_image_icon(d, c, c, 0.85 * SS)
    elif kind == "wheelchair":                     # style.wheelchair_icon is drawn about (-4, -3) off its centre
        wheelchair_icon(d, c + 4 * 1.05 * SS, c + 3 * 1.05 * SS, 1.05 * SS, colour=(*INK, 255), width=4)
    elif kind == "gauge":
        gauge_icon(d, c, c, SS, needle_q / 20)
    else:
        person_glyph(d, c, c, SS)
    return _down(big, ICON_BOX, ICON_BOX)


STATION_ICONS = ["privacy", "gauge", "wheelchair", "person"]   # station i's icon; 0 and 2 come from the chips
CHIP_ICON = {0: "privacy", 1: "wheelchair"}                     # principle chip -> its icon
CHIP_STATION = {0: 0, 1: 2}                                     # ... and the station it folds onto
CHIP_ICON_SCALE = 1.2


@lru_cache(maxsize=None)
def principle_spr(i: int) -> Image.Image:
    """Principle chip i without its icon: label on the panel's navy, with a CrowdPulse-cyan bar at left;
    the icon is pasted separately (it moves into the right column at the fold)."""
    label = PRINCIPLES[i]
    tx = PAD + 10 + ICON_BOX + 16
    w, h = int(tx + text_w(label, PRINCIPLE_SIZE, 700) + PAD + 4), PRINCIPLE_H
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rounded(lay, (0, 0, w - 1, h - 1), 16, fill=NAVY_2, alpha=0.94)
    rounded(lay, (0, 0, 7, h - 1), 3, fill=CYAN)
    l, t_, r, b = text_font(label, PRINCIPLE_SIZE, 700).getbbox(label, anchor="la")
    put_text(lay, tx, h / 2 - (t_ + b) / 2, label, PRINCIPLE_SIZE, 700, INK)
    return lay


def principle_box(i: int) -> tuple[float, float]:
    """Top-left of principle chip i (stacked and left-aligned, the pair centred on the right column)."""
    return PRINCIPLE_CX - max(principle_spr(j).width for j in range(2)) / 2, PRINCIPLE_Y0 + i * (PRINCIPLE_H + PRINCIPLE_GAP)


def chip_icon_centre(i: int) -> tuple[float, float]:
    x, y = principle_box(i)
    return x + PAD + 10 + ICON_BOX / 2, y + PRINCIPLE_H / 2


# layout checks: every line fits its card, and the right column's items are left-aligned past the stations
assert PAD + 10 + text_w(LEFT_HEAD, HEAD_SIZE, 700) <= L_BOX[2] - L_BOX[0] - PAD, LEFT_HEAD
assert all(PAD + 40 + text_w(t, ITEM_SIZE, 500) <= L_BOX[2] - L_BOX[0] - PAD for t in LEFT_ITEMS), LEFT_ITEMS
assert PAD + 10 + text_w(POLICY, POLICY_SIZE, 600) <= L_BOX[2] - L_BOX[0] - PAD, POLICY
assert all(R_TEXT_X + text_w(t, ITEM_SIZE, 600) <= R_BOX[2] - PAD for t in RIGHT_ITEMS), RIGHT_ITEMS
assert all(PRINCIPLE_CX + principle_spr(i).width / 2 <= 1860 for i in range(2))


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


def draw_principles(img: Image.Image, t: float) -> None:
    """The two principle chips; at the fold their words fade while their icons fly to stations 1 and 3."""
    words_out = 1 - progress(t, BEATS["fold"], 0.3)
    fly = progress(t, BEATS["fold"], 0.65)
    for i, key in enumerate(("privacy", "behind")):
        k = progress(t, BEATS[key], 0.35)
        if k <= 0:
            continue
        x, y = principle_box(i)
        paste(img, principle_spr(i), x - 24 * (1 - k), y, k * words_out)
        cx, cy = chip_icon_centre(i)
        sx, sy = ST_X, ST_Y[CHIP_STATION[i]]
        px, py = lerp(cx - 24 * (1 - k), sx, fly), lerp(cy, sy, fly) - 40 * math.sin(math.pi * fly)
        paste(img, icon_spr(CHIP_ICON[i]), px, py, k, scale=lerp(CHIP_ICON_SCALE, 1.0, fly), anchor="mm")


def _arrow_head(d: ImageDraw.ImageDraw, tip, direction, colour, size=9.0) -> None:
    dx, dy = direction
    n = math.hypot(dx, dy) or 1
    ux, uy = dx / n, dy / n
    px, py = -uy, ux
    d.polygon([tip, (tip[0] - ux * size * 1.5 + px * size, tip[1] - uy * size * 1.5 + py * size),
               (tip[0] - ux * size * 1.5 - px * size, tip[1] - uy * size * 1.5 - py * size)], fill=colour)


def draw_loop(img: Image.Image, t: float) -> None:
    """The loop: a link down between each pair of stations, and a return arrow up the left back to the top.
    Drawn on "one loop"; the return arrow turns cyan on "approve" (the loop is closed)."""
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
    """The right column: card, header, four stations on the loop, the items as the voice names them."""
    a = progress(t, BEATS["right"], FADE)
    if a <= 0:
        return
    x0, y0, x1 = R_BOX
    card_bg(img, (x0 + (1 - a) * 18, y0, x1 + (1 - a) * 18, R_Y1), CYAN, a)
    kh = progress(t, BEATS["right_head"], 0.4)
    put_text(img, x0 + PAD + 10, y0 + 30 + (1 - kh) * 10, RIGHT_HEAD, HEAD_SIZE, 700, CYAN, kh)
    draw_loop(img, t)
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for i in range(4):                                # station discs: grey while waiting, cyan rim once named
        lit = progress(t, BEATS[f"item_{i}"], 0.4)
        rim = tuple(int(v) for v in lerp(INK_3, CYAN, lit))
        d.ellipse((ST_X - ST_R, ST_Y[i] - ST_R, ST_X + ST_R, ST_Y[i] + ST_R), fill=(*NAVY_3, int(255 * a)),
                  outline=(*rim, int(255 * a)), width=3)
    img.alpha_composite(lay)
    fly_done = t >= BEATS["fold"] + 0.65
    for i, txt in enumerate(RIGHT_ITEMS):
        k = progress(t, BEATS[f"item_{i}"], 0.4)
        kind = STATION_ICONS[i]
        if i in CHIP_STATION.values():                # chip icons: drawn here once they have landed
            if fly_done:
                paste(img, icon_spr(kind), ST_X, ST_Y[i], 1.0, anchor="mm")
        elif k > 0:
            needle_q = 4 + round(10 * progress(t, BEATS["needle"], 0.6)) if kind == "gauge" else 0
            paste(img, icon_spr(kind, needle_q), ST_X, ST_Y[i], clamp(k / 0.5), scale=lerp(0.6, 1.0, ease_out_back(k)), anchor="mm")
        if k > 0:
            put_text_mid(img, R_TEXT_X + (1 - k) * 14, ST_Y[i], txt, ITEM_SIZE, 600, INK, k)


# ---------------------------------------------------------------- frame

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    draw_map(img, t)
    draw_left(img, t)
    draw_right(img, t)
    if t < BEATS["fold"] + 0.65:
        draw_principles(img, t)
    # fixed slots
    chapter_card(img, CARD, fade(t, BEATS["card"] - 0.3, BEATS["card"] + CARD_HOLD + 0.3, 0.3))
    footer(img, FOOTER)
    return img


STILLS = {  # beat name -> time (s) for the layout stills
    "band": 1.6,
    "here": 3.35,
    "policy": 4.4,
    "belief": 5.8,
    "privacy": 7.1,
    "principles": 8.7,
    "fold": 9.45,
    "loop": 10.5,
    "phones": 12.4,
    "forecasts": 14.8,
    "detours": 16.9,
    "approve": 18.5,
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
