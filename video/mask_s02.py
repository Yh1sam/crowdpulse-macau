"""Pixelate passers-by's faces in the S02 source clip (the iOS app in the iPhone Simulator).

S02 shows video/build/clips/S02_sim.mp4 from 5.0 s for 7.0 s: the CrowdPulse Sensor app playing the
public-domain (CC0) Yonge & Dundas clip, with the app's green person boxes. CC0 covers copyright, not
the likeness of the people in it, so every head in the app's camera picture is mosaicked before the
clip reaches the cut (script.md section 6, "Never say or show").

Steps (each writes into video/build/s02_mask/ unless noted):
    .venv/bin/python video/mask_s02.py extract   # 30 fps frames of the window S02 uses
    .venv/bin/python video/mask_s02.py detect    # Apple Vision on 2x crops of the camera picture
    .venv/bin/python video/mask_s02.py boxes     # head boxes per frame -> video/shots/S02_heads.json
    .venv/bin/python video/mask_s02.py apply     # mosaic -> video/build/clips/S02_sim_masked.mp4
    .venv/bin/python video/mask_s02.py all

Head boxes per frame = Apple Vision face rectangles, head boxes built from body-pose head points,
the top of Vision's upper-body and full-body boxes, and the top of each of the app's own green person
boxes. Each box is held for +-HOLD frames, so a face missed in a few frames stays covered. Mosaic
blocks are averaged without the app's green box lines, which stay on top. The boxes are committed as
data (video/shots/S02_heads.json), so `apply` alone reproduces the masked clip without the detector.
The detector (video/tools/detect_heads.swift) needs macOS: `swiftc -O video/tools/detect_heads.swift
-o video/build/tools/detect_heads`.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "video/build/clips/S02_sim.mp4"
DST = ROOT / "video/build/clips/S02_sim_masked.mp4"
WORK = ROOT / "video/build/s02_mask"
BOXES = ROOT / "video/shots/S02_heads.json"
DETECT = ROOT / "video/build/tools/detect_heads"
START, LENGTH, FPS = 5.0, 7.2, 30   # the window S02 uses (recipes.s02: -ss 5, 7.0 s slot) + margin
PIC = (0, 234, 1206, 1066)          # the app's camera picture inside the 1206x2622 recording (measured)
UP = 2                              # detection crops are 2x upscales of PIC
HOLD = 8                            # frames held either side (about 0.27 s)
MIN_HEAD = 14                       # px in the recording; ~6 px in the 1080p cut, not recognisable
HEADPTS = ("nose", "leye", "reye", "lear", "rear")


def frames() -> list[Path]:
    return sorted((WORK / "frames").glob("f_*.png"))


def extract() -> None:
    out = WORK / "frames"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(START), "-i", str(SRC), "-t", str(LENGTH),
                    "-vf", f"fps={FPS}", str(out / "f_%04d.png")], check=True)
    crops = WORK / "crops"
    shutil.rmtree(crops, ignore_errors=True)
    crops.mkdir()
    x0, y0, x1, y1 = PIC
    for f in frames():
        Image.open(f).convert("RGB").crop(PIC).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS).save(crops / f.name)
    print(f"{len(frames())} frames")


def detect() -> None:
    if not DETECT.exists():
        sys.exit("build the detector first (see the module docstring)")
    crops = sorted((WORK / "crops").glob("f_*.png"))
    lst = WORK / "crops.txt"
    lst.write_text("".join(f"{c}\n" for c in crops))
    with open(WORK / "detect.jsonl", "w") as fh:
        subprocess.run([str(DETECT), str(lst)], stdout=fh, check=True)
    print(f"detected on {len(crops)} crops")


def green_mask(a: np.ndarray) -> np.ndarray:
    a = a.astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (g - r > 60) & (g - b > 15) & (g > 100)


def app_boxes(a: np.ndarray, min_w: int = 12, min_h: int = 40) -> list[tuple[int, int, int, int]]:
    """The app's green person boxes (in recording pixels), found from their top-left corners."""
    gm = green_mask(a)
    H, W = gm.shape
    x0p, y0p, x1p, y1p = PIC
    out: list[tuple[int, int, int, int]] = []
    ys, xs = np.nonzero(gm[y0p:y1p, x0p:x1p])
    for y, x in zip(ys + y0p, xs + x0p):
        if (x > 0 and gm[y, x - 1]) or (y > 0 and gm[y - 1, x]):
            continue
        if x + min_w >= x1p or y + 6 >= y1p or not (gm[y, x:x + min_w].all() and gm[y:y + 6, x].all()):
            continue
        xr = x
        while xr + 1 < x1p and (gm[y, xr + 1] or gm[min(y + 1, H - 1), xr + 1] or gm[min(y + 2, H - 1), xr + 1]):
            xr += 1
        yb = y
        while yb + 1 < y1p and (gm[yb + 1, x] or gm[yb + 1, min(x + 1, W - 1)] or gm[yb + 1, min(x + 2, W - 1)]):
            yb += 1
        if yb - y >= min_h and xr - x >= min_w and not any(abs(x - o[0]) <= 3 and abs(y - o[1]) <= 3 for o in out):
            out.append((int(x), int(y), int(xr), int(yb)))
    return out


