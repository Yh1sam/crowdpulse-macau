"""Shot S11 (1:52.0-2:07.0, 15.0 s): two on-device detectors against a careful hand count.

Storyboard: docs/video/script.md, section 3 row S11, section 4 claims row S11, section 6
("Global look and tools", "figure" S11). Shot list: docs/video/shotlist.json (id S11).

0-5.8 s   The same CC0 frame twice: Apple's boxes, then YOLO11n's boxes. The wipe runs 2.8-3.8 s,
          starting in the pause after "clip," so the YOLO11n panel (and its label) is complete as
          "Yo-lo" is spoken; it holds in full to 5.35 s, then cross-fades to the bars (to 5.8 s).
          Faces are mosaicked at the figure's own resolution before any scaling, with the
          detection boxes and the dashed far-kerb line kept on top of the mosaic. Each panel is
          cropped, fitted to 16:9 on navy (no stretching) and slowly pushed in (zoom 1.00 -> 1.06).
5.35-15 s "count vs hand count" bar pairs, Apple -> YOLO11n: within about 20 m (97% lands at about
          6.5 s, inside "ninety-seven percent"), densest frames (not spoken), whole wide scene (on
          "across the whole scene", 27% just before "only twenty-seven").
The storyboard's times (panels to 6.5 s, bars from 6.5 s, "97" at about 7.2 s) are at 140 wpm with
the voice from 0.3 s; the beats below are keyed to the guide voice, which reads faster and speaks
"ninety-seven" from 5.5 s, so the panels end (and the bars start) at 5.35 s instead.
"Apple's detector, 55" and "In the densest frames, 82" are no longer spoken (round-2 lock): both
stay on screen in the bars, with no spoken-number emphasis.

Data sources (read at render time, never retyped):
- experiments/results/video/detector_overlay.png  the two-panel figure (picture only)
- experiments/results/video/summary.json         near-field and whole-frame "found" %, frames
                                                  per group (n), YOLO11n near-field MAE
- experiments/results/video/summary.md           densest-frame "found" % (second table)
- experiments/datasets/video/ground_truth.csv    how many frames have >= 10 nearby people
- docs/video/shotlist.json                       duration (end_s - start_s)

Outputs: video/build/mg/S11.mp4, video/build/mg/stills/S11_*.png, and the mosaicked panel crops
video/build/S11_apple.png / video/build/S11_yolo.png (for the S12 laptop screen).

Run: .venv/bin/python video/mg/S11.py            (render + stills)
     .venv/bin/python video/mg/S11.py --stills   (stills only, for checking the layout)
"""
from __future__ import annotations

import csv
import json
import re
import sys
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from pathlib import Path  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))  # video/mg, for style.py
from style import *  # noqa: E402,F401,F403

SHOT = "S11"
_shot = next(s for s in json.loads((ROOT / "docs/video/shotlist.json").read_text()) if s["id"] == SHOT)
DURATION = round(_shot["end_s"] - _shot["start_s"], 3)          # 15.0 s

# Beat times in seconds from the shot start, keyed to the guide voice video/build/guide/S11.wav
# (say -v Daniel -r 155, 12.12 s) laid from VOICE_START: word times from its pauses (silencedetect:
# 2.71-3.00, 9.19-9.39, 10.64-10.86 s into the file) and prefix syntheses, 17 Oct. Shot times:
# "On eleven frames of a public-domain street clip," 0.2-2.9 (pause 2.91-3.20) | "the open Yo-lo
# model" 3.2-4.5 ("Yo-lo" 3.7-4.3) | "in our app counted" 4.5-5.5 | "ninety-seven percent" 5.5-6.8 |
# "as many nearby people" 6.8-7.9 | "as a careful hand count;" 7.9-9.4 | "across the whole scene,"
# 9.6-10.8 | "only twenty-seven." 11.1-12.2 (the voice ends at 12.3; the bars hold to 15.0).
# Re-key to the real voice take.
VOICE_START = 0.2                 # video/assemble.py default
BEATS = {
    "label_in": 0.0,     # shot start: Apple panel and its label
    "wipe": 2.8,         # end of "clip," (2.91; the eased edge has moved about 10 px by then): Apple ->
                         # YOLO11n, 97% across (label fully in) by 3.6, complete by 3.8, as "Yo-lo" is
                         # spoken (3.7-4.3)
    "to_bars": 5.35,     # "counted" (4.9-5.5): picture cross-fades to the bars; the YOLO11n panel held ~1.75 s
    "near": 5.5,         # "ninety-seven percent" (5.5-6.8): within ~20 m pair grows, 97% lands by 6.5
    "dense": 7.6,        # not spoken ("as a careful hand count", 7.9-9.4): densest pair, with its tag
    "whole": 10.25,      # "across the whole scene" ("whole" 10.3): 27% lands by 11.3, before "twenty-seven" (11.5)
}
WIPE_DUR = 1.0
APPLE_LABEL_OUT = 0.32            # after "wipe": the Apple label fades out (0.2 s), gone by 3.32 s, just before
                                  # the wipe edge reaches the YOLO11n label's right end (x ~850 at 3.32 s), so
                                  # the two labels are never seen spliced into one line
