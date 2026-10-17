"""Shot S17 (3:35.0-3:53.5, 18.5 s): "Can it happen?" Feasibility and the intended user.

Storyboard: docs/video/script.md section 3, row S17; claims table section 4, rows S17; section 6
"motion_graphic" (S17: the cost panel appears only after the team approves docs/cost-estimate.md,
labelled TEAM ESTIMATE, otherwise the operator card holds, never an empty panel; the "No partner
yet" chip is readable on its own) and "Never say or show"; shot list docs/video/shotlist.json (id S17).

Beats (shot seconds, keyed to the guide voice; re-key to the real voice take):
0-4.95      "Phones on temporary mounts can serve one festival, then move to the next": a phone-on-
            clamp kit hops between festival pages of a calendar (hops on "then move" and "the next")
            while a pole-mounted counting camera stays bolted in place (badge ILLUSTRATION, design
            intent, not field-tested).
4.95-9.12   "The intended user is Macau's police, who run crowd control": the operator card (generic
            shapes, no emblems) and, on "Macau's police", the separate "No partner yet" chip; footer
            Law 14/2018, Art. 3. The cost panel would slide in beside the card only if the shot
            list's cost text were filled (labelled TEAM ESTIMATE, and the footer then adds
            "cost: docs/cost-estimate.md"); it is still a bracketed placeholder, so it is not drawn.
9.12-13.88  "The whole chain runs end to end in simulation": slate for the team's B-roll of a real
            pytest run (hard cuts in and out, so the footage drops straight in; the window is about
            4.8 s, so the take must run at least 5 s). From 10.7 s the counters 54 · 24 · 33 · 13 tick
            up over it and the total lands on 124 with "a hundred" (12.1), holding ~1.8 s through
            "and twenty-four automated" (badge LIVE SOFTWARE).
13.88-18.5  the roadmap arrow alone, four stations (cut on "tests").

Data (read, never retyped):
  docs/video/shotlist.json, S17             chapter card, intended-user line, chip, law footer, cost
                                            text, the counters line (the four suite counts and their
                                            sum: 54 / 24 / 33 / 13 = 124, recounted 16-17 Oct) and
                                            roadmap stations, split verbatim from on_screen_text; the
                                            slate wording from "visual"
  docs/testing.md, section 1 table          cross-check of the four counts (iOS must agree; the other
                                            three are reported if the table still has older counts)
  docs/deployment.md, "Operational model"   the peak periods on the calendar pages (not its cost table)
  docs/video/script.md, row S17             cross-check: the narration and every quoted line
Footer sources: docs/deployment.md, Law 14/2018 (claims table), experiments/results/simulation_run/,
docs/testing.md, experiments/datasets/melbourne/, docs/experiment-protocol.md, brief-evidence.md s. 6.

Run: .venv/bin/python video/mg/S17.py [--stills-only]
  -> video/build/mg/S17.mp4, video/build/overlays/S17.mov (chapter card, badge, footer and, over the
     B-roll, the counters, to lay over the team's footage) and stills in video/build/mg/stills/.
"""
from __future__ import annotations

import json
import math
import re
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

NAME = "S17"
SHOT = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == NAME)
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 18.5 s
assert DURATION == 18.5, DURATION

# ---------- timing ----------
# Shot seconds. Keyed to the guide voice video/build/guide/S17.wav of 17 Oct (say -v Daniel -r 155,
# about 148 wpm; 14.74 s of speech, with 124 spoken "a hundred and twenty-four" as guide.py and
# script.md 5C say it), which assemble.py lays 0.2 s into the shot: clause starts are the
# silencedetect boundaries (noise -35 dB, d 0.12 s: 3.25, 4.75, 7.25, 8.92, 11.71 s into the file)
# + 0.2 s; word onsets inside the last clause come from its 10 ms spectrum (into the file: the /h/ of
# "hundred" 11.90, the /t/ of "twenty" 12.39, the /f/ of "four" 12.74, the /t/ of "tests" 13.68,
# the /p/ of "passing" 14.08; speech ends 14.71), cross-checked against `say` prefixes of the
# clause. Re-key to the real voice take (about 140 wpm, so everything after 0.2 s moves about 5% later).
BEATS = {
    "phones": 0.2,         # "Phones on temporary mounts" -> calendar up, kit drops onto page 1
    "kit_down": 0.45,      # kit drop starts (lands ~1.05 s)
    "serve_one": 1.75,     # "can serve one festival" -> page 1 lights, the kit counts
    "then_move": 3.45,     # "then move" (clause 3.45-4.72) -> hop to page 2; "bolted in place" on the pole
    "to_the_next": 4.05,   # "the next" -> hop to page 3 (page 2 holds 3.75-4.05)
    "user": 4.95,          # "The intended user is Macau's police" (4.95-7.18) -> operator card, law footer
    "police": 6.27,        # "Macau's police" -> the separate "No partner yet" chip
    #                        "who run crowd control" (7.45-8.89): the card, chip and footer hold
    "broll": 9.12,         # "The whole chain runs end to end in simulation" (9.12-11.68) -> hard cut to B-roll
    "counters": 10.7,      # "in simulation" -> counters over the B-roll (spec: "from about 11.5 s" at 140 wpm)
    "with_total": 11.91,   # "with a hundred and twenty-four automated tests passing" (11.91-14.91)
    "total": 12.1,         # "a | hundred" -> the total lands and holds through "... and twenty-four automated"
    "roadmap": 13.88,      # "tests" (onset 13.88) -> hard cut to the roadmap, alone to the end (4.62 s)
}
CHAPTER_END = 2.2
HOP = 0.30                 # seconds per hop
HOP_LIFT = 90              # px; the kit stays below the event names in the page header
DROP_LIFT = 80             # px; the kit fades in while it drops onto page 1

# ---------- data ----------

DEPLOY = (ROOT / "docs" / "deployment.md").read_text()
_opmodel = DEPLOY.split("## Operational model", 1)[1].split("\n## ", 1)[0]
PEAKS = [p.strip() for p in re.search(r"peak periods \(([^)]*)\)", _opmodel).group(1).split(",")]
ZH = {"Golden Week": "黃金周", "Grand Prix": "格蘭披治大賽車", "Chinese New Year": "農曆新年"}
# calendar order from October: Golden Week, Grand Prix, Chinese New Year (no dates are shown)
EVENTS = [(p, ZH[p]) for p in ("Golden Week", "Grand Prix", "Chinese New Year") if p in PEAKS]
assert len(EVENTS) == 3, PEAKS

OST = [p.strip() for p in SHOT["on_screen_text"].split(" | ")]
assert len(OST) == 7, OST   # chapter card + the six parts below; a new part needs a new drawing


