"""Metric helpers shared by training and evaluation."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from shared.config import CLASSES


def expected_calibration_error(y_true_idx: np.ndarray, proba: np.ndarray, n_bins: int = 10) -> float:
    conf = proba.max(axis=1)
    pred = proba.argmax(axis=1)
    correct = (pred == y_true_idx).astype(float)
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return float(ece)


def classification_metrics(y_true: list[str] | np.ndarray, y_pred: list[str] | np.ndarray, proba: np.ndarray | None = None) -> dict[str, Any]:
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    out: dict[str, Any] = {
        "n": int(len(y_true)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_macro": float(precision_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)),
        "recall_macro": float(recall_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)),
        "f1_macro": float(f1_score(y_true, y_pred, labels=CLASSES, average="macro", zero_division=0)),
        "f1_weighted": float(f1_score(y_true, y_pred, labels=CLASSES, average="weighted", zero_division=0)),
        "per_class": {},
        "confusion_matrix": confusion_matrix(y_true, y_pred, labels=CLASSES).tolist(),
        "classes": CLASSES,
        "support": {c: int((y_true == c).sum()) for c in CLASSES},
    }
    p = precision_score(y_true, y_pred, labels=CLASSES, average=None, zero_division=0)
    r = recall_score(y_true, y_pred, labels=CLASSES, average=None, zero_division=0)
    f = f1_score(y_true, y_pred, labels=CLASSES, average=None, zero_division=0)
    for i, c in enumerate(CLASSES):
        out["per_class"][c] = {"precision": float(p[i]), "recall": float(r[i]), "f1": float(f[i])}
    if proba is not None:
        y_idx = np.array([CLASSES.index(c) for c in y_true])
        out["ece"] = expected_calibration_error(y_idx, proba)
        present = np.unique(y_idx)
        if len(present) == len(CLASSES):
            try:
                out["roc_auc_ovr_macro"] = float(roc_auc_score(y_idx, proba, multi_class="ovr", average="macro"))
            except ValueError:
                out["roc_auc_ovr_macro"] = None
        else:
            out["roc_auc_ovr_macro"] = None
    return out
