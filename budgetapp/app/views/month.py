"""Month page of the new UI, its HTMX panel and month creation."""

from __future__ import annotations

from datetime import date
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from budgetapp.app.forms import LineForm
from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import Budget
from budgetapp.services.bills import coming_up, month_bills
from budgetapp.services.home import goal_cards
from budgetapp.services.month import MonthSnapshot, build_month_snapshot
from budgetapp.services.months import budget_years, create_month, year_overview
from budgetapp.services.recap import month_recap

from .base import AppTemplateView, month_date, month_url, quick_add_context, shift_month
from .month_settings import settings_context

# Which page layout the refreshable panel renders.
PANEL_TEMPLATES = {
    "home": "app/partials/home_panel.html",
    "month": "app/partials/month_panel.html",
    "sheet": "app/partials/quick_add_chips.html",
}


def bill_context(budget: Budget | None, snap: MonthSnapshot | None, today: date) -> dict[str, Any]:
    """The month's bills, and how many of them are not lines yet."""
    if budget is None or snap is None:
        return {"month_bills": [], "unplanned_bills": 0}
    bills = month_bills(budget, snap, today)
    return {
        "month_bills": bills,
        "unplanned_bills": sum(1 for bill in bills if bill.line_id is None),
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
                **bill_context(budget, snap, today),
                **(
                    settings_context(self.request, budget)
                    if budget and not budget.is_archived
                    else {}
                ),
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
            "bills": coming_up(budget, snap, today) if view == "home" else [],
            **(bill_context(budget, snap, today) if view == "month" else {}),
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


class MonthBillsApplyView(LoginRequiredMixin, View):
    """Add the bills that are due this month but are not lines yet."""

    def post(self, request: HttpRequest, year: int, month: int) -> HttpResponse:
        """Create the bill lines and ask the page to refresh its panel."""
        budget = get_object_or_404(
            Budget, user=request.user, month=month_date(year, month), is_archived=False
        )
        apply_bill_reminders_to_budget(budget)
        response = HttpResponse(status=204)
        response["HX-Trigger"] = "monthChanged"
        return response


class MonthsView(AppTemplateView):
    """All months of 1 year (``?year=``), with their figures. Missing months can be started."""

    template_name = "app/months.html"
    nav = "months"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """The year's 12 month cards and the years to switch to."""
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        try:
            year = int(self.request.GET.get("year", today.year))
        except ValueError:
            year = today.year
        if not 2000 <= year <= 2100:
            raise Http404("No such year.")
        context.update(
            {
                "year": year,
                "years": budget_years(self.request.user, today),
                "cards": year_overview(self.request.user, year, today),
                "month_url": month_url(today),
            }
        )
        return context


class RecapView(AppTemplateView):
    """The recap of 1 month: what was kept, where most went and the best run of days."""

    template_name = "app/recap.html"
    nav = "months"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build the recap of the user's month."""
        context = super().get_context_data(**kwargs)
        first_day = month_date(self.kwargs["year"], self.kwargs["month"])
        budget = get_object_or_404(Budget, user=self.request.user, month=first_day)
        context["recap"] = month_recap(budget, timezone.localdate())
        return context
