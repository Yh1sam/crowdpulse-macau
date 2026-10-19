"""Shot S14 (2:47.5-3:11.0, 23.5 s): "Does acting help?" - the recorded simulation, approve vs no action.

Storyboard: docs/video/script.md section 3, row S14; claims table section 4, row S14; section 6
("Global look and tools", "motion_graphic"); shot list docs/video/shotlist.json (id S14).

Line chart of Senado Square's true density, 13:53-14:40, redrawn from the two recorded runs:
blue = approved (run A), orange = no action (run B), dotted CRITICAL line at the config threshold.
Run A markers (each tagged "run A"): first CRITICAL forecast, redirect recommended,
"approval (scripted operator), 14:14". End labels: this pair (from the CSVs) and, faint, the earlier
pair (README only). The under-chart line and the axis note follow the storyboard verbatim. As the
assumed effect is spoken, a light band marks the effect window (14:14-14:34) and the short "Assumed
diversion, not measured" chip slides in on it. From "Our failure case:" the chart slides left and a
clock panel comes in beside it, under the header "Our failure case" (source: simulation_run/README.md,
"No early warning in this scenario"): crowd build-up ~3 min vs the 5-15 min forecast horizon. On "So
staff on the ground stay in charge." a staff mark ("Staff decide", the hi-vis staff figure of S01 /
S18) lands under the dial. Senado is never drawn green. Declutter (19 Oct): no footer (the sources are
in script.md section 4), a 2-word badge qualifier, the under-chart line at 8 words, the clock panel at
10 words; the minutes above CRITICAL, the effect's size and the window label are kept for Q&A.

Data (read, never retyped):
  experiments/results/simulation_run/A_timeline.csv, B_timeline.csv  (zone == senado_square)
      sim_time, true_density                    the two lines, end values 0.75 / 0.82
      p5/p10/p15 == CRITICAL (first row)        first CRITICAL forecast 14:08:30 (run A)
      true_density >= critical (first row)      true crossing 14:08:09 (run A), 21 s before the forecast
      pending_interventions has senado_square:redirect_flow (first row)   redirect recommended 14:09:08
      minutes with true_density >= critical      32 vs 31 (this pair)
  experiments/results/simulation_run/A_events.json   ui/approve event sim_time    approval 14:14
  shared/config.json   congestion_thresholds.critical (0.70); intervention.assumed_redirect_inflow_reduction (30%)
  experiments/results/simulation_run/README.md       earlier pair 0.73 vs 0.87; window 14:14-14:34
                                                     (checked below; the storyboard text carries them)
  shared/zones.json    Senado Square's Chinese name

Run: .venv/bin/python video/mg/S14.py [--stills]  -> video/build/mg/S14.mp4, stills in video/build/mg/stills/
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timedelta

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

# ---------- timing ----------

SHOTS = json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text())
SHOT = next(s for s in SHOTS if s["id"] == "S14")
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 23.5 s
assert DURATION == 23.5, DURATION

# Seconds from the shot start. Keyed to the guide voice video/build/guide/S14.wav of 19 Oct (say -v Daniel
# -r 155, about 148 wpm; "Senado" read "Se-nah-doo"; 20.47 s of speech), which assemble.py lays 0.2 s into
# the shot (VOICE_START): clause starts are the silencedetect pauses (noise -35 dB, d 0.08 s) + 0.2 s; word
# onsets inside a clause come from synthesising prefixes of the line with the same voice. Pauses in the wav:
# 1.57-1.79, 6.15-6.38, 7.49-7.71, 8.80-9.04, 11.60-11.81, 12.52-12.76, 13.95-14.18, 16.77-16.98 and
# 17.84-18.08 s; speech ends at 20.47 s. Everything up to "not before." is unchanged since the 18 Oct guide
# (same pauses), so those keys stand; the new last sentence follows it.
# Shot times:
#   "In a recorded simulation," 0.2-1.77 | "approving the redirect" 1.99-3.37 | "left Senado less crowded" 3.37-4.89 |
#   "by the end" 4.89-5.48 | "than doing nothing," 5.48-6.35 | "but only modestly:" 6.58-7.69 |
#   "it stayed critical." 7.91-9.00 | "The effect rests on a diversion we assumed," 9.24-11.80 |
#   "not measured." 12.01-12.72 | "Our failure case:" 12.96-14.15 | "the crowd built so fast" 14.38-15.96 |
#   "the alert came with it," 15.96-16.97 | "not before." 17.18-18.04 |
#   "So staff on the ground stay in charge." 18.28-20.67 ("staff" 18.69, "stay" 19.72) | the panel holds to 23.5.
# re-key to the real voice take (the team reads at about 140 wpm, so everything moves ~5% later)
BEATS = {
    "draw": 0.5,               # "In a recorded simulation," -> both lines start drawing left to right
    "approving": 1.99,         # "approving the redirect" (run A markers appear as the sweep passes them)
    "by_the_end": 4.89,        # "by the end" -> lines reach 14:40, this pair's end values
    "doing_nothing": 5.68,     # "doing nothing" -> faint earlier-pair end values
    "only_modestly": 6.58,     # "but only modestly:" -> the under-chart line
    "stayed_critical": 7.91,   # "it stayed critical." -> the CRITICAL line pulses, region above it tinted
    "effect": 9.24,            # "The effect rests on a diversion we assumed, not measured." -> band + chip
    "failure": 12.96,          # "Our failure case:" -> chart slides left, clock panel in under its header
    "crowd_built": 14.38,      # "the crowd built so fast" -> red wedge 0 -> 3 min, then the 5-15 min ring
    "alert": 15.96,            # "the alert came with it," -> run A's first-forecast marker lifted
    "not_before": 17.18,       # "not before."
    "staff": 18.69,            # "So staff on the ground stay in charge." -> the staff mark (speech ends 20.67;
                               # the panel holds to the end)
}
CHAPTER_END = 2.0              # chapter card for about 2 s
DRAW_END = BEATS["by_the_end"] + 0.5

# ---------- data ----------

SIM = ROOT / "experiments" / "results" / "simulation_run"
CFG = json.loads((ROOT / "shared" / "config.json").read_text())
CRIT = CFG["congestion_thresholds"]["critical"]                              # 0.70
REDUCTION = CFG["intervention"]["assumed_redirect_inflow_reduction"]        # 0.30
ZONE = "senado_square"
ZONE_ZH = next(z["name_zh"] for z in zone_graph()["zones"] if z["id"] == ZONE)
README = (SIM / "README.md").read_text()
T0 = datetime.strptime("13:53:00", "%H:%M:%S")   # storyboard x range 13:53-14:40
T1 = datetime.strptime("14:40:00", "%H:%M:%S")


def tsec(hms: str) -> float:
    """Seconds after 13:53:00 for 'HH:MM' or 'HH:MM:SS'."""
    fmt = "%H:%M:%S" if hms.count(":") == 2 else "%H:%M"
    return (datetime.strptime(hms, fmt) - T0).total_seconds()


def hms(sec: float, seconds: bool = True) -> str:
    return (T0 + timedelta(seconds=sec)).strftime("%H:%M:%S" if seconds else "%H:%M")


def load_run(tag: str) -> list[dict]:
    with open(SIM / f"{tag}_timeline.csv", newline="") as fh:
        return [r for r in csv.DictReader(fh) if r["zone"] == ZONE]


def first(rows: list[dict], cond) -> str:
    return next(r["sim_time"] for r in rows if cond(r))


RUN_A, RUN_B = load_run("A"), load_run("B")
SERIES = {tag: [(tsec(r["sim_time"]), float(r["true_density"])) for r in rows] for tag, rows in (("A", RUN_A), ("B", RUN_B))}

FORECAST_T = first(RUN_A, lambda r: "CRITICAL" in (r["p5"], r["p10"], r["p15"]))            # 14:08:30
CROSS_T = first(RUN_A, lambda r: float(r["true_density"]) >= CRIT)                         # 14:08:09
REDIRECT_T = first(RUN_A, lambda r: "senado_square:redirect_flow" in r["pending_interventions"])  # 14:09:08
EVENTS_A = json.loads((SIM / "A_events.json").read_text())
APPROVE_T = next(e["sim_time"] for e in EVENTS_A if e["event"] == "ui" and e.get("action") == "approve")  # 14:14
EFFECT_MIN = 20                                    # storyboard chip: "for 20 min" (README: 14:14-14:34)
EFFECT_END_T = hms(tsec(APPROVE_T) + 60 * EFFECT_MIN, seconds=False)
LEAD_S = int(tsec(FORECAST_T) - tsec(CROSS_T))     # 21 s after the true crossing
END_A, END_B = SERIES["A"][-1][1], SERIES["B"][-1][1]


def minutes_at_or_above(rows: list[dict]) -> int:
    return len({r["sim_time"][:5] for r in rows if float(r["true_density"]) >= CRIT})


MIN_A, MIN_B = minutes_at_or_above(RUN_A), minutes_at_or_above(RUN_B)
EARLIER_A, EARLIER_B = "0.73", "0.87"              # earlier pair: README text only (no data file)

# ---------- on-screen text (storyboard wording) ----------

CHAPTER = "Does acting help?"
BADGE_DETAIL = "recorded run"           # a 2-word qualifier in the pill (the run's date is kept for Q&A)
UNDER = "At 14:40: approved 0.75 vs no action 0.82"
AXIS = "relative index, not people per m²"
CHIP = "Assumed diversion, not measured"
CLOCK_HEADER = "Our failure case"       # header above the clock panel (round-2 lock)
CLOCK_BUILD = "crowd build-up ≈3 min"
CLOCK_HORIZON = "forecast horizon 5-15 min"
STAFF_MARK = "Staff decide"             # with the staff figure, on "So staff on the ground stay in charge."
TITLE_EN = "Senado Square · crowd density"
LEG_A, LEG_B = "approved (run A)", "no action (run B)"
MARK_FORECAST = f"first CRITICAL forecast {FORECAST_T}"
MARK_FORECAST_SUB = f"{LEAD_S} s after the true crossing ({CROSS_T})"
MARK_REDIRECT = f"redirect recommended {REDIRECT_T}"
MARK_APPROVE = f"approval (scripted operator), {APPROVE_T}"

# guards: the storyboard text must still match the data files (fails loudly if a run is re-recorded)
_ost = SHOT["on_screen_text"]
for s_ in (CHAPTER, f"SIMULATED · {BADGE_DETAIL}", f"Under the chart: {UNDER}", f"Axis: {AXIS}", f"Chip: {CHIP}",
           f"Clock panel: {CLOCK_BUILD} / {CLOCK_HORIZON}", STAFF_MARK):
    assert s_ in _ost, f"not in the storyboard's on-screen text: {s_!r}"
assert f"Header above the clock panel: {CLOCK_HEADER}" in _ost
assert "Footer" not in _ost, "S14 has no footer since 19 Oct (internal sources stay in script.md section 4)"
assert f"{CLOCK_HEADER}:" in SHOT["narration"], "the clock panel enters on the spoken 'Our failure case:'"
assert "So staff on the ground stay in charge." in SHOT["narration"], "the staff mark is keyed to this sentence"
assert "No early warning in this scenario" in README, "source of 'Our failure case' (simulation_run/README.md)"
# declutter (19 Oct): the under-chart line at most 8 words, the clock panel (rows + staff mark) at most 10
assert len(UNDER.split()) <= 8 and len(f"{CLOCK_BUILD} {CLOCK_HORIZON} {STAFF_MARK}".split()) <= 10
assert f"approved {END_A:.2f} vs no action {END_B:.2f}" in UNDER
# off screen since 19 Oct but still true of the data (kept for Q&A; script.md section 4 and the shot list notes)
assert f"{MIN_A} vs {MIN_B} minutes" in SHOT["notes"], "minutes above CRITICAL no longer match the notes"
assert f"earlier pair {EARLIER_A} vs {EARLIER_B}" in SHOT["visual"] and f"{EARLIER_A} vs {EARLIER_B}" in README
# the chip says the effect is assumed and unmeasured; its size stays with the config and the notes, and is
# never phrased as a share of the flow diverting
assert CHIP.startswith("Assumed") and "not measured" in CHIP and "divert" not in CHIP.replace("diversion", "")
assert f"{round(100 * REDUCTION)}% less attractive for {EFFECT_MIN} minutes" in SHOT["notes"]
assert f"{APPROVE_T}–{EFFECT_END_T}" in README
assert f"CRITICAL line at {CRIT:.2f}" in SHOT["visual"]
for v in (FORECAST_T, CROSS_T, REDIRECT_T, f"approval (scripted operator), {APPROVE_T}", f"{LEAD_S} s after"):
    assert v in SHOT["visual"], f"A_timeline / A_events no longer match the storyboard: {v!r}"
assert all(d >= CRIT for tag in "AB" for (s, d) in SERIES[tag] if s >= tsec(first(RUN_A if tag == "A" else RUN_B, lambda r: float(r["true_density"]) >= CRIT)))

# ---------- colours ----------

BLUE_T = lerp(BLUE, INK, 0.42)       # text tints of the line colours (more legible on navy)
ORANGE_T = lerp(ORANGE, INK, 0.18)
BLUE_T = tuple(int(c) for c in BLUE_T)
ORANGE_T = tuple(int(c) for c in ORANGE_T)
LINE_A_C = tuple(int(c) for c in lerp(BLUE, INK, 0.12))
LINE_B_C = ORANGE

# ---------- layout ----------

CH_W, CH_H, CH_Y = 1240, 640, 140      # chart panel
CH_X_CENTRE = (W - CH_W) // 2          # 340 while the chart is alone
CH_X_LEFT = 60                         # from "and the crowd built so fast"
CK_X, CK_Y, CK_W, CK_H = 1340, 196, 520, 584   # clock panel, under its header (bottom level with the chart's)
HEADER_BASE = 170                      # "Our failure case": cap top level with the chart panel's top (y 140)
UNDER_Y = 812                          # baseline of the under-chart line (below the panel)

PX0, PX1 = 100, 1040                   # plot x for 13:53 and 14:40 (local to the panel)
PY_TOP, PY_BOT = 240, 575              # plot y for the top and bottom of the value range
V_TOP, V_BOT = 1.0, 0.35
SPAN_S = (T1 - T0).total_seconds()


def xp(sec: float) -> float:
    return PX0 + (PX1 - PX0) * sec / SPAN_S


def yp(v: float) -> float:
    return PY_TOP + (V_TOP - v) / (V_TOP - V_BOT) * (PY_BOT - PY_TOP)


def value_at(series, sec: float) -> float:
    for (s0, v0), (s1, v1) in zip(series, series[1:]):
        if s0 <= sec <= s1:
            return v0 + (v1 - v0) * (sec - s0) / (s1 - s0) if s1 > s0 else v1
    return series[-1][1]


Y_CRIT = yp(CRIT)
BAND_X0, BAND_X1 = xp(tsec(APPROVE_T)), xp(tsec(APPROVE_T) + 60 * EFFECT_MIN)
BAND_Y0 = 112                          # the band reaches up into the header, where its label and chip sit
CHIP_Y = 148

# run A markers: staircase of labels in the empty region under the CRITICAL line, the earliest lowest
MARKERS = [  # (key, time, label, label baseline y)
    ("forecast", tsec(FORECAST_T), MARK_FORECAST, Y_CRIT + 106),   # room for its "alert" box under the redirect pill
    ("redirect", tsec(REDIRECT_T), MARK_REDIRECT, Y_CRIT + 63),
    ("approve", tsec(APPROVE_T), MARK_APPROVE, Y_CRIT + 26),
]
# the forecast "alert" box (yb-26 .. yb+36) keeps a gap under the redirect pill (yb+7) and above the 0.4 gridline
assert MARKERS[0][3] - 26 >= MARKERS[1][3] + 7 + 8, "alert box crowds the redirect label"
assert MARKERS[0][3] + 36 <= yp(0.4) - 8, "alert box reaches the 0.4 gridline"

# ---------- helpers ----------


def rgba(c, a: float = 1.0) -> tuple[int, int, int, int]:
    return (*[int(v) for v in c[:3]], int(round(255 * clamp(a))))


def paste(dst: Image.Image, src: Image.Image, xy, alpha: float = 1.0) -> None:
    if alpha <= 0:
        return
    if alpha < 1:
        src = src.copy()
        src.putalpha(src.getchannel("A").point(lambda v: int(v * alpha)))
    dst.alpha_composite(src, (int(round(xy[0])), int(round(xy[1]))))


class Sprite:
    """Pre-rendered text: paste with the baseline-left (or other) anchor point at (x, y)."""

    def __init__(self, segs, size: int, pad: int = 6):
        fonts = [text_font(s, size, w) for s, _, w in segs]
        widths = [f.getlength(s) for (s, _, _), f in zip(segs, fonts)]
        asc = max(f.getmetrics()[0] for f in fonts)
        desc = max(f.getmetrics()[1] for f in fonts)
        self.w, self.asc, self.desc = sum(widths), asc, desc
        self.img = Image.new("RGBA", (int(self.w) + 2 * pad + 1, asc + desc + 2 * pad), (0, 0, 0, 0))
        d = ImageDraw.Draw(self.img)
        x = pad
        for (s, fill, _), f, wd in zip(segs, fonts, widths):
            d.text((x, pad + asc), s, font=f, fill=rgba(fill), anchor="ls")
            x += wd
        self.pad = pad

    def draw(self, dst: Image.Image, x: float, y: float, alpha: float = 1.0, align: str = "l") -> None:
        """(x, y) is the baseline; align l / m / r horizontally."""
        dx = {"l": 0, "m": self.w / 2, "r": self.w}[align]
        paste(dst, self.img, (x - dx - self.pad, y - self.asc - self.pad), alpha)


def T(text: str, size: int, weight: int = 500, fill=INK) -> Sprite:
    return Sprite([(text, fill, weight)], size)


def ss_layer(size, draw_fn, ss: int = 3) -> Image.Image:
    """Draws with draw_fn(ImageDraw, k) at ss x scale and downsamples (antialiased shapes)."""
    big = Image.new("RGBA", (size[0] * ss, size[1] * ss), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), ss)
    return big.resize(size, Image.LANCZOS)


def dashed_v(d: ImageDraw.ImageDraw, x: float, y0: float, y1: float, fill, width: int = 2, dash: int = 6, gap: int = 5) -> None:
    y = y0
    while y < y1:
        d.line([(x, y), (x, min(y + dash, y1))], fill=fill, width=width)
        y += dash + gap


def dot_sprite(r: float, fill, ring=NAVY_2, ring_w: float = 2.5) -> Image.Image:
    s = int(2 * (r + ring_w) + 4)

    def fn(d, k):
        c = s * k / 2
        d.ellipse((c - (r + ring_w) * k, c - (r + ring_w) * k, c + (r + ring_w) * k, c + (r + ring_w) * k), fill=rgba(ring))
        d.ellipse((c - r * k, c - r * k, c + r * k, c + r * k), fill=rgba(fill))
    return ss_layer((s, s), fn, 4)


def put_dot(dst: Image.Image, spr: Image.Image, x: float, y: float, alpha: float = 1.0) -> None:
    paste(dst, spr, (x - spr.width / 2, y - spr.height / 2), alpha)


# ---------- chart: static background ----------

def chart_static() -> Image.Image:
    img = Image.new("RGBA", (CH_W, CH_H), (0, 0, 0, 0))
    rounded(img, (0, 0, CH_W - 1, CH_H - 1), 22, fill=NAVY_2)
    # title (Chinese name in Noto Sans TC, the rest in Geist, on one baseline)
    Sprite([(ZONE_ZH, INK, 700), ("  " + TITLE_EN, INK, 700)], 26).draw(img, 40, 54)
    # legend
    d = ImageDraw.Draw(img)
    x, y = 40, 92
    for label, col in ((LEG_A, LINE_A_C), (LEG_B, LINE_B_C)):
        d.rounded_rectangle((x, y - 10, x + 34, y - 4), 3, fill=rgba(col))
        T(label, 22, 500, INK_2).draw(img, x + 46, y)
        x += 46 + T(label, 22, 500).w + 44
    # axis note, above the y axis
    T(AXIS, 20, 500, INK_2).draw(img, 40, PY_TOP - 26)
    # gridlines and y ticks
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    for v in (0.4, 0.6, 0.8, 1.0):
        dl.line([(PX0, yp(v)), (PX1, yp(v))], fill=rgba(INK_3, 0.28), width=1)
    dl.line([(PX0, PY_BOT), (PX1, PY_BOT)], fill=rgba(INK_3, 0.6), width=2)
    # x ticks
    for hm in ("13:53", "14:00", "14:10", "14:20", "14:30", "14:40"):
        xx = xp(tsec(hm))
        dl.line([(xx, PY_BOT), (xx, PY_BOT + 7)], fill=rgba(INK_3, 0.8), width=2)
    img.alpha_composite(lay)
    for v in (0.4, 0.6, 0.8, 1.0):
        T(f"{v:.1f}", 20, 500, INK_3).draw(img, PX0 - 16, yp(v) + 7, align="r")
    for hm in ("13:53", "14:00", "14:10", "14:20", "14:30", "14:40"):
        T(hm, 20, 500, INK_3).draw(img, xp(tsec(hm)), PY_BOT + 32, align="m")
    # dotted CRITICAL line and its label
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    xx = PX0
    while xx < PX1:
        dl.line([(xx, Y_CRIT), (min(xx + 6, PX1), Y_CRIT)], fill=rgba(CRITICAL), width=3)
        xx += 12
    img.alpha_composite(lay)
    T(f"CRITICAL {CRIT:.2f}", 20, 700, CRITICAL).draw(img, PX0 + 10, Y_CRIT - 10)
    return img


CHART_BG = chart_static()


def line_layer(series, colour) -> Image.Image:
    def fn(d, k):
        pts = [(xp(s) * k, yp(v) * k) for s, v in series]
        d.line(pts, fill=rgba(colour), width=5 * k, joint="curve")
    return ss_layer((CH_W, CH_H), fn, 3)


LINES = {"A": line_layer(SERIES["A"], LINE_A_C), "B": line_layer(SERIES["B"], LINE_B_C)}
HEAD = {"A": dot_sprite(7, LINE_A_C), "B": dot_sprite(7, LINE_B_C)}
MARK_DOT = dot_sprite(6, INK, ring=NAVY_2)

# CRITICAL emphasis: a glow along the dotted line, and a faint tint over the region above it
_glow = Image.new("RGBA", (CH_W, CH_H), (0, 0, 0, 0))
ImageDraw.Draw(_glow).line([(PX0, Y_CRIT), (PX1, Y_CRIT)], fill=rgba(CRITICAL, 0.9), width=8)
CRIT_GLOW = _glow.filter(ImageFilter.GaussianBlur(6))
ImageDraw.Draw(CRIT_GLOW).line([(PX0, Y_CRIT), (PX1, Y_CRIT)], fill=rgba(lerp(CRITICAL, INK, 0.3), 0.85), width=2)
CRIT_WASH = Image.new("RGBA", (int(PX1 - PX0), int(Y_CRIT - PY_TOP)), rgba(CRITICAL, 1.0))

# band (assumed effect window)
BAND = Image.new("RGBA", (int(round(BAND_X1 - BAND_X0)), int(PY_BOT - BAND_Y0)), rgba(INK, 1.0))
_be = Image.new("RGBA", BAND.size, (0, 0, 0, 0))
_bd = ImageDraw.Draw(_be)
dashed_v(_bd, 0, 0, BAND.height, rgba(INK_2, 1.0), width=2)
dashed_v(_bd, BAND.width - 2, 0, BAND.height, rgba(INK_2, 1.0), width=2)
BAND_EDGES = _be
# the band's own "assumed effect window 14:14-14:34" label left on 19 Oct: the chip on the band says it


def chip_sprite() -> Image.Image:
    """One line: "Assumed" in amber, the rest in ink, on an amber-edged pill at the band's top."""
    head, rest = CHIP.split(" ", 1)
    size, pad_x, pad_y = 26, 20, 14
    spr = Sprite([(head, WARNING, 700), (" " + rest, INK, 600)], size)
    img = Image.new("RGBA", (int(spr.w + 2 * pad_x), pad_y * 2 + spr.asc + spr.desc - 6), (0, 0, 0, 0))
    rounded(img, (0, 0, img.width - 1, img.height - 1), 12, fill=NAVY_3, outline=WARNING, width=2)
    spr.draw(img, pad_x, pad_y + spr.asc - 3)
    return img


