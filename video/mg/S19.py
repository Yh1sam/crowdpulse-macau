"""S19 · Relay close (4:02.5-4:13.5, 11.0 s): the team on camera, one line each, then all together.

Storyboard: docs/video/script.md section 3, row S19 (narration, visual, on-screen text); section 4, the three S19
claims rows (the "Next" line is a plan; "The AI recommends. A person decides." and "Nothing identifying leaves the
phone" are real code); section 1 "Team roles" (who carries which STEMB letter); section 5A item 5 (the pilot authority
is still [TEAM TO RESEARCH]); section 5D and section 6 "team_footage" (wide shot, same set as S05); the S19 row of the
overrun plan (drop the separate all-together second first, never cut a line). docs/video/shotlist.json, entry S19.

Data sources (nothing is retyped):
  - docs/video/shotlist.json: the shot duration (end_s - start_s).
  - docs/video/script.md, section 3, S19 row:
      narration cell  -> the four relay lines and who says them ([M5], [M3], [M2], [M1]), in order;
      visual cell     -> the slate's direction line (its first sentence);
      on-screen cell  -> the two text lines, verbatim: the "Next" line (with its [TEAM TO RESEARCH: ...] placeholder,
                         drawn in an amber dashed box) and "The AI recommends. A person decides." (split at its
                         sentence break so each half lands with its speaker).
    When the team fills the placeholder in the storyboard, re-running this script picks it up.
  - docs/video/script.md, section 1, "Team roles" table: [MEMBER n] -> STEMB letter.

The team has not filmed yet, so the picture is an amber "[TEAM FOOTAGE]" slate: five silhouettes in a wide shot,
the speaker lit in turn (M5, M3, M2, M1; M4 in frame), then everyone together. The two on-screen lines sit in the top
band (y 44-124) so they stay above the faces in the real wide shot; the slate keeps the lower-third slot
(x 60-780, y 795-895) and the caption band (y 900-995) clear for the whole shot, because a new speaker starts four times.
No chapter card, badge or footer: the storyboard gives S19 none. Captions and lower-thirds are added at assembly.

Outputs:
  - video/build/mg/S19.mp4: slate + text (stand-in for the whole shot).
  - video/build/overlays/S19_text.mov: the two text lines and their top scrim only, with alpha, full shot length,
    to lay over the real relay footage at assembly.
  - video/build/mg/stills/S19_*.png: layout checks at the key beats (S19_overlay_check shows the overlay on a bright
    stand-in background, the worst case for legibility).

Run: .venv/bin/python video/mg/S19.py [--stills-only]
"""
from __future__ import annotations

import json
import math
import re
import sys

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F403

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S19"
_entry = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_entry["end_s"] - _entry["start_s"], 3)  # 11.0 s

# Times in seconds from the shot start, keyed to the narration at about 140 words per minute
# (9 + 3 + 3 + 5 words, a 0.4 s hand-off between speakers, then about 1 s all together).
# re-key to the real voice take
BEATS = {
    "m5": 0.25,         # [M5] "Next: a supervised street pilot in Macau, with permission."  -> the "Next" line
    "m5_end": 4.10,
    "m3": 4.50,         # [M3] "The AI recommends."                                          -> first half of the tagline
    "m3_end": 5.80,
    "m2": 6.20,         # [M2] "A person decides."                                           -> second half lands
    "m2_end": 7.50,
    "m1": 7.90,         # [M1] "Nothing identifying leaves the phone."                       (tagline holds)
    "m1_end": 10.00,
    "together": 10.05,  # everyone together, last ~1 s (overrun plan: drop this second first, never a line)
}
HANDOFF = 0.40          # spotlight move from one speaker to the next (s), ends on the next speaker's first word
TEXT_IN = 0.40          # fade-and-rise of each text block (s)
NEXT_OUT = 0.35         # the "Next" line leaves this long before M3 starts
SLIDE = 0.50            # first tagline half slides left to make room for the second (s), in the M2 hand-off
SLIDE_LEAD = 0.40       # ... starting this long before M2's first word, so the halves never overlap

