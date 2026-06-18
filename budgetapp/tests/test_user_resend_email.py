"""Tests for per-user Resend configuration on budget PDF email."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from budgetapp.models import Budget

User = get_user_model()


class UserResendEmailPdfTests(TestCase):
    """Budget PDF email requires Resend credentials on the user profile."""

    def setUp(self) -> None:
        self.client = Client()
        self.user = User.objects.create_user(
            username="resenduser",
            email="resenduser@example.com",
            password="testpassword",
        )
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2024, 8, 1),
            income=Decimal("1000.00"),
        )
        self.url = (
            f"/minimal/budget/{self.budget.month.year}/{self.budget.month.month}/email-pdf/"
        )

    def test_email_pdf_without_resend_returns_400(self) -> None:
        """POST without profile Resend config returns a clear error."""
        self.client.force_login(self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["status"], "error")
        self.assertIn("Resend is not configured", payload["message"])

    def test_user_has_resend_helper(self) -> None:
        """Model helper reflects stored credentials."""
        self.assertFalse(self.user.has_resend_email_config())
        self.user.resend_api_key = "re_test_key"
        self.user.resend_from_email = "sender@example.com"
        self.user.save()
        self.assertTrue(self.user.has_resend_email_config())
