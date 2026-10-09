"""Unit tests for motion models."""

import numpy as np
import pytest

from nados.domain.base import Vector3D
from nados.simulation.motion import (
    ConstantAccelerationModel,
    ConstantVelocityModel,
    KinematicState,
    create_motion_model,
)


class TestKinematicState:
    """Tests for KinematicState."""

    def test_creation(self):
        state = KinematicState(
            position=Vector3D(x=100, y=200, z=50),
            velocity=Vector3D(x=10, y=5, z=0),
            acceleration=Vector3D(x=0, y=0, z=0),
            timestamp=10.0,
        )
        assert state.position.x == 100
        assert state.velocity.y == 5
        assert state.timestamp == 10.0

    def test_state_vector_conversion(self):
        state = KinematicState(
            position=Vector3D(x=1, y=2, z=3),
            velocity=Vector3D(x=4, y=5, z=6),
            acceleration=Vector3D(x=7, y=8, z=9),
        )
        vec = state.to_state_vector()
        expected = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        np.testing.assert_array_equal(vec, expected)

    def test_from_state_vector(self):
        vec = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9])
        state = KinematicState.from_state_vector(vec, timestamp=5.0)
        assert state.position.x == 1
        assert state.velocity.y == 5
        assert state.acceleration.z == 9
        assert state.timestamp == 5.0

    def test_invalid_vector_length(self):
        with pytest.raises(ValueError):
            KinematicState.from_state_vector(np.array([1, 2, 3]))

    def test_validate(self):
        state = KinematicState(
            position=Vector3D(x=1.0, y=2.0, z=3.0),
            velocity=Vector3D(x=0.1, y=0.2, z=0.3),
            acceleration=Vector3D(),
        )
        assert state.validate() is True

        # Test with NaN
        state_nan = KinematicState(
            position=Vector3D(x=float("nan"), y=0, z=0),
            velocity=Vector3D(),
            acceleration=Vector3D(),
        )
        assert state_nan.validate() is False


class TestConstantVelocityModel:
    """Tests for ConstantVelocityModel."""

    def setup_method(self):
        self.model = ConstantVelocityModel()

    def test_predict_position(self):
        state = KinematicState(
            position=Vector3D(x=0, y=0, z=0),
            velocity=Vector3D(x=10, y=20, z=5),
            acceleration=Vector3D(),
            timestamp=0.0,
        )

        new_state = self.model.predict(state, dt=1.0)

        assert new_state.position.x == 10.0
        assert new_state.position.y == 20.0
        assert new_state.position.z == 5.0
        assert new_state.velocity.x == 10.0  # Unchanged
        assert new_state.timestamp == 1.0

    def test_predict_multiple_steps(self):
        state = KinematicState(
            position=Vector3D(x=0, y=0, z=0),
            velocity=Vector3D(x=5, y=0, z=0),
            acceleration=Vector3D(),
        )

        for _i in range(10):
            state = self.model.predict(state, dt=1.0)

        assert state.position.x == 50.0
        assert state.velocity.x == 5.0

    def test_state_transition_matrix(self):
        dt = 0.5
        F = self.model.get_state_transition_matrix(dt)

        assert F.shape == (9, 9)
        # Position depends on velocity
        assert F[0, 3] == dt
        assert F[1, 4] == dt
        assert F[2, 5] == dt
        # Velocity unchanged
        assert F[3, 3] == 1.0
        assert F[4, 4] == 1.0
        assert F[5, 5] == 1.0

    def test_process_noise_matrix(self):
        dt = 1.0
        Q = self.model.get_process_noise_matrix(dt, {"process_noise": 0.1})

        assert Q.shape == (9, 9)
        # Check symmetry
        np.testing.assert_array_almost_equal(Q, Q.T)
        # Check positive semi-definite
        eigvals = np.linalg.eigvalsh(Q)
        assert np.all(eigvals >= -1e-10)
        # Position-position terms
        expected_pos_var = 0.1 * dt**4 / 4
        assert abs(Q[0, 0] - expected_pos_var) < 1e-10


class TestConstantAccelerationModel:
    """Tests for ConstantAccelerationModel."""

    def setup_method(self):
        self.model = ConstantAccelerationModel()

    def test_predict_with_acceleration(self):
        state = KinematicState(
            position=Vector3D(x=0, y=0, z=0),
            velocity=Vector3D(x=10, y=0, z=0),
            acceleration=Vector3D(x=2, y=0, z=0),
            timestamp=0.0,
        )

        new_state = self.model.predict(state, dt=1.0)

        # x = 0 + 10*1 + 0.5*2*1^2 = 11
        assert new_state.position.x == 11.0
        # vx = 10 + 2*1 = 12
        assert new_state.velocity.x == 12.0
        # ax unchanged
        assert new_state.acceleration.x == 2.0

    def test_state_transition_matrix(self):
        dt = 0.5
        F = self.model.get_state_transition_matrix(dt)

        assert F.shape == (9, 9)
        # Position depends on velocity and acceleration
        assert F[0, 3] == dt
        assert F[0, 6] == dt**2 / 2
        # Velocity depends on acceleration
        assert F[3, 6] == dt

    def test_process_noise_matrix(self):
        dt = 1.0
        Q = self.model.get_process_noise_matrix(
            dt,
            {
                "process_noise": 0.1,
                "jerk_noise": 0.01,
            },
        )

        assert Q.shape == (9, 9)
        # Check symmetry
        np.testing.assert_array_almost_equal(Q, Q.T)
        # Acceleration terms should have jerk noise
        assert Q[6, 6] > 0
        assert Q[7, 7] > 0
        assert Q[8, 8] > 0


class TestMotionModelFactory:
    """Tests for motion model factory."""

    def test_create_cv(self):
        model = create_motion_model("constant_velocity")
        assert isinstance(model, ConstantVelocityModel)

    def test_create_cv_alias(self):
        model = create_motion_model("cv")
        assert isinstance(model, ConstantVelocityModel)

    def test_create_ca(self):
        model = create_motion_model("constant_acceleration")
        assert isinstance(model, ConstantAccelerationModel)

    def test_create_ca_alias(self):
        model = create_motion_model("ca")
        assert isinstance(model, ConstantAccelerationModel)

    def test_invalid_model(self):
        with pytest.raises(ValueError):
            create_motion_model("invalid_model")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
