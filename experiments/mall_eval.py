"""Score the sensor app's person detectors on the Mall dataset (2,000 annotated frames of a real crowd).

The 11 hand-counted frames of experiments/video_eval.py were the only real test of the counting layer.
The Mall dataset (Chen, Loy, Gong & Xiang, BMVC 2012; CUHK; research use only) has the head position
of every pedestrian in all 2,000 frames of a shopping-mall webcam (640x480, 13-53 people per frame), so
it measures the same detectors on far more frames and on denser, partly occluded groups.

Detections come from the app's own code: ios/CrowdPulseSensor/Tools/videoeval (PersonDetector +
VisionProcessor) run over the frames wrapped, without re-encoding, into an MJPEG .mov (every frame
byte-identical to the dataset JPEG). Settings are the app's shipped ones: YOLO11n CoreML at confidence
0.25 / IoU 0.7, and Apple's upper-body detector (the in-app fallback).

Metrics, fixed before any result was looked at:
- Counts (what the phone reports): per-frame MAE, mean signed error, share found = sum(detected) /
  sum(annotated), Pearson r across frames, and MAE by crowd-size tercile of the annotated count.
- Matching (whether the counted boxes are the annotated people): one-to-one assignment between head
  points and boxes. A head can match a box if it lies inside the box widened by 5% of its width on each
  side, and vertically between 5% of the box height above its top and HEAD_FRACTION of the height below
  its top (0.35 for full-body YOLO boxes, 0.60 for Apple's head-to-waist boxes); among feasible pairs the
  assignment minimises the distance to the box's expected head point. Precision = matched boxes / boxes,
  recall = matched heads / heads. HEAD_FRACTION +-0.10 is reported as a robustness range.
- Recall by distance: heads split by image row into far (top third), middle and near (bottom third).

Post-hoc follow-up (added after the results above showed a large, systematic under-count with counts
still tracking the crowd): a per-camera linear calibration, annotated ~ a * detected + b, fitted only on
the dataset's usual training frames (1-800), either all of them or 20 spread evenly across them (what a
team could label while setting up a phone), and scored on the held-out frames 801-2000.

    ios/CrowdPulseSensor: xcrun coremlcompiler compile Resources/yolo11n.mlpackage <build>
    swiftc -O -o <build>/videoeval Tools/videoeval/main.swift Sources/Services/PersonDetector.swift \\
        Sources/Services/VisionProcessor.swift Sources/Services/FlowEstimator.swift Sources/Models/SensorObservation.swift Tools/videoeval/Shims.swift
    ffmpeg -framerate 10 -i <mall>/mall_dataset/frames/seq_%06d.jpg -c:v copy -f mov <mall>/mall_frames_mjpeg.mov
    <build>/videoeval <mall>/mall_frames_mjpeg.mov --fps 10 --detector coreml --model <build>/yolo11n.mlmodelc \\
        --out <mall>/runs/counts_yolo11n.csv --boxes-out <mall>/runs/boxes_yolo11n.json
    <build>/videoeval <mall>/mall_frames_mjpeg.mov --fps 10 --out <mall>/runs/counts_apple_upper.csv --boxes-out <mall>/runs/boxes_apple_upper.json
    .venv/bin/python -I experiments/mall_eval.py --mall experiments/datasets/mall --out experiments/results/mall

Only aggregate metrics and charts without dataset imagery are written to --out (committed); per-frame
tables and the annotated example frame stay in the git-ignored dataset folder, because the dataset is
for research use only and is not redistributed under this repository's licence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy.io import loadmat  # noqa: E402
from scipy.optimize import linear_sum_assignment  # noqa: E402

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7"]
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True, "grid.color": GRID, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.labelcolor": INK2, "legend.frameon": False})

W, H, FPS, N_FRAMES = 640, 480, 10, 2000
DETECTORS = {  # run name -> (label, head fraction of box height, expected head point as a fraction of box height)
    "yolo11n": ("YOLO11n CoreML (app default)", 0.35, 0.10),
    "apple_upper": ("Apple upper-body (app fallback)", 0.60, 0.20),
}
MARGIN, ABOVE = 0.05, 0.05
INFEASIBLE = 1e6


def load_ground_truth(mall: Path) -> tuple[np.ndarray, list[np.ndarray]]:
    gt = loadmat(mall / "mall_dataset" / "mall_gt.mat")
    count = np.asarray(gt["count"]).ravel().astype(int)
    heads = [np.asarray(gt["frame"][0, i][0, 0]["loc"], dtype=float) / [W, H] for i in range(gt["frame"].shape[1])]
    assert len(heads) == N_FRAMES and all(len(h) == c for h, c in zip(heads, count)), "ground truth is inconsistent"
    return count, heads


def load_run(mall: Path, name: str) -> tuple[pd.DataFrame, list[np.ndarray]]:
    counts = pd.read_csv(mall / "runs" / f"counts_{name}.csv")
    frames = json.loads((mall / "runs" / f"boxes_{name}.json").read_text())["frames"]
    idx = [round(f["t_sec"] * FPS) for f in frames]
    assert idx == list(range(N_FRAMES)), f"{name}: frames are not exactly 0..{N_FRAMES - 1}"
    assert np.allclose((counts["t_sec"] * FPS).round(), idx), f"{name}: counts and boxes disagree on frame times"
    boxes = [np.asarray(f["boxes"], dtype=float).reshape(-1, 4) for f in frames]
    assert all(len(b) == c for b, c in zip(boxes, counts["person_count"])), f"{name}: person_count differs from the box list"
    return counts, boxes


def matched_heads(heads: np.ndarray, boxes: np.ndarray, head_fraction: float, head_point: float) -> np.ndarray:
    """Boolean per head: matched under the rule (for recall by image region)."""
    out = np.zeros(len(heads), dtype=bool)
    if len(heads) == 0 or len(boxes) == 0:
        return out
    x0, y0, bw, bh = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    hx, hy = heads[:, :1], heads[:, 1:]
    feasible = (hx >= x0 - MARGIN * bw) & (hx <= x0 + bw + MARGIN * bw) & (hy >= y0 - ABOVE * bh) & (hy <= y0 + head_fraction * bh)
    dist = np.hypot((hx - (x0 + bw / 2)) / bw, (hy - (y0 + head_point * bh)) / bh)
    cost = np.where(feasible, dist, INFEASIBLE)
    rows, cols = linear_sum_assignment(cost)
    out[rows[cost[rows, cols] < INFEASIBLE]] = True
    return out


def match(heads: np.ndarray, boxes: np.ndarray, head_fraction: float, head_point: float) -> int:
    """Number of one-to-one head/box matches under the stated containment rule."""
    return int(matched_heads(heads, boxes, head_fraction, head_point).sum())


def evaluate(gt_count: np.ndarray, heads: list[np.ndarray], counts: pd.DataFrame, boxes: list[np.ndarray], head_fraction: float, head_point: float) -> dict:
    det = counts["person_count"].to_numpy()
    err = det - gt_count
    terciles = np.quantile(gt_count, [1 / 3, 2 / 3])
    bands = {"smallest third": gt_count <= terciles[0], "middle third": (gt_count > terciles[0]) & (gt_count <= terciles[1]), "largest third": gt_count > terciles[1]}
    m = {f: sum(match(h, b, f, head_point) for h, b in zip(heads, boxes)) for f in (head_fraction - 0.1, head_fraction, head_fraction + 0.1)}
    region = {"far (top third of image)": [0, 0], "middle": [0, 0], "near (bottom third)": [0, 0]}
    for h, b in zip(heads, boxes):
        ok = matched_heads(h, b, head_fraction, head_point)
        for key, sel in zip(region, (h[:, 1] < 1 / 3, (h[:, 1] >= 1 / 3) & (h[:, 1] < 2 / 3), h[:, 1] >= 2 / 3)):
            region[key][0] += int(ok[sel].sum())
            region[key][1] += int(sel.sum())
    total_heads, total_boxes = int(gt_count.sum()), int(det.sum())
    lo, hi = sorted([m[head_fraction - 0.1], m[head_fraction + 0.1]])
    return {
        "frames": int(len(det)), "annotated_people": total_heads, "detected_boxes": total_boxes,
        "count_mae": round(float(np.abs(err).mean()), 2), "count_bias": round(float(err.mean()), 2),
        "share_found": round(total_boxes / total_heads, 3), "pearson_r": round(float(np.corrcoef(det, gt_count)[0, 1]), 3),
        "mae_by_crowd_size": {k: {"frames": int(v.sum()), "annotated_range": [int(gt_count[v].min()), int(gt_count[v].max())], "mae": round(float(np.abs(err[v]).mean()), 2), "share_found": round(float(det[v].sum() / gt_count[v].sum()), 3)} for k, v in bands.items()},
        "matched": m[head_fraction], "precision": round(m[head_fraction] / max(total_boxes, 1), 3), "recall": round(m[head_fraction] / total_heads, 3),
        "recall_range_head_fraction_pm_0.1": [round(lo / total_heads, 3), round(hi / total_heads, 3)],
        "precision_range_head_fraction_pm_0.1": [round(lo / max(total_boxes, 1), 3), round(hi / max(total_boxes, 1), 3)],
        "recall_by_image_region": {k: {"heads": n, "recall": round(hit / n, 3) if n else None} for k, (hit, n) in region.items()},
        "median_latency_ms_on_mac": round(float(counts["latency_ms"].iloc[1:].median()), 1),
    }


def calibration(gt_count: np.ndarray, counts: pd.DataFrame) -> dict:
    """Post-hoc: linear per-camera calibration fitted on frames 1-800, scored on frames 801-2000."""
    det = counts["person_count"].to_numpy().astype(float)
    test = np.arange(800, N_FRAMES)
    out = {"held_out_frames": "801-2000", "raw_mae_held_out": round(float(np.abs(det[test] - gt_count[test]).mean()), 2)}
    for label, fit in (("20 frames spread over 1-800", np.arange(0, 800, 40)), ("all frames 1-800", np.arange(800))):
        a, b = np.polyfit(det[fit], gt_count[fit], 1)
        pred = a * det[test] + b
        out[label] = {"a": round(float(a), 3), "b": round(float(b), 2), "mae_held_out": round(float(np.abs(pred - gt_count[test]).mean()), 2),
                      "bias_held_out": round(float((pred - gt_count[test]).mean()), 2)}
    return out


def figures(gt_count: np.ndarray, runs: dict, out: Path) -> None:
    t = np.arange(1, N_FRAMES + 1)
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(t, gt_count, color=INK, lw=1.2, label="annotated people (ground truth)")
    for i, (name, (counts, _)) in enumerate(runs.items()):
        ax.plot(t, counts["person_count"], color=SERIES[i], lw=0.9, alpha=0.9, label=DETECTORS[name][0])
    ax.set_xlabel("frame (Mall dataset, 2,000 frames)")
    ax.set_ylabel("people per frame")
    ax.set_title("People counted by the app's detectors vs annotated people", loc="left", color=INK)
    ax.set_ylim(0, gt_count.max() * 1.3)
    ax.legend(loc="upper right", ncol=3, fontsize=8)
    fig.tight_layout()
    fig.savefig(out / "mall_count_timeline.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    lim = [0, max(gt_count.max(), max(c["person_count"].max() for c, _ in runs.values())) + 3]
    ax.plot(lim, lim, color=INK2, lw=0.8, ls="--", label="perfect count")
    for i, (name, (counts, _)) in enumerate(runs.items()):
        ax.scatter(gt_count, counts["person_count"], s=5, alpha=0.25, color=SERIES[i], label=DETECTORS[name][0], linewidths=0)
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("annotated people in frame")
    ax.set_ylabel("people counted by detector")
    ax.legend(fontsize=8, loc="upper left", markerscale=3)
    fig.tight_layout()
    fig.savefig(out / "mall_count_scatter.png", dpi=160)
    plt.close(fig)


def summary_markdown(meta: dict, results: dict) -> str:
    """The committed summary, generated from the metrics so the text cannot drift from them."""
    g = meta["annotated_people_per_frame"]
    lines = [
        "# Mall dataset: person-counting accuracy of the app's detectors",
        "",
        f"Generated by `experiments/mall_eval.py` from `metrics.json`. Data: {meta['dataset']} (not redistributed here). "
        f"{meta['frames']:,} frames from a shopping-mall webcam, 640x480, {g['min']}-{g['max']} annotated people per frame (mean {g['mean']}). "
        "Detections come from the sensor app's own code run on the frames without re-encoding, at the app's shipped settings.",
        "",
        "| detector | share of people counted | count error per frame (MAE) | correlation with true count | boxes that are a person (precision) | people with a box (recall) | recall: near third / middle / far third of image | median latency on Mac |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name, r in results.items():
        reg = list(r["recall_by_image_region"].values())
        lines.append(f"| {DETECTORS[name][0]} | {r['share_found']:.0%} | {r['count_mae']} (bias {r['count_bias']:+}) | {r['pearson_r']} | {r['precision']:.0%} | {r['recall']:.0%} (range {r['recall_range_head_fraction_pm_0.1'][0]:.0%}-{r['recall_range_head_fraction_pm_0.1'][1]:.0%}) | {reg[2]['recall']:.0%} / {reg[1]['recall']:.0%} / {reg[0]['recall']:.0%} | {r['median_latency_ms_on_mac']} ms |")
    lines += ["", "By crowd size (annotated people per frame, thirds of the frames):", "",
              "| detector | " + " | ".join(f"{k} ({v['annotated_range'][0]}-{v['annotated_range'][1]} people)" for k, v in next(iter(results.values()))["mae_by_crowd_size"].items()) + " |",
              "|---|---|---|---|"]
    for name, r in results.items():
        lines.append(f"| {DETECTORS[name][0]} | " + " | ".join(f"{v['share_found']:.0%} counted, MAE {v['mae']}" for v in r["mae_by_crowd_size"].values()) + " |")
    lines += ["", "**Post-hoc follow-up** (added after seeing the under-count above): per-camera linear calibration, annotated ≈ a × detected + b, "
              "fitted on frames 1-800 only and scored on the held-out frames 801-2000.", "",
              "| detector | raw MAE on frames 801-2000 | calibrated on 20 labelled frames | calibrated on 800 labelled frames |", "|---|---|---|---|"]
    for name, r in results.items():
        c = r["post_hoc_linear_calibration"]
        f20, f800 = c["20 frames spread over 1-800"], c["all frames 1-800"]
        lines.append(f"| {DETECTORS[name][0]} | {c['raw_mae_held_out']} | {f20['mae_held_out']} (a = {f20['a']}, b = {f20['b']}) | {f800['mae_held_out']} (a = {f800['a']}, b = {f800['b']}) |")
    lines += ["", f"Matching rule: {meta['matching_rule']}; head fraction {meta['head_fraction']} (recall range: ±0.1).",
              "Charts: `mall_count_timeline.png`, `mall_count_scatter.png`. An annotated example frame is written to the git-ignored dataset folder only.", ""]
    return "\n".join(lines)


def example_overlay(mall: Path, heads: list[np.ndarray], runs: dict, frame: int = 970) -> Path:
    """Annotated example frame (dataset imagery): written to the git-ignored dataset folder only."""
    img = plt.imread(mall / "mall_dataset" / "frames" / f"seq_{frame:06d}.jpg")
    fig, axes = plt.subplots(1, len(runs), figsize=(6 * len(runs), 4.6))
    for ax, (i, (name, (_, boxes))) in zip(np.atleast_1d(axes), enumerate(runs.items())):
        ax.imshow(img)
        for x0, y0, bw, bh in boxes[frame - 1]:
            ax.add_patch(plt.Rectangle((x0 * W, y0 * H), bw * W, bh * H, fill=False, color=SERIES[i], lw=1.2))
        h = heads[frame - 1]
        ax.scatter(h[:, 0] * W, h[:, 1] * H, s=10, color="#ffffff", edgecolors=INK, linewidths=0.6)
        ax.set_title(f"{DETECTORS[name][0]}: {len(boxes[frame - 1])} boxes · {len(h)} annotated heads (dots)", fontsize=9, loc="left")
        ax.axis("off")
    fig.tight_layout()
    path = mall / "figures" / f"overlay_frame_{frame}.png"
    path.parent.mkdir(exist_ok=True)
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mall", type=Path, required=True, help="folder holding mall_dataset/ and runs/")
    ap.add_argument("--out", type=Path, required=True, help="where to write metrics.json, summary.md and charts")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    gt_count, heads = load_ground_truth(args.mall)
    runs = {name: load_run(args.mall, name) for name in DETECTORS}
    results = {name: evaluate(gt_count, heads, *runs[name], DETECTORS[name][1], DETECTORS[name][2]) for name in DETECTORS}
    for name in DETECTORS:
        results[name]["post_hoc_linear_calibration"] = calibration(gt_count, runs[name][0])
    meta = {"dataset": "Mall dataset (Chen, Loy, Gong & Xiang, BMVC 2012), CUHK, research use only", "frames": N_FRAMES,
            "annotated_people_per_frame": {"min": int(gt_count.min()), "mean": round(float(gt_count.mean()), 1), "max": int(gt_count.max())},
            "settings": {"yolo11n": "confidence 0.25, IoU 0.7 (app default)", "apple_upper": "VNDetectHumanRectanglesRequest upperBodyOnly (app fallback)"},
            "matching_rule": f"head inside box widened by {MARGIN:.0%} of width per side, from {ABOVE:.0%} of height above the top to HEAD_FRACTION of height below it; one-to-one assignment by distance to the expected head point",
            "head_fraction": {k: v[1] for k, v in DETECTORS.items()}}
    (args.out / "metrics.json").write_text(json.dumps({"meta": meta, "results": results}, indent=2) + "\n")
    (args.out / "summary.md").write_text(summary_markdown(meta, results))
    figures(gt_count, runs, args.out)
    overlay = example_overlay(args.mall, heads, runs)
    pd.DataFrame({"frame": np.arange(1, N_FRAMES + 1), "annotated": gt_count, **{n: runs[n][0]["person_count"].to_numpy() for n in DETECTORS}}).to_csv(args.mall / "runs" / "per_frame.csv", index=False)
    print(json.dumps(results, indent=2))
    print(f"example overlay (not committed): {overlay}")


if __name__ == "__main__":
    main()