SS = 2                  # supersampling for shapes
PH = re.compile(r"(\[[^\]]+\])")  # a bracketed placeholder

# ---------- text from the storyboard ----------

SCRIPT = (ROOT / "docs" / "video" / "script.md").read_text()


def storyboard_cell(shot: str, col: int) -> str:
    """Cell `col` of the shot's row in the section 3 storyboard (the first table row that starts with the shot id)."""
    row = next(l for l in SCRIPT.splitlines() if l.startswith(f"| {shot} |"))
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    assert len(cells) == 7, (shot, len(cells))
    return cells[col]


NARRATION = storyboard_cell(SHOT, 3)
RELAY = [(f"[MEMBER {n}]", line.strip()) for n, line in re.findall(r"\[M(\d)\]\s*([^\[]+)", NARRATION)]
assert [m for m, _ in RELAY] == ["[MEMBER 5]", "[MEMBER 3]", "[MEMBER 2]", "[MEMBER 1]"], RELAY
SPEAKER_BEATS = ["m5", "m3", "m2", "m1"]

DIRECTION = storyboard_cell(SHOT, 4).split("<br>")[0].split(". ")[0].strip().rstrip(".") + "."
assert DIRECTION.startswith("Wide shot of the whole team"), DIRECTION

ON_SCREEN = [p.strip().strip('"') for p in storyboard_cell(SHOT, 5).split("<br>")]
assert len(ON_SCREEN) == 2, ON_SCREEN
NEXT_LINE, TAGLINE = ON_SCREEN
assert NEXT_LINE.startswith("Next:"), NEXT_LINE
TAG_A, TAG_B = (s if s.endswith(".") else s + "." for s in TAGLINE.split(". ", 1))
assert (TAG_A, TAG_B) == ("The AI recommends.", "A person decides."), (TAG_A, TAG_B)

# [MEMBER n] -> STEMB letter (section 1, Team roles)
ROLE = {m.group(1): m.group(2) for m in re.finditer(r"^\| (\[MEMBER \d\])(?: \(optional\))? \| \*\*([STEMB])\*\* ", SCRIPT, re.M)}
assert sorted(ROLE.values()) == sorted(l for l, _ in STEMB), ROLE

# Slate columns, left to right: the four speakers in relay order, then M4 (in frame, no line).
_in_frame = [m for m in sorted(ROLE) if m not in {r for r, _ in RELAY}]
assert _in_frame == ["[MEMBER 4]"], _in_frame
COLUMNS = [dict(member=m, letter=ROLE[m], line=f"“{l}”", beat=b) for (m, l), b in zip(RELAY, SPEAKER_BEATS)]
COLUMNS += [dict(member=m, letter=ROLE[m], line="in frame", beat=None) for m in _in_frame]

# ---------- small helpers (own) ----------


def S(v: float) -> int:
    return int(round(v * SS))


def SB(box) -> tuple[int, int, int, int]:
    return tuple(S(v) for v in box)


class Sprite:
    """A cropped RGBA image and where it sits on the frame."""

    def __init__(self, img: Image.Image, x: float, y: float):
        self.img, self.x, self.y = img, int(round(x)), int(round(y))


def sprite_from(draw_fn, shadow: float = 0.0) -> Sprite:
    """Runs draw_fn(img, shapes) on a full transparent frame (+ a 2x shape layer composited first) and crops it.
    shadow > 0 adds a soft dark shadow under everything (for text that sits over footage)."""
    shapes = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    img = transparent()
    draw_fn(img, ImageDraw.Draw(shapes))
    base = shapes.resize((W, H), Image.LANCZOS)
    base.alpha_composite(img)
    if shadow > 0:
        a = np.array(base)[..., 3].astype(np.float32) * shadow
        sh = np.zeros((H, W, 4), np.uint8)
        sh[..., 3] = a.astype(np.uint8)
        sh_img = Image.fromarray(sh, "RGBA").filter(ImageFilter.GaussianBlur(9))
        out = transparent()
        out.alpha_composite(sh_img, dest=(0, 4))
        out.alpha_composite(base)
        base = out
    bbox = base.getbbox()
    return Sprite(base.crop(bbox), bbox[0], bbox[1])


