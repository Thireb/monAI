"""Tests for TagTransfer and account-tag breakdown."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from budgetapp.models import Budget, Expense, Tag, TagTransfer

User = get_user_model()


class TagTransferModelTests(TestCase):
    """Tag transfers must not change remaining budget; they adjust breakdown."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="xfer",
            email="xfer@example.com",
            password="testpassword",
        )
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2024, 7, 1),
            income=Decimal("1000.00"),
        )
        self.cash = Tag.objects.create(user=self.user, name="Cash", slug="cash", color="#4caf50")
        self.bank = Tag.objects.create(user=self.user, name="Bank", slug="bank", color="#2196f3")
        Expense.objects.create(
            budget=self.budget,
            name="Groceries",
            amount=Decimal("300.00"),
            tag_foreign_key=self.cash,
        )

    def test_transfer_does_not_change_remaining(self) -> None:
        before = self.budget.get_remaining_budget()
        TagTransfer.objects.create(
            budget=self.budget,
            from_tag=self.cash,
            to_tag=self.bank,
            amount=Decimal("100.00"),
        )
        self.assertEqual(self.budget.get_remaining_budget(), before)
        self.assertEqual(before, Decimal("700.00"))

    def test_breakdown_adjusts_for_transfer(self) -> None:
        TagTransfer.objects.create(
            budget=self.budget,
            from_tag=self.cash,
            to_tag=self.bank,
            amount=Decimal("100.00"),
        )
        breakdown = self.budget.get_tag_account_breakdown()
        self.assertEqual(breakdown["Cash"]["amount"], Decimal("200.00"))
        self.assertEqual(breakdown["Bank"]["amount"], Decimal("100.00"))

    def test_same_tag_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            TagTransfer.objects.create(
                budget=self.budget,
                from_tag=self.cash,
                to_tag=self.cash,
                amount=Decimal("50.00"),
            )


class TagTransferViewTests(TestCase):
    """Create and delete a transfer in the month settings of the new UI."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="xferweb",
            email="xferweb@example.com",
            password="testpassword",
        )
        self.client.login(username="xferweb@example.com", password="testpassword")
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2024, 8, 1),
            income=Decimal("2000.00"),
        )
        self.cash = Tag.objects.create(user=self.user, name="Cash", slug="cash-w", color="#4caf50")
        self.bank = Tag.objects.create(user=self.user, name="Bank", slug="bank-w", color="#2196f3")
        Expense.objects.create(
            budget=self.budget,
            name="Rent",
            amount=Decimal("500.00"),
            tag_foreign_key=self.cash,
        )

    def test_create_and_delete_transfer_keep_remaining(self) -> None:
        create_url = reverse("app:transfer_create", kwargs={"year": 2024, "month": 8})
        remaining_before = self.budget.get_remaining_budget()
        resp = self.client.post(
            create_url,
            {
                "transfer-from_tag": self.cash.id,
                "transfer-to_tag": self.bank.id,
                "transfer-amount": "150.00",
                "transfer-note": "Moved float",
            },
        )
        self.assertContains(resp, "Moved 150 from Cash to Bank.")
        self.assertEqual(TagTransfer.objects.count(), 1)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.get_remaining_budget(), remaining_before)

        transfer = TagTransfer.objects.get()
        del_resp = self.client.post(reverse("app:transfer_delete", kwargs={"pk": transfer.id}))
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(TagTransfer.objects.count(), 0)
