"""S20 · End card (4:20.5-4:26.5, 6.0 s, no voice). Never shorten below 6 s (section 6, never-cut list).

Storyboard: docs/video/script.md section 3, row S20 (visual and on-screen text), section 1 "Team roles" (which
member carries which STEMB letter), section 5A item 1 (fill names, school, supervisor and the grid before
submitting) and 5E (the optional AI-assistance line); docs/video/shotlist.json, entry S20.

Data sources (nothing is retyped):
  - docs/video/shotlist.json: the shot duration (end_s - start_s), and the repository line (checked equal to
    the storyboard's).
  - docs/video/script.md, section 3, S20 row, "on-screen text" cell: every line on the card, verbatim:
      1. "CrowdPulse Macau · [SCHOOL] · Supervisor: [NAME] · Imperial College London Hackathon ... Responsible AI"
         -> the wordmark (first item) plus two identity lines (the other items, split at their " · ");
      2. "Code and evidence: github.com/Yh1sam/crowdpulse-macau" -> the repository line, directly under the
         wordmark, larger than the credits, on screen at full strength for the whole 6 s (frame 0 to the end);
         its address is checked against this checkout's origin remote (git remote get-url origin);
      3. "Who built what: [TEAM TO FILL]" -> the grid header;
      4. the evidence legend line, each "Term = meaning" item with a swatch in its badge colour;
      5. the credits line, one item per " · ", set in two columns;
      6. "[optional: AI-assistance line per the organisers' reply]".
    When the team fills a bracketed placeholder in the storyboard, re-running this script picks it up.
  - docs/video/script.md, section 1, "Team roles" table: [MEMBER n] -> STEMB letter for the grid columns.
  - shared/zones.json (via style.project): the 7-zone mark next to the wordmark, as in S05.

Bracketed placeholders ([SCHOOL], [NAME], [TEAM TO FILL], [MEMBER n], [optional: ...]) are drawn in amber dashed
boxes so nobody can ship them by mistake. No badge, chapter card, footer, caption or lower-third (none in the
storyboard for S20; the caption band y 900-995 stays clear anyway).

Output: video/build/mg/S20.mp4 and stills in video/build/mg/stills/S20_*.png.
Run: .venv/bin/python video/mg/S20.py [--stills-only]
"""
from __future__ import annotations

import json
import math
import re
import subprocess
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F403

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S20"
_entry = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_entry["end_s"] - _entry["start_s"], 3)  # 6.0 s

# Times in seconds from the shot start. S20 has no voice: the card builds in about 1.3 s after the cut from
# S19 and then holds still so the grid and credits can be read.
# re-key to the real voice take (only if S19's last line moves the cut)
BEATS = {
    "repo": 0.0,        # the repository line is on screen, at full strength, from the first frame to the last
    "mark": 0.0,        # cut from S19's "all together": the zone mark pops in, top to bottom
    "word": 0.12,       # "CrowdPulse Macau" wipes in from the mark
    "identity": 0.30,   # [SCHOOL] · Supervisor: [NAME] / event and challenge line
    "grid": 0.45,       # who-built-what panel; the S T E M B columns follow 0.06 s apart
    "legend": 0.80,     # evidence legend line
    "credits": 0.92,    # credits, two columns (left, then right with the AI-assistance placeholder)
    "settled": 1.45,    # everything readable; hold to the end (the last block, the right credits column, lands here)
}
IN_DUR = 0.45           # fade-and-rise of each block (s)
RISE = 14               # px
# the held frame must not replace a block that is still fading in (that would be a small step at "settled")
assert BEATS["settled"] >= max(BEATS["credits"] + 0.08, BEATS["legend"], BEATS["grid"] + 0.08 + 4 * 0.06,
                               BEATS["identity"] + 0.06) + IN_DUR - 1e-9, BEATS

SS = 2                  # supersampling for shapes
PINK = (232, 121, 249)  # stairs links, as in style.draw_zone_graph
LINK = (112, 128, 156)  # zone links, as in S05's mark
PH = re.compile(r"(\[[^\]]+\])")  # a bracketed placeholder

