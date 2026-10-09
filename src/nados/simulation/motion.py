"""
Motion models for virtual objects.
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import numpy as np

from nados.domain import Vector3D
from nados.domain.base import validate_finite


@dataclass
class KinematicState:
    """Complete kinematic state of an object."""
    position: Vector3D
    velocity: Vector3D
    acceleration: Vector3D
    timestamp: float = 0.0
    
    def to_state_vector(self) -> np.ndarray:
        """Convert to 9-element state vector [x, y, z, vx, vy, vz, ax, ay, az]."""
        return np.array([
            self.position.x, self.position.y, self.position.z,
            self.velocity.x, self.velocity.y, self.velocity.z,
            self.acceleration.x, self.acceleration.y, self.acceleration.z,
        ], dtype=np.float64)
    
    @classmethod
    def from_state_vector(cls, vec: np.ndarray, timestamp: float = 0.0) -> "KinematicState":
        """Create from 9-element state vector."""
        if len(vec) != 9:
            raise ValueError("State vector must have 9 elements")
        return cls(
            position=Vector3D(x=vec[0], y=vec[1], z=vec[2]),
            velocity=Vector3D(x=vec[3], y=vec[4], z=vec[5]),
            acceleration=Vector3D(x=vec[6], y=vec[7], z=vec[8]),
            timestamp=timestamp,
        )
    
    def validate(self) -> bool:
        """Validate all kinematic components are finite."""
        try:
            for v in [self.position.x, self.position.y, self.position.z,
                      self.velocity.x, self.velocity.y, self.velocity.z,
                      self.acceleration.x, self.acceleration.y, self.acceleration.z]:
                validate_finite(v)
        except ValueError:
            return False
        return True


class MotionModel(ABC):
    """Abstract base class for motion models."""
    
    @abstractmethod
    def predict(self, state: KinematicState, dt: float) -> KinematicState:
        """Predict next state after time dt."""
        pass
    
    @abstractmethod
    def get_state_transition_matrix(self, dt: float) -> np.ndarray:
        """Get state transition matrix F for Kalman filter."""
        pass
    
    @abstractmethod
    def get_process_noise_matrix(self, dt: float, noise_params: dict) -> np.ndarray:
        """Get process noise covariance matrix Q."""
        pass


class ConstantVelocityModel(MotionModel):
    """Constant velocity motion model (CV)."""
    
    def predict(self, state: KinematicState, dt: float) -> KinematicState:
        """Predict next state assuming constant velocity."""
        new_pos = Vector3D(
            x=state.position.x + state.velocity.x * dt,
            y=state.position.y + state.velocity.y * dt,
            z=state.position.z + state.velocity.z * dt,
        )
        return KinematicState(
            position=new_pos,
            velocity=state.velocity,
            acceleration=Vector3D(),
            timestamp=state.timestamp + dt,
        )
    
    def get_state_transition_matrix(self, dt: float) -> np.ndarray:
        """Get 9x9 state transition matrix for CV model."""
        F = np.eye(9, dtype=np.float64)
        # Position depends on velocity
        F[0, 3] = dt  # x <- x + vx*dt
        F[1, 4] = dt  # y <- y + vy*dt
        F[2, 5] = dt  # z <- z + vz*dt
        return F
    
    def get_process_noise_matrix(self, dt: float, noise_params: dict) -> np.ndarray:
        """Get process noise covariance for CV model."""
        # White noise acceleration model
        q = noise_params.get("process_noise", 0.1)
        
        # Continuous-time noise spectral density
        q_c = q
        
        # Discrete-time process noise covariance
        dt2 = dt * dt
        dt3 = dt2 * dt
        dt4 = dt3 * dt
        
        Q = np.zeros((9, 9), dtype=np.float64)
        
        # Position-position terms
        Q[0, 0] = Q[1, 1] = Q[2, 2] = q_c * dt4 / 4
        # Position-velocity terms
        Q[0, 3] = Q[3, 0] = q_c * dt3 / 2
        Q[1, 4] = Q[4, 1] = q_c * dt3 / 2
        Q[2, 5] = Q[5, 2] = q_c * dt3 / 2
        # Velocity-velocity terms
        Q[3, 3] = Q[4, 4] = Q[5, 5] = q_c * dt2
        # Acceleration terms (assumed zero for CV)
        
        return Q


class ConstantAccelerationModel(MotionModel):
    """Constant acceleration motion model (CA)."""
    
    def predict(self, state: KinematicState, dt: float) -> KinematicState:
        """Predict next state assuming constant acceleration."""
        dt2 = dt * dt * 0.5
        new_pos = Vector3D(
            x=state.position.x + state.velocity.x * dt + state.acceleration.x * dt2,
            y=state.position.y + state.velocity.y * dt + state.acceleration.y * dt2,
            z=state.position.z + state.velocity.z * dt + state.acceleration.z * dt2,
        )
        new_vel = Vector3D(
            x=state.velocity.x + state.acceleration.x * dt,
            y=state.velocity.y + state.acceleration.y * dt,
            z=state.velocity.z + state.acceleration.z * dt,
        )
        return KinematicState(
            position=new_pos,
            velocity=new_vel,
            acceleration=state.acceleration,
            timestamp=state.timestamp + dt,
        )
    
    def get_state_transition_matrix(self, dt: float) -> np.ndarray:
        """Get 9x9 state transition matrix for CA model."""
        F = np.eye(9, dtype=np.float64)
        dt2 = dt * dt * 0.5
        # Position depends on velocity and acceleration
        F[0, 3] = dt      # x <- x + vx*dt
        F[0, 6] = dt2     # x <- x + ax*dt^2/2
        F[1, 4] = dt
        F[1, 7] = dt2
        F[2, 5] = dt
        F[2, 8] = dt2
        # Velocity depends on acceleration
        F[3, 6] = dt      # vx <- vx + ax*dt
        F[4, 7] = dt
        F[5, 8] = dt
        return F
    
    def get_process_noise_matrix(self, dt: float, noise_params: dict) -> np.ndarray:
        """Get process noise covariance for CA model."""
        q = noise_params.get("process_noise", 0.1)
        jerk_noise = noise_params.get("jerk_noise", 0.01)
        
        Q = np.zeros((9, 9), dtype=np.float64)
        dt2 = dt * dt
        dt3 = dt2 * dt
        dt4 = dt3 * dt
        dt5 = dt4 * dt
        dt6 = dt5 * dt
        
        # Position-position
        Q[0, 0] = Q[1, 1] = Q[2, 2] = q * dt4 / 4 + jerk_noise * dt6 / 36
        # Position-velocity
        Q[0, 3] = Q[3, 0] = q * dt3 / 2 + jerk_noise * dt5 / 12
        Q[1, 4] = Q[4, 1] = q * dt3 / 2 + jerk_noise * dt5 / 12
        Q[2, 5] = Q[5, 2] = q * dt3 / 2 + jerk_noise * dt5 / 12
        # Position-acceleration
        Q[0, 6] = Q[6, 0] = jerk_noise * dt4 / 6
        Q[1, 7] = Q[7, 1] = jerk_noise * dt4 / 6
        Q[2, 8] = Q[8, 2] = jerk_noise * dt4 / 6
        # Velocity-velocity
        Q[3, 3] = Q[4, 4] = Q[5, 5] = q * dt2 + jerk_noise * dt4 / 4
        # Velocity-acceleration
        Q[3, 6] = Q[6, 3] = jerk_noise * dt3 / 3
        Q[4, 7] = Q[7, 4] = jerk_noise * dt3 / 3
        Q[5, 8] = Q[8, 5] = jerk_noise * dt3 / 3
        # Acceleration-acceleration
        Q[6, 6] = Q[7, 7] = Q[8, 8] = jerk_noise * dt2
        
        return Q


def create_motion_model(model_type: str) -> MotionModel:
    """Factory function to create motion models."""
    models = {
        "constant_velocity": ConstantVelocityModel,
        "cv": ConstantVelocityModel,
        "constant_acceleration": ConstantAccelerationModel,
        "ca": ConstantAccelerationModel,
    }
    
    model_class = models.get(model_type.lower())
    if model_class is None:
        raise ValueError(f"Unknown motion model: {model_type}. Available: {list(models.keys())}")
    
    return model_class()