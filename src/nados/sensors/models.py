"""
Sensor models for generating synthetic observations.
"""

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from nados.domain import Vector3D, SensorDefinition, SensorObservation, ValidityStatus
from nados.domain.base import Matrix3x3


@dataclass
class SensorNoiseParams:
    """Noise parameters for sensor models."""
    position_std: Vector3D = field(default_factory=lambda: Vector3D(x=10.0, y=10.0, z=5.0))
    velocity_std: Vector3D = field(default_factory=lambda: Vector3D(x=1.0, y=1.0, z=0.5))
    dropout_probability: float = 0.0
    false_alarm_rate: float = 0.0  # per scan
    bias: Vector3D = field(default_factory=Vector3D)
    correlation_time: float = 1.0  # seconds


class SensorModel(ABC):
    """Abstract base class for sensor models."""
    
    def __init__(self, sensor_def: SensorDefinition, noise_params: Optional[SensorNoiseParams] = None) -> None:
        self.sensor_def = sensor_def
        self.noise_params = noise_params or SensorNoiseParams()
        self._rng = np.random.default_rng()
        self._bias = self.noise_params.bias
        self._last_measurement_time = 0.0
    
    @abstractmethod
    def generate_observation(
        self,
        true_position: Vector3D,
        true_velocity: Vector3D,
        timestamp: float,
        object_id: str,
    ) -> SensorObservation:
        """Generate a single observation for a target."""
        pass
    
    def set_random_seed(self, seed: int) -> None:
        """Set random seed for reproducibility."""
        self._rng = np.random.default_rng(seed)
    
    def _add_noise(self, true_value: Vector3D, std_dev: Vector3D) -> Vector3D:
        """Add Gaussian noise to a 3D vector."""
        noise = Vector3D(
            x=self._rng.normal(0, std_dev.x),
            y=self._rng.normal(0, std_dev.y),
            z=self._rng.normal(0, std_dev.z),
        )
        return Vector3D(
            x=true_value.x + noise.x + self._bias.x,
            y=true_value.y + noise.y + self._bias.y,
            z=true_value.z + noise.z + self._bias.z,
        )
    
    def _check_dropout(self) -> bool:
        """Check if measurement should be dropped out."""
        return self._rng.random() < self.noise_params.dropout_probability
    
    def get_covariance_matrix(self) -> Matrix3x3:
        """Get measurement covariance matrix."""
        return Matrix3x3.diagonal([
            self.noise_params.position_std.x ** 2,
            self.noise_params.position_std.y ** 2,
            self.noise_params.position_std.z ** 2,
        ])


class GenericSensorModel(SensorModel):
    """Generic sensor model with configurable noise."""
    
    def generate_observation(
        self,
        true_position: Vector3D,
        true_velocity: Vector3D,
        timestamp: float,
        object_id: str,
        scenario_id: str = "default",
    ) -> SensorObservation:
        if self._check_dropout():
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.MISSING,
                scenario_id=scenario_id,
            )
        
        measured_pos = self._add_noise(true_position, self.noise_params.position_std)
        
        return SensorObservation(
            observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
            sensor_id=self.sensor_def.sensor_id,
            timestamp=timestamp,
            measured_position=measured_pos,
            measurement_uncertainty=self.get_covariance_matrix(),
            validity_status=ValidityStatus.VALID,
            scenario_id=scenario_id,
        )


