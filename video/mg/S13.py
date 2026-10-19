"""S13 · One-camera counting benchmark and post-hoc calibration, shown as a lead, not proof.

The detector's systematic under-count is shown on the existing scatter plot. Twenty labelled
frames calibrate that one camera: held-out count error 13.4 → 3.3 people per frame, beside a
no-detector guess of 4.8 on the same scale. Numeric endpoints are static; only the error bar
interpolates, so an in-between animation frame cannot be mistaken for another experiment.
"One camera · not yet in the app" stays visible throughout the calibration panel.

Numbers and chart come from experiments/results/mall/ and experiments/results/uncertainty/.
Narration, duration and on-screen text come from docs/video/shotlist.json. Never show Mall imagery.
Run: .venv/bin/python video/mg/S13.py [--stills]
"""
from __future__ import annotations

import json
import math
import re
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

# ---------- timing ----------

SHOT_ID = "S13"
SHOT = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT_ID)
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)

# Guide clause boundaries (+0.2 s voice offset), measured with silencedetect on 19 Oct:
# frames / one camera 0.2–2.65; under-count 2.86–4.30; twenty-frame calibration 4.56–7.40;
# counting error 7.67–11.30; fixed guess 11.54–13.39; not in the app 13.65–15.83.
# Re-key these beats to the team's real take.
VOICE_START = 0.2           # video/assemble.py default
BEATS = {
    "card_in": 0.0,         # scatter card fades in (voice from 0.2 s)
    "two_thousand": 0.5,    # frame-count card
    "dim_apple": 0.9,       # retain the detector's own legend while dimming the Apple series
    "perfect_line": 2.2,    # before "the detector" -> dashed perfect-count line
    "under_arrow": 3.1,     # the detector under-counted
    "under_count": 3.6,
    "calibrate_in": 4.55,   # "Twenty labelled frames" -> calibration panel and scope chip
    "twenty": 4.6,
    "error": 7.65,          # "cutting counting error"
    "thirteen": 8.95,       # raw error endpoint
    "three": 9.35,          # calibrated endpoint appears directly; only the bar interpolates
    "guess": 11.55,         # "A fixed guess" -> the no-detector comparison
    "each_camera": 13.65,   # not-yet-in-app sentence emphasises the already-visible scope chip
}
BAR_SHRINK = 0.85           # only the bar moves; the printed calibrated endpoint is always 3.3
assert DURATION >= BEATS["each_camera"] + 2.5, "keep the scope disclosure readable before the cut"

# ---------- on-screen text: verbatim from the shot list ----------

_OST = [p.strip() for p in SHOT["on_screen_text"].split(" | ")]


def _field(prefix: str) -> str:
    return next(p[len(prefix):].strip() for p in _OST if p.startswith(prefix))


BADGE_KIND, BADGE_DETAIL = _field("Badge (top-right):").split(" · ", 1)   # REAL DATA | Mall benchmark
FOOTER = _field("Footer:")
GUESS_LINE = _field("Beside the counter (required, at least the limits line's size):")
CAVEAT = next(p.split(":", 1)[1].strip() for p in _OST if p.startswith("Limits line ("))

# ---------- data ----------

MALL = ROOT / "experiments" / "results" / "mall"
METRICS = json.loads((MALL / "metrics.json").read_text())
YOLO = METRICS["results"]["yolo11n"]
FRAMES = METRICS["meta"]["frames"]
CAL = YOLO["post_hoc_linear_calibration"]
HELD_OUT = CAL["held_out_frames"]
RAW_MAE = CAL["raw_mae_held_out"]
_K20 = next(k for k in CAL if re.match(r"^\d+ frames spread", k))
N_LABELLED = int(re.match(r"^(\d+)", _K20).group(1))
CAL_MAE = CAL[_K20]["mae_held_out"]
# the no-detector guess: always say the mean annotated count of the same 20 calibration frames
UNC = json.loads((ROOT / "experiments" / "results" / "uncertainty" / "metrics.json").read_text())["mall"]
GUESS_MAE = UNC["detector_free"]["mean_of_20_calibration_frames"]["mae_held_out"]      # 4.79

FRAMES_TXT = f"{FRAMES:,}"
FRAMES_LABEL = "annotated frames"
RAW_TXT, CAL_TXT = f"{RAW_MAE:.1f}", f"{CAL_MAE:.1f}"
TAG_TXT = f"{N_LABELLED} labelled frames"
PPF = "people per frame"
ERR_LABEL = "count error"

