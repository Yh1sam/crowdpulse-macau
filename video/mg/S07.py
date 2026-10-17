"""Shot S07, "How is ours different?" (0:42.0-0:59.0, 17.0 s), [MEMBER 4] voice-over. Motion graphic.

The WHY -> HOW hinge. Credits the police crowd forecast and early-warning system and its planned
expansion (on screen), states the team's two aims (privacy, no one left behind), then claims only
what CrowdPulse proposes: movable phones that send only numbers, 5-15 minute forecasts that say how
sure they are (a confidence score), and a person's approval.

Beats (keyed to the guide voice, see BEATS):
  "Macau's police already run a crowd warning system here."
        The 7-zone graph. A soft shaded band lights up over the zone model's whole corridor
        (Ruins -> Company of Jesus Square -> Rua de S. Paulo -> St. Dominic's -> Senado); the police
        panel (system name + the "Officially: ..." line) labels it with a leader line, and the
        "2026 Policy Address" line comes in under it. The band is an area only: no camera positions
        are drawn. It ends flat just past Senado's disc, short of Av. de Almeida Ribeiro ("Ruins to
        Senado").
  "We believe crowd safety shouldn't cost anyone their privacy, or leave anyone behind."
        The map stays as it is. The police lines leave at 6 s; two principle chips build in their
        place, "Privacy" (a crossed-out picture) on "privacy" and "No one left behind" (a wheelchair)
        on "leave anyone behind". No numbers, no claims: the team's aims, as the voice says.
  "So we propose movable phones that send only numbers, and forecasts that say how sure they are."
        The chips leave. One phone per sensor in shared/zones.json drops, inside the band
        and on the Tercena route alike (no square is singled out; each phone sits clear of other
        zones' phones); number packets flow to a server, fanning over its racks and fading in;
        every zone gets +5 / +10 / +15 min chips, then a confidence dot in each chip; the "What
        we propose" line builds up item by item.

Data sources (nothing below is retyped):
- docs/video/shotlist.json, S07: duration, narration and every on-screen line (only the timing
  prefixes are stripped), each checked word for word against the S07 storyboard row in
  docs/video/script.md section 3.
- shared/zones.json: the 7 zones and 7 streets (style.draw_zone_graph) and the 9 sensors (one phone
  each). The band's corridor is the shortest street path from the Ruins to Senado Square.
- shared/config.json: forecast_horizons_min (the chips), checked against the "What we propose" line.

The zoom out to a Macau schematic (grey pins for border posts and scenic areas), keyed to the old
", and plan to expand it", went when those words left the voice (18 Oct restructure).

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
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 17.0 s
NARRATION = _shot["narration"]

_row = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {SHOT} |"))
_cols = [c.strip() for c in _row.strip().strip("|").split(" | ")]
assert len(_cols) == 7 and _cols[3] == NARRATION, "storyboard row S07 and shotlist.json disagree on the narration"

_PREFIX = re.compile(r"^(?:Chapter card \(top-left\)|From 0 s, held to 6 s|From 2 s, held to 6 s|"
                     r"6\.4-9\.5 s, two principle chips|9\.8-17 s|Footer): ")
_lines = []
for _part in _shot["on_screen_text"].split(" | "):
    _m = _PREFIX.match(_part.strip())
    assert _m, f"unexpected on-screen part: {_part!r}"
    _lines.append(_part.strip()[_m.end():])
CARD, _police, POLICY, _principles, TAGLINE, FOOTER = _lines
POLICE_NAME, POLICE_STATUS = _police.split(" · ")
PRINCIPLES = _principles.split(" · ")                              # ["Privacy", "No one left behind"]
assert len(PRINCIPLES) == 2, PRINCIPLES
for _txt in (CARD, POLICE_NAME, POLICE_STATUS, POLICY, *PRINCIPLES, TAGLINE, FOOTER):
    assert f'"{_txt}"' in _cols[5], f"not in the storyboard row: {_txt!r}"
assert not any(c.isdigit() for c in _principles), "the principle chips carry no numbers"
assert "horizon and accuracy not published" in POLICE_STATUS      # section 6: kept next to the system's name
assert text_size(FOOTER, 20, 500)[0] <= 1150, "footer must fit one line of the footer slot"

HORIZONS = json.loads((ROOT / "shared" / "config.json").read_text())["forecast_horizons_min"]   # [5, 10, 15]
assert f"{HORIZONS[0]}-{HORIZONS[-1]} min forecasts" in TAGLINE, TAGLINE

# The narration, clause by clause as the guide voice pauses (BEATS are keyed to these).
CLAUSES = ["Macau's police already run a crowd warning system here.",
           "We believe crowd safety shouldn't cost anyone their privacy,", "or leave anyone behind.",
           "So we propose movable phones that send only numbers,", "and forecasts that say how sure they are."]
assert " ".join(CLAUSES) == NARRATION, "narration changed: re-measure the guide voice and re-key BEATS"

# ---------------------------------------------------------------- zone model

ZONES = zone_graph()["zones"]
EDGES = zone_graph()["edges"]
SENSORS = zone_graph()["sensors"]


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
assert any(s["zone_id"] in CORRIDOR for s in SENSORS) and any(s["zone_id"] == "tercena_corridor" for s in SENSORS)

# ---------------------------------------------------------------- timing
# Guide voice video/build/guide/S07.wav (say -v Daniel -r 155), laid at 0.2 s into the shot.
# Clause boundaries from `ffmpeg -af silencedetect=noise=-35dB:d=0.08` on the wav, plus 0.2 s:
#   0.20-3.49   "Macau's police already run a crowd warning system here."
#   3.73-7.04   "We believe crowd safety shouldn't cost anyone their privacy,"
#   7.25-8.68   "or leave anyone behind."
#   8.94-11.99  "So we propose movable phones that send only numbers,"
#   12.21-14.52 "and forecasts that say how sure they are."   (then 2.5 s without voice)
# Word times inside a clause from synthesising prefixes of the line, read off the wav's 20 ms energy
# envelope: "privacy" 6.40, "leave" 7.38, "behind" 8.18, "propose" 9.32, "movable" 9.80,
# "phones" 10.24, "send" 10.80, "only" 11.10, "numbers" 11.40, "forecasts" 12.36, "how sure" 13.46.
# re-key to the real voice take (the team speaks at about 140 wpm)
BEATS = {
    "card": 0.0,          # chapter card in (out after about 2 s)
    "panel": 0.0,         # police name + "Officially: ..." lines, held to about 6 s
    "band": 0.15,         # "Macau's police": the band sweeps Ruins -> Senado
    "policy": 2.0,        # the "2026 Policy Address" line, as the card goes (on screen only; held to about 6 s)
    "here": 3.0,          # "here": the band brightens once
    "panel_out": 5.85,    # police lines out (gone by about 6.15), during "...cost anyone their"
    "privacy": 6.35,      # "privacy": first principle chip, in the panel's place
    "behind": 7.35,       # "leave anyone behind": second principle chip
    "propose": 8.94,      # "So we propose": the band quietens
    "chips_out": 9.45,    # principle chips out (gone by about 9.75), before the server comes in
    "tag": 9.8,           # "movable phones": "What we propose" line, "movable phones"
    "phones": 10.2,       # "phones": the phones drop (all down by about 11.25)
    "server": 10.4,       # the server comes in
    "packets": 10.8,      # "send": number packets flow (first wave; more waves follow)
    "numbers": 11.1,      # "only numbers": "numbers only" on the line
    "forecasts": 12.35,   # "forecasts": +5 / +10 / +15 min chips, zone by zone, and the line item
    "confidence": 13.45,  # "how sure": a confidence dot in every chip
    "approves": 14.6,     # end of speech: "a person approves" (reads for 2.4 s to the end)
}
CARD_HOLD = 2.0
PACKET_WAVES = [BEATS["packets"], 12.4, 13.9, 15.4]   # numbers keep flowing while the shot holds
PANEL_FADE = 0.3

# ---------------------------------------------------------------- layout and colours

GRAPH_BOX = (600, 190, 1100, 800)
PROJ = project(GRAPH_BOX)
ZPOS = {z["id"]: PROJ(z["lat"], z["lon"]) for z in ZONES}
R = 26
BAND_HW = 64                                        # half-width of the police band (px)
BAND = tuple(int(c) for c in lerp(BLUE, INK, 0.30))
CHIP_FILL = tuple(int(c) for c in lerp(NAVY_2, CYAN, 0.28))
SERVER = (330, 520)
TAG_Y = 852                                         # "What we propose" line (caption band starts at y 926)
TAG_SIZE = 32

PANEL_X0, PANEL_X1, PANEL_Y0 = 60, 820, 150         # police panel (screen-fixed)
PANEL_PAD = 26
PRINCIPLE_H, PRINCIPLE_GAP, PRINCIPLE_SIZE = 84, 16, 36   # principle chips, stacked in the panel's place
GRAPH_TAG = "zone model · schematic"

SHORT = {"tercena_corridor": "Rua da Tercena", "rua_sao_paulo": "Rua de S. Paulo", "almeida_ribeiro": "Av. de Almeida Ribeiro"}
LABEL_DY = {"tercena_corridor": -9}                 # lift this tag clear of St. Dominic's circle below it
LABEL_SIZE = 22
CHIP_GAP = 8


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


@lru_cache(maxsize=None)
def glow_spr(colour, r: int, blur: int) -> Image.Image:
    size = 2 * (r + 3 * blur)
    im = Image.new("RGBA", (size, size), (*colour, 0))
    a = Image.new("L", (size, size), 0)
    ImageDraw.Draw(a).ellipse((size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r), fill=255)
    im.putalpha(a.filter(ImageFilter.GaussianBlur(blur)))
    return im


@lru_cache(maxsize=None)
def phone_spr() -> Image.Image:
    s = 0.42
    w, h = int(44 * s) + 4, int(80 * s) + 4
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    phone_icon(ImageDraw.Draw(im), w * SS / 2, h * SS / 2, s * SS, fill=INK, screen=tuple(int(c) for c in lerp(NAVY_3, CYAN, 0.45)))
    return _down(im, w, h)


@lru_cache(maxsize=None)
def server_spr() -> Image.Image:
    s = 1.15
    w, h = int(110 * s), int(100 * s)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    server_icon(ImageDraw.Draw(im), w * SS / 2, h * SS / 2 + 4 * SS, s * SS, fill=INK_2)
    return _down(im, w, h)


@lru_cache(maxsize=None)
def pill_spr(text: str, size: int, fill, text_fill, outline=None, h: int = 30, pad: int = 12, extra: int = 0) -> Image.Image:
    """A pill with its text; `extra` px of room at the right (for the confidence dot)."""
    tw = text_w(text, size, 700)
    w = int(tw + 2 * pad + extra)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((SS, SS, w * SS - SS, h * SS - SS), (h * SS) // 2 - SS, fill=(*fill, 255),
                        outline=(*outline, 255) if outline else None, width=2 * SS)
    im = _down(im, w, h)
    spr, dx, dy = text_spr(text, size, 700, text_fill)
    x = pad - 2 if extra else (w - spr.width) / 2           # with a dot: text left, dot at the right
    im.alpha_composite(spr, dest=(int(round(x)), int(round((h - spr.height) / 2))))
    return im


DOT_D, DOT_GAP = 10, 7


def chip_text(h_min: int) -> str:
    return f"+{h_min} min" if h_min == HORIZONS[-1] else f"+{h_min}"


def chip_spr(h_min: int) -> Image.Image:
    return pill_spr(chip_text(h_min), 20, CHIP_FILL, INK, CYAN, h=30, pad=11, extra=DOT_D + DOT_GAP)


@lru_cache(maxsize=None)
def dot_spr() -> Image.Image:
    d_ = DOT_D + 2
    im = Image.new("RGBA", (d_ * SS, d_ * SS), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((SS, SS, (d_ - 1) * SS, (d_ - 1) * SS), fill=(*INK, 255))
    return _down(im, d_, d_)


def packet_spr() -> Image.Image:
    return pill_spr("123", 20, CYAN, NAVY, None, h=30, pad=10)


# ---------------------------------------------------------------- the police band

CORRIDOR_PTS = [ZPOS[z] for z in CORRIDOR]


def _seg_dist(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    k = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1))
    return math.hypot(p[0] - ax - k * dx, p[1] - ay - k * dy)


def band_dist(p) -> float:
    """Distance from the band's centre line; a point past the band's flat end at Senado counts as
    outside the band (at least BAND_HW away)."""
    d = min(_seg_dist(p, a, b) for a, b in zip(BAND_PTS, BAND_PTS[1:]))
    (ax, ay), (bx, by) = BAND_PTS[-2], BAND_PTS[-1]
    over = ((p[0] - bx) * (bx - ax) + (p[1] - by) * (by - ay)) / math.hypot(bx - ax, by - ay)
    return max(d, BAND_HW + over) if over > 0 else d


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

# band anchor for the panel's leader line: left edge of the band beside Company of Jesus Square
_a, _b = ZPOS[CORRIDOR[0]], ZPOS[CORRIDOR[1]]
BAND_ANCHOR = (lerp(_a[0], _b[0], 0.55) - BAND_HW * 0.72, lerp(_a[1], _b[1], 0.55))

# ---------------------------------------------------------------- zone labels, chips, phones


def zone_label(z: dict) -> str:
    return f'{z["name_zh"]} {SHORT.get(z["id"], z["name"])}'


def label_box(z: dict):
    """Label tag to the right of the zone: (x0, y0, x1, y1) and the text origin."""
    x, y = ZPOS[z["id"]]
    y += LABEL_DY.get(z["id"], 0)
    tw = text_w(zone_label(z), LABEL_SIZE, 600)
    x0 = x + R + 12
    return (x0, y - 18, x0 + tw + 20, y + 18), (x0 + 10, y - 15)


def chips_origin(z: dict) -> tuple[float, float]:
    (x0, y0, x1, y1), _ = label_box(z)
    return x1 + 10, (y0 + y1) / 2


def row_box(z: dict):
    """Label tag plus its three chips."""
    (x0, y0, x1, y1), _ = label_box(z)
    cx, _ = chips_origin(z)
    return (x0, y0, cx + sum(chip_spr(h).width for h in HORIZONS) + CHIP_GAP * (len(HORIZONS) - 1), y1)


assert max(row_box(z)[2] for z in ZONES) <= 1860, "a chip row runs past the right margin"


def _rect_pts(cx, cy, hw, hh, n=4):
    return [(cx + hw * (2 * i / n - 1), cy + hh * (2 * j / n - 1)) for i in range(n + 1) for j in range(n + 1)]


def _rect_gap(r1, r2) -> float:
    dx = max(r2[0] - r1[2], r1[0] - r2[2], 0)
    dy = max(r2[1] - r1[3], r1[1] - r2[3], 0)
    return math.hypot(dx, dy) if dx or dy else -min(r1[2] - r2[0], r2[2] - r1[0], r1[3] - r2[1], r2[3] - r1[1])


PHONE_HW, PHONE_HH = 11, 18             # phone half-size plus a small margin
OWN_GAP = 90                             # a phone keeps this far (centre to centre) from other zones' phones
BAND_IN = BAND_HW - 6                    # a corridor zone's phone stays this close to the band's centre line
PHONE_DISTS = (R + 18, R + 22, R + 30)    # phone centre to zone centre


def _place_phone(s: dict, others: list[tuple[str, tuple[float, float]]]):
    """Best free spot beside the sensor's zone, given the other phones placed so far."""
    hw, hh = PHONE_HW, PHONE_HH
    rows = [row_box(z) for z in ZONES]
    zid = s["zone_id"]
    z = next(z for z in ZONES if z["id"] == zid)
    x, y = ZPOS[zid]
    bearing = math.degrees(math.atan2(s["lat"] - z["lat"], (s["lon"] - z["lon"]) * math.cos(math.radians(z["lat"]))))
    best = None
    for ang in range(0, 360, 10):
        for dist in PHONE_DISTS:
            cx, cy = x + dist * math.cos(math.radians(ang)), y - dist * math.sin(math.radians(ang))
            rect = (cx - hw, cy - hh, cx + hw, cy + hh)
            pts = _rect_pts(cx, cy, hw, hh)
            clear = min(_seg_dist(pt, ZPOS[e["from"]], ZPOS[e["to"]]) for pt in pts for e in EDGES) - 4
            clear = min(clear, min(math.hypot(pt[0] - zx, pt[1] - zy) for pt in pts for zx, zy in ZPOS.values()) - R)
            clear = min([clear] + [_rect_gap(rect, rb) for rb in rows]
                        + [_rect_gap(rect, (ox - hw, oy - hh, ox + hw, oy + hh)) for _, (ox, oy) in others])
            clear = min(clear, cy - hh - 130, TAG_Y - 10 - (cy + hh))
            db = max(band_dist(pt) for pt in pts) if zid in CORRIDOR else min(band_dist(pt) for pt in pts)
            band_pen = max(0.0, db - BAND_IN) if zid in CORRIDOR else max(0.0, BAND_HW + 6 - db)
            # a phone must read as its own zone's: keep it away from other zones' phones
            own_pen = sum(max(0.0, OWN_GAP - math.hypot(cx - ox, cy - oy)) for oz, (ox, oy) in others if oz != zid)
            to_server = math.degrees(math.atan2(-(SERVER[1] - y), SERVER[0] - x))
            diff = abs((ang - bearing + 180) % 360 - 180)
            diff_s = abs((ang - to_server + 180) % 360 - 180)
            score = (min(clear, 14) - 10.0 * max(0.0, 3 - clear)        # never on a street, disc, tag or phone
                     - 2.0 * band_pen - 0.5 * own_pen
                     - 0.03 * diff_s - 0.01 * diff - 0.05 * (dist - R - 22))
            if best is None or score > best[0]:
                best = (score, (cx, cy))
    return best[1]


