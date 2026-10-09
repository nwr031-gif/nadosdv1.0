"""Unit tests for sensor models."""

import numpy as np
import pytest

from nados.domain import SensorDefinition, SensorType, ValidityStatus, Vector3D
from nados.domain.base import Matrix3x3
from nados.sensors.models import (
    GenericSensorModel, RadarModel, LidarModel, OpticalModel,
    SensorNoiseParams, create_sensor_model,
)


class TestSensorNoiseParams:
    """Tests for SensorNoiseParams."""
    
    def test_defaults(self):
        params = SensorNoiseParams()
        assert params.position_std.x == 10.0
        assert params.velocity_std.x == 1.0
        assert params.dropout_probability == 0.0
        assert params.false_alarm_rate == 0.0


class TestGenericSensorModel:
    """Tests for GenericSensorModel."""
    
    def setup_method(self):
        self.sensor_def = SensorDefinition(
            sensor_id="generic_001",
            sensor_type=SensorType.GENERIC,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.diagonal([100, 100, 25]),
        )
        self.noise_params = SensorNoiseParams(
            position_std=Vector3D(x=10, y=10, z=5),
        )
        self.model = GenericSensorModel(self.sensor_def, self.noise_params)
        self.model.set_random_seed(42)
    
    def test_valid_observation(self):
        true_pos = Vector3D(x=1000, y=2000, z=100)
        true_vel = Vector3D(x=50, y=0, z=0)
        
        obs = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        assert obs.sensor_id == "generic_001"
        assert obs.validity_status == ValidityStatus.VALID
        assert obs.timestamp == 10.0
        assert obs.scenario_id == "default"
        
        # Check measurement has noise added
        assert obs.measured_position.x != true_pos.x
        assert obs.measured_position.y != true_pos.y
    
    def test_deterministic_with_seed(self):
        true_pos = Vector3D(x=1000, y=2000, z=100)
        true_vel = Vector3D(x=50, y=0, z=0)
        
        # Generate with same seed
        self.model.set_random_seed(42)
        obs1 = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        self.model.set_random_seed(42)
        obs2 = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        assert obs1.measured_position.x == obs2.measured_position.x
        assert obs1.measured_position.y == obs2.measured_position.y
        assert obs1.measured_position.z == obs2.measured_position.z
    
    def test_covariance_matrix(self):
        cov = self.model.get_covariance_matrix()
        assert cov.data[0][0] == 100  # 10^2
        assert cov.data[1][1] == 100
        assert cov.data[2][2] == 25   # 5^2
    
    def test_dropout(self):
        # High dropout probability
        model = GenericSensorModel(
            self.sensor_def,
            SensorNoiseParams(dropout_probability=1.0)
        )
        model.set_random_seed(42)
        
        obs = model.generate_observation(
            Vector3D(x=1000, y=0, z=0),
            Vector3D(), 10.0, "target_001"
        )
        assert obs.validity_status == ValidityStatus.MISSING


class TestRadarModel:
    """Tests for RadarModel."""
    
    def setup_method(self):
        self.sensor_def = SensorDefinition(
            sensor_id="radar_001",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.diagonal([2500, 2500, 625]),
        )
        self.model = RadarModel(self.sensor_def)
        self.model.set_random_seed(42)
    
    def test_valid_observation(self):
        # Target at 10km East, 5km altitude
        true_pos = Vector3D(x=10000, y=0, z=5000)
        true_vel = Vector3D(x=100, y=0, z=0)
        
        obs = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        assert obs.validity_status == ValidityStatus.VALID
        # Measurement should be near true position (with noise)
        assert abs(obs.measured_position.x - true_pos.x) < 500
        assert abs(obs.measured_position.z - true_pos.z) < 200
    
    def test_out_of_range(self):
        # Target at 300km (beyond 200km limit)
        true_pos = Vector3D(x=300000, y=0, z=0)
        true_vel = Vector3D()
        
        obs = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        assert obs.validity_status == ValidityStatus.OUT_OF_RANGE
    
    def test_covariance_at_100km(self):
        cov = self.model.get_covariance_matrix()
        # Should have reasonable values
        assert cov.data[0][0] > 0
        assert cov.data[1][1] > 0
        assert cov.data[2][2] > 0


class TestLidarModel:
    """Tests for LidarModel."""
    
    def setup_method(self):
        self.sensor_def = SensorDefinition(
            sensor_id="lidar_001",
            sensor_type=SensorType.LIDAR,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=0.1,
        )
        self.model = LidarModel(self.sensor_def)
        self.model.set_random_seed(42)
    
    def test_high_precision(self):
        true_pos = Vector3D(x=1000, y=2000, z=100)
        true_vel = Vector3D(x=50, y=0, z=0)
        
        obs = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        assert obs.validity_status == ValidityStatus.VALID
        # Very small noise (0.1m std)
        assert abs(obs.measured_position.x - true_pos.x) < 1.0
        assert abs(obs.measured_position.y - true_pos.y) < 1.0
    
    def test_max_range(self):
        # Beyond 50km
        true_pos = Vector3D(x=60000, y=0, z=0)
        obs = self.model.generate_observation(true_pos, Vector3D(), 10.0, "target_001")
        assert obs.validity_status == ValidityStatus.OUT_OF_RANGE


class TestOpticalModel:
    """Tests for OpticalModel."""
    
    def setup_method(self):
        self.sensor_def = SensorDefinition(
            sensor_id="optical_001",
            sensor_type=SensorType.OPTICAL,
            simulated_position=Vector3D(x=0, y=0, z=0),
            sampling_interval=0.5,
        )
        self.model = OpticalModel(self.sensor_def)
        self.model.set_random_seed(42)
    
    def test_bearing_only(self):
        true_pos = Vector3D(x=10000, y=10000, z=5000)
        true_vel = Vector3D()
        
        obs = self.model.generate_observation(true_pos, true_vel, 10.0, "target_001")
        
        assert obs.validity_status == ValidityStatus.VALID
        # Large covariance in range direction (bearing-only sensors have high range uncertainty)
        cov = np.array(obs.measurement_uncertainty.data)
        trace = np.trace(cov)
        assert trace > 1e7  # Large uncertainty expected for bearing-only sensor


class TestSensorFactory:
    """Tests for sensor model factory."""
    
    def test_create_radar(self):
        sensor_def = SensorDefinition(
            sensor_id="radar_1", sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(), sampling_interval=1.0
        )
        model = create_sensor_model(sensor_def)
        assert isinstance(model, RadarModel)
    
    def test_create_lidar(self):
        sensor_def = SensorDefinition(
            sensor_id="lidar_1", sensor_type=SensorType.LIDAR,
            simulated_position=Vector3D(), sampling_interval=1.0
        )
        model = create_sensor_model(sensor_def)
        assert isinstance(model, LidarModel)
    
    def test_create_optical(self):
        sensor_def = SensorDefinition(
            sensor_id="optical_1", sensor_type=SensorType.OPTICAL,
            simulated_position=Vector3D(), sampling_interval=1.0
        )
        model = create_sensor_model(sensor_def)
        assert isinstance(model, OpticalModel)
    
    def test_create_unknown_type(self):
        sensor_def = SensorDefinition(
            sensor_id="unknown_1", sensor_type=SensorType.GENERIC,
            simulated_position=Vector3D(), sampling_interval=1.0
        )
        model = create_sensor_model(sensor_def)
        assert isinstance(model, GenericSensorModel)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])