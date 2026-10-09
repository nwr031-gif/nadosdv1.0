"""
NADOS Dv1.0 Domain Models

Core domain models for the simulation environment.
All models use Pydantic for validation and serialization.
"""

from .base import SimulationBaseModel, validate_non_negative, validate_positive, Vector3D, Matrix3x3
from .scenario import (
    SimulationScenario,
    VirtualObject,
    SensorDefinition,
    EnvironmentalConditions,
    VisualizationSettings,
    CoordinateSystem,
    ObjectType,
    SensorType,
)
from .observation import SensorObservation, ValidityStatus
from .track import TrackEstimate, TrackingStatus
from .event import SimulationEvent, EventType, EventSeverity
from .run import SimulationRun, RunStatus

__all__ = [
    "SimulationBaseModel",
    "validate_non_negative",
    "validate_positive",
    "Vector3D",
    "Matrix3x3",
    "SimulationScenario",
    "VirtualObject",
    "SensorDefinition",
    "EnvironmentalConditions",
    "VisualizationSettings",
    "CoordinateSystem",
    "ObjectType",
    "SensorType",
    "SensorObservation",
    "ValidityStatus",
    "TrackEstimate",
    "TrackingStatus",
    "SimulationEvent",
    "EventType",
    "EventSeverity",
    "SimulationRun",
    "RunStatus",
]