CHIP_IMG = chip_sprite()
assert CHIP_Y + CHIP_IMG.height < PY_TOP - 4, "chip reaches the plot"
assert BAND_X0 + CHIP_IMG.width < CH_W - 20, "chip does not fit in the panel"

# run A marker labels: [run A] pill + text
PILL = Image.new("RGBA", (int(T("run A", 20, 700).w) + 22, 28), (0, 0, 0, 0))
rounded(PILL, (0, 0, PILL.width - 1, 27), 14, fill=BLUE)
T("run A", 20, 700, INK).draw(PILL, 11, 21)
MARK_TEXT = {k: T(lbl, 22, 600, INK) for k, _, lbl, _ in MARKERS}
MARK_SUB = T(MARK_FORECAST_SUB, 20, 500, INK_2)

# end labels
END_X = PX1 + 18
END_THIS = T("this pair", 20, 600, INK_2)
END_VAL = {"A": T(f"{END_A:.2f}", 30, 700, BLUE_T), "B": T(f"{END_B:.2f}", 30, 700, ORANGE_T)}
END_EARLIER = T("earlier pair", 20, 500, INK_3)
END_EARLIER_V = Sprite([(EARLIER_A, lerp(BLUE_T, INK_3, 0.45), 600), (" vs ", INK_3, 500), (EARLIER_B, lerp(ORANGE_T, INK_3, 0.45), 600)], 20)

