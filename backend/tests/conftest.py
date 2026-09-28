from __future__ import annotations

import os
import pytest

from shared.config import REPO_ROOT


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CROWDPULSE_DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("CROWDPULSE_LIVE_SIM", "false")
    monkeypatch.setenv("CROWDPULSE_REFRESH_SECONDS", "0")
    from backend.app import db as dbmod
    from backend.app.services import engine as engmod
    from backend.app.config import get_settings
    get_settings.cache_clear()
    dbmod.reset_engine()
    engmod.reset_engine()
    from backend.app.main import create_app
    from fastapi.testclient import TestClient
    app = create_app()
    with TestClient(app) as c:
        yield c
    engmod.reset_engine()
    dbmod.reset_engine()
