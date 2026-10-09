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
    assert any(i.startswith("outside any zone") for i in s["issues"]) and s["placement"] == "none"


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


def test_real_sensor_joins_running_simulation(client):
    """Hybrid mode: a phone posting wall-clock timestamps while the live simulation runs is re-timed onto
    the simulated clock, shows as online and contributes to its zone."""
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 10})
    sim_now = datetime.fromisoformat(client.get("/health").json()["time"])
    assert client.get("/health").json()["real_sensor_retiming"] is True
    wall = datetime.now(timezone.utc)
    r = client.post("/sensor/observation", json={"observations": [obs(sensor_id="node-phone1", ts=wall, mode="live"), obs(sensor_id="node-phone1", ts=wall - timedelta(seconds=30), mode="live")]})
    assert r.status_code == 202 and r.json()["zone_assignments"]["node-phone1"] == "senado_square"
    s = client.get("/sensors/node-phone1").json()
    assert s["status"] == "online", s
    last_seen = datetime.fromisoformat(s["last_seen"])
    assert abs((last_seen - sim_now).total_seconds()) < 60, "fresh reading must land at the simulated 'now'"
    z = client.get("/zones/senado_square").json()
    assert "node-phone1" in z["sensors"]
    assert z["state"]["n_sensors"] == 3, "2 simulated nodes + the phone"
    # a reading buffered for 30 real seconds lands 30 x 10 = 300 simulated seconds back
    hist = client.get("/export/observations.csv?hours=1").text.splitlines()
    header = hist[0].split(",")
    ts_i, sid_i = header.index("timestamp"), header.index("sensor_id")
    phone_ts = sorted(datetime.fromisoformat(l.split(",")[ts_i]).replace(tzinfo=timezone.utc) if "+" not in l.split(",")[ts_i] else datetime.fromisoformat(l.split(",")[ts_i]) for l in hist[1:] if l.split(",")[sid_i] == "node-phone1")
    assert len(phone_ts) == 2
    assert abs((phone_ts[1] - phone_ts[0]).total_seconds() - 300) < 30
    assert client.get("/health").json()["stats"]["api_observations_retimed"] == 2
    client.post("/sim/stop")


def test_simulation_observations_are_not_retimed(client):
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 10})
    stats = client.get("/health").json()["stats"]
    assert stats["observations_ingested"] > 0
    assert stats.get("api_observations_retimed", 0) == 0
    client.post("/sim/stop")


def test_wall_clock_without_simulation_is_unchanged(client):
    wall = datetime.now(timezone.utc)
    client.post("/sensor/observation", json=obs(sensor_id="node-phone2", ts=wall))
    assert client.get("/health").json()["real_sensor_retiming"] is False
    s = client.get("/sensors/node-phone2").json()
    assert abs((datetime.fromisoformat(s["last_seen"]) - wall).total_seconds()) < 1


def test_sensor_snapshot_follows_latest_batch_after_sim_stops(client):
    """The simulated clock runs days ahead of the wall clock; after the simulation stops, a phone's new
    wall-clock readings must still update its status (regression: a newest-timestamp rule froze it)."""
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 10})
    client.post("/sensor/observation", json=obs(sensor_id="node-phone7", ts=datetime.now(timezone.utc), count=20))
    client.post("/sim/stop")
    wall = datetime.now(timezone.utc)
    client.post("/sensor/observation", json=obs(sensor_id="node-phone7", ts=wall, count=5))
    s = client.get("/sensors/node-phone7").json()
    assert s["person_count"] == 5
    assert abs((datetime.fromisoformat(s["last_seen"]) - wall).total_seconds()) < 1
    assert s["seconds_since_seen"] >= -1


def test_sim_restart_does_not_freeze_simulated_sensors(client):
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 60})
    client.post("/sim/stop")
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 10})
    now = datetime.fromisoformat(client.get("/health").json()["time"])
    for s in client.get("/sensors").json():
        age = (now - datetime.fromisoformat(s["last_seen"])).total_seconds()
        assert age >= -1, f"{s['sensor_id']} last_seen is in the simulated future ({age:.0f} s)"


def test_batch_order_does_not_matter_for_sensor_snapshot(client):
    wall = datetime.now(timezone.utc)
    client.post("/sensor/observation", json={"observations": [obs(sensor_id="node-phone8", ts=wall, count=9), obs(sensor_id="node-phone8", ts=wall - timedelta(seconds=40), count=1)]})
    s = client.get("/sensors/node-phone8").json()
    assert s["person_count"] == 9 and s["status"] == "online" and s["observation_count"] == 2


