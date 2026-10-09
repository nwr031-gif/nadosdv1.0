"""
Fusion algorithms for combining sensor data.
"""

import math

import numpy as np

from nados.domain import SensorObservation, TrackEstimate, ValidityStatus, Vector3D
from nados.domain.base import Matrix3x3


def weighted_average_fusion(
    observations: list[SensorObservation],
) -> tuple[Vector3D, Matrix3x3]:
    """
    Fuse observations using weighted average (inverse covariance weighting).

    Returns:
        Tuple of (fused_position, fused_covariance)
    """
    if not observations:
        return Vector3D(), Matrix3x3.identity()

    # Filter valid observations
    valid_obs = [obs for obs in observations if obs.validity_status == ValidityStatus.VALID]
    if not valid_obs:
        return Vector3D(), Matrix3x3.identity()

    # Compute weights (inverse covariance)
    positions = []
    covariances = []
    weights = []

    for obs in valid_obs:
        pos = np.array([obs.measured_position.x, obs.measured_position.y, obs.measured_position.z])
        cov = np.array(obs.measurement_uncertainty.data)

        # Use trace of covariance as scalar weight
        weight = 1.0 / (np.trace(cov) + 1e-10)

        positions.append(pos)
        covariances.append(cov)
        weights.append(weight)

    # Normalize weights
    total_weight = sum(weights)
    weights = [w / total_weight for w in weights]

    # Weighted average position
    fused_pos = np.zeros(3)
    for pos, weight in zip(positions, weights, strict=True):
        fused_pos += pos * weight

    # Fused covariance (approximate)
    fused_cov = np.zeros((3, 3))
    for cov, weight in zip(covariances, weights, strict=True):
        fused_cov += cov * (weight**2)

    return (
        Vector3D(x=fused_pos[0], y=fused_pos[1], z=fused_pos[2]),
        Matrix3x3(data=fused_cov.tolist()),
    )


def covariance_intersection_fusion(
    observations: list[SensorObservation],
    omega: float = 0.5,
) -> tuple[Vector3D, Matrix3x3]:
    """
    Fuse observations using Covariance Intersection (CI).

    CI provides a consistent fusion without requiring cross-correlation knowledge.
    """
    if not observations:
        return Vector3D(), Matrix3x3.identity()

    valid_obs = [obs for obs in observations if obs.validity_status == ValidityStatus.VALID]
    if not valid_obs:
        return Vector3D(), Matrix3x3.identity()

    if len(valid_obs) == 1:
        obs = valid_obs[0]
        return obs.measured_position, obs.measurement_uncertainty

    # For two estimates, use optimal omega
    if len(valid_obs) == 2:
        omega = _compute_optimal_omega(
            np.array(valid_obs[0].measurement_uncertainty.data),
            np.array(valid_obs[1].measurement_uncertainty.data),
        )

    # Information form fusion
    fused_info = np.zeros((3, 3))
    fused_info_vec = np.zeros(3)

    for obs in valid_obs:
        cov = np.array(obs.measurement_uncertainty.data)
        pos = np.array([obs.measured_position.x, obs.measured_position.y, obs.measured_position.z])

        try:
            info = np.linalg.inv(cov)
        except np.linalg.LinAlgError:
            info = np.eye(3) * 1e-6

        fused_info += omega * info
        fused_info_vec += omega * info @ pos

    try:
        fused_cov = np.linalg.inv(fused_info)
        fused_pos = fused_cov @ fused_info_vec
    except np.linalg.LinAlgError:
        fused_cov = np.eye(3) * 1e6
        fused_pos = np.zeros(3)

    return (
        Vector3D(x=fused_pos[0], y=fused_pos[1], z=fused_pos[2]),
        Matrix3x3(data=fused_cov.tolist()),
    )


def _compute_optimal_omega(cov1: np.ndarray, cov2: np.ndarray) -> float:
    """Compute optimal omega for two-estimate CI (minimize trace)."""

    # Use scalar optimization
    def trace_fused(omega: float) -> float:
        try:
            info1 = np.linalg.inv(cov1)
            info2 = np.linalg.inv(cov2)
            fused_info = omega * info1 + (1 - omega) * info2
            fused_cov = np.linalg.inv(fused_info)
            return np.trace(fused_cov)
        except np.linalg.LinAlgError:
            return float("inf")

    # Golden section search
    a, b = 0.0, 1.0
    phi = (math.sqrt(5) - 1) / 2  # Golden ratio

    for _ in range(20):
        c = b - phi * (b - a)
        d = a + phi * (b - a)
        if trace_fused(c) < trace_fused(d):
            b = d
        else:
            a = c

    return (a + b) / 2


def track_to_track_fusion(
    tracks: list[TrackEstimate],
    method: str = "ci",
) -> tuple[Vector3D, Matrix3x3]:
    """
    Fuse track estimates (track-to-track fusion).

    Args:
        tracks: List of track estimates to fuse
        method: "ci" for covariance intersection, "weighted" for weighted average

    Returns:
        Tuple of (fused_position, fused_covariance)
    """
    if not tracks:
        return Vector3D(), Matrix3x3.identity()

    # Convert tracks to observation-like format
    pseudo_observations = []
    for track in tracks:
        if track.tracking_status in ("active", "coasting"):
            obs = SensorObservation(
                observation_id=f"track_{track.track_id}",
                sensor_id=track.track_id,
                timestamp=track.timestamp,
                measured_position=track.estimated_position,
                measurement_uncertainty=track.covariance_or_uncertainty,
                validity_status=ValidityStatus.VALID,
                scenario_id="fusion",
            )
            pseudo_observations.append(obs)

    if not pseudo_observations:
        return Vector3D(), Matrix3x3.identity()

    if method == "ci":
        return covariance_intersection_fusion(pseudo_observations)
    else:
        return weighted_average_fusion(pseudo_observations)


def detect_conflicts(
    observations: list[SensorObservation],
    mahalanobis_threshold: float = 9.21,
) -> list[tuple[int, int, float]]:
    """
    Detect conflicting observations using Mahalanobis distance.

    Returns list of (obs_idx_1, obs_idx_2, distance_squared)
    """
    conflicts = []
    valid_obs = [(i, obs) for i, obs in enumerate(observations) if obs.validity_status == ValidityStatus.VALID]

    for idx1, (i, obs1) in enumerate(valid_obs):
        for j, obs2 in valid_obs[idx1 + 1 :]:
            pos1 = np.array([obs1.measured_position.x, obs1.measured_position.y, obs1.measured_position.z])
            pos2 = np.array([obs2.measured_position.x, obs2.measured_position.y, obs2.measured_position.z])
            cov1 = np.array(obs1.measurement_uncertainty.data)
            cov2 = np.array(obs2.measurement_uncertainty.data)

            diff = pos1 - pos2
            combined_cov = cov1 + cov2

            try:
                inv_cov = np.linalg.inv(combined_cov)
                dist_sq = float(diff.T @ inv_cov @ diff)

                if dist_sq > mahalanobis_threshold:
                    conflicts.append((i, j, dist_sq))
            except np.linalg.LinAlgError:
                pass

    return conflicts
