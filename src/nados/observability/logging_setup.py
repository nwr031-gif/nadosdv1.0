"""
Structured logging setup for NADOS Dv1.0.
"""

import logging
import logging.config
import logging.handlers
from pathlib import Path
from typing import Any

import yaml

from nados.config import get_config


def setup_logging(config_path: str | None = None) -> None:
    """Set up application logging from configuration."""

    # Get logging config from app config
    app_config = get_config()
    log_config = app_config.logging

    # Ensure log directory exists
    log_dir = Path(log_config.directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build logging configuration dict
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": log_config.format,
                "datefmt": log_config.date_format,
            },
            "detailed": {
                "format": "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(funcName)s | %(message)s",
                "datefmt": log_config.date_format,
            },
            "json": {
                "format": (
                    '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                    '"logger": "%(name)s", "line": %(lineno)d, '
                    '"function": "%(funcName)s", "message": "%(message)s"}'
                ),
                "datefmt": log_config.date_format,
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_config.level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_dir / "nados.log"),
                "maxBytes": log_config.max_bytes,
                "backupCount": log_config.backup_count,
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(log_dir / "nados_errors.log"),
                "maxBytes": log_config.max_bytes,
                "backupCount": log_config.backup_count,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "nados": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "nados.simulation": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "nados.tracking": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "nados.ui": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_config.level,
            "handlers": ["console", "file", "error_file"],
        },
    }

    # Load from YAML if provided
    if config_path and Path(config_path).exists():
        with open(config_path, encoding="utf-8") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                logging_config.update(yaml_config)

    logging.config.dictConfig(logging_config)


class LoggingContext:
    """Context manager for adding contextual information to logs."""

    def __init__(self, **context: Any) -> None:
        self.context = context
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self) -> "LoggingContext":
        def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
            record = self.old_factory(*args, **kwargs)
            for key, value in self.context.items():
                setattr(record, key, value)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        logging.setLogRecordFactory(self.old_factory)


_logger_cache: dict[str, logging.Logger] = {}


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with caching."""
    if name not in _logger_cache:
        _logger_cache[name] = logging.getLogger(f"nados.{name}")
    return _logger_cache[name]
