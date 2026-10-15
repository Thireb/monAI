"""The django-allauth adapter for monAI accounts."""

from __future__ import annotations

from django.conf import settings
from django.http import HttpRequest

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Close sign-up when the ``ACCOUNT_ALLOW_SIGNUP`` setting is false."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Return the ``ACCOUNT_ALLOW_SIGNUP`` setting (True when it is not set)."""
        return bool(getattr(settings, "ACCOUNT_ALLOW_SIGNUP", True))
