"""Observation -> zone-state aggregation.

This module is the SINGLE implementation used by both the offline training
pipeline and the live backend, so synthetic and real observations are treated
identically.

Pipeline
--------
observations (one row per sensor message)
  -> zone assignment (nearest zone centroid within a radius; zone_hint is only a hint)
  -> per-observation quality weight (stability, obstruction, GPS, vision confidence)
  -> per (zone, time-bin) aggregate: density, visible count, flow vector, speed,
     reliability, sensor disagreement
  -> graph pass: inflow/outflow proxies and neighbour context
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from shared.config import congestion_class, load_config, load_zone_graph
from shared.geo import haversine_m, bearing_deg

OBS_COLUMNS = [
    "sensor_id", "timestamp", "latitude", "longitude", "location_accuracy_m", "heading_deg",
    "device_motion_stability", "person_count", "estimated_density", "flow_direction_deg",
    "flow_speed_mps", "vision_confidence", "camera_obstructed", "model_version",
]

ZONE_STATE_COLUMNS = [
    "zone_id", "bin_start", "density", "person_count_visible", "flow_direction_deg", "flow_speed_mps",
    "flow_coherence", "n_obs", "n_sensors", "reliability", "disagreement", "obstructed_fraction",
    "mean_stability", "mean_gps_accuracy_m", "mean_vision_confidence", "congestion_state",
    "inflow_proxy", "outflow_proxy", "neighbour_density_mean", "neighbour_density_max",
    "neighbour_inflow_sum", "neighbour_max_zone",
]


# --------------------------------------------------------------- assignment
def assign_zone(lat: float, lon: float, graph: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None, zone_hint: str | None = None) -> str | None:
    """Nearest zone centroid within the configured radius, else None."""
    graph = graph or load_zone_graph()
    cfg = cfg or load_config()
    radius = cfg["sensor"]["zone_assignment_radius_m"]
    best, best_d = None, float("inf")
    for z in graph["zones"]:
        d = haversine_m(lat, lon, z["lat"], z["lon"])
        if d < best_d:
            best, best_d = z["id"], d
    if best is not None and best_d <= radius:
        return best
    # fall back to the hint only if it is a known zone and the GPS is merely imprecise (< 3x radius)
    if zone_hint and any(z["id"] == zone_hint for z in graph["zones"]) and best_d <= 3 * radius:
        return zone_hint
    return None


def assign_zones_df(obs: pd.DataFrame, graph: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None) -> pd.DataFrame:
    graph = graph or load_zone_graph()
    cfg = cfg or load_config()
    zlat = np.array([z["lat"] for z in graph["zones"]])
    zlon = np.array([z["lon"] for z in graph["zones"]])
    zids = np.array([z["id"] for z in graph["zones"]])
    lat = np.radians(obs["latitude"].to_numpy(dtype=float))[:, None]
    lon = np.radians(obs["longitude"].to_numpy(dtype=float))[:, None]
    zl = np.radians(zlat)[None, :]
    zo = np.radians(zlon)[None, :]
    a = np.sin((zl - lat) / 2) ** 2 + np.cos(lat) * np.cos(zl) * np.sin((zo - lon) / 2) ** 2
    dist = 2 * 6_371_000.0 * np.arcsin(np.sqrt(a))
    idx = dist.argmin(axis=1)
    best_d = dist[np.arange(len(obs)), idx]
    out = obs.copy()
    out["zone_id"] = np.where(best_d <= cfg["sensor"]["zone_assignment_radius_m"], zids[idx], None)
    out["zone_distance_m"] = best_d
    return out


# ------------------------------------------------------------------ weights
def observation_quality_weight(row: pd.Series | dict[str, Any], cfg: dict[str, Any] | None = None) -> float:
    cfg = cfg or load_config()
    r = cfg["reliability"]
    stab = float(row["device_motion_stability"])
    stab_f = min(1.0, max(0.0, (stab - 0.5) / (r["min_motion_stability"] - 0.5))) if stab < r["min_motion_stability"] else 1.0
    obst_f = 0.15 if bool(row["camera_obstructed"]) else 1.0
    acc = float(row["location_accuracy_m"])
    gps_f = 1.0 if acc <= r["max_gps_accuracy_m"] else max(0.3, r["max_gps_accuracy_m"] / acc)
    vis = float(row["vision_confidence"])
    vis_f = min(1.0, max(0.1, vis / max(1e-6, r["min_vision_confidence"]))) if vis < r["min_vision_confidence"] else 1.0
    return float(stab_f * obst_f * gps_f * vis_f)


def quality_weights_df(obs: pd.DataFrame, cfg: dict[str, Any] | None = None) -> np.ndarray:
    cfg = cfg or load_config()
    r = cfg["reliability"]
    stab = obs["device_motion_stability"].to_numpy(dtype=float)
    stab_f = np.where(stab < r["min_motion_stability"], np.clip((stab - 0.5) / (r["min_motion_stability"] - 0.5), 0, 1), 1.0)
    obst_f = np.where(obs["camera_obstructed"].astype(bool).to_numpy(), 0.15, 1.0)
    acc = obs["location_accuracy_m"].to_numpy(dtype=float)
    gps_f = np.where(acc <= r["max_gps_accuracy_m"], 1.0, np.maximum(0.3, r["max_gps_accuracy_m"] / np.maximum(acc, 1e-6)))
    vis = obs["vision_confidence"].to_numpy(dtype=float)
    vis_f = np.where(vis < r["min_vision_confidence"], np.clip(vis / max(1e-6, r["min_vision_confidence"]), 0.1, 1.0), 1.0)
    return stab_f * obst_f * gps_f * vis_f


# -------------------------------------------------------------- aggregation
def _circ_mean(deg: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    """Weighted circular mean (deg) and resultant length (0..1 = coherence)."""
    if len(deg) == 0 or w.sum() <= 0:
        return float("nan"), 0.0
    r = np.radians(deg)
    e = float((w * np.sin(r)).sum() / w.sum())
    n = float((w * np.cos(r)).sum() / w.sum())
    return (math.degrees(math.atan2(e, n)) + 360.0) % 360.0, float(math.hypot(e, n))


def aggregate_zone_bins(obs: pd.DataFrame, graph: dict[str, Any] | None = None, cfg: dict[str, Any] | None = None, expected_sensors: dict[str, int] | None = None) -> pd.DataFrame:
    """Aggregate observations into (zone, bin) states. ``obs`` must contain the
    schema columns; ``zone_id`` is computed if absent. Returns a DataFrame with
    one row per zone per bin that has at least one observation. Fully vectorised."""
    graph = graph or load_zone_graph()
    cfg = cfg or load_config()
    if obs.empty:
        return pd.DataFrame(columns=ZONE_STATE_COLUMNS)
    df = obs.copy()
    if "zone_id" not in df.columns or df["zone_id"].isna().all():
        df = assign_zones_df(df, graph, cfg)
    df = df[df["zone_id"].notna()].copy()
    if df.empty:
        return pd.DataFrame(columns=ZONE_STATE_COLUMNS)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    bin_s = int(cfg["aggregation"]["bin_seconds"])
    df["bin_start"] = ts.dt.floor(f"{bin_s}s")
    df["w"] = quality_weights_df(df, cfg)
    df["camera_obstructed"] = df["camera_obstructed"].astype(bool).astype(float)
    if expected_sensors is None:
        expected_sensors = {}
        for s in graph.get("sensors", []):
            expected_sensors[s["zone_id"]] = expected_sensors.get(s["zone_id"], 0) + 1
    r = cfg["reliability"]
    keys = ["zone_id", "bin_start"]
    g = df.groupby(keys, sort=True)
    wsum = g["w"].transform("sum")
    df["eff_w"] = np.where(wsum > 1e-6, df["w"], 1.0)
    dens = df["estimated_density"].to_numpy(dtype=float)
    spd = df["flow_speed_mps"].to_numpy(dtype=float)
    rad = np.radians(df["flow_direction_deg"].to_numpy(dtype=float))
    df["_wd"] = df["eff_w"] * dens
    df["_ws"] = df["eff_w"] * spd
    df["_sw"] = df["eff_w"] * np.maximum(spd, 1e-3)
    df["_sin"] = df["_sw"] * np.sin(rad)
    df["_cos"] = df["_sw"] * np.cos(rad)
    agg = df.groupby(keys, sort=True).agg(
        n_obs=("w", "size"), quality=("w", "mean"), eff_wsum=("eff_w", "sum"), _wd=("_wd", "sum"), _ws=("_ws", "sum"),
        _sw=("_sw", "sum"), _sin=("_sin", "sum"), _cos=("_cos", "sum"), obstructed_fraction=("camera_obstructed", "mean"),
        mean_stability=("device_motion_stability", "mean"), mean_gps_accuracy_m=("location_accuracy_m", "mean"),
        mean_vision_confidence=("vision_confidence", "mean"),
    ).reset_index()
    per_sensor = df.groupby(keys + ["sensor_id"], sort=True).agg(density=("estimated_density", "mean"), count=("person_count", "mean")).reset_index()
    ps = per_sensor.groupby(keys, sort=True).agg(n_sensors=("sensor_id", "nunique"), person_count_visible=("count", "sum"), disagreement=("density", lambda s: float(s.std(ddof=0)) if len(s) > 1 else 0.0)).reset_index()
    agg = agg.merge(ps, on=keys, how="left")
    agg["density"] = agg["_wd"] / agg["eff_wsum"]
    agg["flow_speed_mps"] = agg["_ws"] / agg["eff_wsum"]
    e = agg["_sin"] / agg["_sw"]
    n = agg["_cos"] / agg["_sw"]
    agg["flow_direction_deg"] = (np.degrees(np.arctan2(e, n)) + 360.0) % 360.0
    agg["flow_coherence"] = np.hypot(e, n)
    expected = agg["zone_id"].map(lambda z: max(1, expected_sensors.get(z, 1))).to_numpy(dtype=float)
    online_f = np.minimum(1.0, agg["n_sensors"].to_numpy(dtype=float) / expected)
    quality_f = agg["quality"].to_numpy(dtype=float)
    disagreement_f = np.maximum(0.0, 1.0 - r["disagreement_penalty_scale"] * agg["disagreement"].to_numpy(dtype=float))
    w_q = r["weights"]["stability"] + r["weights"]["obstruction"] + r["weights"]["gps"] + r["weights"]["vision"]
    agg["reliability"] = np.clip(r["weights"]["online"] * online_f + w_q * quality_f, 0, 1) * disagreement_f
    th = cfg["congestion_thresholds"]
    agg["congestion_state"] = np.select([agg["density"] >= th["critical"], agg["density"] >= th["warning"]], ["CRITICAL", "WARNING"], default="SAFE")
    agg["n_obs"] = agg["n_obs"].astype(int)
    agg["n_sensors"] = agg["n_sensors"].astype(int)
    return add_graph_context(agg, graph)


def add_graph_context(states: pd.DataFrame, graph: dict[str, Any] | None = None) -> pd.DataFrame:
    """Add inflow/outflow proxies and neighbour context using the zone graph.

    outflow_proxy(z) = density_z * speed_z * sum_n max(0, cos(dir_z - bearing(z->n))) * coherence_z
    inflow_proxy(z)  = sum_n density_n * speed_n * max(0, cos(dir_n - bearing(n->z))) * coherence_n
    These are observable proxies derived only from the anonymous flow vectors."""
    graph = graph or load_zone_graph()
    ctx_cols = ["inflow_proxy", "outflow_proxy", "neighbour_density_mean", "neighbour_density_max", "neighbour_inflow_sum", "neighbour_max_zone"]
    if states.empty:
        out = states.copy()
        for c in ctx_cols:
            out[c] = pd.Series(dtype=object if c == "neighbour_max_zone" else float)
        return out.reindex(columns=ZONE_STATE_COLUMNS)
    zones = {z["id"]: z for z in graph["zones"]}
    rows = []
    for e in graph["edges"]:
        a, b = e["from"], e["to"]
        bab = bearing_deg(zones[a]["lat"], zones[a]["lon"], zones[b]["lat"], zones[b]["lon"])
        bba = (bab + 180.0) % 360.0
        rows.append({"zone_id": a, "nbr": b, "bearing_zn": bab, "bearing_nz": bba})
        rows.append({"zone_id": b, "nbr": a, "bearing_zn": bba, "bearing_nz": bab})
    edges = pd.DataFrame(rows)
    st = states.copy()
    st["flow_coherence"] = st["flow_coherence"].fillna(0.0)
    base = st[["zone_id", "bin_start", "density", "flow_speed_mps", "flow_direction_deg", "flow_coherence"]]
    pairs = base.merge(edges, on="zone_id", how="left")
    nb = base.rename(columns={"zone_id": "nbr", "density": "n_density", "flow_speed_mps": "n_speed", "flow_direction_deg": "n_dir", "flow_coherence": "n_coh"})
    pairs = pairs.merge(nb, on=["nbr", "bin_start"], how="left")
    toward_zn = np.maximum(0.0, np.cos(np.radians(pairs["flow_direction_deg"] - pairs["bearing_zn"]))) * pairs["flow_coherence"]
    pairs["_out"] = pairs["density"] * pairs["flow_speed_mps"] * toward_zn.fillna(0.0)
    toward_nz = np.maximum(0.0, np.cos(np.radians(pairs["n_dir"] - pairs["bearing_nz"]))) * pairs["n_coh"]
    pairs["_in"] = (pairs["n_density"] * pairs["n_speed"] * toward_nz).fillna(0.0)
    grp = pairs.groupby(["zone_id", "bin_start"], sort=False)
    ctx = grp.agg(outflow_proxy=("_out", "sum"), inflow_proxy=("_in", "sum"), neighbour_density_mean=("n_density", "mean"), neighbour_density_max=("n_density", "max")).reset_index()
    # zone of the densest neighbour
    valid = pairs[pairs["n_density"].notna()]
    if not valid.empty:
        idx = valid.groupby(["zone_id", "bin_start"])["n_density"].idxmax()
        mz = valid.loc[idx, ["zone_id", "bin_start", "nbr"]].rename(columns={"nbr": "neighbour_max_zone"})
        ctx = ctx.merge(mz, on=["zone_id", "bin_start"], how="left")
    else:
        ctx["neighbour_max_zone"] = None
    st = st.merge(ctx, on=["zone_id", "bin_start"], how="left")
    # neighbour inflow sum (second pass over neighbours' inflow proxies)
    inflow_nb = st[["zone_id", "bin_start", "inflow_proxy"]].rename(columns={"zone_id": "nbr", "inflow_proxy": "n_inflow"})
    p2 = edges[["zone_id", "nbr"]].merge(st[["zone_id", "bin_start"]], on="zone_id").merge(inflow_nb, on=["nbr", "bin_start"], how="left")
    nis = p2.groupby(["zone_id", "bin_start"], sort=False)["n_inflow"].sum(min_count=1).fillna(0.0).reset_index().rename(columns={"n_inflow": "neighbour_inflow_sum"})
    st = st.merge(nis, on=["zone_id", "bin_start"], how="left")
    st["neighbour_inflow_sum"] = st["neighbour_inflow_sum"].fillna(0.0)
    return st.reindex(columns=ZONE_STATE_COLUMNS)