XFADE_DUR = 0.45
TITLE_IN, FRAME_IN = 0.1, 0.15    # after to_bars: title and bar tracks fade in (0.5 s) as the bars start
GROW_DUR = 0.9
PUSH_IN = 0.06                    # zoom 1.00 -> 1.06 over the picture part

# ---------- data ----------
RES = ROOT / "experiments/results/video"
SUMMARY = json.loads((RES / "summary.json").read_text())["variants"]
APPLE_KEY = next(k for k in SUMMARY if k.startswith("Apple built-in, upper body"))
YOLO_KEY = next(k for k in SUMMARY if k.startswith("YOLO11n CoreML, conf 0.25"))


def dense_found(md: str, prefix: str) -> float:
    """'near found, dense frames' from the second table of summary.md."""
    section = md.split("## Where the errors come from", 1)[1].split("\n## ", 1)[0]
    for line in section.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].startswith(prefix):
            return float(re.match(r"([\d.]+)%", cells[-1]).group(1))
    raise KeyError(prefix)


_md = (RES / "summary.md").read_text()
with open(ROOT / "experiments/datasets/video/ground_truth.csv", newline="") as fh:
    _truth = list(csv.DictReader(fh))
N_FRAMES = SUMMARY[YOLO_KEY]["near_field"]["n"]                               # 11
N_DENSE = sum(int(r["near_count"]) >= 10 for r in _truth)                     # 2 (video_eval.py: near_count >= 10)
YOLO_NEAR_MAE = SUMMARY[YOLO_KEY]["near_field"]["mae"]                        # 1.45 -> "1.5"

GROUPS = [  # (label, Apple %, YOLO11n %, note under the pair, beat)
    ("within ≈20 m", SUMMARY[APPLE_KEY]["near_field"]["found_pct"], SUMMARY[YOLO_KEY]["near_field"]["found_pct"],
     f"nearby = within ~20 m · YOLO11n error {YOLO_NEAR_MAE:.1f} people per frame", "near"),
    ("densest frames", dense_found(_md, "Apple built-in, upper body"), dense_found(_md, "YOLO11n CoreML, conf 0.25"),
     f"{N_DENSE} frames with ≥10 nearby people", "dense"),
    ("whole wide scene", SUMMARY[APPLE_KEY]["whole_frame"]["found_pct"], SUMMARY[YOLO_KEY]["whole_frame"]["found_pct"],
     None, "whole"),
]

BADGE_DETAIL = f"{N_FRAMES} hand-counted frames · indicative, not a benchmark"
LABEL_APPLE = "Apple's built-in detector"
LABEL_YOLO = "YOLO11n (Ultralytics), open model on the device"
CREDIT = "'Diagonal crosswalk at Yonge & Dundas in Toronto', Raysonho, Wikimedia Commons, CC0 · faces pixelated by us"
FOOTER = "experiments/results/video/summary.md"
TITLE = "count vs hand count"
DEFINITION = ("= detector count ÷ hand count, summed over the frames in each group "
              "(not the share of individuals detected)")