class RadarModel(SensorModel):
    """Radar sensor model with range/azimuth/elevation measurements."""
    
    def __init__(self, sensor_def: SensorDefinition, noise_params: Optional[SensorNoiseParams] = None) -> None:
        super().__init__(sensor_def, noise_params)
        # Radar-specific noise parameters
        self.range_std = noise_params.position_std.x if noise_params else 50.0  # meters
        self.azimuth_std = math.radians(0.1)  # radians
        self.elevation_std = math.radians(0.1)  # radians
        self.range_rate_std = noise_params.velocity_std.x if noise_params else 1.0  # m/s
        self.max_range = 200000  # 200 km
    
    def generate_observation(
        self,
        true_position: Vector3D,
        true_velocity: Vector3D,
        timestamp: float,
        object_id: str,
        scenario_id: str = "default",
    ) -> SensorObservation:
        # Check range
        dx = true_position.x - self.sensor_def.simulated_position.x
        dy = true_position.y - self.sensor_def.simulated_position.y
        dz = true_position.z - self.sensor_def.simulated_position.z
        range_m = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if range_m > self.max_range:
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.OUT_OF_RANGE,
                scenario_id=scenario_id,
            )
        
        if self._check_dropout():
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.MISSING,
                scenario_id=scenario_id,
            )
        
        # Sensor position
        sx, sy, sz = self.sensor_def.simulated_position.x, self.sensor_def.simulated_position.y, self.sensor_def.simulated_position.z
        
        # Relative position
        dx = true_position.x - sx
        dy = true_position.y - sy
        dz = true_position.z - sz
        
        # True range, azimuth, elevation
        true_range = math.sqrt(dx*dx + dy*dy + dz*dz)
        true_azimuth = math.atan2(dy, dx)
        true_elevation = math.atan2(dz, math.sqrt(dx*dx + dy*dy))
        
        # Add noise in spherical coordinates
        meas_range = true_range + self._rng.normal(0, self.range_std)
        meas_azimuth = true_azimuth + self._rng.normal(0, self.azimuth_std)
        meas_elevation = true_elevation + self._rng.normal(0, self.elevation_std)
        
        # Convert back to Cartesian
        cos_el = math.cos(meas_elevation)
        meas_x = sx + meas_range * cos_el * math.cos(meas_azimuth)
        meas_y = sy + meas_range * cos_el * math.sin(meas_azimuth)
        meas_z = sz + meas_range * math.sin(meas_elevation)
        
        measured_pos = Vector3D(x=meas_x, y=meas_y, z=meas_z)
        
        # Approximate Cartesian covariance from spherical
        cov = self._spherical_to_cartesian_covariance(
            true_range, true_azimuth, true_elevation
        )
        
        return SensorObservation(
            observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
            sensor_id=self.sensor_def.sensor_id,
            timestamp=timestamp,
            measured_position=measured_pos,
            measurement_uncertainty=Matrix3x3(data=cov),
            validity_status=ValidityStatus.VALID,
            scenario_id=scenario_id,
        )
    
    def _spherical_to_cartesian_covariance(self, r: float, az: float, el: float) -> List[List[float]]:
        """Convert spherical covariance to Cartesian approximation."""
        cos_el = math.cos(el)
        sin_el = math.sin(el)
        cos_az = math.cos(az)
        sin_az = math.sin(az)
        
        # Jacobian from spherical to Cartesian
        # [cos(el)*cos(az), -r*cos(el)*sin(az), -r*sin(el)*cos(az)]
        # [cos(el)*sin(az),  r*cos(el)*cos(az), -r*sin(el)*sin(az)]
        # [sin(el),           0,                   r*cos(el)]
        
        # Spherical variances
        var_r = self.range_std ** 2
        var_az = self.azimuth_std ** 2
        var_el = self.elevation_std ** 2
        
        # Propagate covariance
        J = np.array([
            [cos_el*cos_az, -r*cos_el*sin_az, -r*sin_el*cos_az],
            [cos_el*sin_az,  r*cos_el*cos_az, -r*sin_el*sin_az],
            [sin_el,          0,                r*cos_el],
        ])
        
        Sigma_sph = np.diag([var_r, var_az, var_el])
        Sigma_cart = J @ Sigma_sph @ J.T
        
        return Sigma_cart.tolist()
    
    def get_covariance_matrix(self) -> Matrix3x3:
        # Return approximate covariance at 100km range
        cov = self._spherical_to_cartesian_covariance(100000, 0, 0)
        return Matrix3x3(data=cov)


class LidarModel(SensorModel):
    """LIDAR sensor model with high precision but limited range."""
    
    def __init__(self, sensor_def: SensorDefinition, noise_params: Optional[SensorNoiseParams] = None) -> None:
        super().__init__(sensor_def, noise_params)
        # LIDAR typically has very precise range but limited FOV
        self.range_std = noise_params.position_std.x if noise_params else 0.1  # meters
        self.angular_std = math.radians(0.01)  # Very precise angle
        self.max_range = 50000  # 50 km
    
    def generate_observation(
        self,
        true_position: Vector3D,
        true_velocity: Vector3D,
        timestamp: float,
        object_id: str,
        scenario_id: str = "default",
    ) -> SensorObservation:
        # Check range
        dx = true_position.x - self.sensor_def.simulated_position.x
        dy = true_position.y - self.sensor_def.simulated_position.y
        dz = true_position.z - self.sensor_def.simulated_position.z
        range_m = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if range_m > self.max_range:
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.OUT_OF_RANGE,
                scenario_id=scenario_id,
            )
        
        if self._check_dropout():
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.MISSING,
                scenario_id=scenario_id,
            )
        
        # High precision Cartesian noise
        measured_pos = self._add_noise(true_position, Vector3D(
            x=self.range_std, y=self.range_std, z=self.range_std
        ))
        
        return SensorObservation(
            observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
            sensor_id=self.sensor_def.sensor_id,
            timestamp=timestamp,
            measured_position=measured_pos,
            measurement_uncertainty=self.get_covariance_matrix(),
            validity_status=ValidityStatus.VALID,
            scenario_id=scenario_id,
        )
    
    def get_covariance_matrix(self) -> Matrix3x3:
        return Matrix3x3.diagonal([self.range_std**2, self.range_std**2, self.range_std**2])