def ost_part(label: str) -> str:
    """The text after '<label>:' or '<label> (<timing note>):' (the timing notes change with each
    re-key, the labels do not)."""
    rx = re.compile(rf"^{re.escape(label)}(?: \([^)]*\))?: (.*)$")
    hits = [m.group(1).strip() for m in map(rx.match, OST) if m]
    assert len(hits) == 1, (label, OST)
    return hits[0]


CHAPTER = ost_part("Chapter card")                                      # Can it happen?
USER_LINE = "Intended user: " + ost_part("Intended user")               # shown whole, as written
USER_HEAD, USER_BODY = USER_LINE.split(": ", 1)
USER_HEAD += ":"
USER_NAME, USER_ROLE = USER_BODY.split(" · ")                           # Public Security Police Force / gets counts, never images
CHIP = ost_part("Chip")                                                 # No partner yet
LAW_FOOTER = ost_part("Footer")                                         # Law 14/2018, Art. 3: ...
COST_TEXT = ost_part("Cost panel")
COUNTERS_LINE = ost_part("Counters")                                    # Python 54 · dashboard 24 · ... = 124 automated tests
ROAD = ost_part("Roadmap").split(" → ")
STATIONS = []                                                          # (name, aside) exactly as written
for s_ in ROAD:
    m = re.match(r"^(.*?)(?: (\([^)]*\)))?$", s_)
    STATIONS.append((m.group(1), m.group(2) or ""))
assert len(STATIONS) == 4, ROAD

# the four suite counts and their sum, from the shot list's counters line (recounted 16-17 Oct:
# pytest --collect-only 54, dashboard vitest 24, SketchFuture vitest 33; iOS 13 from docs/testing.md)
TOTAL_LABEL = "automated tests"
_cm = re.fullmatch(rf"(.+) = (\d+) {TOTAL_LABEL}", COUNTERS_LINE)
assert _cm, COUNTERS_LINE
SUITES = []
for _p in _cm.group(1).split(" · "):
    _sm = re.fullmatch(r"(.+) (\d+)", _p)
    assert _sm, _p
    SUITES.append((_sm.group(1), int(_sm.group(2))))
assert [label for label, _ in SUITES] == ["Python", "dashboard", "SketchFuture", "iOS"], SUITES
TOTAL = sum(n for _, n in SUITES)
assert TOTAL == int(_cm.group(2)), f"counters line: the suites sum to {TOTAL}, not {_cm.group(2)}"

# cross-check with docs/testing.md, section 1 (the canonical table of expected results)
TESTING = (ROOT / "docs" / "testing.md").read_text()
SUITE_ROWS = {  # label on screen -> regex on the docs/testing.md section 1 table
    "Python": r"^\| backend API \+ ML pipeline \|.*\| (\d+) passed \|$",
    "dashboard": r"^\| dashboard components \|.*\| (\d+) passed \|$",
    "SketchFuture": r"^\| SketchFuture model \+ CrowdPulse hand-over \|.*\| (\d+) passed \|$",
    "iOS": r"^\| iOS logic \+ detector \|.*\| (\d+) tests, 0 failures \|$",
}
DOC_COUNTS = {label: int(re.search(rx, TESTING, re.M).group(1)) for label, rx in SUITE_ROWS.items()}
assert dict(SUITES)["iOS"] == DOC_COUNTS["iOS"], "iOS is not re-run: its count must be docs/testing.md's"
TESTING_STALE = [(label, n, DOC_COUNTS[label]) for label, n in SUITES if DOC_COUNTS[label] != n]
if TESTING_STALE:
    print("WARNING: docs/testing.md section 1 still lists " +
          ", ".join(f"{label} {doc} (shot list: {n})" for label, n, doc in TESTING_STALE) +
          "; update it before the cut (the B-roll footer cites it)", file=sys.stderr)

# the storyboard row must carry the same narration and lines (script.md section 3)
_ROW = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {NAME} |"))
assert f"| {SHOT['narration']} |" in _ROW, "narration differs between shotlist.json and script.md"
for _s in (CHAPTER, USER_LINE, CHIP, LAW_FOOTER, COST_TEXT, COUNTERS_LINE, " → ".join(ROAD)):
    assert f'"{_s}"' in _ROW, f"script.md row S17 lacks {_s!r}"

# the beats above are keyed to these clauses; if the narration changes, re-key them
CLAUSES = ["Phones on temporary mounts can serve one festival,", "then move to the next.",
           "The intended user is Macau's police,", "who run crowd control.",
           "The whole chain runs end to end in simulation,", f"with {TOTAL} automated tests passing."]
assert SHOT["narration"] == " ".join(CLAUSES), SHOT["narration"]

# guards: the screen text must agree with the narration, the visual column and the B-roll
_expect = " · ".join(f"{label} {n}" for label, n in SUITES) + f" = {TOTAL} {TOTAL_LABEL}"
assert COUNTERS_LINE == _expect, (COUNTERS_LINE, _expect)
assert f"with {TOTAL} automated tests passing" in SHOT["narration"], SHOT["narration"]
assert " · ".join(str(n) for _, n in SUITES) in SHOT["visual"] and f"lands on {TOTAL}" in SHOT["visual"], SHOT["visual"]
assert f"'{SUITES[0][1]} passed'" in SHOT["visual"], SHOT["visual"]
# filmed without -q (pyproject.toml already adds one; a second hides the "N passed" line)
_m = re.search(r"(B-roll filmed by the team) \([^)]*\), (a member runs \S+ -m pytest and the screen shows '(\d+) passed')", SHOT["visual"])
assert _m and int(_m.group(3)) == SUITES[0][1], SHOT["visual"]
SLATE_TEXT = f"{_m.group(1)}: {_m.group(2)}"

# the cost panel: drawn only when the team has filled it (no brackets) and labelled it TEAM ESTIMATE
COST_BRACKETED = COST_TEXT.startswith("[") and COST_TEXT.endswith("]")
SHOW_COST = not COST_BRACKETED
if SHOW_COST:
    assert COST_TEXT.startswith("TEAM ESTIMATE"), "a filled cost panel must be labelled TEAM ESTIMATE"
assert not (COST_BRACKETED and SHOW_COST), "the cost panel must stay out while its text is bracketed"
COST_DRAWS = 0             # counted by draw_cost_panel(); checked after rendering