def test_very_old_timestamp_does_not_fail_the_batch(client):
    """Regression: age x acceleration overflowed datetime arithmetic (HTTP 500, whole batch lost, uploader stuck)."""
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 120})
    r = client.post("/sensor/observation", json={"observations": [obs(sensor_id="node-phone9", ts=datetime(1970, 1, 1, tzinfo=timezone.utc)), obs(sensor_id="node-phone9", ts=datetime.now(timezone.utc))]})
    assert r.status_code == 202 and r.json()["accepted"] == 2
    client.post("/sim/stop")


def test_phone_reading_is_placed_against_an_up_to_date_sim_clock(client):
    """Ingestion advances the simulation to the present before placing a real reading, so a reading that
    arrives between background ticks is not placed behind the simulation frontier."""
    import time as _t
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 60})
    before = datetime.fromisoformat(client.get("/health").json()["time"])
    _t.sleep(0.6)
    client.post("/sensor/observation", json=obs(sensor_id="node-phone10", ts=datetime.now(timezone.utc)))
    last_seen = datetime.fromisoformat(client.get("/sensors/node-phone10").json()["last_seen"])
    assert (last_seen - before).total_seconds() >= 25, "0.6 real s at 60x is 36 simulated seconds"
    client.post("/sim/stop")


def test_concurrent_refresh_requests_do_not_queue_full_refreshes(client):
    """Regression: N requests that all found a refresh due each ran a full refresh in turn (refresh storm)."""
    import threading
    from backend.app.services.engine import get_engine
    client.post("/sensor/observation", json=obs())
    eng = get_engine()
    before = eng.stats["refreshes"]
    gate = threading.Barrier(6)
    def ask():
        gate.wait()
        eng.refresh()
    ts = [threading.Thread(target=ask) for _ in range(6)]
    for t in ts: t.start()
    for t in ts: t.join()
    assert eng.stats["refreshes"] - before <= 2, eng.stats["refreshes"] - before


def test_future_dated_reading_does_not_lock_sensor(client):
    wall = datetime.now(timezone.utc)
    client.post("/sensor/observation", json=obs(sensor_id="node-skew1", ts=wall + timedelta(hours=2), count=10))
    client.post("/sensor/observation", json=obs(sensor_id="node-skew1", ts=wall, count=77))
    assert client.get("/sensors/node-skew1").json()["person_count"] == 77


def _pred(cls, conf, low, h=5):
    return {"status": "ok", "predicted_class": cls, "effective_confidence": conf, "low_confidence": low, "horizon_min": h, "reasons": ["test"], "id": None}


def test_confident_critical_supersedes_pending_monitoring(client):
    """Regression: a pending low-confidence 'increase monitoring' blocked the confident CRITICAL redirect for its
    whole 20-minute lifetime (found in the end-to-end simulation: redirect came 25 simulated minutes late)."""
    from backend.app.db import session_scope
    from backend.app.models import AuditLog, Intervention
    from backend.app.services.engine import get_engine
    from sqlalchemy import select
    eng = get_engine()
    now = eng.clock.now()
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.45, True)], now)
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.45, True), _pred("CRITICAL", 0.9, False, h=10)], now + timedelta(minutes=1))
    with session_scope() as db:
        ivs = db.execute(select(Intervention).where(Intervention.zone_id == "senado_square").order_by(Intervention.id)).scalars().all()
        assert [(i.kind, i.status) for i in ivs][0] == ("increase_monitoring", "superseded")
        assert ivs[1].status == "pending" and ivs[1].kind in ("redirect_flow", "reduce_inflow") and ivs[1].horizon_min == 10
        assert db.execute(select(AuditLog).where(AuditLog.action == "intervention_superseded")).scalars().first() is not None
    # a superseded recommendation can no longer be approved
    assert client.post(f"/interventions/{ivs[0].id}/approve", json={}).status_code == 409


def test_equal_or_weaker_recommendation_does_not_replace_pending_or_approved(client):
    from backend.app.db import session_scope
    from backend.app.models import Intervention
    from backend.app.services.engine import get_engine
    from sqlalchemy import select
    eng = get_engine()
    now = eng.clock.now()
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.9, False)], now)
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.95, False)], now + timedelta(minutes=1))   # same rank
        eng._maybe_recommend(db, "senado_square", [_pred("WARNING", 0.9, False)], now + timedelta(minutes=2))     # weaker
    with session_scope() as db:
        ivs = db.execute(select(Intervention).where(Intervention.zone_id == "senado_square")).scalars().all()
        assert len(ivs) == 1 and ivs[0].status == "pending"
    client.post(f"/interventions/{ivs[0].id}/approve", json={"operator": "t"})
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.99, False)], now + timedelta(minutes=3))
    with session_scope() as db:
        assert len(db.execute(select(Intervention).where(Intervention.zone_id == "senado_square")).scalars().all()) == 1, "an approved action is not second-guessed"


