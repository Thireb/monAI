"""
Regression tests for account (tag) deletion and the PDF report context (tag breakdown).

Deleting an account keeps its lines, and the PDF report adds up the lines by account.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from budgetapp.models import Budget, Expense, Tag
from budgetapp.services.report import report_context

User = get_user_model()


class TagDeleteTests(TestCase):
    """Deleting an account on the More page keeps its lines (SET_NULL)."""

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
            reverse("app:manage_delete", kwargs={"kind": "account", "pk": tag.id})
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
        expense.refresh_from_db()
        self.assertIsNone(expense.tag_foreign_key_id)


class BudgetEmailPdfContextTests(TestCase):
    """report_context builds tag_breakdown for the PDF (account breakdown)."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="pdfctx",
            email="pdfctx@example.com",
            password="testpassword",
        )
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

        ctx = report_context(self.budget)

        breakdown = ctx["tag_breakdown"]
        self.assertEqual(breakdown["Cash"]["amount"], Decimal("150"))
        self.assertEqual(breakdown["Card"]["amount"], Decimal("50"))
        self.assertEqual(breakdown["Cash"]["amount_display"], "150.00")
        self.assertEqual(breakdown["Cash"]["color"], "#111111")
        self.assertEqual(breakdown["Card"]["color"], "#222222")
        # Total expenses 200: Cash 75%, Card 25%
        self.assertEqual(breakdown["Cash"]["percentage"], Decimal("75"))
        self.assertEqual(breakdown["Card"]["percentage_display"], "25.0")

    def test_tag_breakdown_empty_when_no_tagged_expenses(self) -> None:
        Expense.objects.create(
            budget=self.budget,
            name="Untagged",
            amount=Decimal("80.00"),
            tag_foreign_key=None,
        )
        ctx = report_context(self.budget)
        self.assertEqual(ctx["tag_breakdown"], {})