# ---------- text from the storyboard ----------

SCRIPT = (ROOT / "docs" / "video" / "script.md").read_text()


def storyboard_cell(shot: str, col: int) -> str:
    """Cell `col` of the shot's row in the section 3 storyboard (the first table row that starts with the shot id)."""
    row = next(l for l in SCRIPT.splitlines() if l.startswith(f"| {shot} |"))
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    assert len(cells) == 7, (shot, len(cells))
    return cells[col]


ON_SCREEN = [p.strip().strip('"') for p in storyboard_cell(SHOT, 5).split("<br>")]
assert len(ON_SCREEN) == 6, ON_SCREEN
_ident = [p.strip() for p in ON_SCREEN[0].split(" · ")]
WORDMARK = _ident[0]
assert WORDMARK == "CrowdPulse Macau", WORDMARK
TITLE_A, TITLE_B = WORDMARK.split(" ", 1)
ID_LINE_1 = " · ".join(_ident[1:3])          # [SCHOOL] · Supervisor: [NAME]
ID_LINE_2 = " · ".join(_ident[3:])           # Imperial College London Hackathon ... · Challenge 2(c) Responsible AI
assert ID_LINE_1.startswith("[SCHOOL]") or "Supervisor" in ID_LINE_1, ID_LINE_1
REPO_LINE = ON_SCREEN[1]                     # Code and evidence: github.com/Yh1sam/crowdpulse-macau
GRID_HEAD = ON_SCREEN[2]                     # Who built what: [TEAM TO FILL]
LEGEND = [p.strip() for p in ON_SCREEN[3].split(" · ")]
assert ON_SCREEN[4].startswith("Credits: "), ON_SCREEN[4]
CREDITS = [p.strip() for p in ON_SCREEN[4][len("Credits: "):].split(" · ")]
assert CREDITS[-1] == "fonts: Geist, Noto Sans TC (SIL OFL)", CREDITS[-1]
AI_LINE = ON_SCREEN[5]

# the repository line: the same words in the shotlist, and the address is this checkout's origin remote
assert REPO_LINE in [p.strip() for p in _entry["on_screen_text"].split(" | ")], (REPO_LINE, _entry["on_screen_text"])
REPO_LABEL, REPO_URL = REPO_LINE.split(": ", 1)
REPO_LABEL += ":"
assert REPO_LABEL == "Code and evidence:", REPO_LABEL
_origin = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"], capture_output=True, text=True,
                         check=True).stdout.strip()
assert re.sub(r"^(https://|git@)|\.git$", "", _origin).replace("github.com:", "github.com/") == REPO_URL, (_origin, REPO_URL)
assert "for the full 6 s" in storyboard_cell(SHOT, 6) and "full 6 s" in _entry["notes"]   # shown frame 0 to the end

# [MEMBER n] -> STEMB letter (section 1, Team roles); columns follow the S T E M B strip order
_roles = {m.group(2): m.group(1) for m in re.finditer(
    r"^\| (\[MEMBER \d\])(?: \(optional\))? \| \*\*([STEMB])\*\* ", SCRIPT, re.M)}
assert sorted(_roles) == sorted(l for l, _ in STEMB), _roles
COLUMNS = [(letter, word, _roles[letter]) for letter, word in STEMB]

LEGEND_BADGE = {"simulated": "SIMULATED", "real": "REAL DATA", "model check": "MODEL CHECK",
                "pending": "PENDING", "corrected": "CORRECTED"}

# ---------- layout ----------

LOCK_Y = 120                 # centre line of the mark + wordmark lockup
WORD_SIZE, MARK_H = 88, 100
REPO_Y = 226                 # centre line of the repository line (directly under the wordmark)
REPO_LABEL_SIZE, REPO_SIZE = 30, 38   # both larger than the credits (CRED_SIZE)
ID1_Y, ID2_Y = 294, 342      # centre lines of the two identity lines
GRID = (60, 372, 1860, 624)  # who-built-what panel
LEGEND_Y = 662               # centre line of the evidence legend
CRED_Y = 700                 # top of the credits block
CRED_LABEL_X, CRED_COLS = 60, ((214, 1010), (1066, 1860))
CRED_SIZE, CRED_PITCH, CRED_GAP = 22, 29, 9
assert min(REPO_LABEL_SIZE, REPO_SIZE) > CRED_SIZE


