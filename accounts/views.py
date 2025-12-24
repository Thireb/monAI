from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView

from .forms import ProfileUpdateForm


class ProfileView(LoginRequiredMixin, TemplateView):
    """Display user profile."""

    template_name = "minimal/accounts/profile.html"


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile."""

    form_class = ProfileUpdateForm
    template_name = "minimal/accounts/profile_update.html"
    success_url = reverse_lazy("accounts:profile")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