BADGE_SEGMENTS = [  # (start, end, kind, detail, sub-line); no badge on the card or the roadmap
    (0.0, BEATS["user"], "ILLUSTRATION", "", "design intent, not field-tested"),
    (BEATS["broll"], BEATS["roadmap"], "LIVE SOFTWARE", "", "real test runs"),
]
# section 6: a filled cost panel is "labelled TEAM ESTIMATE with that sheet in the footer", so the
# sheet joins the law footer for as long as the panel can be on screen (the width assert below holds)
COST_SHEET = "docs/cost-estimate.md"
USER_FOOTER = LAW_FOOTER + (f" · cost: {COST_SHEET}" if SHOW_COST else "")
assert (ROOT / COST_SHEET).is_file(), COST_SHEET
FOOTER_SEGMENTS = [
    (0.0, BEATS["user"], "Operational model: docs/deployment.md"),
    (BEATS["user"], BEATS["broll"], USER_FOOTER),
    (BEATS["broll"], BEATS["roadmap"], "Simulation run: experiments/results/simulation_run/ · test counts: docs/testing.md"),
    (BEATS["roadmap"], DURATION, "experiments/datasets/melbourne/ · docs/experiment-protocol.md · "
                                 "docs/research/brief-evidence.md, section 6"),
]

# section 6, "Never say or show": none of these may appear in anything this shot draws
BANNED = ["in partnership with", "the police support it", "built for the police", "replaces", "better than",
          "prevents crushes", "saves lives", "legal", "compliant", "approved", "dangerous"]
SCREEN_TEXT = [CHAPTER, USER_LINE, CHIP, COUNTERS_LINE, " → ".join(ROAD), SLATE_TEXT] + \
              [f[2] for f in FOOTER_SEGMENTS] + [b[4] for b in BADGE_SEGMENTS] + ([COST_TEXT] if SHOW_COST else [])
for _s in SCREEN_TEXT:
    assert not any(b in _s.lower() for b in BANNED), _s

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


def scaled(im: Image.Image, s: float) -> Image.Image:
    if abs(s - 1) < 1e-3:
        return im
    return im.resize((max(1, int(round(im.width * s))), max(1, int(round(im.height * s)))), Image.LANCZOS)


def put_scaled(img: Image.Image, sprite, s: float, alpha: float = 1.0) -> None:
    """Puts a sprite scaled by s about its centre."""
    im, (x, y) = sprite
    sm = scaled(im, s)
    put(img, (sm, (x + (im.width - sm.width) / 2, y + (im.height - sm.height) / 2)), alpha)


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


def advance(text: str, size: int, weight: int) -> float:
    return text_font(text, size, weight).getlength(text)


def script_runs(text: str) -> list[tuple[str, bool]]:
    """Splits text into (run, is_cjk) so Latin is set in Geist and only the Chinese in Noto Sans TC
    (style.text_font picks one font for a whole string)."""
    runs: list[tuple[str, bool]] = []
    for ch in text:
        c = has_cjk(ch)
        if runs and runs[-1][1] == c:
            runs[-1] = (runs[-1][0] + ch, c)
        else:
            runs.append((ch, c))
    return runs


def mixed_sprite(xy, text: str, size: int, weight: int = 400, fill=INK, anchor: str = "la"):
    """A one-line label mixing Latin and Chinese, each in its own font, on one baseline.
    anchor: 'la' (left-top), 'ma' (centre-top) or 'ra' (right-top); top = the Geist ascender line."""
    runs = script_runs(text)
    widths = [font(size, weight, cjk=c).getlength(r) for r, c in runs]
    x, y = xy
    x -= {"la": 0, "ma": sum(widths) / 2, "ra": sum(widths)}[anchor]
    base = y + font(size, weight).getmetrics()[0]

    def fn(im):
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        xx = x
        for (r, c), w_ in zip(runs, widths):
            d.text((xx, base), r, font=font(size, weight, cjk=c), fill=(*fill, 255), anchor="ls")
            xx += w_
        im.alpha_composite(lay)
    return layer_sprite(fn)


def rich_lines(runs, size: int, max_w: float):
    """Lays out styled runs [(text, weight, colour)] word by word, wrapping at max_w.
    Returns lines of [(text, weight, colour, x offset)]; spaces stay with the word after them."""
    tokens = [(tok, wgt, col) for text, wgt, col in runs for tok in re.findall(r"\s*\S+|\s+", text)]
    lines, line, x = [], [], 0.0
    for tok, wgt, col in tokens:
        if not tok.strip():                    # bare space(s): advance unless at a line start
            if line:
                x += advance(tok, size, wgt)
            continue
        if line and x + advance(tok.rstrip(), size, wgt) > max_w:
            lines.append(line)
            line, x, tok = [], 0.0, tok.lstrip()
        if not line:
            tok = tok.lstrip()
        line.append((tok, wgt, col, x))
        x += advance(tok, size, wgt)
    if line:
        lines.append(line)
    return lines


def balanced_lines(text: str, size: int, weight: int, max_w: int) -> list[str]:
    """One line if it fits, else the two-line split with the shorter longest line."""
    if text_size(text, size, weight)[0] <= max_w:
        return [text]
    words = text.split()
    best = min(range(1, len(words)), key=lambda i: max(text_size(" ".join(words[:i]), size, weight)[0],
                                                      text_size(" ".join(words[i:]), size, weight)[0]))
    return [" ".join(words[:best]), " ".join(words[best:])]


# ---------- part 1 (0-4.95 s): calendar and pole ----------

KIT_W, KIT_H = 130, 220          # phone-on-clamp kit; feet at y 214, phone centre (65, 70)
KIT_PHONE_TOP = 22


def kit_sprite() -> Image.Image:
    def fn(d, q):
        cx, cy = 65 * q, 70 * q
        clamp_c, jaw = (*INK_2, 255), (*GREY, 255)
        # back bar of the clamp, behind the phone
        d.rounded_rectangle((cx - 40 * q, cy - 8 * q, cx + 40 * q, cy + 8 * q), 5 * q, fill=clamp_c)
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
        d.ellipse((cx - 9 * q, top + 2 * q, cx + 9 * q, top + 20 * q), fill=clamp_c)
        d.rounded_rectangle((cx - 4 * q, top + 14 * q, cx + 4 * q, top + 62 * q), 3 * q, fill=clamp_c)
        foot = 214 * q
        for dx in (-38, 0, 38):
            d.line([(cx, top + 58 * q), (cx + dx * q, foot)], fill=clamp_c, width=5 * q)
        d.ellipse((cx - 7 * q, top + 54 * q, cx + 7 * q, top + 68 * q), fill=clamp_c)
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


def shadow_sprite() -> Image.Image:
    im = Image.new("RGBA", (140, 40), (0, 0, 0, 0))
    ImageDraw.Draw(im).ellipse((20, 12, 120, 28), fill=(0, 0, 0, 150))
    return im.filter(ImageFilter.GaussianBlur(4))


