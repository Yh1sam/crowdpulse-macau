"""Shot S17b (4:04.0-4:16.0, 12.0 s): "If it fails, who answers?" [MEMBER 3] voice-over. Motion graphic.

A navy card in the S07 / S17 style: a title and three short rows (who may be more vulnerable, who answers,
how the public is told), each with a plain shape icon, and a short footer ("To be confirmed with the
authorities"). No badge, no chapter card (it continues S17's "Can it happen?"), no lower-third ([MEMBER 3]'s
is in S08), no emblem or logo. Declutter (19 Oct): each row at most 10 words, the footer at most 7; the laws
and "no partner yet" left the footer (S17's chip says it 10 s earlier; script.md section 4 keeps the laws).

Storyboard: docs/video/script.md section 3, row S17b; claims table section 4, rows S17b (and the
on-screen rows under it); section 6 "motion_graphic" (S17b), "On-screen text load" and "Never say or
show"; shot list docs/video/shotlist.json (id S17b).

Beats (shot seconds, keyed to the guide voice video/build/guide/S17b.wav, which starts 0.5 s into
the shot (script.md section 6, "Guide track": S17b 0.5 s); clause starts are the silencedetect
boundaries (noise -35 dB, d 0.08 s: 0, 1.30, 2.31, 3.92, 5.06, 6.71 s into the 9.45 s file of 19 Oct,
unchanged since 18 Oct) + 0.5 s; re-key to the real take):
0.0         the title, then row 1 ("May be more vulnerable", icon: a figure with a walking stick
            beside a wheelchair outline); the footer. The title is fully in by 0.32 s.
0.5-2.57    "If it fails, who answers?": the voice asks the title question (title and row 1 hold).
2.81        "The person who approved it," -> row 2 builds ("Who answers", icon: a log list); it is
            outlined while it is spoken.
4.42        "named in our log," -> the name line in the log icon lights up.
5.56        "and the department running it." (row 2 holds)
7.21        "Every notice says an AI forecast is involved." -> row 3 builds ("Telling the public",
            icon: a sign with a dashed edge, because it is planned) and takes the outline.
9.95-12.0   the voice ends; the outline fades and the whole card holds for reading.

Layout: the title and the rows stay above y 780, clear of the lower-third slot (y 800-890) and the
caption band (y 920-990) that assemble.py burns in; the footer sits in the footer slot (y 1032-1060).

Data (read, never retyped):
  docs/video/shotlist.json, S17b   duration, narration, title, the three rows and the footer (split
                                   verbatim from on_screen_text)
  docs/video/script.md, row S17b   cross-check: the narration and every quoted line
  the code the rows describe       guards only: the "Deciding as" field, the refused names, the name as
                                   the audit-log actor, AI_NOTICE on every public notice
  brief-evidence.md, sections 5, 6 guards only: the hedged at-risk line, the responsibility reading
                                   and the draft (planned) sign

Run: .venv/bin/python video/mg/S17b.py [--stills-only]
  -> video/build/mg/S17b.mp4 and stills in video/build/mg/stills/S17b_<beat>.png
"""
from __future__ import annotations

import ast
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from style import ROOT  # noqa: E402

from PIL import Image, ImageDraw  # noqa: E402

NAME = "S17b"
SHOT = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == NAME)
DURATION = round(SHOT["end_s"] - SHOT["start_s"], 3)  # 12.0 s
assert DURATION == 12.0, DURATION
assert SHOT["visual_type"] == "motion_graphic", SHOT["visual_type"]

# ---------- spec (read, never retyped) ----------

OST = [p.strip() for p in SHOT["on_screen_text"].split(" | ")]
assert len(OST) == 5, OST   # title, three rows, footer; a new part needs a new drawing


def ost_part(label: str) -> str:
    rx = re.compile(rf"^{re.escape(label)}: (.*)$")
    hits = [m.group(1).strip() for m in map(rx.match, OST) if m]
    assert len(hits) == 1, (label, OST)
    return hits[0]


TITLE = ost_part("Title")                                   # If it fails, who answers?
ROW_TEXT = [ost_part(f"Row {i}") for i in (1, 2, 3)]        # each "<head>: <item> · <item>", shown whole
FOOTER = ost_part("Footer")
ROWS = []                                                   # (head with its colon, [items])
for _r in ROW_TEXT:
    _head, _body = _r.split(": ", 1)
    _items = _body.split(" · ")
    assert len(_items) == 2, _r
    ROWS.append((_head + ":", _items))

