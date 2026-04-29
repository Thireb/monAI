from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from budgetapp.models import Budget, Category, Expense, Tag

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


class MobileCatalogSyncApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="catuser",
            email="cat@example.com",
            password="cat-pass-secure",
        )
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.budget = Budget.objects.create(
            user=self.user,
            month=date(2025, 8, 1),
            income=Decimal("1000.00"),
            currency="PKR",
        )

    def test_category_push_create_and_pull_cursor(self):
        url_push = reverse("api-mobile-category-push")
        resp = self.client.post(
            url_push,
            {
                "categories": [
                    {"name": "Food", "color": "#ff0000"},
                    {
                        "name": "Updated",
                        "description": "d",
                    },
                ]
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data["created_ids"]), 2)
        c1 = Category.objects.get(pk=resp.data["created_ids"][0])
        self.assertEqual(c1.name, "Food")
        cid = c1.id
        resp2 = self.client.post(
            url_push,
            {
                "categories": [
                    {"id": cid, "name": "Groceries", "description": "", "color": "#00ff00"}
                ]
            },
            format="json",
        )
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        c1.refresh_from_db()
        self.assertEqual(c1.name, "Groceries")
        ts = timezone.now()
        Category.objects.create(user=self.user, name="Later", slug="later")
        url_pull = reverse("api-mobile-category-pull")
        resp_pull = self.client.get(url_pull, {"updated_after": ts.isoformat()})
        self.assertEqual(resp_pull.status_code, status.HTTP_200_OK)
        names = [x["name"] for x in resp_pull.data["categories"]]
        self.assertIn("Later", names)
        self.assertNotIn("Groceries", names)

    def test_expense_push_requires_budget_and_foreign_keys(self):
        cat = Category.objects.create(user=self.user, name="C", slug="c")
        tag = Tag.objects.create(user=self.user, name="T", slug="t")
        url = reverse("api-mobile-expense-push")
        r = self.client.post(
            url,
            {
                "expenses": [
                    {
                        "budget_id": self.budget.id,
                        "name": "Rent",
                        "amount": "500.00",
                        "category_id": cat.id,
                        "tag_id": tag.id,
                    }
                ]
            },
            format="json",
        )
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        eid = r.data["created_ids"][0]
        e = Expense.objects.get(pk=eid)
        self.assertEqual(e.name, "Rent")
        self.assertEqual(e.category_id, cat.id)
        self.assertEqual(e.tag_foreign_key_id, tag.id)
        url_pull = reverse("api-mobile-expense-pull")
        r2 = self.client.get(url_pull)
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r2.data["expenses"]), 1)
