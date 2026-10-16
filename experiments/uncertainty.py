"""Uncertainty intervals and stronger baselines for CrowdPulse's headline numbers.

The headline forecast numbers (ml/models/metrics.json: +15 min macro-F1 0.865 vs persistence 0.795,
accuracy 0.964 vs 0.943) are single point estimates on three simulated test days. This script puts
95% intervals on them, adds the baselines a sceptical judge would ask for, and re-reads the Mall
calibration result against a detector-free guess. It does not retrain or change any model: every
forecast number comes from the committed ml/models/test_predictions.csv.gz (one row per zone, minute
and horizon on the test days 2026-09-27, 2026-09-30 and 2026-10-04 of the synthetic simulation).

Analysis choices (made by the authors of this script, not pre-registered):
1. Block bootstrap (10,000 resamples, seed 0, percentile 95% intervals). Neighbouring minutes of one
   zone are strongly correlated, so whole blocks are resampled, never single minutes. Primary block =
   one zone on one test day (7 zones x 3 days = 21 blocks). Sensitivity: all zones in one local hour
   of one day (42 blocks; keeps zones that share a street together) and one zone in one local hour
   (294 blocks). Model and baselines are scored on the same resampled blocks (paired), so the gain
   interval accounts for their shared ups and downs.
2. Accuracy of the model, of persistence (future class = current class) and of always answering SAFE
   (the majority class); its accuracy is the SAFE share of the supports.
3. Per test day: macro-F1 of model and persistence, and how many zone-minutes were CRITICAL. Per day,
   macro-F1 averages over the classes that occur as targets that day; this is a reporting choice
   (one test day has no CRITICAL target, which caps the 3-class value at 2/3), so the 3-class value
   is stored too. Per-day intervals use zone-hour blocks, the finest grouping of item 1.
4. Forecasts flagged for review. Two definitions: (a) "flagged as uncertain by the model": model
   confidence (max class probability) < low_confidence_threshold (0.6, shared/config.json), which is
   what metrics.json reports; (b) the live backend's "HUMAN REVIEW REQUIRED" rule
   (backend/app/services/prediction.py):
   effective confidence = confidence x clip(0.4 + 0.6 x reliability) x 0.7 if out-of-distribution,
   flagged below 0.6, and no forecast at all when reliability < 0.25. For (b) only the isolation-forest
   part of the OOD check can be recomputed (the feature-range part needs features that
   test_predictions does not store), so (b)'s flag counts and shares are lower bounds. Accuracy of
   flagged and unflagged forecasts gets a Wilson 95% interval (assumes independent forecasts) and a
   zone-day block bootstrap interval (does not).
5. Moving-average persistence: class of the mean density over the last 3 or 5 one-minute bins of the
   same zone (the bins present in test_predictions; a window with gaps averages the bins it has),
   labelled with the same thresholds as everything else (shared/config.json).
6. Mall dataset (only if the research-only annotations are present locally in
   experiments/datasets/mall/, never committed): held-out (frames 801-2000) MAE of predicting the mean
   annotated count of the same 20 calibration frames that experiments/mall_eval.py uses, for every
   frame, i.e. without any detector. Intervals: bootstrap over 24 blocks of 50 consecutive frames.

All of this is simulation data (except item 6): the intervals describe resampling variation within
three simulated days, not the gap between the simulator and a real street.

Stored values are unrounded; summary.md rounds each figure once, only when it prints it.

    .venv/bin/python -I experiments/uncertainty.py

Writes experiments/results/uncertainty/metrics.json and summary.md (aggregates only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CLASSES = ["SAFE", "WARNING", "CRITICAL"]
SEED = 0
N_BOOT = 10_000
Z95 = 1.959963984540054
MACAU_UTC_OFFSET_H = 8
BLOCK_SCHEMES = {  # name -> (columns that define a block, plain description)
    "zone_day": (["zone_id", "local_date"], "one zone on one test day"),
    "day_hour": (["local_date", "local_hour"], "all zones in one local hour of one day"),
    "zone_hour": (["zone_id", "local_date", "local_hour"], "one zone in one local hour of one day"),
}
PRIMARY = "zone_day"
PREDICTORS = {  # name -> (column holding the predicted class, label)
    "model": ("y_pred", "model (shipped random forest)"),
    "persistence": ("current_state", "persistence (future = now)"),
    "ma3": ("pred_ma3", "3-min moving-average persistence"),
    "ma5": ("pred_ma5", "5-min moving-average persistence"),
    "always_safe": ("pred_safe", "always SAFE (majority class)"),
}
MALL_BLOCK = 50


# ---------------------------------------------------------------- helpers

def load_config() -> dict:
    return json.loads((REPO / "shared" / "config.json").read_text())


def classify(density: np.ndarray, warning: float, critical: float) -> np.ndarray:
    """Same rule as shared.config.congestion_class (density >= critical -> CRITICAL, >= warning -> WARNING)."""
    return np.where(density >= critical, "CRITICAL", np.where(density >= warning, "WARNING", "SAFE"))


def scores_from_cm(cm: np.ndarray, classes: list[int] | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Macro-F1 and accuracy from confusion matrices [..., true, pred] (sklearn's zero_division=0 rule).
    ``classes``: indices to average F1 over (default all three, as in metrics.json)."""
    tp = np.diagonal(cm, axis1=-2, axis2=-1)
    fp = cm.sum(axis=-2) - tp
    fn = cm.sum(axis=-1) - tp
    denom = 2 * tp + fp + fn
    f1 = np.divide(2 * tp, denom, out=np.zeros_like(denom, dtype=float), where=denom > 0)
    acc = tp.sum(axis=-1) / cm.sum(axis=(-2, -1))
    return f1[..., classes if classes is not None else slice(None)].mean(axis=-1), acc


def block_cms(true_idx: np.ndarray, pred_idx: np.ndarray, block: np.ndarray, n_blocks: int) -> np.ndarray:
    cm = np.zeros((n_blocks, 3, 3))
    np.add.at(cm, (block, true_idx, pred_idx), 1)
    return cm


def boot_weights(n_blocks: int, seed: int, n_boot: int = N_BOOT) -> np.ndarray:
    """How often each block is drawn in each resample (n_blocks draws with replacement)."""
    return np.random.default_rng(seed).multinomial(n_blocks, np.full(n_blocks, 1 / n_blocks), size=n_boot).astype(float)


def ci(samples: np.ndarray) -> list[float]:
    """Percentile 95% interval, unrounded (rounding happens only when summary.md prints it)."""
    lo, hi = np.percentile(samples, [2.5, 97.5])
    return [float(lo), float(hi)]


