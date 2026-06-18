"""Tests for budget summary calculations on Budget model helpers."""
from __future__ import annotations

from decimal import Decimal

from django.test import TestCase

from budgetapp.models import Budget, Expense, SubExpense


class BudgetSummaryModelTests(TestCase):
    """Verify gross, net, and return calculations on budgets."""

    def test_net_expenses_and_returns(self) -> None:
        """Net expenses subtract returns from gross budgeted expense totals."""
        budget = Budget.objects.create(month="2024-02-01", income=Decimal("1000.00"))
        exp = Expense.objects.create(budget=budget, name="Rent", amount=Decimal("600.00"))
        SubExpense.objects.create(
            expense=exp, name="Deposit back", amount=Decimal("100.00"), is_return=True
        )
        self.assertEqual(budget.get_gross_budgeted_expenses(), Decimal("600.00"))
        self.assertEqual(budget.get_total_returns(), Decimal("100.00"))
        self.assertEqual(budget.get_net_budgeted_expenses(), Decimal("500.00"))
        self.assertEqual(budget.get_remaining_budget(), Decimal("500.00"))
