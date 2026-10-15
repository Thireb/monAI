"""Tests for Web Push bill alerts: endpoint checks, subscribe views, alert text and sending."""

from __future__ import annotations

import json
from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pywebpush import WebPushException

from budgetapp.bill_reminder_utils import apply_bill_reminders_to_budget
from budgetapp.models import BillReminder, Budget, PushSubscription, SubExpense, WebPushKey
from budgetapp.services.push import bill_alert, is_allowed_endpoint, send_bill_alerts, server_key

User = get_user_model()
D = Decimal
ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"


def subscription_json(endpoint: str = ENDPOINT) -> str:
    return json.dumps({"endpoint": endpoint, "keys": {"p256dh": "BPkey", "auth": "authkey"}})


class EndpointAndKeyTests(TestCase):
    """Only known push services; 1 server key."""

    def test_allowed_endpoints(self) -> None:
        for url in (
            ENDPOINT,
            "https://updates.push.services.mozilla.com/wpush/v2/x",
            "https://web.push.apple.com/abc",
            "https://wns2-par02p.notify.windows.com/w/?token=x",
        ):
            with self.subTest(url=url):
                self.assertTrue(is_allowed_endpoint(url))
        for url in (
            "http://fcm.googleapis.com/x",
            "https://127.0.0.1/x",
            "https://evilfcm.googleapis.com.example.com/x",
            "https://localhost:8000/admin/",
            "ftp://web.push.apple.com/x",
            "",
        ):
            with self.subTest(url=url):
                self.assertFalse(is_allowed_endpoint(url))

    def test_server_key_is_made_once(self) -> None:
        first = server_key()
        self.assertEqual(server_key().pk, first.pk)
        self.assertEqual(WebPushKey.objects.count(), 1)
        self.assertIn("BEGIN PRIVATE KEY", first.private_key)
        self.assertEqual(len(first.public_key), 87)  # 65 bytes, base64 without padding


class PushViewTests(TestCase):
    """Subscribe, unsubscribe and the test alert."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="push", email="push@example.com", password="testpassword"
        )
        self.client = Client()
        self.client.force_login(self.user)

    def post_json(self, name: str, body: str) -> Any:
        return self.client.post(reverse(name), body, content_type="application/json")

    def test_key_subscribe_and_unsubscribe(self) -> None:
        key = self.client.get(reverse("app:push_key")).json()["public_key"]
        self.assertEqual(key, server_key().public_key)
        self.assertEqual(self.post_json("app:push_subscribe", subscription_json()).status_code, 200)
        self.post_json("app:push_subscribe", subscription_json())  # Same browser again.
        subscription = PushSubscription.objects.get()
        self.assertEqual((subscription.user, subscription.auth), (self.user, "authkey"))
        self.post_json("app:push_unsubscribe", json.dumps({"endpoint": ENDPOINT}))
        self.assertFalse(PushSubscription.objects.exists())

    def test_bad_subscriptions(self) -> None:
        for body in ("not json", "{}", subscription_json("https://127.0.0.1:8000/admin/")):
            with self.subTest(body=body):
                self.assertEqual(self.post_json("app:push_subscribe", body).status_code, 400)
        self.assertFalse(PushSubscription.objects.exists())
        self.assertEqual(Client().get(reverse("app:push_key")).status_code, 302)

    def test_unsubscribe_only_removes_own(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        PushSubscription.objects.create(user=other, endpoint=ENDPOINT, p256dh="k", auth="a")
        self.post_json("app:push_unsubscribe", json.dumps({"endpoint": ENDPOINT}))
        self.assertTrue(PushSubscription.objects.exists())

    def test_test_alert(self) -> None:
        response = self.client.post(reverse("app:push_test"))
        self.assertContains(response, "Turn on bill alerts")
        PushSubscription.objects.create(user=self.user, endpoint=ENDPOINT, p256dh="k", auth="a")
        with mock.patch("budgetapp.services.push.webpush") as webpush:
            response = self.client.post(reverse("app:push_test"))
        self.assertContains(response, "Sent a test to 1 device.")
        claims = webpush.call_args.kwargs["vapid_claims"]
        self.assertEqual(claims, {"sub": "mailto:push@example.com"})


class BillAlertTests(TestCase):
    """The alert text and the daily send."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="alerts", email="alerts@example.com", password="testpassword"
        )
        self.today = date(2026, 10, 14)
        self.budget = Budget.objects.create(user=self.user, month=date(2026, 10, 1))

    def _bill(self, name: str, due: date, amount: str = "1000", days: int = 30) -> BillReminder:
        return BillReminder.objects.create(
            user=self.user,
            name=name,
            amount=D(amount),
            next_bill_date=due,
            remind_days_before=days,
        )

    def test_alert_lists_unpaid_bills_due_soon_and_new_reminders(self) -> None:
        self._bill("Internet", date(2026, 10, 16), "3200")
        self._bill("Paid", date(2026, 10, 15))
        self._bill("Later", date(2026, 10, 25))
        apply_bill_reminders_to_budget(self.budget)
        paid = self.budget.expenses.get(name="Paid")
        SubExpense.objects.create(expense=paid, name="x", amount=D("1000"))
        self._bill("Car tax", self.today + timedelta(days=30), "4500")  # Window starts today.
        alert = bill_alert(self.user, self.today)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.title, "2 bills coming up")
        self.assertEqual(alert.body, "Internet 3,200 in 2 days · Car tax 4,500 on 13 Nov 2026")

    def test_no_alert_without_bills(self) -> None:
        self.assertIsNone(bill_alert(self.user, self.today))

    def test_send_once_a_day_and_drop_gone_browsers(self) -> None:
        self._bill("Internet", date(2026, 10, 14))
        apply_bill_reminders_to_budget(self.budget)
        PushSubscription.objects.create(user=self.user, endpoint=ENDPOINT, p256dh="k", auth="a")
        gone = PushSubscription.objects.create(
            user=self.user, endpoint=ENDPOINT + "gone", p256dh="k", auth="a"
        )

        def fake_webpush(**kwargs: Any) -> None:
            if kwargs["subscription_info"]["endpoint"] == gone.endpoint:
                raise WebPushException("gone", response=mock.Mock(status_code=410))
            self.assertIn("Internet 1,000 today", kwargs["data"])

        with mock.patch("budgetapp.services.push.webpush", side_effect=fake_webpush):
            self.assertEqual(send_bill_alerts(self.today), 1)
            self.assertEqual(send_bill_alerts(self.today), 0)  # Already sent today.
        self.assertFalse(PushSubscription.objects.filter(pk=gone.pk).exists())
        self.assertEqual(PushSubscription.objects.get().last_alert_on, self.today)
