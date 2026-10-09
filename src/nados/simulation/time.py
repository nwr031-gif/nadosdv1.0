"""
Simulation time management.
"""

import contextlib
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class SimulationState(str, Enum):
    """Simulation execution state."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class SimulationTime:
    """Simulation time representation."""

    current_time: float = 0.0  # Simulation time in seconds
    timestep: float = 0.1
    duration: float = 60.0
    speed_multiplier: float = 1.0
    wall_clock_start: float | None = None
    paused_duration: float = 0.0
    pause_start: float | None = None

    @property
    def progress(self) -> float:
        """Get simulation progress as fraction (0.0 to 1.0)."""
        if self.duration <= 0:
            return 1.0
        return min(1.0, self.current_time / self.duration)

    @property
    def is_complete(self) -> bool:
        """Check if simulation has reached duration."""
        return self.current_time >= self.duration

    @property
    def steps_remaining(self) -> int:
        """Get number of simulation steps remaining."""
        if self.timestep <= 0:
            return 0
        return max(0, int((self.duration - self.current_time) / self.timestep))


class SimulationClock:
    """Manages simulation time and execution control."""

    def __init__(
        self,
        duration: float = 60.0,
        timestep: float = 0.1,
        speed_multiplier: float = 1.0,
    ) -> None:
        self._time = SimulationTime(
            duration=duration,
            timestep=timestep,
            speed_multiplier=speed_multiplier,
        )
        self._state = SimulationState.IDLE
        self._callbacks: dict[SimulationState, list[Callable[[], None]]] = {state: [] for state in SimulationState}
        self._step_callbacks: list[Callable[[float], None]] = []

    @property
    def time(self) -> SimulationTime:
        return self._time

    @property
    def state(self) -> SimulationState:
        return self._state

    @property
    def current_time(self) -> float:
        return self._time.current_time

    def start(self) -> None:
        """Start or resume simulation."""
        if self._state == SimulationState.RUNNING:
            return

        now = time.perf_counter()

        if self._state == SimulationState.PAUSED and self._time.pause_start is not None:
            self._time.paused_duration += now - self._time.pause_start
            self._time.pause_start = None
        else:
            self._time.wall_clock_start = now
            self._time.paused_duration = 0.0

        self._set_state(SimulationState.RUNNING)

    def pause(self) -> None:
        """Pause simulation."""
        if self._state != SimulationState.RUNNING:
            return

        self._time.pause_start = time.perf_counter()
        self._set_state(SimulationState.PAUSED)

    def stop(self) -> None:
        """Stop simulation."""
        self._set_state(SimulationState.STOPPED)
        self._time.wall_clock_start = None
        self._time.pause_start = None

    def reset(self) -> None:
        """Reset simulation to initial state."""
        self._state = SimulationState.IDLE
        self._time.current_time = 0.0
        self._time.wall_clock_start = None
        self._time.paused_duration = 0.0
        self._time.pause_start = None

    def step(self) -> bool:
        """Advance simulation by one timestep. Returns True if simulation continues."""
        if self._state != SimulationState.RUNNING:
            return False

        if self._time.is_complete:
            self._set_state(SimulationState.COMPLETED)
            return False

        # Execute step callbacks
        for callback in self._step_callbacks:
            try:
                callback(self._time.current_time)
            except Exception:
                self._set_state(SimulationState.ERROR)
                raise

        # Advance time
        self._time.current_time += self._time.timestep

        return True

    def set_speed(self, multiplier: float) -> None:
        """Set simulation speed multiplier."""
        if multiplier <= 0:
            raise ValueError("Speed multiplier must be positive")
        self._time.speed_multiplier = multiplier

    def set_timestep(self, timestep: float) -> None:
        """Set simulation timestep."""
        if timestep <= 0:
            raise ValueError("Timestep must be positive")
        self._time.timestep = timestep

    def register_state_callback(self, state: SimulationState, callback: Callable[[], None]) -> None:
        """Register callback for state changes."""
        self._callbacks[state].append(callback)

    def register_step_callback(self, callback: Callable[[float], None]) -> None:
        """Register callback for each simulation step."""
        self._step_callbacks.append(callback)

    def _set_state(self, new_state: SimulationState) -> None:
        old_state = self._state
        self._state = new_state

        # Execute state change callbacks (errors in callbacks must not affect state)
        for callback in self._callbacks[new_state]:
            with contextlib.suppress(Exception):
                callback()

        # Emit event
        from nados.observability import get_logger

        logger = get_logger("simulation.clock")
        logger.info(f"Simulation state changed: {old_state.value} -> {new_state.value}")


def create_clock_from_scenario(scenario) -> SimulationClock:
    """Create a SimulationClock from a scenario."""
    return SimulationClock(
        duration=scenario.duration_seconds,
        timestep=scenario.timestep_seconds,
    )
