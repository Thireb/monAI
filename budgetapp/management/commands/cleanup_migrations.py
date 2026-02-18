"""
Management command to cleanup problematic database tables and indexes.

WARNING: This is a DESTRUCTIVE command that directly drops database tables.
It should only be used during development or when explicitly required.
"""

import sys

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Cleanup problematic database tables and indexes (DESTRUCTIVE - use with caution!)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Skip confirmation prompts (DANGEROUS)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        force = options.get("force", False)

        self.stdout.write(
            self.style.WARNING(
                "\n" + "=" * 60 + "\n"
                "WARNING: This command will DROP DATABASE TABLES!\n"
                "All data in the affected tables will be PERMANENTLY DELETED.\n"
                "=" * 60 + "\n"
            )
        )

        # Tables and indexes to drop
        tables_to_drop = [
            "budgetapp_budget",
            "budgetapp_expense",
            "budgetapp_subexpense",
            "budgetapp_budgetlog",
            "budgetapp_archivedbudget",
            "budgetapp_category",
            "budgetapp_tag",
            "budgetapp_incomehistory",
            "budgetapp_goal",
            "budgetapp_goalcontribution",
            "budgetapp_debt",
            "budgetapp_debttransaction",
        ]

        indexes_to_drop = [
            "budgetapp_expense_budget_id_idx",
            "budgetapp_subexpense_expense_id_idx",
        ]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - no changes will be made\n"))

        # Show what will be dropped
        self.stdout.write("Tables to be dropped:")
        for table in tables_to_drop:
            self.stdout.write(f"  - {table}")

        self.stdout.write("\nIndexes to be dropped:")
        for index in indexes_to_drop:
            self.stdout.write(f"  - {index}")

        # Require multiple confirmations unless --force is used
        if not force and not dry_run:
            self.stdout.write("")
            confirm1 = input("Are you ABSOLUTELY SURE you want to proceed? [yes/NO]: ")
            if confirm1.lower() != "yes":
                self.stdout.write(self.style.SUCCESS("Aborted."))
                sys.exit(0)

            confirm2 = input(
                'Type "DELETE ALL DATA" to confirm (this is your last chance): '
            )
            if confirm2 != "DELETE ALL DATA":
                self.stdout.write(self.style.SUCCESS("Aborted."))
                sys.exit(0)

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "\nDry run complete. No changes were made.\n"
                    "Remove --dry-run to actually perform the cleanup."
                )
            )
            return

        # Perform the cleanup
        self.stdout.write("\nDropping tables and indexes...")

        with connection.cursor() as cursor:
            # Disable foreign key constraints (SQLite-specific)
            cursor.execute("PRAGMA foreign_keys=OFF")

            # Drop indexes
            for index in indexes_to_drop:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index}")
                    self.stdout.write(f"  Dropped index: {index}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Could not drop index {index}: {e}")
                    )

            # Drop tables
            for table in tables_to_drop:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    self.stdout.write(f"  Dropped table: {table}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Could not drop table {table}: {e}")
                    )

            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")

        self.stdout.write(
            self.style.SUCCESS(
                "\nCleanup complete.\n"
                "You may need to run 'python manage.py migrate' to recreate the tables."
            )
        )
