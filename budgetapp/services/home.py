"""Cards for the home page: goals. The bills come from ``services.bills.coming_up``."""

from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser

from budgetapp.services.goals import GoalView, goal_views


def goal_cards(user: AbstractBaseUser, limit: int = 2) -> list[GoalView]:
    """Return up to ``limit`` active goals: open goals closest to done first."""
    return goal_views(user)[:limit]
