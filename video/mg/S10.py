"""Shot S10 (1:28.0-1:50.0, 22.0 s): "Does it work? Every result is labelled."

Storyboard: docs/video/script.md section 3, row S10; claims table section 4, rows S10; shot list
docs/video/shotlist.json (id S10).

0-1.5 s   the five evidence badges appear centre-screen, then shrink and dock as the bottom-right
          legend strip (style.legend_strip), where they stay for the rest of the shot.
then      grouped macro-F1 bars, model vs "no change", at 3 decimals, +15 pair highlighted, no gap labels.
then      "91% vs 79% of critical minutes caught (+15 min)".
then      flagged as uncertain vs the rest (+15 min).
Badge SIMULATED pinned. Secondary figures (recall at 3 decimals, flagged share, other horizons'
gating, the stress day) stay off screen.

Data (read, never retyped):
  ml/models/metrics.json
    per_horizon.h5/h10/h15.test.f1_macro                      model macro-F1
    per_horizon.h5/h10/h15.persistence_baseline.test.f1_macro  "no change" macro-F1
    per_horizon.h15.test.per_class.CRITICAL.recall             91%
    per_horizon.h15.persistence_baseline.test.per_class.CRITICAL.recall   79%
    per_horizon.h15.confidence_gating.accuracy_flagged / accuracy_confident   56% / 97%
    split_days (train / val / test day lists)                  footer 14 days: 9 / 2 / 3

Run: .venv/bin/python video/mg/S10.py   -> video/build/mg/S10.mp4 and stills in video/build/mg/stills/
"""
from __future__ import annotations

import json
from functools import lru_cache
import sys

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageChops, ImageDraw  # noqa: E402

# ---------- timing ----------

SHOT = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
SHOT = next(s for s in SHOT if s["id"] == "S10")
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 22.0 s

# Seconds from the shot start. Guide timing: voice from 1.0 s at 140 wpm (0.43 s per spoken word,
# numbers read as words: "an F one of point eight six five ..."). re-key to the real voice take.
BEATS = {
    "legend_in": 0.0,          # five badges appear centre-screen (no voice yet)
    "legend_dock": 0.85,       # they shrink and dock bottom-right, docked by 1.5 s
    "voice_on": 1.0,           # "On held-out simulated days,"
    "chart_in": 1.3,           # macro-F1 panel fades in; bars grow left to right
    "fifteen_minute": 2.7,     # "fifteen-minute forecasts" -> +15 pair highlighted
    "f1_model": 5.7,           # "point eight six five"
    "f1_nochange": 7.85,       # "against point seven nine five"
    "and_catch": 11.3,         # "and catch" -> chart slides left, critical-minutes card in
    "ninety_one": 12.15,       # "ninety-one percent of critical minutes"
    "seventy_nine": 14.3,      # "against seventy-nine"
    "flagged": 15.15,          # "Forecasts flagged as uncertain"
    "right_only": 17.3,        # "are right only about" -> flagged bar grows, "right 56%" lands
    "fifty_six": 18.55,        # "fifty-six percent of the time"
    "the_rest": 20.7,          # "the rest, ninety-seven" (97% must be readable before the cut at 22.0)
}
CHAPTER_END = 2.0              # chapter card shown for about 2 s

# ---------- data ----------

METRICS = json.loads((ROOT / "ml" / "models" / "metrics.json").read_text())
HORIZONS = METRICS["horizons"]                                   # [5, 10, 15]
PH = METRICS["per_horizon"]
F1_MODEL = [PH[f"h{h}"]["test"]["f1_macro"] for h in HORIZONS]
F1_BASE = [PH[f"h{h}"]["persistence_baseline"]["test"]["f1_macro"] for h in HORIZONS]
H15 = PH[f"h{HORIZONS[-1]}"]
CRIT_MODEL = round(100 * H15["test"]["per_class"]["CRITICAL"]["recall"])
CRIT_BASE = round(100 * H15["persistence_baseline"]["test"]["per_class"]["CRITICAL"]["recall"])
GATE = H15["confidence_gating"]
ACC_FLAGGED = round(100 * GATE["accuracy_flagged"])
ACC_REST = round(100 * GATE["accuracy_confident"])
SPLIT = METRICS["split_days"]
N_TRAIN, N_VAL, N_TEST = len(SPLIT["train"]), len(SPLIT["val"]), len(SPLIT["test"])

