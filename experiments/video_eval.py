"""Compare the vision pipeline's per-frame person counts with manual ground truth on a
pre-recorded video, for several detector/resolution variants, and produce figures + a
summary table for the presentation. Nothing here is synthetic: counts come from Apple
Vision running on the clip, ground truth from a human counting sampled frames.

Reproduce (see also experiments/datasets/video/README.md):
    curl -L -o experiments/datasets/video/yonge_dundas_raw.webm \
        https://upload.wikimedia.org/wikipedia/commons/d/d2/DiagonalCrosswalkYongeDundas.webm
    ffmpeg -i .../yonge_dundas_raw.webm -vf "scale=640:-2,fps=10"  -an -c:v libx264 -crf 26 -pix_fmt yuv420p .../yonge_dundas_640_10fps.mp4
    ffmpeg -i .../yonge_dundas_raw.webm -vf "scale=1280:-2,fps=10" -an -c:v libx264 -crf 26 -pix_fmt yuv420p .../yonge_dundas_1280_10fps.mp4
    ffmpeg -i .../yonge_dundas_640_10fps.mp4 -vf fps=1/5 .../frames/frame_%03d.png     # count by hand -> ground_truth.csv
    cd ios/CrowdPulseSensor && swiftc -O -o /tmp/videoeval Tools/videoeval/main.swift Sources/Services/VisionProcessor.swift \
        Sources/Services/FlowEstimator.swift Sources/Models/SensorObservation.swift Tools/videoeval/Shims.swift
    /tmp/videoeval .../yonge_dundas_640_10fps.mp4  --out .../counts_640_upper.csv
    /tmp/videoeval .../yonge_dundas_640_10fps.mp4  --out .../counts_640_full.csv  --full-body
    /tmp/videoeval .../yonge_dundas_1280_10fps.mp4 --out .../counts_1280_upper.csv
    /tmp/videoeval .../yonge_dundas_1280_10fps.mp4 --out .../counts_1280_full.csv --full-body
    .venv/bin/python experiments/video_eval.py
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

SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
INK2, GRID = "#52514e", "#e6e5e1"
plt.rcParams.update({"figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.grid": True, "grid.color": GRID, "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.labelcolor": INK2, "legend.frameon": False})

VARIANTS = [("640px, upper-body (app default)", "counts_640_upper.csv"), ("640px, full-body", "counts_640_full.csv"), ("1280px, upper-body", "counts_1280_upper.csv"), ("1280px, full-body", "counts_1280_full.csv")]


def score(counts: pd.DataFrame, truth: pd.DataFrame, column: str, window: float) -> tuple[pd.DataFrame, dict]:
    rows = []
    for _, g in truth.iterrows():
        m = counts[(counts["t_sec"] >= g["t_sec"] - window) & (counts["t_sec"] <= g["t_sec"] + window)]
        if m.empty:
            continue
        rows.append({"t_sec": g["t_sec"], "actual": int(g[column]), "estimated": float(m["person_count"].mean())})
    df = pd.DataFrame(rows)
    err = df["estimated"] - df["actual"]
    s = {"n": int(len(df)), "mae": float(err.abs().mean()), "bias": float(err.mean()), "detected_fraction_pct": float(df["estimated"].sum() / max(1, df["actual"].sum()) * 100),
         "pearson_r": float(np.corrcoef(df["actual"], df["estimated"])[0, 1]) if len(df) > 2 else None, "actual_range": [int(df["actual"].min()), int(df["actual"].max())]}
    return df, s


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", default="experiments/datasets/video")
    ap.add_argument("--out", default="experiments/results/video")
    ap.add_argument("--window", type=float, default=0.5)
    args = ap.parse_args()
    data, out = Path(args.data), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    truth = pd.read_csv(data / "ground_truth.csv")
    summary: dict[str, dict] = {}
    fig, axes = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
    for col, ax, title in [("near_count", axes[0], "near field: people on the crossing / within ~15 m (intended deployment range)"), ("actual_count", axes[1], "whole frame incl. far sidewalk ~50 m away (out of design range)")]:
        ax.plot(truth["t_sec"], truth[col], "o-", color="#0b0b0b", lw=1.5, ms=6, label="manual ground truth (every 5 s)")
        for i, (label, fname) in enumerate(VARIANTS):
            p = data / fname
            if not p.exists():
                continue
            counts = pd.read_csv(p)
            df, s = score(counts, truth, col, args.window)
            s["latency_ms_mean"] = float(counts["latency_ms"].median())
            summary.setdefault(label, {})[col] = s
            ax.plot(counts["t_sec"], counts["person_count"], color=SERIES[i], lw=1.1, alpha=0.9, label=f"{label}: MAE {s['mae']:.1f}, detects {s['detected_fraction_pct']:.0f}%")
        ax.set_ylabel("people"); ax.set_title(title, fontsize=10); ax.legend(fontsize=8, loc="upper left")
    axes[1].set_xlabel("video time (s)")
    fig.suptitle("Pre-recorded CC0 crossing video: Apple Vision person counts vs manual ground truth", fontsize=12, fontweight="semibold")
    fig.tight_layout(); fig.savefig(out / "video_count_accuracy.png", dpi=160)
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["| variant | median latency (ms) | near-field MAE | near-field detected % | near-field r | whole-frame MAE | whole-frame detected % |", "|---|---|---|---|---|---|---|"]
    for label, d in summary.items():
        n, a = d["near_count"], d["actual_count"]
        lines.append(f"| {label} | {n['latency_ms_mean']:.1f} | {n['mae']:.1f} | {n['detected_fraction_pct']:.0f}% | {n['pearson_r']:.2f} | {a['mae']:.1f} | {a['detected_fraction_pct']:.0f}% |")
    (out / "summary.md").write_text("# Video count evaluation\n\nGround truth: 11 frames counted by hand (every 5 s). Near field = people on the crossing within ~15 m of the camera; whole frame also includes the far sidewalk (~50 m).\n\n" + "\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
