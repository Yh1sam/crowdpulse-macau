"""Shared look for the pitch video's motion graphics (docs/video/script.md, section 6).

Every motion-graphics shot is a small script that draws 1920x1080 frames with Pillow and encodes
them with ffmpeg at 30 fps. This module holds the canvas, colours, fonts, the fixed overlay slots
(chapter card, status badge, lower-third with the STEMB strip, caption, evidence legend, footer),
easing, simple shape icons, the zone-graph projection and the encoder, so all shots look alike.

Fonts: video/fonts/Geist[wght].ttf (Latin) and NotoSansTC[wght].ttf (Chinese), SIL OFL, committed with their licence files.
"""
from __future__ import annotations

import json
import math
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterable

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "video" / "build"
FONTS = ROOT / "video" / "fonts"   # committed with their OFL licence files
W, H, FPS = 1920, 1080, 30

# colours (script section 6: navy background, off-white text, dashboard state colours)
NAVY = (11, 18, 32)
NAVY_2 = (20, 31, 52)
NAVY_3 = (33, 48, 76)
INK = (230, 237, 247)
INK_2 = (160, 174, 196)
INK_3 = (98, 113, 138)
SAFE = (46, 160, 67)
WARNING = (245, 166, 35)
CRITICAL = (229, 72, 77)
CYAN = (34, 197, 214)
PURPLE = (150, 110, 230)
GREY = (125, 135, 150)
BLUE = (42, 120, 214)
ORANGE = (235, 104, 52)
STATE_COLOUR = {"SAFE": SAFE, "WARNING": WARNING, "CRITICAL": CRITICAL}

BADGES = {  # status badges (script section 6); no other badge text is allowed
    "SIMULATED": WARNING, "REAL DATA": SAFE, "MODEL CHECK": PURPLE, "PENDING": GREY,
    "CORRECTED": INK, "LIVE SOFTWARE": CYAN, "ILLUSTRATION": GREY,
}
STEMB = [("S", "Science"), ("T", "Technology"), ("E", "Engineering"), ("M", "Medicine"), ("B", "Business")]


# ---------- fonts and text ----------

@lru_cache(maxsize=None)
def font(size: int, weight: int = 400, cjk: bool = False) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(FONTS / ("NotoSansTC[wght].ttf" if cjk else "Geist[wght].ttf")), size)
    f.set_variation_by_axes([weight])
    return f


def has_cjk(text: str) -> bool:
    return any("⺀" <= ch <= "鿿" or "豈" <= ch <= "﫿" or "　" <= ch <= "〿" or "＀" <= ch <= "￯" for ch in text)


def text_font(text: str, size: int, weight: int = 400) -> ImageFont.FreeTypeFont:
    return font(size, weight, cjk=has_cjk(text))


def text_size(text: str, size: int, weight: int = 400) -> tuple[int, int]:
    l, t, r, b = text_font(text, size, weight).getbbox(text)
    return r - l, b - t


