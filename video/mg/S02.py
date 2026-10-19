"""Shot S02 OVERLAY (8.0 s): "What did we build?" It opens the WHAT part of the video.
The spoken question gets a central focus, then moves into a persistent header before the answer.

A transparent overlay composited over the iPhone Simulator recording of the CrowdPulse Sensor app
(Live tab, Video mode, YOLO11n, CC0 Yonge & Dundas clip) at assembly. The phone screen sits
centre-left in the footage (x 440-937, clear of the chapter card), so everything here stays on the
right third and along the top, on semi-opaque panels:
  - the central spoken question, docking into a persistent 40 px header at 2.4 s;
  - badge LIVE SOFTWARE · TEST CLIP with one short note under it, "iPhone Simulator · Toronto, not
    Macau" (never show the app without it: no physical-phone run is documented);
  - on "counts people on the device": four readings peel off the app's counter panel into a payload
    card (real key names; values rounded as in the shot list), "…" marking the keys not shown;
  - on "and sends": the card slides right to a server icon;
  - on "only numbers": a photo icon tries to follow, bounces off a shield, "image upload → HTTP 403"
    lands and holds to the cut.

Data sources:
  - docs/video/shotlist.json, shot S02: duration (end_s - start_s) and the on-screen text (the
    chapter card, the badge detail, the note, the card's rows and the shield label are checked
    against it word for word).
  - experiments/results/simulation_run/ios_app_debug_payload.png, Debug tab, "Last observation
    (exact payload)": the payload keys and values on the card. The PNG is the only place these
    values exist, so they are transcribed from it exactly below; the card shows them rounded to the
    shot list's figures (checked), and says "example payload · test run, 29 Sep 2026" (the payload's
    own timestamp is 2026-09-29).
  - ios/CrowdPulseSensor/Sources/Models/SensorObservation.swift: every key on the card is checked
    against the app's CodingKeys.
  - backend/app/main.py: media uploads get status 403 (PRIVACY_MODE); the 403 is checked there.
The card shows 4 of the payload's 15 keys, all plain numbers; "…" marks the rest.
19 Oct declutter: the two-line Simulator / clip caption became one short note, and the sensor_id line,
the location, heading and sensor_id rows and the "server" label left the picture.

Outputs:
  video/build/overlays/S02.mov          transparent overlay (QuickTime Animation, alpha)
  video/build/mg/stills/S02_*.png        layout checks over a preview of the fallback clip
                                         (faces mosaicked; the preview is not part of the overlay)

Run:  .venv/bin/python video/mg/S02.py            (stills and the overlay)
      .venv/bin/python video/mg/S02.py --stills   (stills only)
"""
from __future__ import annotations

import io
import json
import math
import re
import subprocess
import sys

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403
from PIL import Image, ImageDraw, ImageFilter  # noqa: E402

