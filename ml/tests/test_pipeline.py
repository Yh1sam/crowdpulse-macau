"""ML pipeline tests: deterministic preprocessing, missing data, extreme values, prediction output, schema conformance."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from ml.pipeline.aggregation import aggregate_zone_bins, assign_zone, observation_quality_weight
from ml.pipeline.explain import rule_reasons
from ml.pipeline.features import FEATURE_COLUMNS, build_feature_frame, latest_features
from ml.synthetic.scenarios import golden_week_demo, training_days
from ml.synthetic.simulator import CrowdSimulator, SimParams
from shared.config import CLASSES, congestion_class, load_config, load_zone_graph
from shared.schemas import SensorObservation

MODELS = Path("ml/models")


def small_sim(seed=1, minutes=30, interval=20):
    p = SimParams(seed=seed, start_time=datetime(2026, 10, 2, 3, 0, tzinfo=timezone.utc), duration_min=minutes, sensor_interval_s=interval, day_type="golden_week")
    return CrowdSimulator(p).run()


def test_simulator_output_conforms_to_shared_schema():
    obs, truth = small_sim()
    assert len(obs) > 0 and len(truth) == 30 * 7
    for rec in obs[:300]:
        SensorObservation.model_validate(rec)
    assert not any(k in obs[0] for k in ("face_id", "image", "frame", "name"))


def test_simulator_is_deterministic():
    a, _ = small_sim(seed=5)
    b, _ = small_sim(seed=5)
    assert a == b
    c, _ = small_sim(seed=6)
    assert c != a


def test_preprocessing_is_deterministic_and_complete():
    obs, _ = small_sim()
    df = pd.DataFrame(obs)
    s1 = aggregate_zone_bins(df)
    s2 = aggregate_zone_bins(df.sample(frac=1.0, random_state=0))  # row order must not matter
    pd.testing.assert_frame_equal(s1.reset_index(drop=True), s2.reset_index(drop=True), check_like=True)
    ff = build_feature_frame(s1)
    assert set(FEATURE_COLUMNS) <= set(ff.columns)
    assert ff["density"].between(0, 1).all()
    assert (ff["label_h5"].dropna().isin(CLASSES)).all()


def test_zone_assignment_uses_gps_not_hint():
    g = load_zone_graph()
    z = next(z for z in g["zones"] if z["id"] == "ruins_st_paul")
    assert assign_zone(z["lat"], z["lon"], g) == "ruins_st_paul"
    assert assign_zone(z["lat"], z["lon"], g, zone_hint="senado_square") == "ruins_st_paul"
    assert assign_zone(22.10, 113.60, g) is None, "far away and no zone chosen"
    assert assign_zone(22.10, 113.60, g, zone_hint="nowhere") is None, "unknown zone names are rejected"


def test_zone_choice_places_phones_outside_the_district():
    """A phone at a school (or at home) is placed in the zone the operator chose; GPS still wins in the district."""
    from ml.pipeline.aggregation import place_sensor, resolve_zone_hint
    import copy
    g, cfg = load_zone_graph(), load_config()
    school = (22.2100, 113.5500)            # ~2 km from the district
    far = (51.4988, -0.1749)                # Imperial College London
    assert place_sensor(*school, g, cfg, zone_hint="senado_square")[:2] == ("senado_square", "zone_hint")
    zone, placement, d = place_sensor(*far, g, cfg, zone_hint="Senado Square")
    assert (zone, placement) == ("senado_square", "zone_hint") and d > 9_000_000
    z = next(z for z in g["zones"] if z["id"] == "ruins_st_paul")
    assert place_sensor(z["lat"], z["lon"], g, cfg, zone_hint="senado_square")[:2] == ("ruins_st_paul", "gps")
    for spelling in ("senado_square", "Senado Square", "SENADO SQUARE", "  senado   square ", "senado square"):
        assert resolve_zone_hint(spelling, g) == "senado_square", spelling
    assert resolve_zone_hint("", g) is None and resolve_zone_hint("senado", g) is None
    limited = copy.deepcopy(cfg); limited["sensor"]["zone_hint_max_distance_m"] = 360
    assert place_sensor(*school, g, limited, zone_hint="senado_square") == (None, "none", None), "deployment limit"
    near = (z["lat"] + 0.0015, z["lon"])    # ~170 m from the Ruins, outside every zone radius
    assert place_sensor(*near, g, limited, zone_hint="ruins_st_paul")[:2] == ("ruins_st_paul", "zone_hint")


def test_missing_sensor_data_produces_nan_features_and_staleness():
    obs, _ = small_sim(minutes=20)
    df = pd.DataFrame(obs)
    ts = pd.to_datetime(df["timestamp"], utc=True)
    # drop 6 minutes in the middle for one zone's sensor
    mask = (df["sensor_id"] == "node-f8a6") & ts.between(ts.min() + pd.Timedelta(minutes=8), ts.min() + pd.Timedelta(minutes=14))
    df2 = df[~mask]
    states = aggregate_zone_bins(df2)
    ff = build_feature_frame(states)
    assert ff["staleness_bins"].max() == 0  # senado has a second sensor, so no gap
    only = df2[df2["sensor_id"] != "node-a4b9"]  # remove the second senado sensor too -> real gap
    ff2 = build_feature_frame(aggregate_zone_bins(only))
    sen = ff2[ff2["zone_id"] == "senado_square"]
    assert sen["staleness_bins"].max() >= 5
    assert sen["reliability"].min() < sen["reliability"].max()


def test_quality_weight_penalises_bad_observations():
    cfg = load_config()
    good = {"device_motion_stability": 0.95, "camera_obstructed": False, "location_accuracy_m": 5.0, "vision_confidence": 0.9}
    assert observation_quality_weight(good, cfg) == 1.0
    assert observation_quality_weight({**good, "camera_obstructed": True}, cfg) < 0.2
    assert observation_quality_weight({**good, "device_motion_stability": 0.3}, cfg) < 0.5
    assert observation_quality_weight({**good, "location_accuracy_m": 90.0}, cfg) < 0.5


def test_extreme_values_are_handled():
    obs, _ = small_sim(minutes=10)
    df = pd.DataFrame(obs)
    df.loc[df.index[:50], "person_count"] = 5000
    df.loc[df.index[:50], "estimated_density"] = 1.0
    df.loc[df.index[50:80], "flow_speed_mps"] = 10.0
    states = aggregate_zone_bins(df)
    assert states["density"].between(0, 1).all()
    ff = build_feature_frame(states)
    assert np.isfinite(ff[FEATURE_COLUMNS].fillna(0).to_numpy()).all()
    for rec in df.head(60).to_dict(orient="records"):
        SensorObservation.model_validate(rec)


def test_thresholds_from_central_config():
    cfg = load_config()
    th = cfg["congestion_thresholds"]
    assert congestion_class(th["warning"] - 0.01) == "SAFE"
    assert congestion_class(th["warning"]) == "WARNING"
    assert congestion_class(th["critical"]) == "CRITICAL"


def test_rule_reasons_mention_key_drivers():
    feat = {"density": 0.6, "density_lag3": 0.45, "inflow_proxy": 0.4, "outflow_proxy": 0.2, "neighbour_density_max": 0.75, "neighbour_max_zone": "st_dominic",
            "neighbour_density_change_3": 0.1, "flow_speed_mps": 0.4, "speed_change_3": -0.2, "reliability": 0.9}
    reasons = rule_reasons(feat, "CRITICAL", {"st_dominic": "St. Dominic's Square"})
    text = " ".join(reasons)
    assert "increased 33%" in text and "inflow exceeds outflow" in text and "St. Dominic's Square is CRITICAL" in text and "walking speed has fallen" in text


@pytest.mark.skipif(not (MODELS / "congestion_h5.joblib").exists(), reason="models not trained")
def test_trained_models_predict_valid_output():
    from backend.app.services.prediction import load_models, predict_zone
    bundle = load_models(MODELS)
    assert bundle.loaded and set(bundle.classifiers) == {5, 10, 15}
    obs, _ = small_sim(minutes=15)
    states = aggregate_zone_bins(pd.DataFrame(obs))
    feats = latest_features(states)
    cfg = load_config()
    for _, row in feats.iterrows():
        feat = {k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.to_dict().items()}
        preds = predict_zone(bundle, feat, row["zone_id"], datetime.now(timezone.utc), cfg, {})
        assert len(preds) == 3
        for p in preds:
            assert p["status"] == "ok" and p["predicted_class"] in CLASSES
            assert abs(sum(p["probabilities"].values()) - 1) < 1e-3
            assert 0 <= p["effective_confidence"] <= p["model_confidence"] <= 1
            assert len(p["contributions"]) == 5


@pytest.mark.skipif(not (MODELS / "ood.joblib").exists(), reason="models not trained")
def test_ood_detector_flags_absurd_input_and_accepts_normal():
    from ml.pipeline.ood import OODDetector
    ood = OODDetector.load(str(MODELS / "ood.joblib"))
    obs, _ = small_sim(minutes=15)
    feats = latest_features(aggregate_zone_bins(pd.DataFrame(obs)))
    normal = feats.iloc[0][FEATURE_COLUMNS].astype(float).to_dict()
    weird = {**normal, "density": 1.0, "density_change_3": 0.9, "flow_speed_mps": 9.5, "inflow_proxy": 5.0, "neighbour_inflow_sum": 9.0, "disagreement": 0.9}
    assert ood.check(weird)["is_ood"] is True
    assert isinstance(ood.check(normal)["is_ood"], bool)


def test_demo_scenario_reaches_critical_at_senado():
    sim = CrowdSimulator(golden_week_demo(sensor_interval_s=60))
    _, truth = sim.run()
    sen = [r for r in truth if r["zone_id"] == "senado_square"][:45]
    assert sen[0]["label"] in ("SAFE", "WARNING")
    assert any(r["label"] == "CRITICAL" for r in sen[15:45])


def test_training_days_have_mixed_day_types():
    days = training_days(14)
    assert {p.day_type for p in days} == {"weekday", "weekend", "golden_week"}


def test_rule_reasons_avoid_percentages_against_near_zero_flow():
    reasons = " ".join(rule_reasons({"density": 0.17, "inflow_proxy": 0.36, "outflow_proxy": 0.0}, "SAFE", {}))
    assert "%" not in reasons.split("density")[0] and "almost nobody is leaving" in reasons
    assert "draining" in " ".join(rule_reasons({"density": 0.5, "inflow_proxy": 0.0, "outflow_proxy": 0.3}, "SAFE", {}))


def test_rule_reasons_small_nearly_equal_flows_are_balanced():
    text = " ".join(rule_reasons({"density": 0.3, "inflow_proxy": 0.021, "outflow_proxy": 0.019}, "SAFE", {}))
    assert "almost nobody" not in text
