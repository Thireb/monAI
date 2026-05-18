"""
Home and calendar views.
"""

import calendar
import json
from datetime import date

from django.http import JsonResponse
from django.template.loader import render_to_string

from budgetapp.bill_reminder_utils import dashboard_banner_reminders_for_user
from budgetapp.models import Budget

from .base import LoginRequiredTemplateView, LoginRequiredView


def get_calendar_context_for_year(selected_year, budgets_by_year_month, today):
    """
    Generate calendar context data for a single year.
    Uses pre-fetched budget data to avoid extra queries.
    """
    months = [calendar.month_name[i] for i in range(1, 13)]
    abbrs = [calendar.month_abbr[i] for i in range(1, 13)]

    # Get budgets for this specific year
    budgets_by_month = budgets_by_year_month.get(selected_year, {})

    months_data = []
    for i, (month_name, abbr) in enumerate(zip(months, abbrs), 1):
        # Determine month status based on year comparison
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

    # Group into 3 rows of 4 months each, right-to-left
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


class HomeView(LoginRequiredTemplateView):
    template_name = "minimal/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        selected_year = self.kwargs.get("year", today.year)

        # Prefetch 5 years of data (current ± 2) in a single query
        years_to_cache = range(selected_year - 2, selected_year + 3)
        min_year = selected_year - 2
        max_year = selected_year + 2

        # Single query for all budgets in the 5-year range
        all_budgets = Budget.objects.filter(
            user=self.request.user,
            is_archived=False,
            month__year__gte=min_year,
            month__year__lte=max_year,
        )

        # Organize budgets by year and month
        budgets_by_year_month = {}
        for budget in all_budgets:
            year = budget.month.year
            month = budget.month.month
            if year not in budgets_by_year_month:
                budgets_by_year_month[year] = {}
            budgets_by_year_month[year][month] = budget

        # Generate calendar data for current year (for initial render)
        current_context = get_calendar_context_for_year(
            selected_year, budgets_by_year_month, today
        )
        context.update(current_context)

        # Pre-render HTML for all 5 years and store as JSON for JavaScript
        cached_calendars = {}
        for year in years_to_cache:
            year_context = get_calendar_context_for_year(
                year, budgets_by_year_month, today
            )
            html = render_to_string(
                "minimal/components/calendar_content.html",
                year_context,
                request=self.request,
            )
            cached_calendars[str(year)] = html

        # Serialize to JSON string for safe embedding in JavaScript
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

        # Fetch budgets for this specific year
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

        context = get_calendar_context_for_year(selected_year, budgets_by_year_month, today)
        html = render_to_string(
            "minimal/components/calendar_content.html",
            context,
            request=request,
        )
        return JsonResponse({"html": html, "year": selected_year})
