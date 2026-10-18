"""Shot S10 (1:44.0-2:04.5, 20.5 s): "Does it work? Every result is labelled."

Storyboard: docs/video/script.md section 3, row S10; claims table section 4, rows S10; section 6
("motion_graphic" shot rules, "On-screen text load"); shot list docs/video/shotlist.json (id S10).

0-1.5 s   the four evidence badges appear centre-screen, then shrink and dock as the bottom-right
          legend strip (style.legend_strip), where they stay for the rest of the shot. The voice
          starts at 0.8 s, over the docking legend (VOICE_START below; video/assemble.py must use it).
          The row drops to the strip's height by 1.4 s and slides right into place, beside the
          first caption box, never behind it (see DOCK_DROP).
then      the +15 min macro-F1 pair, model vs "no change", at 3 decimals, no gap label (the +5 and
          +10 min pairs left the picture in the 19 Oct declutter: only the +15 pair is spoken).
9.3 s-end the one-line accuracy comparison, in a pill at the foot of the F1 panel (under the bars,
          so the panel and its accuracy line read as one element).
then      flagged as uncertain vs the rest (the panel slides left to make room).
18.7-20.5 the settled panels hold after the last word (S10 grew 19.5 -> 20.5 s on 19 Oct, all of it
          this end hold: the last value, "the rest: 97%", is fully in from 17.2 s and reads 3.3 s).
Badge SIMULATED pinned. No footer (no outside source: the data is the team's own simulation).
At most two text elements beside the chapter card, the badge and the caption: the F1 panel and the
flagged card (DECLUTTER, 19 Oct). Off screen, kept for Q&A (script.md 5F): the 91% vs 79% critical
minutes (no longer spoken), the +5 / +10 min pairs, the 9 / 2 / 3-day split, recall at 3 decimals,
flagged share, other horizons' gating, the stress day and the +15 min gain interval.

Data (read, never retyped):
  ml/models/metrics.json
    per_horizon.h15.test.f1_macro                              model macro-F1
    per_horizon.h15.persistence_baseline.test.f1_macro         "no change" macro-F1
    per_horizon.h15.confidence_gating.accuracy_flagged / accuracy_confident   56% / 97%
    per_horizon.h15.test.accuracy                              accuracy line: model 96.4%
    per_horizon.h15.persistence_baseline.test.accuracy         accuracy line: "no change" 94.3%
    per_horizon.h15.test.support.SAFE / test.n                 accuracy line: always SAFE 84.6%
  docs/video/shotlist.json: duration, narration and every on-screen line (asserted below)

Run: .venv/bin/python video/mg/S10.py   -> video/build/mg/S10.mp4 and stills in video/build/mg/stills/
"""
from __future__ import annotations

import json
from functools import lru_cache
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageChops, ImageDraw  # noqa: E402

# ---------- timing ----------

SHOT = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
SHOT = next(s for s in SHOT if s["id"] == "S10")
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 20.5 s
assert DURATION == 20.5, DURATION

# Seconds from the shot start, keyed to the guide voice video/build/guide/S10.wav (say -v Daniel
# -r 155, 17.92 s) laid from VOICE_START: word times measured from its pauses (silencedetect) and
# prefix syntheses, 19 Oct. Guide pauses end at 2.40 / 6.42 / 10.27 / 12.67 / 15.95 / 16.95 s into
# the file; the words up to "nothing changes" land where they did on 18 Oct. Shot times:
# "On simulated days it had never seen," 0.8-3.0 | "our fifteen-minute forecasts scored an F one
# of point eight six five," 3.2-7.0 | "against point seven nine five for assuming nothing changes."
# 7.2-10.9 | "When they flagged themselves as uncertain," 11.1-13.3 ("flagged" 11.7) | "they were
# right only about fifty-six percent of the time;" 13.5-16.6 ("56" 14.8) | "otherwise, ninety-seven."
# 16.75-18.7 ("97" 17.75; the voice ends at 18.72, the shot holds to 20.5). Re-key to the real take.
VOICE_START = 0.8              # script.md section 6 (S10 voice from 0.8 s); assemble.py VOICE_START["S10"]
BEATS = {
    "legend_in": 0.0,          # four badges appear centre-screen (no voice yet)
    "legend_dock": 0.85,       # they shrink and dock bottom-right, docked by 1.5 s
    "voice_on": 0.8,           # "On simulated days it had never seen," (0.80-2.98)
    "chart_in": 1.3,           # macro-F1 panel fades in; the two bars grow
    "fifteen_minute": 3.55,    # "our fifteen-minute forecasts" ("fifteen" 3.54) -> "+15 min" label brightens
    "f1_model": 5.85,          # "point eight six five" (5.86-7.06)
    "f1_nochange": 7.85,       # "against point seven nine five" (7.22; "point" 7.85, "five" ends 9.16)
    "accuracy_line": 9.3,      # after "point seven nine five" (ends 9.16): the accuracy line, to the end (10.2 s)
    "when": 11.0,              # "When they flagged" (11.07) -> the F1 panel slides left
    "flagged": 11.7,           # "flagged" (11.71) -> flagged-vs-rest card in
    "right_only": 13.95,       # "they were right only about" ("right" 14.03) -> flagged bar grows, "right 56%" lands
    "fifty_six": 14.8,         # "fifty-six percent of the time" (14.81)
    "the_rest": 16.75,         # "otherwise, ninety-seven" ("otherwise" 16.75; "97" 17.75-18.73; voice ends 18.72)
}
CHAPTER_END = 2.0              # chapter card shown for about 2 s

