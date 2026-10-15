"""Tests for per-user Resend configuration on budget PDF email."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

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
        self.url = reverse("app:month_email", kwargs={"year": 2024, "month": 8})

    def test_email_pdf_without_resend_explains(self) -> None:
        """POST without profile Resend config shows a clear error and makes no PDF."""
        self.client.force_login(self.user)
        with patch("budgetapp.services.report.render_pdf") as render_pdf:
            response = self.client.post(self.url)
        self.assertContains(response, "toast--error")
        self.assertContains(response, "Resend is not configured")
        render_pdf.assert_not_called()

    def test_email_pdf_sends_with_the_users_key(self) -> None:
        """With a Resend key, the report goes to the user's own address."""
        self.user.resend_api_key = "re_test_key"
        self.user.resend_from_email = "sender@example.com"
        self.user.save()
        self.client.force_login(self.user)
        with (
            patch("budgetapp.services.report.render_pdf", return_value=b"%PDF") as render_pdf,
            patch("budgetapp.services.report._send_with_resend") as send,
        ):
            response = self.client.post(self.url)
        self.assertContains(response, "Budget report has been sent to resenduser@example.com")
        render_pdf.assert_called_once()
        self.assertEqual(send.call_args.args[0], "resenduser@example.com")
        self.assertEqual(send.call_args.args[3:], ("re_test_key", "sender@example.com"))

    def test_user_has_resend_helper(self) -> None:
        """Model helper reflects stored credentials."""
        self.assertFalse(self.user.has_resend_email_config())
        self.user.resend_api_key = "re_test_key"
        self.user.resend_from_email = "sender@example.com"
        self.user.save()
        self.assertTrue(self.user.has_resend_email_config())
