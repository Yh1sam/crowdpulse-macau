"""Shot S17 (3:38.5-3:56.5, 18.0 s): "Can it happen?" Feasibility and business.

Storyboard: docs/video/script.md section 3, row S17; claims table section 4, rows S17; section 6
"motion_graphic" (S17: the cost panel stays empty until sourced); shot list docs/video/shotlist.json
(id S17). Speaker [MEMBER 5] (VO over B-roll), a new speaker: the lower-third area stays clear 0-3 s.

0-5 s     a phone-on-clamp kit hops between festival pages of a calendar while a pole-mounted
          counting camera stays bolted in place (badge ILLUSTRATION, design intent, not field-tested).
5-10 s    the two icons slide into the cost panel: phone kit vs fixed counting camera, value slots
          empty, the verbatim research placeholder in an amber dashed box (badge PENDING). No figures.
10-13 s   slate for the team's 3 s B-roll of a real pytest run (hard cuts in and out, so the footage
          drops straight in).
13-18 s   counters 49 + 15 + 27 + 13 tick up to 104; "a fresh clone runs from the README"; the
          intended-operators and AGPL lines; a roadmap arrow with four stations (badge LIVE SOFTWARE).

Data (read, never retyped):
  docs/testing.md, section 1 table          the four suite counts (49 / 15 / 27 / 13) and their sum
  docs/deployment.md, "Operational model"   the peak periods on the calendar pages (not its cost table)
  docs/video/shotlist.json, S17             chapter card, cost placeholder, operators line, test line,
                                            AGPL line and roadmap stations, split verbatim from
                                            on_screen_text; the slate wording from "visual"
Footer sources: docs/testing.md, experiments/results/simulation_run/README.md,
THIRD_PARTY_NOTICES.md, docs/experiment-protocol.md (claims table rows S17).

Run: .venv/bin/python video/mg/S17.py [--stills-only]
  -> video/build/mg/S17.mp4, video/build/overlays/S17.mov (chapter card, badge and footer only, to
     lay over the team B-roll at 10-13 s) and stills in video/build/mg/stills/.
"""
from __future__ import annotations

import json
import math
import re
import sys

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

NAME = "S17"
SHOT = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == NAME)
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 18.0 s

# ---------- timing ----------
# Seconds from the shot start, keyed to the narration at 140 wpm (0.43 s per word, voice from 0 s;
# the cost sentence is a reserved <=10-word slot, 5-10 s). re-key to the real voice take.
BEATS = {
    "phones": 0.0,          # "Phones on temporary mounts" -> calendar pages rise, kit drops onto page 1
    "kit_down": 0.45,       # kit drop starts (lands ~1.1 s)
    "serve_one": 2.1,       # "can serve one festival" -> page 1 lights, kit counting
    "then_move": 3.45,      # "then move" -> hop to page 2; "bolted in place" label on the pole
    "to_the_next": 4.2,     # "to the next" -> hop to page 3
    "cost": 5.0,            # cost slot -> icons slide into the cost panel
    "cost_box": 6.0,        # placeholder box lands
    "broll": 10.0,          # "The whole chain runs end to end in simulation" -> team B-roll (hard cut)
    "tests": 13.0,          # "with 104 automated tests passing" -> counters (hard cut back)
    "total": 14.7,          # "one hundred and four" lands -> total pulses
    "facts": 15.05,         # operators + AGPL lines
    "roadmap": 15.6,        # roadmap arrow slides in
}
CHAPTER_END = 2.2
HOP = 0.55                 # seconds per hop
T_OUT = DURATION

# ---------- data ----------

TESTING = (ROOT / "docs" / "testing.md").read_text()
SUITE_ROWS = [  # (label on screen, regex on the docs/testing.md section 1 table)
    ("Python", r"^\| backend API \+ ML pipeline \|.*\| (\d+) passed \|$"),
    ("dashboard", r"^\| dashboard components \|.*\| (\d+) passed \|$"),
    ("SketchFuture", r"^\| SketchFuture model \+ CrowdPulse hand-over \|.*\| (\d+) passed \|$"),
    ("iOS", r"^\| iOS logic \+ detector \|.*\| (\d+) tests, 0 failures \|$"),
]
SUITES = [(label, int(re.search(rx, TESTING, re.M).group(1))) for label, rx in SUITE_ROWS]
TOTAL = sum(n for _, n in SUITES)

DEPLOY = (ROOT / "docs" / "deployment.md").read_text()
_opmodel = DEPLOY.split("## Operational model", 1)[1].split("\n## ", 1)[0]
PEAKS = [p.strip() for p in re.search(r"peak periods \(([^)]*)\)", _opmodel).group(1).split(",")]
ZH = {"Golden Week": "黃金周", "Grand Prix": "格蘭披治大賽車", "Chinese New Year": "農曆新年"}
# calendar order from October: Golden Week, Grand Prix, Chinese New Year (no dates are shown)
EVENTS = [(p, ZH[p]) for p in ("Golden Week", "Grand Prix", "Chinese New Year") if p in PEAKS]
assert len(EVENTS) == 3, PEAKS

OST = [p.strip() for p in SHOT["on_screen_text"].split(" | ")]
CHAPTER = OST[0].split(": ", 1)[1]                                         # Can it happen?
COST_PLACEHOLDER = next(p for p in OST if p.startswith("Cost panel: ")).split(": ", 1)[1]
_ops = next(p for p in OST if p.startswith("Intended operators:"))
OPS_HEAD, OPS_BODY = _ops.split(": ", 1)
OPS_HEAD += ":"
_tests = next(p for p in OST if p.startswith("Python "))
_lic = next(p for p in OST if p.startswith("Open source"))
LIC_HEAD, LIC_BODY = _lic.split("; ", 1)
LIC_HEAD += ";"
_road = next(p for p in OST if p.startswith("Roadmap: ")).split(": ", 1)[1].split(" → ")
STATIONS = []
for s_ in _road:
    m = re.match(r"^(.*?)(?: \((.*)\))?$", s_)
    STATIONS.append((m.group(1)[0].upper() + m.group(1)[1:], m.group(2) or ""))

