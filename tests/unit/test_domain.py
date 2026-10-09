"""Unit tests for domain models."""

from datetime import datetime

import pytest

from nados.domain import (
    CoordinateSystem,
    EnvironmentalConditions,
    EventSeverity,
    EventType,
    ObjectType,
    RunStatus,
    SensorDefinition,
    SensorObservation,
    SensorType,
    SimulationEvent,
    SimulationRun,
    SimulationScenario,
    TrackEstimate,
    TrackingStatus,
    ValidityStatus,
    VirtualObject,
    VisualizationSettings,
)
from nados.domain.base import Matrix3x3, Vector3D


class TestVector3D:
    """Tests for Vector3D."""

    def test_creation(self):
        v = Vector3D(x=1.0, y=2.0, z=3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_default_zero(self):
        v = Vector3D()
        assert v.x == 0.0
        assert v.y == 0.0
        assert v.z == 0.0

    def test_array_conversion(self):
        v = Vector3D(x=1.0, y=2.0, z=3.0)
        arr = v.to_array()
        assert arr == [1.0, 2.0, 3.0]

        v2 = Vector3D.from_array([4.0, 5.0, 6.0])
        assert v2.x == 4.0
        assert v2.y == 5.0
        assert v2.z == 6.0

    def test_arithmetic(self):
        v1 = Vector3D(x=1.0, y=2.0, z=3.0)
        v2 = Vector3D(x=4.0, y=5.0, z=6.0)

        v_add = v1 + v2
        assert v_add.x == 5.0
        assert v_add.y == 7.0
        assert v_add.z == 9.0

        v_sub = v2 - v1
        assert v_sub.x == 3.0
        assert v_sub.y == 3.0
        assert v_sub.z == 3.0

        v_mul = v1 * 2.0
        assert v_mul.x == 2.0
        assert v_mul.y == 4.0
        assert v_mul.z == 6.0

    def test_magnitude(self):
        v = Vector3D(x=3.0, y=4.0, z=0.0)
        assert v.magnitude() == 5.0

        v_norm = v.normalized()
        assert abs(v_norm.magnitude() - 1.0) < 1e-10

    def test_zero_normalized(self):
        v = Vector3D()
        v_norm = v.normalized()
        assert v_norm.magnitude() == 0.0


class TestMatrix3x3:
    """Tests for Matrix3x3."""

    def test_identity(self):
        m = Matrix3x3.identity()
        assert m.data == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]

    def test_diagonal(self):
        m = Matrix3x3.diagonal([2.0, 3.0, 4.0])
        assert m.data == [[2.0, 0.0, 0.0], [0.0, 3.0, 0.0], [0.0, 0.0, 4.0]]

    def test_trace(self):
        m = Matrix3x3.diagonal([1.0, 2.0, 3.0])
        assert m.trace() == 6.0

    def test_validation(self):
        with pytest.raises(ValueError):
            Matrix3x3(data=[[1, 2], [3, 4]])  # Wrong size

        with pytest.raises(ValueError):
            Matrix3x3(data=[[1, 2, 3], [4, 5, 6]])  # Wrong size


class TestVirtualObject:
    """Tests for VirtualObject."""

    def test_valid_creation(self):
        obj = VirtualObject(
            object_id="test_001",
            object_type=ObjectType.TARGET,
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=100, y=0, z=0),
        )
        assert obj.object_id == "test_001"
        assert obj.object_type == ObjectType.TARGET

    def test_empty_id_rejected(self):
        with pytest.raises(ValueError):
            VirtualObject(object_id="")

    def test_whitespace_id_stripped(self):
        obj = VirtualObject(object_id="  test_001  ")
        assert obj.object_id == "test_001"


class TestSensorDefinition:
    """Tests for SensorDefinition."""

    def test_valid_creation(self):
        sensor = SensorDefinition(
            sensor_id="radar_001",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=1.0,
        )
        assert sensor.sensor_id == "radar_001"
        assert sensor.sampling_interval == 1.0

    def test_invalid_sampling_interval(self):
        with pytest.raises(ValueError):
            SensorDefinition(
                sensor_id="radar_001",
                sensor_type=SensorType.RADAR,
                simulated_position=Vector3D(),
                sampling_interval=-1.0,
            )


