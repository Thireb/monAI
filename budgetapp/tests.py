from decimal import Decimal

from django.test import Client, TestCase
from django.urls import reverse

from .models import Budget, Expense


class BudgetTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.budget = Budget.objects.create(month="2024-01-01", income=Decimal("1000.00"))

    def test_budget_remaining(self):
        Expense.objects.create(budget=self.budget, name="Test Expense", amount=Decimal("500.00"))
        self.assertEqual(self.budget.get_remaining_budget(), Decimal("500.00"))

    def test_delete_budget(self):
        response = self.client.post(
            reverse("delete_budget", kwargs={"year_month": "2024-01"}),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Budget.objects.filter(id=self.budget.id).exists())