def test_phone_counts_toward_expected_sensors(client):
    client.post("/sensor/observation", json=obs(sensor_id="node-phone11", lat=22.19282, lon=113.53925))
    client.post("/sensor/observation", json=obs(sensor_id="node-b1c5", lat=22.19282, lon=113.53925))
    z = client.get("/zones/almeida_ribeiro").json()
    assert z["sensors_expected"] >= len(z["sensors"]) == 2
    assert z["state"]["mean_stability"] is not None and z["state"]["mean_vision_confidence"] is not None


def test_clock_is_published_after_readings_are_stored():
    """The simulated clock must not run ahead of stored readings (a reader saw every sensor as stale)."""
    from backend.app.services.live_sim import LiveSimulation
    sim = LiveSimulation("golden_week_demo", 10.0, 5)
    seen = []
    def ingest(batch):
        seen.append((sim.now, max(o["timestamp"] for o in batch)))
    sim.advance(3.0, ingest)
    clock_during_ingest, newest_reading = seen[0]
    assert clock_during_ingest < sim.now, "clock advanced before the batch was stored"
    assert sim.now.isoformat() >= newest_reading


def test_stored_zone_history_keeps_complete_bins(client):
    """Regression: a refresh whose window started mid-bin overwrote that bin's stored row with a partial aggregate."""
    from backend.app.services.engine import get_engine
    eng = get_engine()
    base = datetime(2026, 10, 3, 6, 0, tzinfo=timezone.utc)
    rows = [obs(sensor_id="node-f8a6", ts=base + timedelta(seconds=5 * i), density=0.5) for i in range(12 * 12)]  # 12 minutes, every 5 s
    eng.clock.attach(lambda: base + timedelta(minutes=12))
    client.post("/sensor/observation", json={"observations": rows})
    eng.refresh(force=True)
    eng.clock.attach(lambda: base + timedelta(minutes=13, seconds=40))   # window now starts at 06:03:40 without the fix
    eng.refresh(force=True)
    hist = {h["bin_start"][11:16]: h["n_obs"] for h in client.get("/zones/senado_square/history?minutes=30").json()}
    assert hist["06:03"] == 12, hist
    eng.clock.detach()


def test_stopping_the_simulation_closes_its_state(client):
    """Review finding: after /sim/stop the simulation's future-dated readings pinned every zone and its sensors
    stayed 'online' for days; its recommendations blocked new ones."""
    from backend.app.db import session_scope
    from backend.app.models import Intervention
    from sqlalchemy import select
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 30})
    from backend.app.services.engine import get_engine
    eng = get_engine()
    now = eng.clock.now()
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("WARNING", 0.9, False)], now)
    ivs = client.get("/interventions?status=pending").json()
    assert ivs
    client.post(f"/interventions/{ivs[0]['id']}/approve", json={"operator": "t"})
    client.post("/sim/stop")
    sim_nodes = [s for s in client.get("/sensors").json() if s["sensor_id"] == "node-f8a6"]
    assert sim_nodes and sim_nodes[0]["status"] == "offline", sim_nodes
    z = client.get("/zones/senado_square").json()
    assert z["state"] is None and z["active_intervention_id"] is None and z["risk"] == "UNKNOWN"
    assert client.get("/alerts").json() == [], "alerts dated in the stopped simulation's future are hidden"
    with session_scope() as db:
        assert all(i.expires_at.year == 2000 for i in db.execute(select(Intervention)).scalars())
    # a real phone now works normally on the wall clock
    client.post("/sensor/observation", json=obs(sensor_id="node-phone12"))
    assert client.get("/zones/senado_square").json()["state"]["n_sensors"] == 1


def test_restart_shows_only_the_new_runs_alerts_and_recommendations(client):
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 30})
    from backend.app.services.engine import get_engine
    from backend.app.db import session_scope
    eng = get_engine()
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.9, False)], eng.clock.now())
    old_ids = {i["id"] for i in client.get("/interventions").json()}
    assert old_ids
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 30})
    assert not ({i["id"] for i in client.get("/interventions").json()} & old_ids)
    assert client.get("/zones/senado_square").json()["active_intervention_id"] not in old_ids
    client.post("/sim/stop")


