"""Reproducible evaluation: turns the artifacts written by ``ml.training.train``
into presentation figures + a metrics table. Nothing here is fabricated: every
number is read from ``ml/models/metrics.json`` / ``test_predictions.csv.gz``.

    python -m ml.evaluation.evaluate --models ml/models --out experiments/results
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from shared.config import CLASSES, load_config, load_zone_graph  # noqa: E402

# Validated palette (dataviz reference instance). Status colours are reserved for classes.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#4a3aa7", "#e34948"]
STATUS = {"SAFE": "#0ca30c", "WARNING": "#fab219", "CRITICAL": "#d03b3b"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e6e5e1"

plt.rcParams.update({
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "axes.edgecolor": GRID, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 10, "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.titleweight": "semibold", "axes.titlesize": 11, "legend.frameon": False,
})


def fig_confusion(metrics: dict, out: Path) -> None:
    hs = list(metrics["per_horizon"].keys())
    fig, axes = plt.subplots(1, len(hs), figsize=(4.2 * len(hs), 4))
    for ax, h in zip(np.atleast_1d(axes), hs):
        cm = np.array(metrics["per_horizon"][h]["test"]["confusion_matrix"], dtype=float)
        norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
        ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
        ax.grid(False)
        ax.set_xticks(range(3), CLASSES); ax.set_yticks(range(3), CLASSES)
        ax.set_xlabel("predicted"); ax.set_ylabel("actual (observed future state)")
        m = metrics["per_horizon"][h]["test"]
        ax.set_title(f"+{h[1:]} min  acc {m['accuracy']:.3f}  F1 {m['f1_macro']:.3f}")
        for i in range(3):
            for j in range(3):
                ax.text(j, i, f"{int(cm[i, j])}\n{norm[i, j]:.2f}", ha="center", va="center", color="white" if norm[i, j] > 0.5 else INK, fontsize=9)
    fig.suptitle("Congestion classification: confusion matrices (held-out test days)", fontsize=12, fontweight="semibold")
    fig.tight_layout(); fig.savefig(out / "confusion_matrix.png", dpi=160); plt.close(fig)


def fig_model_comparison(metrics: dict, out: Path) -> None:
    hs = list(metrics["per_horizon"].keys())
    names = list(metrics["per_horizon"][hs[0]]["model_comparison"].keys()) + ["persistence baseline"]
    fig, ax = plt.subplots(figsize=(8, 4))
    w = 0.8 / len(names)
    for i, name in enumerate(names):
        vals = []
        for h in hs:
            ph = metrics["per_horizon"][h]
            vals.append(ph["persistence_baseline"]["test"]["f1_macro"] if name == "persistence baseline" else ph["model_comparison"][name]["test"]["f1_macro"])
        x = np.arange(len(hs)) + (i - len(names) / 2 + 0.5) * w
        bars = ax.bar(x, vals, width=w * 0.92, color=SERIES[i] if name != "persistence baseline" else "#9a9891", label=name.replace("_", " "))
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", va="bottom", fontsize=8, color=INK2)
    ax.set_xticks(range(len(hs)), [f"+{h[1:]} min" for h in hs])
    ax.set_ylim(0, 1.05); ax.set_ylabel("macro F1 (test)")
    ax.set_title("Model comparison per forecast horizon (higher is better)")
    ax.legend(ncol=2, loc="lower left")
    fig.tight_layout(); fig.savefig(out / "model_comparison.png", dpi=160); plt.close(fig)


def fig_prediction_timeline(pred: pd.DataFrame, out: Path, zone: str = "senado_square", horizon: int = 15) -> str:
    graph = load_zone_graph()
    names = {z["id"]: z["name"] for z in graph["zones"]}
    p = pred[(pred["horizon"] == horizon) & (pred["zone_id"] == zone)].copy()
    day = sorted(p["local_date"].unique())[-1]
    p = p[p["local_date"] == day].sort_values("bin_start")
    p["bin_start"] = pd.to_datetime(p["bin_start"], utc=True)
    t = p["bin_start"] + pd.Timedelta(hours=8)
    t_target = t + pd.Timedelta(minutes=horizon)
    cfg = load_config()
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11, 6.2), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    ax.plot(t, p["density_true_future"].shift(0) if False else p["density"], color=SERIES[0], lw=2, label="observed density (sensors)")
    ax.plot(t_target, p["density_pred"], color=SERIES[1], lw=2, ls="--", label=f"predicted density (+{horizon} min, plotted at target time)")
    ax.plot(t_target, p["density_true_future"], color=INK2, lw=1, alpha=0.6, label="simulation ground truth")
    th = cfg["congestion_thresholds"]
    ax.axhline(th["warning"], color=STATUS["WARNING"], lw=1, ls=":"); ax.axhline(th["critical"], color=STATUS["CRITICAL"], lw=1, ls=":")
    ax.text(t.iloc[0], th["warning"] + 0.01, "WARNING threshold", color=INK2, fontsize=8)
    ax.text(t.iloc[0], th["critical"] + 0.01, "CRITICAL threshold", color=INK2, fontsize=8)
    ax.set_ylim(0, 1.05); ax.set_ylabel("relative density index (0-1)")
    ax.set_title(f"{names.get(zone, zone)} on {day}: observed vs predicted density, +{horizon} min ahead")
    ax.legend(loc="upper left", fontsize=8)
    # class strip: predicted vs actual
    for i, (col, lab) in enumerate([("y_pred", "predicted"), ("y_obs", "actual")]):
        for cls in CLASSES:
            m = (p[col] == cls).to_numpy()
            ax2.fill_between(t_target, i, i + 0.9, where=m, color=STATUS[cls], step="post", linewidth=0)
    ax2.plot(t_target, 2.05 + p["confidence"] * 0.9, color=INK, lw=1)
    ax2.axhline(2.05 + cfg["confidence"]["low_confidence_threshold"] * 0.9, color=STATUS["CRITICAL"], lw=0.8, ls=":")
    ax2.set_yticks([0.45, 1.45, 2.5], ["predicted class", "actual class", "confidence"])
    ax2.set_ylim(0, 3.05); ax2.grid(False)
    ax2.set_xlabel("local time (Macau, UTC+8)")
    acc = float((p["y_pred"] == p["y_obs"]).mean())
    ax2.set_title(f"class agreement on this day: {acc:.1%}   (green SAFE, yellow WARNING, red CRITICAL; dotted = low-confidence threshold)", fontsize=9)
    fig.autofmt_xdate()
    fig.tight_layout(); fig.savefig(out / "prediction_timeline.png", dpi=160); plt.close(fig)
    return day


def fig_density_timeline(pred: pd.DataFrame, out: Path, day: str) -> None:
    graph = load_zone_graph()
    names = {z["id"]: z["name"] for z in graph["zones"]}
    p = pred[(pred["horizon"] == 5) & (pred["local_date"] == day)].copy()
    p["t"] = pd.to_datetime(p["bin_start"], utc=True) + pd.Timedelta(hours=8)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    for i, (z, g) in enumerate(p.groupby("zone_id")):
        g = g.sort_values("t")
        ax.plot(g["t"], g["density"], color=SERIES[i % len(SERIES)], lw=1.6, label=names.get(z, z))
        ax.text(g["t"].iloc[-1], g["density"].iloc[-1], " " + names.get(z, z).split(" (")[0], color=INK2, fontsize=7, va="center")
    ax.set_ylim(0, 1.05); ax.set_ylabel("observed relative density index")
    ax.set_xlabel("local time (Macau, UTC+8)")
    ax.set_title(f"Crowd-density timeline for all zones, {day} (aggregated sensor observations)")
    ax.legend(fontsize=7, ncol=4, loc="upper left")
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "density_timeline.png", dpi=160); plt.close(fig)


def fig_reliability(pred: pd.DataFrame, out: Path, day: str) -> None:
    graph = load_zone_graph()
    names = {z["id"]: z["name"] for z in graph["zones"]}
    p = pred[(pred["horizon"] == 5) & (pred["local_date"] == day)].copy()
    p["t"] = pd.to_datetime(p["bin_start"], utc=True) + pd.Timedelta(hours=8)
    fig, ax = plt.subplots(figsize=(11, 3.8))
    for i, (z, g) in enumerate(p.groupby("zone_id")):
        g = g.sort_values("t")
        ax.plot(g["t"], g["reliability"], color=SERIES[i % len(SERIES)], lw=1.2, label=names.get(z, z).split(" (")[0])
    ax.set_ylim(0, 1.05); ax.set_ylabel("zone sensor reliability (0-1)")
    ax.set_xlabel("local time (Macau, UTC+8)")
    ax.set_title(f"Sensor reliability per zone, {day}: dips = dropout, obstruction, device movement or weak GPS")
    ax.legend(fontsize=7, ncol=4, loc="lower left")
    fig.autofmt_xdate(); fig.tight_layout(); fig.savefig(out / "sensor_reliability.png", dpi=160); plt.close(fig)


def fig_calibration_and_gating(pred: pd.DataFrame, metrics: dict, out: Path) -> None:
    cfg = load_config()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(10, 4))
    for i, h in enumerate(sorted(pred["horizon"].unique())):
        p = pred[pred["horizon"] == h]
        conf = p["confidence"].to_numpy(); correct = (p["y_pred"] == p["y_obs"]).to_numpy()
        bins = np.linspace(0.3, 1.0, 8)
        xs, ys, ns = [], [], []
        for lo, hi in zip(bins[:-1], bins[1:]):
            m = (conf > lo) & (conf <= hi)
            if m.sum() >= 20:
                xs.append(conf[m].mean()); ys.append(correct[m].mean()); ns.append(m.sum())
        ax.plot(xs, ys, marker="o", ms=5, lw=1.6, color=SERIES[i], label=f"+{h} min (ECE {metrics['per_horizon'][f'h{h}']['test']['ece']:.3f})")
    ax.plot([0.3, 1], [0.3, 1], color=INK2, lw=1, ls=":")
    ax.set_xlabel("stated confidence (max class probability)"); ax.set_ylabel("observed accuracy")
    ax.set_title("Calibration: is 80% confidence right 80% of the time?"); ax.legend(fontsize=8)
    thr = cfg["confidence"]["low_confidence_threshold"]
    hs = list(metrics["per_horizon"].keys())
    conf_acc = [metrics["per_horizon"][h]["confidence_gating"]["accuracy_confident"] for h in hs]
    flag_acc = [metrics["per_horizon"][h]["confidence_gating"]["accuracy_flagged"] or 0 for h in hs]
    flag_frac = [metrics["per_horizon"][h]["confidence_gating"]["fraction_flagged"] for h in hs]
    x = np.arange(len(hs))
    b1 = ax2.bar(x - 0.2, conf_acc, 0.38, color=SERIES[0], label=f"confidence >= {thr:.0%}")
    b2 = ax2.bar(x + 0.2, flag_acc, 0.38, color="#9a9891", label="flagged: HUMAN REVIEW REQUIRED")
    for b, v in list(zip(b1, conf_acc)) + list(zip(b2, flag_acc)):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=8, color=INK2)
    ax2.set_xticks(x, [f"+{h[1:]} min\n({f:.1%} flagged)" for h, f in zip(hs, flag_frac)]); ax2.set_ylim(0, 1.25); ax2.set_ylabel("accuracy")
    ax2.set_title("Low-confidence gating protects operators"); ax2.legend(fontsize=8, loc="upper left", ncol=1)
    fig.tight_layout(); fig.savefig(out / "calibration_and_gating.png", dpi=160); plt.close(fig)


def fig_stress(metrics: dict, out: Path) -> None:
    hs = list(metrics["per_horizon"].keys())
    if not metrics["per_horizon"][hs[0]].get("stress_scenario"):
        return
    fig, ax = plt.subplots(figsize=(8, 4))
    x = np.arange(len(hs))
    t_acc = [metrics["per_horizon"][h]["test"]["f1_macro"] for h in hs]
    s_acc = [metrics["per_horizon"][h]["stress_scenario"]["f1_macro"] for h in hs]
    t_ood = [metrics["per_horizon"][h]["stress_scenario"]["ood_flag_rate_test"] for h in hs]
    s_ood = [metrics["per_horizon"][h]["stress_scenario"]["ood_flag_rate"] for h in hs]
    for off, vals, col, lab in [(-0.3, t_acc, SERIES[0], "macro F1: normal test days"), (-0.1, s_acc, SERIES[1], "macro F1: rain + closure + surge day"), (0.1, t_ood, "#9a9891", "OOD flag rate: normal test days"), (0.3, s_ood, "#4a3aa7", "OOD flag rate: stress day")]:
        bars = ax.bar(x + off, vals, 0.19, color=col, label=lab)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center", fontsize=7, color=INK2)
    ax.set_xticks(x, [f"+{h[1:]} min" for h in hs]); ax.set_ylim(0, 1.1)
    ax.set_title("Failure case: unusual conditions degrade accuracy, and the OOD detector notices")
    ax.legend(fontsize=7, ncol=2, loc="upper right")
    fig.tight_layout(); fig.savefig(out / "stress_scenario.png", dpi=160); plt.close(fig)


def metrics_table(metrics: dict) -> str:
    lines = ["| horizon | model | accuracy | precision (macro) | recall (macro) | F1 (macro) | ROC-AUC (ovr) | ECE | persistence F1 | acc vs ground truth | density MAE | stress-day F1 |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for h, v in metrics["per_horizon"].items():
        t = v["test"]; s = v.get("stress_scenario") or {}
        lines.append(f"| +{h[1:]} min | {v['chosen_model']} | {t['accuracy']:.3f} | {t['precision_macro']:.3f} | {t['recall_macro']:.3f} | {t['f1_macro']:.3f} | {t.get('roc_auc_ovr_macro') or float('nan'):.3f} | {t.get('ece', float('nan')):.3f} | {v['persistence_baseline']['test']['f1_macro']:.3f} | {(v.get('test_vs_ground_truth') or {}).get('accuracy', float('nan')):.3f} | {v['density_regression']['mae_vs_observed']:.3f} | {s.get('f1_macro', float('nan')):.3f} |")
    lines.append("")
    lines.append("Per-class (test):")
    lines.append("")
    lines.append("| horizon | class | precision | recall | F1 | support |")
    lines.append("|---|---|---|---|---|---|")
    for h, v in metrics["per_horizon"].items():
        for c in CLASSES:
            pc = v["test"]["per_class"][c]
            lines.append(f"| +{h[1:]} min | {c} | {pc['precision']:.3f} | {pc['recall']:.3f} | {pc['f1']:.3f} | {v['test']['support'][c]} |")
    return "\n".join(lines)


def run(models_dir: Path, out_root: Path) -> Path:
    metrics = json.loads((models_dir / "metrics.json").read_text())
    pred = pd.read_csv(models_dir / "test_predictions.csv.gz")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = out_root / stamp
    out.mkdir(parents=True, exist_ok=True)
    fig_confusion(metrics, out)
    fig_model_comparison(metrics, out)
    day = fig_prediction_timeline(pred, out)
    fig_density_timeline(pred, out, day)
    fig_reliability(pred, out, day)
    fig_calibration_and_gating(pred, metrics, out)
    fig_stress(metrics, out)
    (out / "metrics_table.md").write_text(f"# CrowdPulse evaluation ({stamp})\n\nModel version: {metrics['model_version']}  \nTrained: {metrics['trained_at']}  \nSplit days: {json.dumps(metrics['split_days'])}  \nRows: {json.dumps(metrics['rows'])}\n\n" + metrics_table(metrics) + "\n")
    shutil.copy(models_dir / "metrics.json", out / "metrics.json")
    latest = out_root / "latest"
    if latest.exists():
        shutil.rmtree(latest)
    shutil.copytree(out, latest)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="ml/models")
    ap.add_argument("--out", default="experiments/results")
    args = ap.parse_args()
    out = run(Path(args.models), Path(args.out))
    print("wrote", out)
    print((out / "metrics_table.md").read_text())


if __name__ == "__main__":
    main()
