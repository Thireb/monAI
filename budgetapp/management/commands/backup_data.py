import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from budgetapp.models import ArchivedBudget, Budget, BudgetLog, Expense, SubExpense


class Command(BaseCommand):
    help = "Backup all budget-related data to a JSON file"

    def backup_model(self, model, data_key, transform_func, data):
        try:
            self.stdout.write(f"Backing up {model.__name__}...")
            for item in model.objects.all():
                data[data_key].append(transform_func(item))
        except OperationalError as e:
            self.stdout.write(self.style.WARNING(f"Skipping {model.__name__}: {str(e)}"))

    def handle(self, *args, **options):
        data = {
            "budgets": [],
            "expenses": [],
            "sub_expenses": [],
            "budget_logs": [],
            "archived_budgets": [],
        }

        # Define transform functions for each model
        transforms = {
            Budget: lambda budget: {
                "id": budget.id,
                "month": budget.month.isoformat(),
                "income": str(budget.income),
                "currency": budget.currency,
                "created_at": budget.created_at.isoformat(),
                "updated_at": budget.updated_at.isoformat(),
            },
            Expense: lambda expense: {
                "id": expense.id,
                "budget_id": expense.budget_id,
                "name": expense.name,
                "amount": str(expense.amount),
                "is_recurring": expense.is_recurring,
                "created_at": expense.created_at.isoformat(),
                "updated_at": expense.updated_at.isoformat(),
            },
            SubExpense: lambda sub_expense: {
                "id": sub_expense.id,
                "expense_id": sub_expense.expense_id,
                "name": sub_expense.name,
                "amount": str(sub_expense.amount),
                "created_at": sub_expense.created_at.isoformat(),
                "updated_at": sub_expense.updated_at.isoformat(),
            },
            BudgetLog: lambda log_entry: {
                "id": log_entry.id,
                "month": log_entry.month.isoformat(),
                "action": log_entry.action,
                "timestamp": log_entry.timestamp.isoformat(),
                "details": log_entry.details,
            },
            ArchivedBudget: lambda archived_budget: {
                "id": archived_budget.id,
                "budget_id": archived_budget.budget_id,
                "archived_date": archived_budget.archived_date.isoformat(),
            },
        }

        # Backup each model
        model_keys = {
            Budget: "budgets",
            Expense: "expenses",
            SubExpense: "sub_expenses",
            BudgetLog: "budget_logs",
            ArchivedBudget: "archived_budgets",
        }

        for model, key in model_keys.items():
            self.backup_model(model, key, transforms[model], data)

        # Save to file
        filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"Successfully backed up data to {filename}"))
