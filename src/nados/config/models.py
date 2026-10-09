"""
Configuration models using Pydantic.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DatabaseConfig(BaseModel):
    """Database configuration."""

    path: str = "data/nados.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10


class SimulationConfig(BaseModel):
    """Simulation configuration."""

    default_seed: int = 42
    max_duration_seconds: int = 3600
    max_objects: int = 1000
    max_sensors: int = 100
    max_observations_per_run: int = 100000
    max_events_per_run: int = 10000
    default_timestep: float = 0.1
    min_timestep: float = 0.01
    max_timestep: float = 1.0

    @field_validator("default_timestep", "min_timestep", "max_timestep")
    @classmethod
    def validate_timestep(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Timestep must be positive")
        return v


class VisualizationConfig(BaseModel):
    """Visualization configuration."""

    enable_2d: bool = True
    enable_3d: bool = False
    update_frequency_hz: int = 30
    trail_length: int = 100
    show_uncertainty: bool = True
    coordinate_system: str = "ENU"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    directory: str = "logs"
    max_bytes: int = 10485760
    backup_count: int = 5
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


class ReportsConfig(BaseModel):
    """Reports configuration."""

    output_directory: str = "reports"
    formats: list[str] = Field(default_factory=lambda: ["json", "csv"])
    include_metadata: bool = True
    compress: bool = False


class ScenariosConfig(BaseModel):
    """Scenarios configuration."""

    directory: str = "scenarios"
    schema_version: str = "v1"
    validate_on_load: bool = True


class SafetyConfig(BaseModel):
    """Safety configuration."""

    enforce_simulation_boundary: bool = True
    label_all_data_as_simulated: bool = True
    prohibit_network_access: bool = True
    validate_imports: bool = True


class AppConfig(BaseModel):
    """Main application configuration."""

    model_config = ConfigDict(extra="ignore")

    name: str = "NADOS Dv1.0"
    version: str = "1.0.0"
    debug: bool = False
    language: str = "ar"
    theme: str = "dark"

    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    visualization: VisualizationConfig = Field(default_factory=VisualizationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    scenarios: ScenariosConfig = Field(default_factory=ScenariosConfig)
    safety: SafetyConfig = Field(default_factory=SafetyConfig)
    plugins: dict[str, Any] = Field(default_factory=dict)