class TestSimulationScenario:
    """Tests for SimulationScenario."""

    def create_minimal_scenario(self) -> SimulationScenario:
        return SimulationScenario(
            scenario_id="test_scenario",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
            simulated_sensors=[],
            virtual_objects=[],
        )

    def test_valid_creation(self):
        scenario = self.create_minimal_scenario()
        assert scenario.scenario_id == "test_scenario"
        assert scenario.schema_version == "v1"
        assert scenario.duration_seconds == 60.0

    def test_invalid_schema_version(self):
        with pytest.raises(ValueError):
            SimulationScenario(
                scenario_id="test",
                schema_version="v2",  # Unsupported
                name="Test",
                duration_seconds=60.0,
                timestep_seconds=0.1,
                random_seed=42,
                coordinate_system=CoordinateSystem.ENU,
            )

    def test_invalid_duration(self):
        with pytest.raises(ValueError):
            SimulationScenario(
                scenario_id="test",
                schema_version="v1",
                name="Test",
                duration_seconds=-1.0,
                timestep_seconds=0.1,
                random_seed=42,
                coordinate_system=CoordinateSystem.ENU,
            )

    def test_invalid_timestep(self):
        with pytest.raises(ValueError):
            SimulationScenario(
                scenario_id="test",
                schema_version="v1",
                name="Test",
                duration_seconds=60.0,
                timestep_seconds=0.0,
                random_seed=42,
                coordinate_system=CoordinateSystem.ENU,
            )

    def test_invalid_seed(self):
        with pytest.raises(ValueError):
            SimulationScenario(
                scenario_id="test",
                schema_version="v1",
                name="Test",
                duration_seconds=60.0,
                timestep_seconds=0.1,
                random_seed=-1,
                coordinate_system=CoordinateSystem.ENU,
            )

    def test_duplicate_object_ids(self):
        obj1 = VirtualObject(object_id="obj_1", object_type=ObjectType.GENERIC)
        obj2 = VirtualObject(object_id="obj_1", object_type=ObjectType.GENERIC)

        scenario = SimulationScenario(
            scenario_id="test",
            schema_version="v1",
            name="Test",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
            virtual_objects=[obj1, obj2],
        )

        errors = scenario.validate_references()
        assert any("Duplicate object_id" in e for e in errors)

    def test_duplicate_sensor_ids(self):
        sensor1 = SensorDefinition(
            sensor_id="radar_1", sensor_type=SensorType.RADAR, simulated_position=Vector3D(), sampling_interval=1.0
        )
        sensor2 = SensorDefinition(
            sensor_id="radar_1", sensor_type=SensorType.RADAR, simulated_position=Vector3D(), sampling_interval=1.0
        )

        scenario = SimulationScenario(
            scenario_id="test",
            schema_version="v1",
            name="Test",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
            simulated_sensors=[sensor1, sensor2],
        )

        errors = scenario.validate_references()
        assert any("Duplicate sensor_id" in e for e in errors)

    def test_get_object(self):
        obj = VirtualObject(object_id="target_1", object_type=ObjectType.TARGET)
        scenario = self.create_minimal_scenario()
        scenario.virtual_objects = [obj]

        found = scenario.get_object("target_1")
        assert found is obj

        not_found = scenario.get_object("nonexistent")
        assert not_found is None

    def test_get_sensor(self):
        sensor = SensorDefinition(
            sensor_id="radar_1", sensor_type=SensorType.RADAR, simulated_position=Vector3D(), sampling_interval=1.0
        )
        scenario = self.create_minimal_scenario()
        scenario.simulated_sensors = [sensor]

        found = scenario.get_sensor("radar_1")
        assert found is sensor


class TestSensorObservation:
    """Tests for SensorObservation."""

    def test_valid_creation(self):
        obs = SensorObservation(
            observation_id="obs_001",
            sensor_id="radar_001",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=2000, z=100),
            measurement_uncertainty=Matrix3x3.identity(),
            validity_status=ValidityStatus.VALID,
            scenario_id="scenario_001",
        )
        assert obs.is_valid()
        assert obs.validity_status == ValidityStatus.VALID

    def test_invalid_statuses(self):
        for status in [
            ValidityStatus.MISSING,
            ValidityStatus.INVALID,
            ValidityStatus.OUT_OF_RANGE,
            ValidityStatus.SENSOR_ERROR,
        ]:
            obs = SensorObservation(
                observation_id="obs_001",
                sensor_id="radar_001",
                timestamp=10.0,
                measured_position=Vector3D(),
                measurement_uncertainty=Matrix3x3.identity(),
                validity_status=status,
                scenario_id="scenario_001",
            )
            assert not obs.is_valid()


