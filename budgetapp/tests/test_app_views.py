"""Tests for the new UI views (/app/)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import BillReminder, Budget, Category, Expense, SubExpense, Tag

User = get_user_model()
D = Decimal


class AppViewTestBase(TestCase):
    """A user with the current month: Groceries (day-to-day, Cash) and Rent (Bank)."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="app", email="app@example.com", password="testpassword"
        )
        self.client = Client()
        self.client.force_login(self.user)
        self.today = timezone.localdate()
        self.cash = Tag.objects.create(user=self.user, name="Cash", slug="cash")
        self.bank = Tag.objects.create(user=self.user, name="Bank", slug="bank")
        self.budget = Budget.objects.create(
            user=self.user, month=self.today.replace(day=1), income=D("50000")
        )
        self.groceries = Expense.objects.create(
            budget=self.budget,
            name="Groceries",
            amount=D("12000"),
            is_daily=True,
            tag_foreign_key=self.cash,
        )
        self.rent = Expense.objects.create(
            budget=self.budget, name="Rent", amount=D("20000"), tag_foreign_key=self.bank
        )
        self.month_kwargs = {"year": self.today.year, "month": self.today.month}

    def spend(self, **data: str) -> Any:
        """POST to the quick-add endpoint for this user's budget."""
        return self.client.post(reverse("app:spend_create"), {"budget": self.budget.pk, **data})