def test_audit_lists_newest_written_first_across_simulation_runs(client):
    """Regression: /audit sorted by (simulated) timestamp, so entries from an earlier run that had reached a later
    simulated day stayed above the current run's approvals."""
    from backend.app.db import session_scope
    from backend.app.models import AuditLog
    t0 = datetime(2026, 10, 3, 6, 0, tzinfo=timezone.utc)
    with session_scope() as db:
        db.add(AuditLog(timestamp=t0 + timedelta(days=3), actor="system", action="intervention_expired", target_type="intervention", target_id="1", details={}))
    with session_scope() as db:
        db.add(AuditLog(timestamp=t0, actor="operator", action="intervention_approved", target_type="intervention", target_id="2", details={}))
    audit = client.get("/audit").json()
    assert [(a["action"], a["target_id"]) for a in audit[:2]] == [("intervention_approved", "2"), ("intervention_expired", "1")]


def test_simulation_stops_at_the_end_of_its_scenario(client):
    """Regression: the live simulation ignored the scenario's length, so a demo left running overnight at 6x ended
    days ahead in simulated time and every timestamp it wrote followed it."""
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 60})
    from backend.app.services.engine import get_engine
    eng = get_engine()
    sim = eng.sim
    assert client.get("/health").json()["live_sim"]["duration_min"] == 120
    sim.end_s = sim.elapsed_s + 60  # end the script one simulated minute from now
    end_time = sim.start_time + timedelta(seconds=sim.end_s)
    eng.tick(real_seconds=5)  # 5 s at 60x = 5 simulated minutes, past the end
    assert sim.now == end_time, "simulated time ran past the end of the scenario"
    h = client.get("/health").json()
    assert eng.sim is None and h["live_sim"] is None and h["clock"] == "wall"
    assert h["sim_ended"]["scenario"] == "golden_week_demo" and datetime.fromisoformat(h["sim_ended"]["ended_at"]) == end_time
    client.post("/sim/start", json={"scenario": "golden_week_demo", "acceleration": 60})
    assert client.get("/health").json()["sim_ended"] is None
    client.post("/sim/stop")


def test_stronger_recommendation_added_alongside_approved_weaker_one(client):
    from backend.app.db import session_scope
    from backend.app.models import Intervention
    from backend.app.services.engine import get_engine
    from sqlalchemy import select
    eng = get_engine()
    now = eng.clock.now()
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("WARNING", 0.9, False)], now)
    staff = client.get("/interventions?status=pending").json()[0]
    client.post(f"/interventions/{staff['id']}/approve", json={"operator": "t"})
    with session_scope() as db:
        eng._maybe_recommend(db, "senado_square", [_pred("CRITICAL", 0.9, False)], now + timedelta(minutes=1))
    with session_scope() as db:
        ivs = {i.kind: i.status for i in db.execute(select(Intervention).where(Intervention.zone_id == "senado_square")).scalars()}
    assert ivs["deploy_staff"] == "approved" and ivs.get("redirect_flow", ivs.get("reduce_inflow")) == "pending", ivs
    z = client.get("/zones/senado_square").json()
    assert client.get(f"/interventions/{z['active_intervention_id']}").json()["kind"] in ("redirect_flow", "reduce_inflow")


def test_phone_at_a_school_joins_the_zone_chosen_in_the_app(client):
    school = dict(lat=22.2100, lon=113.5500)   # ~2 km from the historic district
    r = client.post("/sensor/observation", json=obs(sensor_id="node-school1", zone_hint="Senado Square", **school))
    assert r.status_code == 202 and r.json()["zone_assignments"]["node-school1"] == "senado_square"
    s = client.get("/sensors/node-school1").json()
    assert s["zone_id"] == "senado_square" and s["placement"] == "zone_hint" and 1500 < s["distance_to_zone_m"] < 3000
    assert not any(i.startswith("outside any zone") for i in s["issues"])
    z = client.get("/zones/senado_square").json()
    assert "node-school1" in z["sensors"] and z["state"]["n_sensors"] == 1
    # the same phone without a zone choice is not placed
    client.post("/sensor/observation", json=obs(sensor_id="node-school2", **school))
    assert client.get("/sensors/node-school2").json()["zone_id"] is None
    # a phone in the district is placed by GPS even if another zone was chosen
    client.post("/sensor/observation", json=obs(sensor_id="node-dist1", zone_hint="ruins_st_paul"))
    s = client.get("/sensors/node-dist1").json()
    assert s["zone_id"] == "senado_square" and s["placement"] == "gps"
