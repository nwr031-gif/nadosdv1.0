"""
NADOS Dv1.0 Domain Models

Core domain models for the simulation environment.
All models use Pydantic for validation and serialization.
"""

from .base import Matrix3x3, SimulationBaseModel, Vector3D, validate_non_negative, validate_positive
from .event import EventSeverity, EventType, SimulationEvent
from .observation import SensorObservation, ValidityStatus
from .run import RunStatus, SimulationRun
from .scenario import (
    CoordinateSystem,
    EnvironmentalConditions,
    ObjectType,
    SensorDefinition,
    SensorType,
    SimulationScenario,
    VirtualObject,
    VisualizationSettings,
)
from .track import TrackEstimate, TrackingStatus

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
