"""URL routes for account profile pages."""

from __future__ import annotations

from django.urls import URLPattern, path

from . import views

app_name = "accounts"

urlpatterns: list[URLPattern] = [
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/update/", views.ProfileUpdateView.as_view(), name="profile_update"),
]
