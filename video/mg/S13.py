"""Shot S13 (2:17.0-2:34.5, 17.5 s): 2,000 annotated mall frames, a steady under-count, and a
post-hoc calibration shown as a lead, not proof, beside a guess that uses no detector.

Storyboard: docs/video/script.md, section 3 row S13, section 4 claims row S13, section 6 ("Global
look and tools", "motion_graphic", "figure" S13, "On-screen text load"). Shot list:
docs/video/shotlist.json (id S13). Badge: REAL DATA · Mall research benchmark · charts only.

Layout (no chapter card: the "Does it work?" card belongs to S10; no lower-third: [MEMBER 1]'s
is in S02):
  right   the repo chart mall_count_scatter.png at 1:1 on a light card. The orange Apple cloud is
          dimmed with a Pillow mask (and its legend row faded); the blue cloud is labelled
          "YOLO11n, the app default"; the dashed perfect-count line is traced and labelled; an
          arrow marks the gap between the line and the cloud (the under-count), on "steadily
          under-counted".
  left    stage 1: "2,000 annotated frames", then "count vs annotated count: 59% · 93% of boxes
          are people" (93% on "ninety-three percent"; 59% is no longer spoken), then near /
          middle / far recall bars.
          stage 2 (from "Twenty labelled frames"): the schematic "true ≈ a × detected + b", the
          "20 labelled frames" tag, the counter 13.4 → 3.3 people per frame over an error bar,
          the no-detector guess as a second bar on the same scale with its label "a fixed guess,
          no detector: 4.8" (28 px, larger than the 26 px limits line; from the countdown to the
          end), and the limits line (from "that one camera" to the end).
  Nothing is drawn in the caption band (y 900-995).

Never any Mall imagery: only the chart is used (it contains no dataset frame).

Data (read at render time, never retyped):
  experiments/results/mall/mall_count_scatter.png       the chart (data-to-pixel mapping measured
                                                         from its own gridlines)
  experiments/results/mall/metrics.json
    meta.frames                                          2,000 annotated frames
    results.yolo11n.share_found                          59% (count vs annotated count)
    results.yolo11n.precision                            93% of boxes are people
    results.yolo11n.recall_by_image_region               near 78% / middle 64% / far 42%
    results.yolo11n.post_hoc_linear_calibration
      .held_out_frames                                   801-2000
      .raw_mae_held_out                                  13.4 people per frame
      ."20 frames spread over 1-800".mae_held_out        3.3 people per frame (20 labelled frames)
  experiments/results/uncertainty/metrics.json (summary.md, section 6)
    mall.detector_free.mean_of_20_calibration_frames.mae_held_out    4.8 (4.79): always say 30.05
  docs/video/shotlist.json                               duration, narration and the verbatim
                                                         on-screen lines (badge, bar title, guess,
                                                         caveat, footer)

Run: .venv/bin/python video/mg/S13.py            -> video/build/mg/S13.mp4 + stills
     .venv/bin/python video/mg/S13.py --stills   (stills only, for checking the layout)
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
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)   # 17.5 s

# Seconds from the shot start, keyed to the guide voice video/build/guide/S13.wav (say -v Daniel
# -r 155, 15.78 s) laid from VOICE_START: word times from its pauses (silencedetect: 2.40-2.62,
# 4.49-4.71, 7.54-7.79, 10.64-10.91, 14.09-14.33, 14.72-14.94 s into the file) and prefix
# syntheses, 17 Oct. Shot times: "On two thousand annotated mall frames," 0.2-2.6 | "the detector
# steadily under-counted," 2.8-4.7 ("steadily" 3.5) | "yet ninety-three percent of its boxes were
# people." 4.9-7.7 ("ninety-three" 5.3) | "Twenty labelled frames calibrated that one camera," 8.0-10.8
# ("calibrated" 9.5, "that one camera" 9.9) | "cutting error from thirteen to about three people per
# frame." 11.1-14.3 ("thirteen" 12.2, "three" 13.0-13.4) | "A lead, not proof." 14.5-16.0.
# The storyboard's times (calibration from about 7.7 s, limits line from about 9.5 s, counter on
# about 12.0-13.7 s) are at 140 wpm. Re-key to the real voice take.
VOICE_START = 0.2           # video/assemble.py default
BEATS = {
    "card_in": 0.0,         # scatter card fades in (voice from 0.2 s)
    "two_thousand": 0.5,    # "two thousand annotated mall frames" (0.5-2.6) -> frames card
    "dim_apple": 0.9,       # "annotated" (1.1) -> orange Apple cloud dims
    "yolo_label": 1.5,      # "mall frames" (1.7) -> the blue cloud is labelled
    "perfect_line": 2.2,    # before "the detector" (2.8) -> dashed perfect-count line traced
    "under_arrow": 3.45,    # "steadily under-counted" (3.5-4.7) -> under-count arrow and its label
    "under_count": 4.0,     # "under-counted" (4.0) -> arrow label emphasised
    "count_card": 4.45,     # end of "under-counted," -> count card, 59% (on screen only)
    "ninety_three": 5.3,    # "ninety-three percent of its boxes" (5.3)
    "recall_bars": 5.5,     # "of its boxes were people" -> near / middle / far recall bars (the cause)
    "calibrate_in": 8.3,    # stage 2, during "Twenty labelled frames" (8.0-9.5)
    "twenty": 8.7,          # "labelled frames" (8.5-9.5) -> "20 labelled frames" tag
    "formula": 9.45,        # "calibrated" (9.5) -> true ≈ a × detected + b
    "one_camera": 9.85,     # "that one camera" (9.9-10.8) -> calibration limits line, to the end
    "error": 11.1,          # "cutting error" (11.1-11.8) -> "count error" label
    "thirteen": 12.05,      # "from thirteen" ("thirteen" 12.2) -> 13.4, the error bar fills
    "three": 12.5,          # "to about three" (12.5; "three" 13.0-13.4) -> counts down to 3.3 by 13.35
    "guess": 12.5,          # the same moment, to the end: the no-detector guess bar and its label
    "lead": 14.5,           # "A lead, not proof." (14.5-16.0) -> limits line emphasised
}
COUNT_DOWN = 0.85           # 13.4 -> 3.3 takes this long, landing on "three"

# ---------- on-screen text: verbatim from the shot list ----------

_OST = [p.strip() for p in SHOT["on_screen_text"].split(" | ")]


def _field(prefix: str) -> str:
    return next(p[len(prefix):].strip() for p in _OST if p.startswith(prefix))


BADGE_KIND, BADGE_DETAIL = _field("Badge (top-right):").split(" · ", 1)   # REAL DATA | Mall research ...
BAR_TITLE = _field("Bar title:")
FOOTER = _field("Footer:")
COUNT_LINE = next(p for p in _OST if p.startswith("count vs annotated count"))
CAVEAT = next(p for p in _OST if p.startswith("Calibration:"))
GUESS_LINE = _field("Beside the counter (required, at least the limits line's size):")

# ---------- data ----------

MALL = ROOT / "experiments" / "results" / "mall"
METRICS = json.loads((MALL / "metrics.json").read_text())
YOLO = METRICS["results"]["yolo11n"]
FRAMES = METRICS["meta"]["frames"]
COUNT_PCT = round(100 * YOLO["share_found"])
PREC_PCT = round(100 * YOLO["precision"])
_REG = YOLO["recall_by_image_region"]
REGIONS = []  # (label, part of the image, recall %, band index 0 = top third)
for label, part, band in (("near", "bottom third", 2), ("middle", "middle third", 1), ("far", "top third", 0)):
    key = next(k for k in _REG if k.startswith(label))
    REGIONS.append((label, part, round(100 * _REG[key]["recall"]), band))
CAL = YOLO["post_hoc_linear_calibration"]
HELD_OUT = CAL["held_out_frames"]
RAW_MAE = CAL["raw_mae_held_out"]
_K20 = next(k for k in CAL if re.match(r"^\d+ frames spread", k))
N_LABELLED = int(re.match(r"^(\d+)", _K20).group(1))
CAL_MAE = CAL[_K20]["mae_held_out"]
# the no-detector guess: always say the mean annotated count of the same 20 calibration frames
UNC = json.loads((ROOT / "experiments" / "results" / "uncertainty" / "metrics.json").read_text())["mall"]
GUESS_MAE = UNC["detector_free"]["mean_of_20_calibration_frames"]["mae_held_out"]      # 4.79

# guards: the storyboard wording must still match the data files (fails loudly if either changes)
assert BADGE_KIND in BADGES, BADGE_KIND
assert COUNT_LINE == f"count vs annotated count: {COUNT_PCT}% · {PREC_PCT}% of boxes are people", COUNT_LINE
assert CAVEAT == f"Calibration: post-hoc · one camera · held-out frames {HELD_OUT} · not yet in the app", CAVEAT
assert GUESS_LINE == f"a fixed guess, no detector: {GUESS_MAE:.1f}", GUESS_LINE
assert UNC["held_out_frames"] == HELD_OUT and UNC["calibration_frames"].startswith(_K20), UNC["calibration_frames"]
_unc_yolo = UNC["detectors"]["yolo11n"]                       # the same two errors, unrounded
assert round(_unc_yolo["raw_mae_held_out"], 2) == RAW_MAE and round(_unc_yolo["calibrated_20"]["mae_held_out"], 2) == CAL_MAE
assert f"{RAW_MAE:.1f} → {CAL_MAE:.1f} people per frame" in SHOT["visual"]
assert f"'{N_LABELLED} labelled frames'" in SHOT["visual"]
assert "(" + " / ".join(str(r[2]) for r in REGIONS) + "%)" in SHOT["visual"]
assert f"no-detector guess ({GUESS_MAE:.1f})" in SHOT["visual"]
# spoken: "two thousand", "93 percent", "Twenty labelled frames", "from thirteen to about three"
_said = SHOT["narration"]
assert FRAMES == 2000 and "two thousand annotated mall frames" in _said
assert f"{PREC_PCT} percent of its boxes were people" in _said and f"{COUNT_PCT} percent" not in _said
assert N_LABELLED == 20 and "Twenty labelled frames" in _said
assert (round(RAW_MAE), round(CAL_MAE)) == (13, 3) and "from thirteen to about three people per frame" in _said
assert "that one camera" in _said and _said.endswith("A lead, not proof.")

FRAMES_TXT = f"{FRAMES:,}"
COUNT_LABEL, PREC_LABEL = "count vs annotated count:", "of boxes are people"
RAW_TXT, CAL_TXT = f"{RAW_MAE:.1f}", f"{CAL_MAE:.1f}"
TAG_TXT = f"{N_LABELLED} labelled frames"
PPF = "people per frame"
YOLO_LABEL = ("YOLO11n,", "the app default")
FORMULA = [("true", "ink"), (" ≈ ", "dim"), ("a", "blue"), (" × ", "dim"), ("detected", "ink"), (" + ", "dim"), ("b", "blue")]

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
CARD1 = (TOP, TOP + 156)          # "2,000 annotated frames"
CARD2 = (316, 556)                # count vs annotated count / boxes that are people
CARD3 = (576, BOTTOM)             # recall bars
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


def yolo_pill() -> Image.Image:
    w_ = int(max(adv(YOLO_LABEL[0], 24, 700), adv(YOLO_LABEL[1], 24, 600))) + 36
    im = Image.new("RGBA", (w_, 76), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w_ - 1, 75), 16, fill=rgba(BLUE))
    draw_text(im, (18, 10), YOLO_LABEL[0], 24, 700, (255, 255, 255))
    draw_text(im, (18, 40), YOLO_LABEL[1], 24, 600, (255, 255, 255))
    return im


YOLO_PILL = yolo_pill()


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

    # YOLO11n label: leader from the cloud's right edge to the pill in the card's right gutter
    q = progress(t, BEATS["yolo_label"], 0.6)
    lx, ly = cp(50.6, 26)
    pill_x = CX + CHART.width + 14
    if q > 0:
        d.ellipse((lx - 6, ly - 6, lx + 6, ly + 6), fill=rgba(BLUE, q))
        d.line([(lx, ly), (lerp(lx, pill_x, q), ly)], fill=rgba(BLUE, q), width=3)

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

    if q > 0:
        paste(img, YOLO_PILL, (pill_x + (1 - q) * 16, ly - YOLO_PILL.height / 2), q)
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


# ---------- left column, stage 1 ----------

def card1(t: float) -> Image.Image:
    w_, h_ = COL_W, CARD1[1] - CARD1[0]
    img = panel(w_, h_)
    base = 106                                                 # shared baseline of the number and the second line
    draw_text(img, (36, base), FRAMES_TXT, 88, 700, INK, anchor="ls")
    x = 36 + adv(FRAMES_TXT, 88, 700) + 24                     # a two-line stack to the right of the number
    draw_text(img, (x, base - 40), "annotated frames", 34, 500, INK_2, anchor="ls")
    d = ImageDraw.Draw(img)
    d.ellipse((x + 1, base - 17, x + 17, base - 1), fill=rgba(BLUE_L))
    draw_text(img, (x + 28, base), "each dot = one frame", 24, 500, INK_2, anchor="ls")
    return img


CARD1_IMG = card1(0)


def card2(t: float) -> Image.Image:
    w_, h_ = COL_W, CARD2[1] - CARD2[0]
    img = panel(w_, h_)
    a1 = progress(t, BEATS["count_card"] + 0.1, 0.4)        # 59%: on screen only, no longer spoken
    a2 = progress(t, BEATS["ninety_three"] - 0.05, 0.4)
    y1, y2 = 104, 196
    draw_text(img, (36, y1), COUNT_LABEL, 34, 600, INK, anchor="ls")
    draw_text(img, (36 + adv(COUNT_LABEL, 34, 600) + 16, y1 + (1 - a1) * 14), f"{COUNT_PCT}%", 76, 700, BLUE_L, a1, anchor="ls")
    n2 = f"{PREC_PCT}%"
    draw_text(img, (36, y2 + (1 - a2) * 14), n2, 76, 700, BLUE_L, a2, anchor="ls")
    draw_text(img, (36 + adv(n2, 76, 700) + 16, y2), PREC_LABEL, 34, 600, INK, a2, anchor="ls")
    return img


ROW_Y0, ROW_H = 96, 66            # first bar row (local y) and row pitch in card 3
TRACK_X0, TRACK_X1 = 262, 612
GLYPH_X = 196


def card3_static() -> Image.Image:
    w_, h_ = COL_W, CARD3[1] - CARD3[0]
    img = panel(w_, h_)
    draw_text(img, (36, 32), BAR_TITLE, 24, 700, INK, max_width=w_ - 72)
    d = ImageDraw.Draw(img)
    for i, (label, part, _, band) in enumerate(REGIONS):
        y = ROW_Y0 + i * ROW_H
        draw_text(img, (36, y + 22), label, 28, 650, INK, anchor="ls")
        draw_text(img, (36, y + 48), part, 20, 500, INK_3, anchor="ls")
        # a tiny camera image split into thirds, the region of this row filled
        gx0, gy0, gx1, gy1 = GLYPH_X, y, GLYPH_X + 44, y + 33
        d.rounded_rectangle((gx0, gy0, gx1, gy1), 5, outline=rgba(INK_3), width=2)
        bh = (gy1 - gy0) / 3
        d.rectangle((gx0 + 3, gy0 + 3 + band * bh - (1 if band else 0), gx1 - 3, gy0 + (band + 1) * bh - (3 if band == 2 else 0)),
                    fill=rgba(BLUE_L, 0.85))
        d.rounded_rectangle((TRACK_X0, y, TRACK_X1, y + 34), 10, fill=rgba(NAVY_3))
    return img


CARD3_BG = card3_static()


def card3(t: float) -> Image.Image:
    img = CARD3_BG.copy()
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (_, _, pct, _) in enumerate(REGIONS):
        y = ROW_Y0 + i * ROW_H
        g = progress(t, BEATS["recall_bars"] + 0.3 + 0.15 * i, 0.9)
        xe = TRACK_X0 + (TRACK_X1 - TRACK_X0) * pct / 100 * g
        bar(d, TRACK_X0, y, xe, y + 34, rgba(BLUE_L))
    img.alpha_composite(lay)
    for i, (_, _, pct, _) in enumerate(REGIONS):
        y = ROW_Y0 + i * ROW_H
        a = progress(t, BEATS["recall_bars"] + 0.3 + 0.15 * i + 0.75, 0.35)
        draw_text(img, (TRACK_X1 + 20, y + 17), f"{pct}%", 32, 700, INK, a, anchor="lm")
    return img


# ---------- left column, stage 2: calibration ----------

CAL_W, CAL_H = COL_W, CALC[1] - CALC[0]
NUM = 92                                            # counter digits
ROW_BASE = 352                                      # counter baseline (local)
ARROW_W = int(adv(TAG_TXT, 22, 600)) + 36           # the tag sits on the arrow, between the numbers
GAP = 26
_row_w = adv(RAW_TXT, NUM, 700) * 2 + 2 * GAP + ARROW_W
L_RIGHT = (CAL_W - _row_w) / 2 + adv(RAW_TXT, NUM, 700)    # right edge of 13.4
A_X0, A_X1 = L_RIGHT + GAP, L_RIGHT + GAP + ARROW_W         # arrow span
R_LEFT = A_X1 + GAP                                         # left edge of the counting number
DIGIT_MID = ROW_BASE - 34                                   # arrow height (middle of the digits)
BAR_Y0, BAR_Y1 = 440, 472                                   # count error: raw (outline) -> calibrated (solid)
BAR_X0, BAR_X1 = 36, CAL_W - 36
GUESS_Y0, GUESS_Y1 = 496, 528                               # the no-detector guess, on the same scale
GUESS_SIZE = 28                                             # >= the limits line's 26 px (storyboard)
GUESS_X1 = BAR_X0 + (BAR_X1 - BAR_X0) * GUESS_MAE / RAW_MAE
assert GUESS_X1 + 18 + adv(GUESS_LINE, GUESS_SIZE, 600) <= BAR_X1, "guess label runs past the card"
CHIP = (36, 572, CAL_W - 36, 700)


def caveat_lines(width: int) -> list[tuple[str, str]]:
    """The caveat wrapped to `width` at 26 px, with its first word "Calibration:" in bold."""
    head, rest = CAVEAT.split(" ", 1)
    lines, line, room = [], "", width - adv(head + " ", 26, 700)
    for word in rest.split():
        trial = f"{line} {word}".strip()
        if adv(trial, 26, 500) <= room or not line:
            line = trial
        else:
            lines.append(line)
            line, room = word, width
    lines.append(line)
    return [(head, lines[0])] + [("", ln) for ln in lines[1:]]


CAVEAT_LINES = caveat_lines(CHIP[2] - CHIP[0] - 64)


def cal_static() -> Image.Image:
    return panel(CAL_W, CAL_H)


CAL_BG = cal_static()


def cal_card(t: float) -> Image.Image:
    img = CAL_BG.copy()
    d = ImageDraw.Draw(img)

    # schematic: true ≈ a × detected + b
    fa = progress(t, BEATS["formula"], 0.5)
    if fa > 0:
        total = sum(adv(s, 52, 600) for s, _ in FORMULA)
        x = (CAL_W - total) / 2
        for s, kind in FORMULA:
            col = {"ink": INK, "dim": INK_2, "blue": BLUE_L}[kind]
            draw_text(img, (x, 112 + (1 - fa) * 12), s, 52, 600, col, fa, anchor="ls")
            x += adv(s, 52, 600)

    # "count error" label
    ea = progress(t, BEATS["error"], 0.45)
    draw_text(img, (CAL_W / 2, 210), "count error", 26, 600, INK_2, ea, anchor="ms")

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
        tw = adv(TAG_TXT, 22, 600)
        cx = (A_X0 + A_X1) / 2
        dl.rounded_rectangle((cx - tw / 2 - 14, DIGIT_MID - 62, cx + tw / 2 + 14, DIGIT_MID - 24), 19,
                             fill=rgba(NAVY_3, ta), outline=rgba(BLUE_L, ta), width=2)
        img.alpha_composite(lay)
        draw_text(img, (cx, DIGIT_MID - 43), TAG_TXT, 22, 600, INK, ta, anchor="mm")

    # the counter: 13.4 -> 3.3 people per frame
    la = progress(t, BEATS["thirteen"], 0.4)
    draw_text(img, (L_RIGHT, ROW_BASE + (1 - la) * 12), RAW_TXT, NUM, 700, INK_2, la, anchor="rs")
    cd = progress(t, BEATS["three"], COUNT_DOWN)
    ra = progress(t, BEATS["three"] - 0.15, 0.3)
    value = lerp(RAW_MAE, CAL_MAE, cd)
    draw_text(img, (R_LEFT, ROW_BASE), f"{value:.1f}", NUM, 700, tuple(int(c) for c in lerp(INK_2, BLUE_L, cd)), ra, anchor="ls")
    pa = progress(t, BEATS["three"] + COUNT_DOWN - 0.1, 0.4)
    draw_text(img, (CAL_W / 2, ROW_BASE + 46), PPF, 30, 500, INK_2, pa, anchor="ms")

    # error bar: the raw error stays as an outline; the solid bar follows the counter
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

    # the no-detector guess (required, from the countdown to the end): a grey bar on the error bar's
    # scale, so 3.3 (calibrated) and 4.8 (always say 30.05, no detector) can be compared at a glance
    gg = progress(t, BEATS["guess"], 0.6)
    if gg > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        bar(ImageDraw.Draw(lay), BAR_X0, GUESS_Y0, lerp(BAR_X0, GUESS_X1, gg), GUESS_Y1, rgba(GREY))
        img.alpha_composite(lay)
        draw_text(img, (GUESS_X1 + 18, (GUESS_Y0 + GUESS_Y1) / 2), GUESS_LINE, GUESS_SIZE, 600, INK,
                  progress(t, BEATS["guess"] + 0.3, 0.4), anchor="lm")

    # caveat chip; its outline brightens on "A lead, not proof."
    ca = progress(t, BEATS["one_camera"], 0.5)
    if ca > 0:
        em = progress(t, BEATS["lead"], 0.45)
        x0, y0, x1, y1 = CHIP
        rounded(img, CHIP, 18, fill=NAVY_3, alpha=ca)
        rounded(img, CHIP, 18, outline=INK, width=3, alpha=ca * lerp(0.0, 0.85, em))
        n = len(CAVEAT_LINES)
        y = (y0 + y1) / 2 - (n - 1) * 19 + 10
        for i, (head, body) in enumerate(CAVEAT_LINES):
            x = x0 + 32
            if head:
                draw_text(img, (x, y + i * 38), head, 26, 700, INK, ca, anchor="ls")
                x += adv(head + " ", 26, 700)
            draw_text(img, (x, y + i * 38), body, 26, 500, INK, ca, anchor="ls")
    return img


# ---------- frame ----------

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()

    # right: the chart card (dimmed a little in stage 2, so the eye moves to the calibration)
    a_sc = progress(t, BEATS["card_in"], 0.6)
    card = scatter_card(t)
    dim2 = progress(t, BEATS["calibrate_in"], 0.6)
    if dim2 > 0:
        rounded(card, (0, 0, SC_W - 1, SC_H - 1), 22, fill=NAVY, alpha=0.18 * dim2)
    paste(img, card, (SC_X0 + (1 - a_sc) * 26, SC_Y0), a_sc)

    # left, stage 1: frames -> count / boxes -> recall bars; they leave as stage 2 starts
    for i, (beat, y0, maker) in enumerate(((BEATS["two_thousand"], CARD1[0], lambda tt: CARD1_IMG),
                                           (BEATS["count_card"], CARD2[0], card2),
                                           (BEATS["recall_bars"], CARD3[0], card3))):
        a_in = progress(t, beat - 0.25, 0.5)
        out = progress(t, BEATS["calibrate_in"] + 0.05 * i, 0.4)
        a = a_in * (1 - out)
        if a > 0:
            paste(img, maker(t), (COL_X0 + (1 - a_in) * 24 - 50 * out, y0), a)

    # left, stage 2: calibration
    a_cal = progress(t, BEATS["calibrate_in"] + 0.35, 0.5)
    if a_cal > 0:
        paste(img, cal_card(t), (COL_X0 + (1 - a_cal) * 24, CALC[0]), a_cal)

    # overlay slots: badge, legend strip (S10-S16), footer; no chapter card, captions or lower-third here
    badge(img, BADGE_KIND, BADGE_DETAIL, alpha=progress(t, 0.0, 0.35))
    legend_strip(img)
    footer(img, FOOTER, progress(t, 0.2, 0.4))
    return img


STILLS = {
    "open": 1.5,           # chart in, Apple dimming, 2,000 annotated frames
    "scatter": 4.3,        # dimmed, labelled, perfect line traced, under-count arrow
    "count": 6.0,          # count vs annotated count 59% · 93% of boxes are people, recall bars growing
    "recall": 8.2,         # near / middle / far recall bars, just before stage 2
    "formula": 10.8,       # tag, schematic, limits line
    "counter": 17.45,      # 13.4 -> 3.3 people per frame beside the guess, limits line emphasised
}

if __name__ == "__main__":
    for name, ts in STILLS.items():
        print(still(f"S13_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render("S13", DURATION, draw_frame))