KIT, ARCS, POLE, SHADOW = kit_sprite(), arcs_sprite(), pole_sprite(), shadow_sprite()

PAGE_W, PAGE_Y0, PAGE_Y1, PAGE_GAP, PAGE_X0 = 300, 268, 698, 70, 150
BAND_H = 124                                 # page header band holding the event name (en / zh)
GROUND_Y = PAGE_Y1 - 14                      # the line each kit stands on
FLOOR_Y = PAGE_Y1 + 32                       # street level under the pole
PAGE_XS = [PAGE_X0 + i * (PAGE_W + PAGE_GAP) for i in range(3)]
KIT_LAND_Y = GROUND_Y - 2 - 214               # sprite top when the kit's feet stand on the page's ground line
KIT_POS = [(x + PAGE_W / 2 - KIT_W / 2, KIT_LAND_Y) for x in PAGE_XS]
POLE_AT = (1610, FLOOR_Y)                      # base centre
POLE_ORIGIN = (POLE_AT[0] - POLE_BASE[0], POLE_AT[1] - POLE_BASE[1])
SEP_X = 1262


def page_sprite(i: int):
    x0 = PAGE_XS[i]
    en, zh = EVENTS[i]

    def fn(img):   # the event name sits in the header band, so the kit's hops stay clear of it
        rounded(img, (x0, PAGE_Y0, x0 + PAGE_W, PAGE_Y1), 18, fill=NAVY_2)
        rounded(img, (x0, PAGE_Y0, x0 + PAGE_W, PAGE_Y0 + BAND_H), 18, fill=NAVY_3)
        rounded(img, (x0, PAGE_Y0 + BAND_H - 24, x0 + PAGE_W, PAGE_Y0 + BAND_H), 0, fill=NAVY_3)
        draw_text(img, (x0 + PAGE_W / 2, PAGE_Y0 + 32), en, 30, 700, INK, anchor="ma")
        draw_text(img, (x0 + PAGE_W / 2, PAGE_Y0 + 74), zh, 28, 500, INK_2, anchor="ma")
        ground = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ground).line([(x0 + 40, GROUND_Y), (x0 + PAGE_W - 40, GROUND_Y)], fill=(*INK_3, 140), width=2)
        img.alpha_composite(ground)
    base = layer_sprite(fn)
    rings = hires((PAGE_W, 40), lambda d, q: [d.rounded_rectangle(((rx - 7) * q, 2 * q, (rx + 7) * q, 38 * q), 7 * q, fill=(*INK_2, 255)) for rx in (80, 220)])
    return base, (rings, (x0, PAGE_Y0 - 16))


PAGES = [page_sprite(i) for i in range(3)]
GLOW = [(hires((PAGE_W + 16, PAGE_Y1 - PAGE_Y0 + 16), lambda d, q: d.rounded_rectangle((2 * q, 2 * q, (PAGE_W + 14) * q, (PAGE_Y1 - PAGE_Y0 + 14) * q), 22 * q, outline=(*CYAN, 255), width=4 * q)), (x - 8, PAGE_Y0 - 8)) for x in PAGE_XS]


# No mark is drawn on a page once the kit leaves it: a tick on a named real event would read as
# 'deployed there, done', and nothing has been deployed (design intent, not field-tested).

HEAD_L = [text_sprite((PAGE_X0, 156), "Phone on a temporary mount", 30, 700, INK),
          text_sprite((PAGE_X0, 198), "臨時支架上的手機", 26, 500, INK_2)]
HEAD_R_X = 1540
HEAD_R = [text_sprite((HEAD_R_X, 156), "Fixed counting camera", 30, 700, INK, anchor="ma"),
          text_sprite((HEAD_R_X, 198), "固定計數鏡頭", 26, 500, INK_2, anchor="ma")]
# the three pages are deployment.md's peak periods: said once, above the calendar's right edge
PEAK_LABEL = mixed_sprite((PAGE_XS[2] + PAGE_W, 200), "peak periods · 高峰期", 26, 600, INK_2, anchor="ra")
BOLTED = mixed_sprite((HEAD_R_X, FLOOR_Y + 24), "bolted in place · 固定安裝", 26, 600, INK_2, anchor="ma")
# the kit, at rest or at the top of a hop or drop, stays below the page header band (event names)
assert KIT_LAND_Y + KIT_PHONE_TOP - max(HOP_LIFT, DROP_LIFT) > PAGE_Y0 + BAND_H + 4


def scene_static():
    def fn(img):
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        lx, ly = POLE_ORIGIN[0] + 62, POLE_ORIGIN[1] + 112
        d.polygon([(lx, ly), (1318, FLOOR_Y), (1520, FLOOR_Y)], fill=(*CYAN, 26))                     # field of view
        d.line([(1300, FLOOR_Y), (1800, FLOOR_Y)], fill=(*INK_3, 160), width=2)                       # ground
        d.line([(SEP_X, 160), (SEP_X, FLOOR_Y)], fill=(*NAVY_3, 255), width=2)                        # divider
        img.alpha_composite(lay)
    return layer_sprite(fn)


SCENE = scene_static()


def kit_state(t: float):
    """Kit sprite top-left, its height above the ground, the page it stands on (or None), drop progress."""
    land = BEATS["kit_down"] + 0.6
    if t < land:
        k = progress(t, BEATS["kit_down"], 0.6)
        lift = (1 - k) * DROP_LIFT
        x, y = KIT_POS[0]
        return (x, y - lift), lift, None, k
    for ts, frm, to in ((BEATS["then_move"], 0, 1), (BEATS["to_the_next"], 1, 2)):
        if t < ts:
            return KIT_POS[frm], 0.0, frm, 1.0
        if t < ts + HOP:
            k = ease((t - ts) / HOP)
            x = lerp(KIT_POS[frm][0], KIT_POS[to][0], k)
            lift = HOP_LIFT * math.sin(math.pi * k)
            return (x, KIT_LAND_Y - lift), lift, None, 1.0
    return KIT_POS[2], 0.0, 2, 1.0


def page_active(i: int, t: float) -> float:
    if i == 0:
        return fade(t, BEATS["serve_one"], BEATS["then_move"] + 0.1, 0.3)
    if i == 1:
        return fade(t, BEATS["then_move"] + HOP - 0.05, BEATS["to_the_next"] + 0.1, 0.08)
    return fade(t, BEATS["to_the_next"] + HOP - 0.05, BEATS["user"] + 0.4, 0.18)