# guard: the spoken narration must match the data file (fails loudly if metrics.json changes)
_spoken = SHOT["narration"]
for v in (f"{F1_MODEL[-1]:.3f}", f"{F1_BASE[-1]:.3f}", f"{CRIT_MODEL} percent", f"against {CRIT_BASE}",
          f"{ACC_FLAGGED} percent", f"the rest, {ACC_REST}"):
    assert v in _spoken, f"metrics.json no longer matches the narration: {v!r}"

# ---------- on-screen text (storyboard wording) ----------

CHAPTER = "Does it work? Every result is labelled."
AXIS = "macro-F1 (0-1): how well SAFE, WARNING and CRITICAL are all predicted"
LEG_MODEL = "model"
LEG_BASE = "no change: the level stays as it is now"
CRIT_LINE = "of critical minutes caught (+15 min)"
FLAG_LABEL, FLAG_VALUE = "flagged as uncertain:", f"right {ACC_FLAGGED}%"
REST_LABEL, REST_VALUE = "the rest:", f"{ACC_REST}%"
H_TAG = "(+15 min)"
FOOTER = (f"ml/models/metrics.json · {N_TRAIN + N_VAL + N_TEST} simulated days, split by day: "
          f"{N_TRAIN} train / {N_VAL} validate / {N_TEST} test")

MODEL_C = CYAN
BASE_C = GREY

# ---------- layout ----------

CH_W, CH_H = 1040, 630            # macro-F1 panel
CH_Y = 160
CH_X_CENTRE = (W - CH_W) // 2     # 440 while it is the only element
CH_X_LEFT = 60                    # after "and catch"
COL_X0, COL_X1 = 1160, 1860       # right column
CA_Y0, CA_Y1 = 160, 450           # critical-minutes card
CB_Y0, CB_Y1 = 480, 790           # flagged-vs-rest card

# plot geometry inside the panel (local coordinates)
P_X0, P_X1 = 110, 1000
P_TOP, P_BOT = 196, 540           # value 1.0 and value 0.0
BAR_W, BAR_GAP = 100, 14
VAL_GAP = 22                      # value label baseline above the bar top
GROUP_W = (P_X1 - P_X0) / len(HORIZONS)


def ypos(v: float) -> float:
    return P_BOT - v * (P_BOT - P_TOP)


def group_cx(i: int) -> float:
    return P_X0 + GROUP_W * (i + 0.5)


def bar_box(i: int, j: int, v: float) -> tuple[float, float, float, float]:
    """Bar j (0 = model, 1 = no change) of group i, height for value v."""
    cx = group_cx(i)
    x0 = cx - BAR_GAP / 2 - BAR_W if j == 0 else cx + BAR_GAP / 2
    return (x0, ypos(v), x0 + BAR_W, P_BOT)


# ---------- helpers ----------

def rgba(c, a: float) -> tuple[int, int, int, int]:
    return (*c[:3], int(round(255 * clamp(a))))


def paste(dst: Image.Image, src: Image.Image, xy, alpha: float = 1.0) -> None:
    """alpha_composite src onto dst at integer xy, with extra opacity."""
    if alpha <= 0:
        return
    if alpha < 1:
        src = src.copy()
        src.putalpha(src.getchannel("A").point(lambda v: int(v * alpha)))
    dst.alpha_composite(src, (int(round(xy[0])), int(round(xy[1]))))


# ---------- 1. evidence legend: centre-screen, then docked (matches style.legend_strip exactly) ----------

LEGEND = ["SIMULATED", "REAL DATA", "MODEL CHECK", "PENDING", "CORRECTED"]
K = 2.4                                   # centre-screen scale of the legend
LEG_CY = 520                              # centre-screen row centre


