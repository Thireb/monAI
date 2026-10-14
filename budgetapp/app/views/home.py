"""Home page of the new UI: today's number, the month at a glance, bills and goals."""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from budgetapp.models import Budget
from budgetapp.services.bills import coming_up
from budgetapp.services.home import goal_cards
from budgetapp.services.month import build_month_snapshot

from .base import AppTemplateView, month_url, quick_add_context


class HomeView(AppTemplateView):
    """Show the current month: Safe to spend today, accounts, lines, bills and goals."""

    template_name = "app/home.html"
    nav = "home"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build the snapshot of the current month, if its budget exists."""
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        budget = Budget.objects.filter(user=self.request.user, month=today.replace(day=1)).first()
        snap = build_month_snapshot(budget, today) if budget else None
        context.update(
            {
                "today": today,
                "budget": budget,
                "snap": snap,
                "month_url": month_url(today),
                "daily_lines": [line for line in snap.lines if line.is_daily] if snap else [],
                "bills": coming_up(budget, snap, today) if budget and snap else [],
                "goals": goal_cards(self.request.user),
                "quick_add": quick_add_context(budget, snap),
            }
        )
        return context
