"""Views for user profile display and updates."""

from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import BaseForm
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from accounts.models import CustomUser
from .forms import ProfileUpdateForm


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display the authenticated user's profile."""

    template_name = "minimal/accounts/profile.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update the authenticated user's profile fields."""

    form_class = ProfileUpdateForm
    template_name = "minimal/accounts/profile_update.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset: Any = None) -> CustomUser:
        """Return the currently logged-in user."""
        return self.request.user  # type: ignore[return-value]

    def form_valid(self, form: BaseForm) -> HttpResponse:
        """Save profile changes and show a success message."""
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)
