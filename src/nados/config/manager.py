"""
Configuration manager for loading and accessing application configuration.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import ValidationError

from .models import AppConfig, DatabaseConfig, LoggingConfig, SimulationConfig, VisualizationConfig


class ConfigManager:
    """Manages application configuration loading and access."""
    
    _instance: Optional["ConfigManager"] = None
    _config: Optional[AppConfig] = None
    
    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if self._config is None:
            self._config = self._load_default_config()
    
    def _load_default_config(self) -> AppConfig:
        """Load default configuration."""
        return AppConfig()
    
    def load_from_file(self, config_path: str) -> AppConfig:
        """Load configuration from YAML file."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        # Apply environment variable overrides
        data = self._apply_env_overrides(data)
        
        try:
            self._config = AppConfig(**data)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration: {e}")
        
        return self._config
    
    def _apply_env_overrides(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides to configuration."""
        env_mappings = {
            "NADOS_DEBUG": ("debug", lambda x: x.lower() == "true"),
            "NADOS_LANGUAGE": ("language", str),
            "NADOS_THEME": ("theme", str),
            "NADOS_DB_PATH": ("database.path", str),
            "NADOS_DB_ECHO": ("database.echo", lambda x: x.lower() == "true"),
            "NADOS_DEFAULT_SEED": ("simulation.default_seed", int),
            "NADOS_MAX_DURATION": ("simulation.max_duration_seconds", int),
            "NADOS_ENABLE_3D": ("visualization.enable_3d", lambda x: x.lower() == "true"),
            "NADOS_LOG_LEVEL": ("logging.level", str),
            "NADOS_LOG_DIR": ("logging.directory", str),
        }
        
        for env_var, (config_path, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested(data, config_path, converter(value))
        
        return data
    
    def _set_nested(self, data: Dict[str, Any], path: str, value: Any) -> None:
        """Set nested dictionary value using dot notation path."""
        keys = path.split(".")
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value
    
    def get_config(self) -> AppConfig:
        """Get the current configuration."""
        if self._config is None:
            self._config = self._load_default_config()
        return self._config
    
    def update_config(self, updates: Dict[str, Any]) -> AppConfig:
        """Update configuration with new values."""
        if self._config is None:
            self._config = self._load_default_config()
        
        current_dict = self._config.model_dump()
        current_dict.update(updates)
        
        try:
            self._config = AppConfig(**current_dict)
        except ValidationError as e:
            raise ValueError(f"Invalid configuration update: {e}")
        
        return self._config


# Global instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> AppConfig:
    """Get the current application configuration."""
    return get_config_manager().get_config()


def load_config(config_path: str) -> AppConfig:
    """Load configuration from file."""
    return get_config_manager().load_from_file(config_path)