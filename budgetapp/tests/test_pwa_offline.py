"""Browser tests for the PWA offline behaviour (Playwright + headless Chromium).

The live server runs on http://localhost, which browsers treat as a secure context,
so the service worker registers as it does over HTTPS.
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
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover - only when the dev extra is missing
    sync_playwright = None

User = get_user_model()


class PwaOfflineTests(StaticLiveServerTestCase):
    """After 1 online visit, the app must open and show budgets without a network."""

    host = "localhost"
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
            username="offline", email="offline@example.com", password="testpassword"
        )
        for month in (8, 9):
            budget = Budget.objects.create(
                user=self.user, month=date(2024, month, 1), income=Decimal("1000.00")
            )
            Expense.objects.create(budget=budget, name=f"Rent {month}", amount=Decimal("400"))

        client = Client()
        client.force_login(self.user)
        self.context = self.browser.new_context()
        self.context.add_cookies(
            [
                {
                    "name": settings.SESSION_COOKIE_NAME,
                    "value": client.cookies[settings.SESSION_COOKIE_NAME].value,
                    "url": self.live_server_url,
                }
            ]
        )
        self.page = self.context.new_page()

    def tearDown(self) -> None:
        self.context.close()

    def _visit_home_online(self) -> None:
        """Open the home page online and wait until the recent months are cached."""
        self.page.goto(self.live_server_url + reverse("app:home"), wait_until="load")
        # pwa-register.js reloads the page when the new worker takes control.
        self.page.wait_for_function("navigator.serviceWorker.controller !== null", timeout=15000)
        self.page.wait_for_load_state("load")
        month_url = reverse("app:month", kwargs={"year": 2024, "month": 8})
        # wait_for_function does not await a Promise, so poll the cache here.
        for _ in range(30):
            try:
                cached = self.page.evaluate(
                    "url => caches.match(url, {ignoreVary: true}).then(r => !!r)", month_url
                )
            except PlaywrightError:
                # The one-time controllerchange reload replaced the page; try again.
                cached = False
            if cached:
                self.page.wait_for_load_state("load")
                return
            self.page.wait_for_timeout(500)
        self.fail("The service worker did not cache the month page.")

    def test_home_opens_offline_with_styles_and_scripts(self) -> None:
        self._visit_home_online()
        self.context.set_offline(True)
        self.page.goto(self.live_server_url + reverse("app:home"), wait_until="load")

        self.assertNotIn("You are offline", self.page.content())
        self.assertTrue(self.page.evaluate("!!window.htmx"), "HTMX did not load offline")
        self.assertTrue(self.page.evaluate("!!window.anime"), "anime.js did not load offline")
        tokens_css = self.page.evaluate(
            "[...document.styleSheets].some(s => (s.href || '').includes('tokens.css'))"
        )
        self.assertTrue(tokens_css, "The app CSS did not load offline")

    def test_month_never_opened_still_opens_offline(self) -> None:
        self._visit_home_online()
        self.context.set_offline(True)
        url = self.live_server_url + reverse("app:month", kwargs={"year": 2024, "month": 8})
        self.page.goto(url, wait_until="load")
        self.assertIn("Rent 8", self.page.content())
        self.assertNotIn("You are offline", self.page.content())

    def test_page_not_cached_shows_the_offline_page(self) -> None:
        self._visit_home_online()
        self.context.set_offline(True)
        url = self.live_server_url + reverse("app:recap", kwargs={"year": 2024, "month": 8})
        self.page.goto(url, wait_until="load")
        self.assertIn("You are offline", self.page.content())

    def test_offline_urls_list_only_own_budgets(self) -> None:
        other = User.objects.create_user(
            username="someone", email="someone@example.com", password="testpassword"
        )
        Budget.objects.create(user=other, month=date(2024, 1, 1))
        client = Client()
        client.force_login(self.user)
        urls = client.get(reverse("app:offline_urls")).json()["urls"]
        self.assertIn(reverse("app:month", kwargs={"year": 2024, "month": 9}), urls)
        self.assertIn(reverse("app:offline"), urls)
        self.assertNotIn(reverse("app:month", kwargs={"year": 2024, "month": 1}), urls)