def dock_boxes() -> dict[str, tuple[int, int, int, int]]:
    """The exact boxes legend_strip() draws (same arithmetic as style.legend_strip)."""
    boxes, x = {}, 1860
    for kind in reversed(LEGEND):
        tw, _ = text_size(kind, 15, 700)
        x0 = x - tw - 18
        boxes[kind] = (x0, 1000, x, 1024)
        x = x0 - 8
    return boxes


DOCK = dock_boxes()


@lru_cache(maxsize=None)
def pill_sprite(kind: str, k: float, morph: float = 1.0) -> Image.Image:
    """One legend pill drawn at scale k, with legend_strip's proportions (text 15 px, pad 9, height 24).
    morph 0: the large font's own letter spacing, text centred vertically (reads best centre-screen).
    morph 1: each letter at k x its place in legend_strip's 15 px line (hinted advances) and 4 px below
    the pill top, scaled, so the shrunk sprite lines up letter for letter with the strip it turns into.
    In between, the letters slide (by at most a few pixels), so nothing is ever drawn twice."""
    x0, y0, x1, y1 = DOCK[kind]
    w_, h_ = int(round((x1 - x0) * k)), int(round((y1 - y0) * k))
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r, lw = int(round(12 * k)), max(2, int(round(2 * k)))
    if kind == "PENDING":
        d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), r, fill=NAVY_2)
        step, dash = 14 * k, 7 * k          # the same dashes as style.rounded(dash=True), scaled
        x = float(r)
        while x < w_ - r:
            xe = min(x + dash, w_ - r)
            d.line([(x, lw / 2), (xe, lw / 2)], fill=GREY, width=lw)
            d.line([(x, h_ - 1 - lw / 2), (xe, h_ - 1 - lw / 2)], fill=GREY, width=lw)
            x += step
        colour = INK_2
    elif kind == "CORRECTED":
        d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), r, fill=NAVY, outline=INK, width=lw)
        colour = INK
    else:
        d.rounded_rectangle((0, 0, w_ - 1, h_ - 1), r, fill=BADGES[kind])
        colour = NAVY
    small, big = font(15, 700), font(int(round(15 * k)), 700)
    _, t0, _, b0 = big.getbbox(kind, anchor="la")
    y = lerp((h_ - (b0 - t0)) / 2 - t0, 4 * k, morph)
    fit = k * small.getlength(kind) / big.getlength(kind)           # natural spacing, same overall width
    for i, ch in enumerate(kind):
        if ch == " ":
            continue
        x_strip = k * (small.getlength(kind[:i + 1]) - small.getlength(ch))   # where legend_strip puts it
        x_nat = fit * (big.getlength(kind[:i + 1]) - big.getlength(ch))
        d.text((9 * k + lerp(x_nat, x_strip, morph), y), ch, font=big, fill=colour, anchor="la")
    return img


def centre_boxes() -> dict[str, tuple[float, float, float, float]]:
    """The legend row scaled by K and centred on the screen (same spacing as the docked strip)."""
    left = min(b[0] for b in DOCK.values())
    total = (1860 - left) * K
    ox = (W - total) / 2
    out = {}
    for kind, (x0, y0, x1, y1) in DOCK.items():
        out[kind] = (ox + (x0 - left) * K, LEG_CY - 12 * K, ox + (x1 - left) * K, LEG_CY + 12 * K)
    return out


CENTRE = centre_boxes()
DOCK_START = BEATS["legend_dock"]
DOCK_ARRIVE = DOCK_START + 0.65       # the pills land in the strip slot at 1.5 s


def strip_pills() -> dict[str, Image.Image]:
    """Each pill exactly as legend_strip() draws it (cropped from a transparent layer)."""
    layer = transparent()
    legend_strip(layer)
    return {k: layer.crop((x0, y0, x1 + 1, y1 + 1)) for k, (x0, y0, x1, y1) in DOCK.items()}


STRIP = strip_pills()


