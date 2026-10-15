"""Create a budget month, optionally copying income and recurring lines from the last one."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db import transaction

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import Budget, Expense
from budgetapp.services.month import build_month_snapshot, percent, use_status


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


@dataclass(frozen=True)
class MonthCard:
    """One month of the year overview. The figures are ``None`` when the month has no budget."""

    month: date
    exists: bool
    is_current: bool
    is_archived: bool
    income: Decimal | None
    gross: Decimal | None
    spent: Decimal | None
    unallocated: Decimal | None
    spent_pct: int
    status: str


def year_overview(user: AbstractBaseUser, year: int, today: date) -> list[MonthCard]:
    """Return the 12 months of ``year``, with the figures of each month that has a budget.

    ``spent_pct`` is the share of the lines' total that is spent; ``status`` uses the same
    rule as a line (``ok``, ``close``, ``done`` or ``over``).
    """
    budgets = {b.month.month: b for b in Budget.objects.filter(user=user, month__year=year)}
    cards = []
    for number in range(1, 13):
        first_day = date(year, number, 1)
        is_current = (year, number) == (today.year, today.month)
        budget = budgets.get(number)
        if budget is None:
            cards.append(
                MonthCard(first_day, False, is_current, False, None, None, None, None, 0, "ok")
            )
            continue
        snap = build_month_snapshot(budget, today)
        used = snap.spent + snap.returns
        cards.append(
            MonthCard(
                month=first_day,
                exists=True,
                is_current=is_current,
                is_archived=budget.is_archived,
                income=snap.income,
                gross=snap.gross,
                spent=snap.spent,
                unallocated=snap.unallocated,
                spent_pct=percent(used, snap.gross),
                status=use_status(snap.gross, used),
            )
        )
    return cards


def budget_years(user: AbstractBaseUser, today: date) -> list[int]:
    """Years that have a budget, and this year, newest first."""
    years = {d.year for d in Budget.objects.filter(user=user).dates("month", "year")}
    years.add(today.year)
    return sorted(years, reverse=True)
