"""16:9 cover (poster / thumbnail) for the V3 film, in the film's own look.

Draws with pitch_v2's helpers so the fonts, colours and the N05 crowd-rhythm line match the film.
No claims beyond the film's own words: the tagline and the three pills are N18's and N06's lines.

    .venv/bin/python video/cover_v3.py
    -> video/build/v3/cut/crowdpulse_v3_cover_16x9.png (1920x1080), .jpg, and a 1280x720 .jpg for thumbnails
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "video"))
from pitch_v2 import AMBER, BUILD, CYAN, MUTED, PURPLE, W, backdrop, pill, text, text_size  # noqa: E402
from v2_story import PEOPLE  # noqa: E402

OUT = BUILD / "cut"
COMPETITION = "Imperial College London Hackathon Hong Kong & Macau 2026 · Challenge 2(c) Responsible AI"
REPO = "github.com/Yh1sam/crowdpulse-macau"
TAGLINE = "Observe. Forecast. Review. Decide."                     # N18's line
PILLS = [("NUMBERS ONLY, NEVER IMAGES", CYAN), ("FORECASTS SHOW UNCERTAINTY", AMBER), ("A PERSON DECIDES", PURPLE)]


def rhythm(img: Image.Image, t: float = 1.3) -> None:
    """The N05 crowd-rhythm line, static, across the lower half."""
    d = ImageDraw.Draw(img)
    points = [(160 + i * 133, 780 + math.sin(i * .65 + t * .9) * 60) for i in range(13)]
    d.line(points, fill=(30, 83, 105), width=4)
    for i, (x, y) in enumerate(points):
        r = 7 + 4 * (.5 + .5 * math.sin(t * 1.2 - i * .3))
        d.ellipse((x - r, y - r, x + r, y + r), fill=CYAN)


def wordmark(img: Image.Image, y: int, size: int = 150) -> None:
    """"CrowdPulse" in white and "Macau" in cyan, centred as one line."""
    a, b = "CrowdPulse ", "Macau"
    wa, wb = text_size(a, size, 650)[0], text_size(b, size, 650)[0]
    x0 = (W - wa - wb) / 2
    text(img, x0, y, a, size, 650)
    text(img, x0 + wa, y, b, size, 650, CYAN)


def cover() -> Image.Image:
    img = backdrop().copy()
    rhythm(img)
    wordmark(img, 230)
    text(img, W / 2, 425, TAGLINE, 46, 550, CYAN, centre=True)
    text(img, W / 2, 505, "Phones that count people on the device · forecasts with their confidence · staff decide",
         27, 450, MUTED, centre=True)
    widths = [text_size(v, 20, 600)[0] + 36 for v, _ in PILLS]
    x = (W - sum(widths) - 24 * (len(PILLS) - 1)) / 2
    for (value, colour), w in zip(PILLS, widths):
        pill(img, value, x, 585, colour, 20)
        x += w + 24
    names = " · ".join(p["name"] for p in PEOPLE.values())
    text(img, W / 2, 930, names, 22, 450, MUTED, centre=True)
    text(img, 90, 1003, COMPETITION, 20, 450, MUTED)
    text(img, W - 90 - text_size(REPO, 22, 550)[0], 1001, REPO, 22, 550, CYAN)
    return img.convert("RGB")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    img = cover()
    img.save(OUT / "crowdpulse_v3_cover_16x9.png")
    img.save(OUT / "crowdpulse_v3_cover_16x9.jpg", quality=92)
    img.resize((1280, 720), Image.LANCZOS).save(OUT / "crowdpulse_v3_cover_1280x720.jpg", quality=90)
    print(OUT / "crowdpulse_v3_cover_16x9.png")
