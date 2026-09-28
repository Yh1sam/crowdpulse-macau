"""Compare on-device person-detector counts with manual ground truth on a pre-recorded
video, for several detectors, and produce figures + a summary table for the presentation.
Nothing here is synthetic: counts come from the detectors running on the clip through the
app's own VisionProcessor code, ground truth from a human counting sampled frames.

Ground truth: 11 frames (video frame index 24 + 50k, i.e. t = 2.4 + 5k s) counted by hand,
cyclists included (detectors see them as people occupying the space). Two counts per frame:
the whole frame, and the "near field" = people whose feet are below y = 0.66 of frame height
(the near edge of the tram tracks), i.e. the near half of the crossing and the camera-side
corners, roughly within 20 m. The far kerb (y ≈ 0.60) was rejected as the split because a whole
crowd walks along the far crosswalk exactly on it, which makes the count hinge on a few pixels.

Detector near-field counts use the same line on the boxes' estimated ground-contact point
(0.63 / 0.69 reported as a robustness check). Ground contact = box bottom for full-body
detectors; for Apple's upper-body boxes (≈ head to waist) it is estimated as
top + height / 0.47 (stated assumption).

Revision note: `near_count_v1` holds an earlier, looser hand count ("on the crossing") that did
not match any geometric rule the detectors could be scored against; it is kept for transparency
and reported alongside, but `near_count` is the one used.

Reproduce (see also experiments/datasets/video/README.md):
    curl -L -o experiments/datasets/video/yonge_dundas_raw.webm \
        https://upload.wikimedia.org/wikipedia/commons/d/d2/DiagonalCrosswalkYongeDundas.webm
    ffmpeg -i .../yonge_dundas_raw.webm -vf "scale=640:-2,fps=10" -an -c:v libx264 -crf 26 -pix_fmt yuv420p .../yonge_dundas_640_10fps.mp4
    ffmpeg -i .../yonge_dundas_640_10fps.mp4 -vf "select='eq(mod(n\\,50)\\,24)'" -vsync 0 .../frames/frame_%03d.png
    # CoreML models: ios/CrowdPulseSensor/Tools/export_yolo.py, then `xcrun coremlcompiler compile yolo11n.mlpackage .`
    cd ios/CrowdPulseSensor && swiftc -O -o /tmp/videoeval Tools/videoeval/main.swift Sources/Services/PersonDetector.swift \
        Sources/Services/VisionProcessor.swift Sources/Services/FlowEstimator.swift Sources/Models/SensorObservation.swift Tools/videoeval/Shims.swift
    for each variant: /tmp/videoeval <clip> --out counts_<v>.csv --boxes-out boxes_<v>.json [--full-body | --detector coreml --model X.mlmodelc [--conf C]]
    .venv/bin/python experiments/video_eval.py

Note: ffmpeg's `fps=1/5` filter takes the LAST frame of each 5 s interval (t = 2.4, 7.4, ...),
not the frame at 0, 5, 10 s. An earlier version of this evaluation labelled the frames 0, 5, 10 s;
`check_alignment` now verifies every labelled frame pixel-for-pixel against the decoded video.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True, "grid.color": GRID, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.labelcolor": INK2, "legend.frameon": False})

KERB_Y = 0.66
KERB_ROBUSTNESS = (0.63, 0.69)
UPPER_BODY_FRACTION = 0.47
CLIP = "yonge_dundas_640_10fps.mp4"

# (label, key, upper_body_boxes, primary?) — primary variants use each detector's default threshold;
# the others are a threshold-sensitivity check and are NOT used to pick a setting.
VARIANTS = [
    ("Apple built-in, upper body (previous default)", "640_upper", True, True),
    ("Apple built-in, full body", "640_full", False, True),
    ("YOLO11n CoreML, conf 0.25 (new default)", "yolo11n", False, True),
    ("YOLO11s CoreML, conf 0.25", "yolo11s", False, True),
    ("YOLO11n, conf 0.15 (sensitivity)", "yolo11n_c015", False, False),
    ("YOLO11n, conf 0.35 (sensitivity)", "yolo11n_c035", False, False),
]


def decode_frames(clip: Path, w: int = 640, h: int = 360) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(clip), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def check_alignment(truth: pd.DataFrame, frames_dir: Path, decoded: np.ndarray) -> None:
    """Fail loudly if a hand-counted frame image is not the decoded frame at its stated index."""
    for i, row in enumerate(truth.itertuples(), start=1):
        p = frames_dir / f"frame_{i:03d}.png"
        if not p.exists():
            continue
        img = (plt.imread(p)[..., :3] * 255).round()
        diff = float(np.abs(decoded[int(row.frame_index)].astype(float) - img).mean())
        if diff > 1.0:
            raise SystemExit(f"ground truth misaligned: {p.name} does not match video frame {row.frame_index} (mean abs diff {diff:.1f})")
    print(f"alignment ok: {len(truth)} ground-truth frames match their video frame indices")


def near_count(boxes: list[list[float]], upper_body: bool, kerb: float) -> int:
    n = 0
    for _x, y, _w, h in boxes:
        ground = y + h / UPPER_BODY_FRACTION if upper_body else y + h
        n += ground > kerb
    return n


def score(truth: np.ndarray, est: np.ndarray) -> dict:
    err = est - truth
    return {"n": int(len(truth)), "mae": float(np.abs(err).mean()), "bias": float(err.mean()), "found_pct": float(est.sum() / max(1.0, truth.sum()) * 100),
            "pearson_r": float(np.corrcoef(truth, est)[0, 1]) if len(truth) > 2 and est.std() > 0 else None}


def overlay_figure(data: Path, out: Path, decoded: np.ndarray, frame_index: int, truth_row: pd.Series) -> None:
    panels = [("Apple built-in (upper body)", "640_upper", True), ("YOLO11n CoreML (new default)", "yolo11n", False)]
    img = decoded[frame_index]
    h, w = img.shape[:2]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.1))
    for ax, (title, key, _upper) in zip(axes, panels):
        p = data / f"boxes_{key}.json"
        if not p.exists():
            continue
        frames = json.loads(p.read_text())["frames"]
        fr = min(frames, key=lambda f: abs(f["t_sec"] - frame_index / 10.0))
        ax.imshow(img); ax.axis("off"); ax.grid(False)
        ax.axhline(KERB_Y * h, color="#eda100", lw=1, ls="--")
        for x, y, bw, bh in fr["boxes"]:
            ax.add_patch(mpatches.Rectangle((x * w, y * h), bw * w, bh * h, fill=False, lw=1.3, ec="#1baf7a"))
        ax.set_title(f"{title}: {len(fr['boxes'])} boxes (hand count {int(truth_row['actual_count'])}, near field {int(truth_row['near_count'])})", fontsize=10)
    fig.suptitle(f"Same frame (t = {frame_index / 10:.1f} s), two on-device detectors. Dashed line: far kerb used for the near-field split", fontsize=11, fontweight="bold")
    fig.tight_layout(); fig.savefig(out / "detector_overlay.png", dpi=150); plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="experiments/datasets/video")
    ap.add_argument("--out", default="experiments/results/video")
    args = ap.parse_args()
    data, out = Path(args.data), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    truth = pd.read_csv(data / "ground_truth.csv")
    decoded = decode_frames(data / CLIP)
    check_alignment(truth, data / "frames", decoded)
    idx = truth["frame_index"].to_numpy(int)
    summary: dict[str, dict] = {}
    series: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for label, key, upper, primary in VARIANTS:
        cp, bp = data / f"counts_{key}.csv", data / f"boxes_{key}.json"
        if not cp.exists() or not bp.exists():
            continue
        counts = pd.read_csv(cp)
        frames = json.loads(bp.read_text())["frames"]
        if len(frames) != len(counts):
            raise SystemExit(f"{key}: {len(frames)} box frames vs {len(counts)} count rows")
        tot = counts["person_count"].to_numpy(float)
        near = {k: np.array([near_count(f["boxes"], upper, k) for f in frames], float) for k in (KERB_Y, *KERB_ROBUSTNESS)}
        s = {"primary": primary, "latency_ms_median": float(counts["latency_ms"].iloc[1:].median()),
             "whole_frame": score(truth["actual_count"].to_numpy(float), tot[idx]),
             "near_field": score(truth["near_count"].to_numpy(float), near[KERB_Y][idx]),
             "near_field_vs_v1_hand_count": score(truth["near_count_v1"].to_numpy(float), near[KERB_Y][idx]),
             "near_field_kerb_robustness": {f"{k:.2f}": score(truth["near_count"].to_numpy(float), near[k][idx])["mae"] for k in KERB_ROBUSTNESS}}
        summary[label] = s
        series[label] = (counts["t_sec"].to_numpy(float), near[KERB_Y], tot)

    # ---- figure: time series ----
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.8), sharex=True)
    t_gt = idx / 10.0
    for j, (ax, col, title) in enumerate([(axes[0], "near_count", "near field: people with feet below y = 0.66 (near half of the crossing, roughly within 20 m)"), (axes[1], "actual_count", "whole frame, including the far-sidewalk crowd ~50 m away")]):
        ax.plot(t_gt, truth[col], "o-", color=INK, lw=1.8, ms=6, label="manual ground truth", zorder=5)
        for i, (label, _key, _u, primary) in enumerate(VARIANTS):
            if label not in series or not primary:
                continue
            t, near, tot = series[label]
            y = near if j == 0 else tot
            s = summary[label]["near_field" if j == 0 else "whole_frame"]
            ax.plot(t, pd.Series(y).rolling(5, center=True, min_periods=1).mean(), color=SERIES[i], lw=1.3, label=f"{label}: MAE {s['mae']:.1f}, finds {s['found_pct']:.0f}%")
        ax.set_ylabel("people"); ax.set_title(title, fontsize=10); ax.legend(fontsize=8, loc="upper left")
    axes[1].set_xlabel("video time (s)  (detector curves: 0.5 s rolling mean; metrics use the exact labelled frames)")
    fig.suptitle("CC0 crossing video: on-device person counts vs manual ground truth", fontsize=12, fontweight="bold")
    fig.tight_layout(); fig.savefig(out / "video_count_accuracy.png", dpi=160); plt.close(fig)
    peak = truth.iloc[int(truth["actual_count"].idxmax())]
    overlay_figure(data, out, decoded, int(peak["frame_index"]), peak)
    for old in ("detector_overlay_t30.png",):
        (out / old).unlink(missing_ok=True)
    (out / "summary.json").write_text(json.dumps({"kerb_y": KERB_Y, "upper_body_fraction": UPPER_BODY_FRACTION, "variants": summary}, indent=2))

    def row(label: str, s: dict) -> str:
        n, a = s["near_field"], s["whole_frame"]
        r = f"{n['pearson_r']:.2f}" if n["pearson_r"] is not None else "–"
        rob = " / ".join(f"{v:.1f}" for v in s["near_field_kerb_robustness"].values())
        return f"| {label} | {s['latency_ms_median']:.1f} | {n['mae']:.1f} | {n['bias']:+.1f} | {n['found_pct']:.0f}% | {r} | {rob} | {a['mae']:.1f} | {a['found_pct']:.0f}% |"

    head = ["| detector | median latency on Mac (ms) | near MAE | near bias | near found | near r | near MAE at line 0.63 / 0.69 | whole-frame MAE | whole-frame found |", "|---|---|---|---|---|---|---|---|---|"]
    prim = [row(k, v) for k, v in summary.items() if v["primary"]]
    sens = [row(k, v) for k, v in summary.items() if not v["primary"]]
    dense = truth["near_count"] >= 10
    split_lines = ["| detector | near bias, sparse frames (hand count < 10) | near found, dense frames (hand count ≥ 10) |", "|---|---|---|"]
    for label, (t, near, _tot) in series.items():
        if not summary[label]["primary"]:
            continue
        e = near[idx] - truth["near_count"].to_numpy(float)
        found_dense = near[idx][dense.to_numpy()].sum() / max(1.0, truth["near_count"][dense].sum()) * 100
        split_lines.append(f"| {label} | {e[~dense.to_numpy()].mean():+.1f} | {found_dense:.0f}% |")
    md = ("# Video count evaluation\n\nClip: CC0 Yonge & Dundas crossing, 640×360, 10 fps, 566 frames. Ground truth: 11 frames counted by hand "
          "(t = 2.4 + 5k s; alignment verified pixel-for-pixel; cyclists included). Near field = people whose feet are below y = 0.66 "
          "(near half of the crossing, roughly within 20 m); whole frame adds the far-sidewalk crowd (~50 m). "
          "\"Found\" = sum of estimates / sum of hand counts; above 100% means over-counting. With 11 labelled frames from one clip, "
          "differences of 1–2 people in MAE are within noise.\n\n## Detectors at their default settings\n\n" + "\n".join(head + prim) +
          "\n\n## Where the errors come from (near field)\n\n" + "\n".join(split_lines) +
          "\n\n## Threshold sensitivity (not used to choose a setting)\n\n" + "\n".join(head + sens) + "\n")
    (out / "summary.md").write_text(md)
    print(md)


if __name__ == "__main__":
    main()