class TestTrackEstimate:
    """Tests for TrackEstimate."""

    def test_valid_creation(self):
        track = TrackEstimate(
            track_id="track_001",
            timestamp=10.0,
            estimated_position=Vector3D(x=1000, y=2000, z=100),
            estimated_velocity=Vector3D(x=100, y=0, z=0),
            covariance_or_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            observation_count=5,
            tracking_status=TrackingStatus.ACTIVE,
            source_sensor_ids=["radar_001"],
        )
        assert track.is_active()
        assert track.observation_count == 5

    def test_position_uncertainty(self):
        track = TrackEstimate(
            track_id="track_001",
            timestamp=10.0,
            covariance_or_uncertainty=Matrix3x3.diagonal([100, 64, 25]),
        )
        unc = track.get_position_uncertainty()
        assert abs(unc.x - 10.0) < 1e-10
        assert abs(unc.y - 8.0) < 1e-10
        assert abs(unc.z - 5.0) < 1e-10

    def test_inactive_statuses(self):
        for status in [TrackingStatus.LOST, TrackingStatus.TERMINATED, TrackingStatus.INITIALIZING]:
            track = TrackEstimate(
                track_id="track_001",
                timestamp=10.0,
                tracking_status=status,
            )
            assert not track.is_active()


class TestSimulationEvent:
    """Tests for SimulationEvent."""

    def test_valid_creation(self):
        event = SimulationEvent(
            event_id="evt_001",
            event_type=EventType.SCENARIO_STARTED,
            timestamp=0.0,
            severity=EventSeverity.INFO,
            message="Simulation started",
            source_module="simulation.engine",
        )
        assert event.event_type == EventType.SCENARIO_STARTED
        assert event.severity == EventSeverity.INFO

    def test_empty_message_rejected(self):
        with pytest.raises(ValueError):
            SimulationEvent(
                event_id="evt_001",
                event_type=EventType.SCENARIO_STARTED,
                timestamp=0.0,
                severity=EventSeverity.INFO,
                message="",
                source_module="simulation.engine",
            )


class TestSimulationRun:
    """Tests for SimulationRun."""

    def test_valid_creation(self):
        run = SimulationRun(
            run_id="run_001",
            scenario_id="scenario_001",
            random_seed=42,
            application_version="1.0.0",
            configuration_hash="abc123",
            status=RunStatus.RUNNING,
        )
        assert run.run_id == "run_001"
        assert run.status == RunStatus.RUNNING
        assert run.duration_seconds() is None

    def test_duration_calculation(self):
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 1, 30)

        run = SimulationRun(
            run_id="run_001",
            scenario_id="scenario_001",
            started_at=start,
            completed_at=end,
            random_seed=42,
            application_version="1.0.0",
        )
        assert run.duration_seconds() == 90.0

    def test_is_complete(self):
        for status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            run = SimulationRun(
                run_id="run_001", scenario_id="s1", random_seed=42, application_version="1.0.0", status=status
            )
            assert run.is_complete()

        for status in [RunStatus.PENDING, RunStatus.RUNNING, RunStatus.PAUSED]:
            run = SimulationRun(
                run_id="run_001", scenario_id="s1", random_seed=42, application_version="1.0.0", status=status
            )
            assert not run.is_complete()


class TestEnvironmentalConditions:
    """Tests for EnvironmentalConditions."""

    def test_defaults(self):
        env = EnvironmentalConditions()
        assert env.temperature_celsius == 20.0
        assert env.pressure_hpa == 1013.25
        assert env.humidity_percent == 50.0


class TestVisualizationSettings:
    """Tests for VisualizationSettings."""

    def test_defaults(self):
        vis = VisualizationSettings()
        assert vis.show_trails is True
        assert vis.trail_length == 100
        assert vis.map_range_km == 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
