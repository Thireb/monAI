"""Month page of the new UI, its HTMX panel and month creation."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import LineForm
from budgetapp.models import Budget
from budgetapp.services.home import goal_cards, upcoming_bills
from budgetapp.services.month import build_month_snapshot
from budgetapp.services.months import create_month

from .base import AppTemplateView, month_date, month_url, quick_add_context, shift_month

# Which page layout the refreshable panel renders.
PANEL_TEMPLATES = {
    "home": "app/partials/home_panel.html",
    "month": "app/partials/month_panel.html",
    "sheet": "app/partials/quick_add_chips.html",
}


class MonthView(AppTemplateView):
    """One budget month: summary, day-by-day chart, accounts and lines by category."""

    template_name = "app/month.html"
    nav = "month"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build the month snapshot, or the "create this month" state."""
        context = super().get_context_data(**kwargs)
        first_day = month_date(self.kwargs["year"], self.kwargs["month"])
        today = timezone.localdate()
        budget = Budget.objects.filter(user=self.request.user, month=first_day).first()
        snap = build_month_snapshot(budget, today) if budget else None
        previous = (
            Budget.objects.filter(user=self.request.user, month__lt=first_day)
            .order_by("-month")
            .first()
        )
        context.update(
            {
                "first_day": first_day,
                "budget": budget,
                "snap": snap,
                "today": today,
                "prev_url": month_url(shift_month(first_day, -1)),
                "next_url": month_url(shift_month(first_day, 1)),
                "previous_budget": previous,
                "line_form": LineForm(user=self.request.user, prefix="line"),
                "quick_add": quick_add_context(budget, snap),
            }
        )
        return context


class MonthPanelView(LoginRequiredMixin, View):
    """HTMX partial: the refreshable part of the home or month page after a change."""

    def get(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Render the panel named by ``?view=`` (``home`` or ``month``)."""
        view = request.GET.get("view", "month")
        template = PANEL_TEMPLATES.get(view, PANEL_TEMPLATES["month"])
        budget = get_object_or_404(Budget, user=request.user, month=month_date(year, month))
        today = timezone.localdate()
        snap = build_month_snapshot(budget, today)
        context = {
            "budget": budget,
            "snap": snap,
            "today": today,
            "month_url": month_url(budget.month),
            "daily_lines": [line for line in snap.lines if line.is_daily],
            "bills": upcoming_bills(request.user, today) if view == "home" else [],
            "goals": goal_cards(request.user) if view == "home" else [],
            "lines": quick_add_context(budget, snap).get("lines", []),
        }
        return render(request, template, context)


class MonthCreateView(LoginRequiredMixin, View):
    """Create a missing month, empty or as a copy of the last one."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponseRedirect:
        """Create the month unless it exists, then open it."""
        first_day = month_date(year, month)
        if not Budget.objects.filter(user=request.user, month=first_day).exists():
            create_month(request.user, first_day, copy_previous=request.POST.get("copy") == "1")
        return redirect(month_url(first_day))