# guards: the shot list's wording must match what is drawn, and the spoken numbers the data
_ost = _shot["on_screen_text"]
for v in (f"Badge (top-right): REAL DATA · {BADGE_DETAIL}", f"Panel labels: {LABEL_APPLE} / {LABEL_YOLO}",
          f"Bar title: {TITLE} {DEFINITION}", f"Small, under the densest pair: {GROUPS[1][3]}", GROUPS[0][3],
          f"Credit: {CREDIT}", f"Footer: {FOOTER}"):
    assert v in _ost, f"shotlist.json on_screen_text no longer matches: {v!r}"
_vis = _shot["visual"]
for label, apple, yolo, _note, _beat in GROUPS:
    assert f"{apple:.0f}% → {yolo:.0f}%" in _vis, (label, apple, yolo)
for v in ("on eleven frames", f"counted {GROUPS[0][2]:.0f} percent as many nearby people", f"only {GROUPS[2][2]:.0f}."):
    assert v in _shot["narration"].lower(), f"narration no longer matches the data: {v!r}"
assert N_FRAMES == 11  # "eleven frames" is spoken as a word

# ---------- picture prep: mosaic faces, crop panels ----------
FIGURE = RES / "detector_overlay.png"            # 1950 x 615
PANEL_APPLE = (27, 68, 959, 593)                 # picture area of the left panel (measured once)
PANEL_DX = 964                                   # right panel = left panel shifted by 964 px
# Head boxes (x0, y0, x1, y1) in figure pixels, measured on the left panel; the right panel is the
# same frame, so the same boxes are shifted by PANEL_DX. Every face turned towards the camera.
HEADS = [
    (546, 336, 617, 411),   # man at the centre (largest face)
    (275, 325, 292, 346),   # green-shirt man
    (213, 340, 228, 358),   # woman in the pink top
    (355, 325, 370, 342),   # man in the white shirt, behind
    (836, 326, 858, 351),   # man in the black polo, right
    (928, 334, 957, 367),   # man with glasses, right edge
    (788, 370, 806, 389),   # child in white
    (744, 372, 763, 406),   # blonde woman, profile
    (739, 333, 752, 347),   # mid-ground man
    (777, 341, 791, 356),   # mid-ground woman in red
    (811, 332, 824, 346),   # mid-ground man in white, profile
    (475, 339, 487, 351),   # mid-ground walker
    (531, 334, 541, 348),   # mid-ground walker
    (507, 332, 520, 346),   # mid-ground woman with the yellow bag
    (393, 335, 406, 347),   # mid-ground man, striped shirt
    (157, 326, 168, 336),   # small figure, far left
]


LINE_RUN = 10          # a box edge is a straight green run at least this long (px, figure scale)


def _runs(m: np.ndarray, n: int, axis: int) -> np.ndarray:
    """Pixels of `m` lying on a straight run of at least n True pixels along `axis` (1 = rows)."""
    m = m if axis == 1 else m.T
    cs = np.concatenate([np.zeros((m.shape[0], 1), np.int32), np.cumsum(m, axis=1, dtype=np.int32)], axis=1)
    full = (cs[:, n:] - cs[:, :-n]) == n             # window starting at column j is all True
    out = np.zeros_like(m)
    for k in range(n):
        out[:, k:k + full.shape[1]] |= full
    return out if axis == 1 else out.T


