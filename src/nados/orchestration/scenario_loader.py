"""
Scenario loading and validation.
"""

import json
from pathlib import Path

from nados.domain import SimulationScenario
from nados.observability import get_logger

logger = get_logger("orchestration.scenario_loader")


def load_scenario(file_path: str) -> SimulationScenario:
    """Load and validate a scenario from JSON file."""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Scenario file not found: {file_path}")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    # Validate and create scenario
    scenario = SimulationScenario.model_validate(data)

    # Additional validation
    errors = scenario.validate_references()
    if errors:
        raise ValueError(f"Scenario validation failed: {'; '.join(errors)}")

    logger.info(f"Loaded scenario: {scenario.name} ({scenario.scenario_id})")
    return scenario


def validate_scenario_file(file_path: str) -> list[str]:
    """Validate a scenario file and return list of errors."""
    errors = []

    try:
        path = Path(file_path)
        if not path.exists():
            errors.append(f"File not found: {file_path}")
            return errors

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        # Check required fields
        required_fields = [
            "scenario_id",
            "schema_version",
            "name",
            "duration_seconds",
            "timestep_seconds",
            "random_seed",
            "coordinate_system",
            "simulated_sensors",
            "virtual_objects",
        ]

        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        # Validate schema version
        if data.get("schema_version") not in ["v1"]:
            errors.append(f"Unsupported schema version: {data.get('schema_version')}")

        # Validate numeric values
        if data.get("duration_seconds", 0) <= 0:
            errors.append("duration_seconds must be positive")

        if data.get("timestep_seconds", 0) <= 0:
            errors.append("timestep_seconds must be positive")

        if data.get("random_seed", -1) < 0:
            errors.append("random_seed must be non-negative")

        # Validate objects
        for i, obj in enumerate(data.get("virtual_objects", [])):
            if not obj.get("object_id"):
                errors.append(f"Object {i}: missing object_id")

        # Validate sensors
        sensor_ids = set()
        for i, sensor in enumerate(data.get("simulated_sensors", [])):
            sensor_id = sensor.get("sensor_id")
            if not sensor_id:
                errors.append(f"Sensor {i}: missing sensor_id")
            elif sensor_id in sensor_ids:
                errors.append(f"Duplicate sensor_id: {sensor_id}")
            sensor_ids.add(sensor_id)

        object_ids = set()
        for i, obj in enumerate(data.get("virtual_objects", [])):
            obj_id = obj.get("object_id")
            if not obj_id:
                errors.append(f"Object {i}: missing object_id")
            elif obj_id in object_ids:
                errors.append(f"Duplicate object_id: {obj_id}")
            object_ids.add(obj_id)

    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
    except Exception as e:
        errors.append(f"Validation error: {e}")

    return errors


def create_demo_scenario(scenario_type: str = "basic") -> SimulationScenario:
    """Create a demo scenario programmatically."""

    if scenario_type == "basic":
        return _create_basic_tracking_scenario()
    elif scenario_type == "noisy":
        return _create_noisy_sensor_scenario()
    elif scenario_type == "multi_sensor":
        return _create_multi_sensor_scenario()
    else:
        raise ValueError(f"Unknown scenario type: {scenario_type}")


def _create_basic_tracking_scenario() -> SimulationScenario:
    """Create basic tracking demo scenario."""
    from nados.domain import (
        CoordinateSystem,
        EnvironmentalConditions,
        ObjectType,
        SensorDefinition,
        SensorType,
        VirtualObject,
        VisualizationSettings,
    )
    from nados.domain.base import Matrix3x3, Vector3D

    # Single object moving at constant velocity
    obj = VirtualObject(
        object_id="target_001",
        object_type=ObjectType.TARGET,
        initial_position=Vector3D(x=0, y=50000, z=10000),  # 50km North, 10km altitude
        initial_velocity=Vector3D(x=250, y=0, z=0),  # 250 m/s East
        initial_acceleration=Vector3D(),
        dimensions=Vector3D(x=10, y=10, z=5),
        simulation_enabled=True,
        metadata={"motion_model": "constant_velocity"},
    )

    # Single radar sensor
    sensor = SensorDefinition(
        sensor_id="radar_001",
        sensor_type=SensorType.RADAR,
        simulated_position=Vector3D(x=0, y=0, z=0),
        sampling_interval=1.0,
        measurement_noise=Matrix3x3.diagonal([100, 100, 50]),  # 100m horizontal, 50m vertical
        metadata={"dropout_probability": 0.0},
    )

    return SimulationScenario(
        scenario_id="basic_tracking",
        schema_version="v1",
        name="تتبع أساسي - جسم واحد بمستشعر نظيف",
        description="سيناريو توضيحي لتتبع جسم واحد باستخدام مستشعر رادار بقياسات نظيفة",
        duration_seconds=60.0,
        timestep_seconds=0.1,
        random_seed=42,
        coordinate_system=CoordinateSystem.ENU,
        simulated_sensors=[sensor],
        virtual_objects=[obj],
        environmental_conditions=EnvironmentalConditions(),
        visualization_settings=VisualizationSettings(
            map_center=Vector3D(x=0, y=50000, z=0),
            map_range_km=100,
        ),
    )


