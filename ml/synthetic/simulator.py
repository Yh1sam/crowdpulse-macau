"""Synthetic crowd-flow simulator for the Macau tourist district zone graph.

Design goals
------------
* Emits sensor observations that use EXACTLY the same schema as real phones
  (``shared.schemas.SensorObservation``) so synthetic and real data enter the
  same pipeline.
* Also emits a separate ground-truth table (true zone occupancy per minute)
  that the sensors never see; it is used only for evaluation.
* Deliberately models sensor failure modes: dropout, obstruction (with
  silent, unflagged obstruction), device disturbance, weak GPS, occlusion
  under-counting at high density, rain and low light.

The crowd model is a simple mesoscopic flow model on the zone graph:
each zone holds an occupancy N_z; per simulated minute people arrive at entry
zones, move along edges (rate limited by edge capacity and destination space,
and slowed by density), and leave at exit zones.  Walking speed follows a
heuristic density-speed relation v = v_free * max(0.05, 1 - 0.9 d).
This is a prototype model, not a validated pedestrian-dynamics model.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from shared.config import congestion_class, load_config, load_zone_graph
from shared.geo import bearing_deg, unit_vec, vec_to_bearing

MACAU_UTC_OFFSET_H = 8
SIM_MODEL_VERSION = "sim-1.0"

# Position of each zone along the main north-south tourist spine
# (0 = Almeida Ribeiro in the south ... 5 = Ruins of St. Paul's in the north).
SPINE_INDEX = {
    "almeida_ribeiro": 0,
    "senado_square": 1,
    "st_dominic": 2,
    "tercena_corridor": 2,  # side branch, similar "height"
    "rua_sao_paulo": 3,
    "jesus_square": 4,
    "ruins_st_paul": 5,
}

MOVE_RATE_BY_KIND = {"attraction": 0.12, "square": 0.22, "corridor": 0.60, "avenue": 0.28}
ARRIVAL_SHARE = {"almeida_ribeiro": 0.65, "ruins_st_paul": 0.35}
DEPARTURE_RATE = {"almeida_ribeiro": 0.30, "ruins_st_paul": 0.16}
DAY_TYPE_FACTOR = {"weekday": 1.0, "weekend": 1.6, "golden_week": 2.4}
ALTERNATE_ROUTE_WEIGHT = 0.35  # the Tercena corridor is less popular than the main spine
OCCLUSION_COEF = 0.20  # fraction of people missed by the detector at extreme density (d=1)


@dataclass
class Episode:
    until_min: float = -1.0
    value: float = 0.0

    def active(self, t: float) -> bool:
        return t < self.until_min


@dataclass
class SensorState:
    sensor_id: str
    zone_id: str
    lat: float
    lon: float
    heading_deg: float
    visible_fraction: float
    offline: Episode = field(default_factory=Episode)
    obstructed: Episode = field(default_factory=Episode)
    obstruction_flagged: bool = True
    disturbed: Episode = field(default_factory=Episode)
    weak_gps: Episode = field(default_factory=Episode)


@dataclass
class SimParams:
    seed: int = 42
    start_time: datetime = field(default_factory=lambda: datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc))
    duration_min: int = 840
    sensor_interval_s: int = 20
    day_type: str = "golden_week"
    arrival_scale: float = 1.0
    peak_arrivals_per_min: float = 110.0  # weekday peak total arrivals (before day-type factor)
    walking_speed_free: float = 1.3
    noise_sd: float = 0.10
    bottleneck_scale: float = 1.0
    initial_fill: float = 0.06
    # sensor error model
    sensor_count_error_sd: float = 0.12
    sensor_dropout_p: float = 0.004
    obstruction_p: float = 0.003
    silent_obstruction_p: float = 0.25
    disturbance_p: float = 0.003
    weak_gps_p: float = 0.004
    # scripted events (minutes from start)
    surges: list[dict[str, Any]] = field(default_factory=list)      # {"time_min", "zone_id", "people"}
    event_ends: list[dict[str, Any]] = field(default_factory=list)  # {"time_min", "zone_id", "people"}
    closures: list[dict[str, Any]] = field(default_factory=list)    # {"edge_id", "start_min", "end_min"}
    rain: list[dict[str, Any]] = field(default_factory=list)        # {"start_min", "end_min"}
    # sensors to use (defaults to shared/zones.json)
    sensors: Optional[list[dict[str, Any]]] = None
    warmup_min: int = 0


class CrowdSimulator:
    """Mesoscopic crowd-flow simulator + sensor emulator."""

    def __init__(self, params: SimParams, graph: dict[str, Any] | None = None, config: dict[str, Any] | None = None):
        self.p = params
        self.graph = graph or load_zone_graph()
        self.cfg = config or load_config()
        self.rng = random.Random(params.seed)
        self.zones = {z["id"]: z for z in self.graph["zones"]}
        self.edges = {e["id"]: e for e in self.graph["edges"]}
        self.neighbours: dict[str, list[tuple[str, dict[str, Any]]]] = {z: [] for z in self.zones}
        for e in self.graph["edges"]:
            self.neighbours[e["from"]].append((e["to"], e))
            self.neighbours[e["to"]].append((e["from"], e))
        self.bearings: dict[tuple[str, str], float] = {}
        for a in self.zones:
            for b, _ in self.neighbours[a]:
                za, zb = self.zones[a], self.zones[b]
                self.bearings[(a, b)] = bearing_deg(za["lat"], za["lon"], zb["lat"], zb["lon"])
        self.occupancy: dict[str, float] = {z: self.zones[z]["capacity"] * params.initial_fill for z in self.zones}
        self.t_min: float = 0.0  # simulated minutes since start
        self.last_flows: dict[str, dict[str, float]] = {z: {} for z in self.zones}  # flows z->n in last step
        self.last_inflow: dict[str, float] = {z: 0.0 for z in self.zones}
        self.last_outflow: dict[str, float] = {z: 0.0 for z in self.zones}
        self.redirects: dict[str, dict[str, float]] = {}  # zone -> {"multiplier", "until_min"}
        self.runtime_closures: dict[str, float] = {}  # edge_id -> until_min
        sensors = params.sensors or self.graph["sensors"]
        self.sensors = [SensorState(s["sensor_id"], s["zone_id"], s["lat"], s["lon"], s["heading_deg"], s["visible_fraction"]) for s in sensors]
        self._fired_events: set[tuple[str, int]] = set()
        if params.warmup_min > 0:
            # Pre-roll the crowd model on a negative clock with scripted events disabled,
            # so the live run starts from a plausible steady state at t=0.
            saved = (params.surges, params.event_ends, params.closures, params.rain)
            params.surges, params.event_ends, params.closures, params.rain = [], [], [], []
            self.t_min = -float(params.warmup_min)
            for _ in range(params.warmup_min):
                self.dynamics_step(record=False)
            params.surges, params.event_ends, params.closures, params.rain = saved
            self._fired_events.clear()
            self.t_min = 0.0

    # ------------------------------------------------------------------ time
    @property
    def sim_time(self) -> datetime:
        return self.p.start_time + timedelta(minutes=self.t_min)

    def local_hour(self, t: datetime | None = None) -> float:
        t = t or self.sim_time
        lt = t + timedelta(hours=MACAU_UTC_OFFSET_H)
        return lt.hour + lt.minute / 60.0

    # ------------------------------------------------------------ conditions
    def raining(self, t_min: float | None = None) -> bool:
        t = self.t_min if t_min is None else t_min
        return any(r["start_min"] <= t < r["end_min"] for r in self.p.rain)

    def low_light(self) -> bool:
        h = self.local_hour()
        return h < 7.0 or h >= 19.0

    def edge_capacity(self, e: dict[str, Any]) -> float:
        for c in self.p.closures:
            if c["edge_id"] == e["id"] and c["start_min"] <= self.t_min < c["end_min"]:
                return 0.0
        if e["id"] in self.runtime_closures and self.t_min < self.runtime_closures[e["id"]]:
            return 0.0
        return e["capacity_per_min"] * self.p.bottleneck_scale

    def event_active(self, zone_id: str, window_min: float = 15.0) -> bool:
        return any(ev["zone_id"] == zone_id and abs(ev["time_min"] - self.t_min) <= window_min for ev in self.p.event_ends)

    def northness(self) -> float:
        """+1 = crowd predominantly heading north (towards the Ruins), -1 = heading south."""
        h = self.local_hour()
        # morning northbound, afternoon/evening southbound; smooth transition around 13:30
        return math.tanh((13.5 - h) / 1.6)

    def arrival_rate(self) -> float:
        h = self.local_hour()
        prof = (
            math.exp(-((h - 11.0) ** 2) / (2 * 1.5**2))
            + 0.9 * math.exp(-((h - 15.5) ** 2) / (2 * 2.0**2))
            + 0.35 * math.exp(-((h - 19.5) ** 2) / (2 * 1.2**2))
        )
        rate = self.p.peak_arrivals_per_min * prof * DAY_TYPE_FACTOR.get(self.p.day_type, 1.0) * self.p.arrival_scale
        if self.raining():
            rate *= 0.6
        return rate

    def speed(self, zone_id: str) -> float:
        d = self.density(zone_id)
        return self.p.walking_speed_free * max(0.05, 1.0 - 0.9 * d)

    def density(self, zone_id: str) -> float:
        return min(1.5, self.occupancy[zone_id] / self.zones[zone_id]["capacity"])

    # ------------------------------------------------------- interventions
    def apply_redirect(self, zone_id: str, inflow_multiplier: float, duration_min: float) -> None:
        self.redirects[zone_id] = {"multiplier": inflow_multiplier, "until_min": self.t_min + duration_min}

    def close_edge(self, edge_id: str, duration_min: float) -> None:
        self.runtime_closures[edge_id] = self.t_min + duration_min

    # -------------------------------------------------------------- dynamics
    def _noise(self) -> float:
        return math.exp(self.rng.gauss(0.0, self.p.noise_sd))

    def dynamics_step(self, record: bool = True) -> list[dict[str, Any]]:
        """Advance the crowd model by one simulated minute. Returns ground-truth rows."""
        p = self.p
        north = self.northness()
        vfree = p.walking_speed_free
        flows: dict[str, dict[str, float]] = {z: {} for z in self.zones}
        inflow = {z: 0.0 for z in self.zones}
        outflow = {z: 0.0 for z in self.zones}

        # 1. desired movements
        for z, zone in self.zones.items():
            n_z = self.occupancy[z]
            if n_z <= 0:
                continue
            v_ratio = self.speed(z) / vfree
            move_rate = MOVE_RATE_BY_KIND.get(zone["kind"], 0.3) * (0.4 + 0.6 * v_ratio)
            weights: dict[str, float] = {}
            for n, e in self.neighbours[z]:
                if self.edge_capacity(e) <= 0:
                    continue
                w = 1.0 + 0.6 * north * (SPINE_INDEX[n] - SPINE_INDEX[z]) / max(1, abs(SPINE_INDEX[n] - SPINE_INDEX[z]))
                if n == "tercena_corridor" or z == "tercena_corridor":
                    w *= ALTERNATE_ROUTE_WEIGHT if z != "tercena_corridor" else 1.0
                # redirect: reduce attractiveness of a zone under inflow restriction
                rd = self.redirects.get(n)
                if rd and self.t_min < rd["until_min"]:
                    w *= rd["multiplier"]
                weights[n] = max(0.02, w)
            total_w = sum(weights.values())
            if total_w <= 0:
                continue
            desired_total = n_z * move_rate * self._noise()
            for n, w in weights.items():
                e = self._edge_between(z, n)
                cap = self.edge_capacity(e)
                space = max(0.0, self.zones[n]["capacity"] * 1.05 - self.occupancy[n]) * 0.5
                f = min(desired_total * w / total_w, cap, space)
                flows[z][n] = max(0.0, f)

        # 2. apply flows
        for z in self.zones:
            for n, f in flows[z].items():
                self.occupancy[z] -= f
                self.occupancy[n] += f
                outflow[z] += f
                inflow[n] += f

        # 3. arrivals and departures at entry zones
        lam = self.arrival_rate()
        for z, share in ARRIVAL_SHARE.items():
            arrivals = self._poisson(lam * share)
            self.occupancy[z] += arrivals
            inflow[z] += arrivals
            leave_mult = 0.6 + 0.8 * (1.0 - north) / 2.0
            departures = min(self.occupancy[z], self.occupancy[z] * DEPARTURE_RATE[z] * leave_mult * self._noise())
            self.occupancy[z] -= departures
            outflow[z] += departures

        # 4. scripted events
        for ev in p.surges:
            key = ("surge", int(ev["time_min"]))
            if key not in self._fired_events and ev["time_min"] <= self.t_min:
                self._fired_events.add(key)
                self.occupancy[ev["zone_id"]] += ev["people"]
                inflow[ev["zone_id"]] += ev["people"]
        for ev in p.event_ends:
            key = ("event_end", int(ev["time_min"]))
            if key not in self._fired_events and ev["time_min"] <= self.t_min:
                self._fired_events.add(key)
                self.occupancy[ev["zone_id"]] += ev["people"]
                inflow[ev["zone_id"]] += ev["people"]

        for z in self.zones:
            self.occupancy[z] = max(0.0, self.occupancy[z])

        self.last_flows = flows
        self.last_inflow = inflow
        self.last_outflow = outflow
        rows: list[dict[str, Any]] = []
        if record:
            ts = self.sim_time
            for z in self.zones:
                d = self.density(z)
                rows.append(
                    {
                        "timestamp": ts.isoformat(),
                        "zone_id": z,
                        "occupancy": round(self.occupancy[z], 1),
                        "density": round(min(1.0, d), 4),
                        "speed_mps": round(self.speed(z), 3),
                        "inflow": round(inflow[z], 1),
                        "outflow": round(outflow[z], 1),
                        "label": congestion_class(min(1.0, d), self.cfg),
                        "rain": int(self.raining()),
                        "low_light": int(self.low_light()),
                        "event_active": int(self.event_active(z)),
                        "closure_active": int(any(self.edge_capacity(e) <= 0 for _, e in self.neighbours[z])),
                        "day_type": p.day_type,
                    }
                )
        self.t_min += 1.0
        return rows

    def _edge_between(self, a: str, b: str) -> dict[str, Any]:
        for n, e in self.neighbours[a]:
            if n == b:
                return e
        raise KeyError((a, b))

    def _poisson(self, lam: float) -> int:
        if lam <= 0:
            return 0
        if lam > 50:
            return max(0, int(round(self.rng.gauss(lam, math.sqrt(lam)))))
        l_exp, k, prod = math.exp(-lam), 0, 1.0
        while True:
            prod *= self.rng.random()
            if prod <= l_exp:
                return k
            k += 1

    # ------------------------------------------------------------- sensing
    def zone_flow_vector(self, z: str) -> tuple[float, float]:
        east = north = 0.0
        for n, _ in self.neighbours[z]:
            out_f = self.last_flows[z].get(n, 0.0)
            in_f = self.last_flows[n].get(z, 0.0)
            ue, un = unit_vec(self.bearings[(z, n)])
            east += (out_f - in_f) * ue
            north += (out_f - in_f) * un
        return east, north

    def _update_episodes(self, s: SensorState, dt_min: float) -> None:
        p, rng = self.p, self.rng
        rain_mult = 6.0 if self.raining() else 1.0
        if not s.offline.active(self.t_min) and rng.random() < p.sensor_dropout_p * dt_min:
            s.offline = Episode(self.t_min + rng.expovariate(1 / 5.0))
        if not s.obstructed.active(self.t_min) and rng.random() < p.obstruction_p * rain_mult * dt_min:
            s.obstructed = Episode(self.t_min + rng.expovariate(1 / 4.0))
            s.obstruction_flagged = rng.random() > p.silent_obstruction_p
        if not s.disturbed.active(self.t_min) and rng.random() < p.disturbance_p * dt_min:
            s.disturbed = Episode(self.t_min + rng.expovariate(1 / 2.0), rng.uniform(0.15, 0.6))
        if not s.weak_gps.active(self.t_min) and rng.random() < p.weak_gps_p * dt_min:
            s.weak_gps = Episode(self.t_min + rng.expovariate(1 / 3.0), rng.uniform(25.0, 60.0))

    def observe(self, ts: datetime | None = None, dt_min: float | None = None) -> list[dict[str, Any]]:
        """Emit one observation per online sensor for the current crowd state."""
        p, rng = self.p, self.rng
        ts = ts or self.sim_time
        dt_min = dt_min if dt_min is not None else p.sensor_interval_s / 60.0
        rain, night = self.raining(), self.low_light()
        obs: list[dict[str, Any]] = []
        for s in self.sensors:
            self._update_episodes(s, dt_min)
            if s.offline.active(self.t_min):
                continue
            z = s.zone_id
            n_z = self.occupancy[z]
            d = self.density(z)
            cap = self.zones[z]["capacity"]
            visible_capacity = s.visible_fraction * cap
            occlusion = OCCLUSION_COEF * min(1.0, d) ** 2  # under-count in dense crowds (documented failure mode)
            expected = n_z * s.visible_fraction * (1.0 - occlusion)
            err_sd = p.sensor_count_error_sd * (1.8 if rain else 1.0) * (1.4 if night else 1.0)
            obstructed = s.obstructed.active(self.t_min)
            disturbed = s.disturbed.active(self.t_min)
            if obstructed:
                count = expected * rng.uniform(0.0, 0.3)
                vision = rng.uniform(0.08, 0.35)
            elif disturbed:
                count = expected * rng.uniform(0.3, 1.7)
                vision = rng.uniform(0.3, 0.6)
            else:
                count = expected * (1.0 + rng.gauss(0.0, err_sd))
                vision = 0.93 - 0.35 * min(1.0, d) - (0.2 if rain else 0.0) - (0.25 if night else 0.0) + rng.gauss(0.0, 0.04)
            count = int(max(0, round(count)))
            vision = min(0.99, max(0.05, vision))
            est_density = min(1.0, count / max(1.0, visible_capacity))

            east, north = self.zone_flow_vector(z)
            mag = math.hypot(east, north)
            if mag > 3.0 and not obstructed:
                direction = (vec_to_bearing(east, north) + rng.gauss(0.0, 12.0)) % 360.0
            else:
                direction = rng.uniform(0.0, 360.0)  # milling crowd / no coherent flow
            speed = self.speed(z) * (1.0 + rng.gauss(0.0, 0.1))
            if obstructed:
                speed = abs(rng.gauss(0.0, 0.05))
            if disturbed:
                speed = rng.uniform(0.0, 2.0)
                direction = rng.uniform(0.0, 360.0)
            stability = s.disturbed.value if disturbed else rng.uniform(0.9, 0.99)
            accuracy = s.weak_gps.value if s.weak_gps.active(self.t_min) else rng.uniform(3.0, 12.0)
            jitter = accuracy / 111_320.0 * 0.5
            obs.append(
                {
                    "sensor_id": s.sensor_id,
                    "timestamp": ts.isoformat(),
                    "latitude": round(s.lat + rng.gauss(0.0, jitter), 6),
                    "longitude": round(s.lon + rng.gauss(0.0, jitter), 6),
                    "location_accuracy_m": round(accuracy, 1),
                    "heading_deg": round((s.heading_deg + rng.gauss(0.0, 3.0)) % 360.0, 1),
                    "device_motion_stability": round(min(1.0, max(0.0, stability)), 3),
                    "person_count": count,
                    "estimated_density": round(est_density, 4),
                    "flow_direction_deg": round(direction % 360.0, 1),
                    "flow_speed_mps": round(min(10.0, max(0.0, speed)), 3),
                    "vision_confidence": round(vision, 3),
                    "camera_obstructed": bool(obstructed and s.obstruction_flagged),
                    "model_version": SIM_MODEL_VERSION,
                    "mode": "simulated",
                }
            )
        return obs

    # ------------------------------------------------------------- batch run
    def run(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Run the whole scenario. Returns (observations, ground_truth)."""
        observations: list[dict[str, Any]] = []
        truth: list[dict[str, Any]] = []
        per_min = max(1, int(round(60 / self.p.sensor_interval_s)))
        for _ in range(self.p.duration_min):
            minute_start = self.sim_time
            truth.extend(self.dynamics_step())
            for j in range(per_min):
                ts = minute_start + timedelta(seconds=j * self.p.sensor_interval_s)
                observations.extend(self.observe(ts))
        return observations, truth