class PageTests(AppViewTestBase):
    """Full pages render and need a login."""

    def test_pages_need_login(self) -> None:
        anon = Client()
        for url in (reverse("app:home"), reverse("app:month", kwargs=self.month_kwargs)):
            with self.subTest(url=url):
                response = anon.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])

    def test_home_shows_safe_to_spend_and_bills(self) -> None:
        BillReminder.objects.create(
            user=self.user, name="Car token tax", amount=D("4500"), next_bill_date=self.today
        )
        response = self.client.get(reverse("app:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Safe to spend today")
        self.assertContains(response, 'data-testid="safe-today"')
        self.assertContains(response, "Car token tax")
        self.assertContains(response, 'id="quick-add"')

    def test_home_without_daily_lines_asks_to_choose_them(self) -> None:
        Expense.objects.filter(pk=self.groceries.pk).update(is_daily=False)
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, "Choose day-to-day lines")

    def test_home_without_budget_offers_to_create_it(self) -> None:
        self.budget.delete()
        response = self.client.get(reverse("app:home"))
        self.assertContains(response, "has no budget yet")
        self.assertNotContains(response, 'id="quick-add"')

    def test_month_page_lists_lines_by_category(self) -> None:
        food = Category.objects.create(user=self.user, name="Food", slug="food")
        Expense.objects.filter(pk=self.groceries.pk).update(category=food)
        response = self.client.get(reverse("app:month", kwargs=self.month_kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Food")
        self.assertContains(response, "Day-to-day spend by day")
        self.assertContains(response, 'id="line-form"')

    def test_month_without_budget_and_bad_month(self) -> None:
        response = self.client.get(reverse("app:month", kwargs={"year": 2001, "month": 1}))
        self.assertContains(response, "has no budget yet")
        response = self.client.get(reverse("app:month", kwargs={"year": 2026, "month": 13}))
        self.assertEqual(response.status_code, 404)

    def test_panels_render(self) -> None:
        url = reverse("app:month_panel", kwargs=self.month_kwargs)
        for view, marker in (("home", "home-panel"), ("month", "month-panel"), ("sheet", "chips")):
            with self.subTest(view=view):
                response = self.client.get(url, {"view": view})
                self.assertContains(response, marker)

    def test_other_users_month_panel_is_404(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        self.client.force_login(other)
        response = self.client.get(reverse("app:month_panel", kwargs=self.month_kwargs))
        self.assertEqual(response.status_code, 404)


class SpendTests(AppViewTestBase):
    """Quick add and undo."""

    def test_spend_with_amount_and_line(self) -> None:
        response = self.spend(amount="2,500", line=str(self.groceries.pk), note="Weekly shop")
        self.assertEqual(response.status_code, 200)
        spend = SubExpense.objects.get()
        self.assertEqual(
            (spend.expense, spend.amount, spend.name), (self.groceries, D("2500"), "Weekly shop")
        )
        trigger = json.loads(response["HX-Trigger"])
        self.assertEqual(trigger, {"monthChanged": True, "spendAdded": True})
        self.assertContains(response, "Added!")
        self.assertContains(response, "9,500 left")

    def test_spend_from_text(self) -> None:
        response = self.spend(text="groc 1.5k #cash")
        self.assertContains(response, "Added!")
        self.assertEqual(SubExpense.objects.get().amount, D("1500"))

    def test_text_with_two_matches_asks_which_line(self) -> None:
        Expense.objects.create(budget=self.budget, name="Gifts", amount=D("100"))
        response = self.spend(text="g 300")
        self.assertContains(response, "Which line?")
        self.assertContains(response, "Groceries")
        self.assertContains(response, "Gifts")
        self.assertFalse(SubExpense.objects.exists())
        self.assertNotIn("HX-Trigger", response)

    def test_errors_are_explained(self) -> None:
        cases = {
            "no match": ({"text": "fuel 300"}, "No line matches &quot;fuel&quot;"),
            "no amount": ({"text": "groceries"}, "Add an amount"),
            "bad amount": ({"amount": "abc", "line": "1"}, "Enter an amount"),
            "no line": ({"amount": "300"}, "Pick a line"),
        }
        for name, (data, message) in cases.items():
            with self.subTest(name):
                response = self.spend(**data)
                self.assertContains(response, message)
        self.assertFalse(SubExpense.objects.exists())

    def test_cannot_spend_on_other_users_budget_or_line(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        other_budget = Budget.objects.create(user=other, month=date(2026, 1, 1))
        other_line = Expense.objects.create(budget=other_budget, name="X", amount=D("10"))
        response = self.client.post(
            reverse("app:spend_create"),
            {"budget": other_budget.pk, "amount": "5", "line": other_line.pk},
        )
        self.assertEqual(response.status_code, 404)
        response = self.spend(amount="5", line=str(other_line.pk))
        self.assertEqual(response.status_code, 404)
        self.assertFalse(SubExpense.objects.exists())

    def test_undo_removes_the_spend(self) -> None:
        self.spend(amount="100", line=str(self.groceries.pk))
        spend = SubExpense.objects.get()
        response = self.client.post(reverse("app:spend_undo", kwargs={"pk": spend.pk}))
        self.assertContains(response, "Removed the spend from Groceries")
        self.assertEqual(response["HX-Trigger"], "monthChanged")
        self.assertFalse(SubExpense.objects.exists())

    def test_undo_of_other_users_spend_is_404(self) -> None:
        spend = SubExpense.objects.create(expense=self.groceries, name="x", amount=D("1"))
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        self.client.force_login(other)
        response = self.client.post(reverse("app:spend_undo", kwargs={"pk": spend.pk}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(SubExpense.objects.filter(pk=spend.pk).exists())


class LineAndMonthTests(AppViewTestBase):
    """Line toggle, line form and month creation."""

    def test_daily_toggle(self) -> None:
        url = reverse("app:line_daily", kwargs={"pk": self.rent.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response["HX-Trigger"], "monthChanged")
        self.rent.refresh_from_db()
        self.assertTrue(self.rent.is_daily)
        self.client.post(url)
        self.rent.refresh_from_db()
        self.assertFalse(self.rent.is_daily)

    def test_add_line(self) -> None:
        url = reverse("app:line_create", kwargs=self.month_kwargs)
        response = self.client.post(
            url,
            {
                "line-name": "Transport",
                "line-amount": "6000",
                "line-tag_foreign_key": self.cash.pk,
                "line-is_daily": "on",
            },
        )
        self.assertContains(response, 'Added the line "Transport"')
        self.assertEqual(response["HX-Trigger"], "monthChanged")
        line = Expense.objects.get(name="Transport")
        self.assertEqual((line.budget, line.amount, line.is_daily), (self.budget, D("6000"), True))

    def test_add_line_errors_and_foreign_tag(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        foreign_tag = Tag.objects.create(user=other, name="Theirs", slug="theirs")
        url = reverse("app:line_create", kwargs=self.month_kwargs)
        response = self.client.post(
            url, {"line-name": "", "line-amount": "-5", "line-tag_foreign_key": foreign_tag.pk}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form-error")
        self.assertNotIn("HX-Trigger", response)
        self.assertEqual(self.budget.expenses.count(), 2)

    def test_create_month_copies_last_month(self) -> None:
        Expense.objects.filter(pk=self.rent.pk).update(is_recurring=True)
        nxt = date(self.today.year + (self.today.month == 12), self.today.month % 12 + 1, 1)
        url = reverse("app:month_create", kwargs={"year": nxt.year, "month": nxt.month})
        response = self.client.post(url, {"copy": "1"})
        self.assertRedirects(
            response, reverse("app:month", kwargs={"year": nxt.year, "month": nxt.month})
        )
        budget = Budget.objects.get(user=self.user, month=nxt)
        self.assertEqual(budget.income, D("50000"))
        self.assertEqual(list(budget.expenses.values_list("name", flat=True)), ["Rent"])
        # A second POST does not create a duplicate.
        self.client.post(url, {"copy": "1"})
        self.assertEqual(Budget.objects.filter(user=self.user, month=nxt).count(), 1)
