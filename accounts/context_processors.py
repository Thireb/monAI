"""Template context for the account pages."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest


def signup(request: HttpRequest) -> dict[str, bool]:
    """Tell templates if sign-up is open, so the login page can hide its link."""
    return {"signup_open": bool(getattr(settings, "ACCOUNT_ALLOW_SIGNUP", True))}