def _create_noisy_sensor_scenario() -> SimulationScenario:
    """Create noisy sensor demo scenario."""
    from nados.domain import (
        CoordinateSystem,
        EnvironmentalConditions,
        ObjectType,
        SensorDefinition,
        SensorType,
        VirtualObject,
        VisualizationSettings,
    )
    from nados.domain.base import Matrix3x3, Vector3D

    # Object with constant velocity
    obj = VirtualObject(
        object_id="target_001",
        object_type=ObjectType.TARGET,
        initial_position=Vector3D(x=0, y=30000, z=5000),
        initial_velocity=Vector3D(x=200, y=50, z=0),
        initial_acceleration=Vector3D(),
        dimensions=Vector3D(x=8, y=8, z=4),
        simulation_enabled=True,
        metadata={"motion_model": "constant_velocity"},
    )

    # Radar with significant noise
    sensor = SensorDefinition(
        sensor_id="radar_noisy",
        sensor_type=SensorType.RADAR,
        simulated_position=Vector3D(x=0, y=0, z=0),
        sampling_interval=0.5,
        measurement_noise=Matrix3x3.diagonal([500, 500, 200]),  # High noise
        metadata={"dropout_probability": 0.1},  # 10% dropout
    )

    return SimulationScenario(
        scenario_id="noisy_sensor",
        schema_version="v1",
        name="مستشعر ضوضائي - قياسات مع ضوضاء",
        description="سيناريو يوضح الفرق بين القياسات الخام والتقديرات المفلترة مع مستشعر ضوضائي",
        duration_seconds=120.0,
        timestep_seconds=0.1,
        random_seed=12345,
        coordinate_system=CoordinateSystem.ENU,
        simulated_sensors=[sensor],
        virtual_objects=[obj],
        environmental_conditions=EnvironmentalConditions(
            wind_velocity=Vector3D(x=5, y=2, z=0),
        ),
        visualization_settings=VisualizationSettings(
            map_center=Vector3D(x=0, y=30000, z=0),
            map_range_km=80,
            show_uncertainty_ellipses=True,
        ),
    )


def _create_multi_sensor_scenario() -> SimulationScenario:
    """Create multi-sensor demo scenario."""
    from nados.domain import (
        CoordinateSystem,
        EnvironmentalConditions,
        ObjectType,
        SensorDefinition,
        SensorType,
        VirtualObject,
        VisualizationSettings,
    )
    from nados.domain.base import Matrix3x3, Vector3D

    # Single target
    obj = VirtualObject(
        object_id="target_001",
        object_type=ObjectType.TARGET,
        initial_position=Vector3D(x=10000, y=40000, z=8000),
        initial_velocity=Vector3D(x=150, y=-100, z=0),
        initial_acceleration=Vector3D(),
        dimensions=Vector3D(x=12, y=12, z=6),
        simulation_enabled=True,
        metadata={"motion_model": "constant_velocity"},
    )

    # Multiple sensors at different positions
    sensors = [
        SensorDefinition(
            sensor_id="radar_north",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.diagonal([200, 200, 100]),
            metadata={"dropout_probability": 0.05},
        ),
        SensorDefinition(
            sensor_id="radar_east",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(x=50000, y=0, z=0),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.diagonal([150, 150, 80]),
            metadata={"dropout_probability": 0.03},
        ),
        SensorDefinition(
            sensor_id="lidar_south",
            sensor_type=SensorType.LIDAR,
            simulated_position=Vector3D(x=0, y=-30000, z=0),
            sampling_interval=0.2,
            measurement_noise=Matrix3x3.diagonal([10, 10, 5]),
            metadata={"dropout_probability": 0.01},
        ),
    ]

    return SimulationScenario(
        scenario_id="multi_sensor_demo",
        schema_version="v1",
        name="متعدد المستشعرات - دمج بيانات من ثلاثة مستشعرات",
        description="سيناريو يوضح دمج البيانات من مستشعرات رادار وليدار مستقلة",
        duration_seconds=180.0,
        timestep_seconds=0.1,
        random_seed=98765,
        coordinate_system=CoordinateSystem.ENU,
        simulated_sensors=sensors,
        virtual_objects=[obj],
        environmental_conditions=EnvironmentalConditions(),
        visualization_settings=VisualizationSettings(
            map_center=Vector3D(x=10000, y=20000, z=0),
            map_range_km=120,
            show_sensor_fov=True,
        ),
    )
