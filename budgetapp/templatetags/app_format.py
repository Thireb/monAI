"""Display filters for the new UI (/app/)."""

from __future__ import annotations

from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, InvalidOperation
from typing import Any

from django import template

register = template.Library()


@register.filter
def money(value: Any) -> str:
    """Format a number as ``12,150`` or ``12,150.50`` (cents only when they are not 0).

    The sign stays: ``-300``. ``None`` and text that is not a number give ``""``.
    """
    if value is None or value == "":
        return ""
    try:
        number = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError):
        return ""
    text = f"{abs(number):,.2f}"
    if text.endswith(".00"):
        text = text[:-3]
    return f"-{text}" if number < 0 else text


@register.filter
def money_whole(value: Any, direction: str = "down") -> str:
    """Format a number without cents: ``1,965``.

    ``direction`` is ``down`` (default) or ``up``. Round "safe to spend" amounts down and
    "over by" amounts up, so the app never shows more room than there is.
    """
    if value is None or value == "":
        return ""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return ""
    rounding = ROUND_CEILING if direction == "up" else ROUND_FLOOR
    whole = number.quantize(Decimal("1"), rounding=rounding)
    return money(whole)


@register.filter
def absolute(value: Any) -> Any:
    """Return the absolute value of a number (for "over by 300" texts)."""
    try:
        return abs(value)
    except TypeError:
        return value
