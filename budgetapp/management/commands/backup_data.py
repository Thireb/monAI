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
            Budget: lambda b: {
                "id": b.id,
                "month": b.month.isoformat(),
                "income": str(b.income),
                "currency": b.currency,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat(),
            },
            Expense: lambda e: {
                "id": e.id,
                "budget_id": e.budget_id,
                "name": e.name,
                "amount": str(e.amount),
                "is_recurring": e.is_recurring,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
            },
            SubExpense: lambda se: {
                "id": se.id,
                "expense_id": se.expense_id,
                "name": se.name,
                "amount": str(se.amount),
                "created_at": se.created_at.isoformat(),
                "updated_at": se.updated_at.isoformat(),
            },
            BudgetLog: lambda l: {
                "id": l.id,
                "month": l.month.isoformat(),
                "action": l.action,
                "timestamp": l.timestamp.isoformat(),
                "details": l.details,
            },
            ArchivedBudget: lambda a: {
                "id": a.id,
                "budget_id": a.budget_id,
                "archived_date": a.archived_date.isoformat(),
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
