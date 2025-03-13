from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Cleanup problematic database tables and indexes"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # First disable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=OFF")

            # Drop tables in correct order (children first, then parents)
            table_order = [
                "budgetapp_subexpense",  # Child of Expense
                "budgetapp_archivedbudget",  # Child of Budget
                "budgetapp_expense",  # Child of Budget
                "budgetapp_budgetlog",  # Independent
                "budgetapp_budget",  # Parent table
            ]

            for table in table_order:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table}")
                    self.stdout.write(self.style.SUCCESS(f"Dropped table: {table}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error dropping {table}: {e}"))

            # Drop indexes
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='index' AND name LIKE 'budgetapp_%'
            """
            )
            indexes = cursor.fetchall()

            for index in indexes:
                try:
                    cursor.execute(f"DROP INDEX IF EXISTS {index[0]}")
                    self.stdout.write(self.style.SUCCESS(f"Dropped index: {index[0]}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error dropping index {index[0]}: {e}"))

            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys=ON")

        self.stdout.write(self.style.SUCCESS("Successfully cleaned up database tables and indexes"))
