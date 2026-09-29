"""Explainability for congestion predictions.

* ``rule_reasons``: human-readable reasons derived directly from the features
  (always available, deterministic, no model needed).
* ``sensitivity_contributions``: a light-weight local sensitivity analysis:
  each feature is replaced by its training median and the change in the
  predicted-class probability is measured. This is NOT SHAP; it is a cheap,
  honest approximation of "which inputs pushed this prediction".
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from shared.config import load_config

FEATURE_LABELS = {
    "density": "current density", "density_lag1": "density 1 min ago", "density_lag2": "density 2 min ago", "density_lag3": "density 3 min ago",
    "density_change_1": "1-min density change", "density_change_3": "3-min density change", "inflow_proxy": "inflow proxy", "outflow_proxy": "outflow proxy",
    "net_flow_proxy": "net flow (in - out)", "inflow_lag1": "inflow 1 min ago", "flow_speed_mps": "walking speed", "speed_change_3": "3-min speed change",
    "flow_coherence": "flow coherence", "neighbour_density_mean": "neighbour density (mean)", "neighbour_density_max": "neighbour density (max)",
    "neighbour_inflow_sum": "neighbour inflow", "neighbour_density_change_3": "neighbour density change", "hour_sin": "time of day", "hour_cos": "time of day",
    "day_type": "day type", "event_indicator": "scheduled event", "rain_indicator": "rain", "reliability": "sensor reliability", "n_sensors": "sensors online",
    "disagreement": "sensor disagreement", "obstructed_fraction": "camera obstruction", "staleness_bins": "data staleness",
}


def _ok(v: Any) -> bool:
    return v is not None and not (isinstance(v, float) and math.isnan(v))


def rule_reasons(feat: dict[str, Any], predicted: str, zone_names: dict[str, str] | None = None, cfg: dict[str, Any] | None = None) -> list[str]:
    cfg = cfg or load_config()
    th = cfg["congestion_thresholds"]
    zone_names = zone_names or {}
    reasons: list[str] = []
    d, d3 = feat.get("density"), feat.get("density_lag3")
    if _ok(d) and _ok(d3) and d3 > 0.05:
        pct = (d - d3) / d3 * 100.0
        if abs(pct) >= 10:
            reasons.append(f"density {'increased' if pct > 0 else 'decreased'} {abs(pct):.0f}% in the last 3 minutes (now {d:.2f})")
    inflow, outflow = feat.get("inflow_proxy"), feat.get("outflow_proxy")
    if _ok(inflow) and _ok(outflow):
        if max(inflow, outflow) < 0.02:
            reasons.append("very little movement in or out of the zone")
        elif min(inflow, outflow) < 0.02 and max(inflow, outflow) >= 0.05:
            # a percentage against a near-zero denominator reads as nonsense ("exceeds by 3584%")
            reasons.append("people are arriving but almost nobody is leaving" if inflow > outflow else "people are leaving and almost nobody is arriving (zone draining)")
        elif inflow > outflow * 1.15 + 0.01:
            reasons.append(f"inflow exceeds outflow by {((inflow - outflow) / max(outflow, 0.01)) * 100:.0f}% (net inflow)")
        elif outflow > inflow * 1.15 + 0.01:
            reasons.append(f"outflow exceeds inflow by {((outflow - inflow) / max(inflow, 0.01)) * 100:.0f}% (zone draining)")
        else:
            reasons.append("inflow and outflow are roughly balanced")
    nmax, nchg = feat.get("neighbour_density_max"), feat.get("neighbour_density_change_3")
    if _ok(nmax) and nmax >= th["warning"]:
        name = zone_names.get(feat.get("neighbour_max_zone") or "", feat.get("neighbour_max_zone") or "an adjacent zone")
        state = "CRITICAL" if nmax >= th["critical"] else "WARNING"
        trend = " and filling" if _ok(nchg) and nchg > 0.03 else (" and emptying" if _ok(nchg) and nchg < -0.03 else "")
        reasons.append(f"adjacent zone {name} is {state} ({nmax:.2f}){trend}")
    v, dv = feat.get("flow_speed_mps"), feat.get("speed_change_3")
    if _ok(v) and _ok(dv) and dv < -0.08:
        reasons.append(f"walking speed has fallen by {abs(dv):.2f} m/s to {v:.2f} m/s")
    if feat.get("event_indicator"):
        reasons.append("a scheduled event is ending nearby (operator-provided schedule)")
    if feat.get("rain_indicator"):
        reasons.append("rain reported: camera-based counts are less accurate")
    rel = feat.get("reliability")
    if _ok(rel) and rel < 0.6:
        reasons.append(f"sensor reliability is low ({rel:.2f}); treat the estimate with caution")
    if not reasons:
        reasons.append(f"conditions are stable (density {d:.2f})" if _ok(d) else "insufficient recent data")
    return reasons


def sensitivity_contributions(model: Any, x: pd.DataFrame, reference: dict[str, float], feature_columns: list[str], class_idx: int, top_k: int = 5) -> list[dict[str, Any]]:
    """Local sensitivity: for each feature, replace by its training median and measure the
    drop in P(predicted class). Positive delta = this feature's actual value pushed the
    prediction towards the predicted class. One batched predict_proba call."""
    x = x[feature_columns].astype(float)
    rows = [x.iloc[0].to_dict()]
    for f in feature_columns:
        r = x.iloc[0].to_dict()
        r[f] = reference.get(f, r[f])
        rows.append(r)
    batch = pd.DataFrame(rows, columns=feature_columns)
    proba = model.predict_proba(batch)[:, class_idx]
    base = float(proba[0])
    out = []
    for i, f in enumerate(feature_columns):
        delta = base - float(proba[i + 1])
        val = x.iloc[0][f]
        out.append({"feature": f, "label": FEATURE_LABELS.get(f, f), "delta": round(delta, 4), "value": None if pd.isna(val) else round(float(val), 4), "reference": round(float(reference.get(f, float("nan"))), 4) if f in reference else None})
    out.sort(key=lambda r: abs(r["delta"]), reverse=True)
    return out[:top_k]
