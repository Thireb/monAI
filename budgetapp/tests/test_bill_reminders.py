"""Tests for bill reminders, dashboard window, and budget auto-lines."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from budgetapp.bill_reminder_utils import (
    apply_bill_reminders_to_budget,
    should_show_dashboard_banner,
)
from budgetapp.models import BillReminder, Budget, Category, Expense, Tag

User = get_user_model()


class BillReminderUtilsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bruser", email="br@example.com", password="pw-test-12"
        )

    def test_dashboard_banner_visible_before_billing_month(self):
        br = BillReminder(
            user=self.user,
            name="Tax",
            amount=Decimal("500"),
            next_bill_date=date(2026, 3, 20),
            remind_days_before=30,
            severity=BillReminder.Severity.HIGH,
        )
        today = date(2026, 2, 25)
        self.assertTrue(should_show_dashboard_banner(br, today))

    def test_dashboard_banner_hidden_in_billing_month(self):
        br = BillReminder(
            user=self.user,
            name="Tax",
            amount=Decimal("500"),
            next_bill_date=date(2026, 3, 20),
            remind_days_before=30,
            severity=BillReminder.Severity.HIGH,
        )
        today = date(2026, 3, 1)
        self.assertFalse(should_show_dashboard_banner(br, today))

    def test_apply_bill_reminder_creates_expense_and_advances(self):
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

    def test_apply_skips_when_linked_expense_exists(self):
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
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="vuser", email="v@example.com", password="pw-test-12"
        )
        self.client.login(email="v@example.com", password="pw-test-12")

    def test_bill_reminder_list_renders(self):
        url = reverse("minimal:bill_reminder_list")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Bill reminders")

    def test_defaults_view_returns_json(self):
        url = reverse("minimal:bill_reminder_defaults")
        r = self.client.get(url, {"next_bill_date": "2029-06-01"})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["remind_days_before"], 30)

    def test_budget_create_applies_reminder(self):
        BillReminder.objects.create(
            user=self.user,
            name="Property tax",
            amount=Decimal("800.00"),
            next_bill_date=date(2030, 4, 5),
            remind_days_before=7,
        )
        url = reverse("minimal:budget_create")
        r = self.client.post(
            url,
            {
                "copy_recurring": "false",
                "target_year": "2030",
                "target_month": "4",
            },
        )
        self.assertEqual(r.status_code, 200)
        b = Budget.objects.get(user=self.user, month=date(2030, 4, 1))
        self.assertEqual(b.expenses.count(), 1)
        self.assertEqual(b.expenses.first().name, "Property tax")


class BillReminderExpenseSyncTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="euser", email="e@example.com", password="pw-test-12"
        )
        self.client.login(email="e@example.com", password="pw-test-12")
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2031, 2, 1),
            income=Decimal("3000"),
        )
        self.cat = Category.objects.create(
            user=self.user, name="Bills", slug="bills", color="#111111"
        )
        self.tag = Tag.objects.create(user=self.user, name="Home", slug="home", color="#2196f3")

    def test_expense_post_creates_reminder(self):
        url = reverse(
            "minimal:expense_create_update",
            kwargs={"year": 2031, "month": 2},
        )
        r = self.client.post(
            url,
            {
                "name": "Insurance",
                "amount": "99.50",
                "category": str(self.cat.id),
                "tag": str(self.tag.id),
                "bill_reminder_enabled": "on",
                "bill_reminder_next_date": "2032-01-10",
                "bill_reminder_days_before": "45",
                "bill_reminder_severity": BillReminder.Severity.LOW,
                "bill_reminder_recurrence_months": "12",
            },
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data["status"], "success")
        exp = Expense.objects.get(pk=data["expense"]["id"])
        self.assertIsNotNone(exp.bill_reminder_id)
        br = BillReminder.objects.get(pk=exp.bill_reminder_id)
        self.assertEqual(br.name, "Insurance")
        self.assertEqual(br.remind_days_before, 45)
        self.assertEqual(br.next_bill_date, date(2032, 1, 10))
