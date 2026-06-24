"""
Configuration loader for monAI Budget Tracker.

This module loads settings from config.yaml and provides them to the rest of the application.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in ("true", "1", "yes")


def _require_secret_key() -> str:
    """Return SECRET_KEY from the environment or raise a clear error."""
    secret_key = os.getenv("SECRET_KEY", "").strip()
    if not secret_key:
        raise ValueError(
            "SECRET_KEY is required. Set it in config.yaml (app.secret_key) or the "
            "SECRET_KEY environment variable."
        )
    return secret_key


def load_config() -> dict[str, Any]:
    """
    Load configuration from config.yaml file.

    Returns:
        dict: Configuration dictionary

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        yaml.YAMLError: If config.yaml has invalid syntax
    """
    config_path = BASE_DIR / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please create config.yaml from the template."
        )

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_config_value(
    config: dict[str, Any],
    *keys: str,
    default: Any = None,
) -> Any:
    """
    Safely get a nested configuration value.

    Args:
        config: Configuration dictionary
        *keys: Nested keys to traverse
        default: Default value if key not found

    Returns:
        The configuration value or default
    """
    value: Any = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


def _validate_app_secret(app_config: dict[str, Any]) -> None:
    """Ensure secret_key is set when running in production mode."""
    debug = app_config.get("debug", False)
    if debug:
        return
    secret_key = app_config.get("secret_key", "")
    if not secret_key or secret_key == "change-me-use-a-long-random-string-in-production":
        raise ValueError(
            "app.secret_key in config.yaml must be set to a unique random string "
            "before running with debug: false."
        )


# Load configuration at module import time
try:
    CONFIG = load_config()
    _validate_app_secret(CONFIG.get("app", {}))
except FileNotFoundError:
    # Provide defaults for initial setup / migrations (e.g. Render without config.yaml)
    _allowed = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    _hosts = [h.strip() for h in _allowed.split(",") if h.strip()]
    if not _hosts:
        _hosts = ["localhost", "127.0.0.1"]
    _debug = _env_bool("DEBUG", default=False)
    CONFIG = {
        "app": {
            "name": "monAI",
            "debug": _debug,
            "secret_key": _require_secret_key(),
        },
        "server": {
            "allowed_hosts": _hosts,
            "timezone": os.getenv("TIMEZONE", "Asia/Karachi"),
        },
        "urls": {
            "local": "http://localhost:8000",
            "ngrok": "",
        },
        "database": {
            "engine": "mysql",
            "name": "monai",
            "user": "root",
            "password": "",
            "host": "127.0.0.1",
            "port": 3306,
        },
        "celery": {
            "broker_url": "redis://localhost:6379/0",
            "result_backend": "redis://localhost:6379/0",
        },
        "redis": {
            "cache_url": "redis://localhost:6379/1",
            "cache_timeout_seconds": 3600,
        },
        "email": {
            "backend": "console",
        },
        "superuser": {
            "email": "",
            "username": "",
            "password": "",
        },
    }


# Convenience accessors
def get_app_config() -> dict[str, Any]:
    """Get application configuration."""
    return CONFIG.get("app", {})


def get_server_config() -> dict[str, Any]:
    """Get server configuration."""
    return CONFIG.get("server", {})


def get_urls_config() -> dict[str, Any]:
    """Get URLs configuration for CSRF trusted origins (ngrok / LAN dev)."""
    return CONFIG.get("urls", {})


def get_database_config() -> dict[str, Any]:
    """Get database configuration."""
    return CONFIG.get("database", {})


def get_celery_config() -> dict[str, Any]:
    """Get Celery configuration."""
    return CONFIG.get("celery", {})


def get_redis_config() -> dict[str, Any]:
    """Get Redis configuration (Django cache backend)."""
    return CONFIG.get("redis", {})


def get_email_config() -> dict[str, Any]:
    """Get email configuration."""
    return CONFIG.get("email", {})


def get_superuser_config() -> dict[str, Any]:
    """Get initial superuser configuration."""
    return CONFIG.get("superuser", {})
