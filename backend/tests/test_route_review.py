"""Unverified diversions cannot be approved through UI bypass or legacy metadata."""
from datetime import timedelta

import pytest

from backend.app.db import session_scope
from backend.app.models import Intervention
from backend.app.services.engine import get_engine
from backend.app.services.intervention import build_recommendation
from shared.config import load_config, load_zone_graph
from shared.geo import bearing_deg


def make_candidate(source="st_dominic", *, kind=None, accessibility=None, expired=False):
    engine = get_engine()
    graph = load_zone_graph()
    zones = {z["id"]: z for z in graph["zones"]}
    a, b = zones[source], zones["senado_square"]
    states = {source: {"density": .8, "flow_speed_mps": .8, "flow_coherence": .9,
                        "flow_direction_deg": bearing_deg(a["lat"], a["lon"], b["lat"], b["lon"])}}
    prediction = {"predicted_class": "CRITICAL", "effective_confidence": .9,
                  "low_confidence": False, "horizon_min": 15, "reasons": ["Test scenario"]}
    if kind == "deploy_staff":
        prediction["predicted_class"] = "WARNING"
    rec = build_recommendation(b, graph, states, prediction, load_config())
    assert rec["kind"] == (kind or "redirect_flow")
    if accessibility is not None:
        rec["accessibility"] = accessibility
    now = engine.clock.now()
    with session_scope() as db:
        iv = Intervention(zone_id=b["id"], created_at=now, status="pending", **rec,
                          expires_at=now + timedelta(minutes=-1 if expired else 20))
        db.add(iv)
        db.flush()
        return iv.id


@pytest.mark.parametrize("source", ["st_dominic", "almeida_ribeiro"])
def test_model_coverage_does_not_enable_diversion_approval(client, source):
    iv_id = make_candidate(source)
    iv = client.get(f"/interventions/{iv_id}").json()
    assert iv["approval_blocked"] is True
    assert "on site" in iv["approval_block_reason"]
    assert "map records" in iv["accessibility"]["note"]
    assert "not_verified" == iv["accessibility"]["verification_status"]
    refused = client.post(f"/interventions/{iv_id}/approve", json={"operator": "demo-operator-1"})
    assert refused.status_code == 409
    unchanged = client.get(f"/interventions/{iv_id}").json()
    assert unchanged["status"] == "pending" and not unchanged["effect_applied"]
    assert unchanged["projected_after"] is None and unchanged["decided_by"] is None
    assert not [a for a in client.get('/audit').json() if a['action'] == 'intervention_approved']


@pytest.mark.parametrize("metadata", [{}, {"verification_status": "verified", "model_check_passed": True}])
def test_legacy_or_self_declared_metadata_cannot_bypass_server_policy(client, metadata):
    iv_id = make_candidate(accessibility=metadata)
    body = {"operator": "demo-operator-1", "approval_blocked": False, "verified": True}
    assert client.post(f"/interventions/{iv_id}/approve", json=body).status_code == 409


def test_field_request_is_persistent_idempotent_and_not_verification(client):
    iv_id = make_candidate()
    url = f"/interventions/{iv_id}/request-field-check"
    response = client.post(url, json={"operator": " demo-operator-1 ", "note": "Inspect route width and obstructions."})
    assert response.status_code == 200
    initial = response.json()
    assert initial["status"] == "pending" and initial["approval_blocked"]
    assert initial["accessibility"]["field_check_requested_by"] == "demo-operator-1"
    assert initial["accessibility"]["verification_status"] == "not_verified"
    repeated = client.post(url, json={"operator": "demo-operator-2", "note": "Retry"}).json()
    assert repeated["accessibility"] == initial["accessibility"]
    assert client.get(f"/interventions/{iv_id}").json()["accessibility"] == initial["accessibility"]
    assert client.post(f"/interventions/{iv_id}/approve", json={"operator": "demo-operator-1"}).status_code == 409
    events = [a for a in client.get('/audit').json() if a['action'] == 'route_field_check_requested']
    assert len(events) == 1 and events[0]["actor"] == "demo-operator-1"
    assert events[0]["details"]["route_verified"] is False
    rejected = client.post(f"/interventions/{iv_id}/reject", json={"operator": "demo-operator-1", "note": "Insufficient route evidence"})
    assert rejected.status_code == 200 and rejected.json()["status"] == "rejected"
    assert not rejected.json()["effect_applied"]
    assert client.post(url, json={"operator": "demo-operator-1"}).status_code == 409


def test_field_request_requires_name_pending_state_and_redirect_kind(client):
    candidate = make_candidate()
    assert client.post(f'/interventions/{candidate}/request-field-check', json={"operator": ""}).status_code == 422
    assert client.post('/interventions/999/request-field-check', json={"operator": "demo-operator-1"}).status_code == 404
    expired = make_candidate(expired=True)
    assert client.post(f'/interventions/{expired}/request-field-check', json={"operator": "demo-operator-1"}).status_code == 409
    assert client.post(f'/interventions/{expired}/approve', json={"operator": "demo-operator-1"}).status_code == 409
    staff = make_candidate(kind='deploy_staff')
    assert client.post(f'/interventions/{staff}/request-field-check', json={"operator": "demo-operator-1"}).status_code == 409
    allowed = client.post(f'/interventions/{staff}/approve', json={"operator": "demo-operator-1"})
    assert allowed.status_code == 200 and allowed.json()['approval_blocked'] is False
