from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select

from backend.app.api.deps import DB, ENGINE, Engine, Session
from backend.app.config import get_settings
from backend.app.models import Sensor
from backend.app.schemas import IngestResponse, SensorOut
from shared.schemas import ObservationBatch, SensorObservation

router = APIRouter(tags=["sensors"])


@router.post("/sensor/observation", response_model=IngestResponse, status_code=202)
def post_observation(body: SensorObservation | ObservationBatch, request: Request, engine: Engine = ENGINE):
    """Ingest one observation or a batch (numerical metadata only)."""
    obs = body.observations if isinstance(body, ObservationBatch) else [body]
    res = engine.ingest(obs)
    return {**res, "privacy_mode": get_settings().privacy_mode}


@router.post("/sensor/frame", status_code=403, include_in_schema=True)
def post_frame():
    """Deliberately disabled. PRIVACY_MODE forbids raw frame / video upload."""
    raise HTTPException(status_code=403, detail="Raw frame upload is disabled: PRIVACY_MODE only accepts numerical metadata.")


@router.get("/sensors", response_model=list[SensorOut])
def list_sensors(db: Session = DB, engine: Engine = ENGINE):
    return [engine.sensor_status(s) for s in db.execute(select(Sensor).order_by(Sensor.sensor_id)).scalars()]


@router.get("/sensors/{sensor_id}", response_model=SensorOut)
def get_sensor(sensor_id: str, db: Session = DB, engine: Engine = ENGINE):
    s = db.get(Sensor, sensor_id)
    if not s:
        raise HTTPException(404, "unknown sensor")
    return engine.sensor_status(s)
