"""
Run all scripts matching the current code version.

This command runs all scripts that are marked as run_on_deploy=True
and match the current CODE_VERSION from settings.

Usage:
    python manage.py run_scripts              # Run all version-matching scripts
    python manage.py run_scripts --dry-run    # Show what would run without executing
    python manage.py run_scripts --list       # List scripts that would run
"""

import io
import sys
import traceback
import uuid

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from script_runner.models import ScriptExecution
from script_runner.registry import get_scripts_for_version


class Command(BaseCommand):
    help = "Run all scripts matching the current code version"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would run without executing",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List scripts that would run for this version",
        )
        parser.add_argument(
            "--code-version",
            help="Override CODE_VERSION from settings",
        )
        parser.add_argument(
            "--continue-on-error",
            action="store_true",
            help="Continue running remaining scripts if one fails",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        list_only = options.get("list", False)
        continue_on_error = options.get("continue_on_error", False)

        # Get code version
        code_version = options.get("code_version") or getattr(settings, "CODE_VERSION", "1.0.0")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("🚀 monAI Script Runner"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"\nCode Version: {self.style.WARNING(code_version)}")

        # Get scripts for this version
        scripts = get_scripts_for_version(code_version, deploy_only=True)

        if not scripts:
            self.stdout.write(
                self.style.WARNING(
                    f"\nNo deploy scripts found for version {code_version}"
                )
            )
            return

        self.stdout.write(f"Scripts to run: {len(scripts)}\n")

        # List mode - just show what would run
        if list_only:
            self.stdout.write(self.style.HTTP_INFO("Scripts for this version:"))
            for i, script in enumerate(scripts, 1):
                version_range = ""
                if script.min_version or script.max_version:
                    version_range = f" [{script.min_version or '*'} - {script.max_version or '*'}]"
                self.stdout.write(
                    f"  {i}. {self.style.WARNING(script.name)}{version_range}"
                )
                self.stdout.write(f"      {script.description}")
            self.stdout.write("")
            return

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no scripts will be executed\n"))

        # Generate batch ID for this run
        batch_id = str(uuid.uuid4())[:8]
        self.stdout.write(f"Batch ID: {batch_id}\n")

        # Run each script
        results = {"success": 0, "failed": 0, "skipped": 0}

        for i, script in enumerate(scripts, 1):
            self.stdout.write("-" * 60)
            self.stdout.write(
                f"[{i}/{len(scripts)}] Running: {self.style.WARNING(script.name)}"
            )

            if dry_run:
                self.stdout.write(self.style.SUCCESS("  Would run (dry-run)"))
                results["skipped"] += 1
                continue

            # Create execution record
            execution = ScriptExecution.objects.create(
                script_name=script.name,
                code_version=code_version,
                batch_id=batch_id,
            )

            # Capture output
            output_buffer = io.StringIO()
            old_stdout = sys.stdout
            old_stderr = sys.stderr

            try:
                sys.stdout = output_buffer
                sys.stderr = output_buffer

                # Run the command
                call_command(script.name, stdout=output_buffer, stderr=output_buffer)

                sys.stdout = old_stdout
                sys.stderr = old_stderr

                output = output_buffer.getvalue()
                execution.mark_success(output)
                results["success"] += 1

                self.stdout.write(self.style.SUCCESS(f"  ✓ Completed ({execution.duration_seconds:.2f}s)"))

            except Exception as e:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

                error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
                execution.mark_failed(error_message)
                results["failed"] += 1

                self.stdout.write(self.style.ERROR(f"  ✗ Failed: {e}"))

                if not continue_on_error:
                    self.stdout.write(
                        self.style.ERROR(
                            "\nStopping due to error. Use --continue-on-error to keep going."
                        )
                    )
                    raise CommandError(f"Script '{script.name}' failed: {e}") from e

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("Summary:"))
        self.stdout.write(f"  ✓ Success: {results['success']}")
        if results["failed"]:
            self.stdout.write(self.style.ERROR(f"  ✗ Failed:  {results['failed']}"))
        if results["skipped"]:
            self.stdout.write(f"  ⊘ Skipped: {results['skipped']}")
        self.stdout.write(f"  Batch ID: {batch_id}")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        if results["failed"] and not continue_on_error:
            raise CommandError(f"{results['failed']} script(s) failed")

