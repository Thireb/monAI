"""Tests for the new UI: the More page, the Months page and the month settings."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import (
    BillReminder,
    Budget,
    Category,
    Debt,
    Expense,
    IncomeHistory,
    Tag,
    TagTransfer,
)
from budgetapp.services.months import year_overview

User = get_user_model()
D = Decimal


class ManageBase(TestCase):
    """A user with 2 accounts, a category and this month's budget."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="more", email="more@example.com", password="testpassword"
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        self.cash = Tag.objects.create(user=self.user, name="Cash", slug="cash")
        self.bank = Tag.objects.create(user=self.user, name="Bank", slug="bank")
        self.food = Category.objects.create(user=self.user, name="Food", slug="food")
        self.budget = Budget.objects.create(
            user=self.user, month=self.today.replace(day=1), income=D("50000")
        )
        self.kw = {"year": self.today.year, "month": self.today.month}

    def other_user(self) -> object:
        return User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )


class ManageTests(ManageBase):
    """Accounts, categories and bills on the More page."""

    def test_page_lists_items(self) -> None:
        BillReminder.objects.create(
            user=self.user, name="Car tax", amount=D("4000"), next_bill_date=date(2027, 3, 1)
        )
        page = self.client.get(reverse("app:manage"))
        for text in ("Cash", "Bank", "Food", "Car tax", "4,000"):
            self.assertContains(page, text)

    def test_create_account_and_rename_moves_the_slug(self) -> None:
        url = reverse("app:manage_new", kwargs={"kind": "account"})
        response = self.client.post(
            url, {"account-name": "Wallet", "account-color": "#112233", "account-is_active": "on"}
        )
        self.assertContains(response, "Saved the account &quot;Wallet&quot;.")
        self.assertContains(response, "data-sheet-done")
        self.assertIn("manageChanged", response["HX-Trigger"])
        wallet = Tag.objects.get(name="Wallet")
        self.assertEqual((wallet.user, wallet.slug, wallet.color), (self.user, "wallet", "#112233"))
        url = reverse("app:manage_item", kwargs={"kind": "account", "pk": self.cash.pk})
        self.client.post(url, {"account-name": "Pocket", "account-color": "#2e8b57"})
        self.cash.refresh_from_db()
        self.assertEqual(
            (self.cash.name, self.cash.slug, self.cash.is_active), ("Pocket", "pocket", False)
        )
        # The old name is free again.
        response = self.client.post(
            reverse("app:manage_new", kwargs={"kind": "account"}),
            {"account-name": "Cash", "account-color": "#2e8b57"},
        )
        self.assertContains(response, "data-sheet-done")

    def test_duplicate_and_bad_names(self) -> None:
        url = reverse("app:manage_new", kwargs={"kind": "category"})
        for name, error in (("food", "already have one"), ("Food!", "too close")):
            with self.subTest(name=name):
                response = self.client.post(
                    url, {"category-name": name, "category-color": "#2e8b57"}
                )
                self.assertContains(response, error)
                self.assertNotIn("HX-Trigger", response)
        response = self.client.post(url, {"category-name": "Rent", "category-color": "red"})
        self.assertContains(response, "Pick a colour.")
        # A name with no Latin letters gets a random slug.
        response = self.client.post(url, {"category-name": "کھانا", "category-color": "#2e8b57"})
        self.assertContains(response, "data-sheet-done")
        self.assertTrue(Category.objects.get(name="کھانا").slug.startswith("category-"))

    def test_delete_account_and_category(self) -> None:
        line = Expense.objects.create(
            budget=self.budget,
            name="Rent",
            amount=D("1"),
            tag_foreign_key=self.bank,
            category=self.food,
        )
        sheet = self.client.get(
            reverse("app:manage_item", kwargs={"kind": "account", "pk": self.bank.pk})
        )
        self.assertContains(sheet, "Tap again: 1 line lose this account")
        self.client.post(
            reverse("app:manage_delete", kwargs={"kind": "account", "pk": self.bank.pk})
        )
        self.client.post(
            reverse("app:manage_delete", kwargs={"kind": "category", "pk": self.food.pk})
        )
        line.refresh_from_db()
        self.assertIsNone(line.tag_foreign_key)
        self.assertIsNone(line.category)
        self.assertFalse(Tag.objects.filter(pk=self.bank.pk).exists())

    def test_debt_account_cannot_be_deleted(self) -> None:
        debt = Debt.objects.create(user=self.user, name="Laptop", total_amount=D("100"))
        url = reverse("app:manage_delete", kwargs={"kind": "account", "pk": debt.debt_tag.pk})
        response = self.client.post(url)
        self.assertContains(response, "belongs to a debt")
        self.assertTrue(Debt.objects.filter(pk=debt.pk).exists())

    def test_bill_form(self) -> None:
        url = reverse("app:manage_new", kwargs={"kind": "bill"})
        response = self.client.post(
            url,
            {
                "bill-name": "Car tax",
                "bill-amount": "4000",
                "bill-next_bill_date": "2027-03-01",
                "bill-recurrence_months": "0",
                "bill-remind_days_before": "30",
            },
        )
        self.assertContains(response, "form-error")
        response = self.client.post(
            url,
            {
                "bill-name": "Car tax",
                "bill-amount": "4000",
                "bill-next_bill_date": "2027-03-01",
                "bill-recurrence_months": "12",
                "bill-remind_days_before": "30",
                "bill-tag": self.cash.pk,
                "bill-is_active": "on",
            },
        )
        self.assertContains(response, "Saved the bill &quot;Car tax&quot;.")
        bill = BillReminder.objects.get()
        self.assertEqual((bill.user, bill.tag, bill.is_active), (self.user, self.cash, True))

    def test_other_users_items_and_bad_kind(self) -> None:
        other = self.other_user()
        tag = Tag.objects.create(user=other, name="Theirs", slug="theirs")
        for name in ("app:manage_item", "app:manage_delete"):
            url = reverse(name, kwargs={"kind": "account", "pk": tag.pk})
            self.assertEqual(self.client.post(url, {"account-name": "Mine"}).status_code, 404)
        self.assertEqual(
            self.client.get(reverse("app:manage_new", kwargs={"kind": "user"})).status_code, 404
        )
        response = self.client.post(
            reverse("app:manage_new", kwargs={"kind": "bill"}),
            {
                "bill-name": "X",
                "bill-amount": "1",
                "bill-next_bill_date": "2027-03-01",
                "bill-recurrence_months": "12",
                "bill-remind_days_before": "30",
                "bill-tag": tag.pk,
            },
        )
        self.assertContains(response, "form-error")
        tag.refresh_from_db()
        self.assertEqual(tag.name, "Theirs")


