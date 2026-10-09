"""
Simulation engine core implementation.
"""

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from nados.domain import (
    SimulationEvent, EventType, EventSeverity,
    VirtualObject, SensorDefinition, SensorObservation, ValidityStatus,
    TrackEstimate, TrackingStatus,
    SimulationScenario,
)
from nados.domain.base import Vector3D
from nados.observability import get_logger, get_metrics_collector
from .time import SimulationClock, SimulationState, SimulationTime, create_clock_from_scenario
from .motion import MotionModel, KinematicState, create_motion_model


@dataclass
class SimulationStepResult:
    """Result of a single simulation step."""
    success: bool
    current_time: float
    events: List[SimulationEvent] = field(default_factory=list)
    observations: List[SensorObservation] = field(default_factory=list)
    tracks: List[TrackEstimate] = field(default_factory=list)
    error: Optional[str] = None


class ObjectSimulator:
    """Simulates a single virtual object."""
    
    def __init__(self, virtual_object: VirtualObject, motion_model: MotionModel) -> None:
        self.virtual_object = virtual_object
        self.motion_model = motion_model
        self.state = KinematicState(
            position=virtual_object.initial_position,
            velocity=virtual_object.initial_velocity,
            acceleration=virtual_object.initial_acceleration,
            timestamp=0.0,
        )
        self._trajectory: List[KinematicState] = [self.state]
        self._enabled = virtual_object.simulation_enabled
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
    
    def step(self, dt: float) -> KinematicState:
        """Advance object state by dt."""
        if not self._enabled:
            return self.state
        
        self.state = self.motion_model.predict(self.state, dt)
        self._trajectory.append(self.state)
        return self.state
    
    def get_trajectory(self) -> List[KinematicState]:
        return self._trajectory.copy()
    
    def get_current_position(self) -> Vector3D:
        return self.state.position
    
    def get_current_velocity(self) -> Vector3D:
        return self.state.velocity


class SensorSimulator:
    """Simulates a single sensor generating observations."""
    
    def __init__(
        self,
        sensor_def: SensorDefinition,
        random_seed: int,
        object_simulators: Dict[str, ObjectSimulator],
        scenario_id: str = "",
    ) -> None:
        self.sensor_def = sensor_def
        self.object_simulators = object_simulators
        self.scenario_id = scenario_id
        self._rng = np.random.default_rng(random_seed + hash(sensor_def.sensor_id) % 2**32)
        self._next_sample_time = 0.0
        self._available = True
        self._health = 1.0
    
    @property
    def sensor_id(self) -> str:
        return self.sensor_def.sensor_id
    
    @property
    def is_available(self) -> bool:
        return self._available
    
    def set_availability(self, available: bool) -> None:
        self._available = available
    
    def step(self, current_time: float) -> List[SensorObservation]:
        """Generate observations at current time."""
        observations = []
        
        if not self._available:
            return observations
        
        # Check if it's time to sample
        if current_time < self._next_sample_time - 1e-9:
            return observations
        
        # Schedule next sample
        self._next_sample_time = current_time + self.sensor_def.sampling_interval
        
        # Generate observations for each object
        for obj_id, obj_sim in self.object_simulators.items():
            if not obj_sim.enabled:
                continue
            
            # Check range (simplified)
            true_pos = obj_sim.get_current_position()
            sensor_pos = self.sensor_def.simulated_position
            dx = true_pos.x - sensor_pos.x
            dy = true_pos.y - sensor_pos.y
            dz = true_pos.z - sensor_pos.z
            range_km = math.sqrt(dx*dx + dy*dy + dz*dz) / 1000.0
            
            # Simplified range check (max 200 km)
            if range_km > 200:
                obs = SensorObservation(
                    observation_id=f"{self.sensor_def.sensor_id}_{obj_id}_{current_time:.3f}",
                    sensor_id=self.sensor_def.sensor_id,
                    timestamp=current_time,
                    measured_position=Vector3D(),
                    measurement_uncertainty=self.sensor_def.measurement_noise,
                    validity_status=ValidityStatus.OUT_OF_RANGE,
                    scenario_id=self.scenario_id,
                )
                observations.append(obs)
                continue
            
            # Add measurement noise
            noise_cov = self.sensor_def.measurement_noise.to_array()
            noise = self._rng.multivariate_normal([0, 0, 0], noise_cov)
            
            measured_pos = Vector3D(
                x=true_pos.x + noise[0],
                y=true_pos.y + noise[1],
                z=true_pos.z + noise[2],
            )
            
            # Simulate dropouts
            dropout_prob = self.sensor_def.metadata.get("dropout_probability", 0.0)
            if self._rng.random() < dropout_prob:
                obs = SensorObservation(
                    observation_id=f"{self.sensor_def.sensor_id}_{obj_id}_{current_time:.3f}",
                    sensor_id=self.sensor_def.sensor_id,
                    timestamp=current_time,
                    measured_position=Vector3D(),
                    measurement_uncertainty=self.sensor_def.measurement_noise,
                    validity_status=ValidityStatus.MISSING,
                    scenario_id=self.scenario_id,
                )
                observations.append(obs)
                continue
            
            # Valid observation
            obs = SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{obj_id}_{current_time:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=current_time,
                measured_position=measured_pos,
                measurement_uncertainty=self.sensor_def.measurement_noise,
                validity_status=ValidityStatus.VALID,
                scenario_id=self.scenario_id,
            )
            observations.append(obs)
        
        return observations


