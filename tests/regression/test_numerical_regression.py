"""Regression tests with deterministic fixtures and known expected values.

These tests pin the numerical behaviour of core algorithms. Expected
values were computed analytically for the constant-velocity /
constant-acceleration motion models and the linear Kalman filter. If a
model change alters these outputs, the fixture must only be updated
after the change is reviewed and documented in CHANGELOG.md.
"""

import numpy as np
import pytest

from nados.domain.base import Matrix3x3, Vector3D
from nados.simulation.motion import (
    ConstantAccelerationModel,
    ConstantVelocityModel,
    KinematicState,
)
from nados.tracking.kalman import KalmanFilter, KalmanFilterConfig


class TestMotionRegression:
    """Deterministic motion-model fixtures."""

    CV = ConstantVelocityModel()
    CA = ConstantAccelerationModel()

    def test_cv_position_after_10_steps(self):
        """CV: x(t) = x0 + v*t. v = (25, -15, 5) m/s, t = 10 s."""
        state = KinematicState(
            position=Vector3D(x=0, y=0, z=1000),
            velocity=Vector3D(x=25, y=-15, z=5),
            acceleration=Vector3D(),
            timestamp=0.0,
        )
        for _ in range(10):
            state = self.CV.predict(state, dt=1.0)
        assert state.position.x == pytest.approx(250.0, abs=1e-9)
        assert state.position.y == pytest.approx(-150.0, abs=1e-9)
        assert state.position.z == pytest.approx(1050.0, abs=1e-9)
        assert state.timestamp == pytest.approx(10.0, abs=1e-9)

    def test_cv_with_fractional_timestep(self):
        """CV with dt = 0.25 s over 40 steps equals one 10 s prediction."""
        state_a = KinematicState(
            position=Vector3D(),
            velocity=Vector3D(x=10, y=0, z=0),
            acceleration=Vector3D(),
        )
        state_b = KinematicState(
            position=Vector3D(),
            velocity=Vector3D(x=10, y=0, z=0),
            acceleration=Vector3D(),
        )
        for _ in range(40):
            state_a = self.CV.predict(state_a, dt=0.25)
        state_b = self.CV.predict(state_b, dt=10.0)
        assert state_a.position.x == pytest.approx(state_b.position.x, abs=1e-9)

    def test_ca_known_values(self):
        """CA: x(t) = x0 + v0*t + a*t^2/2; v(t) = v0 + a*t."""
        state = KinematicState(
            position=Vector3D(x=0, y=0, z=0),
            velocity=Vector3D(x=10, y=0, z=0),
            acceleration=Vector3D(x=2, y=0, z=0),
            timestamp=0.0,
        )
        state = self.CA.predict(state, dt=5.0)
        # x = 0 + 10*5 + 0.5*2*25 = 75
        assert state.position.x == pytest.approx(75.0, abs=1e-9)
        # v = 10 + 2*5 = 20
        assert state.velocity.x == pytest.approx(20.0, abs=1e-9)
        # acceleration unchanged
        assert state.acceleration.x == pytest.approx(2.0, abs=1e-9)

    def test_cv_state_transition_matrix_fixture(self):
        """Pinned F matrix entries for CV model at dt = 0.5 s."""
        F = self.CV.get_state_transition_matrix(0.5)
        assert F[0, 3] == pytest.approx(0.5, abs=1e-12)
        assert F[1, 4] == pytest.approx(0.5, abs=1e-12)
        assert F[2, 5] == pytest.approx(0.5, abs=1e-12)
        assert F[0, 0] == 1.0
        assert F[3, 3] == 1.0
        assert F[0, 6] == 0.0  # CV: no acceleration coupling

    def test_ca_state_transition_matrix_fixture(self):
        """Pinned F matrix entries for CA model at dt = 2 s."""
        F = self.CA.get_state_transition_matrix(2.0)
        assert F[0, 3] == pytest.approx(2.0, abs=1e-12)
        assert F[0, 6] == pytest.approx(2.0, abs=1e-12)  # dt^2/2 = 2
        assert F[3, 6] == pytest.approx(2.0, abs=1e-12)
        assert F[6, 6] == 1.0

    def test_cv_process_noise_fixture(self):
        """Pinned Q entries: white-noise-acceleration model, q = 0.1, dt = 1."""
        Q = self.CV.get_process_noise_matrix(1.0, {"process_noise": 0.1})
        assert Q[0, 0] == pytest.approx(0.1 * 1.0 / 4.0, abs=1e-12)
        assert Q[0, 3] == pytest.approx(0.1 * 1.0 / 2.0, abs=1e-12)
        assert Q[3, 3] == pytest.approx(0.1, abs=1e-12)
        np.testing.assert_allclose(Q, Q.T, atol=1e-12)


