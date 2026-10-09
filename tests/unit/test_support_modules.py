"""Unit tests for observation generator, report templates, association, and tracker."""

import pytest

from nados.domain import (
    SensorDefinition,
    SensorObservation,
    SensorType,
    TrackingStatus,
    ValidityStatus,
    Vector3D,
)
from nados.domain.base import Matrix3x3
from nados.reporting.templates import (
    CSVReportTemplate,
    JSONReportTemplate,
    ReportTemplate,
    get_template,
)
from nados.sensors.generator import ObservationGenerator
from nados.tracking.association import (
    NearestNeighborAssociator,
    create_associator,
)
from nados.tracking.kalman import KalmanFilter, KalmanFilterConfig
from nados.tracking.tracker import ObjectTracker, TrackManager


def _make_sensor(sensor_id: str, sensor_type: SensorType = SensorType.RADAR) -> SensorDefinition:
    return SensorDefinition(
        sensor_id=sensor_id,
        sensor_type=sensor_type,
        simulated_position=Vector3D(x=0, y=0, z=0),
        sampling_interval=1.0,
        measurement_noise=Matrix3x3.diagonal([100, 100, 25]),
    )


def _make_observation(
    obs_id: str,
    sensor_id: str,
    position: Vector3D,
    timestamp: float = 0.0,
) -> SensorObservation:
    return SensorObservation(
        observation_id=obs_id,
        sensor_id=sensor_id,
        timestamp=timestamp,
        measured_position=position,
        measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
        validity_status=ValidityStatus.VALID,
        scenario_id="test_scenario",
    )


class TestObservationGenerator:
    """Tests for ObservationGenerator."""

    def _states(self):
        from nados.simulation.motion import KinematicState

        return {
            "target_1": KinematicState(
                position=Vector3D(x=1000, y=2000, z=100),
                velocity=Vector3D(x=50, y=0, z=0),
                acceleration=Vector3D(),
                timestamp=0.0,
            )
        }

    def test_generates_for_all_sensors(self):
        sensors = [_make_sensor("s1"), _make_sensor("s2")]
        generator = ObservationGenerator(sensors, self._states(), random_seed=42)
        result = generator.generate_all_observations(timestamp=0.0)
        assert set(result.keys()) == {"s1", "s2"}
        for _sensor_id, observations in result.items():
            assert len(observations) == 1
            assert observations[0].scenario_id == "default"

    def test_deterministic_with_same_seed(self):
        sensors = [_make_sensor("s1")]
        gen1 = ObservationGenerator(sensors, self._states(), random_seed=7)
        gen2 = ObservationGenerator(sensors, self._states(), random_seed=7)
        obs1 = gen1.generate_all_observations(1.0)["s1"][0]
        obs2 = gen2.generate_all_observations(1.0)["s1"][0]
        assert obs1.measured_position.x == obs2.measured_position.x
        assert obs1.measured_position.y == obs2.measured_position.y
        assert obs1.measured_position.z == obs2.measured_position.z

    def test_per_sensor_generation(self):
        sensors = [_make_sensor("s1")]
        generator = ObservationGenerator(sensors, self._states(), random_seed=1)
        observations = generator.generate_observations_for_sensor("s1", timestamp=5.0)
        assert len(observations) == 1
        assert observations[0].timestamp == 5.0

    def test_unknown_sensor_returns_empty(self):
        sensors = [_make_sensor("s1")]
        generator = ObservationGenerator(sensors, self._states(), random_seed=1)
        assert generator.generate_observations_for_sensor("unknown", 0.0) == []

    def test_get_sensor_model(self):
        sensors = [_make_sensor("s1")]
        generator = ObservationGenerator(sensors, self._states(), random_seed=1)
        assert generator.get_sensor_model("s1") is not None
        assert generator.get_sensor_model("missing") is None


class TestReportTemplates:
    """Tests for report templates."""

    def test_base_template_not_implemented(self):
        template = ReportTemplate()
        with pytest.raises(NotImplementedError):
            template.render({})

    def test_json_template_render(self):
        import json

        template = JSONReportTemplate()
        rendered = template.render({"section": {"value": 42}})
        assert json.loads(rendered)["section"]["value"] == 42

    def test_csv_template_render(self):
        template = CSVReportTemplate()
        rendered = template.render({"s1": {"key": "value1"}, "s2": {"num": 7}})
        lines = rendered.strip().splitlines()
        assert lines[0] == "Section,Key,Value"
        assert "s1,key,value1" in rendered
        assert "s2,num,7" in rendered

    def test_get_template_factory(self):
        assert isinstance(get_template("json"), JSONReportTemplate)
        assert isinstance(get_template("csv"), CSVReportTemplate)
        with pytest.raises(ValueError):
            get_template("invalid")