def wrap(text: str, size: int, weight: int, max_width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for w_ in words:
        trial = f"{line} {w_}".strip()
        if text_size(trial, size, weight)[0] <= max_width or not line:
            line = trial
        else:
            lines.append(line)
            line = w_
    if line:
        lines.append(line)
    return lines


def draw_text(img: Image.Image, xy: tuple[float, float], text: str, size: int, weight: int = 400, fill=INK,
              alpha: float = 1.0, anchor: str = "la", max_width: int | None = None, line_gap: float = 1.25) -> int:
    """Draws (optionally wrapped) text with opacity; returns the height used."""
    if alpha <= 0:
        return 0
    lines = wrap(text, size, weight, max_width) if max_width else [text]
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for i, ln in enumerate(lines):
        d.text((x, y + i * size * line_gap), ln, font=text_font(ln, size, weight), fill=(*fill[:3], int(255 * alpha)), anchor=anchor)
    img.alpha_composite(layer)
    return int(len(lines) * size * line_gap)


# ---------- easing and timing ----------

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


def ease(t: float) -> float:
    """Cubic ease-in-out on [0, 1]."""
    t = clamp(t)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def progress(t: float, start: float, dur: float) -> float:
    """Eased progress of an animation that starts at `start` (s) and lasts `dur` (s)."""
    return ease((t - start) / dur) if dur > 0 else float(t >= start)


def fade(t: float, start: float, end: float, edge: float = 0.35) -> float:
    """Opacity for an element visible from start to end, fading in and out over `edge` s."""
    if t < start or t > end:
        return 0.0
    return min(progress(t, start, edge), 1 - progress(t, end - edge, edge))


def lerp(a, b, k: float):
    if isinstance(a, tuple):
        return tuple(lerp(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k


# ---------- canvas and overlay slots ----------

def canvas(colour=NAVY) -> Image.Image:
    return Image.new("RGBA", (W, H), (*colour, 255))


def rounded(img: Image.Image, box, radius: int, fill=None, outline=None, width: int = 2, alpha: float = 1.0, dash: bool = False) -> None:
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    d.rounded_rectangle(box, radius, fill=(*fill[:3], a) if fill else None, outline=None if dash else ((*outline[:3], a) if outline else None), width=width)
    if dash and outline:
        x0, y0, x1, y1 = box
        step = 14
        for x in range(int(x0) + radius, int(x1) - radius, step):
            d.line([(x, y0), (min(x + 7, x1 - radius), y0)], fill=(*outline[:3], a), width=width)
            d.line([(x, y1), (min(x + 7, x1 - radius), y1)], fill=(*outline[:3], a), width=width)
    img.alpha_composite(layer)


def chapter_card(img: Image.Image, text: str, alpha: float = 1.0) -> None:
    """Top-left question card (shown for 2 s at the start of a section)."""
    if alpha <= 0:
        return
    w_, _ = text_size(text, 34, 700)
    rounded(img, (60, 48, 60 + w_ + 48, 48 + 64), 14, fill=NAVY_2, alpha=0.92 * alpha)
    draw_text(img, (84, 63), text, 34, 700, INK, alpha)


def badge(img: Image.Image, kind: str, detail: str = "", sub: str = "", alpha: float = 1.0) -> None:
    """Top-right status pill, right edge at x 1860, y 48; optional one-line sub-line under it."""
    if alpha <= 0:
        return
    assert kind in BADGES, kind
    colour = BADGES[kind]
    label = kind + (f" · {detail}" if detail else "")
    tw, _ = text_size(label, 24, 700)
    x1, y0 = 1860, 48
    x0 = x1 - tw - 44
    if kind == "CORRECTED":
        rounded(img, (x0, y0, x1, y0 + 46), 23, fill=NAVY, outline=INK, width=3, alpha=alpha)
        draw_text(img, (x0 + 22, y0 + 10), label, 24, 700, INK, alpha)
    elif kind == "PENDING":
        rounded(img, (x0, y0, x1, y0 + 46), 23, fill=NAVY_2, outline=GREY, width=3, alpha=alpha, dash=True)
        draw_text(img, (x0 + 22, y0 + 10), label, 24, 700, INK_2, alpha)
    else:
        rounded(img, (x0, y0, x1, y0 + 46), 23, fill=colour, alpha=alpha)
        draw_text(img, (x0 + 22, y0 + 10), label, 24, 700, NAVY, alpha)
    if sub:
        sw, _ = text_size(sub, 20, 500)
        rounded(img, (x1 - sw - 14, y0 + 52, x1 + 8, y0 + 84), 8, fill=NAVY, alpha=0.78 * alpha)
        draw_text(img, (x1 - sw, y0 + 58), sub, 20, 500, INK_2, alpha)


def lower_third(img: Image.Image, name: str, letter: str, role: str, alpha: float = 1.0) -> None:
    """Left lower-third (y 800-890): speaker name and the S T E M B strip with their letter(s) lit ("EB" lights two)."""
    if alpha <= 0:
        return
    strip_w = 5 * 46
    text_w = max(text_size(name, 30, 700)[0], text_size(role, 22, 500)[0])
    x1 = 60 + 28 + text_w + 36 + strip_w + 20
    rounded(img, (60, 800, x1, 890), 16, fill=NAVY_2, alpha=0.92 * alpha)
    draw_text(img, (88, 814), name, 30, 700, INK, alpha)
    draw_text(img, (88, 852), role, 22, 500, INK_2, alpha)
    x = x1 - strip_w - 20
    for i, (l, _) in enumerate(STEMB):
        lit = l in letter
        rounded(img, (x + i * 46, 822, x + i * 46 + 38, 868), 9, fill=CYAN if lit else NAVY_3, alpha=alpha)
        draw_text(img, (x + i * 46 + 19, 845), l, 24, 800, NAVY if lit else INK_3, alpha, anchor="mm")


def caption(img: Image.Image, text: str, alpha: float = 1.0) -> None:
    """Burned-in caption, bottom-centre (y 920-990), at most 1400 px wide."""
    if alpha <= 0 or not text:
        return
    lines = wrap(text, 34, 500, 1360)[-2:]
    hgt = len(lines) * 44 + 20
    widest = max(text_size(l, 34, 500)[0] for l in lines)
    x0 = (W - widest) / 2 - 20
    y1 = 990
    rounded(img, (x0, y1 - hgt, W - x0, y1), 12, fill=(0, 0, 0), alpha=0.62 * alpha)
    for i, l in enumerate(lines):
        draw_text(img, (W / 2, y1 - hgt + 10 + i * 44), l, 34, 500, INK, alpha, anchor="ma")


def legend_strip(img: Image.Image, alpha: float = 1.0) -> None:
    """Evidence legend docked bottom-right (y 1000-1024, at most 620 px wide), S10-S16."""
    if alpha <= 0:
        return
    items = ["SIMULATED", "REAL DATA", "MODEL CHECK", "PENDING"]  # CORRECTED left the legend with S12 (19 Oct)
    x = 1860
    for kind in reversed(items):
        tw, _ = text_size(kind, 15, 700)
        x0 = x - tw - 18
        if kind == "PENDING":
            rounded(img, (x0, 1000, x, 1024), 12, fill=NAVY_2, outline=GREY, width=2, alpha=alpha, dash=True)
            draw_text(img, (x0 + 9, 1004), kind, 15, 700, INK_2, alpha)
        else:
            rounded(img, (x0, 1000, x, 1024), 12, fill=BADGES[kind], alpha=alpha)
            draw_text(img, (x0 + 9, 1004), kind, 15, 700, NAVY, alpha)
        x = x0 - 8


def footer(img: Image.Image, text: str, alpha: float = 1.0) -> None:
    """Small source footer, bottom-left (y 1032-1060), at most 1150 px wide."""
    if alpha <= 0 or not text:
        return
    draw_text(img, (60, 1034), text, 20, 500, INK_3, alpha, max_width=1150)


# ---------- icons (plain shapes; no third-party artwork) ----------

def phone_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0, fill=INK, screen=NAVY_3) -> None:
    w_, h_ = 44 * s, 80 * s
    d.rounded_rectangle((cx - w_ / 2, cy - h_ / 2, cx + w_ / 2, cy + h_ / 2), int(9 * s), fill=fill)
    d.rounded_rectangle((cx - w_ / 2 + 4 * s, cy - h_ / 2 + 9 * s, cx + w_ / 2 - 4 * s, cy + h_ / 2 - 9 * s), int(4 * s), fill=screen)


def server_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0, fill=INK_2) -> None:
    for i in range(3):
        y = cy - 42 * s + i * 30 * s
        d.rounded_rectangle((cx - 50 * s, y, cx + 50 * s, y + 24 * s), int(5 * s), fill=fill)
        d.ellipse((cx + 30 * s, y + 8 * s, cx + 38 * s, y + 16 * s), fill=SAFE)


def person_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0, fill=INK_3) -> None:
    d.ellipse((cx - 9 * s, cy - 34 * s, cx + 9 * s, cy - 16 * s), fill=fill)
    d.rounded_rectangle((cx - 14 * s, cy - 14 * s, cx + 14 * s, cy + 22 * s), int(10 * s), fill=fill)