# guards: the screen text must agree with docs/testing.md and the narration
_expect = " · ".join(f"{label} {n}" for label, n in SUITES) + f" = {TOTAL} automated tests · "
assert _tests.startswith(_expect), (_tests, _expect)
TOTAL_LABEL = "automated tests"
CLONE_LINE = _tests[len(_expect):]                                           # a fresh clone runs from the README
assert f"with {TOTAL} automated tests passing" in SHOT["narration"], SHOT["narration"]
assert f"'{SUITES[0][1]} passed'" in SHOT["visual"], SHOT["visual"]
SLATE_TEXT = f"3 s B-roll: a member runs .venv/bin/python -m pytest -q, screen shows '{SUITES[0][1]} passed'"

BADGE_SEGMENTS = [  # (start, end, kind, detail, sub-line)
    (0.0, BEATS["cost"], "ILLUSTRATION", "", "design intent, not field-tested"),
    (BEATS["cost"], BEATS["broll"], "PENDING", "", "cost: empty until sourced"),
    (BEATS["broll"], DURATION, "LIVE SOFTWARE", "", "real test runs"),
]
FOOTER_SEGMENTS = [
    (0.0, BEATS["cost"], "Operational model: docs/deployment.md · design intent, not field-tested"),
    (BEATS["cost"], BEATS["broll"], "Cost panel: no figures until sourced; the sources will be shown on screen"),
    (BEATS["broll"], BEATS["tests"], "B-roll: the Python test suite, run as in docs/testing.md"),
    (BEATS["tests"], DURATION, "docs/testing.md · experiments/results/simulation_run/ · "
                               "THIRD_PARTY_NOTICES.md · docs/experiment-protocol.md"),
]

# ---------- small drawing helpers (sprites = (image, (x, y)) at absolute frame positions) ----------

SS = 3


def hires(size, fn) -> Image.Image:
    """Draws fn(d, q) on a q-times larger canvas and downsamples (anti-aliased shapes)."""
    big = Image.new("RGBA", (int(size[0]) * SS, int(size[1]) * SS), (0, 0, 0, 0))
    fn(ImageDraw.Draw(big), SS)
    return big.resize((int(size[0]), int(size[1])), Image.LANCZOS)


def layer_sprite(fn):
    """Runs fn(img) on a transparent full frame (style helpers draw in place) and crops it."""
    lay = transparent()
    fn(lay)
    bb = lay.getbbox()
    if bb is None:
        return Image.new("RGBA", (1, 1), (0, 0, 0, 0)), (0, 0)
    return lay.crop(bb), (bb[0], bb[1])


def text_sprite(xy, text, size, weight=400, fill=INK, anchor="la", max_width=None):
    return layer_sprite(lambda im: draw_text(im, xy, text, size, weight, fill, anchor=anchor, max_width=max_width))


_LUT: dict[int, list[int]] = {}


def with_alpha(im: Image.Image, a: float) -> Image.Image:
    if a >= 0.999:
        return im
    k = int(round(a * 255))
    lut = _LUT.setdefault(k, [v * k // 255 for v in range(256)])
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lut))
    return out


def put(img: Image.Image, sprite, alpha: float = 1.0, dx: float = 0, dy: float = 0) -> None:
    if alpha <= 0.004:
        return
    im, (x, y) = sprite
    x, y = int(round(x + dx)), int(round(y + dy))
    if x < 0 or y < 0 or x + im.width > W or y + im.height > H:   # clip to the frame
        cx0, cy0 = max(0, -x), max(0, -y)
        cx1, cy1 = min(im.width, W - x), min(im.height, H - y)
        if cx1 <= cx0 or cy1 <= cy0:
            return
        im = im.crop((cx0, cy0, cx1, cy1))
        x, y = x + cx0, y + cy0
    img.alpha_composite(with_alpha(im, alpha), (x, y))


