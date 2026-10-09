"""
Observation generator coordinating multiple sensors.
"""

from typing import Dict, List, Optional

from nados.domain import SensorDefinition, SensorObservation, VirtualObject
from nados.simulation.motion import KinematicState
from .models import SensorModel, create_sensor_model, SensorNoiseParams


class ObservationGenerator:
    """Generates observations from multiple sensors for multiple objects."""
    
    def __init__(
        self,
        sensor_defs: List[SensorDefinition],
        object_states: Dict[str, KinematicState],
        random_seed: int = 42,
        noise_params: Optional[Dict[str, SensorNoiseParams]] = None,
    ) -> None:
        self.sensor_defs = {s.sensor_id: s for s in sensor_defs}
        self.object_states = object_states
        self.random_seed = random_seed
        self.noise_params = noise_params or {}
        
        # Create sensor models
        self.sensor_models: Dict[str, SensorModel] = {}
        for sensor_id, sensor_def in self.sensor_defs.items():
            params = self.noise_params.get(sensor_id)
            self.sensor_models[sensor_id] = create_sensor_model(sensor_def, params)
            self.sensor_models[sensor_id].set_random_seed(random_seed + hash(sensor_id) % 2**32)
    
    def generate_all_observations(self, timestamp: float) -> Dict[str, List[SensorObservation]]:
        """Generate observations from all sensors for all objects."""
        all_observations: Dict[str, List[SensorObservation]] = {}
        
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
    
    def generate_observations_for_sensor(self, sensor_id: str, timestamp: float) -> List[SensorObservation]:
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
    
    def get_sensor_model(self, sensor_id: str) -> Optional[SensorModel]:
        """Get sensor model by ID."""
        return self.sensor_models.get(sensor_id)