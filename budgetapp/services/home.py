"""Cards for the home page: upcoming bills and goals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import AbstractBaseUser

from budgetapp.models import BillReminder, Goal


@dataclass(frozen=True)
class BillView:
    """An active bill reminder that is due soon."""

    id: int
    name: str
    amount: Decimal
    due: date
    days_until: int
    severity: str


@dataclass(frozen=True)
class GoalView:
    """An active savings goal and its progress."""

    id: int
    name: str
    current: Decimal
    target: Decimal
    pct: int
    monthly_needed: Decimal | None


def upcoming_bills(user: AbstractBaseUser, today: date, limit: int = 3) -> list[BillView]:
    """Return the next ``limit`` active bills due today or later, soonest first."""
    reminders = BillReminder.objects.filter(
        user=user, is_active=True, next_bill_date__gte=today
    ).order_by("next_bill_date", "name")[:limit]
    return [
        BillView(
            id=r.id,
            name=r.name,
            amount=r.amount,
            due=r.next_bill_date,
            days_until=(r.next_bill_date - today).days,
            severity=r.severity,
        )
        for r in reminders
    ]


def goal_cards(user: AbstractBaseUser, limit: int = 2) -> list[GoalView]:
    """Return up to ``limit`` active goals, the ones closest to done first."""
    goals = list(Goal.objects.filter(user=user, is_active=True))
    views = [
        GoalView(
            id=g.id,
            name=g.name,
            current=g.current_amount,
            target=g.target_amount,
            pct=max(0, min(100, int(g.progress_percentage))),
            monthly_needed=g.monthly_contribution_needed(),
        )
        for g in goals
    ]
    return sorted(views, key=lambda v: (-v.pct, v.name))[:limit]
