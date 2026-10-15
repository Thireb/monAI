"""Tests for the one-budget-per-user-per-month rule and its data migration."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from budgetapp.models import Budget, IncomeHistory

User = get_user_model()


class BudgetMonthUniqueTests(TestCase):
    """The database, the web view and the mobile push all keep one budget per month."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="monthly", email="monthly@example.com", password="testpassword"
        )
        self.month = date(2024, 5, 1)

    def test_database_rejects_second_budget_for_same_month(self) -> None:
        Budget.objects.create(user=self.user, month=self.month)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Budget.objects.create(user=self.user, month=self.month)

    def test_other_users_can_use_same_month(self) -> None:
        other = User.objects.create_user(
            username="other", email="other@example.com", password="testpassword"
        )
        Budget.objects.create(user=self.user, month=self.month)
        Budget.objects.create(user=other, month=self.month)
        self.assertEqual(Budget.objects.filter(month=self.month).count(), 2)

    def test_create_view_refuses_month_that_is_archived(self) -> None:
        Budget.objects.create(user=self.user, month=self.month, is_archived=True)
        client = Client()
        client.force_login(self.user)
        response = client.post(reverse("app:month_create", kwargs={"year": 2024, "month": 5}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Budget.objects.filter(user=self.user, month=self.month).count(), 1)

    def test_mobile_push_without_id_updates_existing_month(self) -> None:
        existing = Budget.objects.create(user=self.user, month=self.month, income=Decimal("10"))
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.user).key}")
        response = api.post(
            reverse("api-mobile-budget-push"),
            {"budgets": [{"month": "2024-05-01", "income": "500.00", "currency": "PKR"}]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["server_ids"], [existing.id])
        self.assertEqual(response.data["updated_ids"], [existing.id])
        existing.refresh_from_db()
        self.assertEqual(existing.income, Decimal("500.00"))
        self.assertEqual(Budget.objects.filter(user=self.user).count(), 1)

    def test_mobile_push_cannot_move_budget_onto_taken_month(self) -> None:
        Budget.objects.create(user=self.user, month=self.month)
        june = Budget.objects.create(user=self.user, month=date(2024, 6, 1))
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=self.user).key}")
        response = api.post(
            reverse("api-mobile-budget-push"),
            {
                "budgets": [
                    {"id": june.id, "month": "2024-05-01", "income": "1.00", "currency": "PKR"}
                ]
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["conflicting_ids"], [june.id])
        june.refresh_from_db()
        self.assertEqual(june.month, date(2024, 6, 1))


class MergeDuplicateMonthsMigrationTests(TransactionTestCase):
    """Migration 0025 merges duplicate months before it adds the constraint."""

    before = [("budgetapp", "0024_tagtransfer_updated_at")]
    after = [("budgetapp", "0025_unique_budget_month_per_user")]

    def tearDown(self) -> None:
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_duplicates_are_merged_into_the_active_budget(self) -> None:
        executor = MigrationExecutor(connection)
        executor.migrate(self.before)
        old_apps = executor.loader.project_state(self.before).apps
        OldBudget = old_apps.get_model("budgetapp", "Budget")
        OldExpense = old_apps.get_model("budgetapp", "Expense")

        # Only budgetapp moves back; accounts stays at its latest state.
        user = User.objects.create_user(
            username="dup", email="dup@example.com", password="testpassword"
        )
        month = date(2023, 3, 1)
        archived = OldBudget.objects.create(
            user_id=user.id, month=month, income=Decimal("100"), is_archived=True
        )
        active = OldBudget.objects.create(user_id=user.id, month=month, income=Decimal("900"))
        OldExpense.objects.create(budget_id=archived.id, name="Old rent", amount=Decimal("50"))
        OldExpense.objects.create(budget_id=active.id, name="Food", amount=Decimal("20"))

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.after)

        budgets = Budget.objects.filter(user_id=user.id, month=month)
        self.assertEqual(budgets.count(), 1)
        kept = budgets.get()
        self.assertEqual(kept.id, active.id)
        self.assertEqual(kept.income, Decimal("900"))
        self.assertEqual(sorted(kept.expenses.values_list("name", flat=True)), ["Food", "Old rent"])
        history = IncomeHistory.objects.get(budget=kept)
        self.assertEqual(history.old_amount, Decimal("100"))
        self.assertIn(str(archived.id), history.reason)