def alpha_mul(img: Image.Image, k: float) -> Image.Image:
    if k >= 0.999:
        return img
    a = np.array(img)
    a[..., 3] = (a[..., 3].astype(np.float32) * clamp(k)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def put(dst: Image.Image, sp: Sprite, k: float, dx: float = 0.0, dy: float = 0.0) -> None:
    if k <= 0.002:
        return
    dst.alpha_composite(alpha_mul(sp.img, k), dest=(sp.x + int(round(dx)), sp.y + int(round(dy))))


def path_points(pts, step: float = 1.0):
    out = [(pts[0][0], pts[0][1], 0.0)]
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for i in range(1, n + 1):
            out.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, acc + seg * i / n))
        acc += seg
    return out


def dashed_path(d: ImageDraw.ImageDraw, pts, fill, width: int, dash: float, gap: float) -> None:
    run = []
    for x, y, s in path_points(pts):
        if (s % (dash + gap)) < dash:
            run.append((x, y))
        elif run:
            if len(run) > 1:
                d.line(run, fill=fill, width=width)
            run = []
    if len(run) > 1:
        d.line(run, fill=fill, width=width)


def rrect_path(box, r: float, n: int = 10):
    x0, y0, x1, y1 = box
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pts.append(pts[0])
    return pts


def dashed_rrect(d, box, r, colour, width, dash=None, gap=None) -> None:
    """Dashed rounded rectangle on all four sides, at SS scale (box and sizes already scaled)."""
    dashed_path(d, rrect_path(box, r), colour, width, dash or 9 * SS, gap or 6 * SS)


def camera_glyph(d, x: float, y: float, colour=WARNING) -> None:
    """Small video-camera glyph (as in S05), top-left corner at (x, y), SS-scale drawing."""
    d.rounded_rectangle(SB((x, y, x + 34, y + 26)), S(6), fill=colour)
    d.polygon([(S(x + 36), S(y + 13)), (S(x + 50), S(y + 3)), (S(x + 50), S(y + 23))], fill=colour)


# ---------- rich text: words and [placeholders] laid out and wrapped together ----------

PH_PAD = 12


def tokens(text: str) -> list[tuple[str, bool]]:
    out = []
    for part in PH.split(text):
        if not part:
            continue
        if PH.fullmatch(part):
            out.append((part, True))
        else:
            out += [(w_, False) for w_ in part.split()]
    return out


def tok_w(tok: tuple[str, bool], size: int, weight: int) -> float:
    s, ph = tok
    return text_font(s, size, max(weight, 600) if ph else weight).getlength(s) + (2 * PH_PAD if ph else 0)


def rich_lines(text: str, size: int, weight: int, max_w: float) -> list[list[tuple[str, bool]]]:
    space = text_font(" ", size, weight).getlength(" ")
    lines, cur, cw = [], [], 0.0
    for tk in tokens(text):
        w_ = tok_w(tk, size, weight)
        if cur and cw + space + w_ > max_w:
            lines.append(cur)
            cur, cw = [], 0.0
        cw += (space if cur else 0) + w_
        cur.append(tk)
    if cur:
        lines.append(cur)
    return lines


def line_w(line, size: int, weight: int) -> float:
    space = text_font(" ", size, weight).getlength(" ")
    return sum(tok_w(t, size, weight) for t in line) + space * (len(line) - 1)


def draw_rich_line(img, d2, x: float, cy: float, line, size: int, weight: int, fill=INK, chip_h: float = 44,
                   lead_fill=None) -> None:
    """Draws one laid-out line; placeholders sit in amber dashed boxes; lead_fill colours a leading 'Word:'."""
    space = text_font(" ", size, weight).getlength(" ")
    for i, (s, ph) in enumerate(line):
        w_ = tok_w((s, ph), size, weight)
        if ph:
            box = (x, cy - chip_h / 2, x + w_, cy + chip_h / 2)
            d2.rounded_rectangle(SB(box), S(9), fill=(*NAVY, 240))
            dashed_rrect(d2, SB(box), S(9), (*WARNING, 255), S(2.2))
            draw_text(img, (x + PH_PAD, cy), s, size, max(weight, 600), WARNING, anchor="lm")
        else:
            lead = i == 0 and lead_fill is not None and s.endswith(":")
            draw_text(img, (x, cy), s, size, 700 if lead else weight, lead_fill if lead else fill, anchor="lm")
        x += w_ + space