def phone_positions() -> list[tuple[str, tuple[float, float]]]:
    """One phone per sensor in shared/zones.json, beside its zone: a free spot (clear of streets,
    zones, labels and other phones, and well away from other zones' phones), inside the band for
    corridor zones and outside it elsewhere, preferring the side facing the server, then the
    sensor's real bearing from the zone centre. A first pass places them in order; a second pass
    re-places each one knowing where all the others are."""
    out: list[tuple[str, tuple[float, float]]] = []
    for s in SENSORS:
        out.append((s["zone_id"], _place_phone(s, out)))
    for _ in range(2):
        for i, s in enumerate(SENSORS):
            out[i] = (s["zone_id"], _place_phone(s, out[:i] + out[i + 1:]))
    return out


PHONES = phone_positions()
ZONES_TB = sorted(ZONES, key=lambda z: ZPOS[z["id"]][1])   # chips arrive top to bottom
SERVER_EDGE = SERVER[0] + 58                             # right edge of the server icon (style.server_icon, s 1.15)
# packets end a little short of the server (a pill never sits on the icon) and fade out on the way in
SERVER_IN = (SERVER_EDGE + 8 + packet_spr().width / 2, SERVER[1] - 6)
PACKET_DUR, PACKET_FADE_AT, PACKET_FADE = 0.75, 0.45, 0.22
SERVER_FAN = 32                                          # packet ends spread over +-32 px of the racks


