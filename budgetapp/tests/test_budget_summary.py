from decimal import Decimal

from django.test import TestCase

from budgetapp.models import Budget, Expense, SubExpense


class BudgetSummaryModelTests(TestCase):
    def test_net_expenses_and_returns(self):
        budget = Budget.objects.create(month="2024-02-01", income=Decimal("1000.00"))
        exp = Expense.objects.create(budget=budget, name="Rent", amount=Decimal("600.00"))
        SubExpense.objects.create(
            expense=exp, name="Deposit back", amount=Decimal("100.00"), is_return=True
        )
        self.assertEqual(budget.get_gross_budgeted_expenses(), Decimal("600.00"))
        self.assertEqual(budget.get_total_returns(), Decimal("100.00"))
        self.assertEqual(budget.get_net_budgeted_expenses(), Decimal("500.00"))
        self.assertEqual(budget.get_remaining_budget(), Decimal("500.00"))

    def test_multiple_expenses_and_returns_aggregate(self):
        budget = Budget.objects.create(month="2024-03-01", income=Decimal("1000.00"))
        e1 = Expense.objects.create(budget=budget, name="Rent", amount=Decimal("400.00"))
        SubExpense.objects.create(
            expense=e1, name="Deposit", amount=Decimal("50.00"), is_return=True
        )
        Expense.objects.create(budget=budget, name="Food", amount=Decimal("200.00"))
        self.assertEqual(budget.get_gross_budgeted_expenses(), Decimal("600.00"))
        self.assertEqual(budget.get_total_returns(), Decimal("50.00"))
        self.assertEqual(budget.get_net_budgeted_expenses(), Decimal("550.00"))
        self.assertEqual(budget.get_remaining_budget(), Decimal("450.00"))

    def test_non_return_subexpenses_do_not_reduce_budget_total_returns(self):
        budget = Budget.objects.create(month="2024-04-01", income=Decimal("500.00"))
        exp = Expense.objects.create(budget=budget, name="Utilities", amount=Decimal("200.00"))
        SubExpense.objects.create(
            expense=exp, name="Actual bill", amount=Decimal("80.00"), is_return=False
        )
        self.assertEqual(budget.get_total_returns(), Decimal("0.00"))
        self.assertEqual(budget.get_net_budgeted_expenses(), Decimal("200.00"))

    def test_get_summary_display_strings_matches_model_aggregates(self):
        budget = Budget.objects.create(month="2024-05-01", income=Decimal("900.00"))
        exp = Expense.objects.create(budget=budget, name="X", amount=Decimal("300.00"))
        SubExpense.objects.create(
            expense=exp, name="rebate", amount=Decimal("40.00"), is_return=True
        )

        def fmt(v):
            return str(v)

        s = budget.get_summary_display_strings(fmt)
        self.assertEqual(s["gross_budgeted_expenses"], budget.get_gross_budgeted_expenses())
        self.assertEqual(s["total_returns_amount"], budget.get_total_returns())
        self.assertEqual(s["net_budgeted_expenses"], budget.get_net_budgeted_expenses())
        self.assertEqual(s["remaining_budget_display"], fmt(budget.get_remaining_budget()))