# ---------- data ----------

METRICS = json.loads((ROOT / "ml" / "models" / "metrics.json").read_text())
assert 15 in METRICS["horizons"], METRICS["horizons"]           # "our fifteen-minute forecasts"
H15 = METRICS["per_horizon"]["h15"]
F1_MODEL = H15["test"]["f1_macro"]                               # 0.865
F1_BASE = H15["persistence_baseline"]["test"]["f1_macro"]        # 0.795
GATE = H15["confidence_gating"]
ACC_FLAGGED = round(100 * GATE["accuracy_flagged"])
ACC_REST = round(100 * GATE["accuracy_confident"])
# accuracy line (round-2 lock): +15 min test accuracy, "no change" accuracy, and the always-SAFE
# accuracy worked out from the test support (SAFE 14,505 of 17,152; not a stored metric)
_test, _base = H15["test"], H15["persistence_baseline"]["test"]
assert sum(_test["support"].values()) == _test["n"], "support does not add up to n"
ACC_MODEL = 100 * _test["accuracy"]                              # 96.4
ACC_BASE = 100 * _base["accuracy"]                               # 94.3
ACC_SAFE = 100 * _test["support"]["SAFE"] / _test["n"]           # 84.6

# guard: the spoken narration must match the data file (fails loudly if metrics.json changes)
_spoken = SHOT["narration"]
for v in (f"{F1_MODEL:.3f}", f"against {F1_BASE:.3f}", f"{ACC_FLAGGED} percent", f"otherwise, {ACC_REST}"):
    assert v in _spoken, f"metrics.json no longer matches the narration: {v!r}"
assert "critical minutes" not in _spoken, "the 91% vs 79% clause is back in the voice: restore its card"

# ---------- on-screen text (storyboard wording, asserted against the shot list) ----------

CHAPTER = "Does it work? Every result is labelled."
AXIS = "macro-F1: SAFE, WARNING, CRITICAL weighted equally"   # the axis definition, at most 6 words
BAR_NAMES = ("model", "no change")                           # inside the bars (direct labels, no legend)
H_TAG = "+15 min"
FLAG_LABEL, FLAG_VALUE = "flagged as uncertain:", f"right {ACC_FLAGGED}%"
REST_LABEL, REST_VALUE = "the rest:", f"{ACC_REST}%"
ACC_HEAD = "Accuracy:"
ACC_BODY = f"{ACC_MODEL:.1f}% vs {ACC_BASE:.1f}% · always SAFE {ACC_SAFE:.1f}%"
assert len(AXIS.split()) <= 6, AXIS

_ost = SHOT["on_screen_text"]
for v in (f"Chapter card (top-left): {CHAPTER}", "Badge (top-right): SIMULATED (pinned)", f"Axis: {AXIS}",
          f"Bars ({H_TAG}): {BAR_NAMES[0]} / {BAR_NAMES[1]}",
          f"Bars: {FLAG_LABEL} {FLAG_VALUE} · {REST_LABEL} {REST_VALUE}",
          f"Accuracy line (from about {BEATS['accuracy_line']} s to the end, under the bars): {ACC_HEAD} {ACC_BODY}"):
    assert v in _ost, f"shotlist.json on_screen_text no longer matches: {v!r}"
assert "Footer" not in _ost and "critical minutes" not in _ost, "S10 has no footer and no 91% vs 79% card now"

MODEL_C = CYAN
BASE_C = GREY

# ---------- layout ----------