def rrect_path(box, r: float, n: int = 10):
    x0, y0, x1, y1 = box
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def dashed_path(d: ImageDraw.ImageDraw, pts, fill, width: int, dash: float, gap: float) -> None:
    """Dashes along a polyline, continuous around corners."""
    acc, run = 0.0, []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg))
        for i in range(n + 1):
            s = acc + seg * i / n
            p = (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
            if (s % (dash + gap)) < dash:
                run.append(p)
            elif run:
                if len(run) > 1:
                    d.line(run, fill=fill, width=width)
                run = []
        acc += seg
    if len(run) > 1:
        d.line(run, fill=fill, width=width)


def dashed_panel(box, radius, border_colour, fill=NAVY_2, width=3, dash=18, gap=11, fill_alpha=255):
    """Rounded panel with a dashed border, as a sprite."""
    x0, y0, x1, y1 = box
    pad = width + 2
    w_, h_ = x1 - x0 + 2 * pad, y1 - y0 + 2 * pad

    def fn(d, q):
        b = (pad * q, pad * q, (pad + x1 - x0) * q, (pad + y1 - y0) * q)
        if fill is not None:
            d.rounded_rectangle(b, radius * q, fill=(*fill, fill_alpha))
        dashed_path(d, rrect_path(b, radius * q), (*border_colour, 255), width * q, dash * q, gap * q)
    return hires((w_, h_), fn), (x0 - pad, y0 - pad)


def camera_glyph(d, x, y, s, fill):
    """Small film-camera glyph (as on the S12 slate)."""
    d.ellipse((x + 4 * s, y, x + 18 * s, y + 14 * s), outline=fill, width=int(3 * s))
    d.ellipse((x + 20 * s, y, x + 34 * s, y + 14 * s), outline=fill, width=int(3 * s))
    d.rounded_rectangle((x, y + 16 * s, x + 38 * s, y + 42 * s), int(5 * s), fill=fill)
    d.polygon([(x + 40 * s, y + 29 * s), (x + 54 * s, y + 19 * s), (x + 54 * s, y + 39 * s)], fill=fill)


def check_mark(d, cx, cy, s, fill, width):
    d.line([(cx - 0.42 * s, cy + 0.02 * s), (cx - 0.12 * s, cy + 0.32 * s), (cx + 0.45 * s, cy - 0.30 * s)],
           fill=fill, width=width, joint="curve")


def hexagon(d, cx, cy, r, fill):
    d.polygon([(cx + r * math.cos(math.radians(30 + 60 * k)), cy + r * math.sin(math.radians(30 + 60 * k))) for k in range(6)], fill=fill)


# ---------- icon sprites ----------

KIT_W, KIT_H = 130, 220          # phone-on-clamp kit; feet at y 214, phone centre (65, 70)
KIT_PHONE_TOP = 22


def kit_sprite() -> Image.Image:
    def fn(d, q):
        cx, cy = 65 * q, 70 * q
        clamp, jaw = (*INK_2, 255), (*GREY, 255)
        # back bar of the clamp, behind the phone
        d.rounded_rectangle((cx - 40 * q, cy - 8 * q, cx + 40 * q, cy + 8 * q), 5 * q, fill=clamp)
        phone_icon(d, cx, cy, 1.18 * q, fill=(*INK, 255), screen=(*NAVY_3, 255))
        d.ellipse((cx - 3.5 * q, cy - 43 * q, cx + 3.5 * q, cy - 36 * q), fill=(*NAVY, 255))          # lens
        d.ellipse((cx - 8 * q, cy - 6 * q, cx + 8 * q, cy + 10 * q), fill=(*CYAN, 255))              # live dot
        # spring jaws gripping both long edges
        for sgn in (-1, 1):
            x_edge = cx + sgn * 26 * q
            d.rounded_rectangle((min(x_edge, x_edge + sgn * 12 * q), cy - 14 * q, max(x_edge, x_edge + sgn * 12 * q), cy + 14 * q), 4 * q, fill=jaw)
            d.rounded_rectangle((min(x_edge - sgn * 5 * q, x_edge + sgn * 2 * q), cy - 14 * q, max(x_edge - sgn * 5 * q, x_edge + sgn * 2 * q), cy - 6 * q), 2 * q, fill=jaw)
            d.rounded_rectangle((min(x_edge - sgn * 5 * q, x_edge + sgn * 2 * q), cy + 6 * q, max(x_edge - sgn * 5 * q, x_edge + sgn * 2 * q), cy + 14 * q), 2 * q, fill=jaw)
        # ball head, stalk and a small tripod
        top = cy + 47 * q
        d.ellipse((cx - 9 * q, top + 2 * q, cx + 9 * q, top + 20 * q), fill=clamp)
        d.rounded_rectangle((cx - 4 * q, top + 14 * q, cx + 4 * q, top + 62 * q), 3 * q, fill=clamp)
        foot = 214 * q
        for dx in (-38, 0, 38):
            d.line([(cx, top + 58 * q), (cx + dx * q, foot)], fill=clamp, width=5 * q)
        d.ellipse((cx - 7 * q, top + 54 * q, cx + 7 * q, top + 68 * q), fill=clamp)
    return hires((KIT_W, KIT_H), fn)


def arcs_sprite() -> Image.Image:
    """Signal arcs above the kit while it counts."""
    def fn(d, q):
        c = 50 * q
        for r, w_ in ((16, 4), (28, 4)):
            d.arc((c - r * q, c - r * q, c + r * q, c + r * q), 225, 315, fill=(*CYAN, 255), width=w_ * q)
    return hires((100, 60), fn)


POLE_W, POLE_H = 360, 512        # pole-mounted counting camera; base centre at (250, 508)
POLE_BASE = (250, 508)


def pole_sprite() -> Image.Image:
    def fn(d, q):
        Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
        d.polygon([Q(188, 478), Q(312, 478), Q(328, 508), Q(172, 508)], fill=(*NAVY_3, 255))         # footing
        d.rounded_rectangle(Q(240, 120, 260, 470), 6 * q, fill=(*GREY, 255))                         # pole
        d.rounded_rectangle(Q(244, 126, 248, 464), 2 * q, fill=(*INK_2, 150))
        d.rounded_rectangle(Q(198, 460, 302, 480), 5 * q, fill=(*INK_3, 255))                        # base plate
        for bx in (214, 250, 286):
            hexagon(d, bx * q, 470 * q, 8 * q, (*INK_2, 255))
            d.ellipse(Q(bx - 2.5, 467.5, bx + 2.5, 472.5), fill=(*NAVY, 255))
        d.rounded_rectangle(Q(232, 196, 268, 224), 5 * q, fill=(*INK_3, 255))                        # pole band
        for bx in (238, 262):
            hexagon(d, bx * q, 210 * q, 5 * q, (*INK_2, 255))
        d.rounded_rectangle(Q(176, 112, 256, 128), 5 * q, fill=(*GREY, 255))                         # arm
        d.ellipse(Q(236, 106, 264, 130), fill=(*GREY, 255))
        d.ellipse(Q(184, 104, 214, 134), fill=(*INK_3, 255))                                         # tilt joint
        hexagon(d, 199 * q, 119 * q, 6 * q, (*INK_2, 255))
        d.rounded_rectangle(Q(52, 82, 196, 140), 12 * q, fill=(*INK_2, 255))                         # housing
        d.rounded_rectangle(Q(40, 70, 206, 86), 5 * q, fill=(*INK, 255))                             # hood
        d.rounded_rectangle(Q(50, 90, 74, 134), 6 * q, fill=(*NAVY_3, 255))                          # front face
        d.ellipse(Q(46, 96, 78, 128), fill=(*NAVY, 255))                                             # lens
        d.ellipse(Q(54, 104, 70, 120), outline=(*INK_3, 255), width=3 * q)
        d.ellipse(Q(57, 106, 62, 111), fill=(*INK_2, 255))
    return hires((POLE_W, POLE_H), fn)


def scaled(im: Image.Image, s: float) -> Image.Image:
    if abs(s - 1) < 1e-3:
        return im
    return im.resize((max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))), Image.LANCZOS)


