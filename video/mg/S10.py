"""S10 · Held-out simulation: +15 min macro-F1 and critical-minutes recall.

The spoken central question docks into a persistent header before the two metric cards. The macro-F1 panel introduces the
model and persistence baseline, then slides left while the 91% / 79% recall card arrives.
Both cards and the readable accuracy comparison hold to the cut. All results remain under
SIMULATED; confidence-gating figures stay in the supporting evidence rather than this shot.

Numbers come from ml/models/metrics.json. Narration, duration and on-screen text come from
docs/video/shotlist.json. Beats retain the first sentence's guide timing; re-key to real voices.
Run: .venv/bin/python video/mg/S10.py [--stills]
"""
from __future__ import annotations

import json
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageChops, ImageDraw  # noqa: E402

# ---------- timing ----------

SHOT = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
SHOT = next(s for s in SHOT if s["id"] == "S10")
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)

# The question has its own guide beat; the answer starts at2.6 s including assembly's0.2 s offset.
# New S10.wav: body2.61-16.83; recall's final 'against79' clause begins15.34 s.
VOICE_START, ANSWER_START = 0.2, 2.6
BEATS = {
    "voice_on": ANSWER_START,
    "chart_in": ANSWER_START,
    "fifteen_minute": 4.8,
    "f1_model": 7.15,
    "f1_nochange": 9.15,
    "accuracy_line": 10.65,
    "and_catch": 12.4,
    "ninety_one": 13.05,
    "seventy_nine": 15.7,
}
assert DURATION >= BEATS["seventy_nine"] + 0.4 + 1.5, "allow time to read the final fully revealed recall value"

# ---------- data ----------

METRICS = json.loads((ROOT / "ml" / "models" / "metrics.json").read_text())
assert 15 in METRICS["horizons"], METRICS["horizons"]           # "our fifteen-minute forecasts"
H15 = METRICS["per_horizon"]["h15"]
F1_MODEL = H15["test"]["f1_macro"]                               # 0.865
F1_BASE = H15["persistence_baseline"]["test"]["f1_macro"]        # 0.795
CRIT_MODEL = round(100 * H15["test"]["per_class"]["CRITICAL"]["recall"])                         # 91
CRIT_BASE = round(100 * H15["persistence_baseline"]["test"]["per_class"]["CRITICAL"]["recall"])  # 79
# accuracy line (round-2 lock): +15 min test accuracy, "no change" accuracy, and the always-SAFE
# accuracy worked out from the test support (SAFE 14,505 of 17,152; not a stored metric)
_test, _base = H15["test"], H15["persistence_baseline"]["test"]
assert sum(_test["support"].values()) == _test["n"], "support does not add up to n"
ACC_MODEL = 100 * _test["accuracy"]                              # 96.4
ACC_BASE = 100 * _base["accuracy"]                               # 94.3
ACC_SAFE = 100 * _test["support"]["SAFE"] / _test["n"]           # 84.6

# guard: the spoken narration must match the data file (fails loudly if metrics.json changes)
_spoken = SHOT["narration"]
for v in (f"{F1_MODEL:.3f}", f"against {F1_BASE:.3f}", f"caught {CRIT_MODEL} percent of critical minutes",
          f"against {CRIT_BASE}."):
    assert v in _spoken, f"metrics.json no longer matches the narration: {v!r}"

# ---------- on-screen text (storyboard wording, asserted against the shot list) ----------

CHAPTER = "Does it work?"
AXIS = "macro-F1: SAFE, WARNING, CRITICAL weighted equally"   # the axis definition, at most 6 words
BAR_NAMES = ("model", "no change")                           # inside the bars (direct labels, no legend)
H_TAG = "+15 min"
SCOPE = "Held-out simulated days"
CRIT_LINE = f"of critical minutes caught ({H_TAG})"          # under the big numbers, at most 6 words
ACC_HEAD = "Accuracy:"
ACC_BODY = f"{ACC_MODEL:.1f}% vs {ACC_BASE:.1f}% · always SAFE {ACC_SAFE:.1f}%"
assert len(AXIS.split()) <= 6 and len(CRIT_LINE.split()) <= 6, (AXIS, CRIT_LINE)

_ost = SHOT["on_screen_text"]
for v in (f"Chapter question (central then persistent header): {CHAPTER}", "Badge (top-right): SIMULATED (pinned)", f"Axis: {AXIS}",
          f"Bars ({H_TAG}): {BAR_NAMES[0]} / {BAR_NAMES[1]}", SCOPE, f"{ACC_HEAD} {ACC_BODY}",
          f"{CRIT_MODEL}% vs {CRIT_BASE}% {CRIT_LINE}"):
    assert v in _ost, f"shotlist.json on_screen_text no longer matches: {v!r}"
assert "flagged as uncertain" not in _ost and "When they flagged" not in _spoken
assert "Footer" not in _ost, "S10 has no footer (19 Oct declutter)"
assert SHOT["narration"].startswith(CHAPTER)

MODEL_C = CYAN
BASE_C = GREY

# ---------- layout ----------

