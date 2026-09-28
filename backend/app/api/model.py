from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.deps import ENGINE, Engine
from backend.app.config import get_settings

router = APIRouter(tags=["model"])


@router.get("/model/metrics")
def model_metrics(engine: Engine = ENGINE):
    m = engine.models.metrics
    s = get_settings()
    figures = sorted(p.name for p in s.evidence_dir.glob("*.png")) if s.evidence_dir.exists() else []
    return {"status": engine.models.status(), "metrics": m, "evidence_figures": [f"/evidence/{f}" for f in figures]}


@router.get("/model/status")
def model_status(engine: Engine = ENGINE):
    return engine.models.status()
