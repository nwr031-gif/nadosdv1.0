"""
Repository classes for data access.
"""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import Session

from nados.domain import (
    SimulationScenario, VirtualObject, SensorDefinition,
    SensorObservation, ValidityStatus, TrackEstimate, TrackingStatus,
    SimulationEvent, EventType, EventSeverity, SimulationRun, RunStatus,
)
from nados.domain.base import Vector3D, Matrix3x3
from .models import (
    ScenarioModel, RunModel, ObservationModel, TrackModel, EventModel, SettingsModel
)
from .database import get_database


class ScenarioRepository:
    """Repository for scenario persistence."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def save(self, scenario: SimulationScenario) -> None:
        """Save or update a scenario."""
        with self.db.session() as session:
            existing = session.get(ScenarioModel, scenario.scenario_id)
            
            scenario_data = scenario.model_dump_json()
            
            if existing:
                existing.schema_version = scenario.schema_version
                existing.name = scenario.name
                existing.description = scenario.description
                existing.duration_seconds = scenario.duration_seconds
                existing.timestep_seconds = scenario.timestep_seconds
                existing.random_seed = scenario.random_seed
                existing.coordinate_system = scenario.coordinate_system.value
                existing.scenario_data = scenario_data
                existing.updated_at = datetime.utcnow()
            else:
                model = ScenarioModel(
                    id=scenario.scenario_id,
                    schema_version=scenario.schema_version,
                    name=scenario.name,
                    description=scenario.description,
                    duration_seconds=scenario.duration_seconds,
                    timestep_seconds=scenario.timestep_seconds,
                    random_seed=scenario.random_seed,
                    coordinate_system=scenario.coordinate_system,
                    scenario_data=scenario_data,
                )
                session.add(model)
    
    def get(self, scenario_id: str) -> Optional[SimulationScenario]:
        """Get a scenario by ID."""
        with self.db.session() as session:
            model = session.get(ScenarioModel, scenario_id)
            if not model:
                return None
            return SimulationScenario.model_validate_json(model.scenario_data)
    
    def list_all(self) -> List[SimulationScenario]:
        """List all scenarios."""
        with self.db.session() as session:
            models = session.execute(select(ScenarioModel).order_by(ScenarioModel.created_at.desc())).scalars().all()
            return [SimulationScenario.model_validate_json(m.scenario_data) for m in models]
    
    def delete(self, scenario_id: str) -> bool:
        """Delete a scenario."""
        with self.db.session() as session:
            model = session.get(ScenarioModel, scenario_id)
            if model:
                session.delete(model)
                return True
            return False


class RunRepository:
    """Repository for simulation run persistence."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def save(self, run: SimulationRun) -> None:
        """Save or update a run."""
        with self.db.session() as session:
            existing = session.get(RunModel, run.run_id)
            
            summary_json = json.dumps(run.summary_metrics) if run.summary_metrics else "{}"
            
            if existing:
                existing.scenario_id = run.scenario_id
                existing.completed_at = run.completed_at
                existing.random_seed = run.random_seed
                existing.application_version = run.application_version
                existing.configuration_hash = run.configuration_hash
                existing.status = run.status
                existing.summary_metrics = summary_json
                existing.updated_at = datetime.utcnow()
            else:
                model = RunModel(
                    id=run.run_id,
                    scenario_id=run.scenario_id,
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    random_seed=run.random_seed,
                    application_version=run.application_version,
                    configuration_hash=run.configuration_hash,
                    status=run.status,
                    summary_metrics=summary_json,
                )
                session.add(model)
    
    def get(self, run_id: str) -> Optional[SimulationRun]:
        """Get a run by ID."""
        with self.db.session() as session:
            model = session.get(RunModel, run_id)
            if not model:
                return None
            
            summary = json.loads(model.summary_metrics) if model.summary_metrics else {}
            
            return SimulationRun(
                run_id=model.id,
                scenario_id=model.scenario_id,
                started_at=model.started_at,
                completed_at=model.completed_at,
                random_seed=model.random_seed,
                application_version=model.application_version,
                configuration_hash=model.configuration_hash or "",
                status=RunStatus(model.status),
                summary_metrics=summary,
            )
    
    def list_by_scenario(self, scenario_id: str) -> List[SimulationRun]:
        """List runs for a scenario."""
        with self.db.session() as session:
            models = session.execute(
                select(RunModel)
                .where(RunModel.scenario_id == scenario_id)
                .order_by(desc(RunModel.started_at))
            ).scalars().all()
            
            return [
                SimulationRun(
                    run_id=m.id,
                    scenario_id=m.scenario_id,
                    started_at=m.started_at,
                    completed_at=m.completed_at,
                    random_seed=m.random_seed,
                    application_version=m.application_version,
                    configuration_hash=m.configuration_hash or "",
                    status=RunStatus(m.status),
                    summary_metrics=json.loads(m.summary_metrics) if m.summary_metrics else {},
                )
                for m in models
            ]
    
    def get_latest(self, scenario_id: str) -> Optional[SimulationRun]:
        """Get the latest run for a scenario."""
        runs = self.list_by_scenario(scenario_id)
        return runs[0] if runs else None


