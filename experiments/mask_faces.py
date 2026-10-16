"""Pixelate passers-by's faces in the published street-footage figures and app recordings.

The CC0 clip (Yonge & Dundas) and the app recordings that show it are public domain for copyright,
but the people in them did not consent to being shown, so every recognisable face is mosaicked
before a figure or recording is committed. The head boxes are data, in mask_faces_boxes.json next
to this file; this module only applies them, so the masking is reproducible:

- "detector_overlay": head boxes in pixels of the 640x360 clip frame drawn in
  experiments/results/video/detector_overlay.png, keyed by frame index. video_eval.overlay_figure()
  calls mask_overlay_frame() on the frame before plotting it, so the detection boxes and the
  kerb line are drawn on top of the mosaic and no face reaches the figure. A frame index without
  boxes is refused (pick another frame only after adding its head boxes).
- "ios_stills": head boxes in pixels of the two app screenshots in
  experiments/results/simulation_run/ (the far crowd band on the Live tab's camera picture).
- "ios_video": per-frame head boxes for experiments/results/simulation_run/ios_app_video_mode_30s.mp4
  (402x874, 15 fps, 450 frames; frames numbered from 1). "detected" = heads found with Apple Vision
  (face rectangles, body-pose head points and human rectangles, run on 3x crops of the camera
  picture), held for +-5 frames; "app" = the head band of the app's own green person boxes
  (mid-field people), held for +-3 frames; "hand" = hand-marked tracks, linearly interpolated
  between keyframes [frame, x0, y0, x1, y1], for faces the detectors missed (found by eye at 4-8x).

Mosaic: every pixel of a head box is replaced by the mean of its block. In the stills and the video
the app's drawn green box lines are left out of the block means and stay on top, so boxes, counts
and labels are unchanged.

Usage (the unmasked sources are not kept in the working tree):
    .venv/bin/python experiments/mask_faces.py video SRC.mp4 [DST.mp4]
    .venv/bin/python experiments/mask_faces.py still ios_app_live_detection SRC.png [DST.png]
    .venv/bin/python experiments/mask_faces.py still ios_app_offline_buffering SRC.png [DST.png]
DST defaults to the committed path. The detector overlay needs no command: re-running
experiments/video_eval.py re-creates it masked.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, PngImagePlugin

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
BOXES = HERE / "mask_faces_boxes.json"


@lru_cache(maxsize=1)
def boxes() -> dict:
    return json.loads(BOXES.read_text())


# ---------------------------------------------------------------- shared helpers

def _runs(m: np.ndarray, n: int, axis: int) -> np.ndarray:
    """Pixels of m lying on a straight run of at least n True pixels along axis (1 = rows)."""
    m = m if axis == 1 else m.T
    cs = np.concatenate([np.zeros((m.shape[0], 1), np.int32), np.cumsum(m, axis=1, dtype=np.int32)], axis=1)
    full = (cs[:, n:] - cs[:, :-n]) == n
    out = np.zeros_like(m)
    for k in range(n):
        out[:, k:k + full.shape[1]] |= full
    return out if axis == 1 else out.T


def green_lines(a: np.ndarray, run: int) -> np.ndarray:
    """Drawn overlay pixels: straight green box edges plus their anti-aliased fringe. Skin (red above
    green) never qualifies, so faces are mosaicked while the box lines stay on top."""
    a = a.astype(np.int16)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    green = (g - r > 70) & (g - b > 20) & (g > 110)
    edges = _runs(green, run, 1) | _runs(green, run, 0)
    near = np.asarray(Image.fromarray(edges.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))) > 0
    return edges | (near & (g - r > 15) & (g >= b))


def mosaic(a: np.ndarray, box, block: int, clip, keep: np.ndarray | None = None) -> None:
    """In place: replace every pixel of box (x0, y0, x1, y1; clipped to clip) by the mean of its
    block x block cell (cells start at the box corner). keep pixels are left out and untouched."""
    cx0, cy0, cx1, cy1 = clip
    x0, y0, x1, y1 = max(box[0], cx0), max(box[1], cy0), min(box[2], cx1), min(box[3], cy1)
    for by in range(y0, y1, block):
        for bx in range(x0, x1, block):
            ys, xs = slice(by, min(by + block, y1)), slice(bx, min(bx + block, x1))
            cell = a[ys, xs]
            valid = np.ones(cell.shape[:2], bool) if keep is None else ~keep[ys, xs]
            if valid.any():
                cell[valid] = np.round(cell[valid].mean(axis=0)).astype(a.dtype)


# ---------------------------------------------------------------- detector overlay (CC0 frame)

def mask_overlay_frame(img: np.ndarray, frame_index: int) -> np.ndarray:
    """A masked copy of the clip frame `frame_index` (HxWx3 uint8) for the detector-overlay figure."""
    spec = boxes()["detector_overlay"]
    heads = spec["frames"].get(str(frame_index))
    if heads is None:
        raise SystemExit(f"mask_faces: no head boxes for clip frame {frame_index}; mark its faces in "
                         f"{BOXES.name} (detector_overlay.frames) before publishing a figure of it")
    if list(img.shape[1::-1]) != spec["frame_size"]:
        raise SystemExit(f"mask_faces: head boxes are for a {spec['frame_size']} frame, got {img.shape[1::-1]}")
    out = img.copy()
    h, w = out.shape[:2]
    for b in heads:
        mosaic(out, b, max(spec["min_block"], round((b[2] - b[0]) / spec["blocks_across"])), (0, 0, w, h))
    return out


# ---------------------------------------------------------------- app screenshots

def save_png_like(out: Image.Image, src: Image.Image, dst: Path) -> None:
    """Save keeping the source's sRGB intent, text chunks, dpi and EXIF."""
    info = PngImagePlugin.PngInfo()
    if "srgb" in src.info:
        info.add(b"sRGB", bytes([src.info["srgb"]]))
    for k, v in src.info.items():
        if isinstance(v, str):
            info.add_text(k, v)
    kw = {"pnginfo": info, "optimize": True}
    for k in ("dpi", "exif", "icc_profile"):
        if k in src.info:
            kw[k] = src.info[k]
    out.save(dst, **kw)