# ---------- top band: the two on-screen lines (also the overlay for the real footage) ----------

TOP_Y = 44                       # top of the text band (chapter-card height; S19 has no card or badge)
NEXT_SIZE, NEXT_W = 30, 1300     # "Next" line: size, preferred maximum line width (wraps beyond it)
NEXT_PITCH, NEXT_PAD_X, NEXT_PAD_Y = 54, 30, 18
TAG_SIZE = 62

NEXT_LINES = rich_lines(NEXT_LINE, NEXT_SIZE, 600, 1740)        # one line if it fits the frame, else wrapped
if len(NEXT_LINES) > 1:
    NEXT_LINES = rich_lines(NEXT_LINE, NEXT_SIZE, 600, NEXT_W)
_next_w = max(line_w(l, NEXT_SIZE, 600) for l in NEXT_LINES)
NEXT_BOX = ((W - _next_w) / 2 - NEXT_PAD_X, TOP_Y,
            (W + _next_w) / 2 + NEXT_PAD_X, TOP_Y + 2 * NEXT_PAD_Y + NEXT_PITCH * (len(NEXT_LINES) - 1) + 44)
TEXT_CY = (NEXT_BOX[1] + NEXT_BOX[3]) / 2 if len(NEXT_LINES) == 1 else TOP_Y + 40   # tagline centre line


def _next_card(img, d2):
    d2.rounded_rectangle(SB(NEXT_BOX), S(18), fill=(*NAVY_2, 236))
    for i, ln in enumerate(NEXT_LINES):
        cy = NEXT_BOX[1] + NEXT_PAD_Y + 22 + i * NEXT_PITCH
        draw_rich_line(img, d2, (W - line_w(ln, NEXT_SIZE, 600)) / 2, cy, ln, NEXT_SIZE, 600, INK, lead_fill=CYAN)


NEXT_CARD = sprite_from(_next_card, shadow=0.55)

_fa, _fb = text_font(TAG_A, TAG_SIZE, 600), text_font(TAG_B, TAG_SIZE, 800)
TAG_GAP = 0.55 * TAG_SIZE
WA, WB = _fa.getlength(TAG_A), _fb.getlength(TAG_B)
TAG_X0 = (W - (WA + TAG_GAP + WB)) / 2        # final left edge of the whole tagline
TAG_A_ALONE_DX = (W - WA) / 2 - TAG_X0         # while alone, the first half sits centred


def _tag_a(img, d2):
    draw_text(img, (TAG_X0, TEXT_CY), TAG_A, TAG_SIZE, 600, INK, anchor="lm")


def _tag_b(img, d2):
    draw_text(img, (TAG_X0 + WA + TAG_GAP, TEXT_CY), TAG_B, TAG_SIZE, 800, INK, anchor="lm")
    # a short cyan rule under "A person decides." (the human in the loop), drawn once it has landed
    y = TEXT_CY + TAG_SIZE * 0.62
    d2.rounded_rectangle(SB((TAG_X0 + WA + TAG_GAP, y, TAG_X0 + WA + TAG_GAP + WB, y + 5)), S(2.5), fill=(*CYAN, 255))


TAG_A_S = sprite_from(_tag_a, shadow=0.7)
TAG_B_S = sprite_from(_tag_b, shadow=0.7)
TEXT_BOTTOM = max(NEXT_CARD.y + NEXT_CARD.img.height, TAG_B_S.y + TAG_B_S.img.height)