class ObservationRepository:
    """Repository for observation persistence."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def save_batch(self, run_id: str, observations: List[SensorObservation]) -> None:
        """Save multiple observations efficiently."""
        with self.db.session() as session:
            models = []
            for obs in observations:
                cov = obs.measurement_uncertainty.data
                model = ObservationModel(
                    id=obs.observation_id,
                    run_id=run_id,
                    sensor_id=obs.sensor_id,
                    timestamp=obs.timestamp,
                    position_x=obs.measured_position.x,
                    position_y=obs.measured_position.y,
                    position_z=obs.measured_position.z,
                    uncertainty_xx=cov[0][0],
                    uncertainty_xy=cov[0][1],
                    uncertainty_xz=cov[0][2],
                    uncertainty_yy=cov[1][1],
                    uncertainty_yz=cov[1][2],
                    uncertainty_zz=cov[2][2],
                    validity_status=obs.validity_status,
                    scenario_id=obs.scenario_id,
                )
                models.append(model)
            
            session.bulk_save_objects(models)
    
    def get_by_run(self, run_id: str, limit: Optional[int] = None) -> List[SensorObservation]:
        """Get observations for a run."""
        with self.db.session() as session:
            query = select(ObservationModel).where(ObservationModel.run_id == run_id).order_by(ObservationModel.timestamp)
            if limit:
                query = query.limit(limit)
            
            models = session.execute(query).scalars().all()
            return [self._model_to_obs(m) for m in models]
    
    def get_by_sensor(self, run_id: str, sensor_id: str) -> List[SensorObservation]:
        """Get observations for a specific sensor in a run."""
        with self.db.session() as session:
            models = session.execute(
                select(ObservationModel)
                .where(and_(ObservationModel.run_id == run_id, ObservationModel.sensor_id == sensor_id))
                .order_by(ObservationModel.timestamp)
            ).scalars().all()
            
            return [self._model_to_obs(m) for m in models]
    
    def count_by_run(self, run_id: str) -> int:
        """Count observations for a run."""
        with self.db.session() as session:
            return session.execute(
                select(func.count(ObservationModel.id)).where(ObservationModel.run_id == run_id)
            ).scalar() or 0
    
    def _model_to_obs(self, model: ObservationModel) -> SensorObservation:
        return SensorObservation(
            observation_id=model.id,
            sensor_id=model.sensor_id,
            timestamp=model.timestamp,
            measured_position=Vector3D(x=model.position_x, y=model.position_y, z=model.position_z),
            measurement_uncertainty=Matrix3x3(data=[
                [model.uncertainty_xx, model.uncertainty_xy, model.uncertainty_xz],
                [model.uncertainty_xy, model.uncertainty_yy, model.uncertainty_yz],
                [model.uncertainty_xz, model.uncertainty_yz, model.uncertainty_zz],
            ]),
            validity_status=ValidityStatus(model.validity_status),
            scenario_id=model.scenario_id,
        )


class TrackRepository:
    """Repository for track persistence."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def save_batch(self, run_id: str, tracks: List[TrackEstimate]) -> None:
        """Save multiple tracks efficiently."""
        with self.db.session() as session:
            models = []
            for track in tracks:
                cov = track.covariance_or_uncertainty.data
                model = TrackModel(
                    id=f"{run_id}_{track.track_id}_{track.timestamp:.3f}",
                    run_id=run_id,
                    timestamp=track.timestamp,
                    position_x=track.estimated_position.x,
                    position_y=track.estimated_position.y,
                    position_z=track.estimated_position.z,
                    velocity_x=track.estimated_velocity.x,
                    velocity_y=track.estimated_velocity.y,
                    velocity_z=track.estimated_velocity.z,
                    cov_xx=cov[0][0],
                    cov_xy=cov[0][1],
                    cov_xz=cov[0][2],
                    cov_yy=cov[1][1],
                    cov_yz=cov[1][2],
                    cov_zz=cov[2][2],
                    observation_count=track.observation_count,
                    tracking_status=track.tracking_status,
                    source_sensors=json.dumps(track.source_sensor_ids),
                )
                models.append(model)
            
            session.bulk_save_objects(models)
    
    def get_by_run(self, run_id: str) -> List[TrackEstimate]:
        """Get tracks for a run."""
        with self.db.session() as session:
            models = session.execute(
                select(TrackModel)
                .where(TrackModel.run_id == run_id)
                .order_by(TrackModel.timestamp)
            ).scalars().all()
            
            return [self._model_to_track(m) for m in models]
    
    def _model_to_track(self, model: TrackModel) -> TrackEstimate:
        # ID format: run_001_track_0_0.000 -> extract track_0
        parts = model.id.split("_")
        if len(parts) >= 4:
            track_id = f"{parts[2]}_{parts[3]}"
        elif len(parts) >= 2:
            track_id = parts[1]
        else:
            track_id = model.id
        
        return TrackEstimate(
            track_id=track_id,
            timestamp=model.timestamp,
            estimated_position=Vector3D(x=model.position_x, y=model.position_y, z=model.position_z),
            estimated_velocity=Vector3D(x=model.velocity_x, y=model.velocity_y, z=model.velocity_z),
            covariance_or_uncertainty=Matrix3x3(data=[
                [model.cov_xx, model.cov_xy, model.cov_xz],
                [model.cov_xy, model.cov_yy, model.cov_yz],
                [model.cov_xz, model.cov_yz, model.cov_zz],
            ]),
            observation_count=model.observation_count,
            tracking_status=TrackingStatus(model.tracking_status),
            source_sensor_ids=json.loads(model.source_sensors) if model.source_sensors else [],
        )


