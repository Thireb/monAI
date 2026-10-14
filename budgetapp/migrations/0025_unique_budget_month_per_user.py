"""Merge duplicate budgets for the same user and month, then make (user, month) unique."""

from __future__ import annotations

from typing import Any

from django.db import migrations, models
from django.db.models import Count


def merge_duplicate_months(apps: Any, schema_editor: Any) -> None:
    """Move child rows of duplicate budgets into one kept budget, then delete the rest.

    The kept budget is the active one (not archived) that was updated last.
    When the incomes differ, an IncomeHistory row records the dropped income.
    """
    Budget = apps.get_model("budgetapp", "Budget")
    Expense = apps.get_model("budgetapp", "Expense")
    TagTransfer = apps.get_model("budgetapp", "TagTransfer")
    IncomeHistory = apps.get_model("budgetapp", "IncomeHistory")
    RecentUpdate = apps.get_model("budgetapp", "RecentUpdate")
    ArchivedBudget = apps.get_model("budgetapp", "ArchivedBudget")

    groups = (
        Budget.objects.filter(user__isnull=False)
        .values("user_id", "month")
        .annotate(n=Count("id"))
        .filter(n__gt=1)
    )
    for group in groups:
        budgets = list(
            Budget.objects.filter(user_id=group["user_id"], month=group["month"]).order_by(
                "is_archived", "-updated_at", "-id"
            )
        )
        keep, extras = budgets[0], budgets[1:]
        for extra in extras:
            Expense.objects.filter(budget_id=extra.id).update(budget_id=keep.id)
            TagTransfer.objects.filter(budget_id=extra.id).update(budget_id=keep.id)
            IncomeHistory.objects.filter(budget_id=extra.id).update(budget_id=keep.id)
            RecentUpdate.objects.filter(budget_id=extra.id).update(budget_id=keep.id)
            if extra.income != keep.income or extra.currency != keep.currency:
                IncomeHistory.objects.create(
                    budget_id=keep.id,
                    old_amount=extra.income,
                    new_amount=keep.income,
                    old_currency=extra.currency,
                    new_currency=keep.currency,
                    reason=f"Merged duplicate budget {extra.id} into {keep.id}",
                )
            ArchivedBudget.objects.filter(budget_id=extra.id).delete()
            extra.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("budgetapp", "0024_tagtransfer_updated_at"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_months, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="budget",
            constraint=models.UniqueConstraint(
                fields=("user", "month"), name="unique_budget_month_per_user"
            ),
        ),
    ]
