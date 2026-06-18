"""Template filters for budget expense calculations."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from django import template

register = template.Library()


@register.filter
def sum_expenses(expenses: Any) -> Decimal | int:
    """Calculate total amount of expenses.

    Args:
        expenses: Iterable of expense objects with an ``amount`` attribute.

    Returns:
        Sum of expense amounts.
    """
    return sum(expense.amount for expense in expenses)


@register.filter
def subtract(value: Decimal | float | int, arg: Decimal | float | int) -> Decimal | float | int:
    """Subtract the arg from the value.

    Args:
        value: Minuend.
        arg: Subtrahend.

    Returns:
        ``value - arg``.
    """
    return value - arg


@register.filter
def get_item(dictionary: dict[Any, Any], key: Any) -> Any:
    """Return ``dictionary[key]`` or ``0`` when the key is missing.

    Args:
        dictionary: Mapping to look up.
        key: Key to retrieve.

    Returns:
        Value at key, or ``0`` if absent.
    """
    return dictionary.get(key, 0)
