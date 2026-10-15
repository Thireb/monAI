"""Tests for bill reminders: the start of the alert window and the lines added to a month."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget, reminder_start_date
from budgetapp.models import BillReminder, Budget, Expense

User = get_user_model()


class BillReminderUtilsTests(TestCase):
    """Unit tests for bill reminder utility helpers."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="bruser", email="br@example.com", password="pw-test-12"
        )

    def test_reminder_starts_days_before_the_due_date(self) -> None:
        br = BillReminder(
            user=self.user,
            name="Tax",
            amount=Decimal("500"),
            next_bill_date=date(2026, 3, 20),
            remind_days_before=30,
        )
        self.assertEqual(reminder_start_date(br), date(2026, 2, 18))

    def test_apply_bill_reminder_creates_expense_and_advances(self) -> None:
        br = BillReminder.objects.create(
            user=self.user,
            name="Annual fee",
            amount=Decimal("120.00"),
            next_bill_date=date(2027, 5, 10),
            remind_days_before=14,
            recurrence_months=12,
        )
        budget = Budget.objects.create(
            user=self.user,
            month=date(2027, 5, 1),
            income=Decimal("2000.00"),
        )
        n = apply_bill_reminders_to_budget(budget)
        self.assertEqual(n, 1)
        self.assertEqual(budget.expenses.count(), 1)
        exp = budget.expenses.first()
        self.assertEqual(exp.name, "Annual fee")
        self.assertEqual(exp.bill_reminder_id, br.id)
        br.refresh_from_db()
        self.assertEqual(br.next_bill_date, date(2028, 5, 10))

    def test_apply_skips_when_linked_expense_exists(self) -> None:
        br = BillReminder.objects.create(
            user=self.user,
            name="Fee",
            amount=Decimal("50.00"),
            next_bill_date=date(2028, 1, 15),
        )
        budget = Budget.objects.create(
            user=self.user, month=date(2028, 1, 1), income=Decimal("100")
        )
        Expense.objects.create(
            budget=budget,
            name="Fee",
            amount=Decimal("50"),
            bill_reminder=br,
        )
        old_due = br.next_bill_date
        n = apply_bill_reminders_to_budget(budget)
        self.assertEqual(n, 0)
        br.refresh_from_db()
        self.assertEqual(br.next_bill_date, old_due)


class BillReminderViewTests(TestCase):
    """Bill reminders in the new UI: the More page lists them, a new month gets their lines."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="vuser", email="v@example.com", password="pw-test-12"
        )
        self.client.login(email="v@example.com", password="pw-test-12")

    def test_more_page_lists_bill_reminders(self) -> None:
        BillReminder.objects.create(
            user=self.user,
            name="Car insurance",
            amount=Decimal("120.00"),
            next_bill_date=date(2030, 6, 1),
        )
        r = self.client.get(reverse("app:manage"))
        self.assertContains(r, "Bill reminders")
        self.assertContains(r, "Car insurance")

    def test_month_create_applies_reminder(self) -> None:
        BillReminder.objects.create(
            user=self.user,
            name="Property tax",
            amount=Decimal("800.00"),
            next_bill_date=date(2030, 4, 5),
            remind_days_before=7,
        )
        r = self.client.post(reverse("app:month_create", kwargs={"year": 2030, "month": 4}))
        self.assertEqual(r.status_code, 302)
        b = Budget.objects.get(user=self.user, month=date(2030, 4, 1))
        self.assertEqual(b.expenses.count(), 1)
        self.assertEqual(b.expenses.first().name, "Property tax")
