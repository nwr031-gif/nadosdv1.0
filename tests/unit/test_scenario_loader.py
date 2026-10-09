"""Unit tests for scenario loader and validation."""

import json
import os
import tempfile

import pytest

from nados.domain import SimulationScenario
from nados.orchestration.scenario_loader import (
    create_demo_scenario,
    load_scenario,
    validate_scenario_file,
)


class TestLoadScenario:
    """Tests for load_scenario."""

    def test_load_basic_tracking(self):
        scenario = load_scenario("scenarios/basic_tracking.json")
        assert scenario.scenario_id == "basic_tracking"
        assert scenario.duration_seconds == 60.0
        assert scenario.random_seed == 42
        assert len(scenario.virtual_objects) == 1
        assert len(scenario.simulated_sensors) == 1

    def test_load_noisy_sensor(self):
        scenario = load_scenario("scenarios/noisy_sensor.json")
        assert scenario.scenario_id == "noisy_sensor"
        assert scenario.random_seed == 12345
        assert scenario.duration_seconds == 120.0

    def test_load_multi_sensor(self):
        scenario = load_scenario("scenarios/multi_sensor_demo.json")
        assert scenario.scenario_id == "multi_sensor_demo"
        assert len(scenario.simulated_sensors) == 3
        assert scenario.random_seed == 98765

    def test_load_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_scenario("scenarios/does_not_exist.json")

    def test_load_invalid_json_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{invalid json content")
            path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                load_scenario(path)
        finally:
            os.unlink(path)

    def test_load_scenario_with_duplicate_ids_fails(self):
        data = {
            "scenario_id": "dup_test",
            "schema_version": "v1",
            "name": "Duplicate Test",
            "duration_seconds": 10.0,
            "timestep_seconds": 0.1,
            "random_seed": 1,
            "coordinate_system": "ENU",
            "virtual_objects": [
                {
                    "object_id": "obj_1",
                    "object_type": "generic",
                    "initial_position": {"x": 0, "y": 0, "z": 0},
                    "initial_velocity": {"x": 0, "y": 0, "z": 0},
                    "initial_acceleration": {"x": 0, "y": 0, "z": 0},
                    "dimensions": {"x": 1, "y": 1, "z": 1},
                    "simulation_enabled": True,
                },
                {
                    "object_id": "obj_1",
                    "object_type": "generic",
                    "initial_position": {"x": 5, "y": 0, "z": 0},
                    "initial_velocity": {"x": 0, "y": 0, "z": 0},
                    "initial_acceleration": {"x": 0, "y": 0, "z": 0},
                    "dimensions": {"x": 1, "y": 1, "z": 1},
                    "simulation_enabled": True,
                },
            ],
            "simulated_sensors": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            with pytest.raises(ValueError, match="Duplicate"):
                load_scenario(path)
        finally:
            os.unlink(path)


class TestValidateScenarioFile:
    """Tests for validate_scenario_file."""

    def test_valid_scenario_no_errors(self):
        errors = validate_scenario_file("scenarios/basic_tracking.json")
        assert errors == []

    def test_all_demo_scenarios_valid(self):
        for name in ("basic_tracking", "noisy_sensor", "multi_sensor_demo"):
            errors = validate_scenario_file(f"scenarios/{name}.json")
            assert errors == [], f"Unexpected errors in {name}: {errors}"

    def test_missing_file_reports_error(self):
        errors = validate_scenario_file("scenarios/missing.json")
        assert any("not found" in e.lower() for e in errors)

    def test_missing_required_fields(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"scenario_id": "incomplete"}, f)
            path = f.name
        try:
            errors = validate_scenario_file(path)
            assert any("Missing required field" in e for e in errors)
            assert len(errors) >= 5  # Many required fields are missing
        finally:
            os.unlink(path)

    def test_invalid_duration(self):
        data = {
            "scenario_id": "negdur",
            "schema_version": "v1",
            "name": "Negative Duration",
            "duration_seconds": -5.0,
            "timestep_seconds": 0.1,
            "random_seed": 1,
            "coordinate_system": "ENU",
            "simulated_sensors": [],
            "virtual_objects": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            errors = validate_scenario_file(path)
            assert any("duration_seconds" in e for e in errors)
        finally:
            os.unlink(path)

    def test_invalid_seed(self):
        data = {
            "scenario_id": "negseed",
            "schema_version": "v1",
            "name": "Negative Seed",
            "duration_seconds": 10.0,
            "timestep_seconds": 0.1,
            "random_seed": -1,
            "coordinate_system": "ENU",
            "simulated_sensors": [],
            "virtual_objects": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            errors = validate_scenario_file(path)
            assert any("random_seed" in e for e in errors)
        finally:
            os.unlink(path)

    def test_unsupported_schema_version(self):
        data = {
            "scenario_id": "badver",
            "schema_version": "v99",
            "name": "Bad Version",
            "duration_seconds": 10.0,
            "timestep_seconds": 0.1,
            "random_seed": 1,
            "coordinate_system": "ENU",
            "simulated_sensors": [],
            "virtual_objects": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            errors = validate_scenario_file(path)
            assert any("schema" in e.lower() for e in errors)
        finally:
            os.unlink(path)

    def test_duplicate_sensor_ids_detected(self):
        data = {
            "scenario_id": "dupsensors",
            "schema_version": "v1",
            "name": "Duplicate Sensors",
            "duration_seconds": 10.0,
            "timestep_seconds": 0.1,
            "random_seed": 1,
            "coordinate_system": "ENU",
            "simulated_sensors": [
                {
                    "sensor_id": "s1",
                    "sensor_type": "radar",
                    "simulated_position": {"x": 0, "y": 0, "z": 0},
                    "sampling_interval": 1.0,
                    "measurement_noise": {"data": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
                },
                {
                    "sensor_id": "s1",
                    "sensor_type": "radar",
                    "simulated_position": {"x": 1, "y": 0, "z": 0},
                    "sampling_interval": 1.0,
                    "measurement_noise": {"data": [[1, 0, 0], [0, 1, 0], [0, 0, 1]]},
                },
            ],
            "virtual_objects": [],
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump(data, f)
            path = f.name
        try:
            errors = validate_scenario_file(path)
            assert any("Duplicate sensor_id" in e for e in errors)
        finally:
            os.unlink(path)


class TestCreateDemoScenario:
    """Tests for create_demo_scenario factory."""

    def test_basic_type(self):
        scenario = create_demo_scenario("basic")
        assert isinstance(scenario, SimulationScenario)
        assert len(scenario.virtual_objects) == 1
        assert len(scenario.simulated_sensors) == 1

    def test_noisy_type(self):
        scenario = create_demo_scenario("noisy")
        assert isinstance(scenario, SimulationScenario)
        assert scenario.random_seed == 12345

    def test_multi_sensor_type(self):
        scenario = create_demo_scenario("multi_sensor")
        assert isinstance(scenario, SimulationScenario)
        assert len(scenario.simulated_sensors) == 3

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown scenario type"):
            create_demo_scenario("unknown_type")
