"""
Object tracker managing multiple Kalman filters.
"""

import uuid
from typing import Dict, List, Optional, Set

from nados.domain import SensorObservation, TrackEstimate, ValidityStatus, Vector3D
from nados.domain.base import Matrix3x3
from nados.tracking.kalman import KalmanFilter, KalmanFilterConfig
from nados.tracking.association import NearestNeighborAssociator


class TrackManager:
    """Manages multiple tracks and data association."""
    
    def __init__(self, config: Optional[KalmanFilterConfig] = None) -> None:
        self.config = config or KalmanFilterConfig()
        self.tracks: Dict[str, KalmanFilter] = {}
        self.associator = NearestNeighborAssociator()
        self._next_track_id = 1
    
    def process_observations(
        self,
        observations: List[SensorObservation],
        timestamp: float,
        dt: float,
    ) -> List[TrackEstimate]:
        """Process new observations and update tracks."""
        # Predict all existing tracks
        for track in self.tracks.values():
            track.predict(dt)
        
        # Separate valid observations
        valid_obs = [obs for obs in observations if obs.validity_status == ValidityStatus.VALID]
        
        if not valid_obs and self.tracks:
            # No observations, coast all tracks
            for track in self.tracks.values():
                track.coast(dt)
            return self.get_all_estimates()
        
        if not self.tracks:
            # No existing tracks, initialize new ones
            for obs in valid_obs:
                self._create_track(obs, timestamp)
            return self.get_all_estimates()
        
        # Data association
        associations = self.associator.associate(
            tracks=list(self.tracks.values()),
            observations=valid_obs,
            gate_threshold=self.config.gate_threshold,
        )
        
        # Update associated tracks
        associated_obs: Set[int] = set()
        for track_id, obs_idx in associations.items():
            track = self.tracks[track_id]
            obs = valid_obs[obs_idx]
            track.update(obs.measured_position, obs.measurement_uncertainty, obs.sensor_id)
            associated_obs.add(obs_idx)
        
        # Coast unassociated tracks
        for track_id, track in self.tracks.items():
            if track_id not in associations:
                track.coast(dt)
        
        # Create new tracks for unassociated observations
        for i, obs in enumerate(valid_obs):
            if i not in associated_obs:
                self._create_track(obs, timestamp)
        
        # Remove lost tracks
        self._prune_lost_tracks()
        
        return self.get_all_estimates()
    
    def _create_track(self, observation: SensorObservation, timestamp: float) -> None:
        """Create a new track from an observation."""
        track_id = f"track_{self._next_track_id:04d}"
        self._next_track_id += 1
        
        track = KalmanFilter(config=self.config)
        track.track_id = track_id
        track.initialize(
            initial_position=observation.measured_position,
            initial_velocity=Vector3D(),
            timestamp=timestamp,
            track_id=track_id,
        )
        track.source_sensor_ids.append(observation.sensor_id)
        
        self.tracks[track_id] = track
    
    def _prune_lost_tracks(self) -> None:
        """Remove tracks that are lost or terminated."""
        to_remove = [
            track_id for track_id, track in self.tracks.items()
            if track.status == TrackingStatus.LOST
        ]
        for track_id in to_remove:
            del self.tracks[track_id]
    
    def get_all_estimates(self) -> List[TrackEstimate]:
        """Get estimates for all active tracks."""
        return [track.get_estimate() for track in self.tracks.values() if track.status != TrackingStatus.INITIALIZING]
    
    def get_track(self, track_id: str) -> Optional[TrackEstimate]:
        """Get estimate for a specific track."""
        track = self.tracks.get(track_id)
        return track.get_estimate() if track else None
    
    def get_active_tracks(self) -> List[TrackEstimate]:
        """Get only active tracks."""
        return [
            track.get_estimate() for track in self.tracks.values()
            if track.status in (TrackingStatus.ACTIVE, TrackingStatus.COASTING)
        ]


class ObjectTracker:
    """High-level object tracker interface."""
    
    def __init__(self, config: Optional[KalmanFilterConfig] = None) -> None:
        self.manager = TrackManager(config)
        self.config = config or KalmanFilterConfig()
        self.last_timestamp: float = 0.0
    
    def step(
        self,
        observations: List[SensorObservation],
        timestamp: float,
    ) -> List[TrackEstimate]:
        """Process observations at a given timestamp."""
        dt = timestamp - self.last_timestamp if self.last_timestamp > 0 else self.config.coast_max_steps * 0.1
        self.last_timestamp = timestamp
        
        return self.manager.process_observations(observations, timestamp, dt)
    
    def get_tracks(self) -> List[TrackEstimate]:
        """Get all current track estimates."""
        return self.manager.get_all_estimates()
    
    def get_active_tracks(self) -> List[TrackEstimate]:
        """Get only active tracks."""
        return self.manager.get_active_tracks()
    
    def get_track(self, track_id: str) -> Optional[TrackEstimate]:
        """Get specific track."""
        return self.manager.get_track(track_id)
    
    def reset(self) -> None:
        """Reset tracker."""
        self.manager = TrackManager(self.config)
        self.last_timestamp = 0.0