# ---------- helpers (own) ----------

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


class Sprite:
    """A cropped RGBA image and where it sits on the frame."""

    def __init__(self, img: Image.Image, x: float, y: float):
        self.img, self.x, self.y = img, int(round(x)), int(round(y))

    @property
    def right(self) -> int:
        return self.x + self.img.width

    @property
    def bottom(self) -> int:
        return self.y + self.img.height


def sprite_from(draw_fn) -> Sprite:
    """Runs draw_fn(img, shapes) on a full transparent frame (+ a 2x shape layer composited first), crops it."""
    shapes = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    img = transparent()
    draw_fn(img, ImageDraw.Draw(shapes))
    base = shapes.resize((W, H), Image.LANCZOS)
    base.alpha_composite(img)
    bbox = base.getbbox()
    return Sprite(base.crop(bbox), bbox[0], bbox[1])


def alpha_mul(img: Image.Image, k: float) -> Image.Image:
    if k >= 0.999:
        return img
    a = np.array(img)
    a[..., 3] = (a[..., 3].astype(np.float32) * clamp(k)).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def put(dst: Image.Image, sp: Sprite, k: float, dy: float = 0.0) -> None:
    if k <= 0:
        return
    dst.alpha_composite(alpha_mul(sp.img, k), dest=(sp.x, sp.y + int(round(dy))))


def S(v: float) -> int:
    return int(round(v * SS))


CHIP_GAP = 6  # extra air between a placeholder box and the text next to it (px)


def rich_width(text: str, size: int, weight: int, pad: int) -> float:
    w_ = 0.0
    parts = [p for p in PH.split(text) if p]
    for i, part in enumerate(parts):
        ph = bool(PH.fullmatch(part))
        w_ += text_font(part, size, max(weight, 600) if ph else weight).getlength(part) + (2 * pad if ph else 0)
        if ph:
            w_ += CHIP_GAP * ((i > 0) + (i < len(parts) - 1))
    return w_


def draw_rich(img: Image.Image, d2, x: float, cy: float, text: str, size: int, weight: int = 500, fill=INK,
              pad: int = 12, chip_h: float | None = None, first_fill=None) -> float:
    """One line of text in which every [bracketed placeholder] sits in an amber dashed box.
    (x, cy): left edge and vertical centre. first_fill colours the text before the first ':' (e.g. "Next:").
    Returns the right edge."""
    chip_h = chip_h or size * 1.62
    parts = [p for p in PH.split(text) if p]
    for i, part in enumerate(parts):
        f = text_font(part, size, weight)
        if PH.fullmatch(part):
            x += CHIP_GAP if i > 0 else 0
            f = text_font(part, size, max(weight, 600))       # placeholders are set bolder: measure them that way
            wpart = f.getlength(part) + 2 * pad
            box = (x, cy - chip_h / 2, x + wpart, cy + chip_h / 2)
            d2.rounded_rectangle(tuple(S(v) for v in box), S(8), fill=(*NAVY, 235))
            dashed_rrect(d2, tuple(S(v) for v in box), S(8), (*WARNING, 255), S(2.2))
            draw_text(img, (x + pad, cy), part, size, max(weight, 600), WARNING, anchor="lm")
            x += wpart + (CHIP_GAP if i < len(parts) - 1 else 0)
        else:
            if first_fill and ":" in part:
                head, tail = part.split(":", 1)
                head += ":"
                draw_text(img, (x, cy), head, size, weight, first_fill, anchor="lm")
                x += f.getlength(head)
                part = tail
            draw_text(img, (x, cy), part, size, weight, fill, anchor="lm")
            x += f.getlength(part)
    return x


