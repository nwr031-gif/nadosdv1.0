"""Unit tests for Kalman filter."""

import numpy as np
import pytest

from nados.domain import Vector3D, TrackingStatus
from nados.domain.base import Matrix3x3
from nados.tracking.kalman import KalmanFilter, KalmanFilterConfig
from nados.simulation.motion import ConstantVelocityModel


class TestKalmanFilterConfig:
    """Tests for KalmanFilterConfig."""
    
    def test_defaults(self):
        config = KalmanFilterConfig()
        assert config.motion_model_type == "constant_velocity"
        assert config.process_noise == 0.1
        assert config.coast_max_steps == 10
        assert config.gate_threshold == 9.21


class TestKalmanFilter:
    """Tests for KalmanFilter."""
    
    def setup_method(self):
        self.config = KalmanFilterConfig()
        self.kf = KalmanFilter(config=self.config)
    
    def test_initialization(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        assert self.kf.track_id == "track_001"
        assert self.kf.timestamp == 0.0
        assert self.kf.observation_count == 1
        assert self.kf.status == TrackingStatus.ACTIVE
        
        # Check state
        assert self.kf.x[0] == 0.0
        assert self.kf.x[1] == 1000.0
        assert self.kf.x[2] == 100.0
        assert self.kf.x[3] == 50.0
    
    def test_predict_constant_velocity(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=0, z=0),
            initial_velocity=Vector3D(x=100, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        # Predict 1 second
        self.kf.predict(dt=1.0)
        
        # Position should advance by velocity * dt
        assert abs(self.kf.x[0] - 100.0) < 1e-10
        assert abs(self.kf.x[1]) < 1e-10
        assert self.kf.timestamp == 1.0
    
    def test_update_with_measurement(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        # Measurement at same position (perfect)
        meas_pos = Vector3D(x=0, y=1000, z=100)
        meas_cov = Matrix3x3.diagonal([100, 100, 25])
        
        result = self.kf.update(meas_pos, meas_cov, "radar_001")
        
        assert result is True
        assert self.kf.observation_count == 2
        assert "radar_001" in self.kf.source_sensor_ids
    
    def test_update_rejects_outlier(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        # Measurement far from prediction (outside gate)
        meas_pos = Vector3D(x=10000, y=1000, z=100)  # 10km away
        meas_cov = Matrix3x3.diagonal([100, 100, 25])
        
        result = self.kf.update(meas_pos, meas_cov, "radar_001")
        
        # Should be rejected by gate
        assert result is False
        assert self.kf.coast_steps == 1
    
    def test_coast_without_measurement(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        # Coast for several steps
        for i in range(5):
            self.kf.coast(dt=1.0)
        
        assert self.kf.coast_steps == 5
        assert self.kf.status == TrackingStatus.COASTING
        
        # Exceed coast max
        for i in range(6):
            self.kf.coast(dt=1.0)
        
        assert self.kf.status == TrackingStatus.LOST
    
    def test_get_estimate(self):
        self.kf.initialize(
            initial_position=Vector3D(x=100, y=200, z=50),
            initial_velocity=Vector3D(x=10, y=20, z=5),
            timestamp=5.0,
            track_id="track_001",
        )
        
        estimate = self.kf.get_estimate()
        
        assert estimate.track_id == "track_001"
        assert estimate.timestamp == 5.0
        assert estimate.estimated_position.x == 100
        assert estimate.estimated_velocity.y == 20
        assert estimate.observation_count == 1
        assert estimate.tracking_status == TrackingStatus.ACTIVE
    
    def test_innovation_computation(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="track_001",
        )
        
        meas_pos = Vector3D(x=10, y=1005, z=102)
        meas_cov = Matrix3x3.diagonal([100, 100, 25])
        
        innovation, innovation_cov = self.kf.compute_innovation(meas_pos, meas_cov)
        
        assert innovation.shape == (3,)
        assert innovation_cov.shape == (3, 3)
        # Innovation should be measurement - prediction
        assert abs(innovation[0] - 10) < 1e-10
        assert abs(innovation[1] - 5) < 1e-10
    
    def test_validate_state(self):
        self.kf.initialize(
            initial_position=Vector3D(x=0, y=0, z=0),
            initial_velocity=Vector3D(x=0, y=0, z=0),
            timestamp=0.0,
            track_id="test",
        )
        assert self.kf.validate_state() is True
        
        # Inject NaN
        self.kf.x[0] = float('nan')
        assert self.kf.validate_state() is False
    
    def test_reset(self):
        self.kf.initialize(
            initial_position=Vector3D(x=100, y=0, z=0),
            initial_velocity=Vector3D(x=10, y=0, z=0),
            timestamp=10.0,
            track_id="track_001",
        )
        
        self.kf.reset()
        
        assert self.kf.timestamp == 0.0
        assert self.kf.observation_count == 0
        assert self.kf.status == TrackingStatus.INITIALIZING
        assert np.all(self.kf.x == 0)
        assert len(self.kf.source_sensor_ids) == 0


class TestKalmanFilterNumerical:
    """Numerical regression tests for Kalman filter."""
    
    def test_cv_predict_known_values(self):
        """Test CV prediction matches analytical solution."""
        kf = KalmanFilter()
        kf.initialize(
            initial_position=Vector3D(x=0, y=0, z=0),
            initial_velocity=Vector3D(x=10, y=20, z=5),
            timestamp=0.0,
            track_id="test",
        )
        
        # Predict 2 seconds
        kf.predict(2.0)
        
        # x = 0 + 10*2 = 20
        # y = 0 + 20*2 = 40
        # z = 0 + 5*2 = 10
        assert abs(kf.x[0] - 20.0) < 1e-10
        assert abs(kf.x[1] - 40.0) < 1e-10
        assert abs(kf.x[2] - 10.0) < 1e-10
        
        # Velocity unchanged
        assert abs(kf.x[3] - 10.0) < 1e-10
        assert abs(kf.x[4] - 20.0) < 1e-10
        assert abs(kf.x[5] - 5.0) < 1e-10
    
    def test_update_reduces_uncertainty(self):
        """Test that update reduces position uncertainty."""
        kf = KalmanFilter()
        kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=50, y=0, z=0),
            timestamp=0.0,
            track_id="test",
        )
        
        # Get initial covariance trace
        initial_trace = np.trace(kf.P[0:3, 0:3])
        
        # Update with measurement
        meas_pos = Vector3D(x=0, y=1000, z=100)
        meas_cov = Matrix3x3.diagonal([100, 100, 25])
        kf.update(meas_pos, meas_cov, "radar_001")
        
        # Covariance should decrease
        updated_trace = np.trace(kf.P[0:3, 0:3])
        assert updated_trace < initial_trace
    
    def test_multiple_updates_converge(self):
        """Test that repeated updates converge."""
        kf = KalmanFilter()
        kf.initialize(
            initial_position=Vector3D(x=0, y=0, z=0),
            initial_velocity=Vector3D(x=100, y=0, z=0),
            timestamp=0.0,
            track_id="test",
        )
        
        meas_cov = Matrix3x3.diagonal([100, 100, 25])
        
        # Multiple perfect measurements
        for i in range(10):
            kf.predict(1.0)
            kf.update(Vector3D(x=100*(i+1), y=0, z=0), meas_cov, "radar_001")
        
        # Velocity estimate should converge to 100
        estimate = kf.get_estimate()
        assert abs(estimate.estimated_velocity.x - 100.0) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])