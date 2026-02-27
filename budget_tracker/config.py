"""
Configuration loader for monAI Budget Tracker.

This module loads settings from config.yaml and provides them to the rest of the application.
"""

import os
from pathlib import Path

import yaml

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent


def load_config():
    """
    Load configuration from config.yaml file.

    Returns:
        dict: Configuration dictionary

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        yaml.YAMLError: If config.yaml has invalid syntax
    """
    config_path = BASE_DIR / "new_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Please create config.yaml from the template."
        )

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    return config


def get_config_value(config, *keys, default=None):
    """
    Safely get a nested configuration value.

    Args:
        config: Configuration dictionary
        *keys: Nested keys to traverse
        default: Default value if key not found

    Returns:
        The configuration value or default
    """
    value = config
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    return value


# Load configuration at module import time
try:
    CONFIG = load_config()
except FileNotFoundError:
    # Provide defaults for initial setup / migrations (e.g. Render without config.yaml)
    _allowed = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1")
    _hosts = [h.strip() for h in _allowed.split(",") if h.strip()]
    if not _hosts:
        _hosts = ["localhost", "127.0.0.1"]
    _debug = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")
    _resend_api_key = os.getenv("RESEND_API_KEY", "")
    CONFIG = {
        "app": {
            "name": "monAI",
            "debug": _debug,
            "secret_key": os.getenv(
                "SECRET_KEY",
                "django-insecure-fallback-key-for-development-only"
            ),
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
            "engine": "sqlite3",
            "name": "db.sqlite3",
        },
        "celery": {
            "broker_url": "redis://localhost:6379/0",
            "result_backend": "redis://localhost:6379/0",
        },
        "email": {
            "backend": "console",
            "resend": {
                "api_key": _resend_api_key,
                "from_email": os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"),
            },
        },
        "superuser": {
            "email": "",
            "username": "",
            "password": "",
        },
    }


# Convenience accessors
def get_app_config():
    """Get application configuration."""
    return CONFIG.get("app", {})


def get_server_config():
    """Get server configuration."""
    return CONFIG.get("server", {})


def get_urls_config():
    """Get URLs configuration for APK builds."""
    return CONFIG.get("urls", {})


def get_database_config():
    """Get database configuration."""
    return CONFIG.get("database", {})


def get_celery_config():
    """Get Celery configuration."""
    return CONFIG.get("celery", {})


def get_email_config():
    """Get email configuration."""
    return CONFIG.get("email", {})


def get_superuser_config():
    """Get initial superuser configuration."""
    return CONFIG.get("superuser", {})

