"""Zone-state -> ML feature frame (with lag features and future labels).

Used by training (offline, whole dataset) and by the backend (live, last few
bins) so features are computed identically in both places.
"""
from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd

from shared.config import congestion_class, load_config

FEATURE_COLUMNS = [
    "density", "density_lag1", "density_lag2", "density_lag3", "density_change_1", "density_change_3",
    "inflow_proxy", "outflow_proxy", "net_flow_proxy", "inflow_lag1",
    "flow_speed_mps", "speed_change_3", "flow_coherence",
    "neighbour_density_mean", "neighbour_density_max", "neighbour_inflow_sum", "neighbour_density_change_3",
    "hour_sin", "hour_cos", "day_type", "event_indicator", "rain_indicator",
    "reliability", "n_sensors", "disagreement", "obstructed_fraction", "staleness_bins",
]
CONTEXT_COLUMNS = ["day_type", "event_indicator", "rain_indicator"]
MACAU_UTC_OFFSET_H = 8
MAX_STALENESS_BINS = 10


def day_type_for(ts: pd.Timestamp) -> int:
    """0 = weekday, 1 = weekend, 2 = Golden Week (1-7 Oct, and 1-3 May). Operator-configurable in a real deployment."""
    lt = ts + pd.Timedelta(hours=MACAU_UTC_OFFSET_H)
    d: date = lt.date()
    if (d.month == 10 and 1 <= d.day <= 7) or (d.month == 5 and 1 <= d.day <= 3):
        return 2
    return 1 if d.weekday() >= 5 else 0


def build_feature_frame(states: pd.DataFrame, cfg: dict[str, Any] | None = None, horizons: list[int] | None = None, context: pd.DataFrame | None = None, with_labels: bool = True) -> pd.DataFrame:
    """Build features per (zone, bin).

    ``states``: output of ``aggregate_zone_bins``.
    ``context``: optional frame with columns [zone_id, bin_start, event_indicator, rain_indicator]
    (operator-known schedule / weather). Missing -> 0.
    Labels ``label_h{h}`` / ``density_h{h}`` are the aggregated OBSERVED density h bins ahead.
    """
    cfg = cfg or load_config()
    horizons = horizons or cfg["forecast_horizons_min"]
    bin_s = int(cfg["aggregation"]["bin_seconds"])
    if states.empty:
        return pd.DataFrame(columns=["zone_id", "bin_start", *FEATURE_COLUMNS])
    df = states.copy()
    df["bin_start"] = pd.to_datetime(df["bin_start"], utc=True)
    df = df.sort_values(["zone_id", "bin_start"]).reset_index(drop=True)
    out_parts = []
    for zone_id, g in df.groupby("zone_id", sort=False):
        g = g.set_index("bin_start")
        full_idx = pd.date_range(g.index.min(), g.index.max(), freq=f"{bin_s}s", tz="UTC")
        g = g.reindex(full_idx)
        g.index.name = "bin_start"
        g["zone_id"] = zone_id
        observed = g["density"].notna()
        # staleness: number of bins since the last observation (0 when observed in this bin)
        grp = observed.cumsum()
        g["staleness_bins"] = (~observed).groupby(grp).cumsum().astype(int)
        # forward-fill numeric state for up to 5 bins so short dropouts do not kill features
        num_cols = ["density", "person_count_visible", "flow_direction_deg", "flow_speed_mps", "flow_coherence", "inflow_proxy", "outflow_proxy",
                    "neighbour_density_mean", "neighbour_density_max", "neighbour_inflow_sum", "reliability", "disagreement", "obstructed_fraction"]
        g[num_cols] = g[num_cols].ffill(limit=5)
        g["n_sensors"] = g["n_sensors"].fillna(0)
        g["n_obs"] = g["n_obs"].fillna(0)
        g.loc[~observed, "reliability"] = g.loc[~observed, "reliability"].fillna(0.0) * np.clip(1 - 0.25 * g.loc[~observed, "staleness_bins"], 0, 1)
        g["density_lag1"] = g["density"].shift(1)
        g["density_lag2"] = g["density"].shift(2)
        g["density_lag3"] = g["density"].shift(3)
        g["density_change_1"] = g["density"] - g["density_lag1"]
        g["density_change_3"] = g["density"] - g["density_lag3"]
        g["net_flow_proxy"] = g["inflow_proxy"] - g["outflow_proxy"]
        g["inflow_lag1"] = g["inflow_proxy"].shift(1)
        g["speed_change_3"] = g["flow_speed_mps"] - g["flow_speed_mps"].shift(3)
        g["neighbour_density_change_3"] = g["neighbour_density_mean"] - g["neighbour_density_mean"].shift(3)
        hour = (g.index + pd.Timedelta(hours=MACAU_UTC_OFFSET_H)).hour + (g.index + pd.Timedelta(hours=MACAU_UTC_OFFSET_H)).minute / 60.0
        g["hour_sin"] = np.sin(2 * np.pi * hour / 24.0)
        g["hour_cos"] = np.cos(2 * np.pi * hour / 24.0)
        g["day_type"] = [day_type_for(t) for t in g.index]
        g["event_indicator"] = 0
        g["rain_indicator"] = 0
        if with_labels:
            for h in horizons:
                steps = int(round(h * 60 / bin_s))
                fut = g["density"].shift(-steps)
                g[f"density_h{h}"] = fut
                g[f"label_h{h}"] = [congestion_class(v, cfg) if pd.notna(v) else None for v in fut]
        out_parts.append(g.reset_index())
    out = pd.concat(out_parts, ignore_index=True)
    # rows unobserved for a long time (e.g. overnight when sensors are off) carry no information
    out = out[out["staleness_bins"] <= MAX_STALENESS_BINS].reset_index(drop=True)
    if context is not None and not context.empty:
        ctx = context.copy()
        ctx["bin_start"] = pd.to_datetime(ctx["bin_start"], utc=True)
        out = out.drop(columns=["event_indicator", "rain_indicator"]).merge(ctx[["zone_id", "bin_start", "event_indicator", "rain_indicator"]], on=["zone_id", "bin_start"], how="left")
        out["event_indicator"] = out["event_indicator"].fillna(0).astype(int)
        out["rain_indicator"] = out["rain_indicator"].fillna(0).astype(int)
    return out


def latest_features(states: pd.DataFrame, cfg: dict[str, Any] | None = None, context: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return the last feature row per zone (used by the live prediction service)."""
    ff = build_feature_frame(states, cfg=cfg, context=context, with_labels=False)
    if ff.empty:
        return ff
    return ff.sort_values("bin_start").groupby("zone_id").tail(1).reset_index(drop=True)


def feature_matrix(ff: pd.DataFrame) -> pd.DataFrame:
    """Select model inputs (NaN allowed; models use imputation)."""
    return ff[FEATURE_COLUMNS].astype(float)