# ---------- the mark (7-zone graph, as in S05) ----------

def _graph_extent() -> tuple[float, float]:
    proj = project((0, 0, 100000, MARK_H))
    pts = [proj(z["lat"], z["lon"]) for z in zone_graph()["zones"]]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys)


def lockup() -> dict:
    fa, fb = text_font(TITLE_A, WORD_SIZE, 700), text_font(TITLE_B, WORD_SIZE, 600)
    wa, wb = fa.getlength(TITLE_A + " "), fb.getlength(TITLE_B)
    mark_w, _ = _graph_extent()
    gap = 44
    x0 = (W - (mark_w + gap + wa + wb)) / 2
    box = (x0, LOCK_Y - MARK_H / 2, x0 + mark_w, LOCK_Y + MARK_H / 2)
    proj = project(box)
    zones = zone_graph()["zones"]
    return dict(box=box, tx=x0 + mark_w + gap, wa=wa, end=x0 + mark_w + gap + wa + wb,
                pos={z["id"]: proj(z["lat"], z["lon"]) for z in zones})


LOCK = lockup()
ZONE_ORDER = sorted(LOCK["pos"], key=lambda k: LOCK["pos"][k][1])  # pop order: top (Ruins) to bottom


def mark_sprite(t: float | None) -> Sprite:
    """The zone mark at time t (None = settled). Nodes pop in top to bottom, links grow after them."""
    x0, y0, x1, y1 = LOCK["box"]
    pad = 24
    ox, oy = x0 - pad, y0 - pad
    layer = Image.new("RGBA", (S(x1 - x0 + 2 * pad), S(y1 - y0 + 2 * pad)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pos = LOCK["pos"]

    def node_k(zid):
        if t is None:
            return 1.0
        return progress(t, BEATS["mark"] + ZONE_ORDER.index(zid) * 0.035, 0.32)

    edge_k = 1.0 if t is None else progress(t, BEATS["mark"] + 0.10, 0.40)
    for e in zone_graph()["edges"]:
        a = min(node_k(e["from"]), node_k(e["to"])) * edge_k
        if a <= 0:
            continue
        p0 = pos[e["from"]]
        p1 = lerp(p0, pos[e["to"]], edge_k)
        P0, P1 = (S(p0[0] - ox), S(p0[1] - oy)), (S(p1[0] - ox), S(p1[1] - oy))
        if e.get("has_stairs"):
            n = max(2, int(math.hypot(P1[0] - P0[0], P1[1] - P0[1]) // S(6)))
            for i in range(0, n, 2):
                q0 = lerp(P0, P1, i / n)
                q1 = lerp(P0, P1, min(1.0, (i + 1) / n))
                d.line([q0, q1], fill=(*PINK, int(255 * a)), width=S(3.6))
        else:
            d.line([P0, P1], fill=(*LINK, int(255 * a)), width=S(4.2))
    for zid in ZONE_ORDER:
        k = node_k(zid)
        if k <= 0:
            continue
        r = 9.5 * (0.35 + 0.65 * k)
        cx, cy = S(pos[zid][0] - ox), S(pos[zid][1] - oy)
        d.ellipse((cx - S(r), cy - S(r), cx + S(r), cy + S(r)), fill=(*CYAN, int(255 * k)))
    return Sprite(layer.resize((layer.width // SS, layer.height // SS), Image.LANCZOS), ox, oy)


MARK_FINAL = mark_sprite(None)


def _wordmark(img, d2):
    draw_text(img, (LOCK["tx"], LOCK_Y), TITLE_A, WORD_SIZE, 700, INK, anchor="lm")
    draw_text(img, (LOCK["tx"] + LOCK["wa"], LOCK_Y), TITLE_B, WORD_SIZE, 600, CYAN, anchor="lm")


WORD = sprite_from(_wordmark)


# ---------- the repository line (directly under the wordmark; full strength from frame 0) ----------

REPO_GAP = 14                # between the label and the address (px)
REPO_PAD_X, REPO_H = 30, 56  # the pill around it


def _repo(img, d2):
    fl, fu = text_font(REPO_LABEL, REPO_LABEL_SIZE, 500), text_font(REPO_URL, REPO_SIZE, 650)
    wl, wu = fl.getlength(REPO_LABEL), fu.getlength(REPO_URL)
    x0 = (W - (wl + REPO_GAP + wu)) / 2
    box = (x0 - REPO_PAD_X, REPO_Y - REPO_H / 2, x0 + wl + REPO_GAP + wu + REPO_PAD_X, REPO_Y + REPO_H / 2)
    d2.rounded_rectangle(tuple(S(v) for v in box), S(REPO_H / 2), fill=(*NAVY_2, 255), outline=(*NAVY_3, 255),
                         width=S(2))
    draw_text(img, (x0, REPO_Y), REPO_LABEL, REPO_LABEL_SIZE, 500, INK_2, anchor="lm")
    draw_text(img, (x0 + wl + REPO_GAP, REPO_Y), REPO_URL, REPO_SIZE, 650, CYAN, anchor="lm")


REPO = sprite_from(_repo)


def wipe(dst: Image.Image, sp: Sprite, k: float, feather: float = 90.0) -> None:
    """Left-to-right reveal with a soft leading edge (k 0..1)."""
    if k <= 0:
        return
    if k >= 1:
        dst.alpha_composite(sp.img, dest=(sp.x, sp.y))
        return
    reveal = lerp(sp.x - feather, sp.right + feather, k)
    a = np.array(sp.img)
    cols = sp.x + np.arange(sp.img.width, dtype=np.float32)
    m = np.clip((reveal - cols) / feather, 0, 1)
    a[..., 3] = (a[..., 3].astype(np.float32) * m[None, :]).astype(np.uint8)
    dst.alpha_composite(Image.fromarray(a, "RGBA"), dest=(sp.x, sp.y))


# ---------- identity lines ----------

def _centred_rich(cy, text, size, weight, fill):
    def fn(img, d2):
        w_ = rich_width(text, size, weight, 12)
        draw_rich(img, d2, (W - w_) / 2, cy, text, size, weight, fill)
    return fn


ID1 = sprite_from(_centred_rich(ID1_Y, ID_LINE_1, 30, 600, INK))
ID2 = sprite_from(_centred_rich(ID2_Y, ID_LINE_2, 26, 500, INK_2))

# ---------- who-built-what grid (the full S T E M B strip heads its columns) ----------

COL_GAP = 22
COL_W = (GRID[2] - GRID[0] - 2 * 32 - 4 * COL_GAP) / 5
COL_X = [GRID[0] + 32 + i * (COL_W + COL_GAP) for i in range(5)]
TILE = 56
HEAD_Y = GRID[1] + 40                 # centre line of the grid header
TILE_Y = GRID[1] + 76
CHIP_Y = TILE_Y + TILE + 16           # top of the member chip
CELL = (CHIP_Y + 48, GRID[3] - 20)    # contribution slot (top, bottom)
assert CELL[1] - CELL[0] >= 36, CELL  # room for one line of the team's text


def _grid_panel(img, d2):
    d2.rounded_rectangle(tuple(S(v) for v in GRID), S(22), fill=(*NAVY_2, 255))
    draw_rich(img, d2, GRID[0] + 32, HEAD_Y, GRID_HEAD, 30, 700, INK)


GRID_PANEL = sprite_from(_grid_panel)


def _grid_col(i):
    letter, word, member = COLUMNS[i]
    x = COL_X[i]

    def fn(img, d2):
        d2.rounded_rectangle(tuple(S(v) for v in (x, TILE_Y, x + TILE, TILE_Y + TILE)), S(14), fill=(*CYAN, 255))
        draw_text(img, (x + TILE / 2, TILE_Y + TILE / 2), letter, 33, 800, NAVY, anchor="mm")
        draw_text(img, (x + TILE + 18, TILE_Y + TILE / 2), word, 30, 600, INK, anchor="lm")
        draw_rich(img, d2, x, CHIP_Y + 20, member, 24, 700, INK, pad=12, chip_h=40)
        cell = (x, CELL[0], x + COL_W, CELL[1])
        dashed_rrect(d2, tuple(S(v) for v in cell), S(10), (*WARNING, 120), S(1.8), S(7), S(6))
    return fn


GRID_COLS = [sprite_from(_grid_col(i)) for i in range(5)]

# ---------- evidence legend line ----------


def _legend(img, d2):
    size, sw_w, sw_h, gap = 24, 34, 18, 12
    sep = "  ·  "
    sep_w = text_font(sep, size, 500).getlength(sep)
    widths = [sw_w + gap + text_font(it, size, 500).getlength(it) for it in LEGEND]
    x = (W - (sum(widths) + sep_w * (len(LEGEND) - 1))) / 2
    for i, it in enumerate(LEGEND):
        kind = LEGEND_BADGE[it.split(" = ")[0].strip().lower()]
        box = tuple(S(v) for v in (x, LEGEND_Y - sw_h / 2, x + sw_w, LEGEND_Y + sw_h / 2))
        if kind == "PENDING":
            d2.rounded_rectangle(box, S(sw_h / 2), fill=(*NAVY_2, 255))
            dashed_rrect(d2, box, S(sw_h / 2), (*GREY, 255), S(2), S(5), S(4))
        elif kind == "CORRECTED":
            d2.rounded_rectangle(box, S(sw_h / 2), fill=(*NAVY, 255), outline=(*INK, 255), width=S(2))
        else:
            d2.rounded_rectangle(box, S(sw_h / 2), fill=(*BADGES[kind], 255))
        term, meaning = it.split(" = ", 1)
        tx = x + sw_w + gap
        draw_text(img, (tx, LEGEND_Y), term, size, 700, INK, anchor="lm")
        tx += text_font(term, size, 700).getlength(term)
        draw_text(img, (tx, LEGEND_Y), " = " + meaning, size, 500, INK_2, anchor="lm")
        x += widths[i] + (text_font(term, size, 700).getlength(term) - text_font(term, size, 500).getlength(term))
        if i < len(LEGEND) - 1:
            draw_text(img, (x, LEGEND_Y), sep, size, 500, INK_3, anchor="lm")
            x += sep_w


LEGEND_S = sprite_from(_legend)

# ---------- credits (two columns) and the AI-assistance placeholder ----------


def _split_columns(items: list[str]) -> tuple[list[str], list[str]]:
    """Keeps the storyboard order; puts the break where the two columns are closest in height."""
    def lines(it, width):
        return len(wrap(it, CRED_SIZE, 500, width))
    best = None
    for k in range(1, len(items)):
        h1 = sum(lines(it, CRED_COLS[0][1] - CRED_COLS[0][0]) for it in items[:k])
        h2 = sum(lines(it, CRED_COLS[1][1] - CRED_COLS[1][0]) for it in items[k:]) + 1.4  # + the AI line
        score = max(h1, h2)
        if best is None or score < best[0]:
            best = (score, k)
    k = best[1]
    return items[:k], items[k:]


CRED_L, CRED_R = _split_columns(CREDITS)


def _credit_col(items, col, with_ai):
    x0, x1 = col

    def fn(img, d2):
        y = CRED_Y
        for it in items:
            d2.ellipse(tuple(S(v) for v in (x0, y + 11, x0 + 7, y + 18)), fill=(*INK_3, 255))
            h = draw_text(img, (x0 + 20, y), it, CRED_SIZE, 500, INK_2, max_width=int(x1 - x0 - 20),
                          line_gap=CRED_PITCH / CRED_SIZE)
            y += h + CRED_GAP
        if with_ai:
            y += 6
            draw_rich(img, d2, x0, y + 17, AI_LINE, CRED_SIZE, 500, INK_2, pad=12, chip_h=38)
    return fn


def _credit_label(img, d2):
    draw_text(img, (CRED_LABEL_X, CRED_Y - 1), "Credits", 24, 700, INK)


CRED_LABEL = sprite_from(_credit_label)
CRED_COL_L = sprite_from(_credit_col(CRED_L, CRED_COLS[0], False))
CRED_COL_R = sprite_from(_credit_col(CRED_R, CRED_COLS[1], True))

# layout checks: nothing in the caption band, nothing off-frame, columns inside their slots
for _sp in [REPO, ID1, ID2, GRID_PANEL, *GRID_COLS, LEGEND_S, CRED_LABEL, CRED_COL_L, CRED_COL_R, WORD, MARK_FINAL]:
    assert _sp.x >= 56 and _sp.right <= W - 56 and _sp.y >= 40 and _sp.bottom <= 898, (_sp.x, _sp.y, _sp.right, _sp.bottom)


def _ink_rows(sp: Sprite) -> tuple[int, int]:
    """Top and bottom frame rows of a sprite's visible pixels."""
    rows = np.nonzero(np.array(sp.img)[..., 3].max(axis=1) > 8)[0]
    return sp.y + int(rows[0]), sp.y + int(rows[-1]) + 1


# vertical order with air between blocks: wordmark and mark, repository line, identity lines, grid, legend, credits
_stack = [("lockup", min(_ink_rows(WORD)[0], _ink_rows(MARK_FINAL)[0]), max(_ink_rows(WORD)[1], _ink_rows(MARK_FINAL)[1])),
          ("repo", *_ink_rows(REPO)), ("id1", *_ink_rows(ID1)), ("id2", *_ink_rows(ID2)), ("grid", *_ink_rows(GRID_PANEL)),
          ("legend", *_ink_rows(LEGEND_S)), ("credits", _ink_rows(CRED_LABEL)[0],
                                             max(_ink_rows(CRED_COL_L)[1], _ink_rows(CRED_COL_R)[1]))]
for (_a, _, _a1), (_b, _b0, _) in zip(_stack, _stack[1:]):
    assert _b0 - _a1 >= 10, (_a, _a1, _b, _b0)

# ---------- frames ----------

BG = canvas(NAVY)
SETTLED = None


def compose(t: float) -> Image.Image:
    img = BG.copy()
    put(img, REPO, 1.0 if t >= BEATS["repo"] else 0.0)   # no fade: readable on every frame of the shot
    settled_mark = t >= BEATS["mark"] + len(ZONE_ORDER) * 0.035 + 0.5
    put(img, MARK_FINAL if settled_mark else mark_sprite(t), 1.0)
    wipe(img, WORD, progress(t, BEATS["word"], 0.6))

    def block(sp, start):
        k = progress(t, start, IN_DUR)
        put(img, sp, k, (1 - k) * RISE)

    block(ID1, BEATS["identity"])
    block(ID2, BEATS["identity"] + 0.06)
    block(GRID_PANEL, BEATS["grid"])
    for i, sp in enumerate(GRID_COLS):
        block(sp, BEATS["grid"] + 0.08 + i * 0.06)
    block(LEGEND_S, BEATS["legend"])
    block(CRED_LABEL, BEATS["credits"])
    block(CRED_COL_L, BEATS["credits"])
    block(CRED_COL_R, BEATS["credits"] + 0.08)
    return img


def frame(t: float) -> Image.Image:
    global SETTLED
    if t >= BEATS["settled"]:
        if SETTLED is None:
            SETTLED = compose(DURATION)
        return SETTLED.copy()
    return compose(t)


STILLS = {  # name: time (s)
    "first": 0.0,
    "build": 0.42,
    "grid_in": 0.80,
    "settled": 1.6,
    "hold_end": DURATION - 1 / FPS,
}

if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--stills-only", action="store_true")
    args = ap.parse_args()
    for name, tt in STILLS.items():
        print("still", still(f"{SHOT}_{name}", frame(tt)))
    if not args.stills_only:
        print("video", render(SHOT, DURATION, frame))
