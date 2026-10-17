"""S09 (1:30.0-1:38.5, 8.5 s), motion-graphics part only: the first 4.5 s, before the cut to the real
dashboard crops (C2a zone detail, C2b "Decided / expired" list), which are added at assembly
(video/recipes.py, s09).

Narration ([MEMBER 3], VO): "We lower its confidence when a sensor is unreliable or the data is
unusual. Below sixty percent, a person must review it."

What it shows (docs/video/script.md, section 3, S09 row):
- the equation builds term by term:
  effective confidence = model probability × sensor-reliability factor × unusual-data (OOD) factor;
- a gauge of effective confidence whose needle drops as each factor is applied: under a marked
  0.60 line with the sensor-reliability factor, and lower still with the unusual-data factor;
- the stamp "LOW CONFIDENCE — HUMAN REVIEW REQUIRED" (styled like the dashboard's ConfidenceBadge,
  dashboard/src/components/Badges.tsx) and the line "Below 0.60 → … only 'increase monitoring' is
  recommended";
- footer: "sensor-reliability factor = 0.4 + 0.6 × reliability (backend/app/services/prediction.py)
  · threshold in shared/config.json".
No chapter card (S08 shows "Can it be trusted?"). No status badge: the S09 storyboard row defines none.

Data sources (read at run time, never retyped):
- docs/video/shotlist.json, S09: the narration (checked; the beats are keyed to it) and the shot length;
- shared/config.json: confidence.low_confidence_threshold (the 0.60 line) and
  confidence.ood_confidence_multiplier (used only to place the needle's last drop);
- backend/app/services/prediction.py: the sensor-reliability factor 0.4 + 0.6 × reliability
  (the `rel_factor = ...` line, line 146 when written).
The needle positions are an example run of that formula (model probability EXAMPLE_MODEL_PROB,
sensor reliability EXAMPLE_RELIABILITY, unusual data on); no example value is printed on screen.

Output: video/build/mg/S09_mg.mp4 (1920x1080, 30 fps, 4.5 s) and stills in video/build/mg/stills/.
Run: .venv/bin/python video/mg/S09.py
"""
from __future__ import annotations

import json
import math
import re
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw  # noqa: E402

NAME = "S09_mg"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == "S09")
SHOT_DURATION = round(_shot["end_s"] - _shot["start_s"], 3)      # 8.5 s
NARRATION = ("We lower its confidence when a sensor is unreliable or the data is unusual. "
             "Below sixty percent, a person must review it.")
assert _shot["narration"] == NARRATION, "narration changed: re-measure the guide voice and re-key BEATS"
DURATION = 4.5  # the motion-graphics part: recipes.py s09 cuts to the dashboard crops at 4.5 s and keys its overlays to that cut
assert DURATION < SHOT_DURATION

# Beats in seconds from the shot start. The narration starts 0.2 s into the shot (assemble.py,
# VOICE_START). Keyed to the guide voice (video/build/guide/S09.wav, say -v Daniel -r 155):
# silencedetect pauses at 4.42-4.65 and 6.12-6.32 s of the wav; word starts from synthesising
# prefixes of the line, read off the wav's 20 ms energy envelope; + 0.2 s gives the shot times below:
#   "We lower its confidence" 0.20-1.50 ("confidence" 0.86) | "when a sensor" 1.52 ("sensor" 1.78) |
#   "is unreliable" 2.36-3.18 | "or the data is unusual." 3.22-4.62 ("unusual" 3.80) | pause |
#   "Below sixty percent," 4.85-6.34 | "a person must review it." 6.52-7.95 (both over the dashboard crops).
# The cut comes at 4.5 s, as "unusual" ends; the sensor-reliability drop alone takes the needle
# under 0.60 ("...when a sensor is unreliable OR the data is unusual") and the rule and stamp land on
# "unreliable", up for over a second before the cut; the unusual-data factor then takes it lower still.
# re-key to the real voice take
BEATS = {
    "lhs": 0.00,      # first frame: "effective confidence =" and the gauge appear
    "model": 0.10,    # "We lower its confidence": model probability; the needle swings up to it (by ~0.9 s)
    "sensor": 1.75,   # "sensor" (1.78): × sensor-reliability factor; the needle drops under 0.60 (1.9-2.45)
    "rule": 2.45,     # "unreliable", as the needle settles: "Below 0.60 →"
    "stamp": 2.55,    # LOW CONFIDENCE — HUMAN REVIEW REQUIRED stamps on
    "monitor": 2.8,   # "only 'increase monitoring' is recommended" (on screen only; held to the cut)
    "ood": 3.15,      # "or the data is unusual" (3.22): × unusual-data (OOD) factor; the needle drops further
}

