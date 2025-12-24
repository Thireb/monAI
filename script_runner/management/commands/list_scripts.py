"""
List all available scripts and their status.

Usage:
    python manage.py list_scripts              # List all scripts
    python manage.py list_scripts --version    # Show version-specific scripts
    python manage.py list_scripts --history    # Show execution history
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from script_runner.models import ScriptExecution
from script_runner.registry import get_scripts_by_category, get_scripts_for_version


class Command(BaseCommand):
    help = "List all available scripts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--code-version",
            help="Show scripts for a specific version (default: CODE_VERSION from settings)",
        )
        parser.add_argument(
            "--history",
            nargs="?",
            const="all",
            help="Show execution history (optionally for a specific script)",
        )
        parser.add_argument(
            "--history-limit",
            type=int,
            default=10,
            help="Number of history entries to show (default: 10)",
        )
        parser.add_argument(
            "--deploy-only",
            action="store_true",
            help="Only show scripts that run on deploy",
        )

    def show_history(self, script_name=None, limit=10):
        """Show execution history."""
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        if script_name and script_name != "all":
            self.stdout.write(self.style.SUCCESS(f"Execution History: {script_name}"))
        else:
            self.stdout.write(self.style.SUCCESS("Recent Script Executions"))
        self.stdout.write(self.style.SUCCESS("=" * 60) + "\n")

        queryset = ScriptExecution.objects.all()
        if script_name and script_name != "all":
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
            elif exec_record.status == ScriptExecution.Status.SKIPPED:
                status_display = self.style.WARNING("⊘ SKIPPED")
            else:
                status_display = self.style.WARNING("⋯ RUNNING")

            # Format duration
            duration = ""
            if exec_record.duration_seconds:
                if exec_record.duration_seconds < 1:
                    duration = f"({exec_record.duration_seconds*1000:.0f}ms)"
                else:
                    duration = f"({exec_record.duration_seconds:.1f}s)"

            # Format version and batch
            version_info = ""
            if exec_record.code_version:
                version_info = f" v{exec_record.code_version}"
            if exec_record.batch_id:
                version_info += f" [{exec_record.batch_id}]"

            self.stdout.write(
                f"{exec_record.started_at.strftime('%Y-%m-%d %H:%M:%S')} | "
                f"{status_display} | {self.style.WARNING(exec_record.script_name)} "
                f"{duration}{version_info}"
            )

            # Show error if failed
            if exec_record.status == ScriptExecution.Status.FAILED and exec_record.error_message:
                error = exec_record.error_message[:100]
                if len(exec_record.error_message) > 100:
                    error += "..."
                self.stdout.write(self.style.ERROR(f"    Error: {error}"))

        self.stdout.write("")

    def handle(self, *args, **options):
        version = options.get("code_version") or getattr(settings, "CODE_VERSION", "1.0.0")
        history = options.get("history")
        history_limit = options.get("history_limit", 10)
        deploy_only = options.get("deploy_only", False)

        # Show history mode
        if history:
            self.show_history(history if history != "all" else None, history_limit)
            return

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Available Scripts"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"\nCode Version: {self.style.WARNING(version)}")

        if deploy_only:
            scripts = get_scripts_for_version(version, deploy_only=True)
            self.stdout.write(self.style.HTTP_INFO("\nDeploy Scripts Only:\n"))
            for script in scripts:
                danger = " ⚠️" if script.dangerous else ""
                deploy = " 🚀" if script.run_on_deploy else ""
                self.stdout.write(f"  {self.style.WARNING(script.name)}{danger}{deploy}")
                self.stdout.write(f"      {script.description}")
                if script.example:
                    self.stdout.write(f"      Example: python manage.py {script.example}")
        else:
            by_category = get_scripts_by_category()

            for category in sorted(by_category.keys()):
                self.stdout.write(f"\n{self.style.HTTP_INFO(category)}:")
                for script in sorted(by_category[category], key=lambda s: s.name):
                    danger = " ⚠️ DANGEROUS" if script.dangerous else ""
                    deploy = " 🚀" if script.run_on_deploy else ""

                    # Check version match
                    matches = script.matches_version(version)
                    version_info = ""
                    if script.min_version or script.max_version:
                        version_range = f"[{script.min_version or '*'} - {script.max_version or '*'}]"
                        if not matches:
                            version_info = f" {self.style.WARNING(version_range + ' (not applicable)')}"
                        else:
                            version_info = f" {version_range}"

                    self.stdout.write(
                        f"  {self.style.WARNING(script.name)}{danger}{deploy}{version_info}"
                    )
                    self.stdout.write(f"      {script.description}")
                    if script.example:
                        self.stdout.write(f"      Example: python manage.py {script.example}")

        self.stdout.write("\n" + "-" * 60)
        self.stdout.write("Commands:")
        self.stdout.write("  python manage.py <script_name> [args]  # Run individual script")
        self.stdout.write("  python manage.py run_scripts           # Run all deploy scripts")
        self.stdout.write("  python manage.py list_scripts --history # View execution history")
        self.stdout.write("")

