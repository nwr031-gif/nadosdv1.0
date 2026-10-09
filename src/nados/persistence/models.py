"""
SQLAlchemy models for persistence.
"""

import json
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Text, ForeignKey, Index, Boolean, LargeBinary
)
from sqlalchemy.orm import relationship

from .database import Base


class ScenarioModel(Base):
    """Scenario persistence model."""
    
    __tablename__ = "scenarios"
    
    id = Column(String(64), primary_key=True)
    schema_version = Column(String(16), nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text)
    duration_seconds = Column(Float, nullable=False)
    timestep_seconds = Column(Float, nullable=False)
    random_seed = Column(Integer, nullable=False)
    coordinate_system = Column(String(16), nullable=False)
    scenario_data = Column(Text, nullable=False)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    runs = relationship("RunModel", back_populates="scenario", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_scenarios_name", "name"),
        Index("ix_scenarios_created", "created_at"),
    )


class RunModel(Base):
    """Simulation run persistence model."""
    
    __tablename__ = "runs"
    
    id = Column(String(64), primary_key=True)
    scenario_id = Column(String(64), ForeignKey("scenarios.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    random_seed = Column(Integer, nullable=False)
    application_version = Column(String(32), nullable=False)
    configuration_hash = Column(String(64))
    status = Column(String(32), nullable=False)
    summary_metrics = Column(Text)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    scenario = relationship("ScenarioModel", back_populates="runs")
    observations = relationship("ObservationModel", back_populates="run", cascade="all, delete-orphan")
    tracks = relationship("TrackModel", back_populates="run", cascade="all, delete-orphan")
    events = relationship("EventModel", back_populates="run", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("ix_runs_scenario", "scenario_id"),
        Index("ix_runs_status", "status"),
        Index("ix_runs_started", "started_at"),
    )


class ObservationModel(Base):
    """Sensor observation persistence model."""
    
    __tablename__ = "observations"
    
    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    sensor_id = Column(String(64), nullable=False)
    timestamp = Column(Float, nullable=False)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    uncertainty_xx = Column(Float, nullable=False)
    uncertainty_xy = Column(Float, nullable=False)
    uncertainty_xz = Column(Float, nullable=False)
    uncertainty_yy = Column(Float, nullable=False)
    uncertainty_yz = Column(Float, nullable=False)
    uncertainty_zz = Column(Float, nullable=False)
    validity_status = Column(String(32), nullable=False)
    scenario_id = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RunModel", back_populates="observations")
    
    __table_args__ = (
        Index("ix_observations_run", "run_id"),
        Index("ix_observations_sensor", "sensor_id"),
        Index("ix_observations_time", "timestamp"),
    )


class TrackModel(Base):
    """Track estimate persistence model."""
    
    __tablename__ = "tracks"
    
    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    timestamp = Column(Float, nullable=False)
    position_x = Column(Float, nullable=False)
    position_y = Column(Float, nullable=False)
    position_z = Column(Float, nullable=False)
    velocity_x = Column(Float, nullable=False)
    velocity_y = Column(Float, nullable=False)
    velocity_z = Column(Float, nullable=False)
    cov_xx = Column(Float, nullable=False)
    cov_xy = Column(Float, nullable=False)
    cov_xz = Column(Float, nullable=False)
    cov_yy = Column(Float, nullable=False)
    cov_yz = Column(Float, nullable=False)
    cov_zz = Column(Float, nullable=False)
    observation_count = Column(Integer, default=0)
    tracking_status = Column(String(32), nullable=False)
    source_sensors = Column(Text)  # JSON array
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RunModel", back_populates="tracks")
    
    __table_args__ = (
        Index("ix_tracks_run", "run_id"),
        Index("ix_tracks_time", "timestamp"),
        Index("ix_tracks_status", "tracking_status"),
    )


class EventModel(Base):
    """Simulation event persistence model."""
    
    __tablename__ = "events"
    
    id = Column(String(64), primary_key=True)
    run_id = Column(String(64), ForeignKey("runs.id"), nullable=False)
    event_type = Column(String(64), nullable=False)
    timestamp = Column(Float, nullable=False)
    severity = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
    source_module = Column(String(64), nullable=False)
    associated_object_id = Column(String(64), nullable=True)
    metadata = Column(Text)  # JSON serialized
    created_at = Column(DateTime, default=datetime.utcnow)
    
    run = relationship("RunModel", back_populates="events")
    
    __table_args__ = (
        Index("ix_events_run", "run_id"),
        Index("ix_events_type", "event_type"),
        Index("ix_events_time", "timestamp"),
        Index("ix_events_severity", "severity"),
    )


class SettingsModel(Base):
    """Application settings persistence model."""
    
    __tablename__ = "settings"
    
    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=False)
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)