def part_calendar(img: Image.Image, t: float) -> None:
    out = 1 - progress(t, BEATS["user"] - 0.15, 0.3)          # leaves as "The intended user" starts, under the card
    if out <= 0:
        return
    put(img, SCENE, out * progress(t, 0.0, 0.5))
    for j, sp in enumerate(HEAD_L + HEAD_R):
        put(img, sp, out * progress(t, 0.05 * j, 0.4), dy=10 * (1 - progress(t, 0.05 * j, 0.4)))
    kp = progress(t, 0.4, 0.4)
    put(img, PEAK_LABEL, out * kp, dy=10 * (1 - kp))
    for i, (base, rings) in enumerate(PAGES):
        k = progress(t, 0.08 + 0.12 * i, 0.5)
        dy = 24 * (1 - k)
        put(img, base, out * k, dy=dy)
        put(img, rings, out * k, dy=dy)
        put(img, GLOW[i], out * k * page_active(i, t), dy=dy)
    put(img, BOLTED, out * progress(t, BEATS["then_move"], 0.4), dy=8 * (1 - progress(t, BEATS["then_move"], 0.4)))
    put(img, (POLE, POLE_ORIGIN), out * progress(t, 0.15, 0.5))       # bolted in place: it never moves

    (kx, ky), lift, on_page, k_drop = kit_state(t)
    shadow_a = out * k_drop * (1 - lift / 180)
    if shadow_a > 0:
        sw = 1 - 0.4 * lift / 100
        sh = scaled(SHADOW, sw) if sw < 0.999 else SHADOW
        put(img, (sh, (kx + KIT_W / 2 - sh.width / 2, KIT_LAND_Y + 214 - sh.height / 2 + 2)), shadow_a)
    put(img, (KIT, (kx, ky)), out * k_drop)
    if on_page is not None:
        act = page_active(on_page, t)
        if act > 0:
            pulse = 0.55 + 0.45 * math.sin(2 * math.pi * 1.4 * (t - BEATS["serve_one"]))
            put(img, (ARCS, (kx + KIT_W / 2 - 50, ky + KIT_PHONE_TOP - 50)), act * out * pulse)


# ---------- part 2 (4.95-9.12 s): the operator card, the chip and (only if filled) the cost panel ----------

ICON_W, ICON_H = 230, 170


def operator_icon(d, q):
    """An operations-room screen showing counts (bars), and a struck-through picture: counts, never
    images. Generic shapes only: no emblem, badge or logo."""
    Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
    d.rounded_rectangle(Q(6, 8, 176, 122), 12 * q, fill=(*NAVY_3, 255))                 # monitor
    d.rounded_rectangle(Q(18, 20, 164, 110), 6 * q, fill=(*NAVY, 255))
    for i, w_ in enumerate((104, 70, 88)):                                             # counts as bars
        d.rounded_rectangle(Q(32, 34 + i * 24, 32 + w_, 46 + i * 24), 5 * q, fill=(*CYAN, 255))
    d.rounded_rectangle(Q(82, 122, 100, 142), 3 * q, fill=(*NAVY_3, 255))               # stand
    d.rounded_rectangle(Q(54, 142, 128, 152), 4 * q, fill=(*NAVY_3, 255))
    # the picture, struck through, over the monitor's corner (navy ring keeps it apart)
    d.rounded_rectangle(Q(140, 92, 226, 166), 12 * q, fill=(*NAVY_2, 255))
    d.rounded_rectangle(Q(148, 100, 218, 158), 7 * q, fill=(*NAVY, 255), outline=(*INK_2, 255), width=3 * q)
    d.polygon([Q(156, 150), Q(176, 124), Q(190, 140), Q(198, 130), Q(212, 150)], fill=(*INK_3, 255))
    d.ellipse(Q(196, 108, 208, 120), fill=(*INK_3, 255))
    d.line([Q(146, 162), Q(222, 96)], fill=(*NAVY_2, 255), width=13 * q)
    d.line([Q(146, 162), Q(222, 96)], fill=(*CRITICAL, 255), width=6 * q)


def build_user_scene(cost_text: str | None) -> dict:
    """Sprites of the intended-user scene. With cost_text None the card sits centred and alone (the
    cost panel is never drawn empty); with a filled TEAM ESTIMATE text the card moves left and the
    cost panel slides in beside it."""
    card = (120, 342, 1800, 562) if cost_text is None else (100, 300, 1000, 620)
    x0, y0, x1, y1 = card
    ix, iy = x0 + 36, (y0 + y1) / 2 - ICON_H / 2
    tx = ix + ICON_W + 34
    size = 46 if cost_text is None else 40
    runs = [(USER_NAME, 700, INK), (" · ", 500, INK_3), (USER_ROLE, 600, CYAN)]
    lines = rich_lines(runs, size, x1 - 36 - tx)
    lh = int(size * 1.3)
    block_h = 34 + 26 + len(lines) * lh
    ty = (y0 + y1) / 2 - block_h / 2
    sc = {"card": card,
          "bg": layer_sprite(lambda im: rounded(im, card, 26, fill=NAVY_2)),
          "icon": (hires((ICON_W, ICON_H), operator_icon), (ix, iy)),
          "head": text_sprite((tx, ty), USER_HEAD, 34, 600, INK_2),
          "main": layer_sprite(lambda im: [draw_text(im, (tx + xo, ty + 60 + i * lh), tok, size, wgt, col)
                                           for i, ln in enumerate(lines) for tok, wgt, col, xo in ln])}
    assert sc["main"][0].width + sc["main"][1][0] <= x1 - 30, "intended-user line runs off the card"
    if cost_text is None:
        assert len(lines) == 1, "the intended-user line must stay on one line on the lone card"

    # the chip: its own pill under the card, readable on its own; ring icon + text centred in the pill
    l_, _, r_, _ = text_font(CHIP, 44, 700).getbbox(CHIP)
    ring_r, ring_gap, pad = 10, 16, 34
    group_w = 2 * ring_r + ring_gap + (r_ - l_)
    cx = (x0 + x1) / 2
    gx = cx - group_w / 2
    cy0 = y1 + 52
    pill = (gx - pad, cy0, gx + group_w + pad, cy0 + 82)

    def chip_fn(d, q):
        ox, oy = pill[0] - 4, pill[1] - 4
        b = ((pill[0] - ox) * q, (pill[1] - oy) * q, (pill[2] - ox) * q, (pill[3] - oy) * q)
        d.rounded_rectangle(b, 41 * q, fill=(*NAVY_2, 255), outline=(*WARNING, 255), width=4 * q)
        r_cx, r_cy = (gx + ring_r - ox) * q, (pill[1] + 41 - oy) * q
        d.ellipse((r_cx - ring_r * q, r_cy - ring_r * q, r_cx + ring_r * q, r_cy + ring_r * q), outline=(*WARNING, 255), width=4 * q)
    chip_bg = (hires((pill[2] - pill[0] + 8, pill[3] - pill[1] + 8), chip_fn), (pill[0] - 4, pill[1] - 4))
    chip_txt = text_sprite((gx + 2 * ring_r + ring_gap - l_, pill[1] + 41), CHIP, 44, 700, INK, anchor="lm")
    sc["chip"] = layer_sprite(lambda im: (put(im, chip_bg), put(im, chip_txt)))
    sc["cost"] = None
    if cost_text is not None:
        box = (1040, card[1], 1820, card[3])
        head, _, body = cost_text.partition(": ")
        assert head.startswith("TEAM ESTIMATE"), head

        def cost_fn(im):
            rounded(im, box, 26, fill=NAVY_2, outline=WARNING, width=3)
            draw_text(im, (box[0] + 36, box[1] + 30), head, 34, 700, WARNING)
            draw_text(im, (box[0] + 36, box[1] + 84), body, 28, 500, INK, max_width=box[2] - box[0] - 72, line_gap=1.3)
        sc["cost"] = layer_sprite(cost_fn)
        assert sc["cost"][0].height + sc["cost"][1][1] <= box[3] + 4, "cost text overflows its panel"
    return sc


