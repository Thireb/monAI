"""
Management command wrapper for building Android APKs.

This command wraps the scripts/build_apks.py script to build APKs
for the Capacitor Android app with different server configurations.

Usage:
    python manage.py build_apk              # Build both local and ngrok APKs
    python manage.py build_apk --local      # Build only localhost APK
    python manage.py build_apk --ngrok      # Build only ngrok APK
    python manage.py build_apk --check      # Check configuration only
"""

import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BUILD_SCRIPT = BASE_DIR / "scripts" / "build_apks.py"
CAPACITOR_DIR = BASE_DIR / "capacitor-app"


class Command(BaseCommand):
    help = "Build Android APKs for the Capacitor app"

    def add_arguments(self, parser):
        parser.add_argument(
            "--local",
            action="store_true",
            help="Build only the localhost APK",
        )
        parser.add_argument(
            "--ngrok",
            action="store_true",
            help="Build only the ngrok APK",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Only check configuration without building",
        )

    def check_prerequisites(self):
        """Check that all prerequisites are in place."""
        errors = []

        # Check build script exists
        if not BUILD_SCRIPT.exists():
            errors.append(f"Build script not found: {BUILD_SCRIPT}")

        # Check capacitor directory exists
        if not CAPACITOR_DIR.exists():
            errors.append(f"Capacitor directory not found: {CAPACITOR_DIR}")

        # Check config.yaml exists
        config_file = BASE_DIR / "config.yaml"
        if not config_file.exists():
            errors.append(
                f"Config file not found: {config_file}\n"
                "  Create config.yaml with your URLs configuration."
            )

        # Check Android directory exists
        android_dir = CAPACITOR_DIR / "android"
        if not android_dir.exists():
            errors.append(
                f"Android directory not found: {android_dir}\n"
                "  Run 'cd capacitor-app && npx cap add android' first."
            )

        return errors

    def show_configuration(self):
        """Show current APK build configuration."""
        try:
            import yaml

            config_file = BASE_DIR / "config.yaml"
            if config_file.exists():
                with open(config_file, encoding="utf-8") as f:
                    config = yaml.safe_load(f)

                urls = config.get("urls", {})
                self.stdout.write("\n📋 Current Configuration:")
                self.stdout.write(f"  Local URL:  {urls.get('local', '(not set)')}")
                self.stdout.write(f"  Ngrok URL:  {urls.get('ngrok', '(not set)')}")
                self.stdout.write("")
            else:
                self.stdout.write(
                    self.style.WARNING("\n⚠️  No config.yaml found - using defaults")
                )
        except ImportError:
            self.stdout.write(
                self.style.WARNING("\n⚠️  pyyaml not installed - cannot read config")
            )

    def handle(self, *args, **options):
        build_local = options.get("local")
        build_ngrok = options.get("ngrok")
        check_only = options.get("check")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("📱 monAI APK Builder"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        # Check prerequisites
        errors = self.check_prerequisites()
        if errors:
            self.stdout.write(self.style.ERROR("\n❌ Prerequisites check failed:"))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  • {error}"))
            self.stdout.write("")
            raise CommandError("Prerequisites not met. Fix the issues above and try again.")

        self.stdout.write(self.style.SUCCESS("\n✅ Prerequisites check passed"))

        # Show configuration
        self.show_configuration()

        if check_only:
            self.stdout.write(self.style.SUCCESS("Check complete. Ready to build."))
            self.stdout.write("")
            return

        # Build command
        cmd = [sys.executable, str(BUILD_SCRIPT)]
        if build_local and not build_ngrok:
            cmd.append("--local")
            self.stdout.write("Building: localhost APK only")
        elif build_ngrok and not build_local:
            cmd.append("--ngrok")
            self.stdout.write("Building: ngrok APK only")
        else:
            self.stdout.write("Building: both localhost and ngrok APKs")

        self.stdout.write("")

        # Run the build script
        try:
            result = subprocess.run(
                cmd,
                cwd=BASE_DIR,
                capture_output=False,  # Let output stream directly
                text=True,
            )

            if result.returncode != 0:
                raise CommandError(f"Build failed with exit code {result.returncode}")

        except FileNotFoundError:
            raise CommandError(
                "Python executable not found. Make sure Python is in your PATH."
            )
        except subprocess.SubprocessError as e:
            raise CommandError(f"Build process error: {e}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("✅ APK build command completed"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