def bez(p0, c, p1, k):
    return ((1 - k) ** 2 * p0[0] + 2 * (1 - k) * k * c[0] + k ** 2 * p1[0],
            (1 - k) ** 2 * p0[1] + 2 * (1 - k) * k * c[1] + k ** 2 * p1[1])


_PY0, _PY1 = min(y for _, (_, y) in PHONES), max(y for _, (_, y) in PHONES)


def packet_path(p0):
    """Leaves the phone heading left (away from the zone graph), then bends into the server. The ends
    fan out over the server's racks in the phones' top-to-bottom order, so packets never pile up."""
    p1 = (SERVER_IN[0], SERVER_IN[1] + lerp(-SERVER_FAN, SERVER_FAN, (p0[1] - _PY0) / (_PY1 - _PY0)))
    c = (lerp(p0[0], p1[0], 0.55), lerp(p0[1], p1[1], 0.2) - 30)
    return p0, c, p1


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


@lru_cache(maxsize=1)
def labels_layer():
    lay = transparent()
    for z in ZONES:                      # label tags (navy backing so street lines never run through text)
        box, org = label_box(z)
        rounded(lay, box, 10, fill=NAVY_2, alpha=0.94)
        put_text(lay, org[0], org[1], zone_label(z), LABEL_SIZE, 600, INK)
    return _crop(lay)