class SimulationEngine:
    """Main simulation engine orchestrating objects, sensors, and tracking."""
    
    def __init__(self, scenario: SimulationScenario, random_seed: Optional[int] = None) -> None:
        self.scenario = scenario
        self.random_seed = random_seed or scenario.random_seed
        self._rng = np.random.default_rng(self.random_seed)
        
        self.clock = create_clock_from_scenario(scenario)
        self._state = SimulationState.IDLE
        
        # Object simulators
        self._object_simulators: Dict[str, ObjectSimulator] = {}
        self._initialize_objects()
        
        # Sensor simulators
        self._sensor_simulators: Dict[str, SensorSimulator] = {}
        self._initialize_sensors()
        
        # Event system
        self._event_handlers: List[Callable[[SimulationEvent], None]] = []
        self._events: List[SimulationEvent] = []
        
        # Metrics
        self.metrics = get_metrics_collector()
        
        # Thread safety
        self._lock = threading.RLock()
        self._worker_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Register clock callbacks
        self.clock.register_step_callback(self._on_simulation_step)
        for state in SimulationState:
            self.clock.register_state_callback(state, lambda s=state: self._on_state_change(s))
        
        self.logger = get_logger("simulation.engine")
    
    def _initialize_objects(self) -> None:
        """Initialize object simulators from scenario."""
        for vobj in self.scenario.virtual_objects:
            if not vobj.simulation_enabled:
                continue
            
            # Determine motion model from metadata
            model_type = vobj.metadata.get("motion_model", "constant_velocity")
            motion_model = create_motion_model(model_type)
            
            self._object_simulators[vobj.object_id] = ObjectSimulator(vobj, motion_model)
    
    def _initialize_sensors(self) -> None:
        """Initialize sensor simulators from scenario."""
        for sensor_def in self.scenario.simulated_sensors:
            self._sensor_simulators[sensor_def.sensor_id] = SensorSimulator(
                sensor_def, self.random_seed, self._object_simulators, self.scenario.scenario_id
            )
    
    def _on_simulation_step(self, sim_time: float) -> None:
        """Called on each simulation step."""
        with self._lock:
            if self._state != SimulationState.RUNNING:
                return
            
            # Step all objects
            for obj_sim in self._object_simulators.values():
                obj_sim.step(self.clock.time.timestep)
            
            # Generate observations
            all_observations = []
            for sensor_sim in self._sensor_simulators.values():
                observations = sensor_sim.step(sim_time)
                for obs in observations:
                    all_observations.extend(observations)
            
            # Emit observation events
            for obs in all_observations:
                event = SimulationEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=EventType.OBSERVATION_GENERATED,
                    timestamp=sim_time,
                    severity=EventSeverity.INFO,
                    message=f"Observation from {obs.sensor_id}",
                    source_module="simulation.engine",
                    associated_object_id=obs.sensor_id,
                    metadata={"observation_id": obs.observation_id},
                )
                self._emit_event(event)
            
            # Update metrics
            self.metrics.increment_counter("simulation.steps")
            self.metrics.increment_counter("simulation.observations", len(all_observations))
            self.metrics.set_gauge("simulation.time", sim_time)
            self.metrics.set_gauge("simulation.progress", self.clock.time.progress)
    
    def _on_state_change(self, new_state: SimulationState) -> None:
        """Handle simulation state changes."""
        self._state = new_state
        self.logger.info(f"Engine state changed to: {new_state.value}")
        
        event = SimulationEvent(
            event_id=str(uuid.uuid4()),
            event_type=EventType.SYSTEM_EVENT,
            timestamp=self.clock.current_time,
            severity=EventSeverity.INFO,
            message=f"Simulation state: {new_state.value}",
            source_module="simulation.engine",
        )
        self._emit_event(event)
    
    def _emit_event(self, event: SimulationEvent) -> None:
        """Emit event to handlers."""
        self._events.append(event)
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Event handler error: {e}")
    
    def register_event_handler(self, handler: Callable[[SimulationEvent], None]) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)
    
    def get_events(self, since_time: float = 0.0) -> List[SimulationEvent]:
        """Get events since a given time."""
        return [e for e in self._events if e.timestamp >= since_time]
    
    def start(self) -> None:
        """Start the simulation."""
        with self._lock:
            if self._state == SimulationState.RUNNING:
                return
            
            self.clock.start()
            self._state = SimulationState.RUNNING
            self._stop_event.clear()
            
            # Emit start event
            event = SimulationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SCENARIO_STARTED,
                timestamp=self.clock.current_time,
                severity=EventSeverity.INFO,
                message="Simulation started",
                source_module="simulation.engine",
            )
            self._emit_event(event)
            
            self.metrics.increment_counter("simulation.runs_started")
    
    def pause(self) -> None:
        """Pause the simulation."""
        with self._lock:
            if self._state != SimulationState.RUNNING:
                return
            
            self.clock.pause()
            self._state = SimulationState.PAUSED
            
            event = SimulationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SCENARIO_PAUSED,
                timestamp=self.clock.current_time,
                severity=EventSeverity.INFO,
                message="Simulation paused",
                source_module="simulation.engine",
            )
            self._emit_event(event)
    
    def resume(self) -> None:
        """Resume the simulation."""
        with self._lock:
            if self._state != SimulationState.PAUSED:
                return
            
            self.clock.start()  # This resumes
            self._state = SimulationState.RUNNING
            
            event = SimulationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SCENARIO_RESUMED,
                timestamp=self.clock.current_time,
                severity=EventSeverity.INFO,
                message="Simulation resumed",
                source_module="simulation.engine",
            )
            self._emit_event(event)
    
    def stop(self) -> None:
        """Stop the simulation."""
        with self._lock:
            if self._state in (SimulationState.STOPPED, SimulationState.COMPLETED, SimulationState.IDLE):
                return
            
            self.clock.stop()
            self._state = SimulationState.STOPPED
            self._stop_event.set()
            
            event = SimulationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SCENARIO_STOPPED,
                timestamp=self.clock.current_time,
                severity=EventSeverity.INFO,
                message="Simulation stopped",
                source_module="simulation.engine",
            )
            self._emit_event(event)
    
    def reset(self) -> None:
        """Reset the simulation to initial state."""
        with self._lock:
            self.clock.reset()
            self._state = SimulationState.IDLE
            self._events.clear()
            self._stop_event.clear()
            
            # Reset objects
            for obj_sim in self._object_simulators.values():
                obj_sim.state = KinematicState(
                    position=obj_sim.virtual_object.initial_position,
                    velocity=obj_sim.virtual_object.initial_velocity,
                    acceleration=obj_sim.virtual_object.initial_acceleration,
                    timestamp=0.0,
                )
                obj_sim._trajectory = [obj_sim.state]
            
            # Reset sensors
            for sensor_sim in self._sensor_simulators.values():
                sensor_sim._next_sample_time = 0.0
            
            event = SimulationEvent(
                event_id=str(uuid.uuid4()),
                event_type=EventType.SCENARIO_RESET,
                timestamp=0.0,
                severity=EventSeverity.INFO,
                message="Simulation reset",
                source_module="simulation.engine",
            )
            self._emit_event(event)
    
    def step(self) -> SimulationStepResult:
        """Execute a single simulation step."""
        with self._lock:
            if self._state != SimulationState.RUNNING:
                return SimulationStepResult(
                    success=False,
                    current_time=self.clock.current_time,
                    error="Simulation not running",
                )
            
            try:
                continued = self.clock.step()
                
                if not continued:
                    self._state = SimulationState.COMPLETED
                    event = SimulationEvent(
                        event_id=str(uuid.uuid4()),
                        event_type=EventType.SCENARIO_COMPLETED,
                        timestamp=self.clock.current_time,
                        severity=EventSeverity.INFO,
                        message="Simulation completed",
                        source_module="simulation.engine",
                    )
                    self._emit_event(event)
                
                return SimulationStepResult(
                    success=True,
                    current_time=self.clock.current_time,
                    events=self.get_events(self.clock.current_time - self.clock.time.timestep),
                )
            except Exception as e:
                self._state = SimulationState.ERROR
                self.logger.error(f"Simulation step error: {e}")
                return SimulationStepResult(
                    success=False,
                    current_time=self.clock.current_time,
                    error=str(e),
                )
    
    def run_sync(self, max_steps: Optional[int] = None) -> SimulationStepResult:
        """Run simulation synchronously until completion or max_steps."""
        self.start()
        
        steps = 0
        while self._state == SimulationState.RUNNING:
            result = self.step()
            if not result.success:
                return result
            
            steps += 1
            if max_steps and steps >= max_steps:
                break
        
        return SimulationStepResult(
            success=self._state == SimulationState.COMPLETED,
            current_time=self.clock.current_time,
            events=self._events,
        )
    
    def get_object_position(self, object_id: str) -> Optional[Vector3D]:
        """Get current position of an object."""
        obj_sim = self._object_simulators.get(object_id)
        return obj_sim.get_current_position() if obj_sim else None
    
    def get_object_velocity(self, object_id: str) -> Optional[Vector3D]:
        """Get current velocity of an object."""
        obj_sim = self._object_simulators.get(object_id)
        return obj_sim.get_current_velocity() if obj_sim else None
    
    def get_object_trajectory(self, object_id: str) -> List[KinematicState]:
        """Get full trajectory of an object."""
        obj_sim = self._object_simulators.get(object_id)
        return obj_sim.get_trajectory() if obj_sim else []
    
    def get_sensor_observations(self, sensor_id: str) -> List[SensorObservation]:
        """Get recent observations from a sensor."""
        # This would need to be tracked by the engine
        return []
    
    @property
    def state(self) -> SimulationState:
        return self._state
    
    @property
    def current_time(self) -> float:
        return self.clock.current_time
    
    @property
    def progress(self) -> float:
        return self.clock.time.progress


import math  # For sqrt in SensorSimulator