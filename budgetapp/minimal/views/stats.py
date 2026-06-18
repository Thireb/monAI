"""Statistics views for category and tag stats."""

from __future__ import annotations

from typing import Any

from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone

from budgetapp.models import Budget

from .base import LoginRequiredView


class CategoryStatsView(LoginRequiredView):
    """View for AJAX updates to category statistics."""

    def _format_currency(self, val: float) -> str:
        """Format a float as a comma-separated currency string.

        Args:
            val: Numeric value to format.

        Returns:
            Formatted string with two decimal places.
        """
        return intcomma(f"{val:,.2f}")

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Return rendered category stats HTML for the budget month."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=self.request.user
        )

        expenses_qs = budget.expenses.all()
        total_expenses = sum(e.amount for e in expenses_qs)

        expenses_by_category = {}
        if expenses_qs.exists():
            category_totals = {}
            for expense in expenses_qs:
                cat = expense.category.name if expense.category else "Uncategorized"
                if cat not in category_totals:
                    category_totals[cat] = {
                        "amount": 0,
                        "color": expense.category.color if expense.category else "#e0e0e0",
                    }
                category_totals[cat]["amount"] += float(expense.amount)
            for cat, data in category_totals.items():
                percent = (data["amount"] / float(total_expenses) * 100) if total_expenses else 0
                expenses_by_category[cat] = {
                    "amount": data["amount"],
                    "amount_display": self._format_currency(data["amount"]),
                    "color": data["color"],
                    "percentage": percent,
                    "percentage_display": f"{percent:.1f}",
                }

        context = {
            "budget": budget,
            "expenses_by_category": expenses_by_category,
        }

        html = render_to_string("minimal/budget_detail_pages/category_stats_content.html", context)
        return JsonResponse({"html": html})


class TagStatsView(LoginRequiredView):
    """View for AJAX updates to tag statistics."""

    def _format_currency(self, val: float) -> str:
        """Format a float as a comma-separated currency string.

        Args:
            val: Numeric value to format.

        Returns:
            Formatted string with two decimal places.
        """
        return intcomma(f"{val:,.2f}")

    def get(
        self,
        request: HttpRequest,
        *args: Any,
        **kwargs: Any,
    ) -> JsonResponse:
        """Return rendered tag stats HTML for the budget month."""
        year = kwargs.get("year")
        month = kwargs.get("month")
        budget_date = timezone.datetime(year=year, month=month, day=1).date()
        budget = get_object_or_404(
            Budget, month=budget_date, is_archived=False, user=self.request.user
        )

        expenses_qs = budget.expenses.all()

        tag_totals = {}
        tag_labels = {}
        for expense in expenses_qs:
            if expense.tag_foreign_key:
                tag_name = expense.tag_foreign_key.name
                if tag_name not in tag_totals:
                    tag_totals[tag_name] = 0
                    tag_labels[tag_name] = tag_name
                tag_totals[tag_name] += float(expense.amount)

        context = {
            "budget": budget,
            "tag_totals": tag_totals,
            "tag_labels": tag_labels,
        }

        html = render_to_string("minimal/budget_detail_pages/tag_stats_content.html", context)
        return JsonResponse({"html": html})
