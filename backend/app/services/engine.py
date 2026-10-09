"""The CrowdPulse engine: ingestion -> aggregation -> prediction -> alerts -> interventions.

One instance per process; the API routers call into it and a background task
ticks it (live simulation + periodic refresh)."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
import pandas as pd
from sqlalchemy import delete, func, select

from backend.app.config import Settings
from backend.app.db import session_scope
from backend.app.models import Alert, AuditLog, Intervention, Observation, Prediction, Sensor, ZoneState
from backend.app.services.clock import Clock, utc
from backend.app.services.intervention import build_recommendation
from backend.app.services.live_sim import LiveSimulation
from backend.app.services.prediction import ModelBundle, load_models, predict_zone, what_if_prediction
from ml.pipeline.aggregation import OBS_COLUMNS, aggregate_zone_bins, assign_zone, observation_quality_weight
from ml.pipeline.features import FEATURE_COLUMNS, latest_features
from shared.config import load_config, load_zone_graph
from shared.geo import haversine_m
from shared.schemas import SensorObservation

log = logging.getLogger("crowdpulse.engine")
ALERT_COOLDOWN_MIN = 5
MAX_RETIME_AGE_S = 6 * 3600
FUTURE_TOLERANCE_S = 120  # simulation readings may briefly run ahead of the published clock
# expiry given to recommendations of a simulation run that has ended: in the past for every clock
SIMULATION_ENDED_EXPIRY = datetime(2000, 1, 1, tzinfo=timezone.utc)
INTERVENTION_TTL_MIN = 20
INTERVENTION_RANK = {"increase_monitoring": 0, "deploy_staff": 1, "reduce_inflow": 2, "redirect_flow": 2}


class Engine:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cfg = load_config()
        self.graph = load_zone_graph()
        self.zones = {z["id"]: z for z in self.graph["zones"]}
        self.zone_names = {z["id"]: z["name"] for z in self.graph["zones"]}
        self.expected_sensors: dict[str, int] = {}
        for s in self.graph.get("sensors", []):
            self.expected_sensors[s["zone_id"]] = self.expected_sensors.get(s["zone_id"], 0) + 1
        self.clock = Clock()
        self.models: ModelBundle = load_models(settings.models_dir)
        self.sim: LiveSimulation | None = None
        self.sim_ended: dict[str, Any] | None = None  # the last run that stopped on its own at the end of its scenario
        self.context: dict[str, dict[str, int]] = {}
        self.lock = threading.RLock()
        self.last_refresh: datetime | None = None
        self.latest_states: dict[str, dict[str, Any]] = {}
        self.latest_predictions: dict[str, list[dict[str, Any]]] = {}
        self.latest_features: dict[str, dict[str, Any]] = {}
        self._last_refresh_real = 0.0
        self._last_refresh_started = 0.0
        self.run_markers: dict[str, int] = {"alert_id": 0, "intervention_id": 0}
        self._dirty = False
        self.stats = {"observations_ingested": 0, "observations_rejected": 0, "refreshes": 0, "last_refresh_ms": 0.0}

    # ----------------------------------------------------------- simulation
    def start_sim(self, scenario: str | None = None, acceleration: float | None = None) -> dict[str, Any]:
        with self.lock:
            self.stop_sim()
            self.sim_ended = None
            self.sim = LiveSimulation(scenario or self.settings.sim_scenario, acceleration or self.settings.sim_acceleration, self.cfg["sensor"]["observation_interval_s"])
            self.sim.running = True
            with session_scope() as db:
                self.run_markers = {"alert_id": db.execute(select(func.max(Alert.id))).scalar() or 0,
                                    "intervention_id": db.execute(select(func.max(Intervention.id))).scalar() or 0}
            self.clock.attach(lambda: self.sim.now)
            self.context = self.sim.context()
            self._prime_sim_history()
            return self.sim.status()

    def _prime_sim_history(self, minutes: int = 8) -> None:
        """Emit a few minutes of history quickly so lag features exist from the first frame."""
        assert self.sim is not None
        for _ in range(minutes * 60 // max(1, self.sim.sensor_interval_s)):
            self.sim.advance(self.sim.sensor_interval_s / self.sim.acceleration, self._ingest_from_sim)
        self.refresh(force=True)
        self.sim.sync_real_time()

    def stop_sim(self) -> None:
        with self.lock:
            was_running = self.sim is not None
            if self.sim is not None:
                self.sim.running = False
            # detach first: lock-free readers call clock.now(), which reads self.sim while attached
            self.clock.detach()
            self.sim = None
            if was_running:
                self._close_simulation_run()

    def _close_simulation_run(self) -> None:
        """A stopped simulation's state is no longer current. Drop the cached zone states and forecasts, and
        close the recommendations it produced: their expiry times are in simulated time, which after a stop or
        restart can lie days ahead of the new clock and would block new recommendations indefinitely."""
        self.latest_states, self.latest_predictions, self.latest_features = {}, {}, {}
        marker = self.run_markers.get("intervention_id", 0)
        now = self.clock.now()
        with session_scope() as db:
            for iv in db.execute(select(Intervention).where(Intervention.id > marker, Intervention.status.in_(["pending", "approved"]))).scalars():
                if iv.status == "pending":
                    iv.status = "expired"
                iv.expires_at = SIMULATION_ENDED_EXPIRY
                db.add(AuditLog(timestamp=now, actor="system", action="intervention_closed_simulation_ended", target_type="intervention", target_id=str(iv.id), details={"zone_id": iv.zone_id, "kind": iv.kind, "status": iv.status}))

    def tick(self, real_seconds: float | None = None) -> None:
        """Advance the live simulation to the present (background loop), or by an explicit number of real
        seconds (scripts/tests that step simulated time deterministically)."""
        with self.lock:
            if self.sim is not None and self.sim.running:
                if real_seconds is None:
                    self.sim.advance_to_now(self._ingest_from_sim)
                else:
                    self.sim.advance(real_seconds, self._ingest_from_sim)
                    self.sim.sync_real_time()
                self.context = self.sim.context()
                if self.sim.finished:
                    # Stop at the end of the scenario's script. Left running, a demo kept going overnight and its
                    # simulated clock ended days ahead, with every stored timestamp following it.
                    self.sim_ended = {"scenario": self.sim.scenario, "ended_at": self.sim.now.isoformat(), "reason": "scenario_complete"}
                    self.stop_sim()
        if time.monotonic() - self._last_refresh_real >= self.settings.refresh_seconds:
            self.refresh()

    # ------------------------------------------------------------ ingestion
    def _ingest_from_sim(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        return self.ingest_dicts(rows, source="simulation")

    def ingest_dicts(self, rows: list[dict[str, Any]], source: str = "api") -> dict[str, Any]:
        valid: list[SensorObservation] = []
        rejected = 0
        for r in rows:
            try:
                valid.append(SensorObservation.model_validate(r))
            except Exception:
                rejected += 1
        res = self.ingest(valid, source=source)
        res["rejected"] += rejected
        return res

    def _retime_onto_sim_clock(self, observations: list[SensorObservation]) -> list[SensorObservation]:
        """Hybrid mode: while the live simulation runs, real sensors (phones, replays) report wall-clock
        timestamps, but every recency window in the engine uses the simulated clock. Map each reading onto
        the simulated clock, keeping its real age scaled by the simulation speed:
            sim_ts = sim_now - (wall_now - device_ts) * acceleration
        A reading taken 30 s ago at 10x lands 5 simulated minutes back, so buffered readings flushed late stay
        in the past. Device clocks running ahead of the server are treated as age 0."""
        # bring the simulation up to the present first, so readings are not placed against a clock that has
        # been standing still during a refresh
        self.sim.advance_to_now(self._ingest_from_sim)
        self.context = self.sim.context()
        wall_now = datetime.now(timezone.utc)
        sim_now = self.clock.now()
        accel = self.sim.acceleration
        out = []
        for o in observations:
            # clamp: readings older than MAX_RETIME_AGE_S are far outside every recency window anyway, and an
            # unbounded age x acceleration overflows datetime arithmetic (one bad timestamp would fail the batch)
            age_s = min(MAX_RETIME_AGE_S, max(0.0, (wall_now - utc(o.timestamp)).total_seconds()))
            out.append(o.model_copy(update={"timestamp": sim_now - timedelta(seconds=age_s * accel)}))
        self.stats["api_observations_retimed"] = self.stats.get("api_observations_retimed", 0) + len(out)
        return out

    def ingest(self, observations: list[SensorObservation], source: str = "api") -> dict[str, Any]:
        """``source`` is "api" for HTTP clients and "simulation" for the built-in live simulation.
        It is set by the caller inside the process and cannot be chosen by an HTTP client."""
        # The simulation check, the re-timing and the write happen under one engine lock, so /sim/stop or a
        # restart cannot interleave (previously: HTTP 500, or readings stored against the wrong clock).
        with self.lock:
            if source == "api" and self.sim is not None and self.sim.running:
                observations = self._retime_onto_sim_clock(observations)
            return self._store(observations, source)

    def _store(self, observations: list[SensorObservation], source: str) -> dict[str, Any]:
        now = self.clock.now()
        assignments: dict[str, str | None] = {}
        # Within one batch (e.g. a flushed offline buffer) the sensor's "last_*" snapshot comes from its
        # newest reading, whatever order the batch is in. Across batches the latest batch always wins:
        # comparing against the stored last_seen would freeze sensors whenever the clock jumps back
        # (simulation stopped or restarted, since the simulated clock runs ahead of the wall clock).
        newest: dict[str, int] = {}
        for i, o in enumerate(observations):
            j = newest.get(o.sensor_id)
            if j is None or utc(o.timestamp) >= utc(observations[j].timestamp):
                newest[o.sensor_id] = i
        with session_scope() as db:
            sensors = {s.sensor_id: s for s in db.execute(select(Sensor).where(Sensor.sensor_id.in_({o.sensor_id for o in observations}))).scalars()}
            for i, o in enumerate(observations):
                zone_id = assign_zone(o.latitude, o.longitude, self.graph, self.cfg, o.zone_hint)
                row = o.model_dump(exclude={"zone_hint"})
                w = observation_quality_weight(row, self.cfg)
                db.add(Observation(received_at=now, zone_id=zone_id, quality_weight=w, **row))
                s = sensors.get(o.sensor_id)
                if s is None:
                    s = Sensor(sensor_id=o.sensor_id, first_seen=o.timestamp, observation_count=0)
                    db.add(s)
                    sensors[o.sensor_id] = s
                s.observation_count = (s.observation_count or 0) + 1
                if newest[o.sensor_id] != i:
                    continue
                assignments[o.sensor_id] = zone_id
                s.zone_id = zone_id
                s.last_seen = o.timestamp
                s.last_lat, s.last_lon, s.last_accuracy_m = o.latitude, o.longitude, o.location_accuracy_m
                s.last_heading_deg, s.last_stability, s.last_obstructed = o.heading_deg, o.device_motion_stability, o.camera_obstructed
                s.last_vision_confidence, s.last_person_count, s.last_density = o.vision_confidence, o.person_count, o.estimated_density
                s.model_version, s.mode = o.model_version, o.mode
        self.stats["observations_ingested"] += len(observations)
        if source == "api":
            # only client writes make the next read wait for a refresh (read-after-write); the simulation's
            # own readings are picked up by the periodic refresh
            self._dirty = True
        return {"accepted": len(observations), "rejected": 0, "zone_assignments": assignments, "server_time": now}

    # ---------------------------------------------------------- aggregation
    def _recent_observations(self, db, minutes: int) -> pd.DataFrame:
        # Start the window on a bin boundary. A window starting mid-bin aggregates a partial first bin, and
        # _upsert_states then overwrote that bin's complete stored row with the partial one (by the end of a run
        # every stored bin held its last, partial write: e.g. 2 readings instead of 14).
        bin_s = int(self.cfg["aggregation"]["bin_seconds"])
        start = (self.clock.now() - timedelta(minutes=minutes)).timestamp()
        since = datetime.fromtimestamp(start - start % bin_s, tz=timezone.utc)
        # upper bound: readings dated after "now" belong to a stopped or earlier simulation run (or a device
        # clock running ahead) and must not pin the current state
        rows = db.execute(select(Observation).where(Observation.timestamp >= since, Observation.timestamp <= self.clock.now(), Observation.zone_id.is_not(None))).scalars().all()
        if not rows:
            return pd.DataFrame(columns=OBS_COLUMNS + ["zone_id"])
        return pd.DataFrame([{c: getattr(r, c) for c in OBS_COLUMNS + ["zone_id"]} for r in rows])

    def refresh_if_due(self) -> None:
        """Recompute states/predictions if the periodic refresh is overdue (keeps reads fresh
        even when the background loop has not run yet, e.g. right after ingestion or in tests)."""
        since = time.monotonic() - self._last_refresh_real
        if not (since >= self.settings.refresh_seconds or (self._dirty and since >= 0.5)):
            return
        # Reads wait for the engine only after a client write (so a GET after a POST reflects it). Otherwise,
        # if a refresh or simulation step is running, they return the current results: blocking here let
        # dashboard polls queue refresh after refresh and starve the simulation step for up to ~10 s under load.
        if not self.lock.acquire(blocking=self._dirty):
            return
        try:
            self.refresh()
        finally:
            self.lock.release()

    def refresh(self, force: bool = False) -> None:
        """Recompute zone states for the recent window, run predictions, raise alerts and interventions.

        Several threads (background loop, dashboard requests) can ask for a refresh at once. They queue on the
        engine lock; a caller whose request was already covered by a refresh that STARTED after it asked returns
        immediately instead of recomputing. Without this, every waiting request ran its own full refresh in turn
        and requests waited 20-30 s under normal dashboard polling."""
        requested = time.monotonic()
        with self.lock:
            if not force and self._last_refresh_started >= requested:
                return
            t0 = time.monotonic()
            self._last_refresh_started = t0
            now = self.clock.now()
            hist = int(self.cfg["aggregation"]["history_bins_for_features"]) + 4
            with session_scope() as db:
                obs = self._recent_observations(db, minutes=hist)
                if obs.empty:
                    self._last_refresh_real = time.monotonic()
                    return
                states = aggregate_zone_bins(obs, self.graph, self.cfg, self.expected_sensors)
                self._upsert_states(db, states)
                ctx = pd.DataFrame([{"zone_id": z, "bin_start": b, **self.context.get(z, {"event_indicator": 0, "rain_indicator": 0})} for z, b in zip(states["zone_id"], states["bin_start"])]) if self.context else None
                feats = latest_features(states, self.cfg, ctx)
                stale_after = self.cfg["reliability"]["stale_after_s"]
                for _, row in feats.iterrows():
                    zid = row["zone_id"]
                    feat = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in row.to_dict().items()}
                    age = (now - utc(row["bin_start"].to_pydatetime())).total_seconds()
                    if age > stale_after + self.cfg["aggregation"]["bin_seconds"]:
                        feat["reliability"] = float(feat.get("reliability") or 0.0) * max(0.0, 1 - age / (5 * 60))
                    self.latest_features[zid] = feat
                    st = states[states["zone_id"] == zid].sort_values("bin_start").iloc[-1].to_dict()
                    st["bin_start"] = utc(st["bin_start"].to_pydatetime())
                    self.latest_states[zid] = st
                    preds = predict_zone(self.models, feat, zid, now, self.cfg, self.zone_names)
                    for p in preds:
                        rec = Prediction(**{k: v for k, v in p.items() if k in Prediction.__table__.columns.keys()})
                        db.add(rec)
                        db.flush()
                        p["id"] = rec.id
                    self.latest_predictions[zid] = preds
                    self._raise_alerts(db, zid, preds, now)
                    self._maybe_recommend(db, zid, preds, now)
                self._expire_interventions(db, now)
                self._retention(db, now)
            self.last_refresh = now
            self._dirty = False
            self.stats["refreshes"] += 1
            self.stats["last_refresh_ms"] = round((time.monotonic() - t0) * 1000, 1)
            self._last_refresh_real = time.monotonic()

    def _upsert_states(self, db, states: pd.DataFrame) -> None:
        cols = [c for c in ZoneState.__table__.columns.keys() if c != "id"]
        for rec in states.to_dict(orient="records"):
            rec = {k: (None if (isinstance(v, float) and np.isnan(v)) else v) for k, v in rec.items() if k in cols}
            rec["bin_start"] = utc(pd.Timestamp(rec["bin_start"]).to_pydatetime())
            existing = db.execute(select(ZoneState).where(ZoneState.zone_id == rec["zone_id"], ZoneState.bin_start == rec["bin_start"])).scalar_one_or_none()
            if existing:
                for k, v in rec.items():
                    setattr(existing, k, v)
            else:
                db.add(ZoneState(**rec))

    # ----------------------------------------------------------- alerts etc
    def _raise_alerts(self, db, zid: str, preds: list[dict[str, Any]], now: datetime) -> None:
        name = self.zone_names[zid]
        recent = db.execute(select(Alert).where(Alert.zone_id == zid, Alert.created_at >= now - timedelta(minutes=ALERT_COOLDOWN_MIN))).scalars().all()
        levels = {a.level for a in recent}
        st = self.latest_states.get(zid, {})
        if st.get("congestion_state") == "CRITICAL" and "critical_now" not in levels:
            db.add(Alert(zone_id=zid, created_at=now, level="critical_now", title=f"{name}: CRITICAL now", message=f"Observed density {st['density']:.2f} is above the CRITICAL threshold (reliability {st.get('reliability', 0):.2f}).", confidence=st.get("reliability")))
            levels.add("critical_now")
        for p in sorted(preds, key=lambda p: p["horizon_min"]):
            if p["status"] != "ok":
                continue
            if p["predicted_class"] == "CRITICAL":
                lvl = "human_review" if p["low_confidence"] else "critical"
                if lvl in levels:
                    continue
                msg = f"CRITICAL predicted at {name} in {p['horizon_min']} min ({p['effective_confidence']:.0%} confidence). " + "; ".join(p["reasons"][:3])
                if p["low_confidence"]:
                    msg = "LOW CONFIDENCE - HUMAN REVIEW REQUIRED. " + msg
                if p["ood_flag"]:
                    msg += " " + self.cfg["ood"]["message"]
                db.add(Alert(zone_id=zid, created_at=now, level=lvl, title=f"{name}: CRITICAL forecast (+{p['horizon_min']} min)", message=msg, horizon_min=p["horizon_min"], prediction_id=p.get("id"), confidence=p["effective_confidence"]))
                levels.add(lvl)
                break
            if p["predicted_class"] == "WARNING" and not p["low_confidence"] and "warning" not in levels and st.get("congestion_state") == "SAFE":
                db.add(Alert(zone_id=zid, created_at=now, level="warning", title=f"{name}: WARNING forecast (+{p['horizon_min']} min)", message=f"WARNING predicted in {p['horizon_min']} min ({p['effective_confidence']:.0%} confidence). " + "; ".join(p["reasons"][:2]), horizon_min=p["horizon_min"], prediction_id=p.get("id"), confidence=p["effective_confidence"]))
                levels.add("warning")
                break
        if preds and preds[0]["ood_flag"] and "ood" not in levels:
            db.add(Alert(zone_id=zid, created_at=now, level="ood", title=f"{name}: unusual conditions", message=self.cfg["ood"]["message"] + " " + "; ".join(preds[0]["ood_reasons"][:2]), confidence=None))
        if st.get("reliability", 1.0) < 0.5 and "sensor" not in levels:
            db.add(Alert(zone_id=zid, created_at=now, level="sensor", title=f"{name}: sensor reliability low", message=f"Zone reliability {st.get('reliability', 0):.2f}: {st.get('n_sensors', 0)}/{self.expected_sensors.get(zid, 0)} sensors online, obstruction {st.get('obstructed_fraction', 0):.0%}, disagreement {st.get('disagreement', 0):.2f}.", confidence=st.get("reliability")))

    def _maybe_recommend(self, db, zid: str, preds: list[dict[str, Any]], now: datetime) -> None:
        ok = sorted((p for p in preds if p["status"] == "ok"), key=lambda p: p["horizon_min"])
        recommend = [p for p in ok if p["predicted_class"] in self.cfg["intervention"]["recommend_when"]]
        # a confident CRITICAL forecast at any horizon outranks a low-confidence one at a shorter horizon
        trigger = next((p for p in recommend if not p["low_confidence"]), None) or (recommend[0] if recommend else None)
        if trigger is None and self.latest_states.get(zid, {}).get("congestion_state") == "CRITICAL":
            trigger = ok[0] if ok else None
        if trigger is None:
            trigger = next((p for p in ok if p["predicted_class"] in self.cfg["intervention"]["monitor_when"] and not p["low_confidence"]), None)
        if trigger is None:
            return
        rec = build_recommendation(self.zones[zid], self.graph, self.latest_states, trigger, self.cfg)
        open_ivs = db.execute(select(Intervention).where(Intervention.zone_id == zid, Intervention.status.in_(["pending", "approved"]), Intervention.expires_at > now)).scalars().all()
        rank = INTERVENTION_RANK.get(rec["kind"], 0)
        # An open recommendation blocks new ones unless the new one is a stronger action (monitoring -> staff ->
        # redirect / inflow control). Weaker PENDING ones are superseded; APPROVED ones stay approved (an action in
        # progress) and the stronger recommendation is added alongside. Previously a pending "increase monitoring"
        # or an approved "deploy staff" blocked a confident CRITICAL redirect for its whole 20-minute lifetime.
        if any(INTERVENTION_RANK.get(o.kind, 0) >= rank for o in open_ivs):
            return
        for open_iv in open_ivs:
            if open_iv.status == "pending":
                open_iv.status = "superseded"
                db.add(AuditLog(timestamp=now, actor="system", action="intervention_superseded", target_type="intervention", target_id=str(open_iv.id),
                                details={"zone_id": zid, "kind": open_iv.kind, "superseded_by_kind": rec["kind"], "predicted_class": rec["predicted_class"], "confidence": rec["confidence"]}))
        iv = Intervention(zone_id=zid, created_at=now, status="pending", prediction_id=trigger.get("id"), expires_at=now + timedelta(minutes=INTERVENTION_TTL_MIN), **{k: v for k, v in rec.items() if k in Intervention.__table__.columns.keys()})
        db.add(iv)
        db.flush()
        db.add(AuditLog(timestamp=now, actor="system", action="intervention_recommended", target_type="intervention", target_id=str(iv.id), details={"zone_id": zid, "kind": rec["kind"], "predicted_class": rec["predicted_class"], "confidence": rec["confidence"], "horizon_min": rec["horizon_min"]}))

    def decide_intervention(self, iv_id: int, approve: bool, operator: str, note: str | None) -> Intervention:
        now = self.clock.now()
        with self.lock, session_scope() as db:
            iv = db.get(Intervention, iv_id)
            if iv is None:
                raise KeyError(iv_id)
            if iv.status != "pending":
                raise ValueError(f"intervention {iv_id} already {iv.status}")
            iv.status = "approved" if approve else "rejected"
            iv.decided_at, iv.decided_by, iv.decision_note = now, operator, note
            if approve:
                eff = iv.assumed_effect or {}
                mult = 1.0 - float(eff.get("inflow_reduction", 0.0))
                if self.sim is not None and iv.kind in ("redirect_flow", "reduce_inflow") and mult < 1.0:
                    self.sim.apply_redirect(iv.zone_id, mult, float(eff.get("duration_min", 20)))
                    iv.effect_applied = True
                feat = self.latest_features.get(iv.zone_id)
                if feat and self.models.loaded and mult < 1.0:
                    iv.projected_after = what_if_prediction(self.models, feat, mult)
            db.add(AuditLog(timestamp=now, actor=operator, action="intervention_approved" if approve else "intervention_rejected", target_type="intervention", target_id=str(iv.id), details={"zone_id": iv.zone_id, "kind": iv.kind, "note": note, "effect_applied_to_simulation": iv.effect_applied}))
            db.flush()
            db.refresh(iv)
            return iv

    def _expire_interventions(self, db, now: datetime) -> None:
        for iv in db.execute(select(Intervention).where(Intervention.status == "pending", Intervention.expires_at <= now)).scalars():
            iv.status = "expired"
            db.add(AuditLog(timestamp=now, actor="system", action="intervention_expired", target_type="intervention", target_id=str(iv.id), details={"zone_id": iv.zone_id}))

    def _retention(self, db, now: datetime) -> None:
        if self.stats["refreshes"] % 100 != 0:
            return
        cutoff = now - timedelta(hours=self.settings.retention_hours)
        db.execute(delete(Observation).where(Observation.timestamp < cutoff))
        db.execute(delete(Prediction).where(Prediction.created_at < cutoff))

    # -------------------------------------------------------------- queries
    def sensor_status(self, s: Sensor) -> dict[str, Any]:
        now = self.clock.now()
        age = (now - utc(s.last_seen)).total_seconds()
        r = self.cfg["reliability"]
        issues = []
        if age < -FUTURE_TOLERANCE_S:
            status = "offline"; issues.append("last reading is dated in the future (device clock ahead, or from a stopped simulation)")
        elif age > r["stale_after_s"] * 4:
            status = "offline"; issues.append("no observations received")
        elif age > r["stale_after_s"]:
            status = "stale"; issues.append("observations delayed")
        else:
            status = "online"
        if s.last_obstructed:
            issues.append("camera obstructed")
        if s.last_stability < r["min_motion_stability"]:
            issues.append("device moving")
        if s.last_accuracy_m > r["max_gps_accuracy_m"]:
            issues.append("weak GPS")
        if s.last_vision_confidence < r["min_vision_confidence"]:
            issues.append("low vision confidence")
        placement, distance = "none", None
        if s.zone_id is None:
            issues.append("outside any zone: choose a zone in the app's Setup page")
        elif s.zone_id in self.zones:
            z = self.zones[s.zone_id]
            distance = haversine_m(s.last_lat, s.last_lon, z["lat"], z["lon"])
            placement = "gps" if distance <= self.cfg["sensor"]["zone_assignment_radius_m"] else "zone_hint"
        q = observation_quality_weight({"device_motion_stability": s.last_stability, "camera_obstructed": s.last_obstructed, "location_accuracy_m": s.last_accuracy_m, "vision_confidence": s.last_vision_confidence}, self.cfg)
        score = q * (1.0 if status == "online" else 0.5 if status == "stale" else 0.0)
        return {"sensor_id": s.sensor_id, "zone_id": s.zone_id, "status": status, "last_seen": s.last_seen, "seconds_since_seen": round(age, 1), "latitude": s.last_lat, "longitude": s.last_lon,
                "location_accuracy_m": s.last_accuracy_m, "heading_deg": s.last_heading_deg, "device_motion_stability": s.last_stability, "camera_obstructed": s.last_obstructed,
                "vision_confidence": s.last_vision_confidence, "person_count": s.last_person_count, "estimated_density": s.last_density, "model_version": s.model_version, "mode": s.mode,
                "observation_count": s.observation_count, "reliability_score": round(score, 3), "issues": issues,
                "placement": placement, "distance_to_zone_m": None if distance is None else round(distance, 1)}

    def zone_view(self, db, zid: str) -> dict[str, Any]:
        z = self.zones[zid]
        now = self.clock.now()
        st = self.latest_states.get(zid)
        preds = self.latest_predictions.get(zid, [])
        sensors = db.execute(select(Sensor).where(Sensor.zone_id == zid)).scalars().all()
        online = sum(1 for s in sensors if self.sensor_status(s)["status"] == "online")
        age = (now - st["bin_start"]).total_seconds() if st else None
        stale = st is None or age > self.cfg["reliability"]["stale_after_s"] + self.cfg["aggregation"]["bin_seconds"]
        risk = "UNKNOWN"
        if st:
            order = ["SAFE", "WARNING", "CRITICAL"]
            risk = st["congestion_state"]
            for p in preds:
                if p["status"] == "ok" and not p["low_confidence"] and order.index(p["predicted_class"]) > order.index(risk):
                    risk = p["predicted_class"]
        open_ivs = db.execute(select(Intervention).where(Intervention.zone_id == zid, Intervention.status.in_(["pending", "approved"]), Intervention.expires_at > now).order_by(Intervention.created_at.desc())).scalars().all()
        iv = max(open_ivs, key=lambda o: (INTERVENTION_RANK.get(o.kind, 0), o.status == "pending"), default=None)
        nbrs = sorted({e["to"] for e in self.graph["edges"] if e["from"] == zid} | {e["from"] for e in self.graph["edges"] if e["to"] == zid})
        return {"id": zid, "name": z["name"], "lat": z["lat"], "lon": z["lon"], "kind": z["kind"], "capacity": z["capacity"], "polygon_radius_m": z["polygon_radius_m"], "neighbours": nbrs,
                "state": st, "stale": stale, "seconds_since_update": age, "sensors": [s.sensor_id for s in sensors], "sensors_online": online, "sensors_expected": max(self.expected_sensors.get(zid, 0), len(sensors)),
                "predictions": preds, "risk": risk, "active_intervention_id": iv.id if iv else None}


_engine: Engine | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        from backend.app.config import get_settings
        _engine = Engine(get_settings())
    return _engine


def reset_engine() -> None:
    global _engine
    if _engine is not None:
        _engine.stop_sim()
    _engine = None