@lru_cache(maxsize=1)
def server_layer():
    lay = transparent()
    paste(lay, server_spr(), SERVER[0], SERVER[1], anchor="mm")
    put_text(lay, SERVER[0], SERVER[1] + 64, "server", 22, 600, INK_2, align="m")
    return _crop(lay)


def name_lines() -> list[str]:
    head, rest = POLICE_NAME.split(" (", 1)
    return [head, "(" + rest]


def status_lines() -> list[str]:
    parts = POLICE_STATUS.split("; ")
    return [p + (";" if i < len(parts) - 1 else "") for i, p in enumerate(parts)]


NAME_SIZE, STATUS_SIZE, POLICY_SIZE = 30, 27, 30


@lru_cache(maxsize=1)
def panel_spr():
    """The police panel: system name, then the "Officially: ..." lines; a band-coloured bar at left."""
    names, stats = name_lines(), status_lines()
    w = PANEL_X1 - PANEL_X0
    tx = PANEL_PAD + 10
    assert all(text_w(l, NAME_SIZE, 700) <= w - tx - PANEL_PAD for l in names), names
    assert all(text_w(l, STATUS_SIZE, 500) <= w - tx - PANEL_PAD for l in stats), stats
    h = PANEL_PAD + len(names) * 42 + 14 + len(stats) * 36 + PANEL_PAD - 6
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rounded(lay, (0, 0, w - 1, h - 1), 16, fill=NAVY_2, alpha=0.94)
    rounded(lay, (0, 0, 7, h - 1), 3, fill=BAND)
    y = PANEL_PAD - 4
    for l in names:
        put_text(lay, tx, y, l, NAME_SIZE, 700, INK)
        y += 42
    y += 14
    for i, l in enumerate(stats):
        if i == 0 and l.startswith("Officially:"):
            put_text(lay, tx, y, "Officially:", STATUS_SIZE, 700, INK)
            put_text(lay, tx + text_w("Officially: ", STATUS_SIZE, 700), y, l[len("Officially: "):], STATUS_SIZE, 500, INK)
        else:
            put_text(lay, tx, y, l, STATUS_SIZE, 500, INK)
        y += 36
    return lay


