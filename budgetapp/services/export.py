"""Portable JSON export of 1 budget.

This is the single place that shapes a budget as JSON for the REST API
(``GET /api/budgets/{id}/export/``) and for the MCP tools in
``budgetapp/services/mcp_tools.py``. The money comes straight from
``Budget.get_gross_budgeted_expenses`` and friends, so it matches the web UI
and the PDF report exactly.

A consumer such as the ``budget-notes`` app can turn each top-level expense
into an item of the month's note, and, for an expense that has sub-expenses,
make a second note named after that expense with its sub-expenses as items.
This module only exports the data; it does not shape it into notes.
"""

from __future__ import annotations

from typing import Any

from django.utils import timezone

from budgetapp.models import Budget

SCHEMA_VERSION = "1.0"


def build_budget_export(budget: Budget) -> dict[str, Any]:
    """Return 1 budget, its expenses and sub-expenses as a plain JSON-ready dict.

    Args:
        budget: The budget to export. The caller must have already checked
            that it belongs to the requesting user.
    """
    expenses = list(
        budget.expenses.select_related("category", "tag_foreign_key", "bill_reminder").order_by(
            "name"
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "app": "monAI",
        "exported_at": timezone.now().isoformat(),
        "budget": {
            "id": budget.id,
            "month": budget.month.isoformat(),
            "income": str(budget.income),
            "currency": budget.currency,
            "is_archived": budget.is_archived,
            "summary": {
                "gross": str(budget.get_gross_budgeted_expenses()),
                "returns": str(budget.get_total_returns()),
                "net": str(budget.get_net_budgeted_expenses()),
                "remaining": str(budget.get_remaining_budget()),
            },
        },
        "expenses": [_export_expense(expense) for expense in expenses],
    }


def _export_expense(expense: Any) -> dict[str, Any]:
    """Return 1 expense line with its sub-expenses, for ``build_budget_export``."""
    sub_expenses = list(expense.sub_expenses.order_by("created_at", "id"))
    return {
        "id": expense.id,
        "name": expense.name,
        "amount": str(expense.amount),
        "is_recurring": expense.is_recurring,
        "is_daily": expense.is_daily,
        "category": expense.category.name if expense.category else None,
        "account": expense.tag_foreign_key.name if expense.tag_foreign_key else None,
        "bill_reminder": expense.bill_reminder.name if expense.bill_reminder else None,
        "sub_expenses": [
            {
                "id": sub.id,
                "name": sub.name,
                "amount": str(sub.amount),
                "is_return": sub.is_return,
            }
            for sub in sub_expenses
        ],
    }