def shadow_sprite() -> Image.Image:
    im = Image.new("RGBA", (140, 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((20, 12, 120, 28), fill=(0, 0, 0, 150))
    return im.filter(ImageFilter.GaussianBlur(4))


KIT, ARCS, POLE, SHADOW = kit_sprite(), arcs_sprite(), pole_sprite(), shadow_sprite()
POLE_SMALL_S = 0.5
POLE_SMALL = scaled(POLE, POLE_SMALL_S)

# ---------- part 1: calendar and pole ----------

PAGE_W, PAGE_Y0, PAGE_Y1, PAGE_GAP, PAGE_X0 = 300, 268, 698, 70, 150
GROUND_Y = PAGE_Y1 - 14                      # the line each kit stands on
FLOOR_Y = PAGE_Y1 + 32                       # street level under the pole
PAGE_XS = [PAGE_X0 + i * (PAGE_W + PAGE_GAP) for i in range(3)]
KIT_LAND_Y = GROUND_Y - 2 - 214               # sprite top when the kit's feet stand on the page's ground line
KIT_POS = [(x + PAGE_W / 2 - KIT_W / 2, KIT_LAND_Y) for x in PAGE_XS]
POLE_AT = (1610, FLOOR_Y)                      # base centre in part 1
POLE_ORIGIN = (POLE_AT[0] - POLE_BASE[0], POLE_AT[1] - POLE_BASE[1])
SEP_X = 1262


def page_sprite(i: int):
    x0 = PAGE_XS[i]
    en, zh = EVENTS[i]

    def fn(img):
        rounded(img, (x0, PAGE_Y0, x0 + PAGE_W, PAGE_Y1), 18, fill=NAVY_2)
        rounded(img, (x0, PAGE_Y0, x0 + PAGE_W, PAGE_Y0 + 62), 18, fill=NAVY_3)
        rounded(img, (x0, PAGE_Y0 + 40, x0 + PAGE_W, PAGE_Y0 + 62), 0, fill=NAVY_3)
        draw_text(img, (x0 + PAGE_W / 2, PAGE_Y0 + 31), "peak period · 高峰期", 20, 600, INK_2, anchor="mm")
        draw_text(img, (x0 + PAGE_W / 2, PAGE_Y0 + 92), en, 30, 700, INK, anchor="ma")
        draw_text(img, (x0 + PAGE_W / 2, PAGE_Y0 + 136), zh, 28, 500, INK_2, anchor="ma")
        ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ground).line([(x0 + 40, GROUND_Y), (x0 + PAGE_W - 40, GROUND_Y)], fill=(*INK_3, 140), width=2)
        img.alpha_composite(ground)
    base = layer_sprite(fn)
    rings = hires((PAGE_W, 40), lambda d, q: [d.rounded_rectangle(((rx - 7) * q, 2 * q, (rx + 7) * q, 38 * q), 7 * q, fill=(*INK_2, 255)) for rx in (80, 220)])
    return base, (rings, (x0, PAGE_Y0 - 16))


PAGES = [page_sprite(i) for i in range(3)]
GLOW = [(hires((PAGE_W + 16, PAGE_Y1 - PAGE_Y0 + 16), lambda d, q: d.rounded_rectangle((2 * q, 2 * q, (PAGE_W + 14) * q, (PAGE_Y1 - PAGE_Y0 + 14) * q), 22 * q, outline=(*CYAN, 255), width=4 * q)), (x - 8, PAGE_Y0 - 8)) for x in PAGE_XS]


def served_sprite(i: int):
    x0 = PAGE_XS[i]

    def fn(d, q):   # a check where the kit stood, once it has moved on
        d.ellipse((2 * q, 2 * q, 62 * q, 62 * q), fill=(*SAFE, 255))
        check_mark(d, 32 * q, 32 * q, 36 * q, (*INK, 255), 6 * q)
    return hires((64, 64), fn), (x0 + PAGE_W / 2 - 32, GROUND_Y - 150)


SERVED = [served_sprite(i) for i in range(3)]

HEAD_L = [text_sprite((PAGE_X0, 156), "Phone on a temporary mount", 30, 700, INK),
          text_sprite((PAGE_X0, 198), "臨時支架上的手機", 26, 500, INK_2)]
HEAD_R_X = 1540
HEAD_R = [text_sprite((HEAD_R_X, 156), "Fixed counting camera", 30, 700, INK, anchor="ma"),
          text_sprite((HEAD_R_X, 198), "固定計數鏡頭", 26, 500, INK_2, anchor="ma")]
BOLTED = text_sprite((HEAD_R_X, FLOOR_Y + 24), "bolted in place · 固定安裝", 26, 600, INK_2, anchor="ma")


def scene_static():
    def fn(img):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        lx, ly = POLE_ORIGIN[0] + 62, POLE_ORIGIN[1] + 112
        d.polygon([(lx, ly), (1318, FLOOR_Y), (1520, FLOOR_Y)], fill=(*CYAN, 26))                     # field of view
        d.line([(1300, FLOOR_Y), (1800, FLOOR_Y)], fill=(*INK_3, 160), width=2)                       # ground
        d.line([(SEP_X, 160), (SEP_X, FLOOR_Y)], fill=(*NAVY_3, 255), width=2)                    # divider
        img.alpha_composite(lay)
    return layer_sprite(fn)


SCENE = scene_static()


def kit_state(t: float):
    """Kit sprite top-left, its height above the ground and the page it stands on (or None)."""
    land = [BEATS["kit_down"] + 0.6, BEATS["then_move"] + HOP, BEATS["to_the_next"] + HOP]
    if t < land[0]:
        k = progress(t, BEATS["kit_down"], 0.6)
        lift = (1 - k) * 260
        x, y = KIT_POS[0]
        return (x, y - lift), lift, None, k
    for i, (ts, frm, to) in enumerate(((BEATS["then_move"], 0, 1), (BEATS["to_the_next"], 1, 2))):
        if t < ts:
            return KIT_POS[frm], 0.0, frm, 1.0
        if t < ts + HOP:
            k = ease((t - ts) / HOP)
            x = lerp(KIT_POS[frm][0], KIT_POS[to][0], k)
            lift = 170 * math.sin(math.pi * k)
            return (x, KIT_LAND_Y - lift), lift, None, 1.0
    return KIT_POS[2], 0.0, 2, 1.0


def page_active(i: int, t: float) -> float:
    if i == 0:
        return fade(t, BEATS["serve_one"], BEATS["then_move"] + 0.1, 0.3)
    if i == 1:
        return fade(t, BEATS["then_move"] + HOP - 0.05, BEATS["to_the_next"] + 0.1, 0.18)
    return fade(t, BEATS["to_the_next"] + HOP - 0.05, BEATS["cost"] + 0.4, 0.2)


def served_alpha(i: int, t: float) -> float:
    start = [BEATS["then_move"] + 0.3, BEATS["to_the_next"] + 0.3, 99][i]   # once the kit has left the page
    return progress(t, start, 0.3)


# ---------- part 2: cost panel ----------

PANEL = (240, 160, 1680, 830)
COL_L, COL_R = 640, 1280
KIT_COST = (COL_L - KIT_W / 2, 262)                        # kit sprite top-left in the panel
POLE_COST_BASE = (COL_R + 50, 488)                         # pole base centre in the panel


def panel_static():
    def fn(img):
        rounded(img, PANEL, 26, fill=NAVY_2)
        draw_text(img, (PANEL[0] + 48, PANEL[1] + 36), "Cost · 成本", 34, 700, INK)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).line([(960, 300), (960, 470)], fill=(*NAVY_3, 255), width=2)
        img.alpha_composite(lay)
        draw_text(img, (960, 388), "vs", 30, 600, INK_3, anchor="mm")
    return layer_sprite(fn)


