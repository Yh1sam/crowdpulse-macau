"""Built-in live simulation: drives the shared CrowdSimulator on an accelerated
simulated clock and feeds observations through the SAME ingestion path real
phones use. Interventions approved by the operator feed back into it."""
from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from ml.synthetic.scenarios import SCENARIOS
from ml.synthetic.simulator import CrowdSimulator


class LiveSimulation:
    def __init__(self, scenario: str, acceleration: float, sensor_interval_s: int, start_utc: datetime | None = None):
        if scenario not in SCENARIOS:
            raise ValueError(f"unknown scenario {scenario}; choose from {sorted(SCENARIOS)}")
        self.scenario = scenario
        self.acceleration = float(acceleration)
        self.sensor_interval_s = sensor_interval_s
        self.params = SCENARIOS[scenario](sensor_interval_s=sensor_interval_s) if start_utc is None else SCENARIOS[scenario](start_utc=start_utc, sensor_interval_s=sensor_interval_s)
        self.sim = CrowdSimulator(self.params)
        self.start_time = self.params.start_time
        self.elapsed_s = 0.0
        self._next_dynamics_s = 60.0
        self._next_obs_s = 0.0
        self.running = False
        self.lock = threading.Lock()
        self.started_at = datetime.now(timezone.utc)

    @property
    def now(self) -> datetime:
        return self.start_time + timedelta(seconds=self.elapsed_s)

    def advance(self, real_seconds: float, ingest: Callable[[list[dict[str, Any]]], Any]) -> int:
        """Advance simulated time and emit observations. Returns observations emitted."""
        emitted = 0
        with self.lock:
            self.elapsed_s += real_seconds * self.acceleration
            while self._next_dynamics_s <= self.elapsed_s:
                self.sim.dynamics_step(record=False)
                self._next_dynamics_s += 60.0
            batch: list[dict[str, Any]] = []
            while self._next_obs_s <= self.elapsed_s:
                ts = self.start_time + timedelta(seconds=self._next_obs_s)
                batch.extend(self.sim.observe(ts=ts, dt_min=self.sensor_interval_s / 60.0))
                self._next_obs_s += self.sensor_interval_s
        if batch:
            ingest(batch)
            emitted = len(batch)
        return emitted

    def context(self) -> dict[str, dict[str, int]]:
        return {z: {"event_indicator": int(self.sim.event_active(z)), "rain_indicator": int(self.sim.raining())} for z in self.sim.zones}

    def truth(self) -> dict[str, dict[str, float]]:
        return {z: {"occupancy": round(self.sim.occupancy[z], 1), "density": round(min(1.0, self.sim.density(z)), 4)} for z in self.sim.zones}

    def apply_redirect(self, zone_id: str, inflow_multiplier: float, duration_min: float) -> None:
        with self.lock:
            self.sim.apply_redirect(zone_id, inflow_multiplier, duration_min)

    def inject(self, zone_id: str, people: int) -> None:
        with self.lock:
            self.sim.occupancy[zone_id] += people

    def status(self) -> dict[str, Any]:
        return {"running": self.running, "scenario": self.scenario, "acceleration": self.acceleration, "sim_time": self.now.isoformat(), "elapsed_sim_min": round(self.elapsed_s / 60.0, 2),
                "sensor_interval_s": self.sensor_interval_s, "started_at": self.started_at.isoformat(), "redirects": self.sim.redirects, "ground_truth": self.truth()}
