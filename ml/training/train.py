"""Train and compare congestion classifiers (and density regressors) per forecast horizon.

    python -m ml.training.train --data ml/data --out ml/models

Outputs (all real, produced by this run):
  ml/models/congestion_h{5,10,15}.joblib   chosen classifier per horizon (+ calibration)
  ml/models/density_h{5,10,15}.joblib      density regressor per horizon
  ml/models/ood.joblib                     isolation-forest OOD detector
  ml/models/metrics.json                   full metrics (test set, persistence baseline, model comparison, stress set)
  ml/models/feature_spec.json              feature list + training medians (for sensitivity explanations)
  ml/models/test_predictions.csv.gz        per-row predictions for the evaluation figures
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.pipeline.features import FEATURE_COLUMNS, feature_matrix
from ml.pipeline.metrics import classification_metrics, expected_calibration_error
from ml.pipeline.ood import OODDetector
from ml.training.dataset import prepare_dataset
from shared.config import CLASSES, load_config

MODEL_VERSION = "crowdpulse-clf-0.1"


def make_models(seed: int) -> dict[str, Pipeline]:
    return {
        "logistic_regression": Pipeline([
            ("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler()),
            ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", C=1.0)),
        ]),
        "random_forest": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced_subsample", n_jobs=-1, random_state=seed)),
        ]),
        "gradient_boosting": Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("clf", HistGradientBoostingClassifier(max_iter=400, learning_rate=0.05, max_leaf_nodes=31, l2_regularization=1.0, class_weight="balanced", random_state=seed, early_stopping=True, validation_fraction=0.1)),
        ]),
    }


def split_days(ff: pd.DataFrame, test_idx: list[int], val_idx: list[int]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, list[str]]]:
    days = sorted(ff["local_date"].unique())
    test_days = [days[i] for i in test_idx if i < len(days)]
    val_days = [days[i] for i in val_idx if i < len(days)]
    train_days = [d for d in days if d not in test_days and d not in val_days]
    return ff[ff["local_date"].isin(train_days)], ff[ff["local_date"].isin(val_days)], ff[ff["local_date"].isin(test_days)], {"train": train_days, "val": val_days, "test": test_days}


def labelled(ff: pd.DataFrame, h: int) -> pd.DataFrame:
    return ff[ff[f"label_h{h}"].notna() & ff["density"].notna()]


def maybe_calibrate(model: Pipeline, X_val: pd.DataFrame, y_val: np.ndarray) -> tuple[Any, dict[str, Any]]:
    """Isotonic calibration fitted on half of the validation set, accepted only if it
    lowers ECE on the other half (no test-set peeking)."""
    try:
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.frozen import FrozenEstimator
    except ImportError:  # older sklearn
        return model, {"calibrated": False, "reason": "sklearn too old"}
    n = len(X_val)
    if n < 400 or len(np.unique(y_val)) < len(CLASSES):
        return model, {"calibrated": False, "reason": "validation set too small"}
    half = n // 2
    Xa, ya, Xb, yb = X_val.iloc[:half], y_val[:half], X_val.iloc[half:], y_val[half:]
    yb_idx = np.array([CLASSES.index(c) for c in yb])
    raw_ece = expected_calibration_error(yb_idx, _proba_in_class_order(model, Xb))
    cal = CalibratedClassifierCV(FrozenEstimator(model), method="isotonic").fit(Xa, ya)
    cal_ece = expected_calibration_error(yb_idx, _proba_in_class_order(cal, Xb))
    if cal_ece < raw_ece - 0.005:
        full = CalibratedClassifierCV(FrozenEstimator(model), method="isotonic").fit(X_val, y_val)
        return full, {"calibrated": True, "ece_raw_holdout": raw_ece, "ece_calibrated_holdout": cal_ece}
    return model, {"calibrated": False, "ece_raw_holdout": raw_ece, "ece_calibrated_holdout": cal_ece}


def _proba_in_class_order(model: Any, X: pd.DataFrame) -> np.ndarray:
    p = model.predict_proba(X)
    order = [list(model.classes_).index(c) for c in CLASSES]
    return p[:, order]


def train(data_dir: Path, out_dir: Path, seed: int = 0, test_idx: list[int] | None = None, val_idx: list[int] | None = None) -> dict[str, Any]:
    cfg = load_config()
    horizons = cfg["forecast_horizons_min"]
    t0 = time.time()
    obs = pd.read_csv(data_dir / "synthetic_observations.csv.gz")
    truth = pd.read_csv(data_dir / "synthetic_ground_truth.csv.gz")
    ff = prepare_dataset(obs, truth, cfg)
    stress = None
    if (data_dir / "stress_observations.csv.gz").exists():
        stress = prepare_dataset(pd.read_csv(data_dir / "stress_observations.csv.gz"), pd.read_csv(data_dir / "stress_ground_truth.csv.gz"), cfg)
    train_df, val_df, test_df, days = split_days(ff, test_idx or [6, 9, 13], val_idx or [4, 11])
    out_dir.mkdir(parents=True, exist_ok=True)
    medians = feature_matrix(train_df).median().to_dict()
    summary: dict[str, Any] = {
        "model_version": MODEL_VERSION, "trained_at": pd.Timestamp.utcnow().isoformat(), "seed": seed,
        "features": FEATURE_COLUMNS, "horizons": horizons, "classes": CLASSES, "split_days": days,
        "rows": {"train": int(len(train_df)), "val": int(len(val_df)), "test": int(len(test_df)), "stress": int(len(stress)) if stress is not None else 0},
        "label_distribution_train": {f"h{h}": train_df[f"label_h{h}"].value_counts(normalize=True).round(3).to_dict() for h in horizons},
        "thresholds": cfg["congestion_thresholds"], "per_horizon": {},
    }
    pred_rows: list[pd.DataFrame] = []
    # OOD detector on training features
    ood = OODDetector(feature_columns=FEATURE_COLUMNS, contamination=cfg["ood"]["contamination"]).fit(feature_matrix(train_df[train_df["density"].notna()]), seed=seed)
    ood.save(str(out_dir / "ood.joblib"))
    for h in horizons:
        tr, va, te = labelled(train_df, h), labelled(val_df, h), labelled(test_df, h)
        Xtr, ytr = feature_matrix(tr), tr[f"label_h{h}"].to_numpy()
        Xva, yva = feature_matrix(va), va[f"label_h{h}"].to_numpy()
        Xte, yte = feature_matrix(te), te[f"label_h{h}"].to_numpy()
        comparison: dict[str, Any] = {}
        fitted: dict[str, Pipeline] = {}
        for name, model in make_models(seed).items():
            t1 = time.time()
            model.fit(Xtr, ytr)
            fitted[name] = model
            m_val = classification_metrics(yva, model.predict(Xva), _proba_in_class_order(model, Xva))
            m_test = classification_metrics(yte, model.predict(Xte), _proba_in_class_order(model, Xte))
            comparison[name] = {"val": m_val, "test": m_test, "fit_seconds": round(time.time() - t1, 1)}
        # persistence baseline: future class = current class
        persist_val = classification_metrics(yva, va["current_state"].to_numpy())
        persist_test = classification_metrics(yte, te["current_state"].to_numpy())
        best_name = max(comparison, key=lambda k: comparison[k]["val"]["f1_macro"])
        best, cal_info = maybe_calibrate(fitted[best_name], Xva, yva)
        proba = _proba_in_class_order(best, Xte)
        y_pred = np.array(CLASSES)[proba.argmax(axis=1)]
        test_metrics = classification_metrics(yte, y_pred, proba)
        # metrics against simulation ground truth (what really happened, incl. sensing error)
        truth_mask = te[f"true_label_h{h}"].notna().to_numpy()
        truth_metrics = classification_metrics(te[f"true_label_h{h}"].to_numpy()[truth_mask], y_pred[truth_mask], proba[truth_mask]) if truth_mask.any() else None
        # low-confidence gating: accuracy among confident vs flagged predictions
        conf = proba.max(axis=1)
        thr = cfg["confidence"]["low_confidence_threshold"]
        gating = {
            "threshold": thr,
            "fraction_flagged": float((conf < thr).mean()),
            "accuracy_confident": float((y_pred[conf >= thr] == yte[conf >= thr]).mean()) if (conf >= thr).any() else None,
            "accuracy_flagged": float((y_pred[conf < thr] == yte[conf < thr]).mean()) if (conf < thr).any() else None,
        }
        # density regressor
        reg = Pipeline([("imp", SimpleImputer(strategy="median")), ("reg", HistGradientBoostingRegressor(max_iter=400, learning_rate=0.05, random_state=seed, early_stopping=True))])
        reg.fit(Xtr, tr[f"density_h{h}"].to_numpy())
        dens_pred = np.clip(reg.predict(Xte), 0, 1)
        reg_metrics = {
            "mae_vs_observed": float(np.abs(dens_pred - te[f"density_h{h}"].to_numpy()).mean()),
            "mae_vs_truth": float(np.abs(dens_pred[truth_mask] - te[f"true_density_h{h}"].to_numpy()[truth_mask]).mean()) if truth_mask.any() else None,
            "mae_persistence_vs_observed": float(np.abs(te["density"].to_numpy() - te[f"density_h{h}"].to_numpy()).mean()),
        }
        # stress / OOD scenario
        stress_metrics = None
        if stress is not None:
            ste = labelled(stress, h)
            if len(ste):
                sp = _proba_in_class_order(best, feature_matrix(ste))
                spred = np.array(CLASSES)[sp.argmax(axis=1)]
                stress_metrics = classification_metrics(ste[f"label_h{h}"].to_numpy(), spred, sp)
                stress_metrics["ood_flag_rate"] = float((ood.score_frame(feature_matrix(ste)) < ood.threshold).mean())
                stress_metrics["ood_flag_rate_test"] = float((ood.score_frame(Xte) < ood.threshold).mean())
        joblib.dump({"model": best, "model_type": best_name, "feature_columns": FEATURE_COLUMNS, "classes": CLASSES, "horizon": h, "version": MODEL_VERSION, "calibration": cal_info}, out_dir / f"congestion_h{h}.joblib")
        joblib.dump({"model": reg, "feature_columns": FEATURE_COLUMNS, "horizon": h, "version": MODEL_VERSION}, out_dir / f"density_h{h}.joblib")
        # feature importances (tree models) for the dashboard's explanation page
        importances = None
        clf = fitted[best_name].named_steps["clf"]
        if hasattr(clf, "feature_importances_"):
            importances = {f: float(v) for f, v in sorted(zip(FEATURE_COLUMNS, clf.feature_importances_), key=lambda t: -t[1])}
        elif hasattr(clf, "coef_"):
            importances = {f: float(v) for f, v in sorted(zip(FEATURE_COLUMNS, np.abs(clf.coef_).mean(axis=0)), key=lambda t: -t[1])}
        summary["per_horizon"][f"h{h}"] = {
            "chosen_model": best_name, "calibration": cal_info, "test": test_metrics, "test_vs_ground_truth": truth_metrics,
            "persistence_baseline": {"val": persist_val, "test": persist_test}, "model_comparison": comparison,
            "confidence_gating": gating, "density_regression": reg_metrics, "stress_scenario": stress_metrics,
            "feature_importances": importances,
        }
        pr = te[["zone_id", "bin_start", "local_date", "density", "current_state", f"label_h{h}", f"true_label_h{h}", f"density_h{h}", f"true_density_h{h}", "reliability"]].copy()
        pr.columns = ["zone_id", "bin_start", "local_date", "density", "current_state", "y_obs", "y_true", "density_obs_future", "density_true_future", "reliability"]
        pr["horizon"] = h
        pr["y_pred"] = y_pred
        pr["confidence"] = conf
        for i, c in enumerate(CLASSES):
            pr[f"p_{c}"] = proba[:, i]
        pr["density_pred"] = dens_pred
        pr["ood_score"] = ood.score_frame(Xte)
        pred_rows.append(pr)
        print(f"[h={h:>2}] best={best_name:18s} test acc={test_metrics['accuracy']:.3f} F1(macro)={test_metrics['f1_macro']:.3f} | persistence acc={persist_test['accuracy']:.3f} F1={persist_test['f1_macro']:.3f} | vs truth acc={(truth_metrics or {}).get('accuracy', float('nan')):.3f} | density MAE={reg_metrics['mae_vs_observed']:.3f}")
    pd.concat(pred_rows).to_csv(out_dir / "test_predictions.csv.gz", index=False, compression="gzip")
    (out_dir / "feature_spec.json").write_text(json.dumps({"feature_columns": FEATURE_COLUMNS, "medians": {k: (None if pd.isna(v) else float(v)) for k, v in medians.items()}, "version": MODEL_VERSION}, indent=2))
    summary["train_seconds"] = round(time.time() - t0, 1)
    (out_dir / "metrics.json").write_text(json.dumps(summary, indent=2, default=str))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="ml/data")
    ap.add_argument("--out", default="ml/models")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    s = train(Path(args.data), Path(args.out), seed=args.seed)
    print(json.dumps({h: {"model": v["chosen_model"], "accuracy": round(v["test"]["accuracy"], 4), "f1_macro": round(v["test"]["f1_macro"], 4)} for h, v in s["per_horizon"].items()}, indent=2))
    print("split:", s["split_days"], "seconds:", s["train_seconds"])


if __name__ == "__main__":
    main()