# guards: the storyboard wording must still match the data files (fails loudly if either changes)
assert BADGE_KIND in BADGES and BADGE_DETAIL == "Mall benchmark", (BADGE_KIND, BADGE_DETAIL)
assert f"{FRAMES_TXT} {FRAMES_LABEL}" in _OST
assert "boxes are people" not in SHOT["on_screen_text"]
assert f"Counter: {ERR_LABEL} {RAW_TXT} → {CAL_TXT} {PPF}, tag {TAG_TXT}" in _OST
assert "Chart labels: perfect count · under-count" in _OST
assert GUESS_LINE == f"No-detector guess: {GUESS_MAE:.1f}", GUESS_LINE
assert CAVEAT == "One camera · not yet in the app", CAVEAT
_cite = re.match(r"Mall dataset \((\w+), .*?(\d{4})\)", METRICS["meta"]["dataset"])   # (Chen, Loy, Gong & Xiang, BMVC 2012)
assert FOOTER == f"Mall dataset: {_cite.group(1)} et al., {_cite.group(2)}", FOOTER
assert all(len([w for w in x.split() if w != "·"]) <= 7 for x in (CAVEAT, FOOTER)), "short (DECLUTTER rules 3, 5)"
assert UNC["held_out_frames"] == HELD_OUT and UNC["calibration_frames"].startswith(_K20), UNC["calibration_frames"]
_unc_yolo = UNC["detectors"]["yolo11n"]                       # the same two errors, unrounded
assert round(_unc_yolo["raw_mae_held_out"], 2) == RAW_MAE and round(_unc_yolo["calibrated_20"]["mae_held_out"], 2) == CAL_MAE
# Spoken endpoints and calibration scope must match the source data.
_said = SHOT["narration"]
assert FRAMES == 2000 and "two thousand frames from one mall camera" in _said
assert "percent of its boxes" not in _said
assert N_LABELLED == 20 and "Twenty labelled frames" in _said
assert (round(RAW_MAE), round(CAL_MAE)) == (13, 3) and "from thirteen to about three people per frame" in _said
assert "calibrate that camera" in _said and "This calibration is not yet in the app." in _said
assert round(GUESS_MAE) == 5 and "A fixed guess scored about five." in _said

# ---------- colours ----------

PAPER = (252, 252, 251)           # the chart's own background, so the card and chart are seamless
BLUE_L = (96, 162, 240)           # YOLO11n blue, lightened for text and bars on navy
CHART_INK = NAVY_3                # annotations drawn on the light card

# ---------- layout ----------

TOP, BOTTOM = 140, 888            # under the badge (y 48-94), above the caption band (y 900)
COL_X0, COL_X1 = 60, 809          # left column
COL_W = COL_X1 - COL_X0
SC_X0, SC_Y0, SC_X1, SC_Y1 = 849, TOP, 1860, BOTTOM     # the light scatter card
PAD = 22
SLOT = (436, 592)                 # stage 1: one number card at a time, centred on the chart card
CALC = (TOP, BOTTOM)              # stage 2: calibration


def rgba(c, a: float = 1.0) -> tuple[int, int, int, int]:
    return (*c[:3], int(round(255 * clamp(a))))


def paste(dst: Image.Image, src: Image.Image, xy, alpha: float = 1.0) -> None:
    """alpha_composite src onto dst at integer xy, with extra opacity."""
    if alpha <= 0:
        return
    if alpha < 1:
        src = src.copy()
        src.putalpha(src.getchannel("A").point(lambda v: int(v * alpha)))
    dst.alpha_composite(src, (int(round(xy[0])), int(round(xy[1]))))


def adv(text: str, size: int, weight: int) -> float:
    """Advance width of a run of text (for chaining runs on one baseline)."""
    return text_font(text, size, weight).getlength(text)


def bar(d: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float, colour, radius: int = 10) -> None:
    """A rounded bar that can grow smoothly from zero width (the corner radius shrinks with it)."""
    if x1 - x0 < 1:
        return
    d.rounded_rectangle((x0, y0, x1, y1), max(0, min(radius, int((x1 - x0) / 2))), fill=colour)


def panel(w: int, h: int, fill=NAVY_2) -> Image.Image:
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=rgba(fill))
    return img


# ---------- the chart: dim the Apple cloud, map data to pixels ----------