def _scrim() -> Sprite:
    """Soft navy gradient behind the top band, so the white text reads over any footage."""
    hgt = int(TEXT_BOTTOM + 110)
    ys = np.arange(hgt, dtype=np.float32)
    k = np.clip((hgt - ys) / (hgt - (TEXT_BOTTOM - 40)), 0, 1)
    prof = (k * k * (3 - 2 * k)) * 0.74
    arr = np.zeros((hgt, W, 4), np.uint8)
    arr[..., 0], arr[..., 1], arr[..., 2] = NAVY
    arr[..., 3] = (prof[:, None] * 255).astype(np.uint8)
    return Sprite(Image.fromarray(arr, "RGBA"), 0, 0)


SCRIM = _scrim()


def overlay_at(t: float, img: Image.Image | None = None) -> Image.Image:
    """The top band at time t, drawn onto img (a transparent frame by default)."""
    img = img if img is not None else transparent()
    put(img, SCRIM, progress(t, 0.0, 0.3))
    # the "Next" line: in on M5's first word, out just before M3 starts
    k_in = progress(t, BEATS["m5"] + 0.05, TEXT_IN)
    k_out = progress(t, BEATS["m3"] - NEXT_OUT - 0.05, NEXT_OUT)
    put(img, NEXT_CARD, k_in * (1 - k_out), dy=(1 - k_in) * 12 - k_out * 10)
    # "The AI recommends." on M3; slides left as "A person decides." lands on M2; both hold to the end
    ka = progress(t, BEATS["m3"], TEXT_IN)
    ks = progress(t, BEATS["m2"] - SLIDE_LEAD, SLIDE)
    put(img, TAG_A_S, ka, dx=TAG_A_ALONE_DX * (1 - ks), dy=(1 - ka) * 12)
    kb = progress(t, BEATS["m2"], TEXT_IN)
    put(img, TAG_B_S, kb, dx=(1 - kb) * 18)
    return img


# ---------- the slate (stand-in for the wide relay shot) ----------

PANEL = (60, int(TEXT_BOTTOM + 30), 1860, 782)   # ends above the lower-third slot (y 795) and the caption band
COL_W = (PANEL[2] - PANEL[0]) / len(COLUMNS)
COL_CX = [PANEL[0] + COL_W * (i + 0.5) for i in range(len(COLUMNS))]
HEAD_Y = PANEL[1] + 44           # header centre line
DIR_Y = PANEL[1] + 86            # direction line centre
STAGE_TOP = PANEL[1] + 142       # tallest head top
STAGE_BOT = 540                  # silhouettes are cut here (waist height in a wide shot)
CHIP_CY = 576
QUOTE_Y = 608
QUOTE_SIZE, QUOTE_W = 24, int(COL_W - 50)
TOG_Y = 748
SPOT = (STAGE_TOP - 18, 712)     # spotlight card, top and bottom

SIL_DIM = (40, 56, 88)
SIL_LIT = (104, 128, 170)
assert STAGE_BOT - STAGE_TOP >= 150, "top band too tall for the slate"


def silhouette(d, cx: float, top: float, bottom: float, colour) -> None:
    """Head and shoulders to waist (frame pixels, drawn at SS scale)."""
    h = bottom - top
    hw, hh = 0.17 * h, 0.36 * h                       # head half-width, head height
    d.ellipse(SB((cx - hw, top, cx + hw, top + hh)), fill=colour)
    d.rectangle(SB((cx - 0.08 * h, top + hh * 0.8, cx + 0.08 * h, top + hh + 0.08 * h)), fill=colour)
    d.rounded_rectangle(SB((cx - 0.48 * h, top + hh + 0.04 * h, cx + 0.48 * h, bottom + 0.4 * h)), S(0.26 * h), fill=colour)


def head_top(i: int) -> float:
    return STAGE_TOP + (0, 16, 6, 20, 10)[i % 5]   # people of slightly different heights


def _clip(img: Image.Image, y1: float) -> None:
    """Clears everything below y1 (SS-scale layer): the silhouettes stop at the waist line."""
    a = np.array(img)
    a[S(y1):, :, 3] = 0
    img.paste(Image.fromarray(a, "RGBA"))


