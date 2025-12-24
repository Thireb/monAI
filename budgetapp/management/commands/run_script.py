"""
Centralized script runner with execution logging.

This command provides a single entry point to run various maintenance scripts
while tracking their execution history in the database.

Usage:
    python manage.py run_script                    # List available scripts
    python manage.py run_script <script_name>      # Run a specific script
    python manage.py run_script --history          # View execution history
    python manage.py run_script --history <name>   # View history for specific script

Examples:
    python manage.py run_script backup_data
    python manage.py run_script create_default_categories --user-email user@example.com
    python manage.py run_script --history backup_data
"""

import io
import sys
import traceback

from django.core.management import call_command, get_commands
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from budgetapp.models import ScriptExecution


# Registry of available scripts with descriptions
AVAILABLE_SCRIPTS = {
    # Build & Deploy
    "build_apk": {
        "description": "Build Android APKs for the Capacitor app",
        "category": "Build & Deploy",
        "example": "run_script build_apk -- --local",
    },
    # Data Management
    "backup_data": {
        "description": "Backup all budget-related data to JSON",
        "category": "Data Management",
        "example": "run_script backup_data -- --output my_backup.json",
    },
    "restore_data": {
        "description": "Restore data from a JSON backup file",
        "category": "Data Management",
        "example": "run_script restore_data -- backup.json",
    },
    # User Management
    "setup_superuser": {
        "description": "Create initial superuser from config or interactively",
        "category": "User Management",
        "example": "run_script setup_superuser",
    },
    "assign_data_to_user": {
        "description": "Assign orphaned data to a specific user",
        "category": "User Management",
        "example": "run_script assign_data_to_user --email user@example.com",
    },
    # Categories & Tags
    "create_default_categories": {
        "description": "Create default expense categories for users",
        "category": "Setup",
        "example": "run_script create_default_categories --all-users",
    },
    "create_tags_from_expenses": {
        "description": "Create tags from existing expense tag values",
        "category": "Migration",
        "example": "run_script create_tags_from_expenses",
    },
    "migrate_expense_tags_to_foreign_key": {
        "description": "Migrate expense tags to foreign key references",
        "category": "Migration",
        "example": "run_script migrate_expense_tags_to_foreign_key",
    },
    # Budget Management
    "archive_old_budgets": {
        "description": "Archive budgets from previous years",
        "category": "Maintenance",
        "example": "run_script archive_old_budgets",
    },
    "cleanup_budgets": {
        "description": "Cleanup empty or invalid budgets",
        "category": "Maintenance",
        "example": "run_script cleanup_budgets",
    },
    # Database
    "cleanup_migrations": {
        "description": "Drop database tables (DANGEROUS - development only)",
        "category": "Database",
        "example": "run_script cleanup_migrations --dry-run",
        "dangerous": True,
    },
}