def draw_legend(img: Image.Image, t: float) -> None:
    if t >= DOCK_ARRIVE:
        legend_strip(img)
        return
    p = progress(t, DOCK_START, DOCK_ARRIVE - DOCK_START)
    s = lerp(K, 1.0, p)                          # current scale of the row
    # keep the large font's own letter spacing while the pills are big (legend_strip's hinted 15 px
    # spacing, scaled up, reads as "SIMULAT ED"); switch to the strip's spacing only below about 1.5x,
    # where the shift is a pixel or two and the pills are moving fast (about 3 frames)
    morph = round(clamp((1.5 - s) / (1.5 - 1.2)), 2)
    # then dissolve the sprite into legend_strip's own pixels (scaled; the letters already sit in the
    # same places), so each pill lands as exactly the strip that stays
    mix = clamp((1.2 - s) / (1.2 - 1.02))
    for i, kind in enumerate(LEGEND):
        a_in = progress(t, BEATS["legend_in"] + 0.07 * i, 0.35)
        if a_in <= 0:
            continue
        pop = lerp(0.86, 1.0, a_in)                          # gentle grow-in
        c0, d0 = CENTRE[kind], DOCK[kind]
        box = tuple(lerp(c0[n], d0[n], p) for n in range(4))
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + (1 - a_in) * 14
        w_, h_ = (box[2] - box[0]) * pop, (box[3] - box[1]) * pop
        dw, dh = d0[2] - d0[0], d0[3] - d0[1]
        size = (max(1, int(round(w_ * (dw + 1) / dw))), max(1, int(round(h_ * (dh + 1) / dh))))
        spr = pill_sprite(kind, K, morph).resize(size, Image.LANCZOS)
        if mix > 0:
            spr = Image.blend(spr, STRIP[kind].resize(size, Image.LANCZOS), mix)
        paste(img, spr, (cx - w_ / 2, cy - h_ / 2), a_in)


# ---------- 2. macro-F1 panel ----------

def chart_static() -> Image.Image:
    img = Image.new("RGBA", (CH_W, CH_H), (0, 0, 0, 0))
    rounded(img, (0, 0, CH_W - 1, CH_H - 1), 22, fill=NAVY_2)
    draw_text(img, (40, 34), AXIS, 26, 600, INK, max_width=CH_W - 80)
    # bar legend
    y = 86
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, y + 3, 62, y + 25), 5, fill=MODEL_C)
    draw_text(img, (74, y), LEG_MODEL, 22, 500, INK_2)
    x = 74 + text_size(LEG_MODEL, 22, 500)[0] + 40
    d.rounded_rectangle((x, y + 3, x + 22, y + 25), 5, fill=BASE_C)
    draw_text(img, (x + 34, y), LEG_BASE, 22, 500, INK_2)
    # y-axis tick labels
    for k in range(6):
        v = k / 5
        draw_text(img, (P_X0 - 22, ypos(v)), "0" if k == 0 else f"{v:.1f}", 20, 500, INK_3, anchor="rm")
    return img


CHART_BG = chart_static()
XLAB = [f"+{h} min" for h in HORIZONS]


