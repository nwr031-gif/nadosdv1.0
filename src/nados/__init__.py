"""NADOS Dv1.0 - Main package initialization."""

__version__ = "1.0.0"
__author__ = "NADOS Development Team"
__description__ = "Integrated Air Defense Research & Simulation Environment"

# Ensure proper imports
from .config import get_config, load_config
from .domain import (
    SensorDefinition,
    SensorObservation,
    SimulationEvent,
    SimulationRun,
    SimulationScenario,
    TrackEstimate,
    VirtualObject,
)
from .orchestration import NADOSApplication, create_application

__all__ = [
    "get_config",
    "load_config",
    "SimulationScenario",
    "VirtualObject",
    "SensorDefinition",
    "SensorObservation",
    "TrackEstimate",
    "SimulationEvent",
    "SimulationRun",
    "create_application",
    "NADOSApplication",
]
