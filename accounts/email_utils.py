"""Helpers for per-user Resend email configuration."""

from __future__ import annotations

from accounts.models import CustomUser


def user_has_resend_config(user: CustomUser) -> bool:
    """Return True when the user has both API key and from email set."""
    return bool((user.resend_api_key or "").strip() and (user.resend_from_email or "").strip())


def get_user_resend_credentials(user: CustomUser) -> tuple[str, str] | None:
    """Return (api_key, from_email) for the user, or None if not configured."""
    api_key = (user.resend_api_key or "").strip()
    from_email = (user.resend_from_email or "").strip()
    if api_key and from_email:
        return api_key, from_email
    return None


def resend_not_configured_message() -> str:
    """User-facing message when Resend is not set on the profile."""
    return (
        "Resend is not configured for your account. "
        "Add your Resend API key and from email under Profile → Edit Profile. "
        "Until then, budget PDF emails cannot be sent (Django system mail uses console "
        "unless SMTP is configured in config.yaml)."
    )