PANEL_BG = panel_static()
COST_LABELS = [
    [text_sprite((COL_L, 514), "Phone kit", 30, 700, INK, anchor="ma"),
     text_sprite((COL_L, 556), "手機套件", 26, 500, INK_2, anchor="ma")],
    [text_sprite((COL_R, 514), "Fixed counting camera", 30, 700, INK, anchor="ma"),
     text_sprite((COL_R, 556), "固定計數鏡頭", 26, 500, INK_2, anchor="ma")],
]


def value_slot(cx: float):
    box = (cx - 190, 616, cx + 190, 682)
    frame_, pos = dashed_panel(box, 14, INK_3, fill=NAVY, width=2, dash=10, gap=8, fill_alpha=255)
    label = text_sprite((cx, 649), "empty until sourced", 22, 500, INK_3, anchor="mm")
    return [(frame_, pos), label]


SLOTS = [value_slot(COL_L), value_slot(COL_R)]


def placeholder_sprite(text: str, cx: float, top: float, size: int = 28, max_w: int = 1300):
    lines = wrap(text, size, 600, max_w - 48)
    lh = int(size * 1.35)
    tw = max(text_size(l, size, 600)[0] for l in lines)
    box = (cx - tw / 2 - 26, top, cx + tw / 2 + 26, top + lh * len(lines) + 30)
    frame_ = dashed_panel(box, 14, WARNING, fill=NAVY, width=3)
    txt = layer_sprite(lambda im: [draw_text(im, (cx, top + 15 + i * lh + lh / 2), l, size, 600, WARNING, anchor="mm") for i, l in enumerate(lines)])
    return [frame_, txt]


COST_BOX = placeholder_sprite(COST_PLACEHOLDER, 960, 722)

# ---------- part 3: B-roll slate ----------

SLATE = (120, 150, 1800, 790)


def slate_static():
    x0, y0, x1, y1 = SLATE
    frame_ = dashed_panel(SLATE, 22, WARNING, fill=NAVY_2, width=3)
    glyph = (hires((70, 50), lambda d, q: camera_glyph(d, 4 * q, 3 * q, 1.1 * q, (*WARNING, 255))), (x0 + 60, y0 + 56))
    title = text_sprite((x0 + 150, y0 + 60), "[TEAM FOOTAGE]", 40, 700, WARNING)
    body = text_sprite((x0 + 60, y0 + 140), SLATE_TEXT, 36, 500, INK, max_width=x1 - x0 - 120)

    def laptop(d, q):
        Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
        d.rounded_rectangle(Q(30, 0, 450, 250), 14 * q, fill=(*NAVY_3, 255))
        d.rounded_rectangle(Q(46, 16, 434, 234), 8 * q, fill=(*NAVY, 255))
        for i, w_ in enumerate((300, 220, 260, 180)):
            d.rounded_rectangle(Q(70, 40 + i * 34, 70 + w_, 54 + i * 34), 4 * q, fill=(*INK_3, 255))
        d.rounded_rectangle(Q(70, 190, 230, 206), 4 * q, fill=(*SAFE, 255))
        d.rounded_rectangle(Q(0, 252, 480, 272), 8 * q, fill=(*INK_3, 255))
    lap = (hires((480, 274), laptop), ((x0 + x1) / 2 - 240, y0 + 300))
    return [frame_, glyph, title, body, lap]


SLATE_SPRITES = slate_static()
SLATE_BAR = (SLATE[0] + 60, SLATE[3] - 46, SLATE[2] - 60)       # 3 s duration bar (x0, y, x1)

# ---------- part 4: counters, facts and roadmap ----------

DY4 = 20                          # part 4 sits a little lower, centred between the badge and the caption band
TILE_W, TOTAL_W, OP_W, TILE_Y0, TILE_Y1 = 230, 320, 64, 160 + DY4, 340 + DY4
_row_w = 4 * TILE_W + TOTAL_W + 4 * OP_W
_x = (W - _row_w) / 2
TILES = []
for _ in range(4):
    TILES.append((_x, _x + TILE_W))
    _x += TILE_W + OP_W
TOTAL_TILE = (_x, _x + TOTAL_W)
OPS = [(TILES[i][1] + OP_W / 2, "+" if i < 3 else "=") for i in range(4)]
NUM_Y = 238 + DY4
TILE_LABEL_Y = 304 + DY4


def digit_sprites(size: int, colour) -> tuple[list[Image.Image], list[float]]:
    """One sprite per digit, each as wide as its own advance (proportional figures, so a '1' does
    not leave a gap); the number is laid out from these advances and centred."""
    f = font(size, 700)
    adv = [f.getlength(str(k)) for k in range(10)]
    out = []
    for k in range(10):
        im = Image.new("RGBA", (int(math.ceil(adv[k])) + 8, int(size * 1.4)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, size * 0.7), str(k), font=f, fill=(*colour, 255), anchor="lm")
        out.append(im)
    return out, adv


DIGITS, DIGIT_ADV = digit_sprites(88, INK)
DIGITS_T, DIGIT_ADV_T = digit_sprites(100, CYAN)


