"""Clock abstraction: wall-clock by default, simulated (accelerated) time when the
built-in live simulation is running. Everything time-related in the backend
(staleness, bins, horizons) goes through ``Clock.now()``."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable, Optional


class Clock:
    def __init__(self) -> None:
        self._source: Optional[Callable[[], datetime]] = None

    def attach(self, source: Callable[[], datetime]) -> None:
        self._source = source

    def detach(self) -> None:
        self._source = None

    @property
    def simulated(self) -> bool:
        return self._source is not None

    def now(self) -> datetime:
        if self._source is not None:
            return self._source()
        return datetime.now(timezone.utc)


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
