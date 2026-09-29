from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from backend.app.api.deps import DB, ENGINE, Engine, Session
from backend.app.models import Alert, AuditLog
from backend.app.schemas import AlertOut, DecisionIn

router = APIRouter(tags=["alerts"])


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(limit: int = Query(100, ge=1, le=1000), level: str | None = None, db: Session = DB, engine: Engine = ENGINE):
    engine.refresh_if_due()
    # hide alerts dated after "now" (from a stopped or earlier simulation run); while a simulation runs, show
    # only this run's alerts
    q = select(Alert).where(Alert.created_at <= engine.clock.now())
    if engine.sim is not None:
        q = q.where(Alert.id > engine.run_markers.get("alert_id", 0))
    if level:
        q = q.where(Alert.level == level)
    return db.execute(q.order_by(Alert.created_at.desc()).limit(limit)).scalars().all()


@router.post("/alerts/{alert_id}/ack", response_model=AlertOut)
def ack_alert(alert_id: int, body: DecisionIn, db: Session = DB, engine: Engine = ENGINE):
    a = db.get(Alert, alert_id)
    if not a:
        raise HTTPException(404, "unknown alert")
    a.acknowledged, a.acknowledged_by = True, body.operator
    db.add(AuditLog(timestamp=engine.clock.now(), actor=body.operator, action="alert_acknowledged", target_type="alert", target_id=str(alert_id), details={"note": body.note}))
    db.commit()
    db.refresh(a)
    return a
