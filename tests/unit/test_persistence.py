"""Unit tests for persistence layer."""

import tempfile

import pytest

from nados.domain import (
    CoordinateSystem,
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
)
from nados.domain.base import Matrix3x3, Vector3D
from nados.persistence import (
    DatabaseManager,
    EventRepository,
    ObservationRepository,
    RunRepository,
    ScenarioRepository,
    SettingsRepository,
    TrackRepository,
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    db = DatabaseManager(db_path, echo=False)
    db.initialize()

    yield db

    db.close()
    import os

    os.unlink(db_path)


@pytest.fixture
def sample_scenario():
    """Create a sample scenario for testing."""
    return SimulationScenario(
        scenario_id="test_scenario",
        schema_version="v1",
        name="Test Scenario",
        description="Test description",
        duration_seconds=60.0,
        timestep_seconds=0.1,
        random_seed=42,
        coordinate_system=CoordinateSystem.ENU,
        simulated_sensors=[
            SensorDefinition(
                sensor_id="radar_001",
                sensor_type=SensorType.RADAR,
                simulated_position=Vector3D(x=0, y=0, z=0),
                sampling_interval=1.0,
                measurement_noise=Matrix3x3.diagonal([100, 100, 25]),
            )
        ],
        virtual_objects=[
            VirtualObject(
                object_id="target_001",
                object_type=ObjectType.TARGET,
                initial_position=Vector3D(x=0, y=10000, z=1000),
                initial_velocity=Vector3D(x=100, y=0, z=0),
            )
        ],
    )


class TestDatabaseManager:
    """Tests for DatabaseManager."""

    def test_initialize(self, temp_db):
        assert temp_db._initialized is True
        assert temp_db._engine is not None

    def test_session_context(self, temp_db):
        from sqlalchemy import text

        with temp_db.session() as session:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1

    def test_backup(self, temp_db):
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            backup_path = f.name

        try:
            temp_db.backup(backup_path)
            import os

            assert os.path.exists(backup_path)
            assert os.path.getsize(backup_path) > 0
        finally:
            import os

            if os.path.exists(backup_path):
                os.unlink(backup_path)


class TestScenarioRepository:
    """Tests for ScenarioRepository."""

    def test_save_and_get(self, temp_db, sample_scenario):
        repo = ScenarioRepository(temp_db)

        repo.save(sample_scenario)
        retrieved = repo.get("test_scenario")

        assert retrieved is not None
        assert retrieved.scenario_id == "test_scenario"
        assert retrieved.name == "Test Scenario"
        assert len(retrieved.simulated_sensors) == 1
        assert len(retrieved.virtual_objects) == 1

    def test_list_all(self, temp_db, sample_scenario):
        repo = ScenarioRepository(temp_db)

        repo.save(sample_scenario)
        scenarios = repo.list_all()

        assert len(scenarios) == 1
        assert scenarios[0].scenario_id == "test_scenario"

    def test_delete(self, temp_db, sample_scenario):
        repo = ScenarioRepository(temp_db)

        repo.save(sample_scenario)
        assert repo.get("test_scenario") is not None

        result = repo.delete("test_scenario")
        assert result is True
        assert repo.get("test_scenario") is None

    def test_delete_nonexistent(self, temp_db):
        repo = ScenarioRepository(temp_db)
        result = repo.delete("nonexistent")
        assert result is False


class TestRunRepository:
    """Tests for RunRepository."""

    def test_save_and_get(self, temp_db):
        # First create the scenario
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="scenario_001",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        repo = RunRepository(temp_db)

        run = SimulationRun(
            run_id="run_001",
            scenario_id="scenario_001",
            random_seed=42,
            application_version="1.0.0",
            configuration_hash="abc123",
            status=RunStatus.RUNNING,
            summary_metrics={"steps": 100},
        )

        repo.save(run)
        retrieved = repo.get("run_001")

        assert retrieved is not None
        assert retrieved.run_id == "run_001"
        assert retrieved.scenario_id == "scenario_001"
        assert retrieved.status == RunStatus.RUNNING
        assert retrieved.summary_metrics["steps"] == 100

    def test_list_by_scenario(self, temp_db):
        # First create the scenario
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="scenario_001",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        repo = RunRepository(temp_db)

        for i in range(3):
            run = SimulationRun(
                run_id=f"run_{i:03d}",
                scenario_id="scenario_001",
                random_seed=42 + i,
                application_version="1.0.0",
                status=RunStatus.COMPLETED,
            )
            repo.save(run)

        runs = repo.list_by_scenario("scenario_001")
        assert len(runs) == 3
        # Should be ordered by started_at desc
        assert runs[0].run_id == "run_002"

    def test_get_latest(self, temp_db):
        # First create the scenario
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="scenario_001",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        repo = RunRepository(temp_db)

        for i in range(3):
            run = SimulationRun(
                run_id=f"run_{i:03d}",
                scenario_id="scenario_001",
                random_seed=42,
                application_version="1.0.0",
                status=RunStatus.COMPLETED,
            )
            repo.save(run)

        latest = repo.get_latest("scenario_001")
        assert latest is not None
        assert latest.run_id == "run_002"


class TestObservationRepository:
    """Tests for ObservationRepository."""

    def test_save_batch_and_get(self, temp_db):
        # First create the scenario and run
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="test_scenario",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        run_repo = RunRepository(temp_db)
        run = SimulationRun(
            run_id="run_001",
            scenario_id="test_scenario",
            random_seed=42,
            application_version="1.0.0",
            status=RunStatus.COMPLETED,
        )
        run_repo.save(run)

        repo = ObservationRepository(temp_db)

        observations = [
            SensorObservation(
                observation_id=f"obs_{i}",
                sensor_id="radar_001",
                timestamp=float(i),
                measured_position=Vector3D(x=1000 + i * 10, y=0, z=0),
                measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
                validity_status=ValidityStatus.VALID,
                scenario_id="test_scenario",
            )
            for i in range(10)
        ]

        repo.save_batch("run_001", observations)
        retrieved = repo.get_by_run("run_001")

        assert len(retrieved) == 10
        assert retrieved[0].sensor_id == "radar_001"
        assert retrieved[0].measured_position.x == 1000

    def test_get_by_sensor(self, temp_db):
        # First create the scenario and run
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="test_scenario",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        run_repo = RunRepository(temp_db)
        run = SimulationRun(
            run_id="run_001",
            scenario_id="test_scenario",
            random_seed=42,
            application_version="1.0.0",
            status=RunStatus.COMPLETED,
        )
        run_repo.save(run)

        repo = ObservationRepository(temp_db)

        observations = [
            SensorObservation(
                observation_id="obs_1",
                sensor_id="radar_001",
                timestamp=1.0,
                measured_position=Vector3D(x=1000, y=0, z=0),
                measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
                validity_status=ValidityStatus.VALID,
                scenario_id="test_scenario",
            ),
            SensorObservation(
                observation_id="obs_2",
                sensor_id="radar_002",
                timestamp=1.0,
                measured_position=Vector3D(x=2000, y=0, z=0),
                measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
                validity_status=ValidityStatus.VALID,
                scenario_id="test_scenario",
            ),
        ]

        repo.save_batch("run_001", observations)

        radar1_obs = repo.get_by_sensor("run_001", "radar_001")
        assert len(radar1_obs) == 1
        assert radar1_obs[0].sensor_id == "radar_001"

    def test_count_by_run(self, temp_db):
        # First create the scenario and run
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="test",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        run_repo = RunRepository(temp_db)
        run = SimulationRun(
            run_id="run_001",
            scenario_id="test",
            random_seed=42,
            application_version="1.0.0",
            status=RunStatus.COMPLETED,
        )
        run_repo.save(run)

        repo = ObservationRepository(temp_db)

        observations = [
            SensorObservation(
                observation_id=f"obs_{i}",
                sensor_id="radar_001",
                timestamp=float(i),
                measured_position=Vector3D(),
                measurement_uncertainty=Matrix3x3.identity(),
                validity_status=ValidityStatus.VALID,
                scenario_id="test",
            )
            for i in range(5)
        ]

        repo.save_batch("run_001", observations)
        count = repo.count_by_run("run_001")
        assert count == 5


class TestTrackRepository:
    """Tests for TrackRepository."""

    def test_save_batch_and_get(self, temp_db):
        # First create the scenario and run
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="test_scenario",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        run_repo = RunRepository(temp_db)
        run = SimulationRun(
            run_id="run_001",
            scenario_id="test_scenario",
            random_seed=42,
            application_version="1.0.0",
            status=RunStatus.COMPLETED,
        )
        run_repo.save(run)

        repo = TrackRepository(temp_db)

        tracks = [
            TrackEstimate(
                track_id=f"track_{i}",
                timestamp=float(i),
                estimated_position=Vector3D(x=1000 + i * 10, y=0, z=0),
                estimated_velocity=Vector3D(x=100, y=0, z=0),
                covariance_or_uncertainty=Matrix3x3.diagonal([50, 50, 10]),
                observation_count=i + 1,
                tracking_status=TrackingStatus.ACTIVE,
                source_sensor_ids=["radar_001"],
            )
            for i in range(5)
        ]

        repo.save_batch("run_001", tracks)
        retrieved = repo.get_by_run("run_001")

        assert len(retrieved) == 5
        assert retrieved[0].track_id == "track_0"
        assert retrieved[0].observation_count == 1


class TestEventRepository:
    """Tests for EventRepository."""

    def test_save_batch_and_get(self, temp_db):
        # First create the scenario and run
        scenario_repo = ScenarioRepository(temp_db)
        scenario = SimulationScenario(
            scenario_id="test_scenario",
            schema_version="v1",
            name="Test Scenario",
            duration_seconds=60.0,
            timestep_seconds=0.1,
            random_seed=42,
            coordinate_system=CoordinateSystem.ENU,
        )
        scenario_repo.save(scenario)

        run_repo = RunRepository(temp_db)
        run = SimulationRun(
            run_id="run_001",
            scenario_id="test_scenario",
            random_seed=42,
            application_version="1.0.0",
            status=RunStatus.COMPLETED,
        )
        run_repo.save(run)

        repo = EventRepository(temp_db)

        events = [
            SimulationEvent(
                event_id=f"evt_{i}",
                event_type=EventType.OBSERVATION_GENERATED,
                timestamp=float(i),
                severity=EventSeverity.INFO,
                message=f"Observation {i}",
                source_module="simulation.engine",
                associated_object_id="target_001",
            )
            for i in range(5)
        ]

        repo.save_batch("run_001", events)
        retrieved = repo.get_by_run("run_001")

        assert len(retrieved) == 5
        assert retrieved[0].event_type == EventType.OBSERVATION_GENERATED


class TestSettingsRepository:
    """Tests for SettingsRepository."""

    def test_set_and_get(self, temp_db):
        repo = SettingsRepository(temp_db)

        repo.set("test_key", {"value": 42}, "Test setting")
        value = repo.get("test_key")

        assert value == {"value": 42}

    def test_get_default(self, temp_db):
        repo = SettingsRepository(temp_db)
        value = repo.get("nonexistent", "default_value")
        assert value == "default_value"

    def test_delete(self, temp_db):
        repo = SettingsRepository(temp_db)

        repo.set("to_delete", "value")
        assert repo.get("to_delete") == "value"

        result = repo.delete("to_delete")
        assert result is True
        assert repo.get("to_delete") is None

    def test_list_all(self, temp_db):
        repo = SettingsRepository(temp_db)

        repo.set("key1", "value1")
        repo.set("key2", "value2")

        all_settings = repo.list_all()
        assert all_settings["key1"] == "value1"
        assert all_settings["key2"] == "value2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