def wilson(k: int, n: int) -> list[float] | None:
    if n == 0:
        return None
    p = k / n
    centre = (p + Z95**2 / (2 * n)) / (1 + Z95**2 / n)
    half = Z95 * math.sqrt(p * (1 - p) / n + Z95**2 / (4 * n * n)) / (1 + Z95**2 / n)
    return [centre - half, centre + half]


def fl(x: float) -> float:
    """Plain float for JSON. Deliberately not rounded: every displayed figure is rounded once, from this value."""
    return float(x)


# ---------------------------------------------------------------- forecast data

def load_predictions(path: Path, cfg: dict) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["t"] = pd.to_datetime(df["bin_start"], utc=True)
    df["local_hour"] = (df["t"] + pd.Timedelta(hours=MACAU_UTC_OFFSET_H)).dt.hour
    th = cfg["congestion_thresholds"]
    # density is a property of (zone, minute): identical in every horizon's rows
    assert df.groupby(["zone_id", "t"])["density"].nunique().max() == 1, "density differs between horizons"
    assert (classify(df["density"].to_numpy(), th["warning"], th["critical"]) == df["current_state"].to_numpy()).all(), "current_state does not follow the thresholds"
    dens = df.drop_duplicates(["zone_id", "t"])[["zone_id", "t", "density"]]
    parts = []
    for zone, g in dens.groupby("zone_id"):
        s = g.set_index("t")["density"].sort_index()
        s = s.reindex(pd.date_range(s.index.min(), s.index.max(), freq="60s", tz="UTC"))
        part = pd.DataFrame({"zone_id": zone, "t": s.index})
        for k in (3, 5):
            part[f"ma{k}"] = s.rolling(k, min_periods=1).mean().to_numpy()  # mean of the bins present in the window
            part[f"full{k}"] = (s.notna().astype(int).rolling(k, min_periods=k).sum() == k).to_numpy()
        parts.append(part[s.notna().to_numpy()])
    df = df.merge(pd.concat(parts), on=["zone_id", "t"], how="left", validate="many_to_one")
    for k in (3, 5):
        df[f"pred_ma{k}"] = classify(df[f"ma{k}"].to_numpy(), th["warning"], th["critical"])
    df["pred_safe"] = "SAFE"
    for scheme, (cols, _) in BLOCK_SCHEMES.items():
        df[f"block_{scheme}"] = df.groupby(cols, sort=True).ngroup()
    return df


def headline(df: pd.DataFrame, horizons: list[int], published: dict) -> dict:
    """Items 1, 2 and 5: macro-F1 and accuracy with block-bootstrap intervals, paired gains."""
    out: dict = {}
    for scheme in BLOCK_SCHEMES:
        n_blocks = int(df[f"block_{scheme}"].max()) + 1
        w = boot_weights(n_blocks, SEED)
        res: dict = {"n_blocks": n_blocks, "per_horizon": {}}
        for h in horizons:
            g = df[df["horizon"] == h]
            true_idx = g["y_obs"].map(CLASSES.index).to_numpy()
            block = g[f"block_{scheme}"].to_numpy()
            f1s, accs, pts = {}, {}, {}
            for name, (col, _) in PREDICTORS.items():
                cm = block_cms(true_idx, g[col].map(CLASSES.index).to_numpy(), block, n_blocks)
                f1_pt, acc_pt = scores_from_cm(cm.sum(axis=0))
                f1s[name], accs[name] = scores_from_cm(np.einsum("bk,kij->bij", w, cm))
                pts[name] = {"f1_macro": fl(f1_pt), "accuracy": fl(acc_pt)}
            entry = {"n": int(len(g)), "support": {c: int((g["y_obs"] == c).sum()) for c in CLASSES}, "predictors": {}}
            for name in PREDICTORS:
                entry["predictors"][name] = {**pts[name], "f1_macro_ci95": ci(f1s[name]), "accuracy_ci95": ci(accs[name])}
            entry["gains"] = {}
            for base in ("persistence", "ma3", "ma5", "always_safe"):
                d_f1, d_acc = f1s["model"] - f1s[base], accs["model"] - accs[base]
                entry["gains"][f"model_minus_{base}"] = {
                    "f1_macro": fl(pts["model"]["f1_macro"] - pts[base]["f1_macro"]), "f1_macro_ci95": ci(d_f1),
                    "share_of_resamples_gain_le_0": fl((d_f1 <= 0).mean()),
                    "accuracy": fl(pts["model"]["accuracy"] - pts[base]["accuracy"]), "accuracy_ci95": ci(d_acc),
                }
            res["per_horizon"][f"h{h}"] = entry
        out[scheme] = res
    # point estimates must reproduce the published metrics exactly
    for h in horizons:
        e = out[PRIMARY]["per_horizon"][f"h{h}"]
        pub = published["per_horizon"][f"h{h}"]
        assert abs(e["predictors"]["model"]["f1_macro"] - pub["test"]["f1_macro"]) < 1e-4
        assert abs(e["predictors"]["persistence"]["f1_macro"] - pub["persistence_baseline"]["test"]["f1_macro"]) < 1e-4
        assert abs(e["predictors"]["model"]["accuracy"] - pub["test"]["accuracy"]) < 1e-4
        assert e["support"] == pub["test"]["support"], "supports differ from metrics.json"
        assert abs(e["predictors"]["always_safe"]["accuracy"] - pub["test"]["support"]["SAFE"] / pub["test"]["n"]) < 1e-4
    return out


def moving_average_coverage(df: pd.DataFrame, horizons: list[int]) -> dict:
    return {f"h{h}": {f"share_rows_full_{k}min_window": fl(df.loc[df["horizon"] == h, f"full{k}"].mean()) for k in (3, 5)} for h in horizons}