# the storyboard row must carry the same narration and lines (script.md section 3)
_ROW = next(l for l in (ROOT / "docs" / "video" / "script.md").read_text().splitlines() if l.startswith(f"| {NAME} |"))
_cols = [c.strip() for c in _ROW.strip().strip("|").split(" | ")]
assert len(_cols) == 7 and _cols[3] == SHOT["narration"], "narration differs between shotlist.json and script.md"
for _s in [TITLE, *ROW_TEXT, FOOTER]:
    assert f'"{_s}"' in _cols[5], f"script.md row {NAME} lacks {_s!r}"

# the beats below are keyed to these clauses (the guide's six speech runs); if the narration changes, re-key
CLAUSES = ["If it fails,", "who answers?", "The person who approved it,", "named in our log,",
           "and the department running it.", "Every notice says an AI forecast is involved."]
assert SHOT["narration"] == " ".join(CLAUSES), SHOT["narration"]
assert " ".join(CLAUSES[:2]) == TITLE, (CLAUSES[:2], TITLE)         # the voice asks the title question aloud
# row 2's short written form ("the named approver") is what the voice says as "the person who approved it,
# named in our log"
assert ROW_TEXT[1].startswith("Who answers: the named approver"), ROW_TEXT[1]
# declutter (19 Oct): every row at most 10 words (head and items; the " · " separator is not a word), the
# footer at most 7
for _r in ROW_TEXT:
    assert len(_r.replace(" · ", " ").split()) <= 10, _r
assert len(FOOTER.split()) <= 7, FOOTER

# section 6, S17b and "Never say or show"
assert ROWS[0][0].casefold().startswith("may be more vulnerable"), ROWS[0]       # the hedge stays
assert "named" in ROW_TEXT[1], ROW_TEXT[1]                                       # "named", never a checked identity
assert "(planned)" in ROW_TEXT[2] and "sign" in ROW_TEXT[2], ROW_TEXT[2]         # the sign is a plan
assert "to be confirmed with the authorities" in FOOTER.casefold(), FOOTER   # "no partner yet": S17's chip
BANNED = ["most at risk", "signed in", "logged in", "verified", "authenticated", "legal", "compliant", "approved",
          "in partnership with", "the police support it", "built for the police", "replaces", "better than",
          "prevents crushes", "saves lives", "dangerous"]
# "approved" is banned about the law; the voice's "the person who approved it" is the operator approving an
# intervention (the decision engine.py records), so only that phrase is let through, and only in the voice
NARRATION_OK = ["the person who approved it"]
_narr = SHOT["narration"].casefold()
for _ok in NARRATION_OK:
    assert _narr.count(_ok) == 1, _ok
    _narr = _narr.replace(_ok, "")
for _s in [TITLE, *ROW_TEXT, FOOTER, _narr]:
    assert not any(b in _s.casefold() for b in BANNED), _s
assert text_size(FOOTER, 20, 500)[0] <= 1150, "the footer must stay one line of the 1,150 px footer slot"

# guards: the code and the evidence the rows describe (claims table section 4, rows S17b)
_read = lambda p: (ROOT / p).read_text()  # noqa: E731
assert ">Deciding as<" in _read("dashboard/src/components/OperatorField.tsx")
_schemas = _read("backend/app/schemas.py")
assert 'casefold() == "operator"' in _schemas and 'casefold() == "system"' in _schemas, "the refused names moved"
assert "actor=operator" in _read("backend/app/services/engine.py"), "the approver is no longer the audit-log actor"
_iv = _read("backend/app/services/intervention.py")
assert re.search(r'^AI_NOTICE = \{\s*"en": "[^"]*\bAI\b', _iv, re.M) and "AI_NOTICE[lang]" in _iv, "AI_NOTICE moved"
_brief = _read("docs/research/brief-evidence.md")
for _k in ("At-risk groups (keep the hedges)", "Responsibility (for discussion, not settled)", "Law 8/2005",
           "Law 14/2018", "Proposed trilingual sign"):
    assert _k in _brief, _k

# ---------- timing ----------

# voice start into the shot: 0.5 s (shot list S17b and script.md section 6, "Guide track"); if
# video/assemble.py's VOICE_START names S17b, it must agree
VOICE = 0.5
_vs = re.search(r"^VOICE_START = (\{[^}\n]*\})", _read("video/assemble.py"), re.M)
_assembly_start = ast.literal_eval(_vs.group(1)).get(NAME) if _vs else None
if _assembly_start is None:
    print(f"WARNING: video/assemble.py VOICE_START has no {NAME!r} entry, so the voice would be laid at 0.2 s; "
          f"add \"{NAME}\": {VOICE} (script.md section 6)", file=sys.stderr)
