"""
Scenario and related domain models.
"""

from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import Matrix3x3, SimulationBaseModel, Vector3D, validate_positive


class CoordinateSystem(str, Enum):
    """Supported coordinate systems."""

    ENU = "ENU"  # East-North-Up (local tangent plane)
    ECEF = "ECEF"  # Earth-Centered Earth-Fixed
    LLA = "LLA"  # Latitude-Longitude-Altitude


class ObjectType(str, Enum):
    """Types of virtual objects in simulation."""

    GENERIC = "generic"
    VEHICLE = "vehicle"
    PROJECTILE = "projectile"
    TARGET = "target"
    DECOY = "decoy"
    UNKNOWN = "unknown"


class SensorType(str, Enum):
    """Types of simulated sensors."""

    RADAR = "radar"
    LIDAR = "lidar"
    OPTICAL = "optical"
    IRST = "irst"  # Infrared Search and Track
    ACOUSTIC = "acoustic"
    GENERIC = "generic"


class EnvironmentalConditions(SimulationBaseModel):
    """Environmental conditions for the simulation."""

    wind_velocity: Vector3D = Field(default_factory=Vector3D)
    temperature_celsius: float = 20.0
    pressure_hpa: float = 1013.25
    humidity_percent: float = 50.0
    visibility_km: float = 10.0
    precipitation: str = "none"
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisualizationSettings(SimulationBaseModel):
    """Visualization settings for the scenario."""

    show_trails: bool = True
    trail_length: int = 100
    show_uncertainty_ellipses: bool = True
    show_sensor_fov: bool = True
    show_coordinates: bool = True
    map_center: Vector3D = Field(default_factory=Vector3D)
    map_range_km: float = 100.0
    background_color: str = "#1a1a2e"
    object_colors: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VirtualObject(SimulationBaseModel):
    """Virtual object in the simulation."""

    object_id: str
    object_type: ObjectType = ObjectType.GENERIC
    initial_position: Vector3D = Field(default_factory=Vector3D)
    initial_velocity: Vector3D = Field(default_factory=Vector3D)
    initial_acceleration: Vector3D = Field(default_factory=Vector3D)
    dimensions: Vector3D = Field(default_factory=lambda: Vector3D(x=1.0, y=1.0, z=1.0))
    appearance: dict[str, Any] = Field(default_factory=dict)
    simulation_enabled: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("object_id")
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("object_id cannot be empty")
        return v.strip()


class SensorDefinition(SimulationBaseModel):
    """Definition of a simulated sensor."""

    sensor_id: str
    sensor_type: SensorType = SensorType.GENERIC
    simulated_position: Vector3D = Field(default_factory=Vector3D)
    sampling_interval: float = 1.0
    measurement_noise: Matrix3x3 = Field(default_factory=Matrix3x3.identity)
    availability_schedule: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("sensor_id")
    @classmethod
    def validate_sensor_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("sensor_id cannot be empty")
        return v.strip()

    @field_validator("sampling_interval")
    @classmethod
    def validate_sampling_interval(cls, v: float) -> float:
        return validate_positive(v, "sampling_interval")


class SimulationScenario(SimulationBaseModel):
    """Complete simulation scenario definition."""

    scenario_id: str
    schema_version: str = "v1"
    name: str
    description: str = ""
    duration_seconds: float = 60.0
    timestep_seconds: float = 0.1
    random_seed: int = 42
    coordinate_system: CoordinateSystem = CoordinateSystem.ENU
    simulated_sensors: list[SensorDefinition] = Field(default_factory=list)
    virtual_objects: list[VirtualObject] = Field(default_factory=list)
    environmental_conditions: EnvironmentalConditions = Field(default_factory=EnvironmentalConditions)
    visualization_settings: VisualizationSettings = Field(default_factory=VisualizationSettings)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("scenario_id")
    @classmethod
    def validate_scenario_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("scenario_id cannot be empty")
        return v.strip()

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        supported = ["v1"]
        if v not in supported:
            raise ValueError(f"Unsupported schema version: {v}. Supported: {supported}")
        return v

    @field_validator("duration_seconds")
    @classmethod
    def validate_duration(cls, v: float) -> float:
        return validate_positive(v, "duration_seconds")

    @field_validator("timestep_seconds")
    @classmethod
    def validate_timestep(cls, v: float) -> float:
        return validate_positive(v, "timestep_seconds")

    @field_validator("random_seed")
    @classmethod
    def validate_seed(cls, v: int) -> int:
        if v < 0:
            raise ValueError("random_seed must be non-negative")
        return v

    def get_object(self, object_id: str) -> VirtualObject | None:
        """Get virtual object by ID."""
        for obj in self.virtual_objects:
            if obj.object_id == object_id:
                return obj
        return None

    def get_sensor(self, sensor_id: str) -> SensorDefinition | None:
        """Get sensor by ID."""
        for sensor in self.simulated_sensors:
            if sensor.sensor_id == sensor_id:
                return sensor
        return None

    def validate_references(self) -> list[str]:
        """Validate cross-references and return list of errors."""
        errors = []
        object_ids = {obj.object_id for obj in self.virtual_objects}
        sensor_ids = {sensor.sensor_id for sensor in self.simulated_sensors}

        if len(object_ids) != len(self.virtual_objects):
            errors.append("Duplicate object_id found in virtual_objects")

        if len(sensor_ids) != len(self.simulated_sensors):
            errors.append("Duplicate sensor_id found in simulated_sensors")

        return errors