def per_day(df: pd.DataFrame, horizons: list[int]) -> dict:
    """Item 3: per-test-day macro-F1 (gain interval from zone-hour blocks inside that day).

    A day without a single CRITICAL target would get F1 = 0 for CRITICAL under the 3-class convention of
    metrics.json, capping its macro-F1 at 2/3. So per day the headline figure averages F1 over the classes
    that occur as targets that day (a reporting choice); the 3-class value is kept as f1_macro_3class.
    Zone-hour blocks are the finest grouping of the headline sensitivity check, so these intervals are
    likely optimistic."""
    out: dict = {}
    uniq = df.drop_duplicates(["zone_id", "t"])
    for d, gd in df.groupby("local_date"):
        u = uniq[uniq["local_date"] == d]
        crit_now = u[u["current_state"] == "CRITICAL"]
        day = {
            "weekday": pd.Timestamp(d).day_name(),
            "zone_minutes_observed": int(len(u)),
            "zone_minutes_critical_now": int(len(crit_now)),
            "minutes_with_any_zone_critical_now": int(crit_now["t"].nunique()),
            "zones_ever_critical": sorted(crit_now["zone_id"].unique().tolist()),
            "per_horizon": {},
        }
        for h in horizons:
            g = gd[gd["horizon"] == h]
            block = g.groupby(["zone_id", "local_hour"]).ngroup().to_numpy()
            n_blocks = int(block.max()) + 1
            w = boot_weights(n_blocks, SEED)
            true_idx = g["y_obs"].map(CLASSES.index).to_numpy()
            present = sorted(set(true_idx.tolist()))
            res = {"n": int(len(g)), "classes_present": [CLASSES[i] for i in present],
                   "target_zone_minutes_critical": int((g["y_obs"] == "CRITICAL").sum()),
                   "target_zone_minutes_warning": int((g["y_obs"] == "WARNING").sum())}
            reps = {}
            for name in ("model", "persistence", "ma3"):
                pred_idx = g[PREDICTORS[name][0]].map(CLASSES.index).to_numpy()
                cm = block_cms(true_idx, pred_idx, block, n_blocks)
                full = cm.sum(axis=0)
                f1, acc = scores_from_cm(full, present)
                f1_3 = scores_from_cm(full)[0]
                reps[name] = scores_from_cm(np.einsum("bk,kij->bij", w, cm), present)[0]
                crit_recall = full[2, 2] / full[2].sum() if full[2].sum() else None
                res[name] = {"f1_macro": fl(f1), "f1_macro_ci95": ci(reps[name]), "f1_macro_3class": fl(f1_3), "accuracy": fl(acc),
                             "critical_recall": None if crit_recall is None else fl(crit_recall),
                             "critical_forecasts": int(full[:, 2].sum()), "false_critical_forecasts": int(full[:2, 2].sum())}
            res["gain_f1_model_minus_persistence"] = fl(res["model"]["f1_macro"] - res["persistence"]["f1_macro"])
            res["gain_f1_model_minus_persistence_ci95"] = ci(reps["model"] - reps["persistence"])
            day["per_horizon"][f"h{h}"] = res
        out[d] = day
    return out


def review_flags(df: pd.DataFrame, horizons: list[int], cfg: dict, published: dict, ood_threshold: float | None) -> dict:
    """Item 4: forecasts flagged for human review, accuracy with Wilson and block-bootstrap intervals."""
    c = cfg["confidence"]
    thr = c["low_confidence_threshold"]
    out: dict = {"threshold": thr, "ood_threshold_isolation_forest": ood_threshold,
                 "live_rule": {"source": "backend/app/services/prediction.py", "ood_confidence_multiplier": c["ood_confidence_multiplier"],
                               "min_reliability_for_prediction": c["min_reliability_for_prediction"], "threshold": thr},
                 "per_horizon": {}}
    n_blocks = int(df[f"block_{PRIMARY}"].max()) + 1
    w = boot_weights(n_blocks, SEED)
    for h in horizons:
        g = df[df["horizon"] == h]
        correct = (g["y_pred"] == g["y_obs"]).to_numpy()
        block = g[f"block_{PRIMARY}"].to_numpy()

        def summarise(mask: np.ndarray) -> dict:
            k, n = int(correct[mask].sum()), int(mask.sum())
            nb = np.bincount(block[mask], minlength=n_blocks).astype(float)
            kb = np.bincount(block[mask], weights=correct[mask].astype(float), minlength=n_blocks)
            with np.errstate(invalid="ignore", divide="ignore"):
                reps = (w @ kb) / (w @ nb)
            reps = reps[np.isfinite(reps)]
            return {"n": n, "share_of_forecasts": fl(n / len(g)), "correct": k, "accuracy": fl(k / n) if n else None,
                    "accuracy_wilson95": wilson(k, n), "accuracy_block_bootstrap95": ci(reps) if len(reps) else None,
                    "per_block_n": {"blocks": n_blocks, "blocks_with_none": int((nb == 0).sum()), "min": int(nb.min()),
                                    "median": fl(np.median(nb)), "max": int(nb.max())},
                    "true_class_counts": {cl: int((g["y_obs"].to_numpy()[mask] == cl).sum()) for cl in CLASSES},
                    "predicted_class_counts": {cl: int((g["y_pred"].to_numpy()[mask] == cl).sum()) for cl in CLASSES}}

        conf = g["confidence"].to_numpy()
        flagged = conf < thr
        entry = {"training_report_rule": {"flagged": summarise(flagged), "not_flagged": summarise(~flagged)}}
        pub = published["per_horizon"][f"h{h}"]["confidence_gating"]
        assert abs(entry["training_report_rule"]["flagged"]["share_of_forecasts"] - pub["fraction_flagged"]) < 1e-4
        assert abs(entry["training_report_rule"]["flagged"]["accuracy"] - pub["accuracy_flagged"]) < 1e-4
        if ood_threshold is not None:
            rel = g["reliability"].to_numpy()
            ood = g["ood_score"].to_numpy() < ood_threshold
            stress = published["per_horizon"][f"h{h}"].get("stress_scenario") or {}
            if "ood_flag_rate_test" in stress:
                assert abs(ood.mean() - stress["ood_flag_rate_test"]) < 1e-6, "OOD flag rate differs from metrics.json"
            eff =conf * np.clip(0.4 + 0.6 * rel, 0, 1) * np.where(ood, c["ood_confidence_multiplier"], 1.0)
            insufficient = rel < c["min_reliability_for_prediction"]
            low = ~insufficient & (eff < thr)
            entry["live_rule_lower_bound"] = {
                "no_forecast_insufficient_data": {"n": int(insufficient.sum()), "share_of_forecasts": fl(insufficient.mean())},
                "isolation_forest_ood_rows": int(ood.sum()),
                "low_confidence_flagged": summarise(low),
                "shown_without_flag": summarise(~insufficient & ~low),
                "total_needing_review": int((insufficient | low).sum()),
                "share_needing_review": fl((insufficient | low).mean()),
            }
        out["per_horizon"][f"h{h}"] = entry
    return out


# ---------------------------------------------------------------- Mall

