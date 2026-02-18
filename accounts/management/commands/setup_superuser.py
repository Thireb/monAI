"""
Management command to create an initial superuser.

This command can create a superuser from:
1. config.yaml settings (if superuser credentials are configured)
2. Environment variables (DJANGO_SUPERUSER_*)
3. Interactive prompts (if neither above is configured)
"""

import os
import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Create an initial superuser from config, environment, or interactively"

    def add_arguments(self, parser):
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

    def handle(self, *args, **options):
        # Try to get credentials from various sources
        email = options.get("email")
        username = options.get("username")
        password = options.get("password")

        # 1. Try config.yaml
        if not email or not username or not password:
            try:
                from budget_tracker.config import get_superuser_config

                config = get_superuser_config()
                email = email or config.get("email")
                username = username or config.get("username")
                password = password or config.get("password")
            except ImportError:
                pass

        # 2. Try environment variables
        email = email or os.getenv("DJANGO_SUPERUSER_EMAIL")
        username = username or os.getenv("DJANGO_SUPERUSER_USERNAME")
        password = password or os.getenv("DJANGO_SUPERUSER_PASSWORD")

        # 3. Check if user already exists
        if email and User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"User with email {email} already exists. Skipping creation.")
            )
            return

        # 4. Interactive mode if not all credentials available
        if not options.get("no_input"):
            if not email:
                email = input("Email: ")
            if not username:
                username = input("Username: ")
            if not password:
                import getpass

                password = getpass.getpass("Password: ")
                password2 = getpass.getpass("Password (again): ")
                if password != password2:
                    self.stderr.write(self.style.ERROR("Passwords do not match."))
                    sys.exit(1)

        # Validate required fields
        if not email or not username or not password:
            self.stderr.write(
                self.style.ERROR(
                    "Email, username, and password are required. "
                    "Provide them via config.yaml, environment variables, "
                    "command arguments, or interactively."
                )
            )
            sys.exit(1)

        # Create the superuser
        try:
            user = User.objects.create_superuser(
                email=email,
                username=username,
                password=password,
            )
            self.stdout.write(
                self.style.SUCCESS(f"Successfully created superuser: {user.email}")
            )
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating superuser: {e}"))
            sys.exit(1)