CH_W, CH_H = 860, 630             # macro-F1 panel (with the accuracy line at its foot)
CH_Y = 160
CH_X_CENTRE = (W - CH_W) // 2     # 530 while it is the only element
CH_X_LEFT = 60                    # after "When they flagged"
COL_X0, COL_X1 = 980, 1860        # flagged-vs-rest card, the same height as the panel
CB_Y0, CB_Y1 = CH_Y, CH_Y + CH_H

# plot geometry inside the panel (local coordinates)
P_X0, P_X1 = 110, CH_W - 60
P_TOP, P_BOT = 150, 450           # value 1.0 and value 0.0
BAR_W, BAR_GAP = 170, 24
VAL_GAP = 24                      # value label baseline above the bar top
ACC_SIZE = 26                     # the accuracy line is read, not small print
ACC_Y0, ACC_Y1 = 540, 590         # its pill, under the "+15 min" label, inside the panel


def ypos(v: float) -> float:
    return P_BOT - v * (P_BOT - P_TOP)


PAIR_CX = (P_X0 + P_X1) / 2


def bar_box(j: int, v: float) -> tuple[float, float, float, float]:
    """Bar j (0 = model, 1 = no change), height for value v."""
    x0 = PAIR_CX - BAR_GAP / 2 - BAR_W if j == 0 else PAIR_CX + BAR_GAP / 2
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

LEGEND = ["SIMULATED", "REAL DATA", "MODEL CHECK", "PENDING"]
assert f"Legend strip (bottom-right): {' · '.join(LEGEND)} |" in _ost, "shotlist.json legend line no longer matches"
K = 2.4                                  # centre-screen scale of the legend
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
# The row drops to the strip's y faster than it travels in x, accelerating (ease-in) and reaching
# y 1012 at 1.4 s, then slides right along the strip row into its slots. The first caption (from
# 0.8 s, box y 926-990 at x 645-1274) lies between the centre row and the strip, left of the slots
# (SIMULATED's starts at x 1412). The pills are in the box's rows in one frame only (1.37 s), by
# then 103 px right of it, so they never pass behind it (a drop of 0.45 s or less: 1 frame behind).
DOCK_DROP = 0.55


def drop(t: float) -> float:
    """Vertical progress of the docking row: quadratic ease-in, complete DOCK_DROP s after the start."""
    return clamp((t - DOCK_START) / DOCK_DROP) ** 2


def strip_pills() -> dict[str, Image.Image]:
    """Each pill exactly as legend_strip() draws it (cropped from a transparent layer)."""
    layer = transparent()
    legend_strip(layer)
    # legend_strip draws exactly LEGEND's pills: nothing left of SIMULATED's slot, none missing
    assert layer.getbbox()[0] == min(b[0] for b in DOCK.values()), (layer.getbbox(), DOCK)
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
    py = drop(t)
    for i, kind in enumerate(LEGEND):
        a_in = progress(t, BEATS["legend_in"] + 0.07 * i, 0.35)
        if a_in <= 0:
            continue
        pop = lerp(0.86, 1.0, a_in)                          # gentle grow-in
        c0, d0 = CENTRE[kind], DOCK[kind]
        box = tuple(lerp(c0[n], d0[n], p) for n in range(4))         # x and size follow p
        cy = lerp((c0[1] + c0[3]) / 2, (d0[1] + d0[3]) / 2, py)     # y follows the faster drop
        cx, cy = (box[0] + box[2]) / 2, cy + (1 - a_in) * 14
        w_, h_ = (box[2] - box[0]) * pop, (box[3] - box[1]) * pop
        dw, dh = d0[2] - d0[0], d0[3] - d0[1]
        size = (max(1, int(round(w_ * (dw + 1) / dw))), max(1, int(round(h_ * (dh + 1) / dh))))
        spr = pill_sprite(kind, K, morph).resize(size, Image.LANCZOS)
        if mix > 0:
            spr = Image.blend(spr, STRIP[kind].resize(size, Image.LANCZOS), mix)
        paste(img, spr, (cx - w_ / 2, cy - h_ / 2), a_in)


# ---------- 2. macro-F1 panel: the +15 min pair, with the accuracy line at its foot ----------

def accuracy_pill() -> Image.Image:
    """The accuracy line, head in bold, on a NAVY_3 pill (centred at the foot of the F1 panel)."""
    f_head, f_body = font(ACC_SIZE, 700), font(ACC_SIZE, 500)
    head_w = f_head.getlength(ACC_HEAD + " ")
    tw = head_w + f_body.getlength(ACC_BODY)
    w_, h_ = int(round(tw + 56)), ACC_Y1 - ACC_Y0
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 14, fill=NAVY_3)
    draw_text(img, (28, h_ / 2), ACC_HEAD, ACC_SIZE, 700, INK, anchor="lm")
    draw_text(img, (28 + head_w, h_ / 2), ACC_BODY, ACC_SIZE, 500, INK, anchor="lm")
    return img