def _slate_base(img, d2):
    d2.rounded_rectangle(SB(PANEL), S(26), fill=(*NAVY_2, 255))
    dashed_rrect(d2, SB(PANEL), S(26), (*WARNING, 255), S(3), S(18), S(11))
    camera_glyph(d2, PANEL[0] + 44, HEAD_Y - 13)
    head = "[TEAM FOOTAGE]"
    draw_text(img, (PANEL[0] + 110, HEAD_Y), head, 30, 700, WARNING, anchor="lm")
    hw = text_font(head, 30, 700).getlength(head)
    draw_text(img, (PANEL[0] + 110 + hw + 18, HEAD_Y), "whole team, relay", 30, 600, INK, anchor="lm")
    draw_text(img, (PANEL[0] + 110, DIR_Y), DIRECTION, 24, 500, INK_2, anchor="lm")


def _people(colour):
    def fn(img, d2):
        for i, cx in enumerate(COL_CX):
            silhouette(d2, cx, head_top(i), STAGE_BOT, (*colour, 255))
    return fn


def _labels(img, d2):
    """Member chips (amber dashed: [MEMBER n] is a placeholder) with their STEMB tiles, unlit."""
    for col, cx in zip(COLUMNS, COL_CX):
        tw = text_font(col["member"], 24, 700).getlength(col["member"]) + 2 * PH_PAD
        tile, gap = 40, 10
        x0 = cx - (tile + gap + tw) / 2
        d2.rounded_rectangle(SB((x0, CHIP_CY - tile / 2, x0 + tile, CHIP_CY + tile / 2)), S(9), fill=(*NAVY_3, 255))
        draw_text(img, (x0 + tile / 2, CHIP_CY), col["letter"], 24, 800, INK_3, anchor="mm")
        box = (x0 + tile + gap, CHIP_CY - 20, x0 + tile + gap + tw, CHIP_CY + 20)
        d2.rounded_rectangle(SB(box), S(9), fill=(*NAVY, 255))
        dashed_rrect(d2, SB(box), S(9), (*WARNING, 255), S(2))
        draw_text(img, (box[0] + PH_PAD, CHIP_CY), col["member"], 24, 700, WARNING, anchor="lm")


def tile_box(i: int):
    col = COLUMNS[i]
    tw = text_font(col["member"], 24, 700).getlength(col["member"]) + 2 * PH_PAD
    x0 = COL_CX[i] - (40 + 10 + tw) / 2
    return (x0, CHIP_CY - 20, x0 + 40, CHIP_CY + 20)


def _tile_lit(i: int):
    def fn(img, d2):
        x0, y0, x1, y1 = tile_box(i)
        d2.rounded_rectangle(SB((x0, y0, x1, y1)), S(9), fill=(*CYAN, 255))
        draw_text(img, ((x0 + x1) / 2, (y0 + y1) / 2), COLUMNS[i]["letter"], 24, 800, NAVY, anchor="mm")
    return fn


def _quote(i: int, colour):
    def fn(img, d2):
        col = COLUMNS[i]
        for k, ln in enumerate(wrap(col["line"], QUOTE_SIZE, 500, QUOTE_W)):
            draw_text(img, (COL_CX[i], QUOTE_Y + k * 31), ln, QUOTE_SIZE, 500, colour, anchor="ma")
    return fn


TOG_LABEL = "then all together"


def _together(colour, rule):
    def fn(img, d2):
        tw = text_font(TOG_LABEL, 26, 600).getlength(TOG_LABEL)
        x0, x1 = COL_CX[0] - 120, COL_CX[-1] + 120
        for a, b in ((x0, W / 2 - tw / 2 - 22), (W / 2 + tw / 2 + 22, x1)):
            d2.rounded_rectangle(SB((a, TOG_Y - 1.5, b, TOG_Y + 1.5)), S(1.5), fill=(*rule, 255))
        for x in (x0, x1):
            d2.rounded_rectangle(SB((x - 1.5, TOG_Y - 14, x + 1.5, TOG_Y + 1.5)), S(1.5), fill=(*rule, 255))
        draw_text(img, (W / 2, TOG_Y), TOG_LABEL, 26, 600, colour, anchor="mm")
    return fn


