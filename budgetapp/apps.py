"""Django app configuration for budgetapp."""

from __future__ import annotations

from django.apps import AppConfig


class BudgetappConfig(AppConfig):
    """Application config; wires model signals on startup."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "budgetapp"

    def ready(self) -> None:
        """Import signal handlers when Django loads the app."""
        import budgetapp.signals  # noqa: F401
