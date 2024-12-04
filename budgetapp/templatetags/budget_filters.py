from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sum_expenses(expenses):
    """Calculate total amount of expenses"""
    return sum(expense.amount for expense in expenses) 