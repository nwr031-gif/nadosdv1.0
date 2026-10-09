"""Unit tests for configuration management."""

import os
import tempfile

import pytest
import yaml

from nados.config import AppConfig, ConfigManager, get_config, load_config
from nados.config.models import DatabaseConfig, SimulationConfig, VisualizationConfig


class TestAppConfig:
    """Tests for AppConfig model."""

    def test_defaults(self):
        config = AppConfig()
        assert config.name == "NADOS Dv1.0"
        assert config.version == "1.0.0"
        assert config.debug is False
        assert config.language == "ar"
        assert config.theme == "dark"

        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.simulation, SimulationConfig)
        assert isinstance(config.visualization, VisualizationConfig)

    def test_database_config(self):
        db = DatabaseConfig(path="custom.db", echo=True, pool_size=10)
        assert db.path == "custom.db"
        assert db.echo is True
        assert db.pool_size == 10

    def test_simulation_config_validation(self):
        with pytest.raises(ValueError):
            SimulationConfig(default_timestep=-0.1)

        with pytest.raises(ValueError):
            SimulationConfig(min_timestep=0.0)

    def test_extra_fields_ignored(self):
        config = AppConfig(extra_field="ignored")
        assert not hasattr(config, "extra_field")


class TestConfigManager:
    """Tests for ConfigManager."""

    def setup_method(self):
        # Reset singleton
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_singleton(self):
        mgr1 = ConfigManager()
        mgr2 = ConfigManager()
        assert mgr1 is mgr2

    def test_load_from_file(self):
        # Ensure NADOS_DB_PATH is not set from previous tests
        if "NADOS_DB_PATH" in os.environ:
            del os.environ["NADOS_DB_PATH"]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "name": "Test App",
                    "debug": True,
                    "database": {"path": "test.db", "echo": True},
                    "simulation": {"default_seed": 12345},
                },
                f,
            )
            config_path = f.name

        try:
            manager = ConfigManager()
            config = manager.load_from_file(config_path)

            assert config.name == "Test App"
            assert config.debug is True
            assert config.database.path == "test.db"
            assert config.database.echo is True
            assert config.simulation.default_seed == 12345
        finally:
            os.unlink(config_path)

    def test_env_overrides(self):
        os.environ["NADOS_DEBUG"] = "true"
        os.environ["NADOS_LANGUAGE"] = "en"
        os.environ["NADOS_DB_PATH"] = "/custom/path.db"

        try:
            manager = ConfigManager()
            config = manager._apply_env_overrides({})

            assert config.get("debug") is True
            assert config.get("language") == "en"
            assert config.get("database", {}).get("path") == "/custom/path.db"
        finally:
            del os.environ["NADOS_DEBUG"]
            del os.environ["NADOS_LANGUAGE"]
            del os.environ["NADOS_DB_PATH"]

    def test_get_config(self):
        manager = ConfigManager()
        config = manager.get_config()
        assert isinstance(config, AppConfig)

    def test_update_config(self):
        manager = ConfigManager()
        config = manager.update_config({"debug": True, "theme": "light"})
        assert config.debug is True
        assert config.theme == "light"


class TestGlobalFunctions:
    """Tests for global config functions."""

    def setup_method(self):
        ConfigManager._instance = None
        ConfigManager._config = None

    def test_get_config(self):
        config = get_config()
        assert isinstance(config, AppConfig)

    def test_load_config(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({"name": "Loaded App"}, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            assert config.name == "Loaded App"
        finally:
            os.unlink(config_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