CHART_SRC = Image.open(MALL / "mall_count_scatter.png").convert("RGB")
SCALE = (SC_Y1 - SC_Y0 - 2 * PAD) / CHART_SRC.height      # 1.0 for the 736x704 chart: drawn 1:1
assert SCALE <= 1.5


def grid_mapping(img: Image.Image):
    """Data -> chart-pixel mapping from the chart's own light gridlines (ticks 10..50 on both axes)."""
    a = np.asarray(img).astype(int)
    grid = (np.abs(a[..., 0] - 232) < 4) & (np.abs(a[..., 1] - 231) < 4) & (np.abs(a[..., 2] - 227) < 5)

    def centres(counts):
        idx = [i for i, c in enumerate(counts) if c > 200]
        groups, cur = [], [idx[0]]
        for i in idx[1:]:
            if i - cur[-1] <= 1:
                cur.append(i)
            else:
                groups.append(cur)
                cur = [i]
        groups.append(cur)
        return [sum(g) / len(g) + 0.5 for g in groups]       # pixel-centre convention

    xs, ys = centres(grid.sum(0)), centres(grid.sum(1))      # xs: 10..50 left to right; ys: 50..10 top to bottom
    assert len(xs) == 5 and len(ys) == 5, (xs, ys)
    kx, ky = (xs[-1] - xs[0]) / 40, (ys[-1] - ys[0]) / 40   # px per person (both positive)
    x0, y0 = xs[0] - 10 * kx, ys[-1] + 10 * ky                # pixel of the value 0 on each axis
    return lambda x, y: ((x0 + kx * x) * SCALE, (y0 - ky * y) * SCALE)


DPX = grid_mapping(CHART_SRC)


def dim_apple(src: Image.Image) -> Image.Image:
    """The Apple (orange) cloud faded towards the paper colour with a Pillow mask; pixels where an
    orange dot covers a blue one are given back their blue; the Apple legend row is faded too."""
    r, g, b = src.split()
    orange = ImageChops.subtract(r, b).point(lambda v: max(0, min(255, (v - 10) * 255 // 30)))
    faded = Image.blend(src, Image.new("RGB", src.size, PAPER), 0.78)
    out = Image.composite(faded, src, orange)
    # orange-over-blue overlaps are purple-grey (green lowest): a YOLO11n dot is underneath, so show it blue
    a = np.asarray(src).astype(float)
    purple = (a[..., 1] < a[..., 0] - 6) & (a[..., 1] < a[..., 2] - 6) & (a[..., 0] < 225)
    light = np.clip((a.mean(-1) - 95) / (PAPER[0] - 95), 0, 1)[..., None]
    blue = np.array(BLUE, float) * (1 - light) + np.array(PAPER, float) * light
    o = np.asarray(out).astype(float)
    o[purple] = blue[purple[..., None].repeat(3, -1)].reshape(-1, 3)
    out = Image.fromarray(o.round().astype(np.uint8))
    # the legend row "Apple upper-body (app fallback)": find its (orange) marker, fade the row
    om = np.asarray(orange)[:150, :220] > 128
    ys, xs = np.nonzero(om)
    row = (int(xs.min()) - 4, int(ys.min()) - 7, 480, int(ys.max()) + 8)
    reg = out.crop(row)
    out.paste(Image.blend(reg, Image.new("RGB", reg.size, PAPER), 0.72), row[:2])
    return out


def scaled(im: Image.Image) -> Image.Image:
    im = im.convert("RGBA")
    if abs(SCALE - 1) < 1e-6:
        return im
    return im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.LANCZOS)


CHART = scaled(CHART_SRC)
CHART_DIM = scaled(dim_apple(CHART_SRC))
SC_W, SC_H = SC_X1 - SC_X0, SC_Y1 - SC_Y0
CX, CY = PAD, PAD                                            # chart's top-left inside the card


def sc_base(k: float) -> Image.Image:
    img = panel(SC_W, SC_H, PAPER)
    chart = CHART if k <= 0 else CHART_DIM if k >= 1 else Image.blend(CHART, CHART_DIM, k)
    img.alpha_composite(chart, (CX, CY))
    return img


SC_BASE = sc_base(0.0)
SC_BASE_DIM = sc_base(1.0)


def cp(x: float, y: float) -> tuple[float, float]:
    """Data (annotated, detected) -> pixel inside the scatter card."""
    px, py = DPX(x, y)
    return CX + px, CY + py


LINE_END = 55.5                                              # the perfect-count line runs to the plot corner
_ANG = math.degrees(math.atan2(cp(0, 0)[1] - cp(1, 1)[1], cp(1, 1)[0] - cp(0, 0)[0]))   # ~44 deg on screen


def rotated_label(text: str) -> Image.Image:
    f = text_font(text, 24, 650)
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), text, font=f, fill=rgba(CHART_INK))
    return im.rotate(_ANG, resample=Image.BICUBIC, expand=True)


