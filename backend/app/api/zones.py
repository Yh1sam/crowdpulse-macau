from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from backend.app.api.deps import DB, ENGINE, Engine, Session
from backend.app.models import Prediction, ZoneState
from backend.app.schemas import ContextIn, PredictionOut, ZoneOut, ZoneStateOut

router = APIRouter(tags=["zones"])


@router.get("/zones", response_model=list[ZoneOut])
def list_zones(db: Session = DB, engine: Engine = ENGINE):
    engine.refresh_if_due()
    return [engine.zone_view(db, zid) for zid in engine.zones]


@router.get("/zones/{zone_id}", response_model=ZoneOut)
def get_zone(zone_id: str, db: Session = DB, engine: Engine = ENGINE):
    if zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    engine.refresh_if_due()
    return engine.zone_view(db, zone_id)


@router.get("/zones/{zone_id}/history", response_model=list[ZoneStateOut])
def zone_history(zone_id: str, minutes: int = Query(60, ge=1, le=24 * 60), db: Session = DB, engine: Engine = ENGINE):
    if zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    since = engine.clock.now() - timedelta(minutes=minutes)
    rows = db.execute(select(ZoneState).where(ZoneState.zone_id == zone_id, ZoneState.bin_start >= since, ZoneState.bin_start <= engine.clock.now()).order_by(ZoneState.bin_start)).scalars().all()
    return [ZoneStateOut.model_validate(r, from_attributes=True) for r in rows]


@router.get("/zones/{zone_id}/prediction", response_model=list[PredictionOut])
def zone_prediction(zone_id: str, fresh: bool = False, engine: Engine = ENGINE):
    if zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    if fresh or zone_id not in engine.latest_predictions:
        engine.refresh(force=True)
    else:
        engine.refresh_if_due()
    preds = engine.latest_predictions.get(zone_id)
    if not preds:
        now = engine.clock.now()
        return [PredictionOut(zone_id=zone_id, created_at=now, horizon_min=h, target_time=now + timedelta(minutes=h), status="insufficient_data", predicted_class=None, probabilities={},
                              model_confidence=0.0, reliability=0.0, effective_confidence=0.0, low_confidence=True, human_review_required=True, ood_flag=False, ood_score=None, ood_reasons=[], ood_message=None,
                              predicted_density=None, reasons=["no observations received for this zone yet"], contributions=[], model_type="", model_version=engine.models.version, current_state=None,
                              message="No sensor data for this zone. HUMAN REVIEW REQUIRED.") for h in engine.cfg["forecast_horizons_min"]]
    return preds


@router.get("/zones/{zone_id}/prediction/history", response_model=list[PredictionOut])
def zone_prediction_history(zone_id: str, minutes: int = Query(60, ge=1, le=24 * 60), horizon: int | None = None, db: Session = DB, engine: Engine = ENGINE):
    if zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    since = engine.clock.now() - timedelta(minutes=minutes)
    q = select(Prediction).where(Prediction.zone_id == zone_id, Prediction.created_at >= since)
    if horizon:
        q = q.where(Prediction.horizon_min == horizon)
    rows = db.execute(q.order_by(Prediction.created_at)).scalars().all()
    out = []
    for r in rows:
        d = {c: getattr(r, c) for c in Prediction.__table__.columns.keys()}
        d["human_review_required"] = r.low_confidence
        d["ood_message"] = engine.cfg["ood"]["message"] if r.ood_flag else None
        out.append(d)
    return out


@router.post("/zones/{zone_id}/context")
def set_context(zone_id: str, body: ContextIn, engine: Engine = ENGINE):
    """Operator-provided context (scheduled event ending, rain). Not sensor data."""
    if zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    cur = engine.context.setdefault(zone_id, {"event_indicator": 0, "rain_indicator": 0})
    if body.event_indicator is not None:
        cur["event_indicator"] = body.event_indicator
    if body.rain_indicator is not None:
        cur["rain_indicator"] = body.rain_indicator
    return {"zone_id": zone_id, "context": cur}
