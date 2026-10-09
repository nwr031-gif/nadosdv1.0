"""
Base classes and validators for domain models.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SimulationBaseModel(BaseModel):
    """Base model for all simulation domain objects."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        ser_json_timedelta="iso8601",
        ser_json_bytes="base64",
    )
    
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("updated_at", mode="before")
    @classmethod
    def set_updated_at(cls, v: Any) -> datetime:
        return datetime.utcnow()


def validate_non_negative(value: float, field_name: str = "value") -> float:
    """Validate that a value is non-negative."""
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative, got {value}")
    return value


def validate_positive(value: float, field_name: str = "value") -> float:
    """Validate that a value is positive."""
    if value <= 0:
        raise ValueError(f"{field_name} must be positive, got {value}")
    return value


def validate_finite(value: float, field_name: str = "value") -> float:
    """Validate that a value is finite (not NaN or infinity)."""
    import math
    if not math.isfinite(value):
        raise ValueError(f"{field_name} must be finite, got {value}")
    return value


class Vector3D(BaseModel):
    """3D vector with x, y, z components."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
    )
    
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    
    def to_array(self) -> list[float]:
        return [self.x, self.y, self.z]
    
    @classmethod
    def from_array(cls, arr: list[float]) -> "Vector3D":
        if len(arr) != 3:
            raise ValueError("Array must have exactly 3 elements")
        return cls(x=arr[0], y=arr[1], z=arr[2])
    
    def __add__(self, other: "Vector3D") -> "Vector3D":
        return Vector3D(x=self.x + other.x, y=self.y + other.y, z=self.z + other.z)
    
    def __sub__(self, other: "Vector3D") -> "Vector3D":
        return Vector3D(x=self.x - other.x, y=self.y - other.y, z=self.z - other.z)
    
    def __mul__(self, scalar: float) -> "Vector3D":
        return Vector3D(x=self.x * scalar, y=self.y * scalar, z=self.z * scalar)
    
    def magnitude(self) -> float:
        import math
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)
    
    def normalized(self) -> "Vector3D":
        mag = self.magnitude()
        if mag == 0:
            return Vector3D()
        return self * (1.0 / mag)


class Matrix3x3(BaseModel):
    """3x3 matrix for covariance and transformation matrices."""
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
    )
    
    data: list[list[float]] = Field(
        default_factory=lambda: [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    )
    
    @field_validator("data")
    @classmethod
    def validate_matrix(cls, v: list[list[float]]) -> list[list[float]]:
        if len(v) != 3 or any(len(row) != 3 for row in v):
            raise ValueError("Matrix must be 3x3")
        return v
    
    @classmethod
    def identity(cls) -> "Matrix3x3":
        return cls()
    
    @classmethod
    def diagonal(cls, values: list[float]) -> "Matrix3x3":
        if len(values) != 3:
            raise ValueError("Need exactly 3 diagonal values")
        return cls(data=[[values[0], 0, 0], [0, values[1], 0], [0, 0, values[2]]])
    
    def to_array(self) -> list[list[float]]:
        return self.data
    
    def trace(self) -> float:
        return sum(self.data[i][i] for i in range(3))