# under-chart line (below the panel): "At 14:40: approved 0.75 vs no action 0.82", the values in the line colours
_pre, _rest = UNDER.split("approved ", 1)
_va, _vb = _rest.split(" vs no action ", 1)
_UNDER_RUNS = [(_pre, INK_2, 500), ("approved ", INK, 500), (_va, BLUE_T, 700), (" vs no action ", INK, 500), (_vb, ORANGE_T, 700)]
UNDER_S = Sprite(_UNDER_RUNS, 26)
assert "".join(s for s, _, _ in _UNDER_RUNS) == UNDER


# sweep timing: when the drawing reaches a given time on the x axis
def sweep_x(t: float) -> float:
    return PX0 + (PX1 - PX0) * progress(t, BEATS["draw"], DRAW_END - BEATS["draw"])


def sweep_time(sec: float) -> float:
    """Shot time at which the sweep passes simulated time `sec` (bisection on the eased sweep)."""
    target, lo, hi = xp(sec), BEATS["draw"], DRAW_END
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if sweep_x(mid) < target else (lo, mid)
    return hi


MARK_T = {k: sweep_time(s) for k, s, _, _ in MARKERS}


def chart_frame(t: float) -> Image.Image:
    img = CHART_BG.copy()
    xc = sweep_x(t)

    # region above CRITICAL tinted from "it stayed critical"
    sc = BEATS["stayed_critical"]
    wash = 0.075 * progress(t, sc, 0.5) + 0.06 * fade(t, sc, sc + 1.6, 0.5)
    paste(img, CRIT_WASH, (PX0, PY_TOP), wash)

    # assumed effect window (band grows from the approval marker as the effect is spoken)
    ef = BEATS["effect"]
    g = progress(t, ef, 0.7)
    if g > 0:
        bw = max(1, int(round(BAND.width * g)))
        paste(img, BAND.crop((0, 0, bw, BAND.height)), (BAND_X0, BAND_Y0), 0.075 * min(1, g * 1.6))
        paste(img, BAND_EDGES.crop((0, 0, bw, BAND.height)), (BAND_X0, BAND_Y0), 0.45 * g)

    # CRITICAL line pulse
    pulse = fade(t, sc - 0.1, sc + 1.5, 0.45)
    paste(img, CRIT_GLOW, (0, 0), pulse)

    # run A marker stems and labels (drawn as the sweep passes them)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    alert = progress(t, BEATS["alert"] - 0.2, 0.5)
    for key, sec, _, yb in MARKERS:
        a = progress(t, MARK_T[key], 0.45)
        if a <= 0:
            continue
        x = xp(sec)
        top = yp(value_at(SERIES["A"], sec)) + 8
        bottom = yb - 8
        stem = lerp(INK_2, INK, alert) if key == "forecast" else INK_2
        dashed_v(dl, x, top + (bottom - top) * (1 - a), bottom, rgba(stem, 0.9 * a), width=2)
    img.alpha_composite(lay)
    for key, sec, _, yb in MARKERS:
        a = progress(t, MARK_T[key] + 0.1, 0.45)
        if a <= 0:
            continue
        x = xp(sec) + 10
        if key == "forecast" and alert > 0:   # "the alert came with it": the first forecast marker is lifted
            w_ = PILL.width + 10 + MARK_SUB.w + 4
            w_ = max(w_, PILL.width + 10 + MARK_TEXT[key].w)
            rounded(img, (x - 8, yb - 26, x + w_ + 14, yb + 36), 10, fill=NAVY_3, outline=INK_3, width=2, alpha=alert)
        paste(img, PILL, (x + (1 - a) * 10, yb - 21), a)
        MARK_TEXT[key].draw(img, x + PILL.width + 10 + (1 - a) * 10, yb, a)
        if key == "forecast":
            MARK_SUB.draw(img, x + PILL.width + 10, yb + 27, alert)

    # the two lines, revealed left to right, with a head dot
    for tag in ("B", "A"):
        if xc <= PX0:
            continue
        img.alpha_composite(LINES[tag].crop((0, 0, int(xc) + 1, CH_H)))
        series = SERIES[tag]
        last_s = series[-1][0]
        sec = min((xc - PX0) / (PX1 - PX0) * SPAN_S, last_s)
        put_dot(img, HEAD[tag], xp(sec), yp(value_at(series, sec)))

    # marker dots on the run A line
    for key, sec, _, _ in MARKERS:
        a = progress(t, MARK_T[key], 0.3)
        if a > 0:
            put_dot(img, MARK_DOT, xp(sec), yp(value_at(SERIES["A"], sec)), a)

    # end labels: this pair (from the CSVs), then the earlier pair, faint
    e1 = progress(t, DRAW_END - 0.15, 0.45)
    if e1 > 0:
        ya, yb_ = yp(END_A), yp(END_B)
        END_THIS.draw(img, END_X, yb_ - 26, e1)
        END_VAL["B"].draw(img, END_X + (1 - e1) * 10, yb_ + 11, e1)
        END_VAL["A"].draw(img, END_X + (1 - e1) * 10, ya + 11, e1)
        e2 = progress(t, BEATS["doing_nothing"], 0.5)
        END_EARLIER.draw(img, END_X, ya + 48, e2)
        END_EARLIER_V.draw(img, END_X, ya + 74, e2)

    # the limit chip, on the band's top
    c = progress(t, ef + 0.15, 0.5)
    if c > 0:
        paste(img, CHIP_IMG, (BAND_X0 + 4, CHIP_Y - (1 - c) * 16), c)
    return img