@lru_cache(maxsize=1)
def policy_spr():
    w = int(text_w(POLICY, POLICY_SIZE, 700) + 2 * PANEL_PAD + 10)
    h = 66
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rounded(lay, (0, 0, w - 1, h - 1), 16, fill=NAVY_2, alpha=0.94)
    rounded(lay, (0, 0, 7, h - 1), 3, fill=BAND)
    put_text(lay, PANEL_PAD + 10, 17, POLICY, POLICY_SIZE, 700, INK)
    return lay


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


@lru_cache(maxsize=None)
def principle_spr(i: int) -> Image.Image:
    """Principle chip i: icon + label on the panel's navy, with a CrowdPulse-cyan bar at left."""
    label = PRINCIPLES[i]
    icon_w = 64
    tx = PANEL_PAD + 10 + icon_w + 16
    w, h = int(tx + text_w(label, PRINCIPLE_SIZE, 700) + PANEL_PAD + 4), PRINCIPLE_H
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rounded(lay, (0, 0, w - 1, h - 1), 16, fill=NAVY_2, alpha=0.94)
    rounded(lay, (0, 0, 7, h - 1), 3, fill=CYAN)
    big = Image.new("RGBA", (icon_w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    c = (icon_w * SS / 2, h * SS / 2)
    if i == 0:
        no_image_icon(d, c[0], c[1], SS)
    else:                                   # style.wheelchair_icon is drawn about (-4, -3) off its centre
        wheelchair_icon(d, c[0] + 4 * 1.25 * SS, c[1] + 3 * 1.25 * SS, 1.25 * SS, colour=(*INK, 255), width=4)
    lay.alpha_composite(_down(big, icon_w, h), dest=(PANEL_PAD + 10, 0))
    l, t_, r, b = text_font(label, PRINCIPLE_SIZE, 700).getbbox(label, anchor="la")
    put_text(lay, tx, h / 2 - (t_ + b) / 2, label, PRINCIPLE_SIZE, 700, INK)
    return lay


PRINCIPLE_W = max(principle_spr(i).width for i in range(2))
assert PANEL_X0 + PRINCIPLE_W <= GRAPH_BOX[0] - 40, "a principle chip runs into the zone graph"


# ---------------------------------------------------------------- drawing

def band_alpha(t: float) -> float:
    base = 0.34 * progress(t, BEATS["band"], 0.5)
    here = 0.22 * math.sin(math.pi * clamp((t - BEATS["here"]) / 0.7))
    dim = 0.14 * progress(t, BEATS["propose"] + 0.4, 0.6)        # quieter while the phones work
    return clamp(base + here - dim)


def draw_band(img: Image.Image, t: float) -> None:
    k = progress(t, BEATS["band"], 0.9)
    if k <= 0:
        return
    spr = band_spr(max(1, int(round(k * 60))))
    paste(img, spr, BAND_BOX[0], BAND_BOX[1], band_alpha(t))


def draw_principles(img: Image.Image, t: float) -> None:
    """The two principle chips, stacked where the police panel was; they leave before the server comes."""
    out = 1 - progress(t, BEATS["chips_out"], PANEL_FADE)
    for i, key in enumerate(("privacy", "behind")):
        k = progress(t, BEATS[key], 0.35)
        a = k * out
        if a > 0:
            paste(img, principle_spr(i), PANEL_X0 - 24 * (1 - k), PANEL_Y0 + i * (PRINCIPLE_H + PRINCIPLE_GAP), a)


def draw_panel(img: Image.Image, t: float) -> None:
    out = 1 - progress(t, BEATS["panel_out"], PANEL_FADE)
    a = progress(t, BEATS["panel"], 0.3) * out
    if a <= 0:
        return
    spr = panel_spr()
    # leader line from the panel to the band
    ax, ay = BAND_ANCHOR
    sx, sy = PANEL_X1, PANEL_Y0 + 44
    lay = transparent()
    d = ImageDraw.Draw(lay)
    a_lead = a * progress(t, BEATS["band"] + 0.3, 0.5)
    d.line([(sx, sy), (sx + 22, sy), (ax, ay)], fill=(*BAND, int(255 * 0.9 * a_lead)), width=3, joint="curve")
    d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), fill=(*BAND, int(255 * a_lead)))
    img.alpha_composite(lay)
    paste(img, spr, PANEL_X0, PANEL_Y0, a)
    a_pol = progress(t, BEATS["policy"], 0.4) * out
    paste(img, policy_spr(), PANEL_X0, PANEL_Y0 + spr.height + 16 + (1 - a_pol) * 12, a_pol)


