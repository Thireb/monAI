"""REST API coverage for budget aggregates (gross, returns, net, remaining)."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from budgetapp.models import Budget, Expense, SubExpense

User = get_user_model()


class BudgetViewSetAggregateTests(TestCase):
    """BudgetSerializer.to_representation must stay aligned with Budget model math."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="api_budget_user",
            email="api_budget@example.com",
            password="api-budget-pass-secure",
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_detail_exposes_gross_returns_net_and_remaining(self):
        budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 6, 1),
            income=Decimal("1000.00"),
            currency="PKR",
        )
        exp = Expense.objects.create(budget=budget, name="Rent", amount=Decimal("600.00"))
        SubExpense.objects.create(
            expense=exp, name="Deposit back", amount=Decimal("100.00"), is_return=True
        )
        url = reverse("api-budget-detail", kwargs={"pk": budget.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data["total_expenses"])), Decimal("600.00"))
        self.assertEqual(Decimal(str(response.data["total_returns"])), Decimal("100.00"))
        self.assertEqual(Decimal(str(response.data["net_expenses"])), Decimal("500.00"))
        self.assertEqual(Decimal(str(response.data["remaining_budget"])), Decimal("500.00"))

    def test_aggregates_across_multiple_expense_lines(self):
        budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 7, 1),
            income=Decimal("1000.00"),
            currency="PKR",
        )
        e1 = Expense.objects.create(budget=budget, name="A", amount=Decimal("400.00"))
        SubExpense.objects.create(
            expense=e1, name="r1", amount=Decimal("50.00"), is_return=True
        )
        Expense.objects.create(budget=budget, name="B", amount=Decimal("200.00"))
        url = reverse("api-budget-detail", kwargs={"pk": budget.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Decimal(str(response.data["total_expenses"])), Decimal("600.00"))
        self.assertEqual(Decimal(str(response.data["total_returns"])), Decimal("50.00"))
        self.assertEqual(Decimal(str(response.data["net_expenses"])), Decimal("550.00"))
        self.assertEqual(Decimal(str(response.data["remaining_budget"])), Decimal("450.00"))

    def test_list_includes_aggregate_fields_per_budget(self):
        budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 8, 1),
            income=Decimal("300.00"),
            currency="PKR",
        )
        url = reverse("api-budget-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        row = response.data[0]
        self.assertEqual(Decimal(str(row["total_expenses"])), Decimal("0.00"))
        self.assertEqual(Decimal(str(row["total_returns"])), Decimal("0.00"))
        self.assertEqual(Decimal(str(row["net_expenses"])), Decimal("0.00"))
        self.assertEqual(Decimal(str(row["remaining_budget"])), Decimal("300.00"))
        self.assertEqual(row["id"], budget.id)

    def test_cannot_read_other_users_budget(self):
        other = User.objects.create_user(
            username="other_budget",
            email="other_budget@example.com",
            password="other-budget-pass-secure",
        )
        b = Budget.objects.create(
            user=other,
            month=date(2025, 9, 1),
            income=Decimal("100.00"),
            currency="PKR",
        )
        url = reverse("api-budget-detail", kwargs={"pk": b.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