# ---------- clock panel ----------

DIAL_C = (260, 166)
R_FACE, R_WEDGE, R_RING_IN, R_RING_OUT, R_LABEL = 88, 79, 97, 114, 134


def ang(minutes: float) -> float:
    return -90 + 6 * minutes


def clock_static() -> Image.Image:
    img = Image.new("RGBA", (CK_W, CK_H), (0, 0, 0, 0))
    rounded(img, (0, 0, CK_W - 1, CK_H - 1), 22, fill=NAVY_2)
    cx, cy = DIAL_C

    def fn(d, k):
        d.ellipse(((cx - R_FACE) * k, (cy - R_FACE) * k, (cx + R_FACE) * k, (cy + R_FACE) * k), fill=rgba(NAVY_3))
        d.ellipse(((cx - R_RING_OUT) * k, (cy - R_RING_OUT) * k, (cx + R_RING_OUT) * k, (cy + R_RING_OUT) * k),
                  outline=rgba(INK_3, 0.35), width=int(2 * k))
        for m in range(0, 60, 5):
            a = math.radians(ang(m))
            r0, r1 = (R_FACE - 14, R_FACE - 3)
            d.line([((cx + r0 * math.cos(a)) * k, (cy + r0 * math.sin(a)) * k),
                    ((cx + r1 * math.cos(a)) * k, (cy + r1 * math.sin(a)) * k)], fill=rgba(INK_3), width=int(3 * k))
    img.alpha_composite(ss_layer((CK_W, CK_H), fn, 3))
    for m, lab in ((0, "0"), (5, "5"), (10, "10"), (15, "15 min")):
        a = math.radians(ang(m))
        x, y = cx + R_LABEL * math.cos(a), cy + R_LABEL * math.sin(a)
        align = "m" if m == 0 else "l"
        x = x if m == 0 else x - 6
        T(lab, 20, 600, INK_2).draw(img, x, y + 7, align=align)
    return img


