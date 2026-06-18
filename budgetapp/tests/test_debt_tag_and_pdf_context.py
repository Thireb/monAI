"""
Regression tests for debt/tag deletion and PDF budget context (tag breakdown).

Covers recently merged behavior: deleting a debt-tracking tag cascades debt cleanup,
and PDF email context aggregates expenses by tag for the report.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from budgetapp.minimal.views.budget import BudgetEmailPDFView
from budgetapp.models import Budget, Debt, DebtTransaction, Expense, Tag

User = get_user_model()


class TagDeleteDebtCascadeTests(TestCase):
    """Deleting a tag that backs debts removes those debts and their transactions."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="debttest",
            email="debttest@example.com",
            password="testpassword",
        )
        # Custom user model uses email as USERNAME_FIELD
        self.client.login(username="debttest@example.com", password="testpassword")
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2024, 6, 1),
            income=Decimal("5000.00"),
        )

    def test_deleting_debt_tag_removes_debts_and_transactions(self) -> None:
        debt = Debt.objects.create(
            user=self.user,
            name="Board upgrade",
            total_amount=Decimal("500.00"),
        )
        self.assertIsNotNone(debt.debt_tag_id)
        tag = debt.debt_tag
        DebtTransaction.objects.create(
            debt=debt,
            amount=Decimal("100.00"),
            date=date(2024, 6, 15),
        )
        self.assertEqual(Debt.objects.filter(user=self.user).count(), 1)
        self.assertEqual(DebtTransaction.objects.count(), 1)

        response = self.client.post(
            reverse("minimal:tag_delete"),
            {"tag_id": str(tag.id)},
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertIn("debt", payload["message"].lower())

        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
        self.assertEqual(Debt.objects.filter(user=self.user).count(), 0)
        self.assertEqual(DebtTransaction.objects.count(), 0)

    def test_deleting_tag_with_only_expenses_sets_expenses_to_no_tag(self) -> None:
        """Non-debt tags: delete leaves expenses intact with tag cleared (SET_NULL)."""
        tag = Tag.objects.create(
            user=self.user,
            name="Groceries",
            description="",
            color="#00ff00",
        )
        expense = Expense.objects.create(
            budget=self.budget,
            name="Shop",
            amount=Decimal("40.00"),
            tag_foreign_key=tag,
        )
        response = self.client.post(
            reverse("minimal:tag_delete"),
            {"tag_id": str(tag.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
        expense.refresh_from_db()
        self.assertIsNone(expense.tag_foreign_key_id)


class BudgetEmailPdfContextTests(TestCase):
    """_get_budget_context builds tag_breakdown for the PDF (account breakdown)."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="pdfctx",
            email="pdfctx@example.com",
            password="testpassword",
        )
        self.factory = RequestFactory()
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2024, 7, 1),
            income=Decimal("3000.00"),
        )
        self.tag_a = Tag.objects.create(
            user=self.user, name="Cash", description="", color="#111111"
        )
        self.tag_b = Tag.objects.create(
            user=self.user, name="Card", description="", color="#222222"
        )

    def test_tag_breakdown_aggregates_by_tag_and_percentages(self) -> None:
        Expense.objects.create(
            budget=self.budget,
            name="A1",
            amount=Decimal("100.00"),
            tag_foreign_key=self.tag_a,
        )
        Expense.objects.create(
            budget=self.budget,
            name="A2",
            amount=Decimal("50.00"),
            tag_foreign_key=self.tag_a,
        )
        Expense.objects.create(
            budget=self.budget,
            name="B1",
            amount=Decimal("50.00"),
            tag_foreign_key=self.tag_b,
        )

        request = self.factory.get("/")
        request.user = self.user
        view = BudgetEmailPDFView()
        view.request = request
        ctx = view._get_budget_context(self.budget)

        breakdown = ctx["tag_breakdown"]
        self.assertEqual(breakdown["Cash"]["amount"], 150.0)
        self.assertEqual(breakdown["Card"]["amount"], 50.0)
        self.assertEqual(breakdown["Cash"]["color"], "#111111")
        self.assertEqual(breakdown["Card"]["color"], "#222222")
        # Total expenses 200: Cash 75%, Card 25%
        self.assertAlmostEqual(breakdown["Cash"]["percentage"], 75.0, places=5)
        self.assertAlmostEqual(breakdown["Card"]["percentage"], 25.0, places=5)

    def test_tag_breakdown_empty_when_no_tagged_expenses(self) -> None:
        Expense.objects.create(
            budget=self.budget,
            name="Untagged",
            amount=Decimal("80.00"),
            tag_foreign_key=None,
        )
        request = self.factory.get("/")
        request.user = self.user
        view = BudgetEmailPDFView()
        view.request = request
        ctx = view._get_budget_context(self.budget)
        self.assertEqual(ctx["tag_breakdown"], {})