class Command(BaseCommand):
    help = "Run maintenance scripts with execution logging"

    def add_arguments(self, parser):
        parser.add_argument(
            "script_name",
            nargs="?",
            help="Name of the script to run (omit to see list)",
        )
        parser.add_argument(
            "--history",
            action="store_true",
            help="View execution history instead of running",
        )
        parser.add_argument(
            "--history-limit",
            type=int,
            default=10,
            help="Number of history entries to show (default: 10)",
        )
        parser.add_argument(
            "--no-log",
            action="store_true",
            help="Don't log this execution to the database",
        )
        # Pass through any additional arguments to the target script
        parser.add_argument(
            "script_args",
            nargs="*",
            help="Arguments to pass to the script",
        )

    def print_available_scripts(self):
        """Print list of available scripts grouped by category."""
        self.stdout.write("\n" + self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Available Scripts"))
        self.stdout.write(self.style.SUCCESS("=" * 60))

        # Group scripts by category
        by_category = {}
        for name, info in AVAILABLE_SCRIPTS.items():
            category = info.get("category", "Other")
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((name, info))

        for category in sorted(by_category.keys()):
            self.stdout.write(f"\n{self.style.HTTP_INFO(category)}:")
            for name, info in sorted(by_category[category]):
                # Mark dangerous scripts
                danger = " ⚠️ DANGEROUS" if info.get("dangerous") else ""
                self.stdout.write(f"  {self.style.WARNING(name)}{danger}")
                self.stdout.write(f"      {info['description']}")
                self.stdout.write(f"      Example: python manage.py {info['example']}")

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("Usage: python manage.py run_script <script_name> [args...]")
        self.stdout.write("       python manage.py run_script --history [script_name]")
        self.stdout.write("")

    def print_history(self, script_name=None, limit=10):
        """Print execution history."""
        self.stdout.write("\n" + self.style.SUCCESS("=" * 60))
        if script_name:
            self.stdout.write(self.style.SUCCESS(f"Execution History: {script_name}"))
        else:
            self.stdout.write(self.style.SUCCESS("Recent Script Executions"))
        self.stdout.write(self.style.SUCCESS("=" * 60) + "\n")

        queryset = ScriptExecution.objects.all()
        if script_name:
            queryset = queryset.filter(script_name=script_name)

        executions = queryset[:limit]

        if not executions:
            self.stdout.write(self.style.WARNING("No execution history found.\n"))
            return

        for exec_record in executions:
            # Format status with colors
            if exec_record.status == ScriptExecution.Status.SUCCESS:
                status_display = self.style.SUCCESS("✓ SUCCESS")
            elif exec_record.status == ScriptExecution.Status.FAILED:
                status_display = self.style.ERROR("✗ FAILED")
            else:
                status_display = self.style.WARNING("⋯ RUNNING")

            # Format duration
            duration = ""
            if exec_record.duration_seconds:
                if exec_record.duration_seconds < 1:
                    duration = f"({exec_record.duration_seconds*1000:.0f}ms)"
                else:
                    duration = f"({exec_record.duration_seconds:.1f}s)"

            # Format user
            user = f" by {exec_record.executed_by.email}" if exec_record.executed_by else ""

            self.stdout.write(
                f"{exec_record.started_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{status_display} | {self.style.WARNING(exec_record.script_name)} {duration}{user}"
            )

            # Show arguments if any
            if exec_record.arguments:
                args_str = " ".join(
                    f"--{k}={v}" if v is not True else f"--{k}"
                    for k, v in exec_record.arguments.items()
                    if v
                )
                if args_str:
                    self.stdout.write(f"    Args: {args_str}")

            # Show error if failed
            if exec_record.status == ScriptExecution.Status.FAILED and exec_record.error_message:
                # Truncate long error messages
                error = exec_record.error_message[:200]
                if len(exec_record.error_message) > 200:
                    error += "..."
                self.stdout.write(self.style.ERROR(f"    Error: {error}"))

        self.stdout.write("")

    def handle(self, *args, **options):
        script_name = options.get("script_name")
        show_history = options.get("history")
        history_limit = options.get("history_limit", 10)
        no_log = options.get("no_log", False)
        script_args = options.get("script_args", [])

        # Show history mode
        if show_history:
            self.print_history(script_name, history_limit)
            return

        # No script specified - show available scripts
        if not script_name:
            self.print_available_scripts()
            return

        # Check if script is in our registry
        if script_name not in AVAILABLE_SCRIPTS:
            # Check if it's a valid Django management command anyway
            available_commands = get_commands()
            if script_name not in available_commands:
                raise CommandError(
                    f"Unknown script: {script_name}\n"
                    f"Run 'python manage.py run_script' to see available scripts."
                )
            self.stdout.write(
                self.style.WARNING(
                    f"Note: '{script_name}' is not in the script registry but exists as a command."
                )
            )

        # Parse script arguments into a dict for logging
        args_dict = {}
        current_key = None
        for arg in script_args:
            if arg.startswith("--"):
                if "=" in arg:
                    key, value = arg[2:].split("=", 1)
                    args_dict[key] = value
                    current_key = None
                else:
                    current_key = arg[2:]
                    args_dict[current_key] = True
            elif current_key:
                args_dict[current_key] = arg
                current_key = None

        # Create execution record
        execution = None
        if not no_log:
            execution = ScriptExecution.objects.create(
                script_name=script_name,
                arguments=args_dict,
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS(f"Running: {script_name}"))
        if args_dict:
            self.stdout.write(f"Arguments: {args_dict}")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Capture output
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr

        try:
            # Redirect stdout/stderr to capture output
            sys.stdout = output_buffer
            sys.stderr = output_buffer

            # Run the command
            call_command(script_name, *script_args, stdout=output_buffer, stderr=output_buffer)

            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get captured output
            output = output_buffer.getvalue()

            # Print the output
            if output:
                self.stdout.write(output)

            # Mark success
            if execution:
                execution.mark_success(output)

            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write(self.style.SUCCESS(f"✓ Script '{script_name}' completed successfully"))
            if execution:
                self.stdout.write(f"  Duration: {execution.duration_seconds:.2f}s")
                self.stdout.write(f"  Logged as: Execution #{execution.id}")
            self.stdout.write(self.style.SUCCESS("=" * 60))
            self.stdout.write("")

        except Exception as e:
            # Restore stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get any partial output
            output = output_buffer.getvalue()
            if output:
                self.stdout.write(output)

            # Get error details
            error_message = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

            # Mark failed
            if execution:
                execution.mark_failed(error_message)

            self.stdout.write("")
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write(self.style.ERROR(f"✗ Script '{script_name}' failed"))
            self.stdout.write(self.style.ERROR(f"  Error: {e}"))
            if execution:
                self.stdout.write(f"  Logged as: Execution #{execution.id}")
            self.stdout.write(self.style.ERROR("=" * 60))
            self.stdout.write("")

            # Re-raise to exit with error code
            raise CommandError(str(e)) from e