USER_SCENE = build_user_scene(COST_TEXT if SHOW_COST else None)
assert (USER_SCENE["cost"] is None) == COST_BRACKETED, "the cost panel must exist only when filled"
_chip_bottom = USER_SCENE["chip"][1][1] + USER_SCENE["chip"][0].height
assert _chip_bottom < 900, "the chip must stay clear of the caption band"


def draw_cost_panel(img: Image.Image, sc: dict, t: float) -> None:
    """Only ever called with a filled, unbracketed TEAM ESTIMATE (never an empty cost panel)."""
    global COST_DRAWS
    assert sc["cost"] is not None
    COST_DRAWS += 1
    k = progress(t, BEATS["user"] + 1.0, 0.5)
    put(img, sc["cost"], k, dx=90 * (1 - k))


def part_user(img: Image.Image, t: float, sc: dict = USER_SCENE) -> None:
    # the card's opaque panel rises over the leaving calendar (overlap, no empty frames) and hides
    # it where they meet, so the card's text can follow at once without a text-on-text crossfade
    out_ease = lambda x: 1 - (1 - clamp(x)) ** 3              # noqa: E731  (ease-out: visible from the first frames)
    k = out_ease((t - (BEATS["user"] - 0.12)) / 0.3)
    put(img, sc["bg"], k, dy=18 * (1 - k))
    t0 = BEATS["user"] - 0.02
    put(img, sc["icon"], out_ease((t - t0) / 0.35), dy=18 * (1 - k))
    for j, key in enumerate(("head", "main")):
        a = out_ease((t - (t0 + 0.07 * j)) / 0.35)
        put(img, sc[key], a, dy=12 * (1 - a) + 18 * (1 - k))
    kc = progress(t, BEATS["police"], 0.3)                      # the chip pops in on "Macau's police"
    if kc > 0:
        put_scaled(img, sc["chip"], 0.86 + 0.14 * kc + 0.05 * math.sin(math.pi * kc), kc)
    if sc["cost"] is not None:
        draw_cost_panel(img, sc, t)


# ---------- part 3 (9.12-13.88 s): B-roll slate and the counters over it ----------

SLATE = (120, 150, 1800, 880)


def slate_static():
    x0, y0, x1, y1 = SLATE
    frame_ = dashed_panel(SLATE, 22, WARNING, fill=NAVY_2, width=3)
    glyph = (hires((70, 50), lambda d, q: camera_glyph(d, 4 * q, 3 * q, 1.1 * q, (*WARNING, 255))), (x0 + 60, y0 + 46))
    title = text_sprite((x0 + 150, y0 + 50), "[TEAM FOOTAGE]", 40, 700, WARNING)
    head_, _, rest_ = SLATE_TEXT.partition(": ")                      # the command and '54 passed' stay whole
    body_lines = [head_ + ":", rest_]
    assert all(text_size(ln, 34, 500)[0] <= x1 - x0 - 120 for ln in body_lines), body_lines
    body = layer_sprite(lambda im: [draw_text(im, (x0 + 60, y0 + 124 + i * 42), ln, 34, 500, INK)
                                    for i, ln in enumerate(body_lines)])
    # these are the guide-voice times this render is keyed to (BEATS); the shot list's "about 9.9-14.9 s" and
    # "from about 11.5 s" are 140 wpm estimates for the real take, so the slate says which clock it uses
    when = (f"{NAME}, guide voice: {BEATS['broll']:.1f}-{BEATS['roadmap']:.1f} s into the shot, hard cuts (film at least 5 s) · "
            f"the counters run over the take from {BEATS['counters']:.1f} s")
    assert text_size(when, 24, 500)[0] <= x1 - x0 - 120, when
    sub = text_sprite((x0 + 60, y0 + 222), when, 24, 500, INK_2)

    def laptop(d, q):
        Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
        d.rounded_rectangle(Q(30, 0, 450, 250), 14 * q, fill=(*NAVY_3, 255))
        d.rounded_rectangle(Q(46, 16, 434, 234), 8 * q, fill=(*NAVY, 255))
        for i, w_ in enumerate((300, 220, 260, 180)):
            d.rounded_rectangle(Q(70, 40 + i * 34, 70 + w_, 54 + i * 34), 4 * q, fill=(*INK_3, 255))
        d.rounded_rectangle(Q(70, 190, 230, 206), 4 * q, fill=(*SAFE, 255))
        d.rounded_rectangle(Q(0, 252, 480, 272), 8 * q, fill=(*INK_3, 255))
    lap = (scaled(hires((480, 274), laptop), 0.8), ((x0 + x1) / 2 - 192, y0 + 276))
    return [frame_, glyph, title, body, sub, lap]


SLATE_SPRITES = slate_static()

TW, SEP_W, EQ_W, TOT_W = 224, 56, 72, 450            # suite tile, "·" gap, "=" gap, total tile
TILE_Y0, TILE_Y1 = 684, 852
_row_w = 4 * TW + 3 * SEP_W + EQ_W + TOT_W
_x = (W - _row_w) / 2
TILES, GAPS = [], []
for _i in range(4):
    TILES.append((_x, _x + TW))
    _x += TW
    GAPS.append((_x + (SEP_W if _i < 3 else EQ_W) / 2, "·" if _i < 3 else "="))
    _x += SEP_W if _i < 3 else EQ_W
