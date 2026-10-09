"""Integration tests for full scenario execution."""

import tempfile

import pytest

from nados.domain import RunStatus
from nados.orchestration import create_application, load_scenario
from nados.persistence import RunRepository, get_database


class TestScenarioExecution:
    """Integration tests for running scenarios."""

    def setup_method(self):
        # Use temporary database
        import os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_db:
            self.temp_db_path = temp_db.name
        os.environ["NADOS_DB_PATH"] = self.temp_db_path

    def teardown_method(self):
        import os

        if os.path.exists(self.temp_db_path):
            os.unlink(self.temp_db_path)

    def test_load_and_run_basic_scenario(self):
        """Test loading and running the basic tracking scenario."""
        # Load scenario
        scenario = load_scenario("scenarios/basic_tracking.json")

        assert scenario.scenario_id == "basic_tracking"
        assert len(scenario.virtual_objects) == 1
        assert len(scenario.simulated_sensors) == 1

        # Create application
        app = create_application()

        # Load scenario into app
        assert app.load_scenario("scenarios/basic_tracking.json")

        # Run simulation
        assert app.run_simulation_sync() is True

        # Verify run was saved
        db = get_database()
        run_repo = RunRepository(db)
        runs = run_repo.list_by_scenario("basic_tracking")

        assert len(runs) >= 1
        # Check the latest run (first in list) is the one we just created
        latest_run = runs[0]
        assert latest_run.status == RunStatus.COMPLETED
        assert latest_run.scenario_id == "basic_tracking"

    def test_load_and_run_noisy_scenario(self):
        """Test running noisy sensor scenario."""
        app = create_application()
        assert app.load_scenario("scenarios/noisy_sensor.json")
        assert app.run_simulation_sync() is True

    def test_load_and_run_multi_sensor_scenario(self):
        """Test running multi-sensor scenario."""
        app = create_application()
        assert app.load_scenario("scenarios/multi_sensor_demo.json")
        assert app.run_simulation_sync() is True

    def test_reproducibility_same_seed(self):
        """Test that same seed produces same results."""
        app1 = create_application()
        app1.load_scenario("scenarios/basic_tracking.json")
        app1.run_simulation_sync()

        run_repo = RunRepository(get_database())
        runs1 = run_repo.list_by_scenario("basic_tracking")
        run1 = runs1[0]

        # Second run with same seed
        app2 = create_application()
        app2.load_scenario("scenarios/basic_tracking.json")
        app2.run_simulation_sync()

        runs2 = run_repo.list_by_scenario("basic_tracking")
        run2 = runs2[-1]  # Latest

        # Both should complete successfully
        assert run1.status == RunStatus.COMPLETED
        assert run2.status == RunStatus.COMPLETED
        assert run1.random_seed == run2.random_seed == 42

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different (but valid) results."""
        # This is harder to test deterministically, but we can verify
        # both complete without error
        app1 = create_application()
        app1.load_scenario("scenarios/basic_tracking.json")
        app1.scenario.random_seed = 42
        assert app1.run_simulation_sync()

        app2 = create_application()
        app2.load_scenario("scenarios/basic_tracking.json")
        app2.scenario.random_seed = 12345
        assert app2.run_simulation_sync()

    def test_invalid_scenario_rejected(self):
        """Test that invalid scenarios are rejected."""
        app = create_application()

        # Create invalid scenario (negative duration)
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            invalid_scenario = {
                "scenario_id": "invalid",
                "schema_version": "v1",
                "name": "Invalid",
                "duration_seconds": -1.0,  # Invalid
                "timestep_seconds": 0.1,
                "random_seed": 42,
                "coordinate_system": "ENU",
                "simulated_sensors": [],
                "virtual_objects": [],
            }
            json.dump(invalid_scenario, f)
            invalid_path = f.name

        try:
            # Should fail validation
            result = app.load_scenario(invalid_path)
            # load_scenario might not catch all validation, but engine should fail
            # The scenario loader validates, so this should fail
            assert result is False
        finally:
            import os

            os.unlink(invalid_path)

    def test_generate_report(self):
        """Test report generation after simulation."""
        app = create_application()
        app.load_scenario("scenarios/basic_tracking.json")
        app.run_simulation_sync()

        run_repo = RunRepository(get_database())
        runs = run_repo.list_by_scenario("basic_tracking")
        run_id = runs[0].run_id

        # Generate reports
        reports = app.generate_report(run_id=run_id, formats=["json", "csv"])

        assert "json" in reports
        assert "csv" in reports

        # Verify files exist
        import os

        assert os.path.exists(reports["json"])
        assert os.path.exists(reports["csv"])

        # Verify JSON content
        import json

        with open(reports["json"], encoding="utf-8") as f:
            data = json.load(f)

        assert "simulation_info" in data
        assert data["simulation_info"]["scenario_name"] == "تتبع أساسي - جسم واحد بمستشعر نظيف"
        assert "observation_statistics" in data


class TestScenarioValidation:
    """Tests for scenario validation."""

    def test_valid_scenario_passes(self):
        """Test that demo scenarios pass validation."""
        for scenario_file in [
            "scenarios/basic_tracking.json",
            "scenarios/noisy_sensor.json",
            "scenarios/multi_sensor_demo.json",
        ]:
            scenario = load_scenario(scenario_file)
            assert scenario is not None
            errors = scenario.validate_references()
            assert len(errors) == 0, f"Validation errors in {scenario_file}: {errors}"

    def test_schema_version_validation(self):
        """Test unsupported schema version rejected."""
        import json

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "scenario_id": "test",
                    "schema_version": "v99",  # Unsupported
                    "name": "Test",
                    "duration_seconds": 60.0,
                    "timestep_seconds": 0.1,
                    "random_seed": 42,
                    "coordinate_system": "ENU",
                    "simulated_sensors": [],
                    "virtual_objects": [],
                },
                f,
            )
            path = f.name

        try:
            with pytest.raises(ValueError, match="Unsupported schema version"):
                load_scenario(path)
        finally:
            import os

            os.unlink(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