def wheelchair_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0, colour=WARNING, width: int = 4) -> None:
    w = max(2, int(width * s))
    d.ellipse((cx - 16 * s, cy - 30 * s, cx - 4 * s, cy - 18 * s), outline=colour, width=w)            # head
    d.line([(cx - 10 * s, cy - 16 * s), (cx - 10 * s, cy + 2 * s), (cx + 10 * s, cy + 2 * s), (cx + 16 * s, cy + 16 * s)], fill=colour, width=w)
    d.arc((cx - 24 * s, cy - 8 * s, cx + 8 * s, cy + 24 * s), 0, 360, fill=colour, width=w)             # wheel


def staff_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0) -> None:
    person_icon(d, cx, cy, s, fill=INK_2)
    d.polygon([(cx - 14 * s, cy - 10 * s), (cx + 14 * s, cy - 10 * s), (cx + 10 * s, cy + 14 * s), (cx - 10 * s, cy + 14 * s)], fill=(214, 255, 61))  # hi-vis vest


def shield_icon(d: ImageDraw.ImageDraw, cx: float, cy: float, s: float = 1.0, fill=CYAN) -> None:
    pts = [(cx, cy - 48 * s), (cx + 40 * s, cy - 32 * s), (cx + 36 * s, cy + 14 * s), (cx, cy + 48 * s), (cx - 36 * s, cy + 14 * s), (cx - 40 * s, cy - 32 * s)]
    d.polygon(pts, fill=fill)


# ---------- the 7-zone graph (shared/zones.json), projected onto the canvas ----------

@lru_cache(maxsize=1)
def zone_graph() -> dict:
    return json.loads((ROOT / "shared" / "zones.json").read_text())


def project(box=(560, 170, 1360, 840)) -> Callable[[float, float], tuple[float, float]]:
    """Linear lat/lon -> pixel projection fitting all zones into `box` (x0, y0, x1, y1), north up."""
    zones = zone_graph()["zones"]
    lats, lons = [z["lat"] for z in zones], [z["lon"] for z in zones]
    la0, la1, lo0, lo1 = min(lats), max(lats), min(lons), max(lons)
    kx = math.cos(math.radians((la0 + la1) / 2))
    span_x, span_y = (lo1 - lo0) * kx, (la1 - la0)
    x0, y0, x1, y1 = box
    scale = min((x1 - x0) / span_x, (y1 - y0) / span_y)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    mx, my = (lo0 + lo1) / 2, (la0 + la1) / 2
    return lambda lat, lon: (cx + (lon - mx) * kx * scale, cy - (lat - my) * scale)


