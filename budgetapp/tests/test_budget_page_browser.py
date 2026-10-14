"""Browser smoke tests for the budget page (Playwright + headless Chromium).

The page loads jQuery, anime.js and Bootstrap from CDNs, so these tests need network access.
They are skipped when Playwright or its Chromium build is not installed:
``uv sync --extra dev`` then ``python -m playwright install chromium``.
"""

from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from typing import Any
from unittest import SkipTest

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import Client
from django.urls import reverse

from budgetapp.models import Budget, Expense

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import Page, sync_playwright
except ImportError:  # pragma: no cover - only when the dev extra is missing
    sync_playwright = None

User = get_user_model()


class BudgetPageBrowserTests(StaticLiveServerTestCase):
    """Regression tests for the budget page glitches fixed in Phase 0."""

    playwright: Any
    browser: Any

    @classmethod
    def setUpClass(cls) -> None:
        if sync_playwright is None:
            raise SkipTest("Playwright is not installed.")
        # Playwright's sync API runs an event loop; the ORM is still used synchronously.
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
            username="browser", email="browser@example.com", password="testpassword"
        )
        self.budget = Budget.objects.create(
            user=self.user, month=date(2024, 9, 1), income=Decimal("1000.00")
        )
        Expense.objects.create(budget=self.budget, name="Rent", amount=Decimal("400.00"))
        self.page = self._logged_in_page()
        self.page.goto(
            self.live_server_url
            + reverse("minimal:budget_detail", kwargs={"year": 2024, "month": 9})
        )
        self.page.wait_for_load_state("load")
        self.page.wait_for_function("!!(window.jQuery && window.anime)")

    def tearDown(self) -> None:
        self.page.context.close()

    def _logged_in_page(self) -> Page:
        client = Client()
        client.force_login(self.user)
        context = self.browser.new_context(service_workers="block")
        context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                    "url": self.live_server_url,
                }
            ]
        )
        return context.new_page()

    def test_add_expense_modal_opens_once(self) -> None:
        self.page.evaluate(
            "window.openCount = 0;"
            "$('#expenseModal').on('modal:opened', () => window.openCount++);"
        )
        self.page.click('button[data-modal-target="#expenseModal"]')
        self.page.wait_for_selector("#expenseModal.show")
        self.assertEqual(self.page.evaluate("window.openCount"), 1)

    def test_saving_expense_keeps_one_summary_section(self) -> None:
        self.page.set_viewport_size({"width": 1280, "height": 1600})
        self.page.click('button[data-modal-target="#expenseModal"]')
        self.page.wait_for_selector("#expenseModal.show")
        self.page.fill("#expense_name", "Groceries")
        self.page.fill("#expense_amount", "150")
        with self.page.expect_response(lambda r: "/summary-cards/" in r.url):
            self.page.click("#expense-submit-btn")
        self.page.wait_for_timeout(300)

        self.assertEqual(self.page.locator(".summary-toggle-btn").count(), 1)
        self.assertEqual(self.page.locator(".summary-cards").count(), 1)
        self.assertIn("550.00", self.page.inner_text(".gross-expenses-value"))

    def test_fast_double_click_keeps_toggle_label_in_sync(self) -> None:
        button = self.page.locator(".summary-toggle-btn")
        button.click()  # Hide.
        self.page.wait_for_selector(".summary-toggle-content", state="hidden")
        button.click()  # Show; the next click lands while this animation runs.
        button.click()
        self.page.wait_for_timeout(1000)

        hidden = not self.page.is_visible(".summary-toggle-content")
        label = self.page.inner_text(".summary-toggle-text")
        self.assertEqual(label, "Show Summary" if hidden else "Hide Summary")

    def test_modal_buttons_reachable_on_short_phone_screen(self) -> None:
        self.page.set_viewport_size({"width": 390, "height": 640})
        self.page.click('button[data-modal-target="#expenseModal"]')
        self.page.wait_for_selector("#expenseModal.show")
        # Clicking needs the button inside the viewport, so the modal must scroll.
        self.page.click("#expenseModal .expense-cancel-btn", timeout=5000)
        self.page.wait_for_selector("#expenseModal", state="hidden")

    def test_modal_can_reopen_while_closing(self) -> None:
        self.page.click('button[data-modal-target="#expenseModal"]')
        self.page.wait_for_selector("#expenseModal.show")
        self.page.click("#expenseModal .expense-cancel-btn")
        self.page.click('button[data-modal-target="#expenseModal"]')
        self.page.wait_for_timeout(600)
        self.assertTrue(self.page.is_visible("#expenseModal"))
