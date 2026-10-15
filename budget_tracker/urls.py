"""
URL configuration for budget_tracker project.

The ``urlpatterns`` list routes URLs to views. See:
https://docs.djangoproject.com/en/5.1/topics/http/urls/
"""

from __future__ import annotations

from django.contrib import admin
from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import URLPattern, URLResolver, include, path, re_path

from rest_framework.authtoken.views import obtain_auth_token

from budgetapp.views import service_worker


def redirect_to_app(request: HttpRequest) -> HttpResponseRedirect:
    """Redirect the root URL to the home page of the new UI (/app/)."""
    return redirect("app:home")


urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("api/", include("budgetapp.api_urls")),
    path("api-token-auth/", obtain_auth_token, name="api_token_auth"),
    # Service worker must be at root level for PWA
    re_path(r"^service-worker\.js$", service_worker, name="service_worker"),
    # Authentication URLs (django-allauth)
    path("accounts/", include("allauth.urls")),
    # Profile URLs
    path("accounts/", include("accounts.urls", namespace="accounts")),
    # Redirect root to minimal theme
    path("", redirect_to_app, name="root_redirect"),
    path("minimal/", include("budgetapp.minimal.urls", namespace="minimal")),
    path("app/", include("budgetapp.app.urls", namespace="app")),
]