def mask_still(name: str, src: Path, dst: Path) -> Path:
    spec = boxes()["ios_stills"][name]
    im = Image.open(src)
    rgb = np.asarray(im.convert("RGB")).copy()
    keep = green_lines(rgb, spec["line_run"])
    for b in spec["boxes"]:
        mosaic(rgb, b, spec["block"], spec["clip"], keep)
    out = Image.fromarray(rgb)
    if im.mode == "RGBA":
        out.putalpha(im.getchannel("A"))
    save_png_like(out, im, dst)
    return dst


# ---------------------------------------------------------------- app recording

def video_boxes(n_frames: int) -> dict[int, list[tuple[float, float, float, float]]]:
    """Head boxes to mosaic in each frame (1-based), holds and interpolation applied."""
    spec = boxes()["ios_video"]
    det = {int(k): v for k, v in spec["detected"].items()}
    app = {int(k): v for k, v in spec["app"].items()}
    per: dict[int, list] = {i: [] for i in range(1, n_frames + 1)}
    for i in per:
        for j in range(max(1, i - spec["detected_hold"]), min(n_frames, i + spec["detected_hold"]) + 1):
            per[i] += det.get(j, [])
    for track in spec["hand"]:
        keys = sorted(track["keys"])
        for (fa, *ba), (fb, *bb) in zip(keys, keys[1:] or keys):
            for i in range(fa, fb + 1):
                t = 0.0 if fb == fa else (i - fa) / (fb - fa)
                if i in per:
                    per[i].append([a + (b - a) * t for a, b in zip(ba, bb)])
    for i in per:
        for j in range(max(1, i - spec["app_hold"]), min(n_frames, i + spec["app_hold"]) + 1):
            per[i] += app.get(j, [])
    return per


def _block_for(w: float) -> int:
    """About 6 blocks across a head, never finer than 3 px nor coarser than 10 px."""
    for b in (3, 4, 6, 8):
        if w / b <= 6.5:
            return b
    return 10


