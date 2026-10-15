"""Tests for the sign-up switch (ACCOUNT_ALLOW_SIGNUP)."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()

SIGNUP_DATA = {
    "email": "new@example.com",
    "username": "newuser",
    "password1": "a-long-test-password-12",
    "password2": "a-long-test-password-12",
}


class SignupSwitchTests(TestCase):
    """Sign-up is open by default; ACCOUNT_ALLOW_SIGNUP=False closes it."""

    @override_settings(ACCOUNT_ALLOW_SIGNUP=True)
    def test_open_signup_shows_the_link_and_makes_an_account(self) -> None:
        self.assertContains(self.client.get(reverse("account_login")), "Sign up")
        self.client.post(reverse("account_signup"), SIGNUP_DATA)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

    @override_settings(ACCOUNT_ALLOW_SIGNUP=False)
    def test_closed_signup_hides_the_link_and_makes_no_account(self) -> None:
        self.assertNotContains(self.client.get(reverse("account_login")), "Sign up")
        response = self.client.get(reverse("account_signup"))
        self.assertContains(response, "Sign-up is closed")
        self.client.post(reverse("account_signup"), SIGNUP_DATA)
        self.assertFalse(User.objects.filter(email="new@example.com").exists())
