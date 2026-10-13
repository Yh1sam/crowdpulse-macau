"""Shot S12 (2:08.0-2:18.0), motion-graphics part only: the public frame-timing correction.

0-8 s of the shot. The last 2 s (the README.md "Correction" paragraph, rendered with pandoc and
recorded with video/capture.py) are a capture added at assembly, so they are not drawn here.

Left half:  a [TEAM FOOTAGE] slate standing in for [MEMBER 1] and [MEMBER 2] at a laptop that
            shows the mosaicked S11 stills (team camera, not filmed yet; swap at assembly).
Right half: from about 1.5 s, the timing inset in three quick beats:
            1. a hand-count label at time t;
            2. the frame actually compared (sampled 2.4 s after the label) in red, then the
               correct frame aligned in green;
            3. the dashed far-kerb line drops in (no extra tag) and the near field is recounted.
            Frames are abstract thumbnails on a 10 fps film-strip timeline, never the raw clip.
On-screen text (docs/video/script.md section 3, S12 row): badge CORRECTED; the overlay under
the inset; footer "README.md · Correction". No chapter card. Evidence legend strip (S10-S16).

Data sources:
- docs/video/shotlist.json: S12 start_s / end_s (DURATION = shot length minus the 2 s README insert).
- experiments/datasets/video/ground_truth.csv: the hand-counted frames sit at t_sec = 2.4 + 5k s.
  experiments/video_eval.py records that v1 labelled them 0, 5, 10 s, so the offset between the
  label and the frame ffmpeg actually sampled is t_sec mod the sampling interval (2.4 s); the clip
  frame rate (film-strip cells) is frame_index / t_sec.
- experiments/results/video/summary.json: kerb_y, the dashed near-field line (fraction of frame height).
- README.md "Correction" paragraph and docs/hackathon-notes.md (the claim; script.md section 4, S12).

Outputs: video/build/mg/S12_mg.mp4 (slate on navy), video/build/overlays/S12_mg.mov (alpha: inset,
overlay, badge, legend and footer only, the footer on a soft navy backing so it reads over the
footage; for compositing over the real take), and stills.
Run: .venv/bin/python video/mg/S12.py [--stills-only]
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys

sys.path.insert(0, "/Users/yhsam/Documents/Imperial_hackathon/video/mg")
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw  # noqa: E402

SHOT = "S12"
NAME = "S12_mg"

# ---------- timing ----------
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
README_INSERT = 2.0                                    # 8-10 s: README capture, added at assembly
DURATION = (_shot["end_s"] - _shot["start_s"]) - README_INSERT   # 8.0 s

# Times in seconds from the shot start, keyed to the narration at about 140 wpm (0.43 s a word):
# [M1] "Our first version of this test had a frame-timing bug." (about 0-4.3 s)
# [M2] "It was caught, fixed, and we published the correction." (about 4.6-8.5 s)
# re-key to the real voice take
BEATS = {
    "m1_start": 0.0,      # "Our ..."                       M1 speaks (slate indicator)
    "inset_in": 1.5,      # "... of this test"              inset slides in, film strip draws
    "label_t": 2.0,       # "test had"                      beat 1: hand-count label at t
    "red_frame": 3.3,     # "frame-timing bug"              beat 2a: frame actually compared, red
    "m1_end": 4.3,
    "m2_start": 4.6,      # "It was ..."                    M2 speaks (slate indicator)
    "green_frame": 5.5,   # "caught, fixed"                 beat 2b: correct frame aligned, green
    "kerb_line": 6.4,     # "and we published"              beat 3: dashed far-kerb line drops in
    "end": DURATION,      # cut to the README insert on M2's word "correction"
}

# ---------- data ----------
_gt = list(csv.DictReader((ROOT / "experiments" / "datasets" / "video" / "ground_truth.csv").open()))
_t0, _t1 = float(_gt[0]["t_sec"]), float(_gt[1]["t_sec"])
INTERVAL = _t1 - _t0                                   # sampling interval between hand-counted frames
OFFSET = round(_t0 % INTERVAL, 1)                      # v1 labels 0, 5, 10 s vs frames at 2.4, 7.4, ... s
CLIP_FPS = round(int(_gt[0]["frame_index"]) / _t0)     # the clip's frame rate (10 fps)
KERB_Y = json.loads((ROOT / "experiments" / "results" / "video" / "summary.json").read_text())["kerb_y"]
OFF = f"{OFFSET:g}"
assert OFF == "2.4", OFF                               # the storyboard's "2.4 s"

OVERLAY_TEXT = "v1 compared hand counts with frames 2.4 s off → fixed; near field redefined, recounted"
FOOTER = "README.md · Correction"
SLATE_TITLE = "[TEAM FOOTAGE]"
SLATE_TEXT = "[MEMBER 1] and [MEMBER 2] at a laptop showing the mosaicked S11 stills; both on camera for both lines"

RED_T = (255, 138, 141)      # light tints of CRITICAL / SAFE for text on navy
GREEN_T = (118, 216, 134)
RED_DIM = (96, 38, 48)

# ---------- layout ----------
SLATE = (60, 140, 920, 780)                  # left half (keeps the lower-third area y 795-895 clear)
INSET_X, INSET_Y, INSET_W, INSET_H = 980, 140, 880, 500
PLATE = (980, 656, 1860, 780)                # overlay text under the inset
PAD = 30
FW, FH = 392, 220                            # thumbnail size (16:9)
C_T = PAD + FW // 2                          # x of time t (inset-local)
C_OFF = INSET_W - PAD - FW // 2              # x of time t + OFFSET
PX_PER_S = (C_OFF - C_T) / OFFSET
CHIP_Y0, CHIP_Y1 = 58, 106
FY = 146                                     # thumbnails top
SY, SH = 404, 32                             # film strip top and height
SS = 2                                       # supersampling for static sprites


def fadeimg(im: Image.Image, a: float) -> Image.Image:
    if a >= 1:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


def over(img: Image.Image, fn, alpha: float = 1.0) -> None:
    """Draw with fn(ImageDraw) on a transparent layer and composite it with opacity."""
    if alpha <= 0:
        return
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    fn(ImageDraw.Draw(layer))
    img.alpha_composite(fadeimg(layer, alpha))


def down(im: Image.Image, size) -> Image.Image:
    return im.resize(size, Image.LANCZOS)


def path_points(pts, step: float = 1.0):
    """Densely sampled points along a polyline, with cumulative length."""
    out = [(pts[0][0], pts[0][1], 0.0)]
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        seg = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(seg / step))
        for i in range(1, n + 1):
            out.append((x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n, acc + seg * i / n))
        acc += seg
    return out


def dashed_path(d: ImageDraw.ImageDraw, pts, fill, width: int, dash: float, gap: float, upto: float = 1.0) -> None:
    sp = path_points(pts)
    total = sp[-1][2]
    limit = total * upto
    run = []
    for x, y, s in sp:
        if s > limit:
            break
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


def check_mark(d, cx, cy, s, fill, width):
    d.line([(cx - 0.42 * s, cy + 0.02 * s), (cx - 0.12 * s, cy + 0.32 * s), (cx + 0.45 * s, cy - 0.30 * s)], fill=fill, width=width, joint="curve")


def cross_mark(d, cx, cy, s, fill, width):
    k = 0.32 * s
    d.line([(cx - k, cy - k), (cx + k, cy + k)], fill=fill, width=width)
    d.line([(cx - k, cy + k), (cx + k, cy - k)], fill=fill, width=width)


def mark_badge(colour, kind: str, r: int = 21) -> Image.Image:
    q = 4
    im = Image.new("RGBA", (2 * r * q + 8 * q, 2 * r * q + 8 * q), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = im.width / 2
    d.ellipse((c - r * q - 3 * q, c - r * q - 3 * q, c + r * q + 3 * q, c + r * q + 3 * q), fill=(*NAVY_2, 255))
    d.ellipse((c - r * q, c - r * q, c + r * q, c + r * q), fill=(*colour, 255))
    (check_mark if kind == "check" else cross_mark)(d, c, c, 1.25 * r * q, (*INK, 255), int(4.2 * q))
    return down(im, (im.width // q, im.height // q))


# ---------- the abstract street thumbnails ----------
BUILD_BG, BLOCK, WINDOW = (24, 34, 56), (33, 47, 74), (52, 70, 104)
WALK, ROAD, STRIPE = (52, 68, 98), (35, 49, 77), (58, 75, 106)
PERSON, PERSON_FAR, PERSON_HI = (150, 166, 192), (104, 120, 148), INK


def _people():
    """Deterministic walkers: (x, y_feet, vx, vy) in frame fractions; far-sidewalk crowd has small y."""
    rng = random.Random(7)
    far = [(0.05 + 0.9 * i / 8 + rng.uniform(-0.02, 0.02), rng.uniform(0.315, 0.345), rng.choice((-1, 1)) * 0.012, 0.0) for i in range(9)]
    road = [(0.12, 0.47, 0.035, 0.02), (0.31, 0.52, -0.03, 0.025), (0.55, 0.45, 0.03, 0.03), (0.80, 0.55, -0.035, 0.02),
            (0.40, 0.61, 0.03, -0.02), (0.68, 0.63, -0.02, 0.025),
            (0.09, 0.76, 0.03, -0.035), (0.27, 0.86, -0.025, -0.03), (0.47, 0.79, 0.035, -0.03),
            (0.64, 0.92, -0.03, -0.025), (0.84, 0.81, 0.02, -0.04), (0.93, 0.95, -0.035, -0.02)]
    return far + road


PEOPLE = _people()


def _moved(people, dt):
    out = []
    for x, y, vx, vy in people:
        x2, y2 = x + vx * dt, y + vy * dt
        if y >= 0.36:
            y2 = min(0.96, max(0.42, y2))
        out.append((min(0.96, max(0.04, x2)), y2, vx, vy))
    return out


def _person_box(x, y):
    """Pixel box (1x) of a figure whose feet are at (x, y) frame fractions; bigger when nearer."""
    h = FH * (0.085 + 0.17 * clamp((y - 0.30) / 0.66))
    w = 0.40 * h
    px, py = x * FW, y * FH
    return px - w / 2, py - h, px + w / 2, py


def _draw_person(d, x, y, colour, box_colour=None):
    x0, y0, x1, y1 = (v * SS for v in _person_box(x, y))
    h, w = y1 - y0, x1 - x0
    r = 0.15 * h
    cx = (x0 + x1) / 2
    d.ellipse((cx - r, y0, cx + r, y0 + 2 * r), fill=colour)
    d.rounded_rectangle((x0, y0 + 2 * r + 0.04 * h, x1, y1), radius=int(w * 0.42), fill=colour)
    if box_colour:
        p = 4 * SS
        d.rectangle((x0 - p, y0 - p, x1 + p, y1 + p), outline=box_colour, width=2 * SS)


def scene(people, highlight: bool = False) -> Image.Image:
    w, h = FW * SS, FH * SS
    im = Image.new("RGBA", (w, h), (*BUILD_BG, 255))
    d = ImageDraw.Draw(im)
    rng = random.Random(3)
    x = -10
    while x < w:                                   # building blocks with windows
        bw = rng.randint(70, 150)
        top = rng.uniform(0.03, 0.15) * h
        d.rectangle((x, top, x + bw - 6, 0.27 * h), fill=BLOCK)
        for wy in range(int(top + 12), int(0.25 * h), 18):
            for wx in range(x + 10, x + bw - 18, 20):
                if rng.random() < 0.55:
                    d.rectangle((wx, wy, wx + 8, wy + 8), fill=WINDOW)
        x += bw
    d.rectangle((0, 0.27 * h, w, 0.36 * h), fill=WALK)
    d.rectangle((0, 0.36 * h, w, 0.88 * h), fill=ROAD)
    d.rectangle((0, 0.88 * h, w, h), fill=WALK)
    for band in ((0.385, 0.465), (0.79, 0.865)):   # crosswalk stripes
        for sx in range(12, w, 40):
            d.rectangle((sx, band[0] * h, sx + 20, band[1] * h), fill=STRIPE)
    for x_, y_, _, _ in sorted(people, key=lambda p: p[1]):
        near = y_ > KERB_Y
        far_crowd = y_ < 0.36
        col = PERSON_HI if (highlight and near) else (PERSON_FAR if far_crowd else PERSON)
        _draw_person(d, x_, y_, col, SAFE if (highlight and near) else None)
    out = down(im, (FW, FH))
    mask = Image.new("L", (FW * SS, FH * SS), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, FW * SS - 1, FH * SS - 1), 10 * SS, fill=255)
    out.putalpha(down(mask, (FW, FH)))
    return out


def frame_sprite(img: Image.Image, colour, tag: str) -> Image.Image:
    """Thumbnail with a coloured border and a tag in its top-left corner; returned with a 6 px margin."""
    m = 6
    sp = Image.new("RGBA", (FW + 2 * m, FH + 2 * m), (0, 0, 0, 0))
    sp.alpha_composite(img, (m, m))
    hi = Image.new("RGBA", (sp.width * SS, sp.height * SS), (0, 0, 0, 0))
    ImageDraw.Draw(hi).rounded_rectangle((m * SS - 4, m * SS - 4, (m + FW) * SS + 3, (m + FH) * SS + 3), 12 * SS, outline=(*colour, 255), width=4 * SS)
    sp.alpha_composite(down(hi, sp.size))
    tw, _ = text_size(tag, 20, 600)
    rounded(sp, (m + 10, m + 10, m + 10 + tw + 40, m + 10 + 34), 9, fill=NAVY, alpha=0.86)
    over(sp, lambda d: d.ellipse((m + 22, m + 23, m + 30, m + 31), fill=(*colour, 255)))
    draw_text(sp, (m + 38, m + 15), tag, 20, 600, INK)
    return sp


def kerb_sprite() -> Image.Image:
    sp = Image.new("RGBA", (FW, 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    for x in range(4, FW - 4, 26):
        d.line([(x, 4), (min(x + 16, FW - 4), 4)], fill=(*WARNING, 255), width=4)
    return sp


def tint_sprite() -> Image.Image:
    sp = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    ImageDraw.Draw(sp).rectangle((0, int(KERB_Y * FH), FW, FH), fill=(*SAFE, 42))
    mask = Image.new("L", (FW, FH), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, FW - 1, FH - 1), 10, fill=255)
    a = Image.composite(sp.getchannel("A"), Image.new("L", (FW, FH), 0), mask)
    sp.putalpha(a)
    return sp


def chip_sprite() -> tuple[Image.Image, int]:
    text = "hand count · t"
    tw, _ = text_size(text, 24, 600)
    w, h = 16 + 30 + 12 + tw + 20, CHIP_Y1 - CHIP_Y0
    hi = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(hi)
    d.rounded_rectangle((0, 0, w * SS - 1, h * SS - 1), 12 * SS, fill=(*INK, 255))
    x0, y0 = 16 * SS, 13 * SS                      # tally marks: four strokes and a bar
    for i in range(4):
        d.line([(x0 + (3 + i * 7) * SS, y0), (x0 + (3 + i * 7) * SS, y0 + 22 * SS)], fill=(*NAVY, 255), width=3 * SS)
    d.line([(x0 - 1 * SS, y0 + 18 * SS), (x0 + 28 * SS, y0 + 4 * SS)], fill=(*NAVY, 255), width=3 * SS)
    sp = down(hi, (w, h))
    draw_text(sp, (16 + 30 + 12, h / 2), text, 24, 600, NAVY, anchor="lm")
    return sp, w


def ghost_sprite() -> Image.Image:
    m = 6
    hi = Image.new("RGBA", ((FW + 2 * m) * SS, (FH + 2 * m) * SS), (0, 0, 0, 0))
    dashed_path(ImageDraw.Draw(hi), rrect_path((m * SS, m * SS, (m + FW) * SS, (m + FH) * SS), 12 * SS), (*INK_3, 255), 2 * SS, 12 * SS, 9 * SS)
    return down(hi, (FW + 2 * m, FH + 2 * m))


# ---------- the slate (left half, mp4 only) ----------

def camera_glyph(d, x, y, s, fill):
    d.ellipse((x + 4 * s, y, x + 18 * s, y + 14 * s), outline=fill, width=int(3 * s))
    d.ellipse((x + 20 * s, y, x + 34 * s, y + 14 * s), outline=fill, width=int(3 * s))
    d.rounded_rectangle((x, y + 16 * s, x + 38 * s, y + 42 * s), int(5 * s), fill=fill)
    d.polygon([(x + 40 * s, y + 29 * s), (x + 54 * s, y + 19 * s), (x + 54 * s, y + 39 * s)], fill=fill)


SPEAKERS = [(240, "[MEMBER 1]", "m1_start", "m1_end"), (740, "[MEMBER 2]", "m2_start", "end")]
PERSON_CY, PERSON_S = 548, 3.0


def slate_static() -> Image.Image:
    x0, y0, x1, y1 = SLATE
    hi = Image.new("RGBA", (W * SS // 2, H * SS), (0, 0, 0, 0))     # left half at 2x
    d = ImageDraw.Draw(hi)
    d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), 18 * SS, fill=(*NAVY_2, 255))
    dashed_path(d, rrect_path((x0 * SS, y0 * SS, x1 * SS, y1 * SS), 18 * SS), (*WARNING, 255), 3 * SS, 18 * SS, 11 * SS)
    camera_glyph(d, 104 * SS, 184 * SS, 0.9 * SS, (*WARNING, 255))
    # laptop showing two mosaicked stills
    lx0, ly0, lx1, ly1 = 330, 440, 650, 620
    d.rounded_rectangle((lx0 * SS, ly0 * SS, lx1 * SS, ly1 * SS), 10 * SS, fill=(*NAVY_3, 255))
    d.rounded_rectangle(((lx0 - 26) * SS, ly1 * SS, (lx1 + 26) * SS, (ly1 + 16) * SS), 6 * SS, fill=(*INK_3, 255))
    rng = random.Random(11)
    for k, bx in enumerate((lx0 + 16, (lx0 + lx1) / 2 + 6)):
        tw_, th_ = (lx1 - lx0) / 2 - 22, ly1 - ly0 - 32
        cell = 11
        for gy in range(int(th_ // cell)):
            for gx in range(int(tw_ // cell)):
                g = rng.randint(46, 92)
                d.rectangle(((bx + gx * cell) * SS, (ly0 + 16 + gy * cell) * SS, (bx + gx * cell + cell) * SS, (ly0 + 16 + gy * cell + cell) * SS), fill=(g, g + 8, g + 22, 255))
        for _ in range(3):
            fx, fy = bx + rng.uniform(10, tw_ - 40), ly0 + 16 + rng.uniform(40, th_ - 50)
            d.rectangle((fx * SS, fy * SS, (fx + 22) * SS, (fy + 44) * SS), outline=(*(SAFE if k else BLUE), 255), width=2 * SS)
    out = down(hi, (W // 2, H))
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.alpha_composite(out)
    draw_text(img, (176, 186), SLATE_TITLE, 32, 700, WARNING)
    draw_text(img, (104, 252), SLATE_TEXT, 30, 500, INK, max_width=772)
    return img


def person_sprite(colour) -> Image.Image:
    hi = Image.new("RGBA", (140 * SS, 180 * SS), (0, 0, 0, 0))
    person_icon(ImageDraw.Draw(hi), 70 * SS, 110 * SS, PERSON_S * SS, fill=(*colour, 255))
    return down(hi, (140, 180))


# ---------- static layers ----------
CHIP, CHIP_W = chip_sprite()
GREEN_SCENE, GREEN_HI = scene(PEOPLE), scene(PEOPLE, highlight=True)
RED_SCENE = scene(_moved(PEOPLE, OFFSET))
RED_SPRITE = frame_sprite(RED_SCENE, CRITICAL, "frame actually compared")
GREEN_SPRITE = frame_sprite(GREEN_SCENE, SAFE, "correct frame, aligned")
GREEN_HI_SPRITE = frame_sprite(GREEN_HI, SAFE, "correct frame, aligned")
GHOST = ghost_sprite()
KERB = kerb_sprite()
TINT = tint_sprite()
X_BADGE, OK_BADGE = mark_badge(CRITICAL, "cross"), mark_badge(SAFE, "check")
NEAR_BOXES = [_person_box(x, y) for x, y, _, _ in PEOPLE if y > KERB_Y]
NEAR_BOXES.sort(key=lambda b: (b[0] + b[2]) / 2)
P_DIM, P_LIT = person_sprite(INK_3), person_sprite(INK_2)

SLOTS = transparent()                                   # fixed overlay slots, drawn once
badge(SLOTS, "CORRECTED")
legend_strip(SLOTS)
footer(SLOTS, FOOTER)

CAM_SLOTS = transparent()                               # overlay only: soft backing under the small footer
_fw, _ = text_size(FOOTER, 18, 500)
rounded(CAM_SLOTS, (46, 1027, 60 + _fw + 16, 1065), 10, fill=NAVY, alpha=0.72)

BG = canvas()                                           # mp4 background: navy + slate
BG.alpha_composite(slate_static())

assert OVERLAY_TEXT.startswith("v1 compared hand counts with frames ") and OVERLAY_TEXT.endswith("near field redefined, recounted")
LINE1 = [(f"v1 compared hand counts with ", INK, "red_frame"), (f"frames {OFF} s off", RED_T, "red_frame")]
LINE2 = [("→ ", INK, "green_frame"), ("fixed", GREEN_T, "green_frame"), ("; ", INK, "green_frame"),
         ("near field redefined, recounted", INK, "kerb_line")]
assert "".join(r[0] for r in LINE1) + " " + "".join(r[0] for r in LINE2) == OVERLAY_TEXT


def x_at(dt: float) -> float:
    """Inset-local x of time t + dt on the film strip."""
    return C_T + dt * PX_PER_S


# ---------- per-frame drawing ----------

def draw_strip(img: Image.Image, t: float) -> None:
    b = BEATS
    intro = progress(t, b["inset_in"] + 0.15, 0.7)
    sweep = progress(t, b["red_frame"], 0.6)
    green = progress(t, b["green_frame"] + 0.2, 0.4)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    pitch = PX_PER_S / CLIP_FPS
    n0 = -int((C_T - PAD) / pitch)
    n1 = int((INSET_W - PAD - C_T) / pitch)
    for n in range(n0, n1 + 1):
        cx = C_T + n * pitch
        a = clamp((intro * (INSET_W + 200) - cx) / 200)          # left-to-right reveal
        if a <= 0:
            continue
        col = NAVY_3
        if 0 < n <= round(OFFSET * CLIP_FPS):
            k = clamp((lerp(C_T, C_OFF, sweep) - cx) / pitch + 1) * (1 - 0.45 * green)
            col = lerp(NAVY_3, RED_DIM, k)
            if n == round(OFFSET * CLIP_FPS):
                col = lerp(col, CRITICAL, sweep * (1 - 0.45 * green))
        if n == 0:
            col = lerp(NAVY_3, SAFE, green)
        d.rounded_rectangle((cx - 5.5, SY, cx + 5.5, SY + SH), 3, fill=(*[int(v) for v in col], int(255 * a)))
    img.alpha_composite(layer)


def build_inset(t: float) -> Image.Image:
    b = BEATS
    im = Image.new("RGBA", (INSET_W, INSET_H), (0, 0, 0, 0))
    rounded(im, (0, 0, INSET_W - 1, INSET_H - 1), 18, fill=NAVY_2, alpha=0.95)
    draw_text(im, (PAD, 20), "FRAME TIMING", 20, 700, INK_3)
    draw_strip(im, t)

    p_chip = progress(t, b["label_t"], 0.45)
    p_pin = progress(t, b["label_t"] + 0.25, 0.4)
    p_ghost = progress(t, b["label_t"] + 0.35, 0.4)
    p_red = progress(t, b["red_frame"] + 0.2, 0.5)
    p_redline = progress(t, b["red_frame"] + 0.45, 0.55)
    p_redmark = progress(t, b["red_frame"] + 0.85, 0.35)
    p_dim = progress(t, b["green_frame"], 0.45)
    p_green = progress(t, b["green_frame"], 0.5)
    p_gline = progress(t, b["green_frame"] + 0.3, 0.35)
    p_okmark = progress(t, b["green_frame"] + 0.5, 0.35)
    p_kerb = progress(t, b["kerb_line"], 0.5)
    p_tint = progress(t, b["kerb_line"] + 0.35, 0.4)

    # time markers and labels under the strip
    if p_pin > 0:
        col_t = lerp(INK_2, SAFE, p_okmark)
        over(im, lambda d: d.line([(C_T, SY - 10), (C_T, SY + SH + 8)], fill=(*[int(v) for v in col_t], 255), width=3), p_pin)
        draw_text(im, (C_T, SY + SH + 14), "t", 24, 700, INK, p_pin, anchor="ma")
    if p_red > 0:
        a = p_red * (1 - 0.45 * p_dim)
        over(im, lambda d: d.line([(C_OFF, SY - 10), (C_OFF, SY + SH + 8)], fill=(*CRITICAL, 255), width=3), a)
        draw_text(im, (C_OFF, SY + SH + 14), f"t + {OFF} s", 24, 700, RED_T, a, anchor="ma")

    # beat 1: label at t, its pin and the empty slot where its frame belongs
    if p_ghost > 0 and p_green < 1:
        im.alpha_composite(fadeimg(GHOST, p_ghost * (1 - p_green)), (C_T - FW // 2 - 6, FY - 6))
    if p_pin > 0:
        y_end = lerp(CHIP_Y1, SY - 10, p_pin)
        def pin(d):
            d.line([(C_T, CHIP_Y1), (C_T, min(y_end, FY - 4))], fill=(*INK_2, 255), width=3)
            if y_end > FY + FH + 4:
                d.line([(C_T, FY + FH + 4), (C_T, y_end)], fill=(*INK_2, 255), width=3)
        over(im, pin, 1.0)

    # beat 2a: the frame actually compared, 2.4 s after the label (red)
    if p_redline > 0:
        pts = [(C_T + CHIP_W / 2 + 4, (CHIP_Y0 + CHIP_Y1) / 2), (C_OFF, (CHIP_Y0 + CHIP_Y1) / 2), (C_OFF, FY - 6)]
        over(im, lambda d: dashed_path(d, pts, (*CRITICAL, 255), 3, 12, 8, p_redline), 1 - 0.6 * p_dim)
    if p_red > 0:
        a = p_red * (1 - 0.42 * p_dim)
        im.alpha_composite(fadeimg(RED_SPRITE, a), (C_OFF - FW // 2 - 6, int(FY - 6 + 22 * (1 - p_red))))
        over(im, lambda d: d.line([(C_OFF, FY + FH + 6), (C_OFF, SY - 10)], fill=(*CRITICAL, 255), width=3), a)
    if p_redmark > 0:
        im.alpha_composite(fadeimg(X_BADGE, p_redmark * (1 - 0.3 * p_dim)), (C_OFF + FW // 2 - X_BADGE.width // 2 - 4, FY - X_BADGE.height // 2 + 2))

    # beat 2b: the correct frame, aligned under the label (green)
    if p_green > 0:
        y = int(FY - 6 + 22 * (1 - p_green))
        im.alpha_composite(fadeimg(GREEN_SPRITE, p_green), (C_T - FW // 2 - 6, y))
        ox, oy = C_T - FW // 2, y + 6                       # thumbnail origin inside the sprite
        for i, (bx0, by0, bx1, by1) in enumerate(NEAR_BOXES):   # recount: near-field people light up
            a = progress(t, b["kerb_line"] + 0.45 + 0.08 * i, 0.25)
            if a > 0:
                box = (int(bx0) - 7 + 6, int(by0) - 7 + 6, int(bx1) + 8 + 6, int(by1) + 8 + 6)
                im.alpha_composite(fadeimg(GREEN_HI_SPRITE.crop(box), a), (ox - 6 + box[0], oy - 6 + box[1]))
        if p_tint > 0:                                       # the near field, below the line
            im.alpha_composite(fadeimg(TINT, p_tint), (ox, oy))
        if p_kerb > 0:                                       # beat 3: dashed far-kerb line drops in
            ky = oy + lerp(0.30 * FH, KERB_Y * FH, p_kerb) - 4      # starts below the frame tag
            im.alpha_composite(fadeimg(KERB, min(1.0, p_kerb * 2)), (ox, int(ky)))
    if p_gline > 0:
        def gl(d):
            d.line([(C_T, CHIP_Y1), (C_T, lerp(CHIP_Y1, FY - 4, p_gline))], fill=(*SAFE, 255), width=4)
            d.line([(C_T, FY + FH + 4), (C_T, lerp(FY + FH + 4, SY - 10, p_gline))], fill=(*SAFE, 255), width=4)
        over(im, gl, 1.0)
    if p_okmark > 0:
        im.alpha_composite(fadeimg(OK_BADGE, p_okmark), (C_T + FW // 2 - OK_BADGE.width // 2 - 4, FY - OK_BADGE.height // 2 + 2))

    # the hand-count label (drawn last, above its pins)
    if p_chip > 0:
        im.alpha_composite(fadeimg(CHIP, p_chip), (int(C_T - CHIP_W / 2), int(CHIP_Y0 - 18 * (1 - p_chip))))
    return im


def build_plate(t: float) -> Image.Image | None:
    b = BEATS
    a_plate = progress(t, b["red_frame"] + 0.4, 0.4)
    if a_plate <= 0:
        return None
    x0, y0, x1, y1 = PLATE
    im = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    rounded(im, (0, 0, im.width - 1, im.height - 1), 16, fill=NAVY_2, alpha=0.95 * a_plate)
    f = font(32, 600)
    for row, runs in enumerate((LINE1, LINE2)):
        x = 30
        for text, colour, beat in runs:
            a = progress(t, b[beat] + (0.5 if beat == "red_frame" else 0.35), 0.4)
            draw_text(im, (x, 22 + row * 42), text, 32, 600, colour, a)
            x += f.getlength(text)
    return im


def foreground(t: float) -> Image.Image:
    """Everything except the slate and background (also the alpha overlay)."""
    fg = SLOTS.copy()
    a_in = progress(t, BEATS["inset_in"], 0.5)
    if a_in > 0:
        fg.alpha_composite(fadeimg(build_inset(t), a_in), (int(INSET_X + 40 * (1 - a_in)), INSET_Y))
    plate = build_plate(t)
    if plate is not None:
        fg.alpha_composite(plate, (PLATE[0], PLATE[1]))
    return fg


def slate_dynamic(img: Image.Image, t: float) -> None:
    """Placeholder speaker cue in the slate: the member whose line it is lights up."""
    for cx, label, start, end in SPEAKERS:
        lit = fade(t, BEATS[start], BEATS[end] + 0.35, 0.25) if BEATS[start] > 0 else (1.0 if t <= BEATS[end] else 1 - progress(t, BEATS[end], 0.25))
        sp_x, sp_y = cx - 70, PERSON_CY - 110
        ly = PERSON_CY + 92
        lw, _ = text_size(label, 22, 600)
        img.alpha_composite(P_DIM, (sp_x, sp_y))
        if lit > 0:
            img.alpha_composite(fadeimg(P_LIT, lit), (sp_x, sp_y))
            dx = cx + 6 - lw / 2 - 22
            over(img, lambda d: d.ellipse((dx, ly + 7, dx + 12, ly + 19), fill=(*WARNING, 255)), lit)
        draw_text(img, (cx + 6, ly), label, 22, 600, tuple(int(v) for v in lerp(INK_3, INK, lit)), anchor="ma")


def frame_overlay(t: float) -> Image.Image:
    """Transparent overlay for the real footage: the foreground plus the footer backing."""
    img = CAM_SLOTS.copy()
    img.alpha_composite(foreground(t))
    return img


def frame_mp4(t: float) -> Image.Image:
    img = BG.copy()
    slate_dynamic(img, t)
    img.alpha_composite(foreground(t))
    return img


STILLS = {"slate": 1.0, "label": 2.9, "red": 4.6, "green": 6.25, "kerb": 7.9}

if __name__ == "__main__":
    for k, tt in STILLS.items():
        still(f"{SHOT}_{k}", frame_mp4(tt))
    if "--stills-only" not in sys.argv:
        print(render(NAME, DURATION, frame_mp4))
        print(render_overlay(NAME, DURATION, frame_overlay))