CLOCK_BG = clock_static()
ROW_Y = (330, 374)
DIVIDER_Y = 412
ROW_S = (T(CLOCK_BUILD, 28, 700, INK), T(CLOCK_HORIZON, 28, 700, INK))
HEADER_S = T(CLOCK_HEADER, 34, 700, INK)
# the staff mark under the divider: two hi-vis staff figures (style.staff_icon, as in S01 / S18) and the words
STAFF_ICON_W, STAFF_ICON_H = 116, 92
STAFF_ICON = ss_layer((STAFF_ICON_W, STAFF_ICON_H),
                      lambda d, k: [staff_icon(d, cx * k, 54 * k, 1.45 * k) for cx in (28, 88)], 3)
STAFF_S = T(STAFF_MARK, 36, 700, INK)
STAFF_ICON_XY = (40, DIVIDER_Y + 34)
STAFF_BASE = STAFF_ICON_XY[1] + 62                      # the words' baseline, level with the figures' middle
assert STAFF_ICON_XY[1] + STAFF_ICON_H <= CK_H - 24, "the staff mark runs into the panel's bottom edge"
assert STAFF_ICON_XY[0] + STAFF_ICON_W + 20 + STAFF_S.w <= CK_W - 40, "the staff mark is wider than the panel"


def clock_frame(t: float) -> Image.Image:
    img = CLOCK_BG.copy()
    cb = BEATS["crowd_built"]
    w1 = progress(t, cb + 0.1, 0.9)           # red wedge: 0 -> 3 min, on "the crowd built so fast"
    w2 = progress(t, cb + 1.0, 0.9)           # cyan ring: 5 -> 15 min, done as "the alert came" ends
    cx, cy = DIAL_C

    def fn(d, k):
        if w2 > 0:
            d.arc(((cx - R_RING_OUT) * k, (cy - R_RING_OUT) * k, (cx + R_RING_OUT) * k, (cy + R_RING_OUT) * k),
                  ang(5), ang(5 + 10 * w2), fill=rgba(CYAN), width=int((R_RING_OUT - R_RING_IN) * k))
        if w1 > 0:
            d.pieslice(((cx - R_WEDGE) * k, (cy - R_WEDGE) * k, (cx + R_WEDGE) * k, (cy + R_WEDGE) * k),
                       ang(0), ang(3 * w1), fill=rgba(CRITICAL))
            a = math.radians(ang(3 * w1))
            d.line([(cx * k, cy * k), ((cx + (R_WEDGE + 4) * math.cos(a)) * k, (cy + (R_WEDGE + 4) * math.sin(a)) * k)],
                   fill=rgba(INK), width=int(4 * k))
        d.ellipse(((cx - 7) * k, (cy - 7) * k, (cx + 7) * k, (cy + 7) * k), fill=rgba(INK))
    if w1 > 0 or w2 > 0:
        # draw only the dial's box at 3x (cheap), then place it
        box = (cx - R_LABEL, cy - R_LABEL, cx + R_LABEL, cy + R_LABEL)
        sub_w, sub_h = box[2] - box[0], box[3] - box[1]

        def fn_local(d, k):
            fn(_ShiftDraw(d, -box[0] * k, -box[1] * k), k)
        img.alpha_composite(ss_layer((sub_w, sub_h), fn_local, 3), (box[0], box[1]))
    else:
        ImageDraw.Draw(img).ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=rgba(INK))

    # rows: swatch + label, each with its sweep
    d = ImageDraw.Draw(img)
    for i, (yb, spr, col, a) in enumerate(zip(ROW_Y, ROW_S, (CRITICAL, CYAN), (w1, w2))):
        a = clamp(a * 1.6)
        if a <= 0:
            continue
        rounded(img, (40, yb - 22, 62, yb), 5, fill=col, alpha=a)
        spr.draw(img, 76 + (1 - a) * 10, yb, a)
    # divider and the staff mark: they come in on "staff" in "So staff on the ground stay in charge."
    sa = progress(t, BEATS["staff"] - 0.3, 0.45)
    if sa > 0:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(lay).line([(40, DIVIDER_Y), (CK_W - 40, DIVIDER_Y)], fill=rgba(INK_3, 0.5 * sa), width=2)
        img.alpha_composite(lay)
        dy = (1 - sa) * 12
        paste(img, STAFF_ICON, (STAFF_ICON_XY[0], STAFF_ICON_XY[1] + dy), sa)
        STAFF_S.draw(img, STAFF_ICON_XY[0] + STAFF_ICON_W + 20, STAFF_BASE + dy, sa)
    return img