TOTAL_TILE = (_x, _x + TOT_W)
BACKING = (TILES[0][0] - 20, TILE_Y0 - 18, TOTAL_TILE[1] + 20, TILE_Y1 + 18)
assert BACKING[3] < 900 and BACKING[0] >= 60 and BACKING[2] <= 1860, BACKING
LABEL_Y, NUM_Y = TILE_Y0 + 34, TILE_Y0 + 108
TOT_NUM_CX = TOTAL_TILE[0] + 26 + 100                # the total ("124") centred in a 200 px box at the tile's left
TOT_TXT_X = TOTAL_TILE[0] + 26 + 200 + 22


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


DIGITS, DIGIT_ADV = digit_sprites(84, INK)
DIGITS_T, DIGIT_ADV_T = digit_sprites(104, CYAN)


def number(img: Image.Image, value: int, cx: float, cy: float, big: bool = False, alpha: float = 1.0) -> None:
    digs, adv = (DIGITS_T, DIGIT_ADV_T) if big else (DIGITS, DIGIT_ADV)
    s = str(value)
    x = cx - sum(adv[int(ch)] for ch in s) / 2
    for ch in s:
        im = digs[int(ch)]
        put(img, (im, (x - 4, cy - im.height / 2)), alpha)
        x += adv[int(ch)]


def counters_static():
    backing = layer_sprite(lambda im: rounded(im, BACKING, 26, fill=NAVY, alpha=0.9))
    tiles = []
    for (x0, x1), (label, _) in zip(TILES, SUITES):
        assert text_size(label, 30, 600)[0] <= TW - 20, label
        tiles.append(layer_sprite(lambda im, x0=x0, x1=x1, label=label: (
            rounded(im, (x0, TILE_Y0, x1, TILE_Y1), 20, fill=NAVY_2),
            draw_text(im, ((x0 + x1) / 2, LABEL_Y), label, 30, 600, INK_2, anchor="mm"))))
    x0, x1 = TOTAL_TILE
    w1, w2 = TOTAL_LABEL.split(" ", 1)                 # "automated" / "tests", stacked after the number
    total = layer_sprite(lambda im: (
        rounded(im, (x0, TILE_Y0, x1, TILE_Y1), 20, fill=NAVY_2, outline=CYAN, width=3),
        draw_text(im, (TOT_TXT_X, NUM_Y - 26), w1, 34, 600, INK, anchor="lm"),
        draw_text(im, (TOT_TXT_X, NUM_Y + 18), w2, 34, 600, INK, anchor="lm")))
    assert TOT_TXT_X + text_size(w1, 34, 600)[0] <= x1 - 16, "total label overflows"
    ops = [text_sprite((cx, NUM_Y - 4), op, 76 if op == "·" else 60, 700 if op == "·" else 600, INK_2, anchor="mm") for cx, op in GAPS]
    return backing, tiles, total, ops


C_BACKING, TILE_SPRITES, TOTAL_SPRITE, OP_SPRITES = counters_static()


def pulse_ring(k: float):
    x0, x1 = TOTAL_TILE
    g = 4 + 14 * k
    box = (x0 - g, TILE_Y0 - g, x1 + g, TILE_Y1 + g)
    im = hires((int(box[2] - box[0]) + 8, int(box[3] - box[1]) + 8),
               lambda d, q: d.rounded_rectangle((4 * q, 4 * q, (box[2] - box[0] + 4) * q, (box[3] - box[1] + 4) * q), int((20 + g) * q), outline=(*CYAN, 255), width=3 * q))
    return im, (box[0] - 4, box[1] - 4)


def tick_window(i: int) -> tuple[float, float]:
    """Suite i counts up from start to end (ends 0.2 s apart); the last one lands with the total
    on "a hundred", so the finished row holds about 1.8 s before the roadmap cut."""
    t0 = BEATS["counters"]
    return t0 + 0.25 + 0.1 * i, BEATS["total"] - 0.2 * (3 - i)


def part_slate(img: Image.Image, t: float) -> None:
    k = progress(t, BEATS["broll"] + 0.05, 0.3)
    put(img, SLATE_SPRITES[0])
    for sp in SLATE_SPRITES[1:]:
        put(img, sp, k)


def part_counters(img: Image.Image, t: float) -> None:
    t0 = BEATS["counters"]
    if t < t0:
        return
    kb = progress(t, t0, 0.35)
    put(img, C_BACKING, kb, dy=16 * (1 - kb))
    shown = []
    for i, ((x0, x1), (_, n)) in enumerate(zip(TILES, SUITES)):
        a = progress(t, t0 + 0.06 * i, 0.35)
        put(img, TILE_SPRITES[i], a, dy=16 * (1 - a))
        start, end = tick_window(i)
        kt = clamp((t - start) / (end - start))
        v = n if kt >= 1 else int(n * (1 - (1 - kt) ** 2.2))   # ease-out, floored: each lands exactly at its end
        shown.append(v)
        number(img, v, (x0 + x1) / 2, NUM_Y + 16 * (1 - a), alpha=a)
    for i, sp in enumerate(OP_SPRITES):
        put(img, sp, progress(t, t0 + 0.1 + 0.06 * i, 0.35))
    a_tot = progress(t, t0 + 0.24, 0.35)
    put(img, TOTAL_SPRITE, a_tot, dy=16 * (1 - a_tot))
    number(img, sum(shown), TOT_NUM_CX, NUM_Y + 16 * (1 - a_tot), big=True, alpha=a_tot)
    if BEATS["total"] <= t <= BEATS["total"] + 0.6:
        kp = (t - BEATS["total"]) / 0.6
        put(img, pulse_ring(ease(kp)), (1 - kp) * 0.9)


# ---------- part 4 (13.88-18.5 s): the roadmap arrow, alone ----------

ROAD_Y, ROAD_X0, ROAD_X1 = 520, 150, 1772
ST_X = [300 + i * (1620 - 300) / 3 for i in range(4)]
ROAD_LABEL = mixed_sprite((ROAD_X0, ROAD_Y - 116), "Roadmap · 路線圖", 32, 700, INK_2)
ST_SIZE, ST_LH, ST_MAXW = 36, 46, 400


def station_sprites(i: int):
    cx = ST_X[i]
    name, aside = STATIONS[i]
    done = i == 0

    def dot(d, q):
        if done:
            d.ellipse((2 * q, 2 * q, 50 * q, 50 * q), fill=(*CYAN, 255))
            check_mark(d, 26 * q, 26 * q, 28 * q, (*NAVY, 255), 5 * q)
        else:
            d.ellipse((2 * q, 2 * q, 50 * q, 50 * q), fill=(*NAVY, 255), outline=(*INK_2, 255), width=5 * q)
    out = [(hires((52, 52), dot), (cx - 26, ROAD_Y - 26))]
    lines = balanced_lines(name, ST_SIZE, 700, ST_MAXW)
    for j, ln in enumerate(lines):
        out.append(text_sprite((cx, ROAD_Y + 48 + j * ST_LH), ln, ST_SIZE, 700, CYAN if done else INK, anchor="ma"))
    if aside:
        out.append(text_sprite((cx, ROAD_Y + 48 + len(lines) * ST_LH + 4), aside, 30, 600, CYAN, anchor="ma"))
    return out


