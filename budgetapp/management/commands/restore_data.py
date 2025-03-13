import json
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date, parse_datetime

from budgetapp.models import ArchivedBudget, Budget, BudgetLog, Expense, SubExpense


class Command(BaseCommand):
    help = "Restore data from a backup JSON file"

    def add_arguments(self, parser):
        parser.add_argument("backup_file", type=str, help="Path to the backup JSON file")

    def handle(self, *args, **options):
        backup_file = options["backup_file"]

        try:
            with open(backup_file, "r") as f:
                data = json.load(f)

            # Restore Budgets first (parent records)
            self.stdout.write("Restoring Budgets...")
            for budget_data in data["budgets"]:
                Budget.objects.create(
                    id=budget_data["id"],
                    month=parse_date(budget_data["month"]),
                    income=Decimal(budget_data["income"]),
                    currency=budget_data["currency"],
                    created_at=parse_datetime(budget_data["created_at"]),
                    updated_at=parse_datetime(budget_data["updated_at"]),
                )

            # Restore Expenses
            self.stdout.write("Restoring Expenses...")
            for expense_data in data["expenses"]:
                Expense.objects.create(
                    id=expense_data["id"],
                    budget_id=expense_data["budget_id"],
                    name=expense_data["name"],
                    amount=Decimal(expense_data["amount"]),
                    is_recurring=expense_data["is_recurring"],
                    created_at=parse_datetime(expense_data["created_at"]),
                    updated_at=parse_datetime(expense_data["updated_at"]),
                )

            # Restore SubExpenses
            self.stdout.write("Restoring SubExpenses...")
            for subexp_data in data["sub_expenses"]:
                SubExpense.objects.create(
                    id=subexp_data["id"],
                    expense_id=subexp_data["expense_id"],
                    name=subexp_data["name"],
                    amount=Decimal(subexp_data["amount"]),
                    created_at=parse_datetime(subexp_data["created_at"]),
                    updated_at=parse_datetime(subexp_data["updated_at"]),
                )

            # Restore BudgetLogs
            self.stdout.write("Restoring BudgetLogs...")
            for log_data in data["budget_logs"]:
                BudgetLog.objects.create(
                    id=log_data["id"],
                    month=parse_date(log_data["month"]),
                    action=log_data["action"],
                    timestamp=parse_datetime(log_data["timestamp"]),
                    details=log_data["details"],
                )

            # Restore ArchivedBudgets
            self.stdout.write("Restoring ArchivedBudgets...")
            for archive_data in data["archived_budgets"]:
                ArchivedBudget.objects.create(
                    id=archive_data["id"],
                    budget_id=archive_data["budget_id"],
                    archived_date=parse_datetime(archive_data["archived_date"]),
                )

            self.stdout.write(self.style.SUCCESS("Successfully restored data from backup"))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Backup file not found: {backup_file}"))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f"Invalid JSON in backup file: {backup_file}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error restoring data: {str(e)}"))