else:
    assert _assembly_start == VOICE, (_assembly_start, VOICE)

GUIDE_CLAUSES = [0.0, 1.297, 2.307, 3.920, 5.062, 6.712]   # silencedetect boundaries in video/build/guide/S17b.wav
GUIDE_END = 9.454
TITLE_IN = 0.35                              # the title's fade-in (it starts a frame before the cut)
BEATS = {
    "title": 0.0,                            # title, then row 1 (row 1 is not spoken)
    "row1": 0.1,
    "question": VOICE + GUIDE_CLAUSES[0],    # 0.5  "If it fails, who answers?" (the title, read aloud)
    "row2": VOICE + GUIDE_CLAUSES[2],        # 2.81 "The person who approved it," -> row 2
    "named": VOICE + GUIDE_CLAUSES[3],       # 4.42 "named in our log," -> the name line lights
    "department": VOICE + GUIDE_CLAUSES[4],  # 5.56 "and the department running it."
    "row3": VOICE + GUIDE_CLAUSES[5],        # 7.21 "Every notice ..." -> row 3
    "voice_end": VOICE + GUIDE_END,          # 9.95; the card holds to 12.0
}
assert BEATS["title"] + TITLE_IN - 1 / FPS <= BEATS["question"], "the title must be fully in when the voice asks it"
assert BEATS["voice_end"] < DURATION - 1.5, "the card must hold after the voice ends"
BUILD_T = [BEATS["row1"], BEATS["row2"], BEATS["row3"]]
ACTIVE = [None, (BEATS["row2"], BEATS["row3"]), (BEATS["row3"], BEATS["voice_end"] + 0.3)]   # outline while spoken

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
    img.alpha_composite(with_alpha(im, alpha), (int(round(x + dx)), int(round(y + dy))))


def out_ease(x: float) -> float:
    """Ease-out (visible from the first frames of a build)."""
    return 1 - (1 - clamp(x)) ** 3


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


def stroke(d, pts, fill, w):
    """A polyline with round caps and joints."""
    d.line(pts, fill=fill, width=int(w), joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - w / 2, y - w / 2, x + w / 2, y + w / 2), fill=fill)


# ---------- icons (plain shapes, 150 x 120; no emblem, logo or photo) ----------

ICON_W, ICON_H = 150, 120


def icon_people(d, q):
    """Row 1: a figure with a walking stick beside a wheelchair outline (amber, as Mrs Chan's in S01)."""
    c = (*WARNING, 255)
    Q = lambda x, y: (x * q, y * q)  # noqa: E731
    d.ellipse((31 * q, 8 * q, 53 * q, 30 * q), fill=c)                         # head
    stroke(d, [Q(42, 38), Q(47, 72)], c, 16 * q)                                # body, leaning a little forward
    stroke(d, [Q(47, 74), Q(37, 110)], c, 9 * q)                                # legs
    stroke(d, [Q(47, 74), Q(56, 110)], c, 9 * q)
    stroke(d, [Q(45, 44), Q(62, 60)], c, 8 * q)                                 # arm to the stick
    stroke(d, [Q(66, 60), Q(68, 112)], c, 5 * q)                                # walking stick
    d.arc((56 * q, 52 * q, 68 * q, 66 * q), 180, 360, fill=c, width=5 * q)      # its crook
    wheelchair_icon(d, 116 * q, 72 * q, 1.5 * q, colour=c, width=4)             # outline (style.py)


LOG_BOX = (10, 8, 140, 114)
LOG_LINES = [(28, 92), (46, 70), (64, 72), (82, 60), (100, 76)]   # (y, bar length); line 2 is the name line
NAME_LINE = 2


def icon_log(d, q, lit: bool = False):
    """Row 2: an audit-log list. lit=False: the list with every line grey; lit=True: only the name
    line (a small person and a cyan bar), drawn over the grey one when it lights up."""
    Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
    if not lit:
        d.rounded_rectangle(Q(*LOG_BOX), 12 * q, fill=(*NAVY_3, 255))
        d.rounded_rectangle(Q(10, 8, 140, 18), 6 * q, fill=(*INK_3, 255))
        d.rectangle(Q(10, 14, 140, 18), fill=(*NAVY_3, 255))
    for i, (y, w_) in enumerate(LOG_LINES):
        if i == NAME_LINE:
            col = (*CYAN, 255) if lit else (*INK_3, 255)
            d.ellipse(Q(24, y - 9, 34, y + 1), fill=col)                           # person: head
            d.pieslice(Q(21, y - 1, 37, y + 15), 180, 360, fill=col)               # shoulders
            d.rounded_rectangle(Q(44, y - 5, 44 + w_ + 18, y + 6), 5 * q, fill=col)
        elif not lit:
            d.ellipse(Q(25, y - 4, 33, y + 4), fill=(*INK_3, 255))
            d.rounded_rectangle(Q(44, y - 4, 44 + w_, y + 4), 4 * q, fill=(*INK_3, 200))