CH_W, CH_H = 860, 630             # macro-F1 panel (with the accuracy line at its foot)
CH_Y = 160
CH_X_CENTRE = (W - CH_W) // 2     # 530 while it is the only element
CH_X_LEFT = 60                    # after "and caught"
COL_X0, COL_X1 = 980, 1860        # the critical-minutes card, beside the F1 panel
CARD_W = COL_X1 - COL_X0          # 880
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


# The evidence key stays docked, so it cannot compete with the opening question.
LEGEND = ["SIMULATED", "REAL DATA", "MODEL CHECK", "PENDING"]
assert f"Legend strip (bottom-right): {' · '.join(LEGEND)} |" in _ost


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
    draw_text(img, (40, 78), SCOPE, 24, 500, INK_2)
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
    # the accuracy line, rising 10 px as it fades in, then held while the panel shows
    a_acc = progress(t, BEATS["accuracy_line"], 0.5)
    if a_acc > 0:
        paste(img, ACC_PILL, ((CH_W - ACC_PILL.width) / 2, ACC_Y0 + (1 - a_acc) * 10), a_acc)
    return img


# ---------- 3. critical minutes card: "91% vs 79% of critical minutes caught (+15 min)" ----------

BIG = 140                                 # the two percentages
A_LX, A_MX, A_RX = 210, CARD_W / 2, 670   # model, "vs", no change (centres)
A_HEAD_Y, A_NUM_Y, A_LINE_Y = 205, 392, 482
_l0, _, _r0, _ = font(BIG, 700).getbbox(f"{CRIT_MODEL}%", anchor="ms")
_l1, _, _r1, _ = font(BIG, 700).getbbox(f"{CRIT_BASE}%", anchor="ms")
_lv, _, _rv, _ = font(40, 500).getbbox("vs", anchor="ms")
assert A_LX + _r0 + 24 <= A_MX + _lv and A_MX + _rv + 24 <= A_RX + _l1, "the big numbers run into 'vs'"
assert A_LX + _l0 >= 40 and A_RX + _r1 <= CARD_W - 40, "the big numbers run past the card"
assert text_size(CRIT_LINE, 32, 600)[0] <= CARD_W - 80, CRIT_LINE


def card_a(t: float) -> Image.Image:
    w_, h_ = CARD_W, CB_Y1 - CB_Y0
    img = Image.new("RGBA", (w_, h_), (0, 0, 0, 0))
    rounded(img, (0, 0, w_ - 1, h_ - 1), 22, fill=NAVY_2)
    a1 = progress(t, BEATS["ninety_one"] - 0.55, 0.45)        # "91%" lands on "ninety-one"
    a2 = progress(t, BEATS["seventy_nine"] - 0.05, 0.45)      # "79%" lands on "seventy-nine"
    draw_text(img, (A_LX, A_HEAD_Y), BAR_NAMES[0], 26, 600, MODEL_C, a1, anchor="mm")
    draw_text(img, (A_LX, A_NUM_Y + (1 - a1) * 16), f"{CRIT_MODEL}%", BIG, 700, MODEL_C, a1, anchor="ms")
    draw_text(img, (A_MX, A_NUM_Y - 8), "vs", 40, 500, INK_2, a2, anchor="ms")
    draw_text(img, (A_RX, A_HEAD_Y), BAR_NAMES[1], 26, 600, INK_2, a2, anchor="mm")
    draw_text(img, (A_RX, A_NUM_Y + (1 - a2) * 16), f"{CRIT_BASE}%", BIG, 700, BASE_C, a2, anchor="ms")
    draw_text(img, (w_ / 2, A_LINE_Y), CRIT_LINE, 32, 600, INK, a1, anchor="mm")
    return img


# ---------- frame ----------

BASE = canvas()

def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()
    if t < ANSWER_START:
        chapter_question(img, CHAPTER, t)
        return img

    # The two metric cards stay together after the recall values land.
    a_ch = progress(t, BEATS["chart_in"], 0.55)
    if a_ch > 0:
        slide = progress(t, BEATS["and_catch"] - 0.3, 0.8)
        x = lerp(CH_X_CENTRE, CH_X_LEFT, slide)
        y = CH_Y - (1 - a_ch) * 20
        paste(img, chart_frame(t), (x, y), a_ch)

    a_recall = progress(t, BEATS["and_catch"] + 0.2, 0.6)
    if a_recall > 0:
        paste(img, card_a(t), (COL_X0 + (1 - a_recall) * 50, CB_Y0), a_recall)

    # overlay slots (no footer: no outside source in this shot)
    badge(img, "SIMULATED", alpha=progress(t, ANSWER_START, 0.4))
    legend_strip(img)
    chapter_question(img, CHAPTER, t)
    return img


STILLS = {
    "question": 1.0,
    "question_docking": 2.2,
    "answer": 3.2,
    "f1_bars": 11.8,         # both +15 values emphasised, accuracy line in (before the slide); also
                             # the source of video/team-kit/prop_M2_F1_chart.png, [MEMBER 2]'s S05 prop
    "critical_minutes": 16.4,
    "hold": DURATION - 0.05,  # F1, accuracy and recall readable together at the cut
}

if __name__ == "__main__":
    only_stills = "--stills" in sys.argv
    for name, ts in STILLS.items():
        print(still(f"S10_{name}", draw_frame(ts)))
    if not only_stills:
        print(render("S10", DURATION, draw_frame))