ACC_PILL = accuracy_pill()
assert ACC_PILL.width <= CH_W - 80, ACC_PILL.width
assert text_size(AXIS, 26, 600)[0] <= CH_W - 80, "axis definition runs past the panel"


def chart_static() -> Image.Image:
    img = Image.new("RGBA", (CH_W, CH_H), (0, 0, 0, 0))
    rounded(img, (0, 0, CH_W - 1, CH_H - 1), 22, fill=NAVY_2)
    draw_text(img, (40, 34), AXIS, 26, 600, INK)
    # y-axis: 0, 0.5 and 1.0 only (the two values carry the reading)
    for v in (0.0, 0.5, 1.0):
        draw_text(img, (P_X0 - 22, ypos(v)), "0" if v == 0 else f"{v:.1f}", 20, 500, INK_3, anchor="rm")
    return img


CHART_BG = chart_static()


def chart_frame(t: float) -> Image.Image:
    img = CHART_BG.copy()
    vals = (F1_MODEL, F1_BASE)
    # value labels at 3 decimals, shown as each bar finishes: (text, x, baseline y, opacity, colour)
    labels = []
    for j, col_txt in enumerate((INK, INK_2)):
        a = progress(t, BEATS["chart_in"] + 0.35 + 0.1 * j + 0.7, 0.35)
        if a > 0:
            x0, y0, x1, _ = bar_box(j, vals[j])
            labels.append((f"{vals[j]:.3f}", (x0 + x1) / 2, y0 - VAL_GAP, a, col_txt))
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for v in (0.0, 0.5, 1.0):                                           # gridlines
        y = ypos(v)
        d.line([(P_X0 - 6, y), (P_X1, y)], fill=rgba(INK_3, 0.55 if v == 0 else 0.28), width=2 if v == 0 else 1)
    if labels:                       # knock the gridlines out behind each value
        cut = Image.new("L", img.size, 0)
        dc = ImageDraw.Draw(cut)
        for txt, x, y, a, _ in labels:
            l_, t_, r_, b_ = font(34, 700).getbbox(txt, anchor="ms")
            dc.rectangle((x + l_ - 8, y + t_ - 6, x + r_ + 8, y + b_ + 6), fill=int(round(255 * a)))
        lay.putalpha(ImageChops.multiply(lay.getchannel("A"), ImageChops.invert(cut)))
    img.alpha_composite(lay)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for j, col in enumerate((MODEL_C, BASE_C)):
        g = progress(t, BEATS["chart_in"] + 0.35 + 0.1 * j, 0.9)
        if g <= 0:
            continue
        x0, y0, x1, y1 = bar_box(j, vals[j] * g)
        r = int(min(8, (y1 - y0) / 2))
        if y1 - y0 >= 1:
            d.rounded_rectangle((x0, y0, x1, y1), r, fill=rgba(col, 1), corners=(True, True, False, False))
    img.alpha_composite(lay)
    # bar names inside the bars, at their foot (direct labels instead of a legend)
    for j, name in enumerate(BAR_NAMES):
        a = progress(t, BEATS["chart_in"] + 0.35 + 0.1 * j + 0.6, 0.35)
        x0, _, x1, _ = bar_box(j, vals[j])
        draw_text(img, ((x0 + x1) / 2, P_BOT - 22), name, 26, 600, NAVY, a, anchor="ms")
    # emphasis pills behind the two spoken values (no gap label)
    for j, (beat, col, a_max) in enumerate(((BEATS["f1_model"], MODEL_C, 0.28), (BEATS["f1_nochange"], BASE_C, 0.4))):
        e = progress(t, beat, 0.35)
        if e > 0:
            bx0, by0, bx1, _ = bar_box(j, vals[j])
            cx = (bx0 + bx1) / 2
            l_, t_, r_, b_ = font(34, 700).getbbox(f"{vals[j]:.3f}", anchor="ms")
            rounded(img, (cx + l_ - 12, by0 - VAL_GAP + t_ - 9, cx + r_ + 12, by0 - VAL_GAP + b_ + 9), 12,
                    fill=col, alpha=a_max * e)
    for txt, x, y, a, col_txt in labels:
        draw_text(img, (x, y), txt, 34, 700, col_txt, a, anchor="ms")
    # horizon label, brightening on "fifteen-minute"
    hl = progress(t, BEATS["fifteen_minute"], 0.5)
    draw_text(img, (PAIR_CX, P_BOT + 40), H_TAG, 28, 700, tuple(int(c) for c in lerp(INK_2, INK, hl)),
              progress(t, BEATS["chart_in"] + 0.2, 0.4), anchor="mm")
    # the accuracy line, rising 10 px as it fades in, then held to the end
    a_acc = progress(t, BEATS["accuracy_line"], 0.5)
    if a_acc > 0:
        paste(img, ACC_PILL, ((CH_W - ACC_PILL.width) / 2, ACC_Y0 + (1 - a_acc) * 10), a_acc)
    return img


