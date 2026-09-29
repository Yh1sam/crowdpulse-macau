"""Pydantic model for the sensor observation — the single schema shared by
real phones, the synthetic generator and the backend ingestion endpoint."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SensorObservation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: str = Field(pattern=r"^node-[a-z0-9]{4,32}$", description="Anonymous node id")
    timestamp: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_accuracy_m: float = Field(ge=0, le=10000)
    heading_deg: float = Field(ge=0, le=360)
    device_motion_stability: float = Field(ge=0, le=1)
    person_count: int = Field(ge=0, le=5000)
    estimated_density: float = Field(ge=0, le=1, description="Relative density index (not persons/m^2)")
    flow_direction_deg: float = Field(ge=0, le=360)
    flow_speed_mps: float = Field(ge=0, le=10)
    vision_confidence: float = Field(ge=0, le=1)
    camera_obstructed: bool
    model_version: str = Field(max_length=64)
    mode: Optional[Literal["live", "video", "simulated"]] = None
    zone_hint: Optional[str] = Field(default=None, max_length=64, description="Operator-chosen zone (id or name); used when GPS is not within a zone")

    @field_validator("timestamp")
    @classmethod
    def _ensure_tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class ObservationBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    observations: list[SensorObservation] = Field(min_length=1, max_length=500)