def _mosaic_grid(a: np.ndarray, keep: np.ndarray, box, block: int, pic) -> None:
    """Mosaic on a global grid of `block` px, so blocks do not crawl as a box moves."""
    x0, y0 = max(pic[0], int(box[0])), max(pic[1], int(box[1]))
    x1, y1 = min(pic[2], math.ceil(box[2])), min(pic[3], math.ceil(box[3]))
    if x1 <= x0 or y1 <= y0:
        return
    for by in range((y0 // block) * block, y1, block):
        for bx in range((x0 // block) * block, x1, block):
            ys = slice(max(by, pic[1]), min(by + block, pic[3]))
            xs = slice(max(bx, pic[0]), min(bx + block, pic[2]))
            cell, valid = a[ys, xs], ~keep[ys, xs]
            if valid.any():
                cell[valid] = np.round(cell[valid].mean(axis=0)).astype(a.dtype)


def mask_video_frame(a: np.ndarray, heads) -> np.ndarray:
    spec = boxes()["ios_video"]
    pic = spec["picture"]
    a = a.copy()
    keep = green_lines(a, spec["line_run"])
    keep[:pic[1]] = True
    keep[pic[3]:] = True
    for b in sorted(heads, key=lambda b: -(b[2] - b[0])):     # larger heads first, coarser blocks
        _mosaic_grid(a, keep, b, _block_for(b[2] - b[0]), pic)
    return a


def mask_video(src: Path, dst: Path, frames_out: Path | None = None) -> Path:
    """Decode src, mosaic every frame, re-encode (H.264, sRGB-tagged BT.709 like the app's recording)."""
    spec = boxes()["ios_video"]
    w, h = spec["frame_size"]
    probe = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
         "stream=width,height,nb_read_frames,r_frame_rate", "-of", "json", str(src)],
        capture_output=True, check=True, text=True).stdout)["streams"][0]
    n = int(probe["nb_read_frames"])
    if (probe["width"], probe["height"], n) != (w, h, spec["n_frames"]):
        raise SystemExit(f"mask_faces: {src} is {probe['width']}x{probe['height']}, {n} frames; "
                         f"the head boxes are for {w}x{h}, {spec['n_frames']} frames")
    per = video_boxes(n)
    tags = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-color_range", "tv"]
    # Decoding honours the source's colour tags (BT.709, TV range). accurate_rnd: swscale's default
    # path loses ~1.6 luma levels per pass at this odd width (402 px), which would darken the copy.
    sws = "flags=accurate_rnd+full_chroma_int"
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-i", str(src), "-vf", f"scale={sws}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{w}x{h}", "-framerate", probe["r_frame_rate"], "-i", "-",
                            "-vf", f"scale=out_color_matrix=bt709:out_range=tv:{sws},format=yuv420p,"
                            "setparams=colorspace=bt709:color_primaries=bt709:color_trc=iec61966-2-1:range=tv",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "23", *tags,
                            "-movflags", "+faststart", str(dst)], stdin=subprocess.PIPE)
    if frames_out:
        frames_out.mkdir(parents=True, exist_ok=True)
    for i in range(1, n + 1):
        raw = dec.stdout.read(w * h * 3)
        a = mask_video_frame(np.frombuffer(raw, np.uint8).reshape(h, w, 3), per[i])
        if frames_out:
            Image.fromarray(a).save(frames_out / f"m_{i:04d}.png")
        enc.stdin.write(a.tobytes())
    enc.stdin.close()
    if enc.wait() or dec.wait():
        raise SystemExit("mask_faces: ffmpeg failed")
    return dst


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("video", help="mask the app's video-mode recording")
    v.add_argument("src", type=Path)
    v.add_argument("dst", type=Path, nargs="?",
                   default=REPO / "experiments/results/simulation_run/ios_app_video_mode_30s.mp4")
    v.add_argument("--frames-out", type=Path, help="also write the masked frames as PNGs (for checking)")
    s = sub.add_parser("still", help="mask one of the app screenshots")
    s.add_argument("name", choices=sorted(boxes()["ios_stills"]))
    s.add_argument("src", type=Path)
    s.add_argument("dst", type=Path, nargs="?")
    args = ap.parse_args()
    if args.cmd == "video":
        if args.src.resolve() == args.dst.resolve():
            raise SystemExit("mask_faces: write to a different path than the source")
        print(mask_video(args.src, args.dst, args.frames_out))
    else:
        dst = args.dst or REPO / f"experiments/results/simulation_run/{args.name}.png"
        print(mask_still(args.name, args.src, dst))


if __name__ == "__main__":
    main()
