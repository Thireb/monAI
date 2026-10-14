"""Create a budget month, optionally copying income and recurring lines from the last one."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import Budget, Expense


@dataclass(frozen=True)
class CreatedMonth:
    """The new budget and what was copied into it."""

    budget: Budget
    copied_from: Budget | None
    copied_lines: int
    reminder_lines: int


def create_month(user: AbstractBaseUser, month: date, copy_previous: bool = True) -> CreatedMonth:
    """Create the budget for ``month`` (any day in it).

    With ``copy_previous``, the income and the recurring lines of the latest earlier
    month are copied, the same as the classic "create budget" action. Lines from
    bill reminders that fall in this month are added in both cases.
    The caller checks first that the month does not exist.
    """
    first_day = month.replace(day=1)
    with transaction.atomic():
        budget = Budget.objects.create(user=user, month=first_day)
        previous = None
        copied = 0
        if copy_previous:
            previous = (
                Budget.objects.filter(user=user, month__lt=first_day).order_by("-month").first()
            )
        if previous is not None:
            budget.income = previous.income
            budget.currency = previous.currency
            budget.save()
            for line in previous.expenses.filter(is_recurring=True):
                Expense.objects.create(
                    budget=budget,
                    name=line.name,
                    amount=line.amount,
                    is_recurring=True,
                    is_daily=line.is_daily,
                    category=line.category,
                    tag_foreign_key=line.tag_foreign_key,
                )
                copied += 1
        reminders = apply_bill_reminders_to_budget(budget)
    return CreatedMonth(
        budget=budget, copied_from=previous, copied_lines=copied, reminder_lines=reminders
    )