def line_mask(fig: Image.Image) -> Image.Image:
    """Pixels of the drawn overlay only: the green detection-box edges (straight runs, plus their
    anti-aliased fringe) and the amber far-kerb dashes (restricted to the kerb rows). Skin or a
    green shirt inside a head box is never kept, so no face pixel survives the mosaic."""
    a = np.asarray(fig).astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g - r > 70) & (g - b > 20) & (g > 110)
    edges = _runs(green, LINE_RUN, 1) | _runs(green, LINE_RUN, 0)
    near = np.asarray(Image.fromarray(edges.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
    fringe = near & (g - r > 15) & (g >= b)          # anti-aliased edge pixels (skin has r > g)
    amber = (r > 200) & (g > 120) & (g < 200) & (b < 100)
    x0, _, x1, _ = PANEL_APPLE
    rows = np.where(amber[:, x0:x1].sum(axis=1) > (x1 - x0) // 4)[0]   # the dashed kerb line (y 414-415)
    kerb = np.zeros_like(amber)
    kerb[rows.min() - 1:rows.max() + 2] = ((r > 150) & (b < 130) & (r - b > 80))[rows.min() - 1:rows.max() + 2]
    return Image.fromarray(((edges | fringe | kerb) * 255).astype(np.uint8))


def mosaic_heads(fig: Image.Image) -> Image.Image:
    """Mosaics every head box in both panels (shrink ~10x with BOX, enlarge with NEAREST) but keeps
    the green detection-box edges and the amber far-kerb dashes on top, so the boxes stay visible."""
    out = fig.copy()
    lines = line_mask(fig)
    for dx in (0, PANEL_DX):
        for x0, y0, x1, y1 in HEADS:
            box = (x0 + dx, y0, x1 + dx, y1)
            pad = 4                                    # context for the line clean-up below
            outer = fig.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
            keep = lines.crop((box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad))
            # average the face without the box lines (else the blocks next to a line turn green)
            clean = outer.copy()
            clean.paste(outer.filter(ImageFilter.MedianFilter(9)), (0, 0), keep.filter(ImageFilter.MaxFilter(3)))
            w_, h_ = box[2] - box[0], box[3] - box[1]
            region = clean.crop((pad, pad, pad + w_, pad + h_))
            small = region.resize((max(2, round(w_ / 10)), max(2, round(h_ / 10))), Image.BOX)
            mos = small.resize((w_, h_), Image.NEAREST)
            mos.paste(outer.crop((pad, pad, pad + w_, pad + h_)), (0, 0), keep.crop((pad, pad, pad + w_, pad + h_)))
            out.paste(mos, box[:2])                    # line pixels stay on top of the mosaic
    return out


def prep_panels() -> tuple[Image.Image, Image.Image]:
    fig = mosaic_heads(Image.open(FIGURE).convert("RGB"))
    x0, y0, x1, y1 = PANEL_APPLE
    apple = fig.crop(PANEL_APPLE)
    yolo = fig.crop((x0 + PANEL_DX, y0, x1 + PANEL_DX, y1))
    BUILD.mkdir(parents=True, exist_ok=True)
    apple.save(BUILD / "S11_apple.png")
    yolo.save(BUILD / "S11_yolo.png")
    return apple, yolo


APPLE_SRC, YOLO_SRC = prep_panels()
FIT = min(W / APPLE_SRC.width, H / APPLE_SRC.height)                     # fit inside 16:9, no stretching
FIT_SIZE = (round(APPLE_SRC.width * FIT), round(APPLE_SRC.height * FIT))
APPLE_FIT = APPLE_SRC.resize(FIT_SIZE, Image.LANCZOS)
YOLO_FIT = YOLO_SRC.resize(FIT_SIZE, Image.LANCZOS)


def pushed(src: Image.Image, z: float) -> Image.Image:
    """The fitted panel centred on navy, zoomed by z about the centre (sub-pixel, no jitter)."""
    cx, cy = src.width / 2, src.height / 2
    data = (1 / z, 0, cx - (W / 2) / z, 0, 1 / z, cy - (H / 2) / z)
    return src.transform((W, H), Image.AFFINE, data, resample=Image.BICUBIC, fillcolor=NAVY).convert("RGBA")


# ---------- small text sprites (drawn once, composited with opacity) ----------

@lru_cache(maxsize=None)
def sprite(text: str, size: int, weight: int = 400, fill=INK, anchor: str = "la"):
    f = text_font(text, size, weight)
    l, t, r, b = f.getbbox(text, anchor=anchor)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), text, font=f, fill=(*fill[:3], 255), anchor=anchor)
    return im, l - 2, t - 2


def with_alpha(im: Image.Image, alpha: float) -> Image.Image:
    if alpha >= 1:
        return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    return im


def put(img: Image.Image, xy, text: str, size: int, weight: int = 400, fill=INK, alpha: float = 1.0, anchor: str = "la"):
    if alpha <= 0:
        return
    im, ox, oy = sprite(text, size, weight, tuple(fill), anchor)
    img.alpha_composite(with_alpha(im, alpha), (int(round(xy[0] + ox)), int(round(xy[1] + oy))))


def layer_alpha(img: Image.Image, layer: Image.Image, alpha: float) -> None:
    if alpha > 0:
        img.alpha_composite(with_alpha(layer, alpha))


# ---------- static layers ----------

def panel_label(text: str) -> Image.Image:
    """Top-left label pill (the chapter-card slot; S11 has no chapter card)."""
    lay = transparent()
    tw, _ = text_size(text, 32, 700)
    rounded(lay, (60, 48, 60 + tw + 48, 48 + 62), 14, fill=NAVY_2, alpha=0.92)
    put(lay, (84, 79), text, 32, 700, INK, anchor="lm")
    return lay


LABEL_APPLE_L = panel_label(LABEL_APPLE)
LABEL_YOLO_L = panel_label(LABEL_YOLO)


def scrims() -> Image.Image:
    """Navy gradients behind the top-right badge and the bottom credit / footer / legend rows."""
    a = np.zeros((H, W), np.float32)
    top = np.clip(1 - np.arange(170) / 170, 0, 1) ** 1.6 * 0.55
    a[:170] = top[:, None]
    ramp = np.clip((np.arange(H) - 930) / 80, 0, 1) * 0.86
    a[930:] = np.maximum(a[930:], ramp[930:, None])
    lay = Image.new("RGBA", (W, H), (*NAVY, 0))
    lay.putalpha(Image.fromarray((a * 255).astype(np.uint8)))
    return lay


SCRIMS = scrims()


def persistent() -> Image.Image:
    """Badge, CC0 credit, evidence legend and footer: on for the whole shot."""
    lay = transparent()
    badge(lay, "REAL DATA", BADGE_DETAIL)
    put(lay, (60, 1001), CREDIT, 20, 500, INK_2)
    legend_strip(lay)
    footer(lay, FOOTER)
    return lay


PERSIST = persistent()

# bar chart geometry
NAME_X, BAR_X0, BAR_X100 = 160, 380, 1630           # bar-name column, 0 % and 100 % (the hand count)
BAR_H, BAR_GAP = 40, 10
ROW_Y = [300, 500, 700]                              # top of each group label
APPLE_COL, YOLO_COL = GREY, CYAN


def bar_y(g: int, k: int) -> int:
    return ROW_Y[g] + 46 + k * (BAR_H + BAR_GAP)


def bar_x(pct: float) -> float:
    return BAR_X0 + (BAR_X100 - BAR_X0) * pct / 100


def chart_title_layer() -> Image.Image:
    lay = transparent()
    put(lay, (140, 136), TITLE, 56, 700, INK)
    for i, ln in enumerate(wrap(DEFINITION, 26, 500, 1640)):
        put(lay, (140, 214 + i * 34), ln, 26, 500, INK_2)
    return lay


def chart_frame_layer() -> Image.Image:
    lay = transparent()
    d = ImageDraw.Draw(lay)
    for g, (label, *_rest) in enumerate(GROUPS):
        put(lay, (140, ROW_Y[g]), label, 30, 700, INK)
        for k, (name, col) in enumerate((("Apple", INK_2), ("YOLO11n", CYAN))):
            y = bar_y(g, k)
            d.rounded_rectangle((BAR_X0, y, BAR_X100, y + BAR_H), 8, fill=(*NAVY_2, 255))
            put(lay, (NAME_X, y + BAR_H / 2), name, 24, 600, col, anchor="lm")
    # 100 % reference (detector count = hand count). Only a bare tick: the storyboard's required
    # lines for S11 hold the one-line definition in the title, so no extra wording here.
    y0, y1 = ROW_Y[0] + 30, bar_y(2, 1) + BAR_H + 8
    for y in range(y0, y1, 14):
        d.line([(BAR_X100, y), (BAR_X100, min(y + 7, y1))], fill=(*INK_2, 255), width=2)
    put(lay, (BAR_X100, ROW_Y[0] + 16), "100%", 22, 600, INK_2, anchor="ms")
    return lay


TITLE_L = chart_title_layer()
FRAME_L = chart_frame_layer()


# ---------- frame ----------

def picture(t: float) -> Image.Image:
    cover = max(W / FIT_SIZE[0], H / FIT_SIZE[1])   # hides the sub-2-px navy pad left by the fit
    z = cover * (1 + PUSH_IN * clamp(t / (BEATS["to_bars"] + XFADE_DUR)))
    k = progress(t, BEATS["wipe"], WIPE_DUR)
    lab = progress(t, BEATS["label_in"], 0.4)
    apple = yolo = None
    if k < 1:
        apple = pushed(APPLE_FIT, z)
        layer_alpha(apple, LABEL_APPLE_L, lab * (1 - progress(t, BEATS["wipe"] + APPLE_LABEL_OUT, 0.2)))
    if k > 0:
        yolo = pushed(YOLO_FIT, z)
        layer_alpha(yolo, LABEL_YOLO_L, 1.0)
    if apple is None:
        return yolo
    if yolo is None:
        return apple
    xb = round(W * (1 - k))                         # wipe edge moves right -> left (xfade wipeleft)
    yolo.paste(apple.crop((0, 0, xb, H)), (0, 0))
    edge = ImageDraw.Draw(yolo)
    edge.rectangle((xb - 2, 0, xb + 1, H), fill=(*INK, 255))
    return yolo


def draw_bars(img: Image.Image, t: float) -> None:
    lay = transparent()
    d = ImageDraw.Draw(lay)
    labels = []
    for g, (_label, apple_pct, yolo_pct, note, beat) in enumerate(GROUPS):
        start = BEATS[beat]
        for k, (pct, col) in enumerate(((apple_pct, APPLE_COL), (yolo_pct, YOLO_COL))):
            p = progress(t, start + 0.12 * k, GROW_DUR)
            if p <= 0:
                continue
            y = bar_y(g, k)
            x1 = BAR_X0 + (bar_x(pct) - BAR_X0) * p
            r = int(min(8, (x1 - BAR_X0) / 2))
            if x1 - BAR_X0 >= 1:
                d.rounded_rectangle((BAR_X0, y, x1, y + BAR_H), r, fill=(*col, 255))
            labels.append((f"{pct:.0f}%", bar_x(pct) - 14, y + BAR_H / 2,
                           progress(t, start + 0.12 * k + GROW_DUR * 0.6, 0.35)))
        if note:
            labels.append((note, None, bar_y(g, 1) + BAR_H + 12, progress(t, start + GROW_DUR, 0.4)))
    img.alpha_composite(lay)
    for text, x, y, a in labels:
        if x is None:
            put(img, (BAR_X0, y), text, 22, 500, INK_2, a)
        else:
            put(img, (x, y), text, 28, 700, NAVY, a, anchor="rm")


def draw_frame(t: float) -> Image.Image:
    xf = progress(t, BEATS["to_bars"], XFADE_DUR)
    if xf < 1:
        img = picture(t)
        if xf > 0:
            img = Image.blend(img, canvas(), xf)
    else:
        img = canvas()
    img.alpha_composite(SCRIMS)
    if t >= BEATS["to_bars"]:
        layer_alpha(img, TITLE_L, progress(t, BEATS["to_bars"] + TITLE_IN, 0.5))
        layer_alpha(img, FRAME_L, progress(t, BEATS["to_bars"] + FRAME_IN, 0.5))
        draw_bars(img, t)
    img.alpha_composite(PERSIST)
    return img


STILLS = {  # beat name -> time (s)
    "apple": 2.0,
    "wipe": 3.2,
    "yolo": 4.6,
    "near": 6.6,
    "dense": 8.8,
    "all": 14.9,
}


def main() -> None:
    for name, t in STILLS.items():
        still(f"{SHOT}_{name}", draw_frame(t))
    if "--stills" in sys.argv:
        return
    out = render(SHOT, DURATION, draw_frame)
    print(out)


if __name__ == "__main__":
    main()