# ---------- 3. flagged vs the rest card ----------

TRACK_X0, TRACK_X1 = 48, COL_X1 - COL_X0 - 48
ROWS = [  # (label, value text, share 0-1, label baseline y, solid fill?)
    (FLAG_LABEL, FLAG_VALUE, GATE["accuracy_flagged"], 205, False),
    (REST_LABEL, REST_VALUE, GATE["accuracy_confident"], 375, True),
]
ROW_BEATS = [BEATS["right_only"] - 0.1, BEATS["the_rest"] - 0.5]   # value text fades in 0.55 s after each
TRACK_H = 64


def card_b(t: float) -> Image.Image:
    w_, h_ = COL_X1 - COL_X0, CB_Y1 - CB_Y0
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 22, fill=NAVY_2)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d_img = ImageDraw.Draw(img)
    for (label, value, share, y, solid), beat in zip(ROWS, ROW_BEATS):
        draw_text(img, (TRACK_X0, y), label, 34, 600, INK, anchor="ls")
        g = progress(t, beat, 1.0)
        by0, by1 = y + 22, y + 22 + TRACK_H
        d_img.rounded_rectangle((TRACK_X0, by0, TRACK_X1, by1), 14, fill=NAVY_3)
        if g > 0:
            xe = TRACK_X0 + (TRACK_X1 - TRACK_X0) * share * g
            r = int(min(14, (xe - TRACK_X0) / 2))       # grows from nothing, no pop
            if xe - TRACK_X0 >= 2:
                if solid:
                    d.rounded_rectangle((TRACK_X0, by0, xe, by1), r, fill=rgba(MODEL_C, 1))
                else:
                    d.rounded_rectangle((TRACK_X0, by0, xe, by1), r, fill=rgba(MODEL_C, 0.32),
                                        outline=rgba(MODEL_C, 1), width=min(3, max(1, r)))
        lx = TRACK_X0 + text_size(label + " ", 34, 600)[0] + 8
        draw_text(img, (lx, y), value, 34, 700, MODEL_C, progress(t, beat + 0.55, 0.4), anchor="ls")
    img.alpha_composite(lay)
    return img


# ---------- frame ----------

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()

    # macro-F1 panel (with its accuracy line): fades in, then slides left on "When they flagged"
    a_ch = progress(t, BEATS["chart_in"], 0.55)
    if a_ch > 0:
        slide = progress(t, BEATS["when"], 0.8)
        x = lerp(CH_X_CENTRE, CH_X_LEFT, slide)
        y = CH_Y - (1 - a_ch) * 20          # settles from above: the panel never dips into the lower-third area
        paste(img, chart_frame(t), (x, y), a_ch)

    # flagged vs the rest card, in as the panel finishes its slide
    a_b = progress(t, BEATS["flagged"] - 0.1, 0.6)
    if a_b > 0:
        paste(img, card_b(t), (COL_X0 + (1 - a_b) * 50, CB_Y0), a_b)

    # overlay slots (no footer: no outside source in this shot)
    chapter_card(img, CHAPTER, fade(t, 0.0, CHAPTER_END, 0.3))
    badge(img, "SIMULATED", alpha=progress(t, BEATS["legend_dock"] + 0.25, 0.4))
    draw_legend(img, t)
    return img


STILLS = {
    "legend_centre": 0.6,
    "legend_docking": 1.15,
    "f1_bars": 10.4,         # both +15 values emphasised, accuracy line in (before the slide); also
                             # the source of video/team-kit/prop_M2_F1_chart.png, [MEMBER 2]'s S05 prop
    "flagged": 15.3,         # "right 56%" landed on "fifty-six"
    "flagged_vs_rest": 20.45,  # the settled end frame, after the 1.8 s end hold
}

if __name__ == "__main__":
    only_stills = "--stills" in sys.argv
    for name, ts in STILLS.items():
        print(still(f"S10_{name}", draw_frame(ts)))
    if not only_stills:
        print(render("S10", DURATION, draw_frame))