def icon_sign(d, q):
    """Row 3: a notice board on a post (dashed edge: planned) with three text lines (zh / en / pt),
    and the phone it stands beside."""
    Q = lambda *v: tuple(x * q for x in v)  # noqa: E731
    d.rounded_rectangle(Q(55, 70, 63, 114), 3 * q, fill=(*INK_3, 255))                   # post
    d.rounded_rectangle(Q(40, 110, 78, 116), 3 * q, fill=(*INK_3, 255))                   # foot
    board = Q(4, 6, 114, 74)
    d.rounded_rectangle(board, 10 * q, fill=(*NAVY_3, 255))
    dashed_path(d, rrect_path(board, 10 * q), (*INK, 255), 3 * q, 10 * q, 7 * q)
    for y, w_ in ((24, 70), (40, 82), (56, 62)):                                           # three languages
        d.rounded_rectangle(Q(20, y - 4, 20 + w_, y + 4), 4 * q, fill=(*INK_2, 255))
    phone_icon(d, 134 * q, 92 * q, 0.42 * q, fill=(*INK, 255), screen=(*NAVY, 255))       # the phone it stands by
    d.ellipse(Q(130, 88, 138, 96), fill=(*CYAN, 255))


# ---------- layout ----------

ROW_X0, ROW_X1, ROW_H, ROW_GAP, ROW_Y0 = 100, 1820, 160, 24, 236
TITLE_XY, TITLE_SIZE = (ROW_X0, 100), 64                    # the title lines up with the rows' left edge
ROW_BOXES = [(ROW_X0, ROW_Y0 + i * (ROW_H + ROW_GAP), ROW_X1, ROW_Y0 + i * (ROW_H + ROW_GAP) + ROW_H) for i in range(3)]
assert ROW_BOXES[-1][3] < 780, "the rows must stay above y 780 (lower-third y 800-890, captions y 920-990)"
ICON_DX = 34
TEXT_X = ROW_X0 + ICON_DX + ICON_W + 38
HEAD_SIZE, HEAD_DY = 30, 32
BODY_DY = 80
TEXT_MAX = ROW_X1 - 34 - TEXT_X
SEP = " · "


def body_runs(items):
    """[(text, weight, colour)] for one row: the items in off-white, the separator dimmer, and
    '(planned)' in amber so the plan status reads at a glance."""
    runs = []
    for j, it in enumerate(items):
        if j:
            runs.append((SEP, 500, INK_3))
        for part in re.split(r"(\(planned\))", it):
            if part:
                runs.append((part, 600, WARNING if part == "(planned)" else INK))
    return runs


def runs_width(runs, size):
    return sum(font(size, w).getlength(t) for t, w, _ in runs)


# one body size for all three rows: the largest that keeps every row on one line
BODY_SIZE = next(s for s in (42, 40, 38, 36) if all(runs_width(body_runs(items), s) <= TEXT_MAX for _, items in ROWS))
assert BODY_SIZE >= 38, BODY_SIZE   # readable on a phone with the sound off (section 6, "Final check")


def draw_runs(im, x, y, runs, size):
    for t, w, col in runs:
        draw_text(im, (x, y), t, size, w, col)
        x += font(size, w).getlength(t)


def row_sprites(i: int) -> dict:
    x0, y0, x1, y1 = ROW_BOXES[i]
    head, items = ROWS[i]
    iy = (y0 + y1) / 2 - ICON_H / 2
    icon_fn = (icon_people, icon_log, icon_sign)[i]
    sp = {"bg": layer_sprite(lambda im: rounded(im, (x0, y0, x1, y1), 24, fill=NAVY_2)),
          "outline": layer_sprite(lambda im: rounded(im, (x0, y0, x1, y1), 24, outline=CYAN, width=3)),
          "icon": (hires((ICON_W, ICON_H), icon_fn), (x0 + ICON_DX, iy)),
          "head": layer_sprite(lambda im: draw_text(im, (TEXT_X, y0 + HEAD_DY), head, HEAD_SIZE, 600, INK_2)),
          "body": layer_sprite(lambda im: draw_runs(im, TEXT_X, y0 + BODY_DY, body_runs(items), BODY_SIZE))}
    bim, (bx, by) = sp["body"]
    # at least the icon's left inset (ICON_DX) of air between the text and the card's right edge
    assert bx + bim.width <= x1 - ICON_DX and by + bim.height <= y1 - 16, f"row {i + 1} text runs off its card"
    if i == 1:
        sp["name_lit"] = (hires((ICON_W, ICON_H), lambda d, q: icon_log(d, q, lit=True)), (x0 + ICON_DX, iy))
        ny = iy + LOG_LINES[NAME_LINE][0]
        ring = (x0 + ICON_DX + 14, ny - 16, x0 + ICON_DX + 44 + LOG_LINES[NAME_LINE][1] + 28, ny + 18)
        sp["name_ring"] = ring
    return sp


