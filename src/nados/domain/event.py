"""
Simulation event domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import SimulationBaseModel, validate_non_negative


class EventType(str, Enum):
    """Types of simulation events."""
    SCENARIO_STARTED = "scenario_started"
    SCENARIO_PAUSED = "scenario_paused"
    SCENARIO_RESUMED = "scenario_resumed"
    SCENARIO_STOPPED = "scenario_stopped"
    SCENARIO_RESET = "scenario_reset"
    SCENARIO_COMPLETED = "scenario_completed"
    OBJECT_CREATED = "object_created"
    OBJECT_DESTROYED = "object_destroyed"
    OBJECT_UPDATED = "object_updated"
    OBSERVATION_GENERATED = "observation_generated"
    OBSERVATION_RECEIVED = "observation_received"
    TRACK_INITIALIZED = "track_initialized"
    TRACK_UPDATED = "track_updated"
    TRACK_LOST = "track_lost"
    TRACK_TERMINATED = "track_terminated"
    FUSION_PERFORMED = "fusion_performed"
    SENSOR_STATUS_CHANGED = "sensor_status_changed"
    ERROR_OCCURRED = "error_occurred"
    WARNING_ISSUED = "warning_issued"
    USER_ACTION = "user_action"
    SYSTEM_EVENT = "system_event"


class EventSeverity(str, Enum):
    """Severity levels for events."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SimulationEvent(SimulationBaseModel):
    """Simulation event for logging and replay."""
    
    event_id: str
    event_type: EventType
    timestamp: float  # Simulation time in seconds
    severity: EventSeverity = EventSeverity.INFO
    message: str
    source_module: str
    associated_object_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("event_id cannot be empty")
        return v.strip()
    
    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: float) -> float:
        return validate_non_negative(v, "timestamp")
    
    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message cannot be empty")
        return v.strip()
    
    @field_validator("source_module")
    @classmethod
    def validate_source_module(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_module cannot be empty")
        return v.strip()