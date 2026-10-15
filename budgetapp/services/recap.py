"""The month recap: a short story of a finished month, shown in the first days of the next one.

Figures (all from ``build_month_snapshot``, so the money rules are the same):

- ``net_spent`` = spent - returns (money that really left).
- ``kept`` = income - net_spent. It is negative when the month spent more than its income.
- ``top_category`` is the category with the most spent (returns and lines without a
  category not counted).
- ``days_under`` counts the days whose day-to-day spending stayed at or under the daily limit;
  ``best_run`` is the longest run of such days.
- ``over_lines`` are the lines that ended over their amount, the most over first.
- ``to_goals`` is the money added to goals with a date in the month.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Sum

from budgetapp.models import Budget, GoalContribution
from budgetapp.services.month import NO_CATEGORY_NAME, LineView, build_month_snapshot

ZERO = Decimal("0")

# The home page shows last month's recap on days 1 to RECAP_DAYS of a month.
RECAP_DAYS = 7


@dataclass(frozen=True)
class Recap:
    """The story of 1 month."""

    month: date
    currency: str
    income: Decimal
    net_spent: Decimal
    kept: Decimal
    top_category: str
    top_category_spent: Decimal
    has_daily_lines: bool
    days_under: int
    days_counted: int
    best_run: int
    over_lines: list[LineView]
    to_goals: Decimal


def month_recap(budget: Budget, today: date) -> Recap:
    """Build the recap of ``budget``'s month. Days after ``today`` are not counted."""
    snap = build_month_snapshot(budget, today)
    net_spent = snap.spent - snap.returns

    spent_by_category: dict[str, Decimal] = {}
    for line in snap.lines:
        if line.category_name == NO_CATEGORY_NAME:
            continue
        spent_by_category[line.category_name] = (
            spent_by_category.get(line.category_name, ZERO) + line.spent
        )
    top_name, top_spent = max(
        spent_by_category.items(), key=lambda item: (item[1], item[0]), default=("", ZERO)
    )

    past_days = [bar for bar in snap.days if not bar.is_future]
    days_under = sum(1 for bar in past_days if not bar.is_over)
    best_run = run = 0
    for bar in past_days:
        run = 0 if bar.is_over else run + 1
        best_run = max(best_run, run)

    month_end = date(budget.month.year, budget.month.month, snap.days_in_month)
    to_goals = GoalContribution.objects.filter(
        goal__user=budget.user, date__gte=budget.month, date__lte=month_end
    ).aggregate(total=Sum("amount"))["total"]

    over = sorted((line for line in snap.lines if line.status == "over"), key=lambda v: v.left)
    return Recap(
        month=budget.month,
        currency=budget.currency,
        income=snap.income,
        net_spent=net_spent,
        kept=snap.income - net_spent,
        top_category=top_name if top_spent > 0 else "",
        top_category_spent=top_spent,
        has_daily_lines=snap.has_daily_lines,
        days_under=days_under if snap.has_daily_lines else 0,
        days_counted=len(past_days) if snap.has_daily_lines else 0,
        best_run=best_run if snap.has_daily_lines else 0,
        over_lines=over[:3],
        to_goals=to_goals or ZERO,
    )


def last_month_recap(user: AbstractBaseUser, today: date) -> Recap | None:
    """Last month's recap for the home page, on days 1 to ``RECAP_DAYS`` only."""
    if today.day > RECAP_DAYS:
        return None
    first = today.replace(day=1)
    last_month = date(first.year - (first.month == 1), (first.month - 2) % 12 + 1, 1)
    budget = Budget.objects.filter(user=user, month=last_month).first()
    if budget is None:
        return None
    return month_recap(budget, today)