ROW_SPRITES = [row_sprites(i) for i in range(3)]
TITLE_SPRITE = layer_sprite(lambda im: draw_text(im, TITLE_XY, TITLE, TITLE_SIZE, 700, INK))
assert TITLE_SPRITE[1][1] + TITLE_SPRITE[0].height < ROW_BOXES[0][1] - 20, "title overlaps row 1"
FOOTER_SPRITE = layer_sprite(lambda im: footer(im, FOOTER))
assert FOOTER_SPRITE[0].height < 30 and FOOTER_SPRITE[1][1] >= 1030, "footer must stay one line in the footer slot"


def name_pulse(k: float):
    """A ring that grows and fades around the name line as it lights up."""
    x0, y0, x1, y1 = ROW_SPRITES[1]["name_ring"]
    g = 10 * k
    box = (x0 - g, y0 - g, x1 + g, y1 + g)
    im = hires((int(box[2] - box[0]) + 8, int(box[3] - box[1]) + 8),
               lambda d, q: d.rounded_rectangle((4 * q, 4 * q, (box[2] - box[0] + 4) * q, (box[3] - box[1] + 4) * q),
                                                int((16 + g) * q), outline=(*CYAN, 255), width=3 * q))
    return im, (box[0] - 4, box[1] - 4)


# ---------- frame drawing ----------

BG = canvas(NAVY)


def seg(t: float, a: float, b: float, edge: float = 0.3) -> float:
    if t < a or t > b + edge:
        return 0.0
    return min(out_ease((t - a) / edge), 1 - progress(t, b, edge))


def frame(t: float) -> Image.Image:
    img = BG.copy()
    a = out_ease((t - BEATS["title"] + 1 / FPS) / TITLE_IN)      # already on the first frame after the cut
    put(img, TITLE_SPRITE, a, dy=12 * (1 - a))
    for i, sp in enumerate(ROW_SPRITES):
        t0 = BUILD_T[i]
        k = out_ease((t - t0) / 0.35)
        if k <= 0:
            continue
        lift = 18 * (1 - k)
        put(img, sp["bg"], k, dy=lift)
        if ACTIVE[i]:
            put(img, sp["outline"], k * seg(t, *ACTIVE[i]), dy=lift)
        ki = out_ease((t - t0 - 0.04) / 0.35)
        put(img, sp["icon"], ki, dy=lift + 8 * (1 - ki))
        if i == 1:
            kn = progress(t, BEATS["named"], 0.3)
            put(img, sp["name_lit"], kn, dy=lift)
            if BEATS["named"] <= t <= BEATS["named"] + 0.6:
                kp = (t - BEATS["named"]) / 0.6
                put(img, name_pulse(ease(kp)), (1 - kp) * 0.9)
        for j, key in enumerate(("head", "body")):
            kt = out_ease((t - t0 - 0.07 * (j + 1)) / 0.35)
            put(img, sp[key], kt, dy=lift + 10 * (1 - kt))
    put(img, FOOTER_SPRITE, out_ease((t - 0.2) / 0.35))
    return img


STILLS = {"title": 0.25, "row1": 0.45, "question": 1.9, "row2": 3.2, "named": 4.6, "department": 5.7,
          "row3": 7.5, "row3_built": 8.2, "voice_end": 10.3, "end": 11.95}

if __name__ == "__main__":
    print(f"rows: body {BODY_SIZE} px; widths " +
          ", ".join(f"{runs_width(body_runs(items), BODY_SIZE):.0f}" for _, items in ROWS) + f" of {TEXT_MAX} px")
    for k_, tt in STILLS.items():
        print(still(f"{NAME}_{k_}", frame(tt)))
    if "--stills-only" not in sys.argv:
        print(render(NAME, DURATION, frame))