class TestKalmanRegression:
    """Deterministic Kalman-filter fixtures."""

    def _initialized_filter(self) -> KalmanFilter:
        kf = KalmanFilter(config=KalmanFilterConfig())
        kf.initialize(
            initial_position=Vector3D(x=0, y=1000, z=100),
            initial_velocity=Vector3D(x=100, y=0, z=0),
            timestamp=0.0,
            track_id="regression",
        )
        return kf

    def test_perfect_measurement_keeps_state(self):
        """A noiseless measurement equal to the prediction cannot move the state."""
        kf = self._initialized_filter()
        kf.predict(1.0)
        predicted = kf.x.copy()
        kf.update(
            Vector3D(x=predicted[0], y=predicted[1], z=predicted[2]),
            Matrix3x3.diagonal([1e-6, 1e-6, 1e-6]),
            "s1",
        )
        np.testing.assert_allclose(kf.x, predicted, atol=1e-3)

    def test_update_reduces_covariance_monotonically(self):
        """Repeated updates with small measurement noise shrink position variance."""
        kf = self._initialized_filter()
        traces = [float(np.trace(kf.P[0:3, 0:3]))]
        for i in range(5):
            kf.predict(1.0)
            kf.update(
                Vector3D(x=100 * (i + 1), y=1000, z=100),
                Matrix3x3.diagonal([100, 100, 25]),
                "s1",
            )
            traces.append(float(np.trace(kf.P[0:3, 0:3])))
        assert traces[-1] < traces[0]

    def test_gating_rejects_outlier_regression(self):
        """Observation 10 km away is rejected by the default 9.21 gate."""
        kf = self._initialized_filter()
        accepted = kf.update(
            Vector3D(x=10000, y=1000, z=100),
            Matrix3x3.diagonal([100, 100, 25]),
            "s1",
        )
        assert accepted is False
        assert kf.coast_steps == 1

    def test_velocity_converges_to_truth(self):
        """After 25 measurements, velocity error < 1 m/s.

        The filter is initialized with a rough velocity (35 m/s vs 40 m/s
        truth) so measurements remain inside the association gate while
        the estimate converges.
        """
        kf = KalmanFilter(config=KalmanFilterConfig())
        kf.initialize(
            initial_position=Vector3D(x=0, y=0, z=0),
            initial_velocity=Vector3D(x=35, y=0, z=0),
            timestamp=0.0,
            track_id="velocity_fit",
        )
        for i in range(1, 26):
            kf.predict(1.0)
            accepted = kf.update(
                Vector3D(x=40 * i, y=0, z=0),
                Matrix3x3.diagonal([100, 100, 25]),
                "s1",
            )
            assert accepted, f"measurement at step {i} unexpectedly rejected"
        assert abs(kf.x[3] - 40.0) < 1.0


class TestSensorNoiseRegression:
    """Deterministic synthetic-sensor noise fixtures."""

    def test_seeded_radar_noise_is_reproducible(self):
        """Same seed must reproduce identical measurements bit-for-bit."""
        from nados.domain import SensorDefinition, SensorType
        from nados.sensors.models import RadarModel

        sensor = SensorDefinition(
            sensor_id="reg_radar",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.diagonal([2500, 2500, 625]),
        )
        truth = Vector3D(x=20000, y=5000, z=1000)

        runs = []
        for _ in range(2):
            model = RadarModel(sensor)
            model.set_random_seed(99)
            obs = model.generate_observation(truth, Vector3D(x=150, y=0, z=0), 1.0, "t1")
            runs.append((obs.measured_position.x, obs.measured_position.y))

        assert runs[0] == runs[1]

    def test_radar_out_of_range_is_stable(self):
        """Target beyond 200 km is consistently OUT_OF_RANGE."""
        from nados.domain import SensorDefinition, SensorType, ValidityStatus
        from nados.sensors.models import RadarModel

        sensor = SensorDefinition(
            sensor_id="far_radar",
            sensor_type=SensorType.RADAR,
            simulated_position=Vector3D(),
            sampling_interval=1.0,
            measurement_noise=Matrix3x3.identity(),
        )
        model = RadarModel(sensor)
        model.set_random_seed(1)
        obs = model.generate_observation(Vector3D(x=300000, y=0, z=0), Vector3D(), 1.0, "far_target")
        assert obs.validity_status == ValidityStatus.OUT_OF_RANGE


class TestScenarioReproducibilityRegression:
    """Whole-scenario determinism fixtures."""

    def test_basic_scenario_seed_reproducibility(self):
        """Two engines on the same scenario/seed produce identical object states."""
        from nados.orchestration.scenario_loader import load_scenario
        from nados.simulation import SimulationEngine

        scenario = load_scenario("scenarios/basic_tracking.json")
        positions = []
        for _ in range(2):
            engine = SimulationEngine(scenario, random_seed=scenario.random_seed)
            engine.start()
            for _ in range(20):
                engine.step()
            positions.append([engine.get_object_position("target_001").x, engine.get_object_position("target_001").y])
        assert positions[0] == positions[1]

    def test_basic_scenario_object_moves_east(self):
        """target_001 moves east at 250 m/s; after 20 steps of 0.1 s -> x = 500 m."""
        from nados.orchestration.scenario_loader import load_scenario
        from nados.simulation import SimulationEngine

        scenario = load_scenario("scenarios/basic_tracking.json")
        engine = SimulationEngine(scenario)
        engine.start()
        for _ in range(20):
            engine.step()
        pos = engine.get_object_position("target_001")
        assert pos.x == pytest.approx(250 * 0.1 * 20, abs=1.0)
        assert pos.y == pytest.approx(50000.0, abs=1.0)