PERFECT_LABEL = rotated_label("perfect count")


def dashed(d: ImageDraw.ImageDraw, p0, p1, colour, width: int, dash: float = 14, gap: float = 9) -> None:
    (x0, y0), (x1, y1) = p0, p1
    n = math.hypot(x1 - x0, y1 - y0)
    if n < 1:
        return
    ux, uy = (x1 - x0) / n, (y1 - y0) / n
    s = 0.0
    while s < n:
        e = min(s + dash, n)
        d.line([(x0 + ux * s, y0 + uy * s), (x0 + ux * e, y0 + uy * e)], fill=colour, width=width)
        s += dash + gap


def scatter_card(t: float) -> Image.Image:
    k = progress(t, BEATS["dim_apple"], 0.8)
    img = SC_BASE.copy() if k <= 0 else SC_BASE_DIM.copy() if k >= 1 else sc_base(k)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)

    # the dashed perfect-count line: a highlighter band, then a bolder dashed line, drawn bottom-left to top-right
    p = progress(t, BEATS["perfect_line"], 0.9)
    if p > 0:
        a0, a1 = cp(0, 0), cp(LINE_END * p, LINE_END * p)
        d.line([a0, a1], fill=rgba(BLUE, 0.13), width=16)
        dashed(d, a0, a1, rgba(CHART_INK), 4)

    # the under-count: an arrow from the perfect-count line down to the top of the blue cloud
    u = progress(t, BEATS["under_arrow"], 0.6)
    if u > 0:
        ux, top = cp(45, 43.6)
        _, bot = cp(45, 31.2)
        yb = lerp(top, bot, u)
        d.line([(ux - 12, top), (ux + 12, top)], fill=rgba(CHART_INK, u), width=4)
        d.line([(ux, top), (ux, yb - 6)], fill=rgba(CHART_INK, u), width=4)
        d.polygon([(ux - 11, yb - 16), (ux + 11, yb - 16), (ux, yb + 2)], fill=rgba(CHART_INK, u))
    img.alpha_composite(lay)

    pl = progress(t, BEATS["perfect_line"] + 0.6, 0.45)
    if pl > 0:
        mx, my = cp(36, 36)
        nx, ny = -math.sin(math.radians(_ANG)), -math.cos(math.radians(_ANG))   # normal, up-left of the line
        paste(img, PERFECT_LABEL, (mx + nx * 34 - PERFECT_LABEL.width / 2, my + ny * 34 - PERFECT_LABEL.height / 2), pl)
    lu = progress(t, BEATS["under_arrow"] + 0.4, 0.45)
    if lu > 0:
        ux, _ = cp(45, 0)
        _, ym = cp(0, 37.4)
        e = progress(t, BEATS["under_count"], 0.4)            # "a steady under-count": label gets a backing pill
        if e > 0:
            tw = adv("under-count", 24, 700)
            rounded(img, (ux + 12, ym - 20, ux + 12 + tw + 24, ym + 20), 20, fill=CHART_INK, alpha=0.14 * e * lu)
        draw_text(img, (ux + 24, ym), "under-count", 24, 700, CHART_INK, lu, anchor="lm")
    return img



# ---------- left column, stage 1: one number card at a time ----------

def number_card(num: str, num_colour, label: str) -> Image.Image:
    """The spoken number, big, with its label on the same baseline."""
    w_, h_ = COL_W, SLOT[1] - SLOT[0]
    img = panel(w_, h_)
    base = 110
    draw_text(img, (36, base), num, 88, 700, num_colour, anchor="ls")
    draw_text(img, (36 + adv(num, 88, 700) + 22, base), label, 34, 600, INK, anchor="ls")
    return img


FRAMES_CARD = number_card(FRAMES_TXT, INK, FRAMES_LABEL)
assert 36 + adv(FRAMES_TXT, 88, 700) + 22 + adv(FRAMES_LABEL, 34, 600) <= COL_W - 36


# ---------- left column, stage 2: calibration ----------

