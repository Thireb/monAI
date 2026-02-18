"""
Management command to backup all budget-related data to a JSON file.

This command exports all models to a JSON file for backup purposes.
The backup includes user associations for multi-tenant data.
"""

import json
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.utils import OperationalError

from budgetapp.models import (
    ArchivedBudget,
    Budget,
    BudgetLog,
    Category,
    Debt,
    DebtTransaction,
    Expense,
    Goal,
    GoalContribution,
    IncomeHistory,
    SubExpense,
    Tag,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Backup all budget-related data to a JSON file"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            "-o",
            help="Output filename (default: backup_YYYYMMDD_HHMMSS.json)",
        )
        parser.add_argument(
            "--user",
            help="Only backup data for a specific user (by email)",
        )

    def backup_model(self, model, data_key, transform_func, data, user_filter=None):
        """Backup a single model's data."""
        try:
            self.stdout.write(f"Backing up {model.__name__}...")
            queryset = model.objects.all()

            # Apply user filter if specified and model has user field
            if user_filter and hasattr(model, "user"):
                queryset = queryset.filter(user=user_filter)

            for item in queryset:
                data[data_key].append(transform_func(item))

            count = len(data[data_key])
            self.stdout.write(self.style.SUCCESS(f"  -> {count} record(s)"))
        except OperationalError as e:
            self.stdout.write(self.style.WARNING(f"Skipping {model.__name__}: {str(e)}"))

    def handle(self, *args, **options):
        # Handle user filter
        user_filter = None
        if options.get("user"):
            try:
                user_filter = User.objects.get(email=options["user"])
                self.stdout.write(f"Filtering data for user: {user_filter.email}")
            except User.DoesNotExist:
                self.stderr.write(
                    self.style.ERROR(f"User not found: {options['user']}")
                )
                return

        data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "user_filter": options.get("user"),
            },
            "budgets": [],
            "expenses": [],
            "sub_expenses": [],
            "categories": [],
            "tags": [],
            "goals": [],
            "goal_contributions": [],
            "debts": [],
            "debt_transactions": [],
            "income_history": [],
            "budget_logs": [],
            "archived_budgets": [],
        }

        # Define transform functions for each model
        transforms = {
            Budget: lambda b: {
                "id": b.id,
                "user_email": b.user.email if b.user else None,
                "month": b.month.isoformat(),
                "income": str(b.income),
                "currency": b.currency,
                "is_archived": b.is_archived,
                "created_at": b.created_at.isoformat(),
                "updated_at": b.updated_at.isoformat(),
            },
            Expense: lambda e: {
                "id": e.id,
                "budget_id": e.budget_id,
                "name": e.name,
                "amount": str(e.amount),
                "is_recurring": e.is_recurring,
                "category_id": e.category_id,
                "tag_foreign_key_id": e.tag_foreign_key_id,
                "created_at": e.created_at.isoformat(),
                "updated_at": e.updated_at.isoformat(),
            },
            SubExpense: lambda s: {
                "id": s.id,
                "expense_id": s.expense_id,
                "name": s.name,
                "amount": str(s.amount),
                "is_return": s.is_return,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
            },
            Category: lambda c: {
                "id": c.id,
                "user_email": c.user.email if c.user else None,
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "icon": c.icon,
                "color": c.color,
                "created_at": c.created_at.isoformat(),
            },
            Tag: lambda t: {
                "id": t.id,
                "user_email": t.user.email if t.user else None,
                "name": t.name,
                "slug": t.slug,
                "description": t.description,
                "color": t.color,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
            },
            Goal: lambda g: {
                "id": g.id,
                "user_email": g.user.email if g.user else None,
                "name": g.name,
                "description": g.description,
                "target_amount": str(g.target_amount),
                "current_amount": str(g.current_amount),
                "start_date": g.start_date.isoformat(),
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "category_id": g.category_id,
                "is_active": g.is_active,
            },
            GoalContribution: lambda gc: {
                "id": gc.id,
                "goal_id": gc.goal_id,
                "amount": str(gc.amount),
                "date": gc.date.isoformat(),
                "source": gc.source,
                "notes": gc.notes,
            },
            Debt: lambda d: {
                "id": d.id,
                "user_email": d.user.email if d.user else None,
                "name": d.name,
                "description": d.description,
                "total_amount": str(d.total_amount),
                "borrowed_amount": str(d.borrowed_amount),
                "debt_tag_id": d.debt_tag_id,
                "is_active": d.is_active,
                "created_at": d.created_at.isoformat(),
                "updated_at": d.updated_at.isoformat(),
            },
            DebtTransaction: lambda dt: {
                "id": dt.id,
                "debt_id": dt.debt_id,
                "amount": str(dt.amount),
                "date": dt.date.isoformat(),
                "notes": dt.notes,
                "created_at": dt.created_at.isoformat(),
            },
            IncomeHistory: lambda ih: {
                "id": ih.id,
                "budget_id": ih.budget_id,
                "old_amount": str(ih.old_amount),
                "new_amount": str(ih.new_amount),
                "old_currency": ih.old_currency,
                "new_currency": ih.new_currency,
                "reason": ih.reason,
                "changed_at": ih.changed_at.isoformat(),
            },
            BudgetLog: lambda bl: {
                "id": bl.id,
                "month": bl.month.isoformat(),
                "action": bl.action,
                "timestamp": bl.timestamp.isoformat(),
                "details": bl.details,
            },
            ArchivedBudget: lambda ab: {
                "id": ab.id,
                "budget_id": ab.budget_id,
                "archived_date": ab.archived_date.isoformat(),
            },
        }

        # Model-to-key mapping
        model_keys = {
            Budget: "budgets",
            Expense: "expenses",
            SubExpense: "sub_expenses",
            Category: "categories",
            Tag: "tags",
            Goal: "goals",
            GoalContribution: "goal_contributions",
            Debt: "debts",
            DebtTransaction: "debt_transactions",
            IncomeHistory: "income_history",
            BudgetLog: "budget_logs",
            ArchivedBudget: "archived_budgets",
        }

        # Backup each model
        self.stdout.write("\nBacking up data...")
        for model, key in model_keys.items():
            self.backup_model(model, key, transforms[model], data, user_filter)

        # Generate filename
        filename = options.get("output")
        if not filename:
            filename = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

        # Save to file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self.stdout.write(self.style.SUCCESS(f"\nSuccessfully backed up data to {filename}"))