class OpticalModel(SensorModel):
    """Optical/infrared sensor model with bearing-only measurements."""
    
    def __init__(self, sensor_def: SensorDefinition, noise_params: Optional[SensorNoiseParams] = None) -> None:
        super().__init__(sensor_def, noise_params)
        # Optical sensors measure angles precisely but no range
        self.azimuth_std = math.radians(0.05)
        self.elevation_std = math.radians(0.05)
        self.max_range = 100000  # 100 km
    
    def generate_observation(
        self,
        true_position: Vector3D,
        true_velocity: Vector3D,
        timestamp: float,
        object_id: str,
        scenario_id: str = "default",
    ) -> SensorObservation:
        # Check range
        dx = true_position.x - self.sensor_def.simulated_position.x
        dy = true_position.y - self.sensor_def.simulated_position.y
        dz = true_position.z - self.sensor_def.simulated_position.z
        range_m = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if range_m > self.max_range:
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.OUT_OF_RANGE,
                scenario_id=scenario_id,
            )
        
        if self._check_dropout():
            return SensorObservation(
                observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
                sensor_id=self.sensor_def.sensor_id,
                timestamp=timestamp,
                measured_position=Vector3D(),
                measurement_uncertainty=self.get_covariance_matrix(),
                validity_status=ValidityStatus.MISSING,
                scenario_id=scenario_id,
            )
        
        # Optical sensors typically provide bearing only
        # For simulation, we add angular noise and assume a nominal range
        sx, sy, sz = self.sensor_def.simulated_position.x, self.sensor_def.simulated_position.y, self.sensor_def.simulated_position.z
        
        true_azimuth = math.atan2(dy, dx)
        true_elevation = math.atan2(dz, math.sqrt(dx*dx + dy*dy))
        
        meas_azimuth = true_azimuth + self._rng.normal(0, self.azimuth_std)
        meas_elevation = true_elevation + self._rng.normal(0, self.elevation_std)
        
        # Assume nominal range for position estimate
        nominal_range = min(range_m, 50000)
        cos_el = math.cos(meas_elevation)
        meas_x = sx + nominal_range * cos_el * math.cos(meas_azimuth)
        meas_y = sy + nominal_range * cos_el * math.sin(meas_azimuth)
        meas_z = sz + nominal_range * math.sin(meas_elevation)
        
        measured_pos = Vector3D(x=meas_x, y=meas_y, z=meas_z)
        
        # Large uncertainty in range direction
        cov = self._bearing_only_covariance(range_m, true_azimuth, true_elevation)
        
        return SensorObservation(
            observation_id=f"{self.sensor_def.sensor_id}_{object_id}_{timestamp:.3f}",
            sensor_id=self.sensor_def.sensor_id,
            timestamp=timestamp,
            measured_position=measured_pos,
            measurement_uncertainty=Matrix3x3(data=cov),
            validity_status=ValidityStatus.VALID,
            scenario_id=scenario_id,
        )
    
    def _bearing_only_covariance(self, r: float, az: float, el: float) -> List[List[float]]:
        """Covariance for bearing-only sensor (large range uncertainty)."""
        # Range uncertainty assumed to be 50% of range
        range_std = r * 0.5
        
        cos_el = math.cos(el)
        sin_el = math.sin(el)
        cos_az = math.cos(az)
        sin_az = math.sin(az)
        
        var_r = range_std ** 2
        var_az = self.azimuth_std ** 2
        var_el = self.elevation_std ** 2
        
        J = np.array([
            [cos_el*cos_az, -r*cos_el*sin_az, -r*sin_el*cos_az],
            [cos_el*sin_az,  r*cos_el*cos_az, -r*sin_el*sin_az],
            [sin_el,          0,                r*cos_el],
        ])
        
        Sigma_sph = np.diag([var_r, var_az, var_el])
        Sigma_cart = J @ Sigma_sph @ J.T
        
        return Sigma_cart.tolist()
    
    def get_covariance_matrix(self) -> Matrix3x3:
        cov = self._bearing_only_covariance(50000, 0, 0)
        return Matrix3x3(data=cov)


def create_sensor_model(sensor_def: SensorDefinition, noise_params: Optional[SensorNoiseParams] = None) -> SensorModel:
    """Factory function to create sensor models based on type."""
    models = {
        "radar": RadarModel,
        "lidar": LidarModel,
        "optical": OpticalModel,
        "irst": OpticalModel,
        "acoustic": GenericSensorModel,
        "generic": GenericSensorModel,
    }
    
    sensor_type = sensor_def.sensor_type.lower() if isinstance(sensor_def.sensor_type, str) else sensor_def.sensor_type.value.lower()
    model_class = models.get(sensor_type, GenericSensorModel)
    return model_class(sensor_def, noise_params)