def chart_frame(t: float) -> Image.Image:
    img = CHART_BG.copy()
    hl = progress(t, BEATS["fifteen_minute"] + 0.2, 0.5)                # +15 pair highlight
    last = len(HORIZONS) - 1
    # highlight band behind the +15 group
    if hl > 0:
        gx = group_cx(last)
        rounded(img, (gx - BAR_W - 40, P_TOP - 62, gx + BAR_W + 40, P_BOT + 66), 16,
                 fill=NAVY_3, outline=MODEL_C, width=2, alpha=hl * 0.9)
    # value labels at 3 decimals, shown as each bar finishes: (text, x, baseline y, opacity, colour)
    labels = []
    for i in range(len(HORIZONS)):
        for j, (vals, col_txt) in enumerate(((F1_MODEL, INK), (F1_BASE, INK_2))):
            a = progress(t, BEATS["chart_in"] + 0.35 + 0.22 * i + 0.08 * j + 0.7, 0.35)
            if a > 0:
                x0, y0, x1, _ = bar_box(i, j, vals[i])
                labels.append((f"{vals[i]:.3f}", (x0 + x1) / 2, y0 - VAL_GAP, a, col_txt, i))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k in range(6):                                                  # gridlines
        y = ypos(k / 5)
        d.line([(P_X0 - 6, y), (P_X1, y)], fill=rgba(INK_3, 0.55 if k == 0 else 0.28), width=2 if k == 0 else 1)
    if labels:                       # knock the gridlines out behind each value (the 1.0 line ran through 0.887)
        cut = Image.new("L", img.size, 0)
        dc = ImageDraw.Draw(cut)
        for txt, x, y, a, _, _ in labels:
            l_, t_, r_, b_ = font(28, 700).getbbox(txt, anchor="ms")
            dc.rectangle((x + l_ - 8, y + t_ - 6, x + r_ + 8, y + b_ + 6), fill=int(round(255 * a)))
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), ImageChops.invert(cut)))
    img.alpha_composite(lay)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(len(HORIZONS)):
        dim = 1 - 0.45 * hl if i != last else 1.0
        for j, (vals, col) in enumerate(((F1_MODEL, MODEL_C), (F1_BASE, BASE_C))):
            g = progress(t, BEATS["chart_in"] + 0.35 + 0.22 * i + 0.08 * j, 0.9)
            if g <= 0:
                continue
            x0, y0, x1, y1 = bar_box(i, j, vals[i] * g)
            r = int(min(8, (y1 - y0) / 2))
            if y1 - y0 >= 1:
                d.rounded_rectangle((x0, y0, x1, y1), r, fill=rgba(col, dim), corners=(True, True, False, False))
    img.alpha_composite(lay)
    # emphasis pills behind the two spoken +15 values (no gap labels)
    for j, (beat, col, a_max) in enumerate(((BEATS["f1_model"], MODEL_C, 0.28), (BEATS["f1_nochange"], BASE_C, 0.4))):
        e = progress(t, beat, 0.35)
        if e > 0:
            v = (F1_MODEL, F1_BASE)[j][last]
            bx0, by0, bx1, _ = bar_box(last, j, v)
            cx = (bx0 + bx1) / 2
            l_, t_, r_, b_ = font(28, 700).getbbox(f"{v:.3f}", anchor="ms")
            rounded(img, (cx + l_ - 12, by0 - VAL_GAP + t_ - 9, cx + r_ + 12, by0 - VAL_GAP + b_ + 9), 12,
                    fill=col, alpha=a_max * e)
    # values at 3 decimals (the +5 and +10 values dim with the highlight)
    for txt, x, y, a, col_txt, i in labels:
        draw_text(img, (x, y), txt, 28, 700, col_txt, a * (1 - 0.3 * hl) if i != last else a, anchor="ms")
    # horizon labels
    for i, lab in enumerate(XLAB):
        a = progress(t, BEATS["chart_in"] + 0.2, 0.4)
        if i == last:
            draw_text(img, (group_cx(i), P_BOT + 34), lab, 28, 700, tuple(int(c) for c in lerp(INK_2, INK, hl)), a, anchor="mm")
        else:
            draw_text(img, (group_cx(i), P_BOT + 34), lab, 28, 600, INK_2, a * (1 - 0.3 * hl), anchor="mm")
    return img


# ---------- 3. critical minutes card ----------

def card_a(t: float) -> Image.Image:
    w_, h_ = COL_X1 - COL_X0, CA_Y1 - CA_Y0
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 22, fill=NAVY_2)
    lx, rx, mx = 180, 520, 350
    a1 = progress(t, BEATS["ninety_one"] - 0.55, 0.45)
    a2 = progress(t, BEATS["seventy_nine"] - 0.05, 0.45)
    draw_text(img, (lx, 50), "model", 22, 600, MODEL_C, a1, anchor="mm")
    draw_text(img, (lx, 182 + (1 - a1) * 16), f"{CRIT_MODEL}%", 120, 700, MODEL_C, a1, anchor="ms")
    draw_text(img, (mx, 176), "vs", 36, 500, INK_2, a2, anchor="ms")
    draw_text(img, (rx, 50), "no change", 22, 600, INK_2, a2, anchor="mm")
    draw_text(img, (rx, 182 + (1 - a2) * 16), f"{CRIT_BASE}%", 120, 700, BASE_C, a2, anchor="ms")
    draw_text(img, (w_ / 2, 238), CRIT_LINE, 30, 600, INK, a1, anchor="mm")
    return img