def _build_base() -> Image.Image:
    """Navy, the dashed slate panel and its header (under the spotlight)."""
    img = canvas(NAVY)
    put(img, sprite_from(_slate_base), 1.0)
    return img


def _build_stage() -> Sprite:
    """Unlit silhouettes, member chips, quotes and the together label (over the spotlight, so they stay crisp)."""
    shapes = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    _people(SIL_DIM)(None, ImageDraw.Draw(shapes))
    _clip(shapes, STAGE_BOT)
    img = shapes.resize((W, H), Image.LANCZOS)
    for sp in [sprite_from(_labels), *(sprite_from(_quote(i, INK_3)) for i in range(len(COLUMNS))),
               sprite_from(_together(INK_3, NAVY_3))]:
        put(img, sp, 1.0)
    bbox = img.getbbox()
    return Sprite(img.crop(bbox), bbox[0], bbox[1])


def _lit_person(i: int) -> Sprite:
    shapes = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    silhouette(ImageDraw.Draw(shapes), COL_CX[i], head_top(i), STAGE_BOT, (*SIL_LIT, 255))
    _clip(shapes, STAGE_BOT)
    lay = shapes.resize((W, H), Image.LANCZOS)
    bbox = lay.getbbox()
    return Sprite(lay.crop(bbox), bbox[0], bbox[1])


BASE = _build_base()
STAGE = _build_stage()
LIT = [_lit_person(i) for i in range(len(COLUMNS))]
TILES_LIT = [sprite_from(_tile_lit(i)) for i in range(len(COLUMNS))]
Q_ACTIVE = [sprite_from(_quote(i, INK)) for i in range(len(COLUMNS))]
Q_DONE = [sprite_from(_quote(i, INK_2)) for i in range(len(COLUMNS))]
TOG_LIT = sprite_from(_together(INK, CYAN))

# layout checks: slate clear of the lower-third slot and the caption band, nothing off-frame
assert PANEL[3] < 795 and TOG_Y + 20 < PANEL[3], PANEL
for _sp in [NEXT_CARD, TAG_A_S, TAG_B_S, *Q_ACTIVE, TOG_LIT]:
    assert _sp.x >= 56 and _sp.x + _sp.img.width <= W - 56 and _sp.y >= 20, (_sp.x, _sp.y)  # (incl. soft shadows)
    assert _sp.y + _sp.img.height <= 790, (_sp.y, _sp.img.height)
assert PANEL[1] > TEXT_BOTTOM, (PANEL, TEXT_BOTTOM)
assert TAG_A_S.x + TAG_A_ALONE_DX >= 56
# when "A person decides." starts to fade in, the sliding first half has already cleared its place
assert TAG_A_ALONE_DX * (1 - progress(BEATS["m2"], BEATS["m2"] - SLIDE_LEAD, SLIDE)) < TAG_GAP - 4

# ---------- timing of the spotlight ----------

SPEAK_T = [BEATS[b] for b in SPEAKER_BEATS]
SPEAK_END = [BEATS[b + "_end"] for b in SPEAKER_BEATS]


def spot_index(t: float) -> float:
    """Spotlight position as a column index: moves to the next speaker during the HANDOFF before their first word."""
    s = 0.0
    for i in range(1, len(SPEAK_T)):
        s += progress(t, SPEAK_T[i] - HANDOFF, HANDOFF)
    return s


def together_k(t: float) -> float:
    return progress(t, BEATS["together"] - 0.05, 0.45)


def speaking(t: float, i: int) -> float:
    if i >= len(SPEAK_T):
        return 0.0
    return fade(t, SPEAK_T[i], SPEAK_END[i], 0.15)


