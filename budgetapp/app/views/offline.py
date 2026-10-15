"""The offline page and the list of pages that the service worker keeps ready offline."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView

from budgetapp.models import Budget

# How many recent months the app keeps ready for offline use.
OFFLINE_BUDGET_MONTHS = 12


class OfflineView(TemplateView):
    """The page the service worker shows for a page that is not in its cache."""

    template_name = "app/offline.html"


class OfflineUrlsView(LoginRequiredMixin, View):
    """List the pages that the service worker caches for offline use.

    The list holds the main pages, the offline page and the pages of the recent months.
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return ``{"urls": [...]}`` for the logged-in user."""
        urls = [
            reverse(name)
            for name in ("app:home", "app:offline", "app:goals", "app:months", "app:manage")
        ]
        budgets = Budget.objects.filter(user=request.user, is_archived=False)
        for budget in budgets.order_by("-month")[:OFFLINE_BUDGET_MONTHS]:
            ym = {"year": budget.month.year, "month": budget.month.month}
            urls.append(reverse("app:month", kwargs=ym))
        return JsonResponse({"urls": urls})
