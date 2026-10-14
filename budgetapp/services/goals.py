"""Goals and debts for the new UI: progress, projected dates and debt payoff dates.

Money rules:

- A goal's ``current_amount`` is the sum of its contributions (``sync_goal_amount``), the same
  as on the classic goal pages.
- A debt is repaid by budget lines that use the debt's account tag (``Debt.repaid_amount``).
  ``owed`` = borrowed - repaid.
- The payoff date uses the average repayment per month, from the month of the first
  repayment to the current month (months without a repayment count as 0). It is ``None``
  when nothing was repaid yet.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import Sum

from budgetapp.models import Budget, Debt, Expense, Goal

ZERO = Decimal("0")

# Goal progress points that get a celebration when a contribution passes them.
MILESTONES = (25, 50, 75, 100)


def sync_goal_amount(goal: Goal) -> None:
    """Set ``goal.current_amount`` to the sum of its contributions."""
    total = goal.contributions.aggregate(t=Sum("amount"))["t"] or ZERO
    if goal.current_amount != total:
        goal.current_amount = total
        goal.save(update_fields=["current_amount"])


def milestone_passed(before_pct: int, after_pct: int) -> int | None:
    """Return the highest milestone in ``(before_pct, after_pct]``, or ``None``."""
    passed = [m for m in MILESTONES if before_pct < m <= after_pct]
    return passed[-1] if passed else None


def _months_between(start: date, end: date) -> int:
    """Count the months from the month of ``start`` to the month of ``end``, both included."""
    return (end.year - start.year) * 12 + end.month - start.month + 1


def _add_months(day: date, months: int) -> date:
    """First day of the month ``months`` after the month of ``day``."""
    index = day.year * 12 + day.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


@dataclass(frozen=True)
class GoalView:
    """A savings goal and its progress."""

    id: int
    name: str
    current: Decimal
    target: Decimal
    left: Decimal
    pct: int
    is_done: bool
    target_date: date | None
    monthly_needed: Decimal | None
    projected_date: date | None
    on_track: bool | None


@dataclass(frozen=True)
class DebtView:
    """A debt: what is borrowed, repaid and still owed, and when it will be paid off."""

    id: int
    name: str
    tag_id: int | None
    tag_name: str
    limit: Decimal
    borrowed: Decimal
    repaid: Decimal
    owed: Decimal
    repaid_pct: int
    can_borrow: Decimal
    monthly_repayment: Decimal | None
    payoff_month: date | None
    is_paid_off: bool


def goal_view(goal: Goal) -> GoalView:
    """Build the view of one goal. Call ``sync_goal_amount`` first."""
    current = goal.current_amount
    target = goal.target_amount
    is_done = current >= target
    projected, _rate, _on_target = goal.get_projected_completion()
    return GoalView(
        id=goal.id,
        name=goal.name,
        current=current,
        target=target,
        left=max(ZERO, target - current),
        pct=max(0, min(100, int(goal.progress_percentage))),
        is_done=is_done,
        target_date=goal.target_date,
        monthly_needed=None if is_done else goal.monthly_contribution_needed(),
        projected_date=None if is_done else projected,
        on_track=goal.is_on_track(),
    )


def goal_views(user: AbstractBaseUser) -> list[GoalView]:
    """Active goals of ``user``: open goals closest to done first, then reached goals."""
    views = []
    for goal in Goal.objects.filter(user=user, is_active=True).prefetch_related("contributions"):
        sync_goal_amount(goal)
        views.append(goal_view(goal))
    return sorted(views, key=lambda v: (v.is_done, -v.pct, v.name))


def debt_view(debt: Debt, today: date) -> DebtView:
    """Build the view of one debt, with its payoff month."""
    tag = debt.debt_tag
    repayments: list[dict[str, Any]] = (
        list(
            Expense.objects.filter(tag_foreign_key=tag, budget__user=debt.user)
            .values("budget__month")
            .annotate(total=Sum("amount"))
            .order_by("budget__month")
        )
        if tag
        else []
    )
    repaid = sum((row["total"] for row in repayments), ZERO)
    borrowed = debt.borrowed_amount
    owed = max(ZERO, borrowed - repaid)
    monthly: Decimal | None = None
    payoff: date | None = None
    if repayments and owed > 0:
        first_month = repayments[0]["budget__month"]
        months = max(1, _months_between(first_month, today))
        monthly = (repaid / months).quantize(Decimal("0.01"))
        if monthly > 0:
            payoff = _add_months(today, math.ceil(owed / monthly))
    return DebtView(
        id=debt.id,
        name=debt.name,
        tag_id=tag.id if tag else None,
        tag_name=tag.name if tag else "",
        limit=debt.total_amount,
        borrowed=borrowed,
        repaid=repaid,
        owed=owed,
        repaid_pct=_pct(repaid, borrowed) if borrowed > 0 else 0,
        can_borrow=max(ZERO, debt.total_amount - borrowed),
        monthly_repayment=monthly,
        payoff_month=payoff,
        is_paid_off=borrowed > 0 and owed <= 0,
    )


def _pct(part: Decimal, whole: Decimal) -> int:
    """``part / whole`` as a whole percent, limited to 0..100."""
    return max(0, min(100, int(part / whole * 100)))


def debt_views(user: AbstractBaseUser, today: date) -> list[DebtView]:
    """Active debts of ``user``: the most owed first, paid-off debts last."""
    debts = Debt.objects.filter(user=user, is_active=True).select_related("debt_tag")
    views = [debt_view(debt, today) for debt in debts]
    return sorted(views, key=lambda v: (v.is_paid_off, -v.owed, v.name))


def add_repayment(debt: Debt, budget: Budget, amount: Decimal) -> Expense:
    """Add ``amount`` to the repayment line of ``debt`` in ``budget``; create it if missing.

    The line uses the debt's account tag, so ``Debt.repaid_amount`` counts it.
    """
    line = Expense.objects.filter(budget=budget, tag_foreign_key=debt.debt_tag).first()
    if line is None:
        line = Expense.objects.create(
            budget=budget,
            name=f"Repay {debt.name}"[:200],
            amount=amount,
            tag_foreign_key=debt.debt_tag,
        )
    else:
        line.amount += amount
        line.save(update_fields=["amount", "updated_at"])
    debt.check_and_update_status()
    return line