def number(img: Image.Image, value: int, cx: float, cy: float, big: bool = False, alpha: float = 1.0) -> None:
    digs, adv = (DIGITS_T, DIGIT_ADV_T) if big else (DIGITS, DIGIT_ADV)
    s = str(value)
    x = cx - sum(adv[int(ch)] for ch in s) / 2
    for ch in s:
        im = digs[int(ch)]
        put(img, (im, (x - 4, cy - im.height / 2)), alpha)
        x += adv[int(ch)]


def tiles_static():
    sprites = []
    for (x0, x1), (label, _) in zip(TILES, SUITES):
        sprites.append(layer_sprite(lambda im, x0=x0, x1=x1, label=label: (
            rounded(im, (x0, TILE_Y0, x1, TILE_Y1), 20, fill=NAVY_2),
            draw_text(im, ((x0 + x1) / 2, TILE_LABEL_Y), label, 26, 600, INK_2, anchor="mm"))))
    x0, x1 = TOTAL_TILE
    total = layer_sprite(lambda im: (
        rounded(im, (x0, TILE_Y0, x1, TILE_Y1), 20, fill=NAVY_2, outline=CYAN, width=3),
        draw_text(im, ((x0 + x1) / 2, TILE_LABEL_Y), TOTAL_LABEL, 26, 600, INK, anchor="mm")))
    ops = [text_sprite((cx, NUM_Y), op, 56, 500, INK_3, anchor="mm") for cx, op in OPS]
    return sprites, total, ops


TILE_SPRITES, TOTAL_SPRITE, OP_SPRITES = tiles_static()


def pulse_ring(k: float):
    x0, x1 = TOTAL_TILE
    g = 4 + 16 * k
    box = (x0 - g, TILE_Y0 - g, x1 + g, TILE_Y1 + g)
    im = hires((int(box[2] - box[0]) + 8, int(box[3] - box[1]) + 8),
               lambda d, q: d.rounded_rectangle((4 * q, 4 * q, (box[2] - box[0] + 4) * q, (box[3] - box[1] + 4) * q), int((20 + g) * q), outline=(*CYAN, 255), width=3 * q))
    return im, (box[0] - 4, box[1] - 4)


def clone_line():
    tw, _ = text_size(CLONE_LINE, 26, 500)
    x = W / 2 - (tw + 40) / 2
    chk = (hires((30, 30), lambda d, q: (d.ellipse((1 * q, 1 * q, 29 * q, 29 * q), fill=(*SAFE, 255)),
                                         check_mark(d, 15 * q, 15 * q, 18 * q, (*INK, 255), 3 * q))), (x, 371 + DY4))
    return [chk, text_sprite((x + 40, 370 + DY4), CLONE_LINE, 26, 500, INK_2)]


CLONE = clone_line()

CARD_Y0, CARD_Y1 = 436 + DY4, 588 + DY4
CARDS_X = [(160, 940), (980, 1760)]


def fact_card(i: int, head: str, body: str, icon_fn):
    x0, x1 = CARDS_X[i]

    def fn(img):
        rounded(img, (x0, CARD_Y0, x1, CARD_Y1), 20, fill=NAVY_2)
        tx = x0 + 112
        draw_text(img, (tx, CARD_Y0 + 24), head, 26, 700, INK)
        for j, ln in enumerate(wrap_keep_parens(body, 24, 500, x1 - tx - 30)):
            draw_text(img, (tx, CARD_Y0 + 62 + j * 31), ln, 24, 500, INK_2)
    card = layer_sprite(fn)
    icon = (hires((80, 90), icon_fn), (x0 + 22, CARD_Y0 + 30))
    return [card, icon]


def wrap_keep_parens(text: str, size: int, weight: int, max_width: int) -> list[str]:
    """Like style.wrap, but a bracketed aside such as "(no partner yet)" is never split."""
    lines, line = [], ""
    for tok in re.findall(r"\([^)]*\)|\S+", text):
        trial = f"{line} {tok}".strip()
        if text_size(trial, size, weight)[0] <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = tok
    if line:
        lines.append(line)
    return lines


def code_icon(d, q):
    w_ = 6 * q
    d.line([(26 * q, 22 * q), (8 * q, 44 * q), (26 * q, 66 * q)], fill=(*CYAN, 255), width=w_, joint="curve")
    d.line([(54 * q, 22 * q), (72 * q, 44 * q), (54 * q, 66 * q)], fill=(*CYAN, 255), width=w_, joint="curve")
    d.line([(46 * q, 18 * q), (34 * q, 70 * q)], fill=(*CYAN, 255), width=w_)


CARDS = [fact_card(0, OPS_HEAD, OPS_BODY, lambda d, q: staff_icon(d, 40 * q, 50 * q, 1.45 * q)),
         fact_card(1, LIC_HEAD, LIC_BODY, code_icon)]
for _c, (_x0, _x1) in zip(CARDS, CARDS_X):
    assert _c[0][0].height <= CARD_Y1 - CARD_Y0 + 2, "fact card text overflows"

ROAD_Y, ROAD_X0, ROAD_X1 = 702 + DY4, 150, 1770
ST_X = [300 + i * (1620 - 300) / 3 for i in range(4)]
ROAD_LABEL = text_sprite((ROAD_X0, ROAD_Y - 70), "Roadmap · 路線圖", 24, 700, INK_2)


def station_sprites(i: int):
    cx = ST_X[i]
    name, sub = STATIONS[i]
    done = i == 0

    def dot(d, q):
        if done:
            d.ellipse((2 * q, 2 * q, 38 * q, 38 * q), fill=(*CYAN, 255))
            check_mark(d, 20 * q, 20 * q, 22 * q, (*NAVY, 255), 4 * q)
        else:
            d.ellipse((2 * q, 2 * q, 38 * q, 38 * q), fill=(*NAVY, 255), outline=(*INK_2, 255), width=4 * q)
    d_ = (hires((40, 40), dot), (cx - 20, ROAD_Y - 20))
    lab = text_sprite((cx, ROAD_Y + 34), name, 26, 700, CYAN if done else INK, anchor="ma")
    out = [d_, lab]
    if sub:
        out.append(text_sprite((cx, ROAD_Y + 70), sub, 22, 500, INK_2, anchor="ma"))
    return out


