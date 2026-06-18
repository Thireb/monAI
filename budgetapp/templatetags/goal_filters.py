"""Template filters for goal-related calculations."""

from __future__ import annotations

from typing import Any

from django import template

register = template.Library()


@register.filter
def sub(value: Any, arg: Any) -> Any:
    """Subtract the arg from the value.

    Args:
        value: Minuend.
        arg: Subtrahend.

    Returns:
        ``value - arg``, or the original value on type errors.
    """
    try:
        return value - arg
    except (ValueError, TypeError):
        return value