# ---------- data ----------
CONFIG = json.loads((ROOT / "shared" / "config.json").read_text())["confidence"]
THRESHOLD = float(CONFIG["low_confidence_threshold"])
OOD_MULT = float(CONFIG["ood_confidence_multiplier"])
_pred_src = (ROOT / "backend" / "app" / "services" / "prediction.py").read_text()
_m = re.search(r"rel_factor\s*=.*?(\d+(?:\.\d+)?)\s*\+\s*(\d+(?:\.\d+)?)\s*\*\s*reliability", _pred_src)
assert _m, "sensor-reliability factor not found in prediction.py"
REL_A, REL_B = float(_m.group(1)), float(_m.group(2))

# example inputs for the needle only (never printed)
EXAMPLE_MODEL_PROB = 0.88
EXAMPLE_RELIABILITY = 0.35
V0 = EXAMPLE_MODEL_PROB
V1 = V0 * min(1.0, REL_A + REL_B * EXAMPLE_RELIABILITY)
V2 = V1 * OOD_MULT
assert V0 > THRESHOLD > V1 > V2, (V0, V1, V2)   # the sensor drop crosses the line (see BEATS); OOD lowers it further

FOOTER = (f"sensor-reliability factor = {REL_A:g} + {REL_B:g} × reliability (backend/app/services/prediction.py)"
          " · threshold in shared/config.json")
THRESHOLD_TXT = f"{THRESHOLD:.2f}"

# ---------- colours ----------
def mix(a, b, k: float) -> tuple[int, int, int]:
    """Integer RGB blend (Pillow needs ints)."""
    return tuple(int(round(x + (y - x) * k)) for x, y in zip(a[:3], b[:3]))


C_MODEL = CYAN
C_SENSOR = mix(BLUE, INK, 0.22)
C_OOD = mix(PURPLE, INK, 0.12)
AMBER_TXT = (253, 230, 138)                                  # tailwind amber-200, as on the dashboard badge
AMBER_FILL = tuple(int(0.6 * a + 0.4 * b) for a, b in zip((69, 26, 3), NAVY))   # amber-950/60 over navy

# ---------- layout ----------
EQ_X = 120                  # left edge of "effective confidence ="
OP_X = 168                  # centre of the × column
CHIP_X = 222                # left edge of the term chips
LHS_Y = 132
ROW_Y = {"model": 274, "sensor": 374, "ood": 474}   # chip centre lines
CHIP_H = 78

GX, GY, R, TW = 1440, 540, 270, 30      # gauge centre, radius of the track centre line, track width
SS = 3                                   # supersampling for the gauge
G_PAD = 110
G_BOX = (GX - R - G_PAD, GY - R - G_PAD, GX + R + G_PAD, GY + 40)   # region drawn at SS×

RULE_CY = 690               # centre line of "Below 0.60 → [stamp]"
MON_Y = 746                 # top of the "only 'increase monitoring' …" line


def ease_out_back(t: float, s: float = 1.6) -> float:
    t = clamp(t) - 1
    return 1 + (s + 1) * t ** 3 + s * t ** 2


def ease_out(t: float) -> float:
    return 1 - (1 - clamp(t)) ** 3


# ---------- sprites (static elements drawn once, then faded / moved per frame) ----------

class Sprite:
    def __init__(self, img: Image.Image):
        box = img.getbbox()
        self.img = img.crop(box)
        self.x, self.y = box[0], box[1]

    def put(self, frame: Image.Image, alpha: float = 1.0, dx: float = 0, dy: float = 0) -> None:
        if alpha <= 0.003:
            return
        im = self.img
        if alpha < 0.999:
            im = im.copy()
            im.putalpha(im.getchannel("A").point(lambda p: int(p * alpha)))
        frame.alpha_composite(im, (int(round(self.x + dx)), int(round(self.y + dy))))


def text_sprite(text: str, xy, size: int, weight: int, fill, anchor: str = "la") -> Sprite:
    img = transparent()
    draw_text(img, xy, text, size, weight, fill, anchor=anchor)
    return Sprite(img)


