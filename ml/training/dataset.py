"""Dataset preparation: observations + (optional) ground truth -> labelled feature frame."""
from __future__ import annotations

from typing import Any

import pandas as pd

from ml.pipeline.aggregation import aggregate_zone_bins
from ml.pipeline.features import build_feature_frame
from shared.config import congestion_class, load_config


def context_from_truth(truth: pd.DataFrame) -> pd.DataFrame:
    """Operator-known context (scheduled events, rain) derived from the simulation
    script. In a real deployment this comes from the operator's event schedule and
    a weather feed, not from the sensors."""
    ctx = truth[["zone_id", "timestamp", "event_active", "rain"]].copy()
    ctx["bin_start"] = pd.to_datetime(ctx["timestamp"], utc=True)
    return ctx.rename(columns={"event_active": "event_indicator", "rain": "rain_indicator"})[["zone_id", "bin_start", "event_indicator", "rain_indicator"]]


def prepare_dataset(obs: pd.DataFrame, truth: pd.DataFrame | None = None, cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    cfg = cfg or load_config()
    horizons = cfg["forecast_horizons_min"]
    bin_s = int(cfg["aggregation"]["bin_seconds"])
    states = aggregate_zone_bins(obs, cfg=cfg)
    ctx = context_from_truth(truth) if truth is not None else None
    ff = build_feature_frame(states, cfg=cfg, context=ctx)
    ff["current_state"] = [congestion_class(d, cfg) if pd.notna(d) else None for d in ff["density"]]
    if truth is not None:
        t = truth[["zone_id", "timestamp", "density", "label"]].copy()
        t["bin_start"] = pd.to_datetime(t["timestamp"], utc=True)
        t = t.rename(columns={"density": "true_density", "label": "true_label"}).drop(columns=["timestamp"])
        ff = ff.merge(t, on=["zone_id", "bin_start"], how="left")
        for h in horizons:
            shifted = t.copy()
            shifted["bin_start"] = shifted["bin_start"] - pd.Timedelta(seconds=h * 60)
            shifted = shifted.rename(columns={"true_density": f"true_density_h{h}", "true_label": f"true_label_h{h}"})
            ff = ff.merge(shifted, on=["zone_id", "bin_start"], how="left")
    ff["local_date"] = (ff["bin_start"] + pd.Timedelta(hours=8)).dt.date.astype(str)
    return ff
