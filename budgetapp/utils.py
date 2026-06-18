"""Utility functions for the budgetapp.

Shared helpers used across views, APIs, and other application modules.
"""

from __future__ import annotations

from typing import Any

from django.contrib.humanize.templatetags.humanize import intcomma
from django.http import JsonResponse


def format_currency(val: float) -> str:
    """Format a float value with comma separator and two decimal places.

    Args:
        val: The numeric value to format.

    Returns:
        Formatted string like ``12,345.67``.

    Example:
        >>> format_currency(12345.67)
        '12,345.67'
    """
    return intcomma(f"{val:,.2f}")


def success_response(
    message: str,
    data: dict[str, Any] | None = None,
    status: int = 200,
) -> JsonResponse:
    """Create a standardized success JSON response.

    Args:
        message: Success message to include.
        data: Additional data to merge into the response body.
        status: HTTP status code (default 200).

    Returns:
        JsonResponse with ``success=True`` and the message.
    """
    response: dict[str, Any] = {"success": True, "message": message}
    if data:
        response.update(data)
    return JsonResponse(response, status=status)


def error_response(message: str, status: int = 400) -> JsonResponse:
    """Create a standardized error JSON response.

    Args:
        message: Error message to include.
        status: HTTP status code (default 400).

    Returns:
        JsonResponse with ``success=False`` and the error message.
    """
    return JsonResponse({"success": False, "error": message}, status=status)


class UnicodeJsonResponse(JsonResponse):
    """JsonResponse that preserves non-ASCII characters in JSON output."""

    def __init__(self, data: Any, **kwargs: Any) -> None:
        """Initialize with Unicode-friendly JSON serialization.

        Args:
            data: JSON-serializable payload.
            **kwargs: Forwarded to JsonResponse.
        """
        kwargs.setdefault("json_dumps_params", {"ensure_ascii": False})
        super().__init__(data, **kwargs)
