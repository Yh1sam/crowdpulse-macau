"""Database tables. Only numerical / categorical metadata is stored - never images."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Index, Integer, String, Text, TypeDecorator, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db import Base


class UTCDateTime(TypeDecorator):
    """Timezone-aware UTC datetimes on every backend. SQLite drops tzinfo, which would make
    the API emit naive timestamps that browsers interpret as local time."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Sensor(Base):
    __tablename__ = "sensors"
    sensor_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_seen: Mapped[datetime] = mapped_column(UTCDateTime())
    last_seen: Mapped[datetime] = mapped_column(UTCDateTime())
    last_lat: Mapped[float] = mapped_column(Float)
    last_lon: Mapped[float] = mapped_column(Float)
    last_accuracy_m: Mapped[float] = mapped_column(Float)
    last_heading_deg: Mapped[float] = mapped_column(Float)
    last_stability: Mapped[float] = mapped_column(Float)
    last_obstructed: Mapped[bool] = mapped_column(Boolean, default=False)
    last_vision_confidence: Mapped[float] = mapped_column(Float)
    last_person_count: Mapped[int] = mapped_column(Integer, default=0)
    last_density: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String(64), default="")
    mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    observation_count: Mapped[int] = mapped_column(Integer, default=0)


class Observation(Base):
    __tablename__ = "observations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sensor_id: Mapped[str] = mapped_column(String(64), index=True)
    zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime())
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_accuracy_m: Mapped[float] = mapped_column(Float)
    heading_deg: Mapped[float] = mapped_column(Float)
    device_motion_stability: Mapped[float] = mapped_column(Float)
    person_count: Mapped[int] = mapped_column(Integer)
    estimated_density: Mapped[float] = mapped_column(Float)
    flow_direction_deg: Mapped[float] = mapped_column(Float)
    flow_speed_mps: Mapped[float] = mapped_column(Float)
    vision_confidence: Mapped[float] = mapped_column(Float)
    camera_obstructed: Mapped[bool] = mapped_column(Boolean)
    model_version: Mapped[str] = mapped_column(String(64))
    mode: Mapped[str | None] = mapped_column(String(16), nullable=True)
    quality_weight: Mapped[float] = mapped_column(Float, default=1.0)
    __table_args__ = (Index("ix_obs_zone_ts", "zone_id", "timestamp"),)


class ZoneState(Base):
    __tablename__ = "zone_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True)
    bin_start: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    density: Mapped[float] = mapped_column(Float)
    person_count_visible: Mapped[float] = mapped_column(Float)
    flow_direction_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    flow_speed_mps: Mapped[float] = mapped_column(Float)
    flow_coherence: Mapped[float] = mapped_column(Float)
    n_obs: Mapped[int] = mapped_column(Integer)
    n_sensors: Mapped[int] = mapped_column(Integer)
    reliability: Mapped[float] = mapped_column(Float)
    disagreement: Mapped[float] = mapped_column(Float)
    obstructed_fraction: Mapped[float] = mapped_column(Float)
    mean_stability: Mapped[float] = mapped_column(Float)
    mean_gps_accuracy_m: Mapped[float] = mapped_column(Float)
    mean_vision_confidence: Mapped[float] = mapped_column(Float)
    congestion_state: Mapped[str] = mapped_column(String(16))
    inflow_proxy: Mapped[float] = mapped_column(Float)
    outflow_proxy: Mapped[float] = mapped_column(Float)
    neighbour_density_mean: Mapped[float | None] = mapped_column(Float, nullable=True)
    neighbour_density_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    neighbour_inflow_sum: Mapped[float] = mapped_column(Float)
    neighbour_max_zone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    __table_args__ = (UniqueConstraint("zone_id", "bin_start", name="uq_zone_bin"),)


class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    horizon_min: Mapped[int] = mapped_column(Integer)
    target_time: Mapped[datetime] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String(32))  # ok | insufficient_data | fallback
    predicted_class: Mapped[str | None] = mapped_column(String(16), nullable=True)
    probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    model_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reliability: Mapped[float] = mapped_column(Float, default=0.0)
    effective_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)
    ood_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    ood_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ood_reasons: Mapped[list] = mapped_column(JSON, default=list)
    predicted_density: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    contributions: Mapped[list] = mapped_column(JSON, default=list)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    model_type: Mapped[str] = mapped_column(String(64), default="")
    model_version: Mapped[str] = mapped_column(String(64), default="")
    current_state: Mapped[str | None] = mapped_column(String(16), nullable=True)
    __table_args__ = (Index("ix_pred_zone_created", "zone_id", "created_at"),)


class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    level: Mapped[str] = mapped_column(String(16))  # info | warning | critical | human_review | sensor
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    horizon_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prediction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    acknowledged_by: Mapped[str | None] = mapped_column(String(64), nullable=True)


class Intervention(Base):
    __tablename__ = "interventions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending | approved | rejected | expired
    kind: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(200))
    recommendation: Mapped[str] = mapped_column(Text)
    rationale: Mapped[list] = mapped_column(JSON, default=list)
    predicted_class: Mapped[str | None] = mapped_column(String(16), nullable=True)
    horizon_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    low_confidence: Mapped[bool] = mapped_column(Boolean, default=False)
    route: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    route_alternatives: Mapped[list] = mapped_column(JSON, default=list)
    accessibility: Mapped[dict] = mapped_column(JSON, default=dict)
    messages: Mapped[dict] = mapped_column(JSON, default=dict)  # zh / en / pt public-facing text
    assumed_effect: Mapped[dict] = mapped_column(JSON, default=dict)
    projected_after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prediction_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)
    decided_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    effect_applied: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime | None] = mapped_column(UTCDateTime(), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    actor: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(32))
    target_id: Mapped[str] = mapped_column(String(64))
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class GroundTruth(Base):
    """Manually recorded ground truth from controlled experiments (school trials)."""
    __tablename__ = "ground_truth"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    zone_id: Mapped[str] = mapped_column(String(64), index=True)
    timestamp: Mapped[datetime] = mapped_column(UTCDateTime(), index=True)
    actual_count: Mapped[int] = mapped_column(Integer)
    actual_class: Mapped[str | None] = mapped_column(String(16), nullable=True)
    condition: Mapped[str | None] = mapped_column(String(64), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[str | None] = mapped_column(String(64), nullable=True)