def spotlight(img: Image.Image, t: float) -> None:
    s, kt = spot_index(t), together_k(t)
    a = progress(t, 0.0, 0.3)
    cx = COL_CX[0] + s * COL_W
    half = COL_W / 2 - 14
    x0 = lerp(cx - half, COL_CX[0] - half, kt)
    x1 = lerp(cx + half, COL_CX[-1] + half, kt)
    y0, y1 = SPOT
    pad = 6
    lay = Image.new("RGBA", (S(x1 - x0 + 2 * pad), S(y1 - y0 + 2 * pad)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    box = (pad, pad, pad + x1 - x0, pad + y1 - y0)
    d.rounded_rectangle(SB(box), S(22), fill=(*NAVY_3, int(150 * a)), outline=(*CYAN, int(200 * a)), width=S(2))
    img.alpha_composite(lay.resize((lay.width // SS, lay.height // SS), Image.LANCZOS), dest=(int(x0 - pad), int(y0 - pad)))


def voice_bars(img: Image.Image, t: float, i: int, k: float) -> None:
    """Three small cyan level bars beside the speaker's head (smooth sine motion, no jitter)."""
    if k <= 0.01:
        return
    h = STAGE_BOT - STAGE_TOP
    x = COL_CX[i] + 0.17 * h + 20
    cy = head_top(i) + 0.18 * h
    lay = Image.new("RGBA", (S(44), S(60)), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for j in range(3):
        amp = 0.5 + 0.5 * math.sin(2 * math.pi * (1.7 + 0.35 * j) * t + 1.9 * j)
        bh = (15 + 23 * amp) * (0.4 + 0.6 * k)
        bx = 4 + j * 13
        d.rounded_rectangle(SB((bx, 30 - bh / 2, bx + 7, 30 + bh / 2)), S(3.5), fill=(*CYAN, int(255 * k)))
    img.alpha_composite(lay.resize((44, 60), Image.LANCZOS), dest=(int(x), int(cy - 30)))


# ---------- frames ----------


def frame(t: float) -> Image.Image:
    img = BASE.copy()
    s, kt = spot_index(t), together_k(t)
    spotlight(img, t)
    put(img, STAGE, 1.0)
    for i in range(len(COLUMNS)):
        lit = max(0.0, 1 - abs(s - i)) * progress(t, 0.0, 0.3) if i < len(SPEAK_T) else 0.0
        lit = max(lit, kt)
        done = clamp(s - i) if i < len(SPEAK_T) else 0.0
        put(img, LIT[i], lit)
        put(img, TILES_LIT[i], lit)
        put(img, Q_DONE[i], done * (1 - lit))
        put(img, Q_ACTIVE[i], lit)
        voice_bars(img, t, i, speaking(t, i) * max(0.0, 1 - abs(s - i)))
    put(img, TOG_LIT, kt)
    return overlay_at(t, img)


def overlay_frame(t: float) -> Image.Image:
    return overlay_at(t)


def overlay_check(t: float) -> Image.Image:
    """The overlay alone on a bright, footage-like stand-in background (worst case for white text)."""
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    xs = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    top, bot = np.array([214, 210, 200], np.float32), np.array([150, 158, 170], np.float32)
    rgb = top * (1 - ys) + bot * ys + 18 * np.sin(xs * 9.0)
    bg = Image.fromarray(np.dstack([np.clip(rgb, 0, 255).astype(np.uint8), np.full((H, W, 1), 255, np.uint8)]), "RGBA")
    return overlay_at(t, bg)


STILLS = {  # name: time (s)
    "next": 2.2,                 # M5 speaking, the "Next" line up
    "ai_recommends": 5.2,        # M3, first tagline half centred
    "person_decides": 7.0,       # M2, full tagline
    "m1_phone": 9.0,             # M1, tagline holds
    "together": DURATION - 1 / FPS,
}

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--stills-only", action="store_true")
    args = ap.parse_args()
    for name, tt in STILLS.items():
        print("still", still(f"{SHOT}_{name}", frame(tt)))
    print("still", still(f"{SHOT}_overlay_check", overlay_check(7.0)))
    if not args.stills_only:
        print("video", render(SHOT, DURATION, frame))
        print("overlay", render_overlay(f"{SHOT}_text", DURATION, overlay_frame))
