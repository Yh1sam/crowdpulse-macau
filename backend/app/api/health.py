from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.deps import ENGINE, Engine
from backend.app.config import get_settings
from shared.config import load_config, load_zone_graph

router = APIRouter(tags=["system"])


@router.get("/health")
def health(engine: Engine = ENGINE):
    s = get_settings()
    return {"status": "ok", "time": engine.clock.now(), "clock": "simulated" if engine.clock.simulated else "wall", "privacy_mode": s.privacy_mode,
            "models_loaded": engine.models.loaded, "model_version": engine.models.version, "live_sim": engine.sim.status() if engine.sim else None,
            "last_refresh": engine.last_refresh, "stats": engine.stats}


@router.get("/config")
def config():
    cfg = load_config()
    return {**cfg, "zone_graph": load_zone_graph(), "privacy_mode_effective": get_settings().privacy_mode}