CAL_W, CAL_H = COL_W, CALC[1] - CALC[0]
NUM = 92                                            # counter digits
ERR_BASE = 168                                      # "count error" (local baseline)
ROW_BASE = 300                                      # counter baseline (local)
TAG_SIZE = 26                                       # the tag is alone on the card for about 3 s: not small print
ARROW_W = int(adv(TAG_TXT, TAG_SIZE, 600)) + 36     # the tag sits on the arrow, between the numbers
GAP = 26
_row_w = adv(RAW_TXT, NUM, 700) * 2 + 2 * GAP + ARROW_W
L_RIGHT = (CAL_W - _row_w) / 2 + adv(RAW_TXT, NUM, 700)    # right edge of 13.4
A_X0, A_X1 = L_RIGHT + GAP, L_RIGHT + GAP + ARROW_W         # arrow span
R_LEFT = A_X1 + GAP                                         # left edge of the calibrated endpoint
DIGIT_MID = ROW_BASE - 34                                   # arrow height (middle of the digits)
BAR_Y0, BAR_Y1 = 396, 428                                   # count error: raw (outline) -> calibrated (solid)
BAR_X0, BAR_X1 = 36, CAL_W - 36
GUESS_Y0, GUESS_Y1 = 452, 484                               # the no-detector guess, on the same scale
GUESS_SIZE, CAVEAT_SIZE = 30, 28                            # the guess at least the limits line's size (storyboard)
assert GUESS_SIZE >= CAVEAT_SIZE
GUESS_X1 = BAR_X0 + (BAR_X1 - BAR_X0) * GUESS_MAE / RAW_MAE
assert GUESS_X1 + 18 + adv(GUESS_LINE, GUESS_SIZE, 600) <= BAR_X1, "guess label runs past the card"
CHIP = (36, 540, CAL_W - 36, 616)
assert adv(CAVEAT, CAVEAT_SIZE, 600) <= CHIP[2] - CHIP[0] - 64, "limits line runs past its chip"
CAL_BG = panel(CAL_W, CAL_H)


def cal_card(t: float) -> Image.Image:
    img = CAL_BG.copy()

    # "count error" label
    ea = progress(t, BEATS["error"], 0.45)
    draw_text(img, (CAL_W / 2, ERR_BASE), ERR_LABEL, 28, 600, INK_2, ea, anchor="ms")

    # the tag on the arrow: "20 labelled frames"
    ta = progress(t, BEATS["twenty"], 0.5)
    if ta > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        ag = progress(t, BEATS["thirteen"] + 0.15, 0.5)        # "from thirteen ... to about three"
        if ag > 0:
            ax1 = lerp(A_X0 + 18, A_X1, ag)
            dl.line([(A_X0, DIGIT_MID), (ax1 - 8, DIGIT_MID)], fill=rgba(INK_2, ta * min(1, ag * 3)), width=4)
            dl.polygon([(ax1 - 18, DIGIT_MID - 11), (ax1, DIGIT_MID), (ax1 - 18, DIGIT_MID + 11)], fill=rgba(INK_2, ta * min(1, ag * 3)))
        tw = adv(TAG_TXT, TAG_SIZE, 600)
        cx = (A_X0 + A_X1) / 2
        dl.rounded_rectangle((cx - tw / 2 - 16, DIGIT_MID - 68, cx + tw / 2 + 16, DIGIT_MID - 24), 22,
                             fill=rgba(NAVY_3, ta), outline=rgba(BLUE_L, ta), width=2)
        img.alpha_composite(lay)
        draw_text(img, (cx, DIGIT_MID - 46), TAG_TXT, TAG_SIZE, 600, INK, ta, anchor="mm")

    # the counter: 13.4 -> 3.3 people per frame
    la = progress(t, BEATS["thirteen"], 0.4)
    draw_text(img, (L_RIGHT, ROW_BASE + (1 - la) * 12), RAW_TXT, NUM, 700, INK_2, la, anchor="rs")
    cd = progress(t, BEATS["three"], BAR_SHRINK)
    ra = progress(t, BEATS["three"] - 0.15, 0.3)
    value = lerp(RAW_MAE, CAL_MAE, cd)
    draw_text(img, (R_LEFT, ROW_BASE), CAL_TXT, NUM, 700, BLUE_L, ra, anchor="ls")
    pa = progress(t, BEATS["three"] - 0.1, 0.4)
    draw_text(img, (CAL_W / 2, ROW_BASE + 46), PPF, 30, 500, INK_2, pa, anchor="ms")

    # Only the bar interpolates; the numeric 13.4 and 3.3 endpoints never count through invented values.
    g = progress(t, BEATS["thirteen"] + 0.1, 0.5)
    if g > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dl = ImageDraw.Draw(lay)
        full = BAR_X1 - BAR_X0
        cur = full * (value / RAW_MAE) * g
        if cd > 0:
            dl.rounded_rectangle((BAR_X0, BAR_Y0, BAR_X1, BAR_Y1), 10, outline=rgba(INK_3, cd), width=2)
        col = tuple(int(c) for c in lerp(GREY, BLUE_L, cd))
        bar(dl, BAR_X0, BAR_Y0, BAR_X0 + cur, BAR_Y1, rgba(col))
        img.alpha_composite(lay)

    # the no-detector guess (required, from the comparison to the end): a grey bar on the error bar's
    # scale, so 3.3 (calibrated) and 4.8 (always say 30.05, no detector) can be compared at a glance
    gg = progress(t, BEATS["guess"], 0.6)
    if gg > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bar(ImageDraw.Draw(lay), BAR_X0, GUESS_Y0, lerp(BAR_X0, GUESS_X1, gg), GUESS_Y1, rgba(GREY))
        img.alpha_composite(lay)
        draw_text(img, (GUESS_X1 + 18, (GUESS_Y0 + GUESS_Y1) / 2), GUESS_LINE, GUESS_SIZE, 600, INK,
                  progress(t, BEATS["guess"] + 0.3, 0.4), anchor="lm")

    # Scope is visible from the calibration panel's arrival, before either error value is claimed.
    ca = progress(t, BEATS["calibrate_in"], 0.5)
    if ca > 0:
        em = progress(t, BEATS["each_camera"] + 0.3, 0.45)
        rounded(img, CHIP, 18, fill=NAVY_3, alpha=ca)
        rounded(img, CHIP, 18, outline=INK, width=3, alpha=ca * lerp(0.0, 0.85, em))
        draw_text(img, ((CHIP[0] + CHIP[2]) / 2, (CHIP[1] + CHIP[3]) / 2), CAVEAT, CAVEAT_SIZE, 600, INK, ca, anchor="mm")
    return img