class TestNearestNeighborAssociator:
    """Tests for NearestNeighborAssociator."""

    def _make_track(self, track_id: str, position: Vector3D) -> KalmanFilter:
        kf = KalmanFilter(config=KalmanFilterConfig())
        kf.initialize(position, Vector3D(), 0.0, track_id)
        return kf

    def test_associates_matching_observation(self):
        track = self._make_track("t1", Vector3D(x=1000, y=0, z=0))
        obs = _make_observation("o1", "s1", Vector3D(x=1010, y=2, z=0), timestamp=0.0)
        result = NearestNeighborAssociator().associate([track], [obs])
        assert result == {"t1": 0}

    def test_rejects_far_observation(self):
        track = self._make_track("t1", Vector3D(x=1000, y=0, z=0))
        obs = _make_observation("o1", "s1", Vector3D(x=50000, y=0, z=0), timestamp=0.0)
        result = NearestNeighborAssociator().associate([track], [obs])
        assert result == {}

    def test_empty_inputs(self):
        result = NearestNeighborAssociator().associate([], [])
        assert result == {}

    def test_nearest_wins_with_two_observations(self):
        track = self._make_track("t1", Vector3D(x=1000, y=0, z=0))
        near = _make_observation("near", "s1", Vector3D(x=1005, y=0, z=0))
        far = _make_observation("far", "s1", Vector3D(x=1100, y=0, z=0))
        result = NearestNeighborAssociator().associate([track], [far, near])
        assert result == {"t1": 1}

    def test_create_associator_factory(self):
        assert isinstance(create_associator("nn"), NearestNeighborAssociator)
        assert isinstance(create_associator("nearest_neighbor"), NearestNeighborAssociator)
        with pytest.raises(ValueError):
            create_associator("bogus")


class TestTrackManager:
    """Tests for TrackManager."""

    def test_creates_track_from_first_observation(self):
        manager = TrackManager()
        obs = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0))]
        estimates = manager.process_observations(obs, timestamp=0.0, dt=1.0)
        assert len(estimates) == 1
        assert estimates[0].tracking_status == TrackingStatus.ACTIVE

    def test_updates_existing_track(self):
        manager = TrackManager()
        obs1 = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0), timestamp=0.0)]
        obs2 = [_make_observation("o2", "s1", Vector3D(x=110, y=0, z=0), timestamp=1.0)]
        manager.process_observations(obs1, timestamp=0.0, dt=1.0)
        estimates = manager.process_observations(obs2, timestamp=1.0, dt=1.0)
        assert len(estimates) == 1
        assert estimates[0].observation_count == 2

    def test_no_observations_coasts_tracks(self):
        manager = TrackManager()
        obs1 = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0), timestamp=0.0)]
        manager.process_observations(obs1, timestamp=0.0, dt=1.0)
        estimates = manager.process_observations([], timestamp=1.0, dt=1.0)
        assert len(estimates) == 1

    def test_get_active_tracks(self):
        manager = TrackManager()
        obs = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0))]
        manager.process_observations(obs, timestamp=0.0, dt=1.0)
        active = manager.get_active_tracks()
        assert len(active) == 1


class TestObjectTracker:
    """Tests for ObjectTracker high-level interface."""

    def test_step_updates_last_timestamp(self):
        tracker = ObjectTracker()
        obs = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0))]
        tracker.step(obs, timestamp=0.0)
        assert tracker.last_timestamp == 0.0
        obs2 = [_make_observation("o2", "s1", Vector3D(x=110, y=0, z=0), timestamp=1.0)]
        tracker.step(obs2, timestamp=1.0)
        assert tracker.last_timestamp == 1.0

    def test_get_tracks(self):
        tracker = ObjectTracker()
        obs = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0))]
        tracker.step(obs, timestamp=0.0)
        assert len(tracker.get_tracks()) == 1

    def test_reset_clears_tracks(self):
        tracker = ObjectTracker()
        obs = [_make_observation("o1", "s1", Vector3D(x=100, y=0, z=0))]
        tracker.step(obs, timestamp=0.0)
        assert len(tracker.get_tracks()) == 1
        tracker.reset()
        assert len(tracker.get_tracks()) == 0
        assert tracker.last_timestamp == 0.0

    def test_invalid_observations_not_tracked(self):
        tracker = ObjectTracker()
        obs = SensorObservation(
            observation_id="bad",
            sensor_id="s1",
            timestamp=0.0,
            measured_position=Vector3D(),
            measurement_uncertainty=Matrix3x3.identity(),
            validity_status=ValidityStatus.MISSING,
            scenario_id="test",
        )
        estimates = tracker.step([obs], timestamp=0.0)
        assert len(estimates) == 0