def to_rec(x: float, y: float) -> tuple[float, float]:
    return x / UP + PIC[0], y / UP + PIC[1]


def vision_heads(d: dict) -> list[list[float]]:
    out = []
    for f in d.get("faces", []):
        (x0, y0), (x1, y1) = to_rec(f["x0"], f["y0"]), to_rec(f["x1"], f["y1"])
        w, h = x1 - x0, y1 - y0
        out.append([x0 - 0.5 * w, y0 - 0.6 * h, x1 + 0.5 * w, y1 + 0.4 * h])
    for p in d.get("poses", []):
        pts = [to_rec(*p[k][:2]) for k in HEADPTS if k in p]
        if not pts:
            continue
        cx, cy = sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)
        span = max([abs(a[0] - b[0]) for a in pts for b in pts] + [0])
        if "lsho" in p and "rsho" in p:
            (sx0, _), (sx1, _) = to_rec(*p["lsho"][:2]), to_rec(*p["rsho"][:2])
            span = max(span, 0.5 * abs(sx1 - sx0))
        s = max(1.6 * span, MIN_HEAD)
        out.append([cx - s, cy - 1.2 * s, cx + s, cy + s])
    for u in d.get("uppers", []):
        (x0, y0), (x1, y1) = to_rec(u["x0"], u["y0"]), to_rec(u["x1"], u["y1"])
        out.append([x0, y0, x1, y0 + 0.45 * (y1 - y0)])
    for u in d.get("fulls", []):
        (x0, y0), (x1, y1) = to_rec(u["x0"], u["y0"]), to_rec(u["x1"], u["y1"])
        w = x1 - x0
        out.append([x0 + 0.15 * w, y0 - 0.02 * (y1 - y0), x1 - 0.15 * w, y0 + 0.2 * (y1 - y0)])
    return out


def boxes() -> None:
    dets = {Path(json.loads(l)["path"]).name: json.loads(l) for l in (WORK / "detect.jsonl").read_text().splitlines() if l.strip()}
    per_frame: list[list[list[float]]] = []
    for f in frames():
        a = np.asarray(Image.open(f).convert("RGB"))
        found = vision_heads(dets.get(f.name, {}))
        for x0, y0, x1, y1 in app_boxes(a):
            h = y1 - y0
            found.append([x0, y0 - 0.04 * h, x1, y0 + 0.24 * h])   # head band of the app's own box
        keep = [[round(v, 1) for v in b] for b in found if (b[2] - b[0]) >= MIN_HEAD and (b[3] - b[1]) >= MIN_HEAD]
        per_frame.append(keep)
    BOXES.write_text(json.dumps({"_about": __doc__.splitlines()[0], "source": str(SRC.relative_to(ROOT)),
                                 "start_s": START, "fps": FPS, "picture": PIC, "hold": HOLD, "min_head": MIN_HEAD,
                                 "frames": per_frame}, separators=(",", ":")))
    print(f"{sum(len(b) for b in per_frame)} boxes over {len(per_frame)} frames -> {BOXES.relative_to(ROOT)}")


def mosaic(a: np.ndarray, box: list[float]) -> None:
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    X0, Y0, X1, Y1 = PIC
    x0, y0, x1, y1 = max(x0, X0), max(y0, Y0), min(x1, X1), min(y1, Y1)
    if x1 - x0 < 4 or y1 - y0 < 4:
        return
    blk = max(8, round((x1 - x0) / 4))
    region = a[y0:y1, x0:x1]
    keep = green_mask(region)
    out = region.copy()
    for by in range(0, y1 - y0, blk):
        for bx in range(0, x1 - x0, blk):
            cell = region[by:by + blk, bx:bx + blk]
            m = ~keep[by:by + blk, bx:bx + blk]
            if m.any():
                out[by:by + blk, bx:bx + blk] = cell[m].mean(axis=0).astype(np.uint8)
    out[keep] = region[keep]                          # the app's green box lines stay on top
    a[y0:y1, x0:x1] = out


def apply() -> None:
    data = json.loads(BOXES.read_text())
    per_frame = data["frames"]
    hold = data["hold"]
    out = WORK / "masked"
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    fs = frames()
    if len(fs) != len(per_frame):
        sys.exit("frame count differs from the stored boxes: run extract first")
    for i, f in enumerate(fs):
        a = np.array(Image.open(f).convert("RGB"))
        for j in range(max(0, i - hold), min(len(per_frame), i + hold + 1)):
            for b in per_frame[j]:
                mosaic(a, b)
        Image.fromarray(a).save(out / f.name, compress_level=1)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", str(out / "f_%04d.png"),
                    "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-color_range", "tv", "-colorspace", "bt709",
                    "-color_primaries", "bt709", "-color_trc", "bt709", str(DST)], check=True)
    print(f"{DST.relative_to(ROOT)}: {len(fs)} frames")


if __name__ == "__main__":
    steps = {"extract": extract, "detect": detect, "boxes": boxes, "apply": apply}
    want = sys.argv[1:] or ["all"]
    for s in (["extract", "detect", "boxes", "apply"] if want == ["all"] else want):
        steps[s]()
