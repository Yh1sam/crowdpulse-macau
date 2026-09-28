"""CrowdPulse Macau backend.

    uvicorn backend.app.main:app --reload --port 8000

OpenAPI docs at /docs. PRIVACY_MODE (default true) means only numerical metadata is
accepted; there is no endpoint that stores images or video.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.api import alerts, export, health, interventions, model, sensors, sim, zones
from backend.app.config import get_settings
from backend.app.db import init_db
from backend.app.services.engine import get_engine

log = logging.getLogger("crowdpulse")


class RateLimiter:
    """Tiny in-memory sliding-window limiter for the ingestion endpoint."""

    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return False
        q.append(now)
        return True


async def _background_loop(app: FastAPI) -> None:
    settings = get_settings()
    engine = get_engine()
    last = time.monotonic()
    while True:
        try:
            now = time.monotonic()
            dt, last = now - last, now
            await asyncio.to_thread(engine.tick, dt)
        except Exception:  # pragma: no cover
            log.exception("tick failed")
        await asyncio.sleep(settings.tick_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)
    init_db()
    engine = get_engine()
    if settings.live_sim:
        engine.start_sim()
        log.info("live simulation started: %s", engine.sim.status()["scenario"])
    task = asyncio.create_task(_background_loop(app))
    try:
        yield
    finally:
        task.cancel()
        engine.stop_sim()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="CrowdPulse Macau API", version="0.1.0", description=__doc__, lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_methods=["*"], allow_headers=["*"])
    limiter = RateLimiter(settings.rate_limit_per_minute)

    @app.middleware("http")
    async def guards(request: Request, call_next):
        ctype = request.headers.get("content-type", "")
        if settings.privacy_mode and request.method == "POST" and (ctype.startswith("multipart/") or ctype.startswith("image/") or ctype.startswith("video/")):
            return JSONResponse({"detail": "PRIVACY_MODE: media uploads are not accepted. Send numerical metadata only."}, status_code=403)
        if request.url.path.startswith("/sensor/") and request.method == "POST":
            key = request.client.host if request.client else "anon"
            if not limiter.allow(key):
                return JSONResponse({"detail": "rate limit exceeded"}, status_code=429)
        return await call_next(request)

    for r in (health, sensors, zones, alerts, interventions, model, sim, export):
        app.include_router(r.router)
    if settings.evidence_dir.exists():
        app.mount("/evidence", StaticFiles(directory=str(settings.evidence_dir)), name="evidence")
    return app


app = create_app()
