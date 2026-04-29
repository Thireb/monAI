from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from budgetapp.models import Budget

User = get_user_model()


class MobileBudgetSyncApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="syncuser",
            email="sync@example.com",
            password="sync-pass-secure",
        )
        self.other = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="other-pass-secure",
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_mobile_token_returns_token(self):
        anon = APIClient()
        url = reverse("api-mobile-token")
        response = anon.post(
            url,
            {"email": "sync@example.com", "password": "sync-pass-secure"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["token"], self.token.key)

    def test_pull_returns_only_own_budgets(self):
        b1 = Budget.objects.create(
            user=self.user,
            month=date(2025, 3, 1),
            income=Decimal("1000.00"),
            currency="PKR",
        )
        Budget.objects.create(
            user=self.other,
            month=date(2025, 4, 1),
            income=Decimal("500.00"),
            currency="PKR",
        )
        url = reverse("api-mobile-budget-pull")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["budgets"]), 1)
        self.assertEqual(response.data["budgets"][0]["id"], b1.id)

    def test_pull_filtered_by_updated_after(self):
        b_old = Budget.objects.create(
            user=self.user,
            month=date(2025, 1, 1),
            income=Decimal("100.00"),
            currency="PKR",
        )
        ts = timezone.now()
        b_new = Budget.objects.create(
            user=self.user,
            month=date(2025, 2, 1),
            income=Decimal("200.00"),
            currency="PKR",
        )
        url = reverse("api-mobile-budget-pull")
        response = self.client.get(url, {"updated_after": ts.isoformat()})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row["id"] for row in response.data["budgets"]]
        self.assertIn(b_new.id, ids)
        self.assertNotIn(b_old.id, ids)

    def test_push_creates_and_updates(self):
        existing = Budget.objects.create(
            user=self.user,
            month=date(2025, 5, 1),
            income=Decimal("50.00"),
            currency="PKR",
        )
        url = reverse("api-mobile-budget-push")
        payload = {
            "budgets": [
                {
                    "month": "2025-06-01",
                    "income": "300.00",
                    "currency": "USD",
                    "is_archived": False,
                },
                {
                    "id": existing.id,
                    "month": "2025-05-01",
                    "income": "99.50",
                    "currency": "PKR",
                    "is_archived": True,
                },
            ],
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["created_ids"]), 1)
        self.assertEqual(response.data["server_ids"], response.data["created_ids"] + [existing.id])
        existing.refresh_from_db()
        self.assertEqual(existing.income, Decimal("99.50"))
        self.assertTrue(existing.is_archived)
        new_id = response.data["created_ids"][0]
        created = Budget.objects.get(pk=new_id)
        self.assertEqual(created.income, Decimal("300.00"))

    def test_push_rejects_unknown_id(self):
        url = reverse("api-mobile-budget-push")
        payload = {
            "budgets": [
                {
                    "id": 999999,
                    "month": "2025-07-01",
                    "income": "1.00",
                    "currency": "PKR",
                }
            ],
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