def phone_drop(t: float, i: int) -> float:
    return clamp((t - (BEATS["phones"] + 0.07 * i)) / 0.5)


def draw_links(img: Image.Image, t: float) -> None:
    """Thin packet links from each phone to the server; they stay, dimmed, once the first packet
    arrives. Drawn under the zone discs and label tags, so a link never runs over a zone or its text."""
    link = transparent()
    ld = ImageDraw.Draw(link)
    for i, (zid, ph) in enumerate(PHONES):
        start = PACKET_WAVES[0] + 0.06 * i
        k = progress(t, start, PACKET_DUR)
        if k <= 0:
            continue
        p0, c, p1 = packet_path(ph)
        n = max(2, int(28 * k))
        pts = [bez(p0, c, p1, k * j / n) for j in range(n + 1)]
        if k >= 1:
            pts.append((SERVER_EDGE + 2, p1[1]))            # the link itself reaches the server
        a_link = 0.34 - 0.18 * progress(t, start + PACKET_DUR, 0.5)
        ld.line(pts, fill=(*CYAN, int(255 * a_link)), width=2)
    img.alpha_composite(link)


def draw_dynamic(img: Image.Image, t: float) -> None:
    # zone rings once the chips arrive (every zone alike)
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for j, z in enumerate(ZONES_TB):
        k = progress(t, BEATS["forecasts"] + 0.07 * j, 0.3)
        if k > 0:
            x, y = ZPOS[z["id"]]
            d.ellipse((x - R - 1, y - R - 1, x + R + 1, y + R + 1), outline=(*CYAN, int(255 * k)), width=3)
    img.alpha_composite(lay)

    # server, glowing as packets arrive
    a_srv = progress(t, BEATS["server"], 0.4)
    if a_srv > 0:
        glow = 0.0
        for w0 in PACKET_WAVES:
            glow = max(glow, math.sin(math.pi * clamp((t - (w0 + 0.55)) / 0.9)))
        if glow > 0:
            paste(img, glow_spr(CYAN, 60, 22), SERVER[0], SERVER[1], 0.32 * glow, anchor="mm")
        spr, x0, y0 = server_layer()
        paste(img, spr, x0, y0, a_srv)

    # phones drop onto the zones
    for i, (zid, (x, y)) in enumerate(PHONES):
        k = phone_drop(t, i)
        if k <= 0:
            continue
        yy = y - (1 - ease_out_back(k, 1.1)) * 70
        a = clamp(k / 0.35)
        paste(img, glow_spr(INK, 10, 6), x, y + 18, 0.22 * a, anchor="mm")
        paste(img, phone_spr(), x, yy, a, anchor="mm")

    # number packets (waves)
    for w_i, w0 in enumerate(PACKET_WAVES):
        for i, (zid, ph) in enumerate(PHONES):
            start = w0 + 0.06 * i + (0.05 * ((i * 7 + w_i * 3) % 5) if w_i else 0)
            k = progress(t, start, PACKET_DUR)
            if 0 < k < 1:
                p0, c, p1 = packet_path(ph)
                k_out = progress(t, start + PACKET_FADE_AT, PACKET_FADE)     # fades and shrinks into the server
                a = min(1, (t - start) / 0.12) * (1 - k_out)
                sc = lerp(0.45, 1.0, clamp((t - start) / 0.25)) * (1 - 0.35 * k_out)
                paste(img, packet_spr(), *bez(p0, c, p1, k), a, scale=sc, anchor="mm")

    # three forecast chips per zone, then a confidence dot in each
    for j, z in enumerate(ZONES_TB):
        cx, cy = chips_origin(z)
        for h_i, h in enumerate(HORIZONS):
            spr = chip_spr(h)
            start = BEATS["forecasts"] + 0.07 * j + 0.06 * h_i
            k = clamp((t - start) / 0.32)
            if k > 0:
                paste(img, spr, cx + spr.width / 2, cy, clamp(k / 0.4), scale=lerp(0.5, 1.0, ease_out_back(k)), anchor="mm")
            kd = clamp((t - (BEATS["confidence"] + 0.06 * j + 0.04 * h_i)) / 0.3)
            if kd > 0 and k >= 1:
                paste(img, dot_spr(), cx + spr.width - 11 - DOT_D / 2 + 0.5, cy, clamp(kd / 0.4), scale=lerp(0.3, 1.0, ease_out_back(kd, 2.0)), anchor="mm")
            cx += spr.width + CHIP_GAP