def mall_baseline(mall: Path) -> dict | None:
    gt_path = mall / "mall_dataset" / "mall_gt.mat"
    if not gt_path.exists():
        return None
    from scipy.io import loadmat

    gt = np.asarray(loadmat(gt_path)["count"]).ravel().astype(float)
    assert len(gt) == 2000
    fit20 = np.arange(0, 800, 40)  # identical to experiments/mall_eval.py: 20 frames spread over 1-800
    fit800 = np.arange(800)
    test = np.arange(800, 2000)
    n_blocks = len(test) // MALL_BLOCK
    w = boot_weights(n_blocks, SEED)
    block = (np.arange(len(test)) // MALL_BLOCK)

    def mae_stats(pred: np.ndarray) -> tuple[float, np.ndarray]:
        err = np.abs(pred - gt[test])
        sums = np.bincount(block, weights=err, minlength=n_blocks)
        cnt = np.bincount(block, minlength=n_blocks).astype(float)
        return float(err.mean()), (w @ sums) / (w @ cnt)

    out: dict = {"held_out_frames": "801-2000", "calibration_frames": "20 frames spread over 1-800 (1, 41, ..., 761), as in mall_eval.py",
                 "bootstrap": f"{n_blocks} blocks of {MALL_BLOCK} consecutive held-out frames, {N_BOOT:,} resamples, seed {SEED}",
                 "held_out_mean_annotated": fl(gt[test].mean()), "held_out_range": [int(gt[test].min()), int(gt[test].max())],
                 "note": "calibration frames are fixed; intervals cover only which held-out frames are drawn"}
    const20 = gt[fit20].mean()
    const800 = gt[fit800].mean()
    mae20, reps20 = mae_stats(np.full(len(test), const20))
    mae800, reps800 = mae_stats(np.full(len(test), const800))
    out["detector_free"] = {
        "mean_of_20_calibration_frames": {"predicted_count": fl(const20), "mae_held_out": fl(mae20), "mae_ci95": ci(reps20)},
        "mean_of_all_800_training_frames": {"predicted_count": fl(const800), "mae_held_out": fl(mae800), "mae_ci95": ci(reps800)},
    }
    out["detectors"] = {}
    for name in ("yolo11n", "apple_upper"):
        p = mall / "runs" / f"counts_{name}.csv"
        if not p.exists():
            continue
        det = pd.read_csv(p)["person_count"].to_numpy().astype(float)
        assert len(det) == 2000
        raw, raw_reps = mae_stats(det[test])
        a, b = np.polyfit(det[fit20], gt[fit20], 1)
        cal, cal_reps = mae_stats(a * det[test] + b)
        a8, b8 = np.polyfit(det[fit800], gt[fit800], 1)
        cal8, cal8_reps = mae_stats(a8 * det[test] + b8)
        out["detectors"][name] = {
            "raw_mae_held_out": fl(raw), "raw_mae_ci95": ci(raw_reps),
            "calibrated_20": {"a": fl(a), "b": fl(b), "mae_held_out": fl(cal), "mae_ci95": ci(cal_reps)},
            "calibrated_800": {"a": fl(a8), "b": fl(b8), "mae_held_out": fl(cal8), "mae_ci95": ci(cal8_reps)},
            "mean20_minus_calibrated20": {"mae": fl(mae20 - cal), "ci95": ci(reps20 - cal_reps), "share_of_resamples_le_0": fl(((reps20 - cal_reps) <= 0).mean())},
        }
    pub = json.loads((REPO / "experiments" / "results" / "mall" / "metrics.json").read_text())["results"]
    for name, d in out["detectors"].items():  # must reproduce the committed Mall numbers
        c = pub[name]["post_hoc_linear_calibration"]
        assert abs(d["raw_mae_held_out"] - c["raw_mae_held_out"]) < 0.006
        assert abs(d["calibrated_20"]["mae_held_out"] - c["20 frames spread over 1-800"]["mae_held_out"]) < 0.006
    return out


# ---------------------------------------------------------------- summary

# Every displayed figure is rounded exactly once, here, from the unrounded value stored in metrics.json.

def f3(x: float) -> str:
    return f"{x:.3f}"


def sg3(x: float) -> str:
    """Signed, 3 decimals; a non-zero value that would print as +0.000 gets a 4th decimal so it is not read as zero."""
    s = f"{x:+.3f}"
    return f"{x:+.4f}" if x != 0 and float(s) == 0 else s


def sg2(x: float) -> str:
    return f"{x:+.2f}"


def iv(lo_hi: list[float], fmt=f3) -> str:
    return f"{fmt(lo_hi[0])} to {fmt(lo_hi[1])}"


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def width(lo_hi: list[float]) -> float:
    return lo_hi[1] - lo_hi[0]


def resamples_le_0(share: float) -> str:
    return f"{round(share * N_BOOT):,} of {N_BOOT:,}"


def join_and(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def summary_markdown(m: dict) -> str:
    hz = m["horizons"]
    P = m["headline"][PRIMARY]
    L: list[str] = [
        "# Uncertainty and stronger baselines for the headline numbers",
        "",
        "Generated by `experiments/uncertainty.py` from `metrics.json` in this folder (re-run: `.venv/bin/python -I experiments/uncertainty.py`). "
        "Forecast figures come from `ml/models/test_predictions.csv.gz`, the shipped models' predictions on the three test days of the **synthetic** simulation "
        f"({', '.join(f'{d} ({v['weekday']})' for d, v in m['per_day'].items())}; {m['inputs']['zones']} zones, forecasts issued "
        f"{m['inputs']['local_time_range'][0]}-{m['inputs']['local_time_range'][1]} local time). Nothing was retrained. "
        f"Intervals: block bootstrap, {N_BOOT:,} resamples, seed {SEED}, percentile 95% intervals. Primary block = {BLOCK_SCHEMES[PRIMARY][1]} "
        f"({P['n_blocks']} blocks). With only {P['n_blocks']} blocks a percentile bootstrap can under-cover (come out too narrow), so treat the 95% intervals as approximate. "
        "Zone-day blocks treat the zones of one day as independent of each other and cannot capture day-to-day variation (section 3). "
        "**The intervals describe resampling variation inside three simulated days only; they say nothing about how the simulator differs from a real street.** "
        "`metrics.json` stores unrounded values; every figure on this page is rounded once, for display.",
        "",
        "## 1. Macro-F1 with 95% intervals (model vs persistence)",
        "",
        "| horizon | forecasts | model macro-F1 | persistence macro-F1 | gain (model - persistence) | resamples with gain <= 0 |",
        "|---|---|---|---|---|---|",
    ]
    for h in hz:
        e = P["per_horizon"][f"h{h}"]
        mo, pe, g = e["predictors"]["model"], e["predictors"]["persistence"], e["gains"]["model_minus_persistence"]
        L.append(f"| +{h} min | {e['n']:,} | {f3(mo['f1_macro'])} ({iv(mo['f1_macro_ci95'])}) | {f3(pe['f1_macro'])} ({iv(pe['f1_macro_ci95'])}) | "
                 f"{g['f1_macro']:+.3f} ({iv(g['f1_macro_ci95'], sg3)}) | {resamples_le_0(g['share_of_resamples_gain_le_0'])} |")
    e15 = P["per_horizon"]["h15"]
    g15 = e15["gains"]["model_minus_persistence"]
    L += ["",
          f"In plain words: at +15 min the model's macro-F1 is {f3(e15['predictors']['model']['f1_macro'])} (95% interval {iv(e15['predictors']['model']['f1_macro_ci95'])}) "
          f"against {f3(e15['predictors']['persistence']['f1_macro'])} for \"it will stay as it is now\"; the gain of {g15['f1_macro']:+.3f} has an interval of "
          f"{iv(g15['f1_macro_ci95'], sg3)}, so on these simulated days the model beats persistence "
          + ("in every resample" if g15["share_of_resamples_gain_le_0"] == 0 else f"in {pct(1 - g15['share_of_resamples_gain_le_0'])} of resamples") + ". "
          "The gain grows with the horizon because \"now\" is a worse guess the further ahead you look.",
          "",
          "Sensitivity of the gain interval to the block choice (macro-F1, model - persistence):",
          "",
          "| horizon | " + " | ".join(f"{BLOCK_SCHEMES[s][1]} ({m['headline'][s]['n_blocks']} blocks)" for s in BLOCK_SCHEMES) + " |",
          "|---|" + "---|" * len(BLOCK_SCHEMES)]
    for h in hz:
        L.append(f"| +{h} min | " + " | ".join(iv(m['headline'][s]['per_horizon'][f'h{h}']['gains']['model_minus_persistence']['f1_macro_ci95'], sg3) for s in BLOCK_SCHEMES) + " |")
    all_positive = all(m["headline"][s]["per_horizon"][f"h{h}"]["gains"]["model_minus_persistence"]["f1_macro_ci95"][0] > 0 for s in BLOCK_SCHEMES for h in hz)
    widest = {}
    for h in hz:
        widths = {s: np.diff(m["headline"][s]["per_horizon"][f"h{h}"]["gains"]["model_minus_persistence"]["f1_macro_ci95"])[0] for s in BLOCK_SCHEMES}
        widest[h] = max(widths, key=widths.get)
    widest_txt = "; ".join(f"+{h} min: {BLOCK_SCHEMES[s][1]}" for h, s in widest.items())
    L += ["", ("Meaning: every grouping of the minutes gives a gain interval above zero at every horizon, so the conclusion does not hinge on the block choice. "
               if all_positive else "Meaning: at least one grouping gives a gain interval that reaches zero; treat the gain as uncertain. ")
          + f"Widest interval per horizon: {widest_txt}.", ""]

    L += ["## 2. Accuracy against the majority class", "",
          "| horizon | SAFE share of targets | always-SAFE accuracy | persistence accuracy | model accuracy | always-SAFE macro-F1 |",
          "|---|---|---|---|---|---|"]
    for h in hz:
        e = P["per_horizon"][f"h{h}"]
        s, pe, mo = e["predictors"]["always_safe"], e["predictors"]["persistence"], e["predictors"]["model"]
        L.append(f"| +{h} min | {e['support']['SAFE']:,} / {e['n']:,} | {f3(s['accuracy'])} ({iv(s['accuracy_ci95'])}) | {f3(pe['accuracy'])} ({iv(pe['accuracy_ci95'])}) | "
                 f"{f3(mo['accuracy'])} ({iv(mo['accuracy_ci95'])}) | {f3(s['f1_macro'])} |")
    s15 = e15["predictors"]["always_safe"]
    L += ["",
          f"Meaning: a system that never warns anyone would already be {pct(s15['accuracy'])} accurate at +15 min, because most zone-minutes are calm; "
          f"accuracy alone hides that, which is why macro-F1 (always-SAFE scores {f3(s15['f1_macro'])}) is the number to lead with.", ""]

    L += ["## 3. Per test day", "",
          "| day | zone-minutes CRITICAL now (of observed) | minutes with any zone CRITICAL | +15 min: CRITICAL targets | model macro-F1 | persistence macro-F1 | gain (model - persistence) | model CRITICAL forecasts (false) |",
          "|---|---|---|---|---|---|---|---|"]
    for d, v in m["per_day"].items():
        r = v["per_horizon"]["h15"]
        L.append(f"| {d} ({v['weekday']}) | {v['zone_minutes_critical_now']:,} of {v['zone_minutes_observed']:,} | {v['minutes_with_any_zone_critical_now']:,} | "
                 f"{r['target_zone_minutes_critical']:,} | {f3(r['model']['f1_macro'])} ({iv(r['model']['f1_macro_ci95'])}) | "
                 f"{f3(r['persistence']['f1_macro'])} ({iv(r['persistence']['f1_macro_ci95'])}) | {r['gain_f1_model_minus_persistence']:+.3f} "
                 f"({iv(r['gain_f1_model_minus_persistence_ci95'], sg3)}) | {r['model']['critical_forecasts']} ({r['model']['false_critical_forecasts']}) |")
    days_f1 = [v["per_horizon"]["h15"]["model"]["f1_macro"] for v in m["per_day"].values()]
    calm = [(d, v) for d, v in m["per_day"].items() if v["per_horizon"]["h15"]["target_zone_minutes_critical"] == 0]
    day_lo = {(d, h): v["per_horizon"][f"h{h}"]["gain_f1_model_minus_persistence_ci95"][0] for d, v in m["per_day"].items() for h in hz}
    weak = [f"{d} at +{h} min" for (d, h), lo in day_lo.items() if lo <= 0]
    # lower bounds above zero that print as +0.000 at 3 decimals: say they only just clear zero
    just = [f"{d} at +{h} min (lower bound {sg3(lo)})" for (d, h), lo in day_lo.items() if 0 < lo and float(f"{lo:.3f}") == 0]
    zh_narrowest = all(min(BLOCK_SCHEMES, key=lambda s: width(m["headline"][s]["per_horizon"][f"h{h}"]["gains"]["model_minus_persistence"]["f1_macro_ci95"])) == "zone_hour"
                       for h in hz)
    gain_txt = []
    if weak:
        gain_txt.append(f"the gain interval reaches zero on {join_and(weak)}")
    if just:
        gain_txt.append(f"only just clears zero on {join_and(just)}")
    L += ["",
          "Columns 5-8 are +15 min forecasts. Macro-F1 here averages over the classes that occur as targets that day (a day with no CRITICAL minute would "
          "otherwise score 0 for CRITICAL and be capped at 0.667; the 3-class values are stored as `f1_macro_3class` in `experiments/results/uncertainty/metrics.json`). "
          "95% intervals: zone-hour blocks within the day. "
          + ("Zone-hour blocks gave the narrowest gain intervals of the three groupings in section 1 at every horizon, so treat these per-day intervals as optimistic."
             if zh_narrowest else "Zone-hour blocks are the finest grouping tried in section 1; treat these per-day intervals as optimistic."),
          f"Meaning: the +15 min model macro-F1 ranges from {f3(min(days_f1))} to {f3(max(days_f1))} across the three days, and its point estimate "
          + ("beats persistence on every day and horizon" if all(v["per_horizon"][f"h{h}"]["gain_f1_model_minus_persistence"] > 0 for v in m["per_day"].values() for h in hz)
             else "does not beat persistence on " + join_and([f"{d} at +{h} min" for d, v in m["per_day"].items() for h in hz
                                                               if v["per_horizon"][f"h{h}"]["gain_f1_model_minus_persistence"] <= 0]))
          + (f" (but {', and '.join(gain_txt)})" if gain_txt else ", with every per-day gain interval clearly above zero")
          + "; with only three test days, day-to-day variation is the largest unknown."
          + "".join(f" On {d} ({v['weekday']}) no zone reached CRITICAL and the model issued {v['per_horizon']['h15']['model']['critical_forecasts']} CRITICAL forecasts at +15 min."
                    for d, v in calm)
          + " The +5 and +10 min per-day figures are in `experiments/results/uncertainty/metrics.json` (`per_day`); `ml/models/metrics.json` has no per-day values.", ""]

    rf = m["review_flags"]
    thr = rf["threshold"]
    gate = f"flagged as uncertain by the model (confidence < {thr})"
    L += ["## 4. Forecasts flagged as uncertain, and the live review flag", "",
          f"Rule in `ml/models/metrics.json` and the video script: a forecast is **{gate}**, where confidence is the largest class probability. "
          "The accuracy of the rest gets only the zone-day block-bootstrap interval: a Wilson interval would treat the "
          f"{rf['per_horizon']['h15']['training_report_rule']['not_flagged']['n']:,} unflagged +15 min forecasts, neighbouring minutes of which are strongly correlated, "
          "as independent and come out far too narrow.", "",
          "| horizon | flagged | accuracy of flagged (Wilson 95%) | same, zone-day block bootstrap | accuracy of the rest (zone-day block bootstrap 95%) | flagged with a true CRITICAL target |",
          "|---|---|---|---|---|---|"]
    for h in hz:
        t = rf["per_horizon"][f"h{h}"]["training_report_rule"]
        f, nf = t["flagged"], t["not_flagged"]
        L.append(f"| +{h} min | {f['n']} ({pct(f['share_of_forecasts'])}) | {f3(f['accuracy'])} ({iv(f['accuracy_wilson95'])}) | {iv(f['accuracy_block_bootstrap95'])} | "
                 f"{f3(nf['accuracy'])} ({iv(nf['accuracy_block_bootstrap95'])}) | {f['true_class_counts']['CRITICAL']} |")
    t15 = rf["per_horizon"]["h15"]["training_report_rule"]
    # Wilson vs block bootstrap for the flagged forecasts, compared per horizon from the stored intervals
    wider, narrower = [], []
    for h in hz:
        f = rf["per_horizon"][f"h{h}"]["training_report_rule"]["flagged"]
        ww, wb = width(f["accuracy_wilson95"]), width(f["accuracy_block_bootstrap95"])
        (wider if wb > ww else narrower).append(f"+{h} min ({f3(wb)} vs {f3(ww)})")
    cmp = []
    if wider:
        cmp.append(f"wider than Wilson at {join_and(wider)}")
    if narrower:
        cmp.append(f"narrower at {join_and(narrower)}")
    nf15 = t15["not_flagged"]
    pb15 = t15["flagged"]["per_block_n"]
    L += ["",
          f"Meaning: at +15 min, {t15['flagged']['n']} of {e15['n']:,} forecasts ({pct(t15['flagged']['share_of_forecasts'])}) are {gate}, and those are right only "
          f"{pct(t15['flagged']['accuracy'])} of the time (Wilson {iv(t15['flagged']['accuracy_wilson95'], pct)}; block bootstrap {iv(t15['flagged']['accuracy_block_bootstrap95'], pct)}) "
          f"against {pct(nf15['accuracy'])} for the rest (block bootstrap {iv(nf15['accuracy_block_bootstrap95'], pct)}): the flag picks out the forecasts that deserve a second look.",
          "",
          f"Wilson treats every forecast as independent; the zone-day block bootstrap does not. For the flagged forecasts the bootstrap interval is {', and '.join(cmp)} "
          f"(interval widths, bootstrap vs Wilson). The bootstrap is not reliably the more cautious of the two here: with only {P['n_blocks']} blocks "
          f"(flagged +15 min forecasts per block: {pb15['min']} to {pb15['max']}, median {pb15['median']:g}"
          + (f", {pb15['blocks_with_none']} blocks with none" if pb15['blocks_with_none'] else "")
          + f"), a percentile bootstrap can itself under-cover. For the rest, a Wilson interval would be {iv(nf15['accuracy_wilson95'])} at +15 min "
          f"(width {f3(width(nf15['accuracy_wilson95']))}) against {iv(nf15['accuracy_block_bootstrap95'])} from the block bootstrap (width {f3(width(nf15['accuracy_block_bootstrap95']))}). All widths in this paragraph are computed from the unrounded endpoints."]
    if "live_rule_lower_bound" in rf["per_horizon"]["h15"]:
        lr = rf["live_rule"]
        L += ["",
              f"This is not the rule behind the live dashboard's \"HUMAN REVIEW REQUIRED\" flag (`human_review_required`). That flag comes from the live backend rule (`{lr['source']}`): "
              f"effective confidence = model confidence x clip(0.4 + 0.6 x sensor reliability, 0, 1), times {lr['ood_confidence_multiplier']} when the input looks unusual (out of distribution), "
              f"flagged below {lr['threshold']}; when reliability is below {lr['min_reliability_for_prediction']} no forecast is shown at all and the entry is also marked for human review. "
              "It flags more. **The flag counts and shares below are lower bounds**: the feature-range half of the out-of-distribution check cannot be recomputed from the stored "
              "predictions, so some forecasts the live rule would flag are counted as unflagged here. The accuracy column is not a bound in either direction.", "",
              "| horizon | no forecast (reliability < " + f"{lr['min_reliability_for_prediction']}) | low-confidence flag | accuracy of low-confidence flagged (Wilson 95%; zone-day block bootstrap 95%) "
              "| needing review, at least |", "|---|---|---|---|---|"]
        for h in hz:
            lv = rf["per_horizon"][f"h{h}"]["live_rule_lower_bound"]
            lf = lv["low_confidence_flagged"]
            L.append(f"| +{h} min | {lv['no_forecast_insufficient_data']['n']} | {lf['n']} | {f3(lf['accuracy'])} ({iv(lf['accuracy_wilson95'])}; {iv(lf['accuracy_block_bootstrap95'])}) | "
                     f"{lv['total_needing_review']:,} ({pct(lv['share_needing_review'])}) |")
    L.append("")

    L += ["## 5. Moving-average persistence baselines", "",
          "| horizon | persistence | 3-min moving average | 5-min moving average | model | model - best of the three baselines |", "|---|---|---|---|---|---|"]
    for h in hz:
        e = P["per_horizon"][f"h{h}"]
        pr = e["predictors"]
        best = max(("persistence", "ma3", "ma5"), key=lambda k: pr[k]["f1_macro"])
        g = e["gains"][f"model_minus_{best}"]
        L.append(f"| +{h} min | {f3(pr['persistence']['f1_macro'])} | {f3(pr['ma3']['f1_macro'])} ({iv(pr['ma3']['f1_macro_ci95'])}) | {f3(pr['ma5']['f1_macro'])} ({iv(pr['ma5']['f1_macro_ci95'])}) | "
                 f"{f3(pr['model']['f1_macro'])} | {g['f1_macro']:+.3f} ({iv(g['f1_macro_ci95'], sg3)}) vs {best} |")
    cov = m["moving_average_coverage"]["h15"]
    pr15 = e15["predictors"]
    best15 = max(("persistence", "ma3", "ma5"), key=lambda k: pr15[k]["f1_macro"])
    L += ["",
          f"Macro-F1 (95% interval). The averages use the same density index and thresholds as the labels; {pct(cov['share_rows_full_3min_window'])} / {pct(cov['share_rows_full_5min_window'])} "
          "of +15 min forecasts had a complete 3 / 5-minute window (the rest average the minutes present).",
          f"Meaning: smoothing the last few minutes is {'a better' if best15 != 'persistence' else 'not a better'} naive forecast than the last minute alone "
          f"(best at +15 min: {PREDICTORS[best15][1]}, {f3(pr15[best15]['f1_macro'])}), and the model still clears it by "
          f"{e15['gains'][f'model_minus_{best15}']['f1_macro']:+.3f}"
          + "".join(f"; at +{h} min the edge over the best smoothing baseline is only {P['per_horizon'][f'h{h}']['gains'][f'model_minus_{b}']['f1_macro']:+.3f} "
                    f"({iv(P['per_horizon'][f'h{h}']['gains'][f'model_minus_{b}']['f1_macro_ci95'], sg3)})"
                    for h in hz[:1] for b in [max(('persistence', 'ma3', 'ma5'), key=lambda k: P['per_horizon'][f'h{h}']['predictors'][k]['f1_macro'])])
          + ". The longer the horizon, the more the model adds over smoothing.", ""]

    L += ["## 6. Mall counting: calibration vs a detector-free guess", ""]
    mall = m.get("mall")
    if mall is None:
        L += ["Skipped: the Mall annotations are not present locally (`experiments/datasets/mall/mall_dataset/mall_gt.mat`).", ""]
    else:
        dfree = mall["detector_free"]["mean_of_20_calibration_frames"]
        L += [f"Held-out frames {mall['held_out_frames']} (mean {mall['held_out_mean_annotated']:.1f} annotated people). Intervals: {mall['bootstrap']}.", "",
              "| method | uses the detector? | held-out MAE (people per frame, 95% interval) |", "|---|---|---|"]
        y = mall["detectors"].get("yolo11n")
        if y:
            L.append(f"| YOLO11n raw count | yes | {y['raw_mae_held_out']:.2f} ({iv(y['raw_mae_ci95'], lambda x: f'{x:.2f}')}) |")
        L.append(f"| always say {dfree['predicted_count']:.2f} (mean annotated count of the same 20 calibration frames) | no | {dfree['mae_held_out']:.2f} ({iv(dfree['mae_ci95'], lambda x: f'{x:.2f}')}) |")
        d8 = mall["detector_free"]["mean_of_all_800_training_frames"]
        L.append(f"| always say {d8['predicted_count']:.2f} (mean of all 800 training frames) | no | {d8['mae_held_out']:.2f} ({iv(d8['mae_ci95'], lambda x: f'{x:.2f}')}) |")
        if y:
            L.append(f"| YOLO11n + linear calibration on the 20 frames | yes | {y['calibrated_20']['mae_held_out']:.2f} ({iv(y['calibrated_20']['mae_ci95'], lambda x: f'{x:.2f}')}) |")
            dd = y["mean20_minus_calibrated20"]
            L += ["",
                  f"Meaning: most of the drop from {y['raw_mae_held_out']:.2f} to {y['calibrated_20']['mae_held_out']:.2f} is fixing the detector's systematic under-count; "
                  f"a fixed guess with no detector at all already gets {dfree['mae_held_out']:.2f}. The calibrated detector beats that guess by {dd['mae']:.2f} people per frame "
                  f"(95% interval {iv(dd['ci95'], lambda x: f'{x:.2f}')}): that margin, not the drop from {y['raw_mae_held_out']:.1f}, is what the detector adds in this mall, where the held-out "
                  f"count stays between {mall['held_out_range'][0]} and {mall['held_out_range'][1]} people. The calibration frames are fixed, so the intervals cover only which held-out frames are drawn."]
        a = mall["detectors"].get("apple_upper")
        if a:
            da = a["mean20_minus_calibrated20"]
            L += ["",
                  f"The app's fallback detector (Apple upper-body), calibrated the same way, reaches {a['calibrated_20']['mae_held_out']:.2f} "
                  f"({iv(a['calibrated_20']['mae_ci95'], lambda x: f'{x:.2f}')}), {da['mae']:.2f} better than the fixed guess "
                  f"(95% interval {iv(da['ci95'], lambda x: f'{x:+.2f}')}): "
                  + ("not distinguishable from guessing, so the fallback adds little beyond a per-site average." if da["ci95"][0] <= 0 else "a small but clear gain.")]
        L.append("")

    L += ["## What can go on screen", ""]
    pe15, mo15 = e15["predictors"]["persistence"], e15["predictors"]["model"]
    gain_ci = g15["f1_macro_ci95"]
    if all(m['headline'][s]['per_horizon']['h15']['gains']['model_minus_persistence']['f1_macro_ci95'][0] > 0 for s in BLOCK_SCHEMES):
        L += [f"- On screen: \"+15 min macro-F1 {f3(mo15['f1_macro'])} vs {f3(pe15['f1_macro'])} for persistence: gain {sg3(g15['f1_macro'])}, "
              f"95% CI {sg2(gain_ci[0])} to {sg2(gain_ci[1])}, simulated test days\". The interval is paired (model and persistence scored on the same resampled blocks; "
              f"3 decimals: {iv(gain_ci, sg3)}) and stays above zero under every block choice in section 1.",
              f"- Q&A, not on screen: the separate intervals, {iv(mo15['f1_macro_ci95'])} (model) and {iv(pe15['f1_macro_ci95'])} (persistence), "
              + ("overlap. That is expected when two scores are computed on the same forecasts and does not weaken the gain, which is the paired comparison."
                 if mo15['f1_macro_ci95'][0] <= pe15['f1_macro_ci95'][1] else
                 f"do not overlap, but only narrowly ({f3(mo15['f1_macro_ci95'][0])} vs {f3(pe15['f1_macro_ci95'][1])}); "
                 "the paired gain interval is the cleaner statement, because model and persistence are scored on the same forecasts.")]
    else:
        L += ["- The +15 min gain interval reaches zero under at least one block choice: keep the gain off screen."]
    live15 = rf["per_horizon"]["h15"].get("live_rule_lower_bound")
    L += [f"- On screen: \"never-warn baseline is {pct(s15['accuracy'])} accurate\" (one clause next to accuracy), so accuracy is not mistaken for skill.",
          f"- On screen: \"{pct(t15['flagged']['share_of_forecasts'])} of +15 min forecasts are {gate}; those are right {pct(t15['flagged']['accuracy'])} of the time, "
          f"the rest {pct(t15['not_flagged']['accuracy'])}\". Do not say these \"go to a person\": the live dashboard's \"HUMAN REVIEW REQUIRED\" flag is the separate live rule in section 4."
          + (f" If that rule is quoted, say \"at least {pct(live15['share_needing_review'])} of +15 min forecasts ({live15['total_needing_review']:,} of {e15['n']:,})\": "
             f"{live15['no_forecast_insufficient_data']['n']} withheld for weak sensor data and {live15['low_confidence_flagged']['n']} shown with the flag, "
             f"which are right {pct(live15['low_confidence_flagged']['accuracy'])} of the time." if live15 else ""),
          "- Q&A only: block-choice sensitivity, per-day table, moving-average baselines, Wilson vs bootstrap intervals, "
          "live-rule flag counts, +5 / +10 min intervals."]
    if mall is not None and mall["detectors"].get("yolo11n"):
        L += [f"- Mall: if \"MAE {mall['detectors']['yolo11n']['raw_mae_held_out']:.1f} -> {mall['detectors']['yolo11n']['calibrated_20']['mae_held_out']:.1f}\" is shown, say in the same clause "
              f"that a no-detector guess scores {mall['detector_free']['mean_of_20_calibration_frames']['mae_held_out']:.1f}; otherwise keep the calibration figure for Q&A."]
    L.append("")
    return "\n".join(L)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--predictions", type=Path, default=REPO / "ml" / "models" / "test_predictions.csv.gz")
    ap.add_argument("--metrics", type=Path, default=REPO / "ml" / "models" / "metrics.json")
    ap.add_argument("--mall", type=Path, default=REPO / "experiments" / "datasets" / "mall")
    ap.add_argument("--out", type=Path, default=REPO / "experiments" / "results" / "uncertainty")
    args = ap.parse_args()
    cfg = load_config()
    published = json.loads(args.metrics.read_text())
    horizons = published["horizons"]
    df = load_predictions(args.predictions, cfg)
    ood_threshold = None
    try:  # the isolation-forest threshold lives in the pickled detector; needs the repo on sys.path
        sys.path.insert(0, str(REPO))
        import joblib

        ood_threshold = float(joblib.load(REPO / "ml" / "models" / "ood.joblib").threshold)
    except Exception as e:  # pragma: no cover
        print(f"live-rule flag counts skipped: could not read the OOD threshold ({e})")
    m: dict = {
        "generated_by": "experiments/uncertainty.py",
        "inputs": {"predictions": "ml/models/test_predictions.csv.gz", "published_metrics": "ml/models/metrics.json",
                   "model_version": published["model_version"], "trained_at": published["trained_at"], "test_days": published["split_days"]["test"],
                   "zones": int(df["zone_id"].nunique()),
                   "local_time_range": [f"{t:%H:%M}" for t in (df["t"] + pd.Timedelta(hours=MACAU_UTC_OFFSET_H)).dt.time.agg(["min", "max"])]},
        "data_note": "Synthetic simulation (ml/synthetic). Labels are the observed (sensed) density index class h minutes ahead, thresholds from shared/config.json.",
        "bootstrap": {"resamples": N_BOOT, "seed": SEED, "interval": "percentile 95%", "primary_block": PRIMARY,
                      "block_schemes": {k: v[1] for k, v in BLOCK_SCHEMES.items()}},
        "horizons": horizons,
        "thresholds": {k: cfg["congestion_thresholds"][k] for k in ("warning", "critical")},
    }
    m["headline"] = headline(df, horizons, published)
    m["moving_average_coverage"] = moving_average_coverage(df, horizons)
    m["per_day"] = per_day(df, horizons)
    m["review_flags"] = review_flags(df, horizons, cfg, published, ood_threshold)
    mall = mall_baseline(args.mall)
    m["mall"] = mall
    if mall is None:
        m["mall_skipped_reason"] = "Mall annotations not present locally"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "metrics.json").write_text(json.dumps(m, indent=2) + "\n")
    (args.out / "summary.md").write_text(summary_markdown(m))
    print((args.out / "summary.md").read_text())


if __name__ == "__main__":
    main()
