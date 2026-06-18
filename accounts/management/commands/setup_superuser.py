"""
Management command to create an initial superuser.

Credentials are resolved from (in order):
1. Command-line arguments
2. config.yaml superuser block
3. DJANGO_SUPERUSER_* environment variables
4. Interactive prompts (unless --no-input)
"""

from __future__ import annotations

import getpass
import os
import sys
from argparse import ArgumentParser
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    """Create an initial superuser from config, environment, or interactively."""

    help = "Create an initial superuser from config, environment, or interactively"

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register CLI flags for superuser credentials."""
        parser.add_argument(
            "--email",
            help="Email address for the superuser",
        )
        parser.add_argument(
            "--username",
            help="Username for the superuser",
        )
        parser.add_argument(
            "--password",
            help="Password for the superuser",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for input (requires config, env vars, or command args)",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Resolve credentials and create the superuser if it does not exist."""
        email: str | None = options.get("email")
        username: str | None = options.get("username")
        password: str | None = options.get("password")

        if not email or not username or not password:
            try:
                from budget_tracker.config import get_superuser_config

                config = get_superuser_config()
                email = email or config.get("email")
                username = username or config.get("username")
                password = password or config.get("password")
            except ImportError:
                pass

        email = email or os.getenv("DJANGO_SUPERUSER_EMAIL")
        username = username or os.getenv("DJANGO_SUPERUSER_USERNAME")
        password = password or os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if email and User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"User with email {email} already exists. Skipping creation.")
            )
            return

        if not options.get("no_input"):
            if not email:
                email = input("Email: ")
            if not username:
                username = input("Username: ")
            if not password:
                password = getpass.getpass("Password: ")
                password2 = getpass.getpass("Password (again): ")
                if password != password2:
                    raise CommandError("Passwords do not match.")

        if not email or not username or not password:
            raise CommandError(
                "Email, username, and password are required. "
                "Provide them via config.yaml, environment variables, "
                "command arguments, or interactively."
            )

        try:
            user: AbstractBaseUser = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created superuser: {user.email}")
            )
        except Exception as exc:
            raise CommandError(f"Error creating superuser: {exc}") from exc