class MonthsPageTests(ManageBase):
    """The year overview."""

    def test_year_overview(self) -> None:
        Expense.objects.create(budget=self.budget, name="Rent", amount=D("60000"))
        cards = year_overview(self.user, self.today.year, self.today)
        self.assertEqual(len(cards), 12)
        card = cards[self.today.month - 1]
        self.assertTrue(card.exists and card.is_current)
        self.assertEqual(card.unallocated, D("-10000"))
        self.assertEqual(sum(c.exists for c in cards), 1)

    def test_page(self) -> None:
        Budget.objects.create(user=self.user, month=date(2020, 5, 1))
        page = self.client.get(reverse("app:months"))
        self.assertContains(page, "No budget yet")
        self.assertContains(page, "?year=2020")
        self.assertContains(self.client.get(reverse("app:months"), {"year": "2020"}), "May")
        self.assertEqual(self.client.get(reverse("app:months"), {"year": "1"}).status_code, 404)


class MonthSettingsTests(ManageBase):
    """Income, transfers, the PDF email and delete."""

    def test_income_update_keeps_history(self) -> None:
        url = reverse("app:income_update", kwargs=self.kw)
        response = self.client.post(url, {"income-income": "60000", "income-currency": "USD"})
        self.assertContains(response, "Income saved: USD 60,000.")
        self.assertEqual(response["HX-Trigger"], "monthChanged")
        history = IncomeHistory.objects.get()
        self.assertEqual((history.old_amount, history.new_amount), (D("50000"), D("60000")))
        response = self.client.post(url, {"income-income": "-1", "income-currency": "XXX"})
        self.assertContains(response, "cannot be negative")
        self.assertContains(response, "Pick a currency")

    def test_transfer(self) -> None:
        url = reverse("app:transfer_create", kwargs=self.kw)
        data = {"transfer-from_tag": self.cash.pk, "transfer-to_tag": self.cash.pk}
        response = self.client.post(url, {**data, "transfer-amount": "100"})
        self.assertContains(response, "same account")
        data["transfer-to_tag"] = self.bank.pk
        response = self.client.post(url, {**data, "transfer-amount": "100"})
        self.assertContains(response, "Moved 100 from Cash to Bank.")
        transfer = TagTransfer.objects.get()
        response = self.client.post(reverse("app:transfer_delete", kwargs={"pk": transfer.pk}))
        self.assertContains(response, "Deleted the transfer.")
        self.assertFalse(TagTransfer.objects.exists())

    def test_email_without_resend_explains(self) -> None:
        response = self.client.post(reverse("app:month_email", kwargs=self.kw))
        self.assertContains(response, "toast--error")

    def test_delete_month(self) -> None:
        response = self.client.post(reverse("app:month_delete", kwargs=self.kw))
        self.assertEqual(response.status_code, 204)
        self.assertIn(reverse("app:months"), response["HX-Redirect"])
        self.assertFalse(Budget.objects.filter(pk=self.budget.pk).exists())

    def test_other_user_cannot_change_the_month(self) -> None:
        other = self.other_user()
        budget = Budget.objects.create(user=other, month=date(2020, 1, 1))
        kw = {"year": 2020, "month": 1}
        for name in ("app:income_update", "app:transfer_create", "app:month_delete"):
            with self.subTest(name=name):
                self.assertEqual(self.client.post(reverse(name, kwargs=kw)).status_code, 404)
        self.assertTrue(Budget.objects.filter(pk=budget.pk).exists())


class RootRedirectTests(ManageBase):
    """The root URL opens the new UI."""

    def test_root_opens_the_new_ui(self) -> None:
        self.assertRedirects(self.client.get("/"), reverse("app:home"))
