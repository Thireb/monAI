"""
URL configuration for budget_tracker project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path, re_path

from rest_framework.authtoken.views import obtain_auth_token

from budgetapp.views import service_worker


def redirect_to_minimal(request):
    """Redirect root URL to minimal theme."""
    return redirect("minimal:home")


urlpatterns = [
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
    path("", redirect_to_minimal, name="root_redirect"),
    path("minimal/", include("budgetapp.minimal.urls", namespace="minimal")),
]
