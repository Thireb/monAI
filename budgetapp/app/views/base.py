"""Shared helpers for the new UI views."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.urls import reverse
from django.views.generic import TemplateView

from budgetapp.models import Budget
from budgetapp.services.month import MonthSnapshot


def month_date(year: int, month: int) -> date:
    """Return the first day of ``year``/``month``; raise 404 for a month that does not exist."""
    try:
        return date(year, month, 1)
    except ValueError as exc:
        raise Http404("No such month.") from exc


def month_url(day: date) -> str:
    """URL of the month page that contains ``day``."""
    return reverse("app:month", kwargs={"year": day.year, "month": day.month})


def shift_month(day: date, months: int) -> date:
    """First day of the month ``months`` after (or before) the month of ``day``."""
    index = day.year * 12 + day.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def quick_add_context(budget: Budget | None, snap: MonthSnapshot | None) -> dict[str, Any]:
    """Context for the quick-add sheet. Without a budget, the sheet is not shown."""
    if budget is None or snap is None:
        return {}
    return {
        "budget": budget,
        "lines": [line for line in snap.lines if line.status != "done"] or snap.lines,
        "action": reverse("app:spend_create"),
    }


class AppTemplateView(LoginRequiredMixin, TemplateView):
    """Base for full pages of the new UI. ``nav`` marks the active bottom-nav item."""

    nav = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the active nav item to the context."""
        context = super().get_context_data(**kwargs)
        context["nav"] = self.nav
        return context
