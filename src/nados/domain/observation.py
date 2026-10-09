"""
Sensor observation domain models.
"""

from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import Matrix3x3, SimulationBaseModel, Vector3D, validate_non_negative


class ValidityStatus(str, Enum):
    """Validity status of a sensor observation."""

    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    DELAYED = "delayed"
    OUT_OF_RANGE = "out_of_range"
    SENSOR_ERROR = "sensor_error"


class SensorObservation(SimulationBaseModel):
    """Single sensor observation."""

    observation_id: str
    sensor_id: str
    timestamp: float  # Simulation time in seconds
    measured_position: Vector3D = Field(default_factory=Vector3D)
    measurement_uncertainty: Matrix3x3 = Field(default_factory=Matrix3x3.identity)
    validity_status: ValidityStatus = ValidityStatus.VALID
    scenario_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("observation_id")
    @classmethod
    def validate_observation_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("observation_id cannot be empty")
        return v.strip()

    @field_validator("sensor_id")
    @classmethod
    def validate_sensor_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sensor_id cannot be empty")
        return v.strip()

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: float) -> float:
        return validate_non_negative(v, "timestamp")

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("scenario_id cannot be empty")
        return v.strip()

    def is_valid(self) -> bool:
        """Check if observation is valid for tracking."""
        return self.validity_status == ValidityStatus.VALID

    def get_covariance_array(self) -> list[list[float]]:
        """Get covariance matrix as nested list."""
        return self.measurement_uncertainty.to_array()
