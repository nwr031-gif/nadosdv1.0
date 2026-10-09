"""
Data association for multi-target tracking.
"""

import numpy as np

from nados.domain import SensorObservation, ValidityStatus
from nados.tracking.kalman import KalmanFilter


class DataAssociation:
    """Base class for data association algorithms."""

    def associate(
        self,
        tracks: list[KalmanFilter],
        observations: list[SensorObservation],
        gate_threshold: float = 9.21,
    ) -> dict[str, int]:
        """
        Associate tracks to observations.

        Returns:
            Dict mapping track_id -> observation_index
        """
        raise NotImplementedError


class NearestNeighborAssociator(DataAssociation):
    """Nearest neighbor data association with gating."""

    def associate(
        self,
        tracks: list[KalmanFilter],
        observations: list[SensorObservation],
        gate_threshold: float = 9.21,
    ) -> dict[str, int]:
        """Associate tracks to observations using nearest neighbor with gating."""
        if not tracks or not observations:
            return {}

        # Compute cost matrix (Mahalanobis distance)
        num_tracks = len(tracks)
        num_obs = len(observations)

        cost_matrix = np.full((num_tracks, num_obs), np.inf)
        valid_gates = np.zeros((num_tracks, num_obs), dtype=bool)

        for i, track in enumerate(tracks):
            for j, obs in enumerate(observations):
                if obs.validity_status != ValidityStatus.VALID:
                    continue

                innovation, innovation_cov = track.compute_innovation(
                    obs.measured_position, obs.measurement_uncertainty
                )

                try:
                    inv_S = np.linalg.inv(innovation_cov)
                    mahalanobis_sq = float(innovation.T @ inv_S @ innovation)

                    if mahalanobis_sq <= gate_threshold:
                        cost_matrix[i, j] = mahalanobis_sq
                        valid_gates[i, j] = True
                except np.linalg.LinAlgError:
                    pass

        # Greedy nearest neighbor assignment
        associations = {}
        used_obs: set[int] = set()

        # Sort tracks by number of valid gates (most constrained first)
        track_order = sorted(range(num_tracks), key=lambda i: np.sum(valid_gates[i]))

        for i in track_order:
            # Find nearest valid observation
            valid_indices = np.where(valid_gates[i])[0]
            if len(valid_indices) == 0:
                continue

            # Find minimum cost among unused observations
            min_cost = np.inf
            best_j = -1
            for j in valid_indices:
                if j not in used_obs and cost_matrix[i, j] < min_cost:
                    min_cost = cost_matrix[i, j]
                    best_j = j

            if best_j >= 0:
                associations[tracks[i].track_id] = best_j
                used_obs.add(best_j)

        return associations


class JointProbabilisticDataAssociation(DataAssociation):
    """JPDA - Joint Probabilistic Data Association (simplified)."""

    def associate(
        self,
        tracks: list[KalmanFilter],
        observations: list[SensorObservation],
        gate_threshold: float = 9.21,
        detection_probability: float = 0.9,
        clutter_density: float = 1e-6,
    ) -> dict[str, int]:
        """Simplified JPDA - returns most likely association."""
        # For now, fall back to NN
        nn = NearestNeighborAssociator()
        return nn.associate(tracks, observations, gate_threshold)


def create_associator(associator_type: str = "nn") -> DataAssociation:
    """Factory for data associators."""
    associators = {
        "nn": NearestNeighborAssociator,
        "nearest_neighbor": NearestNeighborAssociator,
        "jpda": JointProbabilisticDataAssociation,
    }

    cls = associators.get(associator_type.lower())
    if cls is None:
        raise ValueError(f"Unknown associator: {associator_type}")

    return cls()
