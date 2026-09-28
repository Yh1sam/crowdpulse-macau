"""CSV exports for presentation evidence and experiment analysis. Numerical metadata only."""
from __future__ import annotations

import csv
import io
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from backend.app.api.deps import DB, ENGINE, Engine, Session
from backend.app.models import Alert, AuditLog, GroundTruth, Intervention, Observation, Prediction, ZoneState
from backend.app.schemas import GroundTruthIn
from shared.config import congestion_class

router = APIRouter(tags=["export"])
TABLES = {"observations": Observation, "zone_states": ZoneState, "predictions": Prediction, "alerts": Alert, "interventions": Intervention, "audit": AuditLog, "ground_truth": GroundTruth}


def _csv(rows, columns):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns)
    w.writeheader()
    for r in rows:
        w.writerow({c: (getattr(r, c) if not isinstance(r, dict) else r.get(c)) for c in columns})
    buf.seek(0)
    return buf


@router.get("/export/{table}.csv")
def export_table(table: str, hours: float = Query(24, ge=0.01, le=24 * 30), db: Session = DB, engine: Engine = ENGINE):
    if table not in TABLES:
        raise HTTPException(404, f"unknown table; choose from {sorted(TABLES)}")
    model = TABLES[table]
    tcol = getattr(model, "timestamp", None) or getattr(model, "created_at", None) or getattr(model, "bin_start")
    since = engine.clock.now() - timedelta(hours=hours)
    rows = db.execute(select(model).where(tcol >= since).order_by(tcol)).scalars().all()
    cols = list(model.__table__.columns.keys())
    return StreamingResponse(_csv(rows, cols), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={table}.csv"})


@router.post("/experiments/ground-truth", status_code=201)
def add_ground_truth(body: GroundTruthIn, db: Session = DB, engine: Engine = ENGINE):
    if body.zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    gt = GroundTruth(**body.model_dump())
    db.add(gt)
    db.commit()
    return {"id": gt.id}


@router.get("/experiments/results")
def experiment_results(db: Session = DB, engine: Engine = ENGINE):
    """Compare manually recorded ground truth with the system's estimates (nearest 1-min bin)."""
    gts = db.execute(select(GroundTruth).order_by(GroundTruth.timestamp)).scalars().all()
    rows = []
    for g in gts:
        b = g.timestamp.replace(second=0, microsecond=0)
        st = db.execute(select(ZoneState).where(ZoneState.zone_id == g.zone_id, ZoneState.bin_start == b)).scalar_one_or_none()
        pred = db.execute(select(Prediction).where(Prediction.zone_id == g.zone_id, Prediction.horizon_min == 5, Prediction.created_at <= g.timestamp).order_by(Prediction.created_at.desc())).scalars().first()
        rows.append({"zone_id": g.zone_id, "timestamp": g.timestamp.isoformat(), "condition": g.condition, "actual_count": g.actual_count, "actual_class": g.actual_class or congestion_class(0.0),
                     "estimated_count": st.person_count_visible if st else None, "estimated_density": st.density if st else None, "estimated_class": st.congestion_state if st else None,
                     "predicted_class_5min_prior": pred.predicted_class if pred else None, "reliability": st.reliability if st else None, "notes": g.notes})
    matched = [r for r in rows if r["estimated_count"] is not None]
    summary = {"n_ground_truth": len(rows), "n_matched": len(matched)}
    if matched:
        summary["count_mae"] = sum(abs(r["actual_count"] - r["estimated_count"]) for r in matched) / len(matched)
        summary["class_agreement"] = sum(1 for r in matched if r["actual_class"] == r["estimated_class"]) / len(matched)
    return {"summary": summary, "rows": rows}


@router.get("/experiments/results.csv")
def experiment_results_csv(db: Session = DB, engine: Engine = ENGINE):
    res = experiment_results(db, engine)
    cols = ["zone_id", "timestamp", "condition", "actual_count", "actual_class", "estimated_count", "estimated_density", "estimated_class", "predicted_class_5min_prior", "reliability", "notes"]
    return StreamingResponse(_csv(res["rows"], cols), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=experiment_results.csv"})
