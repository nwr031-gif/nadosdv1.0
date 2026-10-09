"""
Track estimate domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import Matrix3x3, SimulationBaseModel, Vector3D, validate_non_negative


class TrackingStatus(str, Enum):
    """Status of a track estimate."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    COASTING = "coasting"  # No recent observations
    LOST = "lost"
    TERMINATED = "terminated"


class TrackEstimate(SimulationBaseModel):
    """Track estimate from filtering/estimation process."""
    
    track_id: str
    timestamp: float  # Simulation time in seconds
    estimated_position: Vector3D = Field(default_factory=Vector3D)
    estimated_velocity: Vector3D = Field(default_factory=Vector3D)
    covariance_or_uncertainty: Matrix3x3 = Field(default_factory=Matrix3x3.identity)
    observation_count: int = 0
    tracking_status: TrackingStatus = TrackingStatus.INITIALIZING
    source_sensor_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("track_id")
    @classmethod
    def validate_track_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("track_id cannot be empty")
        return v.strip()
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: float) -> float:
        return validate_non_negative(v, "timestamp")
    
    @field_validator("observation_count")
    @classmethod
    def validate_observation_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("observation_count must be non-negative")
        return v
    
    def get_position_uncertainty(self) -> Vector3D:
        """Get position uncertainty (sqrt of diagonal covariance)."""
        import math
        cov = self.covariance_or_uncertainty.data
        return Vector3D(
            x=math.sqrt(max(0, cov[0][0])),
            y=math.sqrt(max(0, cov[1][1])),
            z=math.sqrt(max(0, cov[2][2])),
        )
    
    def is_active(self) -> bool:
        """Check if track is actively being updated."""
        return self.tracking_status in (TrackingStatus.ACTIVE, TrackingStatus.COASTING)
    
    def get_covariance_array(self) -> list[list[float]]:
        """Get covariance matrix as nested list."""
        return self.covariance_or_uncertainty.to_array()