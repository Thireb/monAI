"""Tests for budgetapp.services.mcp_tools: the functions behind the MCP server.

These call the plain functions directly (no stdio, no event loop): the
``mcp_server`` management command only wraps them for the MCP transport.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from budgetapp.models import Budget, Category, Expense, Goal, Tag
from budgetapp.services import mcp_tools

User = get_user_model()
D = Decimal


class McpToolsTests(TestCase):
    """Each tool acts only on the given user's own data."""

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            username="agent", email="agent@example.com", password="testpassword"
        )
        self.other = User.objects.create_user(
            username="agent2", email="agent2@example.com", password="testpassword"
        )
        self.budget = Budget.objects.create(
            user=self.user, month=date(2026, 10, 1), income=D("50000")
        )

    def test_upsert_budget_creates_then_updates_same_month(self) -> None:
        created = mcp_tools.upsert_budget(self.user, "2026-12", "10000", "PKR")
        self.assertEqual(Budget.objects.filter(user=self.user, month=date(2026, 12, 1)).count(), 1)
        updated = mcp_tools.upsert_budget(self.user, "2026-12", "20000", "PKR")
        self.assertEqual(created["budget"]["id"], updated["budget"]["id"])
        self.assertEqual(updated["budget"]["income"], "20000.00")
        self.assertEqual(Budget.objects.filter(user=self.user, month=date(2026, 12, 1)).count(), 1)

    def test_upsert_budget_rejects_bad_month(self) -> None:
        with self.assertRaises(mcp_tools.ToolError):
            mcp_tools.upsert_budget(self.user, "not-a-month", "100")

    def test_get_budget_refuses_other_users_budget(self) -> None:
        with self.assertRaises(mcp_tools.ToolError):
            mcp_tools.get_budget(self.other, self.budget.id)

    def test_upsert_expense_creates_category_and_account_by_name(self) -> None:
        result = mcp_tools.upsert_expense(
            self.user,
            self.budget.id,
            "House",
            "20000",
            category_name="Housing",
            account_name="Cash",
        )
        expense = next(e for e in result["expenses"] if e["name"] == "House")
        self.assertEqual(expense["category"], "Housing")
        self.assertEqual(expense["account"], "Cash")
        self.assertTrue(Category.objects.filter(user=self.user, name="Housing").exists())
        self.assertTrue(Tag.objects.filter(user=self.user, name="Cash").exists())

    def test_upsert_expense_reuses_existing_category_by_name_case_insensitive(self) -> None:
        Category.objects.create(user=self.user, name="Housing", slug="housing", color="#000000")
        mcp_tools.upsert_expense(
            self.user, self.budget.id, "House", "1000", category_name="housing"
        )
        self.assertEqual(Category.objects.filter(user=self.user, name__iexact="housing").count(), 1)

    def test_upsert_expense_refuses_expense_from_another_budget(self) -> None:
        other_budget = Budget.objects.create(
            user=self.user, month=date(2027, 1, 1), income=D("1000")
        )
        expense = Expense.objects.create(budget=other_budget, name="Elsewhere", amount=D("10"))
        with self.assertRaises(mcp_tools.ToolError):
            mcp_tools.upsert_expense(
                self.user, self.budget.id, "House", "10", expense_id=expense.id
            )

    def test_subexpense_add_records_spend_and_return(self) -> None:
        expense = Expense.objects.create(budget=self.budget, name="Groceries", amount=D("5000"))
        spend = mcp_tools.add_subexpense(self.user, expense.id, "500", "Milk")
        self.assertFalse(spend["is_return"])
        refund = mcp_tools.add_subexpense(self.user, expense.id, "100", "Refund", is_return=True)
        self.assertTrue(refund["is_return"])
        self.assertEqual(expense.get_total_returns(), D("100"))

    def test_subexpense_add_rejects_zero_amount(self) -> None:
        expense = Expense.objects.create(budget=self.budget, name="Groceries", amount=D("5000"))
        with self.assertRaises(mcp_tools.ToolError):
            mcp_tools.add_subexpense(self.user, expense.id, "0")

    def test_goal_contribution_add_syncs_current_amount(self) -> None:
        goal = Goal.objects.create(user=self.user, name="Laptop", target_amount=D("1000"))
        mcp_tools.add_goal_contribution(self.user, goal.id, "300")
        mcp_tools.add_goal_contribution(self.user, goal.id, "200")
        goal.refresh_from_db()
        self.assertEqual(goal.current_amount, D("500"))

    def test_goal_contribution_add_refuses_other_users_goal(self) -> None:
        goal = Goal.objects.create(user=self.other, name="Laptop", target_amount=D("1000"))
        with self.assertRaises(mcp_tools.ToolError):
            mcp_tools.add_goal_contribution(self.user, goal.id, "100")

    def test_export_budget_json_matches_build_budget_export(self) -> None:
        from budgetapp.services.export import build_budget_export

        self.budget.refresh_from_db()
        via_tool = mcp_tools.export_budget_json(self.user, self.budget.id)
        via_service = build_budget_export(self.budget)
        del via_tool["exported_at"], via_service["exported_at"]
        self.assertEqual(via_tool, via_service)