def chip_sprite(label: str, cy: int, accent) -> Sprite:
    img = transparent()
    tw, _ = text_size(label, 46, 600)
    rounded(img, (CHIP_X, cy - CHIP_H // 2, CHIP_X + tw + 72, cy + CHIP_H // 2), 16, fill=NAVY_2)
    rounded(img, (CHIP_X + 14, cy - 22, CHIP_X + 22, cy + 22), 4, fill=accent)
    draw_text(img, (CHIP_X + 44, cy + 2), label, 46, 600, INK, anchor="lm")
    return Sprite(img)


def warn_triangle(d: ImageDraw.ImageDraw, x: float, cy: float, s: float, colour, ink) -> None:
    """Warning triangle with "!" (Geist has no ⚠ glyph); x is the left edge, s the side length."""
    h = s * math.sqrt(3) / 2
    d.polygon([(x, cy + h / 2), (x + s / 2, cy - h / 2), (x + s, cy + h / 2)], fill=colour)
    d.rounded_rectangle((x + s / 2 - s * 0.055, cy - h * 0.16, x + s / 2 + s * 0.055, cy + h * 0.22), int(s * 0.05), fill=ink)
    d.ellipse((x + s / 2 - s * 0.065, cy + h * 0.29, x + s / 2 + s * 0.065, cy + h * 0.42), fill=ink)


def stamp_image() -> Image.Image:
    """The dashboard's low-confidence badge, enlarged: amber border, dark amber fill, amber-200 text.
    Drawn at 2× so it can be scaled smoothly while it stamps on."""
    k = 2
    label = "LOW CONFIDENCE — HUMAN REVIEW REQUIRED"
    f = font(34 * k, 700)
    l, t, r, b = f.getbbox(label)
    tri = 38 * k
    pad_x, h = 30 * k, 74 * k
    w = pad_x + tri + 18 * k + (r - l) + pad_x
    img = Image.new("RGBA", (w + 8 * k, h + 8 * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4 * k, 4 * k, 4 * k + w, 4 * k + h), 14 * k, fill=(*AMBER_FILL, 255), outline=(*WARNING, 255), width=3 * k)
    cy = 4 * k + h / 2
    warn_triangle(d, 4 * k + pad_x, cy - 1 * k, tri, WARNING, AMBER_FILL)
    d.text((4 * k + pad_x + tri + 18 * k, cy), label, font=f, fill=(*AMBER_TXT, 255), anchor="lm")
    return img


# ---------- gauge ----------

def g_local(x: float, y: float) -> tuple[float, float]:
    return ((x - G_BOX[0]) * SS, (y - G_BOX[1]) * SS)


def ang(v: float) -> float:
    """Pillow arc angle (degrees, clockwise from 3 o'clock) for value v on the upper semicircle."""
    return 180 + 180 * clamp(v)


def polar(v: float, rad: float) -> tuple[float, float]:
    a = math.radians(ang(v))
    return GX + rad * math.cos(a), GY + rad * math.sin(a)


def band(rad: float, width: float):
    """Bounding box for a Pillow arc of `width` px centred on radius `rad` (Pillow draws arc width inwards)."""
    return arc_box(rad + width / 2)


def arc_box(rad: float):
    x0, y0 = g_local(GX - rad, GY - rad)
    x1, y1 = g_local(GX + rad, GY + rad)
    return (x0, y0, x1, y1)


def gauge_base() -> Image.Image:
    """Static gauge track (amber-tinted under the threshold) and ticks, at SS×."""
    gw, gh = (G_BOX[2] - G_BOX[0]) * SS, (G_BOX[3] - G_BOX[1]) * SS
    img = Image.new("RGBA", (gw, gh), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc(band(R, TW), ang(0), ang(1), fill=(*NAVY_3, 255), width=TW * SS)
    # thin amber band inside the track marks the zone under the threshold
    d.arc(band(R - TW / 2 - 13, 6), ang(0), ang(THRESHOLD), fill=(*mix(NAVY, WARNING, 0.6), 255), width=6 * SS)
    for i in range(1, 10):                      # no ticks at 0 and 1: they read as minus signs
        v = i / 10
        p0, p1 = polar(v, R + TW / 2 + 8), polar(v, R + TW / 2 + (20 if i in (0, 5, 10) else 15))
        d.line([g_local(*p0), g_local(*p1)], fill=(*INK_3, 255), width=3 * SS)
    return img


def needle_value(t: float) -> float:
    v = lerp(0.0, V0, ease_out(clamp((t - BEATS["model"] - 0.05) / 0.75)))
    v = lerp(v, V1, progress(t, BEATS["sensor"] + 0.15, 0.55))
    v = lerp(v, V2, progress(t, BEATS["ood"] + 0.15, 0.55))
    return v


def below_mix(t: float) -> float:
    """0 while the needle is at or above the threshold, 1 once it is under; a short blend around it."""
    return clamp((THRESHOLD - needle_value(t)) / 0.08 + 0.5)


def gauge_layer(base: Image.Image, t: float) -> Image.Image:
    img = base.copy()
    d = ImageDraw.Draw(img)
    v = needle_value(t)
    p_s = progress(t, BEATS["sensor"] + 0.15, 0.55)
    p_o = progress(t, BEATS["ood"] + 0.15, 0.55)
    state = mix(SAFE, WARNING, below_mix(t))
    # discounted parts of the arc, in the colour of the factor that removed them
    if p_s > 0:
        d.arc(band(R, TW), ang(lerp(V0, V1, p_s)), ang(V0), fill=(*mix(NAVY_3, C_SENSOR, 0.75), 255), width=TW * SS)
    if p_o > 0:
        d.arc(band(R, TW), ang(lerp(V1, V2, p_o)), ang(V1), fill=(*mix(NAVY_3, C_OOD, 0.75), 255), width=TW * SS)
    if v > 0.002:
        d.arc(band(R, TW), ang(0), ang(v), fill=(*state, 255), width=TW * SS)
    # the marked threshold line: dashed from the hub out past the track
    n_dash, r0, r1 = 13, 46, R + TW / 2 + 30
    for i in range(n_dash):
        a0 = r0 + (r1 - r0) * i / n_dash
        a1 = a0 + (r1 - r0) / n_dash * 0.55
        d.line([g_local(*polar(THRESHOLD, a0)), g_local(*polar(THRESHOLD, a1))], fill=(*INK, 235), width=4 * SS)
    d.line([g_local(*polar(THRESHOLD, R - TW / 2 - 4)), g_local(*polar(THRESHOLD, R + TW / 2 + 4))], fill=(*INK, 255), width=6 * SS)
    # needle: tapered, hub on top
    a = math.radians(ang(v))
    ux, uy = math.cos(a), math.sin(a)
    nx, ny = -uy, ux
    tip = (GX + (R - TW / 2 - 2) * ux, GY + (R - TW / 2 - 2) * uy)
    tail = (GX - 12 * ux, GY - 12 * uy)        # hidden under the hub
    pts = [(tail[0] + 10 * nx, tail[1] + 10 * ny), (tip[0] + 2 * nx, tip[1] + 2 * ny),
           (tip[0] - 2 * nx, tip[1] - 2 * ny), (tail[0] - 10 * nx, tail[1] - 10 * ny)]
    d.polygon([g_local(*p) for p in pts], fill=(*INK, 255))
    hx, hy = g_local(GX, GY)
    d.ellipse((hx - 22 * SS, hy - 22 * SS, hx + 22 * SS, hy + 22 * SS), fill=(*INK, 255))
    d.ellipse((hx - 9 * SS, hy - 9 * SS, hx + 9 * SS, hy + 9 * SS), fill=(*NAVY, 255))
    out = img.resize(((G_BOX[2] - G_BOX[0]), (G_BOX[3] - G_BOX[1])), Image.LANCZOS)
    return out


# ---------- build the static pieces once ----------

BG = canvas()
LHS_LABEL = "effective confidence ="
S_LHS = text_sprite(LHS_LABEL, (EQ_X, LHS_Y), 56, 700, INK)
S_LHS_AMBER = text_sprite(LHS_LABEL, (EQ_X, LHS_Y), 56, 700, AMBER_TXT)
TERMS = [
    ("model", "model probability", C_MODEL, None),
    ("sensor", "sensor-reliability factor", C_SENSOR, "×"),
    ("ood", "unusual-data (OOD) factor", C_OOD, "×"),
]
S_CHIPS = {k: chip_sprite(label, ROW_Y[k], col) for k, label, col, _ in TERMS}
S_OPS = {k: text_sprite(op, (OP_X, ROW_Y[k]), 52, 500, INK_2, anchor="mm") for k, _, _, op in TERMS if op}

GAUGE_BASE = gauge_base()
_lbl = polar(THRESHOLD, R + TW / 2 + 62)
S_THR = text_sprite(THRESHOLD_TXT, _lbl, 38, 700, INK, anchor="mm")
S_THR_AMBER = text_sprite(THRESHOLD_TXT, _lbl, 38, 700, AMBER_TXT, anchor="mm")
_p0, _p1 = polar(0, R), polar(1, R)
_scale = transparent()
draw_text(_scale, (_p0[0], GY + 62), "0", 28, 600, INK_2, anchor="ms")
draw_text(_scale, (_p1[0], GY + 62), "1", 28, 600, INK_2, anchor="ms")
draw_text(_scale, (GX, GY + 62), "effective confidence", 26, 600, INK_2, anchor="ms")
S_SCALE = Sprite(_scale)

STAMP = stamp_image()
STAMP_W, STAMP_H = STAMP.width // 2, STAMP.height // 2
RULE_LABEL = f"Below {THRESHOLD_TXT} →"
_rule_w = text_size(RULE_LABEL, 44, 700)[0]
_row_w = _rule_w + 30 + STAMP_W
RULE_X = (W - _row_w) // 2
STAMP_X = RULE_X + _rule_w + 30
S_RULE = text_sprite(RULE_LABEL, (RULE_X, RULE_CY + 2), 44, 700, INK, anchor="lm")

_mon = transparent()
_parts = [("only ", 36, 500, INK_2), ("‘increase monitoring’", 36, 700, INK), (" is recommended", 36, 500, INK_2)]
_mon_w = sum(text_font(p, s, w_).getlength(p) for p, s, w_, _ in _parts)   # advance widths keep the spaces
_x = (W - _mon_w) / 2
for p, s, w_, col in _parts:
    draw_text(_mon, (_x, MON_Y), p, s, w_, col)
    _x += text_font(p, s, w_).getlength(p)
S_MON = Sprite(_mon)

_foot = transparent()
footer(_foot, FOOTER)
S_FOOT = Sprite(_foot)


def draw_frame(t: float) -> Image.Image:
    img = BG.copy()
    S_FOOT.put(img, progress(t, 0.0, 0.35))

    # equation, term by term
    k = progress(t, BEATS["lhs"], 0.4)
    amber = below_mix(t) if t > BEATS["sensor"] else 0.0   # text turns amber once a factor takes it under the line
    S_LHS.put(img, k * (1 - amber), dx=-28 * (1 - k))
    S_LHS_AMBER.put(img, k * amber, dx=-28 * (1 - k))
    for key, _, _, _ in TERMS:
        k = progress(t, BEATS[key], 0.4)
        if key in S_OPS:
            S_OPS[key].put(img, k)
        S_CHIPS[key].put(img, k, dx=36 * (1 - k))

    # gauge
    g = progress(t, BEATS["lhs"] + 0.05, 0.45)
    if g > 0:
        layer = gauge_layer(GAUGE_BASE, t)
        if g < 0.999:
            layer.putalpha(layer.getchannel("A").point(lambda p: int(p * g)))
        img.alpha_composite(layer, (G_BOX[0], G_BOX[1]))
        S_SCALE.put(img, g)
        S_THR.put(img, g * (1 - amber))
        S_THR_AMBER.put(img, g * amber)

    # rule line and stamp
    k = progress(t, BEATS["rule"], 0.3)
    S_RULE.put(img, k, dx=-24 * (1 - k))
    ks = clamp((t - BEATS["stamp"]) / 0.32)
    if ks > 0:
        sc = lerp(1.22, 1.0, ease_out_back(ks, 1.2))
        a = clamp(ks / 0.45)
        w_, h_ = int(STAMP_W * sc), int(STAMP_H * sc)
        st = STAMP.resize((w_, h_), Image.LANCZOS)
        if a < 0.999:
            st.putalpha(st.getchannel("A").point(lambda p: int(p * a)))
        # scale about the stamp's left edge: centred, the oversized first frames covered "Below 0.60 →"
        img.alpha_composite(st, (STAMP_X, int(round(RULE_CY - h_ / 2))))
    k = progress(t, BEATS["monitor"], 0.35)
    S_MON.put(img, k, dy=14 * (1 - k))
    return img


if __name__ == "__main__":
    out = render(NAME, DURATION, draw_frame)
    print("wrote", out)
    for beat, tt in [("lhs", 0.40), ("model", 1.40), ("sensor", 2.20), ("stamp", 2.90), ("ood", 3.50), ("end", DURATION - 1 / FPS)]:
        print("still", still(f"S09_{beat}", draw_frame(tt)))
