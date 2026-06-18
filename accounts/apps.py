"""Django app configuration for the accounts application."""

from __future__ import annotations

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Register the accounts app and its verbose name."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "User Accounts"