class EventRepository:
    """Repository for event persistence."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def save_batch(self, run_id: str, events: List[SimulationEvent]) -> None:
        """Save multiple events efficiently."""
        with self.db.session() as session:
            models = []
            for event in events:
                model = EventModel(
                    id=event.event_id,
                    run_id=run_id,
                    event_type=event.event_type,
                    timestamp=event.timestamp,
                    severity=event.severity,
                    message=event.message,
                    source_module=event.source_module,
                    associated_object_id=event.associated_object_id,
                    metadata=json.dumps(event.metadata) if event.metadata else "{}",
                )
                models.append(model)
            
            session.bulk_save_objects(models)
    
    def get_by_run(self, run_id: str, limit: Optional[int] = None) -> List[SimulationEvent]:
        """Get events for a run."""
        with self.db.session() as session:
            query = select(EventModel).where(EventModel.run_id == run_id).order_by(EventModel.timestamp)
            if limit:
                query = query.limit(limit)
            
            models = session.execute(query).scalars().all()
            return [self._model_to_event(m) for m in models]
    
    def _model_to_event(self, model: EventModel) -> SimulationEvent:
        return SimulationEvent(
            event_id=model.id,
            event_type=EventType(model.event_type),
            timestamp=model.timestamp,
            severity=EventSeverity(model.severity),
            message=model.message,
            source_module=model.source_module,
            associated_object_id=model.associated_object_id,
            metadata=json.loads(model.metadata) if model.metadata else {},
        )


class SettingsRepository:
    """Repository for application settings."""
    
    def __init__(self, db: Optional[Any] = None) -> None:
        self.db = db or get_database()
    
    def set(self, key: str, value: Any, description: str = "") -> None:
        """Set a setting value."""
        with self.db.session() as session:
            existing = session.get(SettingsModel, key)
            if existing:
                existing.value = json.dumps(value)
                existing.description = description
                existing.updated_at = datetime.utcnow()
            else:
                model = SettingsModel(key=key, value=json.dumps(value), description=description)
                session.add(model)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        with self.db.session() as session:
            model = session.get(SettingsModel, key)
            if model:
                return json.loads(model.value)
            return default
    
    def delete(self, key: str) -> bool:
        """Delete a setting."""
        with self.db.session() as session:
            model = session.get(SettingsModel, key)
            if model:
                session.delete(model)
                return True
            return False
    
    def list_all(self) -> Dict[str, Any]:
        """List all settings."""
        with self.db.session() as session:
            models = session.execute(select(SettingsModel)).scalars().all()
            return {m.key: json.loads(m.value) for m in models}