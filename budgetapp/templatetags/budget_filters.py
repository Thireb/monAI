from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def sum_expenses(expenses):
    """Calculate total amount of expenses"""
    return sum(expense.amount for expense in expenses)


@register.filter
def subtract(value, arg):
    """Subtract the arg from the value."""
    return value - arg
