from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from backend.app.api.deps import DB, ENGINE, Engine, Session
from backend.app.models import AuditLog, Intervention
from backend.app.schemas import AuditOut, DecisionIn, InterventionOut

router = APIRouter(tags=["interventions"])


@router.get("/interventions", response_model=list[InterventionOut])
def list_interventions(status: str | None = None, limit: int = Query(100, ge=1, le=1000), db: Session = DB, engine: Engine = ENGINE):
    engine.refresh_if_due()
    q = select(Intervention)
    if engine.sim is not None:  # while a simulation runs, show only this run's recommendations
        q = q.where(Intervention.id > engine.run_markers.get("intervention_id", 0))
    if status:
        q = q.where(Intervention.status == status)
    return db.execute(q.order_by(Intervention.created_at.desc()).limit(limit)).scalars().all()


@router.get("/interventions/{iv_id}", response_model=InterventionOut)
def get_intervention(iv_id: int, db: Session = DB):
    iv = db.get(Intervention, iv_id)
    if not iv:
        raise HTTPException(404, "unknown intervention")
    return iv


def _decide(iv_id: int, approve: bool, body: DecisionIn, engine: Engine) -> Intervention:
    try:
        return engine.decide_intervention(iv_id, approve, body.operator, body.note)
    except KeyError:
        raise HTTPException(404, "unknown intervention")
    except ValueError as e:
        raise HTTPException(409, str(e))


@router.post("/interventions/{iv_id}/approve", response_model=InterventionOut)
def approve(iv_id: int, body: DecisionIn = DecisionIn(), engine: Engine = ENGINE):
    return _decide(iv_id, True, body, engine)


@router.post("/interventions/{iv_id}/reject", response_model=InterventionOut)
def reject(iv_id: int, body: DecisionIn = DecisionIn(), engine: Engine = ENGINE):
    return _decide(iv_id, False, body, engine)


@router.get("/audit", response_model=list[AuditOut])
def audit(limit: int = Query(200, ge=1, le=5000), db: Session = DB):
    # newest-written first: timestamps are simulated time while a simulation runs, and a restarted run starts
    # earlier than where the last one stopped, so ordering by timestamp put stale runs above current decisions
    return db.execute(select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)).scalars().all()
