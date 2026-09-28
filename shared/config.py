"""Central configuration loader.

All tunable thresholds live in ``shared/config.json`` (one file, by design).
Environment overrides are limited to deployment concerns (database URL, ports).
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

SHARED_DIR = Path(__file__).resolve().parent
REPO_ROOT = SHARED_DIR.parent
CONFIG_PATH = SHARED_DIR / "config.json"
ZONES_PATH = SHARED_DIR / "zones.json"

CLASSES = ["SAFE", "WARNING", "CRITICAL"]


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    with CONFIG_PATH.open() as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_zone_graph() -> dict[str, Any]:
    with ZONES_PATH.open() as f:
        return json.load(f)


def congestion_class(density: float, cfg: dict[str, Any] | None = None) -> str:
    """Map a relative density index to SAFE / WARNING / CRITICAL using the central thresholds."""
    cfg = cfg or load_config()
    th = cfg["congestion_thresholds"]
    if density is None:
        return "SAFE"
    if density >= th["critical"]:
        return "CRITICAL"
    if density >= th["warning"]:
        return "WARNING"
    return "SAFE"


def class_index(label: str) -> int:
    return CLASSES.index(label)
