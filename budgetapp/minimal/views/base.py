"""Base views and utilities for the minimal theme."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from budgetapp.models import Budget

# How many recent budget months the app keeps ready for offline use.
OFFLINE_BUDGET_MONTHS = 12


class LoginRequiredView(LoginRequiredMixin, View):
    """Base view that requires login for all Views."""

    pass


class LoginRequiredTemplateView(LoginRequiredMixin, TemplateView):
    """Base view that requires login for all TemplateViews."""

    pass


class UnicodeJsonResponse(JsonResponse):
    """Custom JsonResponse that doesn't escape Unicode characters."""

    def __init__(self, data: Any, **kwargs: Any) -> None:
        """Initialize with Unicode-friendly JSON serialization.

        Args:
            data: JSON-serializable payload.
            **kwargs: Forwarded to JsonResponse.
        """
        kwargs.setdefault("json_dumps_params", {"ensure_ascii": False})
        super().__init__(data, **kwargs)


class OfflineView(TemplateView):
    """Offline fallback page for PWA."""

    template_name = "minimal/offline.html"


class OfflineUrlsView(LoginRequiredMixin, View):
    """List the pages the service worker should cache for offline use.

    The list holds the home pages, the offline page and, for each recent
    budget month, its pages (new and classic) and the partials they load.
    """

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        """Return ``{"urls": [...]}`` for the logged-in user."""
        year = timezone.now().year
        urls = [
            reverse("app:home"),
            reverse("minimal:home"),
            reverse("minimal:offline"),
            reverse("minimal:calendar_content", kwargs={"year": year}),
        ]
        budgets = Budget.objects.filter(user=request.user, is_archived=False)
        for budget in budgets.order_by("-month")[:OFFLINE_BUDGET_MONTHS]:
            ym = {"year": budget.month.year, "month": budget.month.month}
            urls.append(reverse("app:month", kwargs=ym))
            for name in ("budget_detail", "summary_cards", "category_stats", "tag_stats"):
                urls.append(reverse(f"minimal:{name}", kwargs=ym))
        return JsonResponse({"urls": urls})
