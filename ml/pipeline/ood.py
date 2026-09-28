"""Out-of-distribution / unusual-condition detection.

Two cheap, explainable mechanisms:
1. feature-range checks against the training distribution (0.5th-99.5th percentiles);
2. an Isolation Forest fitted on the training feature matrix.

When triggered the backend shows:
"Conditions differ from training data. Prediction reliability may be reduced."
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer

RANGE_CHECK_COLUMNS = [
    "density", "density_change_3", "inflow_proxy", "outflow_proxy", "flow_speed_mps",
    "neighbour_density_max", "neighbour_inflow_sum", "disagreement", "obstructed_fraction", "reliability",
]


@dataclass
class OODDetector:
    feature_columns: list[str]
    imputer: SimpleImputer | None = None
    forest: IsolationForest | None = None
    threshold: float = 0.0
    ranges: dict[str, tuple[float, float]] = field(default_factory=dict)
    contamination: float = 0.02

    def fit(self, X: pd.DataFrame, seed: int = 0) -> "OODDetector":
        X = X[self.feature_columns]
        self.imputer = SimpleImputer(strategy="median").fit(X)
        Xi = self.imputer.transform(X)
        self.forest = IsolationForest(n_estimators=200, contamination=self.contamination, random_state=seed, n_jobs=-1).fit(Xi)
        scores = self.forest.decision_function(Xi)
        self.threshold = float(np.percentile(scores, 100 * self.contamination))
        for c in RANGE_CHECK_COLUMNS:
            if c in X.columns:
                col = X[c].dropna()
                if len(col):
                    lo, hi = float(col.quantile(0.005)), float(col.quantile(0.995))
                    pad = 0.1 * (hi - lo)
                    self.ranges[c] = (lo - pad, hi + pad)
        return self

    def score_frame(self, X: pd.DataFrame) -> np.ndarray:
        Xi = self.imputer.transform(X[self.feature_columns])
        return self.forest.decision_function(Xi)

    def check(self, row: pd.Series | dict[str, Any]) -> dict[str, Any]:
        """Return {is_ood, score, reasons}. Lower score = more anomalous."""
        x = pd.DataFrame([row])[self.feature_columns].astype(float)
        score = float(self.score_frame(x)[0])
        reasons: list[str] = []
        for c, (lo, hi) in self.ranges.items():
            v = row.get(c) if isinstance(row, dict) else row[c]
            if v is None or (isinstance(v, float) and np.isnan(v)):
                continue
            if v < lo or v > hi:
                reasons.append(f"{c}={v:.3f} outside training range [{lo:.3f}, {hi:.3f}]")
        forest_flag = score < self.threshold
        if forest_flag:
            reasons.append(f"isolation-forest anomaly score {score:.3f} below threshold {self.threshold:.3f}")
        return {"is_ood": bool(forest_flag or len(reasons) > 0), "score": score, "threshold": self.threshold, "reasons": reasons}

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> "OODDetector":
        return joblib.load(path)