STATION_SPRITES = [station_sprites(i) for i in range(4)]
ARROW_HEAD = hires((34, 40), lambda d, q: d.polygon([(0, 2 * q), (32 * q, 20 * q), (0, 38 * q)], fill=(*INK_2, 255)))

# ---------- fixed slots (chapter card, badge, footer) ----------

CHAPTER_SPRITE = layer_sprite(lambda im: chapter_card(im, CHAPTER))
BADGES_S = [(a, b, layer_sprite(lambda im, k=k, dt=dt, sub=sub: badge(im, k, dt, sub))) for a, b, k, dt, sub in BADGE_SEGMENTS]
FOOTERS_S = [(a, b, layer_sprite(lambda im, txt=txt: footer(im, txt))) for a, b, txt in FOOTER_SEGMENTS]
for _a, _b, (_im, _pos) in FOOTERS_S:
    assert _im.height < 30 and _im.width <= 1150, "footer must stay one line, at most 1150 px"


def scrim_sprite(text_fn, pad_x: int = 12, pad_y: int = 6, alpha: float = 0.8):
    """Dark rounded backing behind small grey text, used on the transparent overlay only, so the
    badge sub-line and the footer stay legible over the team's camera footage."""
    _im, (x, y) = layer_sprite(text_fn)
    box = (x - pad_x, y - pad_y, x + _im.width + pad_x, y + _im.height + pad_y)
    return layer_sprite(lambda im: rounded(im, box, 8, fill=NAVY, alpha=alpha))


def badge_sub_only(img: Image.Image, sub: str) -> None:
    """The sub-line exactly where style.badge() draws it (right edge at x 1860, y 106)."""
    sw, _ = text_size(sub, 20, 500)
    draw_text(img, (1860 - sw, 48 + 58), sub, 20, 500, INK_2)


SUB_SCRIMS = [scrim_sprite(lambda im, sub=sub: badge_sub_only(im, sub)) if sub else None for _, _, _, _, sub in BADGE_SEGMENTS]
FOOTER_SCRIMS = [scrim_sprite(lambda im, txt=txt: footer(im, txt), pad_y=5, alpha=0.92) for _, _, txt in FOOTER_SEGMENTS]


def seg_alpha(t: float, a: float, b: float, edge: float = 0.3) -> float:
    """Visible from a to b: fades in just after a, out just before b (no overlap with neighbours)."""
    if t < a or t > b:
        return 0.0
    k_in = 1.0 if a <= 0 else progress(t, a, edge)
    k_out = 1.0 if b >= DURATION else 1 - progress(t, b - edge, edge)
    return min(k_in, k_out)


def slots(img: Image.Image, t: float, scrim: bool = False) -> None:
    """Chapter card, badge with sub-line, footer. scrim=True (overlay only) backs the small grey
    sub-line and footer with a dark pill so they read over camera footage."""
    put(img, CHAPTER_SPRITE, fade(t, 0.0, CHAPTER_END, 0.3), dy=-8 * (1 - progress(t, 0, 0.3)))
    for (a, b, sp), sc in zip(BADGES_S, SUB_SCRIMS):
        al = seg_alpha(t, a, b) if a > 0 else (1.0 if t < b - 0.3 else 1 - progress(t, b - 0.3, 0.3))
        if scrim and sc is not None:
            put(img, sc, al)
        put(img, sp, al)
    for (a, b, sp), sc in zip(FOOTERS_S, FOOTER_SCRIMS):
        al = seg_alpha(t, a, b) if a > 0 else (1.0 if t < b - 0.3 else 1 - progress(t, b - 0.3, 0.3))
        if scrim:
            put(img, sc, al)
        put(img, sp, al)


# ---------- frame drawing ----------

BG = canvas(NAVY)


def part_calendar_cost(img: Image.Image, t: float) -> None:
    out = 1 - progress(t, BEATS["cost"], 0.45)        # calendar and headings leave
    k_move = progress(t, BEATS["cost"], 0.85)          # icons travel into the panel
    k_panel = progress(t, BEATS["cost"] + 0.3, 0.45)   # after the calendar has mostly gone (no text crossfade)

    if out > 0:
        put(img, SCENE, out * progress(t, 0.0, 0.5))
        for j, sp in enumerate(HEAD_L + HEAD_R):
            put(img, sp, out * progress(t, 0.05 * j, 0.4), dy=10 * (1 - progress(t, 0.05 * j, 0.4)))
        for i, (base, rings) in enumerate(PAGES):
            k = progress(t, 0.08 + 0.12 * i, 0.5)
            dy = 24 * (1 - k)
            put(img, base, out * k, dy=dy)
            put(img, rings, out * k, dy=dy)
            put(img, GLOW[i], out * k * page_active(i, t), dy=dy)
            put(img, SERVED[i], out * served_alpha(i, t), dy=dy)
        put(img, BOLTED, out * progress(t, BEATS["then_move"], 0.4), dy=8 * (1 - progress(t, BEATS["then_move"], 0.4)))

    if k_panel > 0:
        put(img, PANEL_BG, k_panel)
        for i, labs in enumerate(COST_LABELS):
            for sp in labs:
                put(img, sp, progress(t, BEATS["cost"] + 0.55 + 0.1 * i, 0.4), dy=10 * (1 - progress(t, BEATS["cost"] + 0.55 + 0.1 * i, 0.4)))
        for i, sl in enumerate(SLOTS):
            for sp in sl:
                put(img, sp, progress(t, BEATS["cost"] + 0.75 + 0.1 * i, 0.4))
        k_box = progress(t, BEATS["cost_box"], 0.45)
        for sp in COST_BOX:
            put(img, sp, k_box, dy=16 * (1 - k_box))

    # pole: bolted in place for the whole of part 1, then it travels into the panel
    pole_in = progress(t, 0.15, 0.5)
    if k_move <= 0:
        put(img, (POLE, POLE_ORIGIN), pole_in)
    else:
        s = lerp(1.0, POLE_SMALL_S, k_move)
        bx, by = lerp(POLE_AT[0], POLE_COST_BASE[0], k_move), lerp(POLE_AT[1], POLE_COST_BASE[1], k_move)
        im = POLE_SMALL if k_move >= 0.999 else scaled(POLE, s)
        put(img, (im, (bx - POLE_BASE[0] * s, by - POLE_BASE[1] * s)))

    # the phone kit
    (kx, ky), lift, on_page, k_drop = kit_state(t)
    if k_move > 0:
        kx, ky = lerp(kx, KIT_COST[0], k_move), lerp(ky, KIT_COST[1], k_move)
        lift = 0
    shadow_a = out * k_drop * (1 - min(lift, 220) / 260)
    if shadow_a > 0:
        sw = 1 - 0.45 * min(lift, 220) / 220
        sh = scaled(SHADOW, sw) if sw < 0.999 else SHADOW
        sx = kx + KIT_W / 2 - sh.width / 2
        put(img, (sh, (sx, KIT_LAND_Y + 214 - sh.height / 2 + 2)), shadow_a)
    put(img, (KIT, (kx, ky)), k_drop)
    if on_page is not None and k_move <= 0:
        act = page_active(on_page, t)
        if act > 0:
            pulse = 0.55 + 0.45 * math.sin(2 * math.pi * 1.4 * (t - BEATS["serve_one"]))
            put(img, (ARCS, (kx + KIT_W / 2 - 50, ky + KIT_PHONE_TOP - 50)), act * out * pulse)


