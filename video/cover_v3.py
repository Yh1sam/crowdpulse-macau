"""16:9 cover (poster / thumbnail) and motion cover for the V3 film, in the film's own look.

Draws with pitch_v2's helpers so the fonts, colours and the N05 crowd-rhythm line match the film.
No claims beyond the film's own words: the tagline is N18's line.

    .venv/bin/python video/cover_v3.py            # still + motion
    .venv/bin/python video/cover_v3.py --still    # still only
Outputs in video/build/v3/cut/:
    crowdpulse_v3_cover_16x9.png / .jpg (1920x1080), crowdpulse_v3_cover_1280x720.jpg
    crowdpulse_v3_cover_motion_1080p.mp4   10 s: the wordmark and tagline rise in, the rhythm line keeps moving
    crowdpulse_v3_cover_loop_1080p.mp4      8 s seamless loop: text settled, only the rhythm line moves
"""
from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video"))
from pitch_v2 import BUILD, CYAN, FPS, H, MUTED, W, backdrop, text, text_size  # noqa: E402
from v2_story import PEOPLE  # noqa: E402

OUT = BUILD / "cut"
COMPETITION = "Imperial College London Hackathon Hong Kong & Macau 2026 · Challenge 2(c) Responsible AI"
REPO = "github.com/Yh1sam/crowdpulse-macau"
TAGLINE = "Observe. Forecast. Review. Decide."                     # N18's line
LINE = "Phones that count people on the device · forecasts with their confidence · staff decide"
LOOP_S = 8.0                                                     # the rhythm line's seamless period
INTRO_S = 1.3                                                    # wordmark and tagline rise in (motion version)


def ease(k: float) -> float:
    k = max(0.0, min(1.0, k))
    return 1 - (1 - k) ** 3


def rhythm(img: Image.Image, t: float) -> None:
    """The N05 crowd-rhythm line across the lower half. Every phase is a whole number of cycles per
    LOOP_S, so frame t and frame t + LOOP_S are identical (seamless loop)."""
    w = 2 * math.pi * t / LOOP_S
    d = ImageDraw.Draw(img)
    points = [(160 + i * 133, 780 + math.sin(i * .65 + w) * 60) for i in range(13)]
    d.line(points, fill=(30, 83, 105), width=4)
    for i, (x, y) in enumerate(points):
        r = 7 + 4 * (.5 + .5 * math.sin(2 * w - i * .3))
        d.ellipse((x - r, y - r, x + r, y + r), fill=CYAN)
    # one brighter pulse travels along the line once per loop
    s = (t / LOOP_S) % 1.0 * (len(points) - 1)
    i, k = int(s), s - int(s)
    (x0, y0), (x1, y1) = points[i], points[min(i + 1, len(points) - 1)]
    px, py = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    glow = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for rr, a in ((56, 28), (40, 60), (26, 110), (14, 255)):
        g.ellipse((60 - rr, 60 - rr, 60 + rr, 60 + rr), fill=(*CYAN, a))
    img.alpha_composite(glow, (int(px) - 60, int(py) - 60))


def wordmark(img: Image.Image, y: float, alpha: float = 1.0, size: int = 150) -> None:
    """"CrowdPulse" in white and "Macau" in cyan, centred as one line."""
    a, b = "CrowdPulse ", "Macau"
    wa, wb = text_size(a, size, 650)[0], text_size(b, size, 650)[0]
    x0 = (W - wa - wb) / 2
    text(img, x0, y, a, size, 650, alpha=alpha)
    text(img, x0 + wa, y, b, size, 650, CYAN, alpha=alpha)


def frame(t: float, intro: bool) -> Image.Image:
    img = backdrop().copy()
    rhythm(img, t)
    k1 = ease(t / INTRO_S) if intro else 1.0                     # wordmark
    k2 = ease((t - 0.35) / INTRO_S) if intro else 1.0            # tagline and line follow
    k3 = ease((t - 0.7) / INTRO_S) if intro else 1.0             # footer lines
    wordmark(img, 230 + (1 - k1) * 28, k1)
    text(img, W / 2, 425 + (1 - k2) * 18, TAGLINE, 46, 550, CYAN, alpha=k2, centre=True)
    text(img, W / 2, 505 + (1 - k2) * 14, LINE, 27, 450, MUTED, alpha=k2, centre=True)
    names = " · ".join(p["name"] for p in PEOPLE.values())
    text(img, W / 2, 930, names, 22, 450, MUTED, alpha=k3, centre=True)
    text(img, 90, 1003, COMPETITION, 20, 450, MUTED, alpha=k3)
    text(img, W - 90 - text_size(REPO, 22, 550)[0], 1001, REPO, 22, 550, CYAN, alpha=k3)
    return img


def render(path: Path, seconds: float, intro: bool) -> None:
    n = int(round(seconds * FPS))
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "pipe:0", "-an", "-c:v", "libx264", "-crf", "18", "-preset", "medium",
                             "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709",
                             "-color_trc", "bt709", "-movflags", "+faststart", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(i / FPS, intro).convert("RGB").tobytes())
    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {path}")
    print(path)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    still = frame(INTRO_S + 1.0, intro=False).convert("RGB")
    still.save(OUT / "crowdpulse_v3_cover_16x9.png")
    still.save(OUT / "crowdpulse_v3_cover_16x9.jpg", quality=92)
    still.resize((1280, 720), Image.LANCZOS).save(OUT / "crowdpulse_v3_cover_1280x720.jpg", quality=90)
    print(OUT / "crowdpulse_v3_cover_16x9.png")
    if "--still" not in sys.argv:
        render(OUT / "crowdpulse_v3_cover_motion_1080p.mp4", 10.0, intro=True)
        render(OUT / "crowdpulse_v3_cover_loop_1080p.mp4", LOOP_S, intro=False)
