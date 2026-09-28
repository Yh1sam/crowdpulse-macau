from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from backend.app.db import get_session
from backend.app.services.engine import Engine, get_engine

DB = Depends(get_session)


def engine_dep() -> Engine:
    return get_engine()


ENGINE = Depends(engine_dep)
__all__ = ["DB", "ENGINE", "Session", "Engine"]
