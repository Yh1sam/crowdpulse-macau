"""Shot S07, "What is new?" (0:58.0-1:11.0, 13.0 s), [MEMBER 5] voice-over. Motion graphic.

Credits Macau's 2019 attraction forecasts (hours to days ahead) and claims only the gap: the next
5-15 minutes, street by street, from phones staff place temporarily.

0-6 s   a log-scale "how far ahead" axis; the grey ticks 4 h · 24 h · 7 days light up above a row of
        20 attraction pins; the "Announced 2019 ..." line; the gov.mo footer.
6-13 s  the camera dives into the first sliver of the axis (5-15 min), which becomes the
        +5 · +10 · +15 min axis over the 7-zone graph; phones drop onto the zones, number packets
        flow to a server, each zone gets three small forecast chips; the CrowdPulse line builds up.

Data sources (no number below is retyped):
- docs/video/shotlist.json, S07: the duration (end_s - start_s) and every on-screen line, verbatim
  (chapter card, the "Announced 2019 ..." line, the gov.mo footer, the CrowdPulse line).
- docs/proposal.md, source table: 20 attractions forecast 4 h, 24 h and 7 days ahead, Macao SAR
  government news of 30 April 2019 (gov.mo/en/?p=111714); checked against the on-screen line.
- shared/config.json: forecast_horizons_min (the +5 / +10 / +15 axis and chips).
- shared/zones.json: the 7 zones and 7 street links (style.draw_zone_graph) and the sensor list
  (one phone icon per listed sensor, at its zone).
- docs/deployment.md, "Operational model" (staff place phones temporarily): cited in the footer.

Output: video/build/mg/S07.mp4 and video/build/mg/stills/S07_<beat>.png.
Run:    .venv/bin/python video/mg/S07.py                         full render + stills
        .venv/bin/python video/mg/S07.py --preview 5.5 12.9 --out DIR   single frames for checks
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S07"

# ---------------------------------------------------------------- data (read, never retyped)

_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = _shot["end_s"] - _shot["start_s"]  # 13.0 s

_ost = [p.strip() for p in _shot["on_screen_text"].split(" | ")]
CARD = _ost[0].split(":", 1)[1].strip()               # What is new?
ANNOUNCE = _ost[1]                                    # Announced 2019: 20 attractions, ... Not confirmed.
FOOTER_2019 = _ost[2].split(":", 1)[1].strip()        # Macao SAR Government news, 30 Apr 2019, gov.mo/...
TAGLINE = _ost[3]                                     # CrowdPulse: next 5-15 min · street by street · ...

_proposal = (ROOT / "docs" / "proposal.md").read_text()
_m = re.search(r"forecasts (\d+) attractions (\d+) h, (\d+) h and (\d+) days ahead", _proposal)
N_ATTRACTIONS, H_A, H_B, D_C = map(int, _m.groups())
_url = re.search(r"https?://www\.(gov\.mo/en/\?p=\d+)", _proposal).group(1)
assert f"{N_ATTRACTIONS} attractions, {H_A} h / {H_B} h / {D_C} days ahead" in ANNOUNCE, ANNOUNCE
assert _url in FOOTER_2019, FOOTER_2019

HORIZONS = json.loads((ROOT / "shared" / "config.json").read_text())["forecast_horizons_min"]  # [5, 10, 15]
assert f"next {HORIZONS[0]}-{HORIZONS[-1]} min" in TAGLINE, TAGLINE

ZONES = zone_graph()["zones"]
EDGES = zone_graph()["edges"]
SENSORS = zone_graph()["sensors"]

# the existing system's ticks (minutes ahead, label)
TICKS_2019 = [(H_A * 60, f"{H_A} h"), (H_B * 60, f"{H_B} h"), (D_C * 24 * 60, f"{D_C} days")]

FOOTER_DESIGN = (f"Prototype design · horizons: shared/config.json · {len(ZONES)} zones, {len(EDGES)} streets: "
                 f"shared/zones.json · phones: docs/deployment.md")

# ---------------------------------------------------------------- timing
# Seconds from the shot start, keyed to the narration at about 140 words per minute:
# "In twenty nineteen, Macau's tourism office announced attraction forecasts, hours to days ahead.
#  We forecast the next five to fifteen minutes, street by street, from phones staff place temporarily."
# re-key to the real voice take
BEATS = {
    "card": 0.0,        # chapter card in (out after CARD_HOLD)
    "axis": 0.15,       # "In twenty nineteen": the log axis draws in
    "pins": 1.3,        # "Macau's tourism office": the 20 attraction pins drop in
    "announced": 2.6,   # "announced": the "Announced 2019 ..." line
    "hours": 3.95,      # "hours": the 4 h tick lights up
    "to": 4.4,          # "to": the 24 h tick
    "days": 4.8,        # "days": the 7 days tick
    "sliver": 5.35,     # "ahead" (pause): the 5-15 min sliver glows
    "dive": 5.9,        # "We forecast the next": camera dives into the sliver
    "five": 7.6,        # "five": +5 label
    "ten": 8.0,         # "to": +10 label
    "fifteen": 8.45,    # "fifteen": +15 min label
    "tag_next": 8.9,    # "minutes": CrowdPulse line, "next 5-15 min"
    "street": 9.35,     # "street by street": streets pulse one by one; "street by street"
    "phones": 10.6,     # "from phones": phones drop onto the zones (land on "phones" ~11.0)
    "packets": 11.1,    # "staff place": number packets flow to the server
    "privacy": 11.55,   # "privacy by design" + shield on the server
    "chips": 11.75,     # "place temporarily": three forecast chips per zone (all in by ~12.5)
}
CARD_HOLD = 2.0         # chapter card visible about 2 s
DIVE = 1.4              # length of the camera dive

# ---------------------------------------------------------------- layout and colours

EXIST = lerp(BLUE, INK, 0.35)          # the existing (2019) system
EXIST = tuple(int(c) for c in EXIST)
CHIP_FILL = tuple(int(c) for c in lerp(NAVY_2, CYAN, 0.28))

# part 1: log axis 1 min .. 14 days
AX_Y, AX_X0, AX_X1 = 370, 160, 1760
AX_MIN, AX_MAX = 1, 14 * 24 * 60
PIN_TIP_Y = 612
ANNOUNCE_Y = 690

# part 2: linear +5 / +10 / +15 axis and the zone graph
AX2_Y = 205
AX2_X = (400, 1480)                    # screen x of the first and last horizon after the dive
GRAPH_BOX = (590, 300, 1070, 790)
SERVER = (330, 520)
TAG_Y = 842


def ax_x(minutes: float) -> float:
    return AX_X0 + (math.log10(minutes) - math.log10(AX_MIN)) / (math.log10(AX_MAX) - math.log10(AX_MIN)) * (AX_X1 - AX_X0)


F = (ax_x(math.sqrt(HORIZONS[0] * HORIZONS[-1])), AX_Y)   # dive focus: the middle of the sliver (log scale)
T = (W / 2, AX2_Y)                                        # where that point lands
Z = (AX2_X[1] - AX2_X[0]) / (ax_x(HORIZONS[-1]) - ax_x(HORIZONS[0]))   # final zoom (~6.8x)


def ease_out(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_out_back(t: float, k: float = 1.25) -> float:
    t = clamp(t)
    return 1 + (k + 1) * (t - 1) ** 3 + k * (t - 1) ** 2


def p_out(t: float, start: float, dur: float) -> float:
    return ease_out((t - start) / dur)


# ---------------------------------------------------------------- sprites (supersampled, cached)

SS = 4


def _down(im: Image.Image, w: int, h: int) -> Image.Image:
    return im.resize((w, h), Image.Resampling.LANCZOS)


@lru_cache(maxsize=None)
def text_spr(text: str, size: int, weight: int = 400, fill=INK, stroke: int = 0, stroke_fill=NAVY):
    """Text sprite cropped to its ink box; returns (sprite, dx, dy) where (dx, dy) is the box's
    offset from the 'la' origin used by style.draw_text."""
    f = text_font(text, size, weight)
    l, t, r, b = f.getbbox(text, anchor="la", stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=f, fill=(*fill[:3], 255), anchor="la",
                            stroke_width=stroke, stroke_fill=(*stroke_fill[:3], 255))
    return im, l - 2, t - 2


def text_w(text: str, size: int, weight: int = 400) -> float:
    return text_font(text, size, weight).getlength(text)


def paste(img: Image.Image, spr: Image.Image, x: float, y: float, alpha: float = 1.0, scale: float = 1.0,
          anchor: str = "lt") -> None:
    """Composites a sprite with opacity and scale; anchor = horizontal (l/m/r) + vertical (t/m/b)."""
    if alpha <= 0.004 or scale <= 0.01:
        return
    if abs(scale - 1.0) > 1e-3:
        spr = spr.resize((max(1, round(spr.width * scale)), max(1, round(spr.height * scale))), Image.Resampling.BICUBIC)
    if alpha < 0.999:
        spr = spr.copy()
        a = spr.getchannel("A").point(lambda v: int(v * alpha))
        spr.putalpha(a)
    ox = x - (spr.width / 2 if anchor[0] == "m" else spr.width if anchor[0] == "r" else 0)
    oy = y - (spr.height / 2 if anchor[1] == "m" else spr.height if anchor[1] == "b" else 0)
    ox, oy = int(round(ox)), int(round(oy))
    sx0, sy0 = max(0, -ox), max(0, -oy)
    sx1, sy1 = min(spr.width, W - ox), min(spr.height, H - oy)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    img.alpha_composite(spr, dest=(ox + sx0, oy + sy0), source=(sx0, sy0, sx1, sy1))


def put_text(img: Image.Image, x: float, y: float, text: str, size: int, weight: int = 400, fill=INK,
             alpha: float = 1.0, align: str = "l", stroke: int = 0, scale: float = 1.0) -> None:
    """Text at the 'la'-style origin (x = left / centre / right edge by align, y = ascender line)."""
    spr, dx, dy = text_spr(text, size, weight, tuple(fill[:3]), stroke)
    adv = text_w(text, size, weight)
    x0 = x - (adv / 2 if align == "m" else adv if align == "r" else 0)
    paste(img, spr, x0 + dx * scale, y + dy * scale, alpha, scale)


@lru_cache(maxsize=None)
def pin_spr(colour) -> Image.Image:
    w, h = 28, 40
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = SS
    d.ellipse((2 * s, 1 * s, 26 * s, 25 * s), fill=(*colour, 255))
    d.polygon([(4.2 * s, 18 * s), (23.8 * s, 18 * s), (14 * s, 39 * s)], fill=(*colour, 255))
    d.ellipse((9 * s, 8 * s, 19 * s, 18 * s), fill=(*NAVY, 255))
    return _down(im, w, h)


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
def shield_spr() -> Image.Image:
    s = 0.42
    w, h = 40, 46
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    shield_icon(d, w * SS / 2, h * SS / 2, s * SS * 1.05, fill=CYAN)
    # a check mark inside
    c = w * SS / 2
    d.line([(c - 8 * SS, h * SS / 2), (c - 2 * SS, h * SS / 2 + 6 * SS), (c + 9 * SS, h * SS / 2 - 7 * SS)], fill=(*NAVY, 255), width=3 * SS)
    return _down(im, w, h)


@lru_cache(maxsize=None)
def pill_spr(text: str, size: int, fill, text_fill, outline=None, h: int = 30, pad: int = 12) -> Image.Image:
    tw = text_w(text, size, 700)
    w = int(tw + 2 * pad)
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((SS, SS, w * SS - SS, h * SS - SS), (h * SS) // 2 - SS, fill=(*fill, 255),
                        outline=(*outline, 255) if outline else None, width=2 * SS)
    im = _down(im, w, h)
    spr, dx, dy = text_spr(text, size, 700, text_fill)
    # centre the ink box
    im.alpha_composite(spr, dest=(int(round((w - spr.width) / 2)), int(round((h - spr.height) / 2))))
    return im


def chip_spr(h_min: int) -> Image.Image:
    return pill_spr(f"+{h_min}", 20, CHIP_FILL, INK, CYAN, h=30, pad=11)


def packet_spr() -> Image.Image:
    return pill_spr("123", 20, CYAN, NAVY, None, h=30, pad=10)


# ---------------------------------------------------------------- part 1: the 2019 forecasts

PIN_X0, PIN_X1 = ax_x(TICKS_2019[0][0]) - 40, ax_x(TICKS_2019[-1][0]) + 50
PIN_XS = [PIN_X0 + i * (PIN_X1 - PIN_X0) / (N_ATTRACTIONS - 1) for i in range(N_ATTRACTIONS)]
TICK_BEATS = [BEATS["hours"], BEATS["to"], BEATS["days"]]


def tick_lit(t: float, i: int) -> float:
    return progress(t, TICK_BEATS[i], 0.45)


def draw_part1(t: float) -> Image.Image:
    """Everything of the first half except the axis line and the sliver (drawn with the camera)."""
    L = transparent()
    a_axis = progress(t, BEATS["axis"], 0.6)
    # axis title and orientation labels (grey, below the line)
    put_text(L, AX_X0, AX_Y - 92, "how far ahead · log scale", 22, 500, INK_3, a_axis)
    d = ImageDraw.Draw(L)
    for m, lab in [(AX_MIN, "1 min"), (60, "1 h")]:
        x = ax_x(m)
        d.line([(x, AX_Y + 2), (x, AX_Y + 12)], fill=(*INK_3, int(255 * a_axis)), width=3)
        put_text(L, x, AX_Y + 22, lab, 22, 500, INK_3, a_axis, align="l" if m == AX_MIN else "m")

    # band linking the lit ticks to the row of pins
    k_band = progress(t, BEATS["hours"], BEATS["days"] + 0.45 - BEATS["hours"])
    if k_band > 0:
        band = transparent()
        bd = ImageDraw.Draw(band)
        xa = ax_x(TICKS_2019[0][0])
        xb = lerp(xa, ax_x(TICKS_2019[-1][0]), k_band)
        top, bot = AX_Y + 16, PIN_TIP_Y - 52
        pa = lerp(PIN_X0 - 18, PIN_X1 + 18, 0.0)
        pb = lerp(PIN_X0 - 18, PIN_X1 + 18, k_band)
        bd.polygon([(xa, top), (xb, top), (pb, bot), (pa, bot)], fill=(*EXIST, int(255 * 0.11 * min(1, k_band * 3))))
        L.alpha_composite(band)

    # the 20 attraction pins
    for i, x in enumerate(PIN_XS):
        k = p_out(t, BEATS["pins"] + i * 0.045, 0.45)
        if k <= 0:
            continue
        lit = progress(t, BEATS["hours"] + 0.1 + i * 0.03, 0.35)
        y = PIN_TIP_Y - 40 - (1 - k) * 36
        paste(L, pin_spr(INK_3), x, y, k * (1 - lit), anchor="mt")
        paste(L, pin_spr(EXIST), x, y, k * lit, anchor="mt")
    a_pins = progress(t, BEATS["pins"] + 0.3, 0.5)
    put_text(L, (PIN_X0 + PIN_X1) / 2, PIN_TIP_Y + 18, f"{N_ATTRACTIONS} attractions", 22, 600, INK_2, a_pins, align="m")

    # the 4 h / 24 h / 7 days ticks: grey, then lit
    for i, (m, lab) in enumerate(TICKS_2019):
        x = ax_x(m)
        lit = tick_lit(t, i)
        a = a_axis
        col = tuple(int(c) for c in lerp(INK_3, EXIST, lit))
        if lit > 0:
            paste(L, glow_spr(EXIST, 14, 9), x, AX_Y, 0.85 * lit, scale=1.0 + 0.25 * math.sin(math.pi * lit), anchor="mm")
        d = ImageDraw.Draw(L)
        d.line([(x, AX_Y - 16), (x, AX_Y + 16)], fill=(*col, int(255 * a)), width=4)
        d.ellipse((x - 7, AX_Y - 7, x + 7, AX_Y + 7), fill=(*col, int(255 * a)))
        put_text(L, x, AX_Y - 62, lab, 34, 700, tuple(int(c) for c in lerp(INK_3, INK, lit)), a, align="m")

    # "Announced 2019: ... · still running today? Not confirmed."
    a_ann = progress(t, BEATS["announced"], 0.5)
    if a_ann > 0:
        main, rest = ANNOUNCE.split(" · ", 1)
        q, nc = rest.rsplit("? ", 1)
        parts = [(main, 600, INK), (" · ", 500, INK_3), (q + "? ", 500, INK_2), (nc, 700, INK)]
        total = sum(text_w(s, 30, w_) for s, w_, _ in parts)
        x = W / 2 - total / 2
        dy = (1 - a_ann) * 14
        for s, w_, col in parts:
            put_text(L, x, ANNOUNCE_Y + dy, s, 30, w_, col, a_ann)
            x += text_w(s, 30, w_)
    return L


@lru_cache(maxsize=1)
def part1_frozen() -> Image.Image:
    return draw_part1(BEATS["dive"])


# ---------------------------------------------------------------- the camera

def camera(t: float):
    """Returns (p, zoom, (tx, ty)): a world point P (first-half coordinates) lands at
    (tx, ty) + (P - F) * zoom."""
    p = progress(t, BEATS["dive"], DIVE)
    z = Z ** p
    return p, z, (lerp(F[0], T[0], p), lerp(F[1], T[1], p))


def to_screen(x: float, y: float, cam) -> tuple[float, float]:
    _, z, (tx, ty) = cam
    return tx + (x - F[0]) * z, ty + (y - F[1]) * z


def zoomed(layer: Image.Image, scale: float, src_pt, dst_pt) -> Image.Image:
    """Layer scaled by `scale` so that its point src_pt lands at dst_pt."""
    a = 1 / scale
    return layer.transform((W, H), Image.Transform.AFFINE,
                           (a, 0, src_pt[0] - dst_pt[0] * a, 0, a, src_pt[1] - dst_pt[1] * a),
                           resample=Image.Resampling.BILINEAR, fillcolor=(0, 0, 0, 0))


def soft_line(img: Image.Image, a, b, colour, width: int, blur: int, alpha: float) -> None:
    """A blurred glow line, drawn on a cropped layer."""
    if alpha <= 0:
        return
    m = width + 3 * blur
    x0, y0 = int(min(a[0], b[0]) - m), int(min(a[1], b[1]) - m)
    x1, y1 = int(max(a[0], b[0]) + m), int(max(a[1], b[1]) + m)
    lay = Image.new("RGBA", (x1 - x0, y1 - y0), (*colour, 0))
    msk = Image.new("L", lay.size, 0)
    ImageDraw.Draw(msk).line([(a[0] - x0, a[1] - y0), (b[0] - x0, b[1] - y0)], fill=int(255 * alpha), width=width)
    lay.putalpha(msk.filter(ImageFilter.GaussianBlur(blur)))
    paste(img, lay, x0, y0)


def horizon_world_x(h: float, morph: float) -> float:
    """World x of a horizon tick: log position on the 2019 axis, morphing to an even spacing."""
    h0, h1 = HORIZONS[0], HORIZONS[-1]
    x_log = ax_x(h)
    x_lin = ax_x(h0) + (h - h0) / (h1 - h0) * (ax_x(h1) - ax_x(h0))
    return lerp(x_log, x_lin, morph)


def draw_axis(img: Image.Image, t: float, cam) -> list[float]:
    """The axis line and the 5-15 min sliver through the camera; returns the horizon tick xs."""
    p = cam[0]
    layer = transparent()
    d = ImageDraw.Draw(layer)
    a_axis = progress(t, BEATS["axis"], 0.6)
    k_draw = progress(t, BEATS["axis"], 0.9)
    grey_a = a_axis * (1 - progress(p, 0.35, 0.6))
    x0, y0 = to_screen(AX_X0, AX_Y, cam)
    x1, _ = to_screen(lerp(AX_X0, AX_X1, k_draw), AX_Y, cam)
    if x1 > x0:
        d.line([(max(-20, x0), y0), (min(W + 20, x1), y0)], fill=(*INK_3, int(255 * grey_a)), width=4)
        xe = x1
        if xe < W + 20:  # arrowhead at the far end
            d.polygon([(xe + 14, y0), (xe - 2, y0 - 9), (xe - 2, y0 + 9)], fill=(*INK_3, int(255 * grey_a)))

    a_s = progress(t, BEATS["sliver"], 0.45)
    morph = progress(t, BEATS["dive"] + 0.45 * DIVE, 0.55 * DIVE)
    xs = [to_screen(horizon_world_x(h, morph), AX_Y, cam)[0] for h in HORIZONS]
    if a_s > 0:
        xa, xb = xs[0], xs[-1]
        img.alpha_composite(layer)
        soft_line(img, (xa, y0), (xb, y0), CYAN, 12, 10, 0.55 * a_s)
        layer = transparent()
        d = ImageDraw.Draw(layer)
        d.line([(xa, y0), (xb, y0)], fill=(*CYAN, int(255 * a_s)), width=int(lerp(6, 7, p)))
        th = lerp(9, 16, p)
        for x in xs:
            d.line([(x, y0 - th), (x, y0 + th)], fill=(*CYAN, int(255 * a_s)), width=int(lerp(3, 4, p)))
            r = lerp(4, 8, p)
            d.ellipse((x - r, y0 - r, x + r, y0 + r), fill=(*CYAN, int(255 * a_s)))
    img.alpha_composite(layer)
    return xs


# ---------------------------------------------------------------- part 2: the street-level picture

PROJ = project(GRAPH_BOX)
ZPOS = {z["id"]: PROJ(z["lat"], z["lon"]) for z in ZONES}
R = 26
SHORT = {"tercena_corridor": "Rua da Tercena", "rua_sao_paulo": "Rua de S. Paulo", "almeida_ribeiro": "Av. de Almeida Ribeiro"}
LABEL_DY = {"tercena_corridor": -9}     # lift this tag clear of St. Dominic's circle just below it
LABEL_SIZE = 22
CHIP_GAP = 8


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


def _seg_dist(p, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    k = clamp(((p[0] - ax) * dx + (p[1] - ay) * dy) / (dx * dx + dy * dy or 1))
    return math.hypot(p[0] - ax - k * dx, p[1] - ay - k * dy)


def _rect_pts(cx, cy, hw, hh, n=4):
    return [(cx + hw * (2 * i / n - 1), cy + hh * (2 * j / n - 1)) for i in range(n + 1) for j in range(n + 1)]


def _rect_gap(r1, r2) -> float:
    dx = max(r2[0] - r1[2], r1[0] - r2[2], 0)
    dy = max(r2[1] - r1[3], r1[1] - r2[3], 0)
    return math.hypot(dx, dy) if dx or dy else -min(r1[2] - r2[0], r2[2] - r1[0], r1[3] - r2[1], r2[3] - r1[1])


def phone_positions() -> list[tuple[str, tuple[float, float]]]:
    """One phone per sensor in shared/zones.json, beside its zone: a free spot (clear of streets,
    zones, labels and other phones), preferring the side facing the server, then the sensor's real
    bearing from the zone centre."""
    hw, hh = 11, 18                      # phone half-size plus a small margin
    rows = [row_box(z) for z in ZONES]
    placed: list[tuple[float, float, float, float]] = []
    out = []
    for s in SENSORS:
        zid = s["zone_id"]
        z = next(z for z in ZONES if z["id"] == zid)
        x, y = ZPOS[zid]
        bearing = math.degrees(math.atan2(s["lat"] - z["lat"], (s["lon"] - z["lon"]) * math.cos(math.radians(z["lat"]))))
        best = None
        for ang in range(0, 360, 10):
            for dist in (R + 24, R + 32):
                cx, cy = x + dist * math.cos(math.radians(ang)), y - dist * math.sin(math.radians(ang))
                rect = (cx - hw, cy - hh, cx + hw, cy + hh)
                pts = _rect_pts(cx, cy, hw, hh)
                clear = min(_seg_dist(pt, ZPOS[e["from"]], ZPOS[e["to"]]) for pt in pts for e in EDGES) - 4
                clear = min(clear, min(math.hypot(pt[0] - zx, pt[1] - zy) for pt in pts for zx, zy in ZPOS.values()) - R)
                clear = min([clear] + [_rect_gap(rect, rb) for rb in rows] + [_rect_gap(rect, pr) for pr in placed])
                clear = min(clear, cy - hh - (AX2_Y + 20), TAG_Y - 8 - (cy + hh))
                to_server = math.degrees(math.atan2(-(SERVER[1] - y), SERVER[0] - x))
                diff = abs((ang - bearing + 180) % 360 - 180)
                diff_s = abs((ang - to_server + 180) % 360 - 180)
                score = min(clear, 14) - 0.03 * diff_s - 0.01 * diff - 0.05 * (dist - R - 24)
                if best is None or score > best[0]:
                    best = (score, (cx, cy), rect)
        placed.append(best[2])
        out.append((zid, best[1]))
    return out


PHONES = phone_positions()
SERVER_IN = (SERVER[0] + 70, SERVER[1] - 6)


def bez(p0, c, p1, k):
    return ((1 - k) ** 2 * p0[0] + 2 * (1 - k) * k * c[0] + k ** 2 * p1[0],
            (1 - k) ** 2 * p0[1] + 2 * (1 - k) * k * c[1] + k ** 2 * p1[1])


def packet_path(p0):
    """Leaves the phone heading left (away from the zone graph), then bends into the server."""
    p1 = SERVER_IN
    c = (lerp(p0[0], p1[0], 0.55), lerp(p0[1], p1[1], 0.2) - 30)
    return p0, c, p1


def draw_zone_discs(img: Image.Image) -> None:
    """Zone discs as style.draw_zone_graph draws them (neutral), with a thin outline."""
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for z in ZONES:
        x, y = ZPOS[z["id"]]
        d.ellipse((x - R, y - R, x + R, y + R), fill=(*NAVY_3, 255), outline=(*INK_3, 255), width=2)
    img.alpha_composite(lay)


@lru_cache(maxsize=1)
def part2_static() -> tuple[Image.Image, Image.Image, Image.Image]:
    """(streets, zones + labels + server, both): the street pulses are drawn between the first two."""
    low = transparent()
    draw_zone_graph(low, PROJ, labels=False, radius=R)
    top = transparent()
    draw_zone_discs(top)
    for z in ZONES:                      # label tags (navy backing so street lines never run through text)
        box, org = label_box(z)
        rounded(top, box, 10, fill=NAVY_2, alpha=0.94)
        put_text(top, org[0], org[1], zone_label(z), LABEL_SIZE, 600, INK)
    paste(top, server_spr(), SERVER[0], SERVER[1], anchor="mm")
    put_text(top, SERVER[0], SERVER[1] + 64, "server", 22, 600, INK_2, align="m")
    full = low.copy()
    full.alpha_composite(top)
    return low, top, full


def phone_drop(t: float, i: int) -> float:
    return clamp((t - (BEATS["phones"] + 0.07 * i)) / 0.5)


def draw_street_pulses(img: Image.Image, t: float) -> None:
    """Streets light up one by one ("street by street"), then settle to a faint cyan."""
    layer = transparent()
    d = ImageDraw.Draw(layer)
    for i, e in enumerate(EDGES):
        start = BEATS["street"] + 0.12 * i
        k = progress(t, start, 0.45)
        if k <= 0:
            continue
        a = 1.0 - 0.65 * progress(t, start + 0.5, 0.6)
        (xa, ya), (xb, yb) = ZPOS[e["from"]], ZPOS[e["to"]]
        tip = (lerp(xa, xb, k), lerp(ya, yb, k))
        d.line([(xa, ya), tip], fill=(*CYAN, int(255 * a)), width=5)
        glow = 0.6 * (1 - progress(t, start + 0.3, 0.35))     # eases out (no pop when the pulse ends)
        if glow > 0.01:
            soft_line(img, (xa, ya), tip, CYAN, 8, 6, glow)
    img.alpha_composite(layer)


def draw_links(img: Image.Image, t: float) -> None:
    """Thin packet links from each phone to the server; they stay, dimmed, once the packet arrives.
    Drawn under the zone discs and label tags, so a link never runs over a zone or its text."""
    link = transparent()
    ld = ImageDraw.Draw(link)
    for i, (zid, ph) in enumerate(PHONES):
        start = BEATS["packets"] + 0.06 * i
        k = progress(t, start, 0.75)
        if k <= 0:
            continue
        p0, c, p1 = packet_path(ph)
        n = max(2, int(28 * k))
        pts = [bez(p0, c, p1, k * j / n) for j in range(n + 1)]
        a_link = 0.34 - 0.18 * progress(t, start + 0.75, 0.5)      # dims once the packet has arrived
        ld.line(pts, fill=(*CYAN, int(255 * a_link)), width=2)
    img.alpha_composite(link)


def draw_part2_dynamic(img: Image.Image, t: float) -> None:
    # zone rings once the chips arrive
    layer = transparent()
    d = ImageDraw.Draw(layer)
    for j, z in enumerate(ZONES):
        k = progress(t, BEATS["chips"] + 0.07 * j, 0.3)
        if k > 0:
            x, y = ZPOS[z["id"]]
            d.ellipse((x - R - 1, y - R - 1, x + R + 1, y + R + 1), outline=(*CYAN, int(255 * k)), width=3)
    img.alpha_composite(layer)

    # packets (their thin links are drawn under the zones and labels, in draw_links)
    packets = []
    for i, (zid, ph) in enumerate(PHONES):
        start = BEATS["packets"] + 0.06 * i
        k = progress(t, start, 0.75)
        if 0 < k < 1:
            p0, c, p1 = packet_path(ph)
            a = min(1, (t - start) / 0.12) * (1 - progress(t, start + 0.62, 0.13))
            packets.append((bez(p0, c, p1, k), a, lerp(0.45, 1.0, clamp((t - start) / 0.25))))

    # server glow as packets arrive, then the privacy shield
    arrive = progress(t, BEATS["packets"] + 0.6, 0.5)
    if arrive > 0:
        paste(img, glow_spr(CYAN, 60, 22), SERVER[0], SERVER[1], 0.35 * arrive, anchor="mm")
        paste(img, server_spr(), SERVER[0], SERVER[1], arrive, anchor="mm")
    a_sh = progress(t, BEATS["privacy"], 0.4)
    paste(img, shield_spr(), SERVER[0] + 62, SERVER[1] - 50, a_sh, scale=lerp(0.7, 1.0, ease_out_back(a_sh)), anchor="mm")

    # phones drop onto the zones
    for i, (zid, (x, y)) in enumerate(PHONES):
        k = phone_drop(t, i)
        if k <= 0:
            continue
        yy = y - (1 - ease_out_back(k, 1.1)) * 70
        a = clamp(k / 0.35)
        paste(img, glow_spr(INK, 10, 6), x, y + 18, 0.22 * a, anchor="mm")
        paste(img, phone_spr(), x, yy, a, anchor="mm")

    for (x, y), a, sc in packets:
        paste(img, packet_spr(), x, y, a, scale=sc, anchor="mm")

    # three forecast chips per zone
    for j, z in enumerate(ZONES):
        cx, cy = chips_origin(z)
        for h_i, h in enumerate(HORIZONS):
            start = BEATS["chips"] + 0.07 * j + 0.06 * h_i
            k = clamp((t - start) / 0.32)
            spr = chip_spr(h)
            if k > 0:
                paste(img, spr, cx + spr.width / 2, cy, clamp(k / 0.4), scale=lerp(0.5, 1.0, ease_out_back(k)), anchor="mm")
            cx += spr.width + CHIP_GAP


def draw_axis2_labels(img: Image.Image, t: float, xs: list[float]) -> None:
    beats = [BEATS["five"], BEATS["ten"], BEATS["fifteen"]]
    for i, (h, x) in enumerate(zip(HORIZONS, xs)):
        a = progress(t, beats[min(i, 2)], 0.4)
        lab = f"+{h} min" if i == len(HORIZONS) - 1 else f"+{h}"
        put_text(img, x, AX2_Y - 62 + (1 - a) * 12, lab, 34, 700, CYAN, a, align="m")


def draw_tagline(img: Image.Image, t: float) -> None:
    head, rest = TAGLINE.split(": ", 1)
    items = rest.split(" · ")
    beats = [BEATS["tag_next"], BEATS["street"] + 0.25, BEATS["phones"] + 0.35, BEATS["privacy"]]
    size = 32
    pieces = [(head + ": ", 700, CYAN, beats[0])]
    for i, it in enumerate(items):
        if i:
            pieces.append((" · ", 500, INK_3, beats[min(i, 3)]))
        pieces.append((it, 600, INK, beats[min(i, 3)]))
    total = sum(text_w(s, size, w_) for s, w_, _, _ in pieces)
    x = W / 2 - total / 2
    for s, w_, col, b in pieces:
        a = progress(t, b, 0.4)
        put_text(img, x, TAG_Y + (1 - a) * 10, s, size, w_, col, a)
        x += text_w(s, size, w_)


# ---------------------------------------------------------------- frame

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    cam = camera(t)
    p, z, tc = cam

    # first half (frozen and zoomed during the dive)
    if t < BEATS["dive"]:
        img.alpha_composite(draw_part1(t))
    else:
        a1 = 1 - progress(t, BEATS["dive"] + 0.05 * DIVE, 0.4 * DIVE)
        if a1 > 0:
            lay = zoomed(part1_frozen(), z, F, tc)
            if a1 < 1:
                lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a1)))
            img.alpha_composite(lay)

    # second half (grows out of the sliver)
    a2 = progress(t, BEATS["dive"] + 0.35 * DIVE, 0.6 * DIVE)
    if a2 > 0:
        low, top, full = part2_static()
        if p < 1:                        # still diving: the whole picture, scaled and fading in
            lay = zoomed(full, z / Z, T, tc)
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * a2)))
            img.alpha_composite(lay)
        else:
            img.alpha_composite(low)
            draw_street_pulses(img, t)
            draw_links(img, t)
            img.alpha_composite(top)
            draw_part2_dynamic(img, t)

    xs = draw_axis(img, t, cam)
    if p >= 1 or t > BEATS["dive"] + 0.8 * DIVE:
        draw_axis2_labels(img, t, xs)
    draw_tagline(img, t)

    # fixed slots
    chapter_card(img, CARD, fade(t, BEATS["card"] - 0.01, BEATS["card"] + CARD_HOLD + 0.3, 0.3))
    badge(img, "ILLUSTRATION", sub="prototype design, schematic", alpha=progress(t, BEATS["dive"] + DIVE - 0.2, 0.4))
    footer(img, FOOTER_2019, 1 - progress(t, BEATS["dive"] + 0.2, 0.4))
    footer(img, FOOTER_DESIGN, progress(t, BEATS["dive"] + 0.7, 0.4))
    return img


STILLS = {  # beat name -> time (s) for the layout stills
    "card": 1.2,
    "ticks": 5.6,
    "dive": 6.9,
    "streets": 9.9,
    "flow": 11.55,
    "end": DURATION - 1 / FPS,
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, nargs="*")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if args.preview:
        args.out.mkdir(parents=True, exist_ok=True)
        for t in args.preview:
            draw_frame(t).convert("RGB").save(args.out / f"{SHOT}_t{t:05.2f}.png")
        return
    out = render(SHOT, DURATION, draw_frame)
    print(out)
    for name, t in STILLS.items():
        print(still(f"{SHOT}_{name}", draw_frame(t)))


if __name__ == "__main__":
    main()
