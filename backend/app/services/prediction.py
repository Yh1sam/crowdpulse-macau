"""Model loading and per-zone prediction with confidence, reliability, OOD and explanations."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ml.pipeline.explain import rule_reasons, sensitivity_contributions
from ml.pipeline.features import FEATURE_COLUMNS
from ml.pipeline.ood import OODDetector
from shared.config import CLASSES, congestion_class

log = logging.getLogger("crowdpulse.prediction")


@dataclass
class ModelBundle:
    classifiers: dict[int, dict[str, Any]] = field(default_factory=dict)
    regressors: dict[int, dict[str, Any]] = field(default_factory=dict)
    ood: OODDetector | None = None
    medians: dict[str, float] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    version: str = "none"

    @property
    def loaded(self) -> bool:
        return bool(self.classifiers)

    def status(self) -> dict[str, Any]:
        return {
            "loaded": self.loaded,
            "version": self.version,
            "horizons": sorted(self.classifiers),
            "model_types": {str(h): c["model_type"] for h, c in self.classifiers.items()},
            "calibration": {str(h): c.get("calibration", {}) for h, c in self.classifiers.items()},
            "ood_detector": self.ood is not None,
            "regressors": sorted(self.regressors),
            "trained_at": self.metrics.get("trained_at"),
            "features": FEATURE_COLUMNS,
        }


def load_models(models_dir: Path) -> ModelBundle:
    b = ModelBundle()
    if not models_dir.exists():
        log.warning("models dir %s missing - running with persistence fallback", models_dir)
        return b
    for p in sorted(models_dir.glob("congestion_h*.joblib")):
        d = joblib.load(p)
        b.classifiers[int(d["horizon"])] = d
        b.version = d.get("version", b.version)
    for p in sorted(models_dir.glob("density_h*.joblib")):
        d = joblib.load(p)
        b.regressors[int(d["horizon"])] = d
    if (models_dir / "ood.joblib").exists():
        b.ood = OODDetector.load(str(models_dir / "ood.joblib"))
    if (models_dir / "feature_spec.json").exists():
        b.medians = {k: v for k, v in json.loads((models_dir / "feature_spec.json").read_text())["medians"].items() if v is not None}
    if (models_dir / "metrics.json").exists():
        b.metrics = json.loads((models_dir / "metrics.json").read_text())
    log.info("loaded models: %s", b.status())
    return b


def _proba_in_class_order(model: Any, X: pd.DataFrame) -> np.ndarray:
    p = model.predict_proba(X)
    order = [list(model.classes_).index(c) for c in CLASSES]
    return p[:, order]


def predict_zone(bundle: ModelBundle, feat: dict[str, Any], zone_id: str, now, cfg: dict[str, Any], zone_names: dict[str, str]) -> list[dict[str, Any]]:
    """Return one prediction dict per horizon for a zone given its latest feature row."""
    conf_cfg = cfg["confidence"]
    density = feat.get("density")
    reliability = float(feat.get("reliability") or 0.0)
    current_state = congestion_class(density, cfg) if density is not None and not pd.isna(density) else None
    out: list[dict[str, Any]] = []
    x = pd.DataFrame([{c: feat.get(c, np.nan) for c in FEATURE_COLUMNS}]).astype(float)
    ood = {"is_ood": False, "score": None, "reasons": []}
    if bundle.ood is not None and density is not None and not pd.isna(density):
        try:
            ood = bundle.ood.check(x.iloc[0].to_dict())
        except Exception as e:  # pragma: no cover
            log.warning("ood check failed: %s", e)
    reasons = rule_reasons(feat, current_state or "SAFE", zone_names, cfg)
    for h in cfg["forecast_horizons_min"]:
        target = now + timedelta(minutes=h)
        base = {
            "zone_id": zone_id, "created_at": now, "horizon_min": h, "target_time": target, "current_state": current_state,
            "reliability": reliability, "ood_flag": bool(ood["is_ood"]), "ood_score": ood["score"], "ood_reasons": ood["reasons"],
            "ood_message": cfg["ood"]["message"] if ood["is_ood"] else None, "reasons": reasons, "contributions": [], "features": {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in feat.items() if k in FEATURE_COLUMNS},
            "predicted_density": None, "model_type": "", "model_version": bundle.version, "probabilities": {},
        }
        if density is None or pd.isna(density) or reliability < conf_cfg["min_reliability_for_prediction"]:
            out.append({**base, "status": "insufficient_data", "predicted_class": None, "model_confidence": 0.0, "effective_confidence": 0.0, "low_confidence": True, "human_review_required": True,
                        "message": "Insufficient reliable sensor data for this zone. HUMAN REVIEW REQUIRED."})
            continue
        if h not in bundle.classifiers:
            # persistence fallback: future = present, clearly flagged
            probs = {c: (0.6 if c == current_state else 0.2) for c in CLASSES}
            out.append({**base, "status": "fallback", "predicted_class": current_state, "probabilities": probs, "model_confidence": 0.6,
                        "effective_confidence": 0.6 * (0.4 + 0.6 * reliability), "low_confidence": True, "human_review_required": True, "model_type": "persistence_fallback",
                        "message": "No trained model available: showing persistence fallback (future = present). HUMAN REVIEW REQUIRED."})
            continue
        clf = bundle.classifiers[h]
        proba = _proba_in_class_order(clf["model"], x)[0]
        idx = int(proba.argmax())
        model_conf = float(proba[idx])
        rel_factor = float(np.clip(0.4 + 0.6 * reliability, 0.0, 1.0))
        eff = model_conf * rel_factor * (conf_cfg["ood_confidence_multiplier"] if ood["is_ood"] else 1.0)
        low = eff < conf_cfg["low_confidence_threshold"]
        pred_density = None
        if h in bundle.regressors:
            pred_density = float(np.clip(bundle.regressors[h]["model"].predict(x)[0], 0, 1))
        contributions = []
        try:
            contributions = sensitivity_contributions(clf["model"], x, bundle.medians, FEATURE_COLUMNS, idx, top_k=5)
        except Exception as e:  # pragma: no cover
            log.warning("sensitivity failed: %s", e)
        out.append({**base, "status": "ok", "predicted_class": CLASSES[idx], "probabilities": {c: round(float(p), 4) for c, p in zip(CLASSES, proba)},
                    "model_confidence": model_conf, "effective_confidence": float(eff), "low_confidence": bool(low), "human_review_required": bool(low),
                    "predicted_density": pred_density, "model_type": clf["model_type"], "contributions": contributions,
                    "message": "LOW CONFIDENCE - HUMAN REVIEW REQUIRED" if low else None})
    return out


def what_if_prediction(bundle: ModelBundle, feat: dict[str, Any], inflow_multiplier: float) -> dict[str, Any]:
    """Re-run the classifiers with inflow proxies scaled (assumed effect of an intervention).
    Clearly a model what-if, not a validated causal estimate."""
    f = dict(feat)
    for k in ("inflow_proxy", "inflow_lag1", "neighbour_inflow_sum"):
        if f.get(k) is not None and not pd.isna(f.get(k)):
            f[k] = float(f[k]) * inflow_multiplier
    if f.get("inflow_proxy") is not None and f.get("outflow_proxy") is not None and not pd.isna(f["inflow_proxy"]) and not pd.isna(f["outflow_proxy"]):
        f["net_flow_proxy"] = f["inflow_proxy"] - f["outflow_proxy"]
    x = pd.DataFrame([{c: f.get(c, np.nan) for c in FEATURE_COLUMNS}]).astype(float)
    res = {}
    for h, clf in bundle.classifiers.items():
        proba = _proba_in_class_order(clf["model"], x)[0]
        res[str(h)] = {"predicted_class": CLASSES[int(proba.argmax())], "confidence": float(proba.max()), "probabilities": {c: round(float(p), 4) for c, p in zip(CLASSES, proba)}}
        if h in bundle.regressors:
            res[str(h)]["predicted_density"] = float(np.clip(bundle.regressors[h]["model"].predict(x)[0], 0, 1))
    return {"inflow_multiplier": inflow_multiplier, "note": "Model what-if with inflow proxies scaled; assumed effect, not a validated causal estimate.", "horizons": res}
