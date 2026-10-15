"""Django app configuration for budgetapp."""

from __future__ import annotations

from django.apps import AppConfig


class BudgetappConfig(AppConfig):
    """Application config of the budget app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "budgetapp"
