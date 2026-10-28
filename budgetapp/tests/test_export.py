"""Tests for the budget JSON export: the service function and its REST endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from budgetapp.models import Budget, Category, Expense, SubExpense, Tag
from budgetapp.services.export import build_budget_export

User = get_user_model()
D = Decimal


class BuildBudgetExportTests(TestCase):
    """build_budget_export shapes 1 budget as portable JSON."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="exporter", email="exporter@example.com", password="testpassword"
        )
        self.budget = Budget.objects.create(
            user=self.user, month=date(2026, 10, 1), income=D("50000"), currency="PKR"
        )
        self.category = Category.objects.create(
            user=self.user, name="Housing", slug="housing", color="#112233"
        )
        self.tag = Tag.objects.create(user=self.user, name="Cash", slug="cash", color="#2e8b57")
        self.house = Expense.objects.create(
            budget=self.budget,
            name="House",
            amount=D("20000"),
            category=self.category,
            tag_foreign_key=self.tag,
        )
        SubExpense.objects.create(expense=self.house, name="Rent", amount=D("18000"))
        SubExpense.objects.create(
            expense=self.house, name="Deposit back", amount=D("500"), is_return=True
        )

    def test_top_level_fields(self) -> None:
        data = build_budget_export(self.budget)
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["app"], "monAI")
        self.assertEqual(data["budget"]["month"], "2026-10-01")
        self.assertEqual(data["budget"]["income"], "50000")
        self.assertEqual(data["budget"]["currency"], "PKR")

    def test_summary_matches_money_rules(self) -> None:
        data = build_budget_export(self.budget)
        summary = data["budget"]["summary"]
        self.assertEqual(summary["gross"], str(self.budget.get_gross_budgeted_expenses()))
        self.assertEqual(summary["returns"], str(self.budget.get_total_returns()))
        self.assertEqual(summary["net"], str(self.budget.get_net_budgeted_expenses()))
        self.assertEqual(summary["remaining"], str(self.budget.get_remaining_budget()))

    def test_expense_carries_category_account_and_subexpenses(self) -> None:
        data = build_budget_export(self.budget)
        self.assertEqual(len(data["expenses"]), 1)
        expense = data["expenses"][0]
        self.assertEqual(expense["name"], "House")
        self.assertEqual(expense["category"], "Housing")
        self.assertEqual(expense["account"], "Cash")
        self.assertEqual(len(expense["sub_expenses"]), 2)
        names = {sub["name"]: sub["is_return"] for sub in expense["sub_expenses"]}
        self.assertEqual(names, {"Rent": False, "Deposit back": True})

    def test_expense_without_category_or_account_is_null(self) -> None:
        Expense.objects.create(budget=self.budget, name="Misc", amount=D("100"))
        data = build_budget_export(self.budget)
        misc = next(e for e in data["expenses"] if e["name"] == "Misc")
        self.assertIsNone(misc["category"])
        self.assertIsNone(misc["account"])


class BudgetExportApiTests(TestCase):
    """GET /api/budgets/{id}/export/ returns the same shape, for the owner only."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="owner", email="owner@example.com", password="testpassword"
        )
        self.other = User.objects.create_user(
            username="other2", email="other2@example.com", password="testpassword"
        )
        self.budget = Budget.objects.create(
            user=self.user, month=date(2026, 11, 1), income=D("1000")
        )

    def _client(self, user: object) -> APIClient:
        api = APIClient()
        api.credentials(HTTP_AUTHORIZATION=f"Token {Token.objects.create(user=user).key}")
        return api

    def test_owner_gets_export(self) -> None:
        response = self._client(self.user).get(
            reverse("api-budget-export", kwargs={"pk": self.budget.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["budget"]["id"], self.budget.id)

    def test_other_user_gets_404(self) -> None:
        response = self._client(self.other).get(
            reverse("api-budget-export", kwargs={"pk": self.budget.pk})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