SHOT = "S02"
_shot = next(s for s in json.loads((ROOT / "docs" / "video" / "shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 8.0 s

# The question is voiced at 0.2 s; its answer starts at 2.608 s. The original answer
# animation is shifted one second later, following the unchanged body wording. The
# central question covers the footage until its header transition at 2.0–2.4 s.
# Re-key to the team's real take.
BEATS = {
    "badge_in": 2.4,  # reveal the software evidence with the answer
    "peel": 3.75,     # answer now begins at 2.608 s, about one second later
    "server_in": 4.6,
    "slide": 5.3,
    "dock": 6.0,
    "shield_in": 5.75,
    "photo": 5.85,
    "impact": 6.25,   # the 403 explanation retains its reading hold
}

# ---------- text (verbatim from the storyboard / shot list) ----------

CHAPTER = "What did we build?"
BADGE_KIND, BADGE_DETAIL = "LIVE SOFTWARE", "TEST CLIP"
NOTE = "iPhone Simulator · Toronto, not Macau"
CARD_LABEL = "example payload · test run, 29 Sep 2026"
SHIELD_TEXT, SHIELD_CODE = "image upload → ", "HTTP 403"

# ---------- the payload (transcribed exactly from ios_app_debug_payload.png) ----------
# Values as the app sent them (JSON numbers); the card shows them rounded to `places` decimals, the
# shot list's figures. The other keys (latitude / longitude, heading_deg, sensor_id, …) stay off the card.
PAYLOAD_EXACT = [
    ("person_count", 11, 0),
    ("estimated_density", 0.2703125, 2),
    ("flow_direction_deg", 115.78803499919758, 0),
    ("vision_confidence", 0.9146414969243168, 2),
]
PAYLOAD = [(k, f"{v:.{n}f}") for k, v, n in PAYLOAD_EXACT]        # 11, 0.27, 116, 0.91

_ost = _shot["on_screen_text"]
assert _ost.startswith(f"Chapter question (central then persistent header): {CHAPTER} | "), _ost
assert _shot["narration"].startswith(CHAPTER)
assert f"Badge (top-right): {BADGE_KIND} · {BADGE_DETAIL} |" in _ost
assert f"Note under the badge: {NOTE} |" in _ost
assert " · ".join(f"{k} {v}" for k, v in PAYLOAD) + " · … |" in _ost
assert f"Shield: {SHIELD_TEXT + SHIELD_CODE}" in _ost
assert "sensor_id =" not in _ost and "iOS app running" not in _ost
assert CARD_LABEL in _shot["notes"]


def _swift_keys() -> set[str]:
    src = (ROOT / "ios" / "CrowdPulseSensor" / "Sources" / "Models" / "SensorObservation.swift").read_text()
    enum = src.split("enum CodingKeys")[1].split("}")[0]
    keys = set()
    for line in enum.splitlines():
        line = line.strip()
        if line.startswith("case"):
            for item in line[4:].split(","):
                m = re.match(r'\s*(\w+)\s*=\s*"([^"]+)"', item)
                keys.add(m.group(2) if m else item.strip())
    return keys


_keys = _swift_keys()
for _k, _ in PAYLOAD:
    assert _k in _keys, f"{_k} is not a key of SensorObservation.swift"
assert "status_code=403" in (ROOT / "backend" / "app" / "main.py").read_text()

# ---------- layout ----------
# Where the Simulator screen sits in the assembled 1920x1080 frame (scaled to the frame height,
# centre-left; video/recipes.py s02). It starts at x 440, right of the chapter card (x 60-425), and is
# raised 16 px (its top 16 px, white above the status bar, cropped) so the app's Stop button ends at
# y 790, above the lower-third (y 800-890, 0.2-3.2 s). The peel starts from the app's counter cells.
# Re-measure on the real recording (and its push-in) and move these numbers if needed.
PHONE = (440, -16, 937, 1064)
# Value cells of the Live tab's counter panel, as fractions of the screen (x centre, y centre),
# measured on simulation_run/ios_app_video_mode_30s.mp4: people in view, density index, flow,
# speed, vision confidence, stability, upload, buffered.
CELLS = [(0.29, 0.446), (0.675, 0.446), (0.29, 0.495), (0.675, 0.495),
         (0.29, 0.545), (0.675, 0.545), (0.29, 0.594), (0.675, 0.594)]
CELL_FOR_ROW = [0, 1, 2, 4]                    # card row i peels from CELLS[CELL_FOR_ROW[i]]: people, density, flow, vision confidence
CELL_W, CELL_H = 130, 30

CARD_W, PAD, ROW_H = 500, 24, 44
CARD_Y = 236                                   # card y 236-518, between the badge note (to y 146) and the photo's path (y 702)
ROWS_Y0 = 62                                   # first row, inside the card
CARD_X_BUILD, CARD_X_DOCK = 992, 1192          # the card builds near the phone, then slides right
RACK = (1774, 200, 1860, 752)                  # the server, right edge
SHIELD_C = (1700, 702)                         # in front of the server's lower half
TRACK_Y = 702                                  # the photo's path
PHOTO_START_X, PHOTO_HIT_X, PHOTO_REST_X = 1060, 1600, 1440
PILL_403_RIGHT, PILL_403_Y = 1750, 776

KEY_COL = (125, 222, 235)                      # light cyan for key names (reads on navy)
CODE_COL = (255, 128, 132)                     # light red for "HTTP 403" on navy
SS = 3                                         # supersampling for smooth shapes


# ---------- small helpers (local to this shot) ----------

def with_alpha(im: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 0.999:
        return im
    out = im.copy()
    out.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return out


def put(dst: Image.Image, im: Image.Image, x: float, y: float, alpha: float = 1.0) -> None:
    """Alpha-composites `im` with its top-left at (x, y), clipped to the canvas."""
    if alpha <= 0.001:
        return
    x, y = int(round(x)), int(round(y))
    l, t = max(0, -x), max(0, -y)
    r, b = min(im.width, dst.width - x), min(im.height, dst.height - y)
    if r <= l or b <= t:
        return
    src = im if (l, t, r, b) == (0, 0, im.width, im.height) else im.crop((l, t, r, b))
    dst.alpha_composite(with_alpha(src, alpha), (x + l, y + t))


def put_c(dst: Image.Image, im: Image.Image, cx: float, cy: float, alpha: float = 1.0) -> None:
    put(dst, im, cx - im.width / 2, cy - im.height / 2, alpha)


def smooth(w: int, h: int, draw_fn) -> Image.Image:
    """Draws with draw_fn(d, k) at SS x scale (k = SS) and downsamples, for anti-aliased shapes."""
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), SS)
    return big.resize((w, h), Image.LANCZOS)


def txt(d: ImageDraw.ImageDraw, xy, text: str, size: int, weight: int, fill, anchor: str = "la", alpha: float = 1.0):
    d.text(xy, text, font=text_font(text, size, weight), fill=(*fill[:3], int(255 * alpha)), anchor=anchor)


def tw(text: str, size: int, weight: int) -> int:
    return int(text_font(text, size, weight).getlength(text))


def bezier(p0, p1, p2, k):
    return tuple((1 - k) ** 2 * a + 2 * (1 - k) * k * b + k ** 2 * c for a, b, c in zip(p0, p1, p2))


def ease_out(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in(t: float) -> float:
    t = clamp(t)
    return t ** 2


def back_out(t: float, s: float = 1.6) -> float:
    t = clamp(t) - 1
    return 1 + t * t * ((s + 1) * t + s)


# ---------- static sprites (drawn once) ----------

def top_slot() -> Image.Image:
    """Badge pill and the one-line Simulator note under it, on a semi-opaque backing."""
    img = transparent()
    # backing flush with the pill's right edge (x 1860); the note sits 16 px inside it
    x0 = 1860 - 16 - tw(NOTE, 24, 600) - 16
    rounded(img, (x0, 104, 1860, 146), 12, fill=NAVY, alpha=0.85)
    badge(img, BADGE_KIND, BADGE_DETAIL)
    txt(ImageDraw.Draw(img), (1844, 111), NOTE, 24, 600, INK, anchor="ra")
    return img


def card_panel() -> tuple[Image.Image, Image.Image, int]:
    """Card background with its label (returns panel, soft shadow, card height)."""
    rows_end = ROWS_Y0 + len(PAYLOAD) * ROW_H
    h = rows_end + 44                                           # room for the "…" (more keys) under the rows

    def draw(d, k):
        d.rounded_rectangle((0, 0, CARD_W * k - 1, h * k - 1), 16 * k, fill=(*NAVY_2, 235),
                            outline=(*CYAN, 110), width=2 * k)
        d.line([(PAD * k, 50 * k), ((CARD_W - PAD) * k, 50 * k)], fill=(*NAVY_3, 255), width=2 * k)
        for i in range(0, len(PAYLOAD), 2):                    # faint stripes for row reading
            y = ROWS_Y0 + i * ROW_H
            d.rounded_rectangle((12 * k, y * k, (CARD_W - 12) * k, (y + ROW_H) * k), 8 * k, fill=(*NAVY_3, 90))
    panel = smooth(CARD_W, h, draw)
    d = ImageDraw.Draw(panel)
    d.ellipse((PAD, 22, PAD + 10, 32), fill=(*CYAN, 255))
    txt(d, (PAD + 18, 27), CARD_LABEL, 20, 600, INK_2, anchor="lm")
    txt(d, (PAD, rows_end + 18), "…", 28, 700, INK_2, anchor="lm")     # more keys not shown
    shadow = Image.new("RGBA", (CARD_W + 60, h + 60), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((30, 36, CARD_W + 30, h + 36), 16, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(12))
    return panel, shadow, h


def row_sprite(key: str, value: str) -> Image.Image:
    im = Image.new("RGBA", (CARD_W, ROW_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    txt(d, (PAD, ROW_H // 2), key, 26, 500, KEY_COL, anchor="lm")
    txt(d, (CARD_W - PAD, ROW_H // 2), value, 28, 700, INK, anchor="rm")
    return im


def rack_sprite(glow: bool = False) -> Image.Image:
    """A tall server rack in the style module's server-icon look (units with a green LED)."""
    x0, y0, x1, y1 = RACK
    w, h = x1 - x0 + 24, y1 - y0 + 24             # 12 px margin for the glow

    def draw(d, k):
        if glow:
            d.rounded_rectangle((2 * k, 2 * k, (w - 2) * k, (h - 2) * k), 18 * k, outline=(*CYAN, 255), width=4 * k)
        d.rounded_rectangle((12 * k, 12 * k, (w - 12) * k, (h - 12) * k), 12 * k, fill=(*NAVY_2, 235),
                            outline=(*NAVY_3, 255), width=2 * k)
        n = 9
        uh = (h - 24 - 16 - (n - 1) * 8) / n
        for i in range(n):
            uy = 12 + 8 + i * (uh + 8)
            d.rounded_rectangle((20 * k, uy * k, (w - 20) * k, (uy + uh) * k), 5 * k, fill=(*INK_2, 255))
            d.rounded_rectangle((28 * k, (uy + uh / 2 - 2) * k, (w - 52) * k, (uy + uh / 2 + 2) * k), 2 * k, fill=(*INK_3, 255))
            cx, cy = w - 34, uy + uh / 2
            d.ellipse(((cx - 5) * k, (cy - 5) * k, (cx + 5) * k, (cy + 5) * k), fill=(*SAFE, 255))
    return smooth(w, h, draw)


def shield_sprite() -> Image.Image:
    s, w, h = 1.05, 96, 112

    def draw(d, k):
        cx, cy = w / 2 * k, h / 2 * k
        shield_icon(d, cx, cy, s * k, fill=(*CYAN, 255))
        # a padlock in the middle
        d.rounded_rectangle((cx - 15 * k, cy - 4 * k, cx + 15 * k, cy + 20 * k), 4 * k, fill=(*NAVY, 255))
        d.arc((cx - 10 * k, cy - 20 * k, cx + 10 * k, cy + 2 * k), 180, 360, fill=(*NAVY, 255), width=5 * k)
        d.line([(cx - 10 * k, cy - 9 * k), (cx - 10 * k, cy - 2 * k)], fill=(*NAVY, 255), width=5 * k)
        d.line([(cx + 10 * k, cy - 9 * k), (cx + 10 * k, cy - 2 * k)], fill=(*NAVY, 255), width=5 * k)
        d.ellipse((cx - 3 * k, cy + 4 * k, cx + 3 * k, cy + 10 * k), fill=(*CYAN, 255))
    return smooth(w, h, draw)


def photo_sprite() -> Image.Image:
    """A generic 'photo' icon: white frame, sky, sun and two hills (plain shapes)."""
    w, h = 104, 82

    def draw(d, k):
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), 10 * k, fill=(*INK, 255))
        ix0, iy0, ix1, iy1 = 8, 8, w - 8, h - 8
        d.rounded_rectangle((ix0 * k, iy0 * k, ix1 * k, iy1 * k), 5 * k, fill=(*BLUE, 255))
        d.ellipse((66 * k, 16 * k, 82 * k, 32 * k), fill=(*WARNING, 255))
        d.polygon([(ix0 * k, iy1 * k), (34 * k, 36 * k), (60 * k, iy1 * k)], fill=(*NAVY_3, 255))
        d.polygon([(36 * k, iy1 * k), (68 * k, 44 * k), (ix1 * k, 62 * k), (ix1 * k, iy1 * k)], fill=(*INK_3, 255))
    return smooth(w, h, draw)


def cross_sprite() -> Image.Image:
    r = 18

    def draw(d, k):
        d.ellipse((0, 0, 2 * r * k - 1, 2 * r * k - 1), fill=(*CRITICAL, 255), outline=(*INK, 255), width=2 * k)
        a, b = 11 * k, (2 * r - 11) * k
        d.line([(a, a), (b, b)], fill=(*INK, 255), width=4 * k)
        d.line([(a, b), (b, a)], fill=(*INK, 255), width=4 * k)
    return smooth(2 * r, 2 * r, draw)


def pill_403() -> Image.Image:
    wa, wb = tw(SHIELD_TEXT, 26, 600), tw(SHIELD_CODE, 26, 800)
    w, h = wa + wb + 44, 50

    def draw(d, k):
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), 25 * k, fill=(*NAVY, 240), outline=(*CRITICAL, 255), width=3 * k)
    im = smooth(w, h, draw)
    d = ImageDraw.Draw(im)
    txt(d, (22, h // 2), SHIELD_TEXT, 26, 600, INK, anchor="lm")
    txt(d, (22 + wa, h // 2), SHIELD_CODE, 26, 800, CODE_COL, anchor="lm")
    return im


TOP = top_slot()
PANEL, SHADOW, CARD_H = card_panel()
ROWS = [row_sprite(k, v) for k, v in PAYLOAD]
RACK_IMG, RACK_GLOW = rack_sprite(), rack_sprite(glow=True)
SHIELD = shield_sprite()
PHOTO = photo_sprite()
CROSS = cross_sprite()
P403 = pill_403()
CARD_GLOW = smooth(CARD_W + 12, CARD_H + 12, lambda d, k: d.rounded_rectangle(
    (2 * k, 2 * k, (CARD_W + 10) * k, (CARD_H + 10) * k), 20 * k, outline=(*CYAN, 255), width=4 * k))
assert CARD_Y > 146 + 40 and CARD_Y + CARD_H < 650 and CARD_X_DOCK + CARD_W < RACK[0] - 12

# ---------- timing ----------
STAGGER, LIFT, FLY, TEXT_FADE = 0.06, 0.16, 0.50, 0.22
SLIDE_DUR, DOCK_PULSE = 0.70, 0.45


def pill_times(i: int) -> tuple[float, float]:
    s = BEATS["peel"] + i * STAGGER
    return s, s + LIFT + FLY                        # start, landing


def card_x(t: float) -> float:
    return lerp(CARD_X_BUILD, CARD_X_DOCK, progress(t, BEATS["slide"], SLIDE_DUR))


def cell_xy(i: int) -> tuple[float, float]:
    fx, fy = CELLS[CELL_FOR_ROW[i]]
    x0, y0, x1, y1 = PHONE
    return x0 + fx * (x1 - x0), y0 + fy * (y1 - y0)


def pill_img(w: float, h: float, a_fill: float) -> Image.Image:
    w, h = max(8, int(round(w))), max(8, int(round(h)))

    def draw(d, k):
        d.rounded_rectangle((0, 0, w * k - 1, h * k - 1), min(h, 30) / 2 * k, fill=(*CYAN, int(220 * a_fill)),
                            outline=(*INK, int(200 * a_fill)), width=2 * k)
    return smooth(w, h, draw)


# ---------- the frame ----------

def frame(t: float) -> Image.Image:
    img = transparent()

    # Reveal the badge with the answer; the question focus is composited last.
    put(img, TOP, 0, 0, progress(t, BEATS["badge_in"], 0.3))

    # server rack (slides in from the right a little)
    ra = progress(t, BEATS["server_in"], 0.45)
    if ra > 0:
        rx = RACK[0] - 12 + (1 - ra) * 30
        put(img, RACK_IMG, rx, RACK[1] - 12, ra)
        pulse = fade(t, BEATS["dock"] - 0.05, BEATS["dock"] + DOCK_PULSE, 0.15)
        put(img, RACK_GLOW, rx, RACK[1] - 12, pulse)

    # payload card
    cx = card_x(t)
    ca = progress(t, BEATS["peel"] + 0.08, 0.35)
    if ca > 0:
        rise = (1 - ca) * 14
        put(img, SHADOW, cx - 30, CARD_Y - 30 + rise, ca)
        put(img, PANEL, cx, CARD_Y + rise, ca)
        for i, row in enumerate(ROWS):
            _, land = pill_times(i)
            put(img, row, cx, CARD_Y + ROWS_Y0 + i * ROW_H, progress(t, land - 0.06, TEXT_FADE))
        # the card's outline pulses with the server as it docks
        put(img, CARD_GLOW, cx - 6, CARD_Y - 6, fade(t, BEATS["dock"] - 0.05, BEATS["dock"] + DOCK_PULSE, 0.15))

    # the readings peel off the app's panel and fly into the card rows
    for i in range(len(ROWS)):
        s, land = pill_times(i)
        if t < s or t > land + 0.25:
            continue
        ox, oy = cell_xy(i)
        lift = progress(t, s, LIFT)
        fly = progress(t, s + LIFT, FLY)
        tx0 = card_x(t) + 12
        ty0 = CARD_Y + ROWS_Y0 + i * ROW_H + 2
        tcx, tcy = tx0 + (CARD_W - 24) / 2, ty0 + (ROW_H - 4) / 2
        start = (ox, oy - 10 * lift)
        ctrl = ((ox + tcx) / 2, min(oy, tcy) - 30)
        px, py = bezier(start, ctrl, (tcx, tcy), fly)
        w = lerp(CELL_W * (0.9 + 0.12 * lift), CARD_W - 24, fly ** 3)    # compact in flight, widens on landing
        h = lerp(CELL_H * (0.9 + 0.12 * lift), ROW_H - 4, fly)
        a = lift * (1 - progress(t, land - 0.04, 0.25))
        if a > 0.01:
            put_c(img, pill_img(w, h, 1.0), px, py, a * (1 - 0.35 * fly))

    # shield rises in front of the server
    sa = progress(t, BEATS["shield_in"], 0.3)
    if sa > 0:
        k = 0.6 + 0.4 * back_out((t - BEATS["shield_in"]) / 0.35)
        sh = SHIELD if k > 0.995 else SHIELD.resize((max(1, int(SHIELD.width * k)), max(1, int(SHIELD.height * k))), Image.LANCZOS)
        put_c(img, sh, *SHIELD_C, sa)
        # impact ring
        ring = t - BEATS["impact"]
        if 0 <= ring <= 0.45:
            # anti-aliased ring on its own layer, composited (drawing straight onto the frame
            # would overwrite the shield's alpha where they overlap)
            q = ring / 0.45
            r = 50 + 20 * ease_out(q)
            size = 2 * 74
            ring_im = smooth(size, size, lambda d, k: d.ellipse(
                ((74 - r) * k, (74 - r) * k, (74 + r) * k, (74 + r) * k),
                outline=(*CRITICAL, 255), width=5 * k))
            put_c(img, ring_im, *SHIELD_C, 1 - q)

    # the photo tries to follow, hits the shield and bounces back
    pa = progress(t, BEATS["photo"], 0.18)
    if pa > 0:
        hit = BEATS["impact"]
        travel_start = BEATS["photo"] + 0.08
        if t < hit:
            k = ease_in((t - travel_start) / (hit - travel_start)) if t > travel_start else 0.0
            x, y, ang = lerp(PHOTO_START_X, PHOTO_HIT_X, k), TRACK_Y, 0.0
            scale = 0.7 + 0.3 * pa
            alpha = pa
        else:
            k = ease_out((t - hit) / 0.5)
            x = lerp(PHOTO_HIT_X, PHOTO_REST_X, k)
            y = TRACK_Y - 26 * math.sin(math.pi * clamp((t - hit) / 0.5)) * (1 - k * 0.3) + 10 * k
            ang = 12 * k
            scale, alpha = 1.0, 1 - 0.3 * k
        ph = PHOTO if scale > 0.995 else PHOTO.resize((int(PHOTO.width * scale), int(PHOTO.height * scale)), Image.LANCZOS)
        if ang:
            ph = ph.rotate(ang, resample=Image.BICUBIC, expand=True)
        if travel_start < t < hit:
            # a short smear behind the photo at speed (sub-frame copies), so the last frames
            # before the hit (about 100 px a frame) read as motion rather than a strobe
            for j, ga in ((3, 0.10), (2, 0.18), (1, 0.30)):
                kg = ease_in((t - j / 90 - travel_start) / (hit - travel_start))
                xg = lerp(PHOTO_START_X, PHOTO_HIT_X, kg)
                if x - xg > 12:
                    put_c(img, ph, xg, y, alpha * ga)
        put_c(img, ph, x, y, alpha)
        xa = progress(t, hit + 0.05, 0.2)
        if xa > 0:
            put_c(img, CROSS, x + 44, y - 34, xa)

    # "image upload → HTTP 403" lands and holds to the cut
    qa = progress(t, BEATS["impact"] + 0.02, 0.25)
    if qa > 0:
        put(img, P403, PILL_403_RIGHT - P403.width, PILL_403_Y - (1 - qa) * 16, qa)

    chapter_question(img, CHAPTER, t, header_size=36)  # leave space beside the phone's x=440 edge
    return img


# ---------- preview background for the stills (not part of the overlay) ----------

def preview_bg() -> Image.Image:
    """Navy frame with a mosaicked frame of the fallback clip where the Simulator screen sits."""
    bg = canvas(NAVY)
    clip = ROOT / "experiments" / "results" / "simulation_run" / "ios_app_video_mode_30s.mp4"
    png = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", "12", "-i", str(clip), "-frames:v", "1",
                          "-f", "image2pipe", "-vcodec", "png", "-"], check=True, capture_output=True).stdout
    fr = Image.open(io.BytesIO(png)).convert("RGB")
    # mosaic the camera picture's head band (shrink about 10x with BOX, enlarge with NEAREST)
    band = (0, int(fr.height * 0.20), fr.width, int(fr.height * 0.37))
    reg = fr.crop(band)
    reg = reg.resize((max(1, reg.width // 10), max(1, reg.height // 10)), Image.BOX).resize(reg.size, Image.NEAREST)
    fr.paste(reg, band[:2])
    x0, y0, x1, y1 = PHONE
    bg.paste(fr.resize((x1 - x0, y1 - y0), Image.LANCZOS), (x0, y0))
    return bg


STILLS = {"question": 1.0, "docking": 2.2, "peel": 4.2, "card": 5.2,
          "dock": 6.0, "bounce": 6.4, "hold": DURATION - 0.05}

if __name__ == "__main__":
    bg = preview_bg()
    for name, tt in STILLS.items():
        f = bg.copy()
        f.alpha_composite(frame(tt))
        print(still(f"{SHOT}_{name}", f))
    if "--stills" not in sys.argv:
        print(render_overlay(SHOT, DURATION, frame))
