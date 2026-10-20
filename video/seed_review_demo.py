"""Seed a labelled verification test in an isolated local recording database.

These recommendations are generated from explicit synthetic prediction inputs, not
from a model inference or a field observation. The API and UI execute real actions.
Never seeds the project's normal database or imports Melbourne test data.
"""
from datetime import timedelta
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
DB = ROOT / 'video/build/v3/route-review-demo.db'
os.environ['CROWDPULSE_DATABASE_URL'] = f'sqlite:///{DB}'
os.environ['CROWDPULSE_LIVE_SIM'] = 'false'

from sqlalchemy import delete
from backend.app.db import init_db, session_scope
from backend.app.models import AuditLog, Intervention
from backend.app.services.engine import get_engine
from backend.app.services.intervention import build_recommendation
from shared.config import load_config, load_zone_graph
from shared.geo import bearing_deg


def seed():
    DB.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    engine = get_engine()
    now = engine.clock.now()
    graph = load_zone_graph()
    zones = {z['id']: z for z in graph['zones']}
    source, target = zones['almeida_ribeiro'], zones['senado_square']
    states = {source['id']: {'density': .8, 'flow_speed_mps': .8, 'flow_coherence': .9,
                            'flow_direction_deg': bearing_deg(source['lat'], source['lon'], target['lat'], target['lon'])}}
    prediction = {'predicted_class': 'CRITICAL', 'effective_confidence': .69,
                  'low_confidence': False, 'horizon_min': 15,
                  'reasons': ['Seeded simulated recommendation for a verification test. No field data.']}
    divert = build_recommendation(target, graph, states, prediction, load_config())
    staff = build_recommendation(target, graph, states, {**prediction, 'predicted_class': 'WARNING'}, load_config())
    with session_scope() as db:
        db.execute(delete(Intervention))
        db.execute(delete(AuditLog))
        records = []
        for rec in [staff, divert]:
            iv = Intervention(zone_id=target['id'], created_at=now, status='pending',
                              expires_at=now + timedelta(hours=2), **rec)
            db.add(iv); db.flush()
            db.add(AuditLog(timestamp=now, actor='system', action='demo_recommendation_seeded',
                           target_type='intervention', target_id=str(iv.id),
                           details={'synthetic_test_input': True, 'model_inference': False, 'kind': iv.kind}))
            records.append({'id': iv.id, 'kind': iv.kind})
    manifest = {'database': str(DB), 'created_at': now.isoformat(),
                'provenance': 'Seeded synthetic prediction inputs; real API/UI; scripted actions; no field inspection.',
                'recommendations': records}
    (DB.parent / 'recording-fixture.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    seed()