def part_slate(img: Image.Image, t: float) -> None:
    k = progress(t, BEATS["broll"] + 0.05, 0.35)
    put(img, SLATE_SPRITES[0])
    for sp in SLATE_SPRITES[1:]:
        put(img, sp, k)
    x0, y, x1 = SLATE_BAR
    p = clamp((t - BEATS["broll"]) / (BEATS["tests"] - BEATS["broll"]))
    lay = Image.new("RGBA", (int(x1 - x0) + 2, 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((0, 0, x1 - x0, 8), 4, fill=(*NAVY_3, 255))
    if p > 0.002:
        d.rounded_rectangle((0, 0, max(8, (x1 - x0) * p), 8), 4, fill=(*WARNING, 255))
    put(img, (lay, (x0, y)), k)


def part_tests(img: Image.Image, t: float) -> None:
    t0 = BEATS["tests"]
    for i, sp in enumerate(TILE_SPRITES):
        a = progress(t, t0 + 0.08 * i, 0.35)
        put(img, sp, a, dy=14 * (1 - a))
    a_tot = progress(t, t0 + 0.32, 0.35)
    put(img, TOTAL_SPRITE, a_tot, dy=14 * (1 - a_tot))
    for i, sp in enumerate(OP_SPRITES):
        put(img, sp, progress(t, t0 + 0.1 + 0.08 * i, 0.35))

    shown = []
    tick_end = BEATS["total"] - 0.05
    for i, ((x0, x1), (_, n)) in enumerate(zip(TILES, SUITES)):
        start = t0 + 0.2 + 0.25 * i
        dur = max(0.4, tick_end - 0.75 + 0.25 * (i - 3) - start + 0.75)
        k = clamp((t - start) / dur)
        k = 1 - (1 - k) ** 3                                   # ease-out: digits settle, no overshoot
        v = int(round(n * k))
        shown.append(v)
        a = progress(t, t0 + 0.08 * i, 0.35)
        number(img, v, (x0 + x1) / 2, NUM_Y + 14 * (1 - a), alpha=a)
    tx0, tx1 = TOTAL_TILE
    number(img, sum(shown), (tx0 + tx1) / 2, NUM_Y + 14 * (1 - a_tot), big=True, alpha=a_tot)
    if BEATS["total"] <= t <= BEATS["total"] + 0.7:
        kp = (t - BEATS["total"]) / 0.7
        put(img, pulse_ring(ease(kp)), (1 - kp) * 0.9)

    a_cl = progress(t, BEATS["total"] + 0.05, 0.4)
    for sp in CLONE:
        put(img, sp, a_cl, dy=8 * (1 - a_cl))

    for i, card in enumerate(CARDS):
        a = progress(t, BEATS["facts"] + 0.18 * i, 0.45)
        for sp in card:
            put(img, sp, a, dy=16 * (1 - a))

    # roadmap: the arrow draws left to right, each station arrives as the line passes it
    tr = BEATS["roadmap"]
    put(img, ROAD_LABEL, progress(t, tr - 0.1, 0.4))
    k_line = progress(t, tr, 1.1)
    if k_line > 0:
        xe = lerp(ROAD_X0, ROAD_X1, k_line)
        lay = Image.new("RGBA", (int(xe - ROAD_X0) + 2, 8), (0, 0, 0, 0))
        ImageDraw.Draw(lay).rounded_rectangle((0, 1, xe - ROAD_X0, 6), 3, fill=(*INK_3, 255))
        put(img, (lay, (ROAD_X0, ROAD_Y - 4)))
        if k_line > 0.02:
            put(img, (ARROW_HEAD, (xe - 8, ROAD_Y - 20)), min(1.0, k_line * 6))
        for i, cx in enumerate(ST_X):
            ks = (xe - (cx - 30)) / 120
            ks = ease(clamp(ks))
            for j, sp in enumerate(STATION_SPRITES[i]):
                put(img, sp, ks, dy=(10 * (1 - ks)) if j else 0)


def foreground(t: float) -> Image.Image:
    """Transparent overlay with the fixed slots only (for compositing over the team B-roll)."""
    img = transparent()
    slots(img, t, scrim=True)
    return img


def frame_mp4(t: float) -> Image.Image:
    img = BG.copy()
    if t < BEATS["broll"]:
        part_calendar_cost(img, t)
    elif t < BEATS["tests"]:
        part_slate(img, t)
    else:
        part_tests(img, t)
    slots(img, t)
    return img


STILLS = {"chapter": 1.2, "hop": 4.45, "cost": 8.0, "slate": 11.5, "counters": 14.1, "end": 17.6}

if __name__ == "__main__":
    for k_, tt in STILLS.items():
        print(still(f"{NAME}_{k_}", frame_mp4(tt)))
    if "--stills-only" not in sys.argv:
        print(render(NAME, DURATION, frame_mp4))
        print(render_overlay(NAME, DURATION, foreground))
