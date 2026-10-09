"""
Simulation run domain models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .base import SimulationBaseModel, validate_non_negative


class RunStatus(str, Enum):
    """Status of a simulation run."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SimulationRun(SimulationBaseModel):
    """Record of a simulation run."""
    
    run_id: str
    scenario_id: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    random_seed: int = 42
    application_version: str = "1.0.0"
    configuration_hash: str = ""
    status: RunStatus = RunStatus.PENDING
    summary_metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("run_id")
    @classmethod
    def validate_run_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("run_id cannot be empty")
        return v.strip()
    
    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("scenario_id cannot be empty")
        return v.strip()
    
    @field_validator("random_seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        if v < 0:
            raise ValueError("random_seed must be non-negative")
        return v
    
    def duration_seconds(self) -> Optional[float]:
        """Get run duration in seconds."""
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def is_complete(self) -> bool:
        """Check if run has completed (successfully or not)."""
        return self.status in (RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED)