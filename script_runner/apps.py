"""Django app configuration for script_runner."""
from __future__ import annotations

from django.apps import AppConfig


class ScriptRunnerConfig(AppConfig):
    """Configuration for the script_runner Django application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "script_runner"
