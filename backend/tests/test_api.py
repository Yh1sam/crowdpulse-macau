"""Backend API tests: schema validation, ingestion, aggregation, prediction, interventions, error handling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from shared.config import load_zone_graph

GRAPH = load_zone_graph()
SENADO = next(z for z in GRAPH["zones"] if z["id"] == "senado_square")


def obs(sensor_id="node-test1", ts=None, lat=None, lon=None, density=0.3, count=30, stability=0.95, obstructed=False, **kw):
    ts = ts or datetime.now(timezone.utc)
    d = {"sensor_id": sensor_id, "timestamp": ts.isoformat(), "latitude": lat if lat is not None else SENADO["lat"], "longitude": lon if lon is not None else SENADO["lon"],
         "location_accuracy_m": 5.0, "heading_deg": 120.0, "device_motion_stability": stability, "person_count": count, "estimated_density": density,
         "flow_direction_deg": 200.0, "flow_speed_mps": 0.9, "vision_confidence": 0.9, "camera_obstructed": obstructed, "model_version": "test-1"}
    d.update(kw)
    return d


def test_health_and_config(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["status"] == "ok" and r.json()["privacy_mode"] is True
    c = client.get("/config").json()
    assert c["congestion_thresholds"]["critical"] > c["congestion_thresholds"]["warning"]
    assert len(c["zone_graph"]["zones"]) == 7


def test_schema_rejects_identifying_and_invalid_fields(client):
    r = client.post("/sensor/observation", json=obs(face_id="abc"))
    assert r.status_code == 422
    r = client.post("/sensor/observation", json=obs(lat=95.0))
    assert r.status_code == 422
    r = client.post("/sensor/observation", json={**obs(), "sensor_id": "john-smith-iphone"})
    assert r.status_code == 422
    r = client.post("/sensor/observation", json={**obs(), "estimated_density": 1.7})
    assert r.status_code == 422


def test_privacy_mode_blocks_media_uploads(client):
    r = client.post("/sensor/observation", files={"file": ("frame.jpg", b"\xff\xd8\xff", "image/jpeg")})
    assert r.status_code == 403
    r = client.post("/sensor/frame")
    assert r.status_code == 403


def test_ingestion_assigns_zone_and_lists_sensor(client):
    r = client.post("/sensor/observation", json=obs())
    assert r.status_code == 202
    body = r.json()
    assert body["accepted"] == 1 and body["zone_assignments"]["node-test1"] == "senado_square"
    sensors = client.get("/sensors").json()
    assert len(sensors) == 1 and sensors[0]["zone_id"] == "senado_square" and sensors[0]["status"] == "online"
    # far away from every zone -> unassigned but still accepted
    r = client.post("/sensor/observation", json=obs(sensor_id="node-far1", lat=22.15, lon=113.55))
    assert r.json()["zone_assignments"]["node-far1"] is None
    s = client.get("/sensors/node-far1").json()
    assert "outside any zone" in s["issues"]


def test_batch_ingestion_and_zone_aggregation(client):
    now = datetime.now(timezone.utc)
    batch = {"observations": [obs(ts=now - timedelta(seconds=s), density=0.5 + 0.01 * (s % 3)) for s in range(0, 120, 5)]}
    r = client.post("/sensor/observation", json=batch)
    assert r.status_code == 202 and r.json()["accepted"] == 24
    z = client.get("/zones/senado_square").json()
    assert z["state"] is not None
    assert abs(z["state"]["density"] - 0.51) < 0.05
    assert z["state"]["congestion_state"] == "WARNING"
    assert z["state"]["n_sensors"] == 1
    assert z["stale"] is False
    hist = client.get("/zones/senado_square/history?minutes=10").json()
    assert len(hist) >= 2


def test_prediction_api_returns_confidence_and_reasons(client):
    now = datetime.now(timezone.utc)
    rows = []
    for m in range(6):
        for s in range(0, 60, 10):
            rows.append(obs(ts=now - timedelta(minutes=5 - m, seconds=-s), density=0.4 + 0.05 * m, count=int(100 * (0.4 + 0.05 * m))))
    client.post("/sensor/observation", json={"observations": rows})
    preds = client.get("/zones/senado_square/prediction?fresh=true").json()
    assert [p["horizon_min"] for p in preds] == [5, 10, 15]
    for p in preds:
        assert p["status"] in ("ok", "fallback")
        assert p["predicted_class"] in ("SAFE", "WARNING", "CRITICAL")
        assert 0.0 <= p["effective_confidence"] <= 1.0
        assert isinstance(p["reasons"], list) and p["reasons"]
        assert p["human_review_required"] == p["low_confidence"]
        assert abs(sum(p["probabilities"].values()) - 1.0) < 1e-3
    assert any("increased" in r for r in preds[0]["reasons"])


def test_unreliable_sensor_lowers_reliability_and_flags_review(client):
    now = datetime.now(timezone.utc)
    rows = [obs(ts=now - timedelta(seconds=s), density=0.9, count=200, stability=0.2, obstructed=True) for s in range(0, 90, 5)]
    client.post("/sensor/observation", json={"observations": rows})
    z = client.get("/zones/senado_square").json()
    assert z["state"]["reliability"] < 0.5
    preds = client.get("/zones/senado_square/prediction?fresh=true").json()
    assert all(p["human_review_required"] for p in preds)


def test_unknown_zone_and_intervention_errors(client):
    assert client.get("/zones/nowhere").status_code == 404
    assert client.get("/zones/nowhere/prediction").status_code == 404
    assert client.post("/interventions/999/approve", json={}).status_code == 404
    assert client.get("/export/nope.csv").status_code == 404
    preds = client.get("/zones/tercena_corridor/prediction").json()
    assert all(p["status"] == "insufficient_data" for p in preds)


def test_critical_forecast_creates_alert_and_intervention_with_audit(client):
    now = datetime.now(timezone.utc)
    rows = []
    for m in range(8):
        for s in range(0, 60, 5):
            rows.append(obs(ts=now - timedelta(minutes=7 - m, seconds=-s), density=min(1.0, 0.55 + 0.06 * m), count=int(160 * (0.55 + 0.06 * m)), flow_speed_mps=0.5 - 0.03 * m))
            rows.append(obs(sensor_id="node-dom01", ts=now - timedelta(minutes=7 - m, seconds=-s), lat=22.19430, lon=113.53990, density=min(1.0, 0.7 + 0.03 * m), count=200, flow_direction_deg=195.0, flow_speed_mps=0.6))
    client.post("/sensor/observation", json={"observations": rows})
    client.get("/zones/senado_square/prediction?fresh=true")
    alerts = client.get("/alerts").json()
    assert alerts, "expected at least one alert"
    ivs = client.get("/interventions?status=pending").json()
    assert ivs, "expected a pending intervention"
    iv = ivs[0]
    assert iv["kind"] in ("redirect_flow", "reduce_inflow", "deploy_staff", "increase_monitoring")
    assert set(iv["messages"]) <= {"zh", "en", "pt"}
    r = client.post(f"/interventions/{iv['id']}/approve", json={"operator": "tester", "note": "ok"})
    assert r.status_code == 200 and r.json()["status"] == "approved" and r.json()["decided_by"] == "tester"
    assert client.post(f"/interventions/{iv['id']}/reject", json={}).status_code == 409
    audit = client.get("/audit").json()
    actions = {a["action"] for a in audit}
    assert "intervention_recommended" in actions and "intervention_approved" in actions
    ack = client.post(f"/alerts/{alerts[0]['id']}/ack", json={"operator": "tester"})
    assert ack.status_code == 200 and ack.json()["acknowledged"] is True


def test_exports_and_ground_truth(client):
    client.post("/sensor/observation", json=obs())
    r = client.get("/export/observations.csv")
    assert r.status_code == 200 and r.text.startswith("id,")
    gt = {"zone_id": "senado_square", "timestamp": datetime.now(timezone.utc).isoformat(), "actual_count": 25, "actual_class": "SAFE", "condition": "A"}
    assert client.post("/experiments/ground-truth", json=gt).status_code == 201
    res = client.get("/experiments/results").json()
    assert res["summary"]["n_ground_truth"] == 1
    assert client.get("/experiments/results.csv").status_code == 200


def test_sim_control(client):
    st = client.get("/sim/status").json()
    assert "golden_week_demo" in st["available_scenarios"] and st["sim"] is None
    r = client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 30})
    assert r.status_code == 200 and r.json()["running"] is True
    zones = client.get("/zones").json()
    assert sum(1 for z in zones if z["state"] is not None) >= 5
    assert client.get("/health").json()["clock"] == "simulated"
    r = client.post("/sim/inject", json={"zone_id": "senado_square", "people": 300})
    assert r.status_code == 200
    assert client.post("/sim/stop").status_code == 200
    assert client.post("/sim/start", json={"scenario": "nope"}).status_code == 400