def tag_pieces():
    head, rest = TAGLINE.split(": ", 1)
    items = rest.split(" · ")
    assert len(items) == 4, items
    beats = [BEATS["tag"], BEATS["numbers"], BEATS["forecasts"], BEATS["approves"]]
    pieces = [(head + ": ", 700, CYAN, beats[0])]
    for i, it in enumerate(items):
        if i:
            pieces.append((" · ", 500, INK_3, beats[i]))
        pieces.append((it, 600, INK, beats[i]))
    return pieces


TAG_PIECES = tag_pieces()
TAG_W = sum(text_w(s, TAG_SIZE, w_) for s, w_, _, _ in TAG_PIECES)
assert TAG_W <= 1800, TAG_W


def draw_tagline(img: Image.Image, t: float) -> None:
    x = W / 2 - TAG_W / 2
    for s, w_, col, b in TAG_PIECES:
        a = progress(t, b, 0.4)
        put_text(img, x, TAG_Y + (1 - a) * 10, s, TAG_SIZE, w_, col, a)
        x += text_w(s, TAG_SIZE, w_)


# ---------------------------------------------------------------- frame

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    draw_band(img, t)
    paste(img, *streets_layer())
    draw_links(img, t)
    paste(img, *discs_layer())
    paste(img, *labels_layer())
    put_text(img, 1860, 128, GRAPH_TAG, 22, 500, INK_3, align="r")
    draw_dynamic(img, t)
    draw_panel(img, t)
    draw_principles(img, t)
    draw_tagline(img, t)

    # fixed slots
    chapter_card(img, CARD, fade(t, BEATS["card"] - 0.3, BEATS["card"] + CARD_HOLD + 0.3, 0.3))
    footer(img, FOOTER)
    return img


STILLS = {  # beat name -> time (s) for the layout stills
    "band": 1.6,
    "here": 3.35,
    "panel_out": 6.0,
    "privacy": 6.9,
    "principles": 8.5,
    "propose": 9.6,
    "phones": 10.6,
    "flow": 11.6,
    "chips": 13.0,
    "confidence": 14.0,
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
