"""Base views and utilities for the minimal theme."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView


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