class _ShiftDraw:
    """ImageDraw proxy that offsets every coordinate (lets the dial be drawn in a small box)."""

    def __init__(self, d: ImageDraw.ImageDraw, dx: float, dy: float):
        self.d, self.dx, self.dy = d, dx, dy

    def _b(self, b):
        return (b[0] + self.dx, b[1] + self.dy, b[2] + self.dx, b[3] + self.dy)

    def arc(self, b, *a, **kw):
        self.d.arc(self._b(b), *a, **kw)

    def pieslice(self, b, *a, **kw):
        self.d.pieslice(self._b(b), *a, **kw)

    def ellipse(self, b, *a, **kw):
        self.d.ellipse(self._b(b), *a, **kw)

    def line(self, pts, *a, **kw):
        self.d.line([(x + self.dx, y + self.dy) for x, y in pts], *a, **kw)


# ---------- frame ----------

BASE = canvas()


def draw_frame(t: float) -> Image.Image:
    img = BASE.copy()

    # chart panel: fades in, then slides left as the clock panel comes in
    a_ch = progress(t, 0.0, 0.5)
    slide = progress(t, BEATS["failure"] - 0.5, 0.85)
    cx = lerp(CH_X_CENTRE, CH_X_LEFT, slide)
    paste(img, chart_frame(t), (cx, CH_Y + (1 - a_ch) * 18), a_ch)
    # under-chart line, centred under the panel
    UNDER_S.draw(img, cx + CH_W / 2, UNDER_Y, progress(t, BEATS["only_modestly"] - 0.1, 0.5), align="m")

    # clock panel beside the chart, under its header "Our failure case"
    a_ck = progress(t, BEATS["failure"] - 0.15, 0.7)
    if a_ck > 0:
        dx = CK_X + (1 - a_ck) * 60
        paste(img, clock_frame(t), (dx, CK_Y), a_ck)
        rounded(img, (int(dx), HEADER_BASE - 25, int(dx) + 7, HEADER_BASE), 3, fill=CRITICAL, alpha=a_ck)
        HEADER_S.draw(img, dx + 21, HEADER_BASE, a_ck)

    # overlay slots
    chapter_card(img, CHAPTER, fade(t, 0.0, CHAPTER_END, 0.3))
    badge(img, "SIMULATED", BADGE_DETAIL, alpha=progress(t, 0.1, 0.4))
    legend_strip(img)
    return img


STILLS = {
    "card": 1.5,
    "end_values": 7.3,
    "critical": 8.5,
    "chip": 11.0,
    "header": 14.0,
    "clock": 16.7,
    "staff": 19.2,
    "end": 23.4,
}

if __name__ == "__main__":
    print(f"S14: {DURATION} s; forecast {FORECAST_T}, crossing {CROSS_T} (+{LEAD_S} s), redirect {REDIRECT_T}, "
          f"approval {APPROVE_T}, window {APPROVE_T}-{EFFECT_END_T}, end {END_A:.4f} vs {END_B:.4f}, "
          f"minutes >= CRITICAL {MIN_A} vs {MIN_B}, threshold {CRIT}")
    for name, ts in STILLS.items():
        print(still(f"S14_{name}", draw_frame(ts)))
    if "--stills" not in sys.argv:
        print(render("S14", DURATION, draw_frame))
