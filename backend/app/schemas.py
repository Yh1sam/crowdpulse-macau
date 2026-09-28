"""API response / request models (Pydantic)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    zone_assignments: dict[str, Optional[str]]
    server_time: datetime
    privacy_mode: bool


class SensorOut(BaseModel):
    sensor_id: str
    zone_id: Optional[str]
    status: str  # online | stale | offline
    last_seen: datetime
    seconds_since_seen: float
    latitude: float
    longitude: float
    location_accuracy_m: float
    heading_deg: float
    device_motion_stability: float
    camera_obstructed: bool
    vision_confidence: float
    person_count: int
    estimated_density: float
    model_version: str
    mode: Optional[str]
    observation_count: int
    reliability_score: float
    issues: list[str]


class PredictionOut(BaseModel):
    id: Optional[int] = None
    zone_id: str
    created_at: datetime
    horizon_min: int
    target_time: datetime
    status: str
    predicted_class: Optional[str]
    probabilities: dict[str, float]
    model_confidence: float
    reliability: float
    effective_confidence: float
    low_confidence: bool
    human_review_required: bool
    ood_flag: bool
    ood_score: Optional[float]
    ood_reasons: list[str]
    ood_message: Optional[str]
    predicted_density: Optional[float]
    reasons: list[str]
    contributions: list[dict[str, Any]]
    model_type: str
    model_version: str
    current_state: Optional[str]
    message: Optional[str] = None


class ZoneStateOut(BaseModel):
    zone_id: str
    bin_start: datetime
    density: float
    person_count_visible: float
    flow_direction_deg: Optional[float]
    flow_speed_mps: float
    flow_coherence: float
    n_obs: int
    n_sensors: int
    reliability: float
    disagreement: float
    obstructed_fraction: float
    congestion_state: str
    inflow_proxy: float
    outflow_proxy: float
    neighbour_density_mean: Optional[float]
    neighbour_density_max: Optional[float]
    neighbour_inflow_sum: float


class ZoneOut(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    kind: str
    capacity: int
    polygon_radius_m: float
    neighbours: list[str]
    state: Optional[ZoneStateOut]
    stale: bool
    seconds_since_update: Optional[float]
    sensors: list[str]
    sensors_online: int
    sensors_expected: int
    predictions: list[PredictionOut]
    risk: str  # SAFE | WARNING | CRITICAL | UNKNOWN (max of current + confident predictions)
    active_intervention_id: Optional[int]


class AlertOut(BaseModel):
    id: int
    zone_id: str
    created_at: datetime
    level: str
    title: str
    message: str
    horizon_min: Optional[int]
    prediction_id: Optional[int]
    confidence: Optional[float]
    acknowledged: bool


class InterventionOut(BaseModel):
    id: int
    zone_id: str
    created_at: datetime
    status: str
    kind: str
    title: str
    recommendation: str
    rationale: list[str]
    predicted_class: Optional[str]
    horizon_min: Optional[int]
    confidence: Optional[float]
    low_confidence: bool
    route: Optional[dict[str, Any]]
    route_alternatives: list[dict[str, Any]]
    accessibility: dict[str, Any]
    messages: dict[str, str]
    assumed_effect: dict[str, Any]
    projected_after: Optional[dict[str, Any]]
    prediction_id: Optional[int]
    decided_at: Optional[datetime]
    decided_by: Optional[str]
    decision_note: Optional[str]
    effect_applied: bool


class DecisionIn(BaseModel):
    operator: str = Field(default="operator", max_length=64)
    note: Optional[str] = Field(default=None, max_length=1000)


class AuditOut(BaseModel):
    id: int
    timestamp: datetime
    actor: str
    action: str
    target_type: str
    target_id: str
    details: dict[str, Any]


class GroundTruthIn(BaseModel):
    zone_id: str
    timestamp: datetime
    actual_count: int = Field(ge=0, le=100000)
    actual_class: Optional[str] = None
    condition: Optional[str] = Field(default=None, max_length=64)
    notes: Optional[str] = Field(default=None, max_length=2000)
    recorded_by: Optional[str] = Field(default=None, max_length=64)


class SimStartIn(BaseModel):
    scenario: str = "golden_week_demo"
    acceleration: float = Field(default=6.0, ge=0.1, le=120)


class SimInjectIn(BaseModel):
    zone_id: str
    people: int = Field(ge=1, le=5000)


class ContextIn(BaseModel):
    event_indicator: Optional[int] = Field(default=None, ge=0, le=1)
    rain_indicator: Optional[int] = Field(default=None, ge=0, le=1)
