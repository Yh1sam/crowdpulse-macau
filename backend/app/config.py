"""Deployment settings (environment variables). Domain thresholds live in shared/config.json."""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from shared.config import REPO_ROOT, load_config

log = logging.getLogger("crowdpulse")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CROWDPULSE_", env_file=".env", extra="ignore")

    database_url: str = f"sqlite:///{REPO_ROOT / 'crowdpulse.db'}"
    models_dir: Path = REPO_ROOT / "ml" / "models"
    evidence_dir: Path = REPO_ROOT / "experiments" / "results" / "latest"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    live_sim: bool = load_config()["live_simulation"]["enabled_by_default"]
    sim_scenario: str = load_config()["live_simulation"]["scenario"]
    sim_acceleration: float = load_config()["live_simulation"]["acceleration"]
    tick_seconds: float = load_config()["live_simulation"]["tick_s"]
    refresh_seconds: float = 2.0  # how often (real s) states/predictions are recomputed
    privacy_mode: bool = load_config()["privacy_mode"]
    rate_limit_per_minute: int = 1200  # observations per client IP per minute
    retention_hours: float = 48.0
    log_level: str = "INFO"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    if not s.privacy_mode:
        log.warning("PRIVACY_MODE is disabled by environment override. This is NOT the supported configuration.")
    return s
