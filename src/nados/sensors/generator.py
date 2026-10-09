"""
Observation generator coordinating multiple sensors.
"""

from nados.domain import SensorDefinition, SensorObservation
from nados.simulation.motion import KinematicState

from .models import SensorModel, SensorNoiseParams, create_sensor_model


class ObservationGenerator:
    """Generates observations from multiple sensors for multiple objects."""

    def __init__(
        self,
        sensor_defs: list[SensorDefinition],
        object_states: dict[str, KinematicState],
        random_seed: int = 42,
        noise_params: dict[str, SensorNoiseParams] | None = None,
    ) -> None:
        self.sensor_defs = {s.sensor_id: s for s in sensor_defs}
        self.object_states = object_states
        self.random_seed = random_seed
        self.noise_params = noise_params or {}

        # Create sensor models
        self.sensor_models: dict[str, SensorModel] = {}
        for sensor_id, sensor_def in self.sensor_defs.items():
            params = self.noise_params.get(sensor_id)
            self.sensor_models[sensor_id] = create_sensor_model(sensor_def, params)
            self.sensor_models[sensor_id].set_random_seed(random_seed + hash(sensor_id) % 2**32)

    def generate_all_observations(self, timestamp: float) -> dict[str, list[SensorObservation]]:
        """Generate observations from all sensors for all objects."""
        all_observations: dict[str, list[SensorObservation]] = {}

        for sensor_id, sensor_model in self.sensor_models.items():
            observations = []

            for obj_id, kinematic_state in self.object_states.items():
                obs = sensor_model.generate_observation(
                    true_position=kinematic_state.position,
                    true_velocity=kinematic_state.velocity,
                    timestamp=timestamp,
                    object_id=obj_id,
                )
                observations.append(obs)

            all_observations[sensor_id] = observations

        return all_observations

    def generate_observations_for_sensor(self, sensor_id: str, timestamp: float) -> list[SensorObservation]:
        """Generate observations for a specific sensor."""
        sensor_model = self.sensor_models.get(sensor_id)
        if not sensor_model:
            return []

        observations = []
        for obj_id, kinematic_state in self.object_states.items():
            obs = sensor_model.generate_observation(
                true_position=kinematic_state.position,
                true_velocity=kinematic_state.velocity,
                timestamp=timestamp,
                object_id=obj_id,
            )
            observations.append(obs)

        return observations

    def get_sensor_model(self, sensor_id: str) -> SensorModel | None:
        """Get sensor model by ID."""
        return self.sensor_models.get(sensor_id)
