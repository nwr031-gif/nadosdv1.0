"""Unit tests for data fusion."""

import numpy as np
import pytest

from nados.domain import SensorObservation, TrackEstimate, TrackingStatus, ValidityStatus, Vector3D
from nados.domain.base import Matrix3x3
from nados.fusion.fusion_algorithms import (
    covariance_intersection_fusion,
    detect_conflicts,
    track_to_track_fusion,
    weighted_average_fusion,
)
from nados.fusion.fusion_service import DataFusionService, FusionMethod


class TestWeightedAverageFusion:
    """Tests for weighted average fusion."""

    def test_two_observations_equal_weight(self):
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1010, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        fused_pos, fused_cov = weighted_average_fusion([obs1, obs2])

        # Equal weights -> average
        assert abs(fused_pos.x - 1005.0) < 1e-10
        assert fused_pos.y == 0
        assert fused_pos.z == 0

        # Covariance should be reduced
        assert fused_cov.data[0][0] < 100

    def test_different_uncertainties(self):
        # Precise sensor
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([10, 10, 10]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        # Noisy sensor
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1020, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([1000, 1000, 1000]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        fused_pos, _ = weighted_average_fusion([obs1, obs2])

        # Should be closer to precise sensor
        assert abs(fused_pos.x - 1000) < abs(fused_pos.x - 1020)

    def test_invalid_observations_ignored(self):
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=5000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.MISSING,
            scenario_id="test",
        )

        fused_pos, _ = weighted_average_fusion([obs1, obs2])

        # Should only use valid observation
        assert abs(fused_pos.x - 1000.0) < 1e-10

    def test_empty_list(self):
        fused_pos, fused_cov = weighted_average_fusion([])
        assert fused_pos.x == 0 and fused_pos.y == 0 and fused_pos.z == 0
        assert fused_cov.data == Matrix3x3.identity().data


class TestCovarianceIntersectionFusion:
    """Tests for Covariance Intersection fusion."""

    def test_two_observations(self):
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1010, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([200, 200, 50]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        fused_pos, fused_cov = covariance_intersection_fusion([obs1, obs2])

        # Result should be between the two
        assert 1000 < fused_pos.x < 1010
        assert fused_pos.y == 0

        # Covariance should be valid
        eigvals = np.linalg.eigvalsh(np.array(fused_cov.data))
        assert np.all(eigvals > 0)

    def test_single_observation(self):
        obs = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        fused_pos, fused_cov = covariance_intersection_fusion([obs])

        assert fused_pos.x == 1000
        np.testing.assert_array_equal(fused_cov.data, obs.measurement_uncertainty.data)

    def test_optimal_omega(self):
        # Two sensors with different uncertainties
        P1 = np.diag([100, 100, 25])
        P2 = np.diag([400, 400, 100])

        from nados.fusion.fusion_algorithms import _compute_optimal_omega

        omega = _compute_optimal_omega(P1, P2)

        assert 0 <= omega <= 1
        # Should favor more precise sensor (P1)
        assert omega > 0.5


class TestTrackToTrackFusion:
    """Tests for track-to-track fusion."""

    def test_two_tracks(self):
        track1 = TrackEstimate(
            track_id="t1",
            timestamp=10.0,
            estimated_position=Vector3D(x=1000, y=0, z=0),
            covariance_or_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            tracking_status=TrackingStatus.ACTIVE,
        )
        track2 = TrackEstimate(
            track_id="t2",
            timestamp=10.0,
            estimated_position=Vector3D(x=1010, y=0, z=0),
            covariance_or_uncertainty=Matrix3x3.diagonal([200, 200, 50]),
            tracking_status=TrackingStatus.ACTIVE,
        )

        fused_pos, fused_cov = track_to_track_fusion([track1, track2], method="ci")

        assert 1000 < fused_pos.x < 1010
        eigvals = np.linalg.eigvalsh(np.array(fused_cov.data))
        assert np.all(eigvals > 0)

    def test_inactive_tracks_ignored(self):
        track1 = TrackEstimate(
            track_id="t1",
            timestamp=10.0,
            estimated_position=Vector3D(x=1000, y=0, z=0),
            covariance_or_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            tracking_status=TrackingStatus.ACTIVE,
        )
        track2 = TrackEstimate(
            track_id="t2",
            timestamp=10.0,
            estimated_position=Vector3D(x=5000, y=0, z=0),
            covariance_or_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            tracking_status=TrackingStatus.LOST,
        )

        fused_pos, _ = track_to_track_fusion([track1, track2])

        # Should only use active track
        assert abs(fused_pos.x - 1000) < 1e-10


class TestConflictDetection:
    """Tests for conflict detection."""

    def test_detect_conflict(self):
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=5000, y=0, z=0),  # Far away
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        conflicts = detect_conflicts([obs1, obs2], mahalanobis_threshold=9.21)

        assert len(conflicts) == 1
        assert conflicts[0][0] == 0
        assert conflicts[0][1] == 1
        assert conflicts[0][2] > 9.21

    def test_no_conflict(self):
        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1010, y=0, z=0),  # Close
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        conflicts = detect_conflicts([obs1, obs2], mahalanobis_threshold=9.21)
        assert len(conflicts) == 0


class TestDataFusionService:
    """Tests for DataFusionService."""

    def test_fuse_observations(self):
        service = DataFusionService(method=FusionMethod.WEIGHTED_AVERAGE)

        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1010, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        fused_pos, fused_cov, conflicts = service.fuse_observations([obs1, obs2], 10.0)

        assert abs(fused_pos.x - 1005.0) < 1e-10
        assert len(conflicts) == 0

    def test_fuse_by_object(self):
        service = DataFusionService()

        obs1 = SensorObservation(
            observation_id="obs1",
            sensor_id="s1",
            timestamp=10.0,
            measured_position=Vector3D(x=1000, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )
        obs2 = SensorObservation(
            observation_id="obs2",
            sensor_id="s2",
            timestamp=10.0,
            measured_position=Vector3D(x=1010, y=0, z=0),
            measurement_uncertainty=Matrix3x3.diagonal([100, 100, 25]),
            validity_status=ValidityStatus.VALID,
            scenario_id="test",
        )

        observations_by_object = {
            "target_1": [obs1, obs2],
        }

        results = service.fuse_by_object(observations_by_object, 10.0)

        assert "target_1" in results
        fused_pos, fused_cov, conflicts = results["target_1"]
        assert abs(fused_pos.x - 1005.0) < 1e-10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
