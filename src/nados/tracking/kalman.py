"""
Kalman filter implementation for object tracking.
"""

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from nados.domain import TrackEstimate, TrackingStatus, Vector3D
from nados.domain.base import Matrix3x3
from nados.simulation.motion import MotionModel, KinematicState, ConstantVelocityModel, create_motion_model


@dataclass
class KalmanFilterConfig:
    """Configuration for Kalman filter."""
    motion_model_type: str = "constant_velocity"
    process_noise: float = 0.1
    measurement_noise_scale: float = 1.0
    initial_position_uncertainty: float = 100.0  # meters^2
    initial_velocity_uncertainty: float = 10.0  # (m/s)^2
    initial_acceleration_uncertainty: float = 1.0  # (m/s^2)^2
    coast_max_steps: int = 10  # Max steps without observation before lost
    gate_threshold: float = 9.21  # Chi-squared 95% for 3 DOF


class KalmanFilter:
    """Kalman filter for 3D position and velocity tracking."""
    
    def __init__(
        self,
        config: Optional[KalmanFilterConfig] = None,
        motion_model: Optional[MotionModel] = None,
    ) -> None:
        self.config = config or KalmanFilterConfig()
        self.motion_model = motion_model or create_motion_model(self.config.motion_model_type)
        
        # State: [x, y, z, vx, vy, vz, ax, ay, az] - 9 dimensions
        self.state_dim = 9
        
        # Measurement: [x, y, z] - 3 dimensions
        self.meas_dim = 3
        
        # State vector
        self.x = np.zeros(self.state_dim, dtype=np.float64)
        
        # Covariance matrix
        self.P = np.eye(self.state_dim, dtype=np.float64)
        
        # Measurement matrix H (maps state to measurement)
        self.H = np.zeros((self.meas_dim, self.state_dim), dtype=np.float64)
        self.H[0, 0] = 1.0  # x
        self.H[1, 1] = 1.0  # y
        self.H[2, 2] = 1.0  # z
        
        # Measurement noise R
        self.R = np.eye(self.meas_dim, dtype=np.float64)
        
        # Process noise Q (updated each step)
        self.Q = np.eye(self.state_dim, dtype=np.float64)
        
        # State transition matrix F (updated each step)
        self.F = np.eye(self.state_dim, dtype=np.float64)
        
        # Identity matrix
        self.I = np.eye(self.state_dim, dtype=np.float64)
        
        # Track management
        self.track_id: str = ""
        self.timestamp: float = 0.0
        self.observation_count: int = 0
        self.coast_steps: int = 0
        self.status: TrackingStatus = TrackingStatus.INITIALIZING
        self.source_sensor_ids: list[str] = []
        
        # History for smoothing (optional)
        self._history: list[tuple[float, np.ndarray, np.ndarray]] = []
    
    def initialize(self, initial_position: Vector3D, initial_velocity: Vector3D, timestamp: float, track_id: str) -> None:
        """Initialize filter with first observation."""
        self.track_id = track_id
        self.timestamp = timestamp
        
        # State vector
        self.x[0] = initial_position.x
        self.x[1] = initial_position.y
        self.x[2] = initial_position.z
        self.x[3] = initial_velocity.x
        self.x[4] = initial_velocity.y
        self.x[5] = initial_velocity.z
        self.x[6:9] = 0.0  # Assume zero initial acceleration
        
        # Initial covariance
        self.P = np.diag([
            self.config.initial_position_uncertainty,
            self.config.initial_position_uncertainty,
            self.config.initial_position_uncertainty,
            self.config.initial_velocity_uncertainty,
            self.config.initial_velocity_uncertainty,
            self.config.initial_velocity_uncertainty,
            self.config.initial_acceleration_uncertainty,
            self.config.initial_acceleration_uncertainty,
            self.config.initial_acceleration_uncertainty,
        ]).astype(np.float64)
        
        self.observation_count = 1
        self.coast_steps = 0
        self.status = TrackingStatus.ACTIVE
        
        # Record history
        self._history.append((timestamp, self.x.copy(), self.P.copy()))
    
    def predict(self, dt: float) -> None:
        """Predict step."""
        if self.status == TrackingStatus.INITIALIZING:
            return
        
        # Update state transition matrix
        self.F = self.motion_model.get_state_transition_matrix(dt)
        
        # Update process noise
        self.Q = self.motion_model.get_process_noise_matrix(dt, {"process_noise": self.config.process_noise})
        
        # Predict state
        self.x = self.F @ self.x
        
        # Predict covariance
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        self.timestamp += dt
        
        # Record history
        self._history.append((self.timestamp, self.x.copy(), self.P.copy()))
    
    def update(self, measurement: Vector3D, measurement_covariance: Matrix3x3, sensor_id: str) -> bool:
        """Update step with measurement."""
        if self.status == TrackingStatus.INITIALIZING:
            # Initialize from first measurement
            self.initialize(measurement, Vector3D(), self.timestamp, self.track_id)
            if sensor_id not in self.source_sensor_ids:
                self.source_sensor_ids.append(sensor_id)
            return True
        
        # Measurement vector
        z = np.array([measurement.x, measurement.y, measurement.z], dtype=np.float64)
        
        # Measurement noise
        R = np.array(measurement_covariance.data, dtype=np.float64) * self.config.measurement_noise_scale
        self.R = R
        
        # Innovation
        y = z - self.H @ self.x
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Gating - check if measurement is consistent
        try:
            S_inv = np.linalg.inv(S)
            mahalanobis_sq = float(y.T @ S_inv @ y)
            
            if mahalanobis_sq > self.config.gate_threshold:
                # Measurement rejected by gate
                self.coast_steps += 1
                if self.coast_steps >= self.config.coast_max_steps:
                    self.status = TrackingStatus.LOST
                return False
        except np.linalg.LinAlgError:
            # Singular matrix
            return False
        
        # Kalman gain
        K = self.P @ self.H.T @ S_inv
        
        # Update state
        self.x = self.x + K @ y
        
        # Update covariance (Joseph form for numerical stability)
        self.P = (self.I - K @ self.H) @ self.P @ (self.I - K @ self.H).T + K @ self.R @ K.T
        
        # Ensure symmetry
        self.P = (self.P + self.P.T) * 0.5
        
        self.observation_count += 1
        self.coast_steps = 0
        self.status = TrackingStatus.ACTIVE
        
        if sensor_id not in self.source_sensor_ids:
            self.source_sensor_ids.append(sensor_id)
        
        return True
    
    def coast(self, dt: float) -> None:
        """Predict without measurement (coasting)."""
        if self.status in (TrackingStatus.LOST, TrackingStatus.TERMINATED, TrackingStatus.INITIALIZING):
            return
        
        self.predict(dt)
        self.coast_steps += 1
        
        if self.coast_steps >= self.config.coast_max_steps:
            self.status = TrackingStatus.LOST
        elif self.status == TrackingStatus.ACTIVE:
            self.status = TrackingStatus.COASTING
    
    def get_estimate(self) -> TrackEstimate:
        """Get current track estimate."""
        pos = Vector3D(x=self.x[0], y=self.x[1], z=self.x[2])
        vel = Vector3D(x=self.x[3], y=self.x[4], z=self.x[5])
        
        # Extract position covariance (3x3)
        pos_cov = self.P[0:3, 0:3]
        cov_matrix = Matrix3x3(data=pos_cov.tolist())
        
        return TrackEstimate(
            track_id=self.track_id,
            timestamp=self.timestamp,
            estimated_position=pos,
            estimated_velocity=vel,
            covariance_or_uncertainty=cov_matrix,
            observation_count=self.observation_count,
            tracking_status=self.status,
            source_sensor_ids=self.source_sensor_ids.copy(),
        )
    
    def get_state_vector(self) -> np.ndarray:
        """Get full state vector."""
        return self.x.copy()
    
    def get_covariance(self) -> np.ndarray:
        """Get full covariance matrix."""
        return self.P.copy()
    
    def compute_innovation(self, measurement: Vector3D, measurement_covariance: Matrix3x3) -> tuple[np.ndarray, np.ndarray]:
        """Compute innovation and innovation covariance for association."""
        z = np.array([measurement.x, measurement.y, measurement.z], dtype=np.float64)
        R = np.array(measurement_covariance.data, dtype=np.float64)
        
        y = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + R
        
        return y, S
    
    def validate_state(self) -> bool:
        """Validate filter state for numerical issues."""
        # Check for NaN or Inf
        if not np.all(np.isfinite(self.x)):
            return False
        if not np.all(np.isfinite(self.P)):
            return False
        # Check covariance is positive semi-definite
        try:
            eigvals = np.linalg.eigvalsh(self.P)
            if np.any(eigvals < -1e-10):
                return False
        except np.linalg.LinAlgError:
            return False
        return True
    
    def reset(self) -> None:
        """Reset filter to initial state."""
        self.x.fill(0.0)
        self.P = np.eye(self.state_dim, dtype=np.float64)
        self.timestamp = 0.0
        self.observation_count = 0
        self.coast_steps = 0
        self.status = TrackingStatus.INITIALIZING
        self.source_sensor_ids.clear()
        self._history.clear()


# Import numpy here for the covariance calculation
import numpy as np