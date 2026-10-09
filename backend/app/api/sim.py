from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.app.api.deps import ENGINE, Engine
from backend.app.schemas import SimInjectIn, SimStartIn
from ml.synthetic.scenarios import SCENARIOS

router = APIRouter(prefix="/sim", tags=["simulation"])


@router.get("/status")
def status(engine: Engine = ENGINE):
    sim = engine.sim  # read once: /sim/stop may clear it concurrently
    return {"available_scenarios": sorted(SCENARIOS), "sim": sim.status() if sim else None, "sim_ended": engine.sim_ended if sim is None else None}


@router.post("/start")
def start(body: SimStartIn, engine: Engine = ENGINE):
    if body.scenario not in SCENARIOS:
        raise HTTPException(400, f"unknown scenario; choose from {sorted(SCENARIOS)}")
    return engine.start_sim(body.scenario, body.acceleration)


@router.post("/stop")
def stop(engine: Engine = ENGINE):
    engine.stop_sim()
    return {"running": False}


@router.post("/inject")
def inject(body: SimInjectIn, engine: Engine = ENGINE):
    """Demo helper: add a sudden surge of people to a zone in the live simulation."""
    sim = engine.sim  # read once: /sim/stop may clear it concurrently
    if sim is None:
        raise HTTPException(409, "live simulation not running")
    if body.zone_id not in engine.zones:
        raise HTTPException(404, "unknown zone")
    sim.inject(body.zone_id, body.people)
    return sim.status()