# ---------- frame ----------

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()

    # right: the chart card (dimmed in stage 2, so the eye moves to the calibration)
    a_sc = progress(t, BEATS["card_in"], 0.6)
    card = scatter_card(t)
    dim2 = progress(t, BEATS["calibrate_in"], 0.6)
    if dim2 > 0:
        rounded(card, (0, 0, SC_W - 1, SC_H - 1), 22, fill=NAVY, alpha=0.45 * dim2)
    paste(img, card, (SC_X0 + (1 - a_sc) * 26, SC_Y0), a_sc)

    # The frame-count card gives way directly to calibration; precision is supporting evidence.
    out1 = progress(t, BEATS["calibrate_in"], 0.3)
    a1 = progress(t, BEATS["two_thousand"] - 0.25, 0.5) * (1 - out1)
    if a1 > 0:
        paste(img, FRAMES_CARD, (COL_X0 + (1 - progress(t, BEATS["two_thousand"] - 0.25, 0.5)) * 24 - 40 * out1, SLOT[0]), a1)

    # left, stage 2: calibration
    a_cal = progress(t, BEATS["calibrate_in"] + 0.35, 0.5)
    if a_cal > 0:
        paste(img, cal_card(t), (COL_X0 + (1 - a_cal) * 24, CALC[0]), a_cal)

    # overlay slots: badge, legend strip (S10-S16), citation footer; no chapter card, captions or lower-third here
    badge(img, BADGE_KIND, BADGE_DETAIL, alpha=progress(t, 0.0, 0.35))
    legend_strip(img)
    footer(img, FOOTER, progress(t, 0.2, 0.4))
    return img


STILLS = {
    "open": 1.5,           # chart in, Apple dimming, 2,000 annotated frames
    "scatter": 4.3,        # under-count, before calibration
    "tag": 5.6,            # calibration scope disclosed before either error endpoint
    "transition": BEATS["three"] + 0.55,  # moving bar, static 3.3 endpoint
    "counter": 13.2,       # calibrated error beside the no-detector guess
    "limits": DURATION - 0.05,  # scope disclosure held to the cut
}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        print(still(f"S13_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render("S13", DURATION, draw_frame))