STATION_SPRITES = [station_sprites(i) for i in range(4)]
_lefts = [min(sp[1][0] for sp in s[1:]) for s in STATION_SPRITES]
_rights = [max(sp[1][0] + sp[0].width for sp in s[1:]) for s in STATION_SPRITES]
assert all(_rights[i] + 24 < _lefts[i + 1] for i in range(3)) and _lefts[0] >= 60 and _rights[3] <= 1860, (_lefts, _rights)
ARROW_HEAD = hires((40, 46), lambda d, q: d.polygon([(0, 2 * q), (38 * q, 23 * q), (0, 44 * q)], fill=(*INK_2, 255)))
CHEVRON = hires((26, 34), lambda d, q: d.line([(4 * q, 4 * q), (20 * q, 17 * q), (4 * q, 30 * q)], fill=(*INK_2, 255), width=5 * q, joint="curve"))
CHEVRON_BG = hires((44, 48), lambda d, q: d.ellipse((2 * q, 2 * q, 42 * q, 46 * q), fill=(*NAVY, 255)))
CHEV_X = [(ST_X[i] + ST_X[i + 1]) / 2 for i in range(3)]       # the "→" between stations


def part_roadmap(img: Image.Image, t: float) -> None:
    tr = BEATS["roadmap"]
    a = 1 - (1 - clamp((t - tr) / 0.3)) ** 3                    # ease-out: something is on screen right after the cut
    put(img, ROAD_LABEL, a, dy=8 * (1 - a))
    k_line = 1 - (1 - clamp((t - tr) / 1.3)) ** 3               # the arrow draws left to right, fast start
    if k_line <= 0:
        return
    xe = lerp(ROAD_X0, ROAD_X1, k_line)
    lay = Image.new("RGBA", (int(xe - ROAD_X0) + 2, 10), (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((0, 1, xe - ROAD_X0, 8), 4, fill=(*INK_3, 255))
    put(img, (lay, (ROAD_X0, ROAD_Y - 5)))
    put(img, (ARROW_HEAD, (xe - 10, ROAD_Y - 23)), min(1.0, k_line * 6))
    for cx in CHEV_X:
        put(img, (CHEVRON_BG, (cx - 22, ROAD_Y - 24)), ease(clamp((xe - cx) / 80)))
        put(img, (CHEVRON, (cx - 13, ROAD_Y - 17)), ease(clamp((xe - cx) / 80)))
    for i, cx in enumerate(ST_X):                               # each station arrives as the line passes it
        ks = ease(clamp((xe - (cx - 30)) / 120))
        for j, sp in enumerate(STATION_SPRITES[i]):
            put(img, sp, ks, dy=(10 * (1 - ks)) if j else 0)


# ---------- fixed slots (chapter card, badge, footer) ----------

CHAPTER_SPRITE = layer_sprite(lambda im: chapter_card(im, CHAPTER))
BADGES_S = [(a, b, layer_sprite(lambda im, k=k, dt=dt, sub=sub: badge(im, k, dt, sub))) for a, b, k, dt, sub in BADGE_SEGMENTS]
FOOTERS_S = [(a, b, layer_sprite(lambda im, txt=txt: footer(im, txt))) for a, b, txt in FOOTER_SEGMENTS]
for _a, _b, (_im, _pos) in FOOTERS_S:
    assert _im.height < 30 and _im.width <= 1150, "footer must stay one line, at most 1150 px"


def scrim_sprite(text_fn, pad_x: int = 12, pad_y: int = 6, alpha: float = 0.8):
    """Dark rounded backing behind the small grey footer, used on the transparent overlay only, so
    it stays legible over the team's camera footage (style.badge already backs its sub-line)."""
    _im, (x, y) = layer_sprite(text_fn)
    box = (x - pad_x, y - pad_y, x + _im.width + pad_x, y + _im.height + pad_y)
    return layer_sprite(lambda im: rounded(im, box, 8, fill=NAVY, alpha=alpha))


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
    footer with a dark pill so it reads over camera footage."""
    put(img, CHAPTER_SPRITE, fade(t, 0.0, CHAPTER_END, 0.3), dy=-8 * (1 - progress(t, 0, 0.3)))
    for a, b, sp in BADGES_S:
        put(img, sp, seg_alpha(t, a, b))
    for (a, b, sp), sc in zip(FOOTERS_S, FOOTER_SCRIMS):
        al = seg_alpha(t, a, b)
        if scrim:
            put(img, sc, al)
        put(img, sp, al)


# ---------- frame drawing ----------

BG = canvas(NAVY)


def foreground(t: float) -> Image.Image:
    """Transparent overlay for compositing over the team B-roll: the fixed slots for the whole shot
    and, inside the B-roll window, the counters on their own backing."""
    img = transparent()
    if BEATS["broll"] <= t < BEATS["roadmap"]:
        part_counters(img, t)
    slots(img, t, scrim=True)
    return img


def frame_mp4(t: float) -> Image.Image:
    img = BG.copy()
    if t < BEATS["broll"]:
        part_calendar(img, t)
        part_user(img, t)
    elif t < BEATS["roadmap"]:
        part_slate(img, t)
        part_counters(img, t)
    else:
        part_roadmap(img, t)
    slots(img, t)
    return img


STILLS = {"chapter": 1.2, "hop": 3.6, "page2": 3.9, "hop2": 4.15, "page3": 4.7, "handover": 4.97,
          "card": 5.9, "chip": 7.5, "slate": 10.2, "ticking": 11.5, "total": 12.3, "held": 13.8,
          "roadmap": 16.0, "end": 18.4}

if __name__ == "__main__":
    for k_, tt in STILLS.items():
        print(still(f"{NAME}_{k_}", frame_mp4(tt)))
    if "--stills-only" not in sys.argv:
        print(render(NAME, DURATION, frame_mp4))
        print(render_overlay(NAME, DURATION, foreground))
    assert COST_DRAWS == 0 or SHOW_COST, "the cost panel was drawn while its text is still bracketed"
    print(f"cost panel: {'drawn (TEAM ESTIMATE filled)' if SHOW_COST else 'skipped (text still bracketed)'}; draws {COST_DRAWS}")
