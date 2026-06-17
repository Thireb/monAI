"""
Home and calendar views.
"""

import calendar
import json
import time
from datetime import date

from django.http import JsonResponse
from django.template.loader import render_to_string

from budgetapp.bill_reminder_utils import dashboard_banner_reminders_for_user
from budgetapp.calendar_cache import get_cached_calendar_year, set_cached_calendar_year
from budgetapp.models import Budget
from budget_tracker.config import get_learning_demo_config

from .base import LoginRequiredTemplateView, LoginRequiredView


def _apply_learning_demo_calendar_delay() -> None:
    """Sleep to simulate a slow DB query (toggle via config.yaml learning_demo)."""
    delay_seconds = get_learning_demo_config().get("calendar_query_delay_seconds", 0) or 0
    if delay_seconds > 0:
        time.sleep(float(delay_seconds))


def get_calendar_context_for_year(selected_year, budgets_by_year_month, today):
    """
    Generate calendar context data for a single year.
    Uses pre-fetched budget data to avoid extra queries.
    """
    months = [calendar.month_name[i] for i in range(1, 13)]
    abbrs = [calendar.month_abbr[i] for i in range(1, 13)]

    budgets_by_month = budgets_by_year_month.get(selected_year, {})

    months_data = []
    for i, (month_name, abbr) in enumerate(zip(months, abbrs), 1):
        if selected_year < today.year:
            status = "past" if i in budgets_by_month else "future"
        elif selected_year > today.year:
            status = "future-created" if i in budgets_by_month else "future"
        else:
            if i < today.month:
                status = "past" if i in budgets_by_month else "future"
            elif i == today.month:
                status = "current" if i in budgets_by_month else "future"
            else:
                status = "future-created" if i in budgets_by_month else "future"

        months_data.append(
            {
                "name": month_name,
                "abbr": abbr,
                "status": status,
                "number": i,
            }
        )

    months_grid = []
    for i in range(0, 12, 4):
        row = months_data[i : i + 4][::-1]
        months_grid.append(row)

    return {
        "months_grid": months_grid,
        "year": selected_year,
        "prev_year": selected_year - 1,
        "next_year": selected_year + 1,
    }


def _organize_budgets_by_year_month(budgets) -> dict[int, dict[int, Budget]]:
    budgets_by_year_month: dict[int, dict[int, Budget]] = {}
    for budget in budgets:
        year = budget.month.year
        month = budget.month.month
        if year not in budgets_by_year_month:
            budgets_by_year_month[year] = {}
        budgets_by_year_month[year][month] = budget
    return budgets_by_year_month


def _fetch_budgets_for_year_range(user, min_year: int, max_year: int):
    _apply_learning_demo_calendar_delay()
    return Budget.objects.filter(
        user=user,
        is_archived=False,
        month__year__gte=min_year,
        month__year__lte=max_year,
    )


def _build_calendar_year_payload(request, year: int, budgets_by_year_month, today):
    context = get_calendar_context_for_year(year, budgets_by_year_month, today)
    html = render_to_string(
        "minimal/components/calendar_content.html",
        context,
        request=request,
    )
    return {"html": html, "context": context}


class HomeView(LoginRequiredTemplateView):
    template_name = "minimal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        selected_year = self.kwargs.get("year", today.year)
        min_year = selected_year - 2
        max_year = selected_year + 2
        years_to_cache = range(min_year, max_year + 1)

        cached_calendars = {}
        missing_years = []
        for year in years_to_cache:
            cached = get_cached_calendar_year(self.request.user.pk, year)
            if cached is not None:
                cached_calendars[str(year)] = cached["html"]
            else:
                missing_years.append(year)

        if missing_years:
            all_budgets = _fetch_budgets_for_year_range(
                self.request.user,
                min_year,
                max_year,
            )
            budgets_by_year_month = _organize_budgets_by_year_month(all_budgets)
            for year in missing_years:
                payload = _build_calendar_year_payload(
                    self.request,
                    year,
                    budgets_by_year_month,
                    today,
                )
                set_cached_calendar_year(self.request.user.pk, year, payload)
                cached_calendars[str(year)] = payload["html"]

        selected_payload = get_cached_calendar_year(self.request.user.pk, selected_year)
        if selected_payload is not None:
            context.update(selected_payload["context"])
        else:
            context.update(
                get_calendar_context_for_year(selected_year, {}, today)
            )

        context["cached_calendars_json"] = json.dumps(cached_calendars)
        context["cache_min_year"] = min_year
        context["cache_max_year"] = max_year

        banners = dashboard_banner_reminders_for_user(self.request.user, today)
        context["bill_reminder_banners"] = [
            {
                "id": r.id,
                "text": f"{r.name} — due {r.next_bill_date.strftime('%b %d, %Y')}",
                "severity": r.severity,
            }
            for r in banners
        ]

        return context


class CalendarContentView(LoginRequiredView):
    """AJAX view to return calendar content HTML for a given year (fallback for uncached years)."""

    def get(self, request, *args, **kwargs):
        selected_year = kwargs.get("year", date.today().year)
        today = date.today()

        cached = get_cached_calendar_year(request.user.pk, selected_year)
        if cached is not None:
            return JsonResponse({"html": cached["html"], "year": selected_year})

        _apply_learning_demo_calendar_delay()
        budgets_by_year_month = {
            selected_year: {
                b.month.month: b
                for b in Budget.objects.filter(
                    user=request.user,
                    is_archived=False,
                    month__year=selected_year,
                )
            }
        }

        payload = _build_calendar_year_payload(
            request,
            selected_year,
            budgets_by_year_month,
            today,
        )
        set_cached_calendar_year(request.user.pk, selected_year, payload)
        return JsonResponse({"html": payload["html"], "year": selected_year})