def draw_zone_graph(img: Image.Image, proj=None, states: dict | None = None, labels: bool = True, alpha: float = 1.0,
                    zh: bool = True, radius: int = 26, highlight: str | None = None) -> dict[str, tuple[float, float]]:
    """Draws the 7 zones and 7 street links of shared/zones.json; stairs links are dashed pink.
    `states` maps zone id -> SAFE/WARNING/CRITICAL or an RGB colour (default: neutral grey).
    Returns the pixel position of each zone."""
    proj = proj or project()
    g = zone_graph()
    pos = {z["id"]: proj(z["lat"], z["lon"]) for z in g["zones"]}
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    for e in g["edges"]:
        (x0, y0), (x1, y1) = pos[e["from"]], pos[e["to"]]
        if e.get("has_stairs"):
            n = int(math.hypot(x1 - x0, y1 - y0) // 14)
            for i in range(0, n, 2):
                p0 = (x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n)
                p1 = (x0 + (x1 - x0) * (i + 1) / n, y0 + (y1 - y0) * (i + 1) / n)
                d.line([p0, p1], fill=(232, 121, 249, a), width=6)
        else:
            d.line([(x0, y0), (x1, y1)], fill=(*INK_3, a), width=7)
    for z in g["zones"]:
        x, y = pos[z["id"]]
        st = (states or {}).get(z["id"])
        col = STATE_COLOUR.get(st, st) if isinstance(st, str) else (st or NAVY_3)
        if highlight == z["id"]:
            d.ellipse((x - radius - 10, y - radius - 10, x + radius + 10, y + radius + 10), outline=(*INK, a), width=3)
        d.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(*col[:3], a))
    img.alpha_composite(layer)
    if labels:
        for z in g["zones"]:
            x, y = pos[z["id"]]
            short = {"tercena_corridor": "Rua da Tercena", "rua_sao_paulo": "Rua de S. Paulo", "almeida_ribeiro": "Av. de Almeida Ribeiro"}.get(z["id"], z["name"])
            draw_text(img, (x + radius + 12, y - 15), f'{z["name_zh"]} {short}' if zh else short, 22, 600, INK, alpha)
    return pos


# ---------- encoding ----------

def render(name: str, duration: float, draw_frame: Callable[[float], Image.Image], out_dir: Path | None = None) -> Path:
    """Renders `duration` seconds at 30 fps by calling draw_frame(t) and encodes BUILD/mg/<name>.mp4."""
    out_dir = out_dir or BUILD / "mg"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"mg-{name}-"))
    try:
        n = int(round(duration * FPS))
        for i in range(n):
            frame = draw_frame(i / FPS)
            frame.convert("RGB").save(tmp / f"f_{i:05d}.png", compress_level=1)
        out = out_dir / f"{name}.mp4"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f_%05d.png"),
                        "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", str(out)], check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def render_overlay(name: str, duration: float, draw_frame: Callable[[float], Image.Image], out_dir: Path | None = None) -> Path:
    """Renders a transparent overlay (draw_frame returns RGBA frames on a transparent canvas) to
    BUILD/overlays/<name>.mov (QuickTime Animation with alpha), for compositing over footage with
    ffmpeg's overlay filter."""
    out_dir = out_dir or BUILD / "overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"ov-{name}-"))
    try:
        n = int(round(duration * FPS))
        for i in range(n):
            draw_frame(i / FPS).save(tmp / f"f_{i:05d}.png", compress_level=1)
        out = out_dir / f"{name}.mov"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(tmp / "f_%05d.png"),
                        "-c:v", "qtrle", "-pix_fmt", "argb", str(out)], check=True)
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def still(name: str, img: Image.Image, out_dir: Path | None = None) -> Path:
    """Saves one frame as PNG (for checking a layout)."""
    out_dir = out_dir or BUILD / "mg" / "stills"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    img.convert("RGB").save(path)
    return path


def overlay_png(name: str, img: Image.Image, out_dir: Path | None = None) -> Path:
    """Saves a transparent 1920x1080 overlay (badges, captions, lower-thirds) for ffmpeg's overlay filter."""
    out_dir = out_dir or BUILD / "overlays"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    img.save(path)
    return path


def transparent() -> Image.Image:
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def iter_frames(duration: float) -> Iterable[float]:
    for i in range(int(round(duration * FPS))):
        yield i / FPS
