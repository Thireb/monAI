"""Browser tests for the new UI (/app/) with Playwright and headless Chromium.

HTMX and anime.js come from ``static/app/vendor/``, so only the web fonts need the network.
The tests are skipped when Playwright or its Chromium build is missing.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any
from unittest import SkipTest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from budgetapp.models import Budget, Debt, DebtTransaction, Expense, Goal, SubExpense, Tag

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page, sync_playwright
except ImportError:  # pragma: no cover - only when the dev extra is missing
    sync_playwright = None

User = get_user_model()
D = Decimal


class AppBrowserTests(StaticLiveServerTestCase):
    """Quick add, undo, the day-to-day toggle, theme and the phone layout."""

    playwright: Any
    browser: Any

    @classmethod
    def setUpClass(cls) -> None:
        if sync_playwright is None:
            raise SkipTest("Playwright is not installed.")
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        try:
            cls.browser = cls.playwright.chromium.launch()
        except PlaywrightError as exc:
            cls.playwright.stop()
            super().tearDownClass()
            raise SkipTest(f"Chromium for Playwright is not installed: {exc}")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="ui", email="ui@example.com", password="testpassword"
        )
        today = timezone.localdate()
        cash = Tag.objects.create(user=self.user, name="Cash", slug="cash")
        self.budget = Budget.objects.create(
            user=self.user, month=today.replace(day=1), income=D("50000")
        )
        self.groceries = Expense.objects.create(
            budget=self.budget,
            name="Groceries",
            amount=D("31000"),
            is_daily=True,
            tag_foreign_key=cash,
        )
        self.gifts = Expense.objects.create(budget=self.budget, name="Gifts", amount=D("3000"))
        self.month_url = reverse("app:month", kwargs={"year": today.year, "month": today.month})
        self.context = None

    def tearDown(self) -> None:
        if self.context is not None:
            self.context.close()

    def open(self, url: str, width: int = 1280, height: int = 900) -> Page:
        """Open ``url`` logged in, and wait for HTMX."""
        client = Client()
        client.force_login(self.user)
        self.context = self.browser.new_context(
            viewport={"width": width, "height": height}, service_workers="block"
        )
        self.context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                    "url": self.live_server_url,
                }
            ]
        )
        page = self.context.new_page()
        page.goto(self.live_server_url + url, wait_until="load")
        page.wait_for_function("!!window.htmx")
        return page

    def test_quick_add_with_keyboard_then_undo(self) -> None:
        page = self.open(reverse("app:home"))
        page.keyboard.press("/")
        page.wait_for_selector("#quick-add[open]")
        page.fill("#quick-add [name=amount]", "2500")
        page.click(f"label[for=qa-line-{self.groceries.pk}]")
        page.click("#quick-add button[type=submit]")

        page.wait_for_selector(".toast--added")
        self.assertIn("2,500 to Groceries", page.inner_text(".toast--added"))
        page.wait_for_selector("#quick-add:not([open])", state="attached")
        self.assertEqual(SubExpense.objects.get().amount, D("2500"))
        # The home panel refreshed: the line now shows what is left after the spend.
        page.wait_for_function(
            "document.querySelector('#home-panel').innerText.includes('28,500 left')"
        )

        page.click(".toast--added >> text=Undo")
        page.wait_for_selector("text=Removed the spend from Groceries")
        self.assertFalse(SubExpense.objects.exists())

    def test_typed_text_with_two_matches_asks_which_line(self) -> None:
        page = self.open(reverse("app:home"))
        page.click("[data-open-quick-add] >> visible=true")
        page.fill("#quick-add [name=text]", "g 300")
        page.click("#quick-add button[type=submit]")
        page.wait_for_selector("text=Which line?")
        page.click("#quick-add-result >> text=Gifts")
        page.wait_for_selector(".toast--added")
        self.assertEqual(SubExpense.objects.get().expense, self.gifts)

    def test_day_to_day_toggle_updates_the_page(self) -> None:
        page = self.open(self.month_url)
        toggle = f"[data-line-id='{self.gifts.pk}'] button[aria-pressed]"
        self.assertEqual(page.get_attribute(toggle, "aria-pressed"), "false")
        page.click(toggle)
        page.wait_for_selector(f"[data-line-id='{self.gifts.pk}'] button[aria-pressed='true']")
        self.gifts.refresh_from_db()
        self.assertTrue(self.gifts.is_daily)

    def test_add_line_form(self) -> None:
        page = self.open(self.month_url)
        page.fill("#id_line-name", "Transport")
        page.fill("#id_line-amount", "6000")
        page.click("#line-form button[type=submit]")
        page.wait_for_selector('text=Added the line "Transport"')
        page.wait_for_selector("#month-panel >> text=Transport")
        self.assertTrue(Expense.objects.filter(name="Transport", budget=self.budget).exists())

    def test_theme_toggle(self) -> None:
        page = self.open(reverse("app:home"))
        before = page.evaluate(
            "matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'"
        )
        page.click("[data-theme-toggle]")
        after = page.get_attribute("html", "data-theme")
        self.assertNotEqual(after, before)
        # theme-init.js runs in <head>, so the HTML alone is enough; no need to wait for fonts.
        page.reload(wait_until="domcontentloaded")
        self.assertEqual(page.get_attribute("html", "data-theme"), after)

    def test_phone_layout(self) -> None:
        page = self.open(self.month_url, width=360, height=740)
        self.assertTrue(page.is_visible(".bottom-nav"))
        overflow = page.evaluate(
            "document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )
        self.assertLessEqual(overflow, 0, "The page scrolls sideways on a phone")
        page.click(".bottom-nav__add")
        page.wait_for_selector("#quick-add[open]")
        page.fill("#quick-add [name=amount]", "100")
        page.click(f"label[for=qa-line-{self.groceries.pk}]")
        # The submit button must be reachable on a short screen.
        page.click("#quick-add button[type=submit]", timeout=5000)
        page.wait_for_selector(".toast--added")

    def test_line_sheet_edit_spend_and_delete(self) -> None:
        page = self.open(self.month_url)
        page.click(f"[data-line-id='{self.gifts.pk}'] .line-row__open")
        page.wait_for_selector("#edit-sheet[open] >> text=Spends and returns")

        page.fill("#edit-sheet [name=amount]", "400")
        page.fill("#edit-sheet [name=note]", "Card")
        page.click("#edit-sheet .line-sheet__spend button[type=submit]")
        page.wait_for_selector("#edit-sheet >> text=Spend saved.")
        page.wait_for_selector("#month-panel >> text=2,600 left")

        # Delete needs 2 taps: the first one only changes the label.
        delete = "#edit-sheet .spend-row button"
        page.click(delete)
        self.assertEqual(page.inner_text(delete), "Tap again")
        self.assertTrue(SubExpense.objects.exists())
        page.click(delete)
        page.wait_for_selector("#edit-sheet >> text=Deleted the spend.")
        self.assertFalse(SubExpense.objects.exists())

        page.click("#edit-sheet summary")
        page.fill("#id_edit-name", "Presents")
        page.click("#edit-sheet >> text=Save changes")
        page.wait_for_selector("#month-panel >> text=Presents")

        page.click("#edit-sheet >> text=Delete line")
        page.click("#edit-sheet >> text=Tap again to delete")
        page.wait_for_selector('text=Deleted the line "Presents"')
        page.wait_for_selector("#edit-sheet:not([open])", state="attached")
        self.assertFalse(Expense.objects.filter(pk=self.gifts.pk).exists())

    def test_goals_page_contribute_and_repay(self) -> None:
        goal = Goal.objects.create(user=self.user, name="Trip", target_amount=D("1000"))
        debt = Debt.objects.create(user=self.user, name="Laptop", total_amount=D("5000"))
        DebtTransaction.objects.create(debt=debt, amount=D("3000"))
        page = self.open(reverse("app:goals"))

        amount = f"#goal-{goal.pk} [name=amount]"
        page.fill(amount, "300")
        page.press(amount, "Enter")
        page.wait_for_selector("text=25%!")
        page.wait_for_selector(f"#goal-{goal.pk} >> text=300 of 1,000")
        self.assertEqual(page.input_value(amount), "")

        repay = f"#debt-{debt.pk} [name=amount]"
        page.fill(repay, "1000")
        page.click(f"#debt-{debt.pk} >> text=Repay this month")
        page.wait_for_selector(f"#debt-{debt.pk} >> text=Repaid 1,000 of 3,000 borrowed")
        line = Expense.objects.get(tag_foreign_key=debt.debt_tag)
        self.assertEqual((line.budget, line.amount), (self.budget, D("1000")))

    def test_offline_quick_add_is_sent_when_online(self) -> None:
        page = self.open(reverse("app:home"))
        self.context.set_offline(True)
        page.keyboard.press("/")
        page.fill("#quick-add [name=amount]", "700")
        page.click(f"label[for=qa-line-{self.groceries.pk}]")
        page.click("#quick-add button[type=submit]")
        page.wait_for_selector("text=Saved on this device")
        page.wait_for_selector("#outbox >> text=1 spend waits for the network")
        self.assertFalse(SubExpense.objects.exists())

        self.context.set_offline(False)
        page.wait_for_selector("text=Sent 1 spend saved offline.")
        page.wait_for_selector("#outbox", state="hidden")
        spend = SubExpense.objects.get()
        self.assertEqual((spend.expense, spend.amount), (self.groceries, D("700")))
        page.wait_for_function(
            "document.querySelector('#home-panel').innerText.includes('30,300 left')"
        )

    def test_more_page_add_and_delete_account(self) -> None:
        page = self.open(reverse("app:manage"))
        page.click("#accounts-title >> xpath=.. >> text=+ New")
        page.wait_for_selector("#edit-sheet[open] >> text=New account")
        page.fill("#id_account-name", "Wallet")
        page.click("#edit-sheet >> text=Save")
        page.wait_for_selector('text=Saved the account "Wallet".')
        page.wait_for_selector("#edit-sheet:not([open])", state="attached")
        page.wait_for_selector("#manage-panel >> text=Wallet")

        page.click("#manage-panel .item-row >> text=Wallet")
        page.wait_for_selector("#edit-sheet[open]")
        page.click("#edit-sheet >> text=Delete")
        page.click("#edit-sheet >> text=Tap again to delete")
        page.wait_for_selector('text=Deleted the account "Wallet".')
        self.assertFalse(Tag.objects.filter(name="Wallet").exists())

    def test_month_settings_income(self) -> None:
        page = self.open(self.month_url)
        page.fill("#id_income-income", "60000")
        page.click("#month-settings >> text=Save income")
        page.wait_for_selector("#month-settings >> text=Income saved")
        page.wait_for_selector("#month-panel >> text=60,000")
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.income, D("60000"))