# ---------- 4. flagged vs the rest card ----------

TRACK_X0, TRACK_X1 = 40, 660
ROWS = [  # (label, value text, share 0-1, top y of label, solid fill?)
    (FLAG_LABEL, FLAG_VALUE, GATE["accuracy_flagged"], 36, False),
    (REST_LABEL, REST_VALUE, GATE["accuracy_confident"], 162, True),
]
ROW_BEATS = [BEATS["right_only"] - 0.1, BEATS["the_rest"] - 0.5]   # value text fades in 0.55 s after each


def card_b(t: float) -> Image.Image:
    w_, h_ = COL_X1 - COL_X0, CB_Y1 - CB_Y0
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 22, fill=NAVY_2)
    draw_text(img, (w_ - 40, ROWS[0][3] + 28), H_TAG, 22, 600, INK_2, anchor="rs")
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d_img = ImageDraw.Draw(img)
    for (label, value, share, y, solid), beat in zip(ROWS, ROW_BEATS):
        draw_text(img, (TRACK_X0, y + 28), label, 28, 600, INK, anchor="ls")
        g = progress(t, beat, 1.0)
        by0, by1 = y + 50, y + 100
        d_img.rounded_rectangle((TRACK_X0, by0, TRACK_X1, by1), 12, fill=NAVY_3)
        if g > 0:
            xe = TRACK_X0 + (TRACK_X1 - TRACK_X0) * share * g
            r = int(min(12, (xe - TRACK_X0) / 2))       # grows from nothing, no pop
            if xe - TRACK_X0 >= 2:
                if solid:
                    d.rounded_rectangle((TRACK_X0, by0, xe, by1), r, fill=rgba(MODEL_C, 1))
                else:
                    d.rounded_rectangle((TRACK_X0, by0, xe, by1), r, fill=rgba(MODEL_C, 0.32),
                                        outline=rgba(MODEL_C, 1), width=min(3, max(1, r)))
        lx = TRACK_X0 + text_size(label + " ", 28, 600)[0] + 8
        draw_text(img, (lx, y + 28), value, 28, 700, MODEL_C, progress(t, beat + 0.55, 0.4), anchor="ls")
    img.alpha_composite(lay)
    return img


# ---------- frame ----------

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()

    # macro-F1 panel: fades in, then slides left on "and catch"
    a_ch = progress(t, BEATS["chart_in"], 0.55)
    if a_ch > 0:
        slide = progress(t, BEATS["and_catch"] - 0.5, 0.8)
        x = lerp(CH_X_CENTRE, CH_X_LEFT, slide)
        y = CH_Y - (1 - a_ch) * 20          # settles from above: the panel never dips into the lower-third area
        paste(img, chart_frame(t), (x, y), a_ch)

    # critical minutes card
    a_a = progress(t, BEATS["and_catch"] + 0.2, 0.6)
    if a_a > 0:
        paste(img, card_a(t), (COL_X0 + (1 - a_a) * 50, CA_Y0), a_a)

    # flagged vs the rest card
    a_b = progress(t, BEATS["flagged"] - 0.2, 0.6)
    if a_b > 0:
        paste(img, card_b(t), (COL_X0 + (1 - a_b) * 50, CB_Y0), a_b)

    # overlay slots
    chapter_card(img, CHAPTER, fade(t, 0.0, CHAPTER_END, 0.3))
    badge(img, "SIMULATED", alpha=progress(t, BEATS["legend_dock"] + 0.25, 0.4))
    footer(img, FOOTER, progress(t, 0.3, 0.4))
    draw_legend(img, t)
    return img


STILLS = {
    "legend_centre": 0.6,
    "legend_docking": 1.15,
    "f1_bars": 9.0,
    "critical_minutes": 15.0,
    "flagged_vs_rest": 21.95,
}

if __name__ == "__main__":
    only_stills = "--stills" in sys.argv
    for name, ts in STILLS.items():
        print(still(f"S10_{name}", draw_frame(ts)))
    if not only_stills:
        print(render("S10", DURATION, draw_frame))
