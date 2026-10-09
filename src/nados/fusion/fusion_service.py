"""
Data fusion service coordinating multi-sensor fusion.
"""

from enum import Enum

import numpy as np

from nados.domain import SensorObservation, TrackEstimate, Vector3D
from nados.domain.base import Matrix3x3
from nados.fusion.fusion_algorithms import (
    covariance_intersection_fusion,
    detect_conflicts,
    track_to_track_fusion,
    weighted_average_fusion,
)


class FusionMethod(str, Enum):
    """Fusion method to use."""

    WEIGHTED_AVERAGE = "weighted_average"
    COVARIANCE_INTERSECTION = "covariance_intersection"
    TRACK_TO_TRACK = "track_to_track"


class DataFusionService:
    """Service for multi-sensor data fusion."""

    def __init__(
        self,
        method: FusionMethod = FusionMethod.COVARIANCE_INTERSECTION,
        conflict_threshold: float = 9.21,
    ) -> None:
        self.method = method
        self.conflict_threshold = conflict_threshold
        self._fusion_history: list[dict] = []

    def fuse_observations(
        self,
        observations: list[SensorObservation],
        timestamp: float,
    ) -> tuple[Vector3D, Matrix3x3, list[tuple[int, int, float]]]:
        """
        Fuse multiple observations of the same object.

        Returns:
            Tuple of (fused_position, fused_covariance, conflicts)
        """
        # Detect conflicts
        conflicts = detect_conflicts(observations, self.conflict_threshold)

        # Perform fusion
        if self.method == FusionMethod.WEIGHTED_AVERAGE:
            fused_pos, fused_cov = weighted_average_fusion(observations)
        elif self.method == FusionMethod.COVARIANCE_INTERSECTION:
            fused_pos, fused_cov = covariance_intersection_fusion(observations)
        else:
            fused_pos, fused_cov = weighted_average_fusion(observations)

        # Record fusion event
        self._fusion_history.append(
            {
                "timestamp": timestamp,
                "method": self.method.value,
                "num_observations": len(observations),
                "num_conflicts": len(conflicts),
                "fused_position": [fused_pos.x, fused_pos.y, fused_pos.z],
                "fused_covariance_trace": np.trace(np.array(fused_cov.data)),
            }
        )

        return fused_pos, fused_cov, conflicts

    def fuse_tracks(
        self,
        tracks: list[TrackEstimate],
        timestamp: float,
    ) -> tuple[Vector3D, Matrix3x3]:
        """Fuse multiple track estimates."""
        fused_pos, fused_cov = track_to_track_fusion(tracks, method=self.method.value)

        self._fusion_history.append(
            {
                "timestamp": timestamp,
                "method": self.method.value,
                "num_tracks": len(tracks),
                "fused_position": [fused_pos.x, fused_pos.y, fused_pos.z],
                "fused_covariance_trace": np.trace(np.array(fused_cov.data)),
            }
        )

        return fused_pos, fused_cov

    def fuse_by_object(
        self,
        observations_by_object: dict[str, list[SensorObservation]],
        timestamp: float,
    ) -> dict[str, tuple[Vector3D, Matrix3x3, list[tuple[int, int, float]]]]:
        """Fuse observations grouped by object ID."""
        results = {}

        for obj_id, observations in observations_by_object.items():
            if not observations:
                continue

            fused_pos, fused_cov, conflicts = self.fuse_observations(observations, timestamp)
            results[obj_id] = (fused_pos, fused_cov, conflicts)

        return results

    def get_fusion_history(self) -> list[dict]:
        """Get fusion history."""
        return self._fusion_history.copy()

    def clear_history(self) -> None:
        """Clear fusion history."""
        self._fusion_history.clear()
