"""Tool functions behind the monAI MCP server (``manage.py mcp_server``).

Each function acts for 1 user and reuses the forms and services the web UI and
the REST API already use (``budgetapp/app/forms.py``, ``budgetapp/services/quick_add.py``,
``budgetapp/services/goals.py``), so the money rules and the ownership checks stay the
same for a chat agent as for a person using the app. See ``docs/agent_intent/README.md``
for the wider design and ``docs/mcp_server.md`` for how to run the server.

There are no delete tools here on purpose: an LLM session can create and change
budgets, lines and goals, but deleting stays in the web UI.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from django.contrib.auth.models import AbstractBaseUser

from budgetapp.app.forms import AccountForm, CategoryForm, LineForm
from budgetapp.models import Budget, Category, Expense, Goal, GoalContribution, SubExpense, Tag
from budgetapp.services.export import build_budget_export
from budgetapp.services.goals import sync_goal_amount
from budgetapp.services.quick_add import record_return, record_spend


class ToolError(ValueError):
    """A tool could not run with the given input. The message is safe to show the model."""


def _decimal(raw: str, field: str) -> Decimal:
    """Parse ``raw`` as a ``Decimal``, or raise ``ToolError`` naming ``field``."""
    try:
        return Decimal(str(raw))
    except InvalidOperation as exc:
        raise ToolError(f"{field} must be a plain number, for example '2500.00'.") from exc


def _month_date(month: str) -> date:
    """Parse ``YYYY-MM`` or ``YYYY-MM-DD`` as the first day of that month."""
    try:
        parts = [int(part) for part in month.split("-")[:2]]
        return date(parts[0], parts[1], 1)
    except (ValueError, IndexError) as exc:
        raise ToolError("month must look like '2026-10'.") from exc


def _own_budget(user: AbstractBaseUser, budget_id: int) -> Budget:
    """Return the user's budget ``budget_id``, or raise ``ToolError``."""
    try:
        return Budget.objects.get(pk=budget_id, user=user)
    except Budget.DoesNotExist as exc:
        raise ToolError(f"No budget {budget_id} for this user.") from exc


def _own_expense(user: AbstractBaseUser, expense_id: int) -> Expense:
    """Return the user's expense line ``expense_id``, or raise ``ToolError``."""
    try:
        return Expense.objects.select_related("budget").get(pk=expense_id, budget__user=user)
    except Expense.DoesNotExist as exc:
        raise ToolError(f"No expense line {expense_id} for this user.") from exc


def _find_or_create_category(user: AbstractBaseUser, name: str) -> Category | None:
    """Return the user's category named ``name``, creating it if needed."""
    name = name.strip()
    if not name:
        return None
    existing = Category.objects.filter(user=user, name__iexact=name).first()
    if existing is not None:
        return existing
    form = CategoryForm(data={"name": name, "color": "#000000"}, user=user)
    if not form.is_valid():
        raise ToolError(f"Could not create category '{name}': {form.errors.as_text()}")
    return form.save()


def _find_or_create_tag(user: AbstractBaseUser, name: str) -> Tag | None:
    """Return the user's account tag named ``name``, creating it if needed."""
    name = name.strip()
    if not name:
        return None
    existing = Tag.objects.filter(user=user, name__iexact=name).first()
    if existing is not None:
        return existing
    form = AccountForm(data={"name": name, "color": "#2196f3", "is_active": True}, user=user)
    if not form.is_valid():
        raise ToolError(f"Could not create account '{name}': {form.errors.as_text()}")
    return form.save()


def list_budgets(user: AbstractBaseUser) -> list[dict[str, Any]]:
    """List the user's budgets, newest month first."""
    budgets = Budget.objects.filter(user=user).order_by("-month")
    return [
        {
            "id": budget.id,
            "month": budget.month.isoformat(),
            "income": str(budget.income),
            "currency": budget.currency,
            "is_archived": budget.is_archived,
            "remaining_budget": str(budget.get_remaining_budget()),
        }
        for budget in budgets
    ]


def get_budget(user: AbstractBaseUser, budget_id: int) -> dict[str, Any]:
    """Return 1 budget with its expenses and sub-expenses."""
    return build_budget_export(_own_budget(user, budget_id))


def export_budget_json(user: AbstractBaseUser, budget_id: int) -> dict[str, Any]:
    """Return 1 budget as a portable JSON document (for backup or another app)."""
    return build_budget_export(_own_budget(user, budget_id))


def upsert_budget(
    user: AbstractBaseUser, month: str, income: str, currency: str = "PKR"
) -> dict[str, Any]:
    """Create, or update, the user's 1 budget for ``month`` (``YYYY-MM``)."""
    month_date = _month_date(month)
    income_dec = _decimal(income, "income")
    if income_dec < 0:
        raise ToolError("income cannot be negative.")
    budget, _ = Budget.objects.update_or_create(
        user=user, month=month_date, defaults={"income": income_dec, "currency": currency}
    )
    return get_budget(user, budget.id)


def upsert_expense(
    user: AbstractBaseUser,
    budget_id: int,
    name: str,
    amount: str,
    expense_id: int | None = None,
    category_name: str = "",
    account_name: str = "",
    is_daily: bool = False,
    is_recurring: bool = False,
) -> dict[str, Any]:
    """Add an expense line to a budget, or update an existing 1 of the same budget."""
    budget = _own_budget(user, budget_id)
    instance = None
    if expense_id is not None:
        instance = _own_expense(user, expense_id)
        if instance.budget_id != budget.id:
            raise ToolError(f"Expense {expense_id} is not in budget {budget_id}.")
    category = _find_or_create_category(user, category_name) if category_name else None
    account = _find_or_create_tag(user, account_name) if account_name else None
    data = {
        "name": name,
        "amount": amount,
        "category": category.id if category else "",
        "tag_foreign_key": account.id if account else "",
        "is_daily": is_daily,
        "is_recurring": is_recurring,
    }
    form = LineForm(data=data, user=user, instance=instance)
    if not form.is_valid():
        raise ToolError(form.errors.as_text())
    expense = form.save(commit=False)
    expense.budget = budget
    expense.save()
    return get_budget(user, budget.id)


def add_subexpense(
    user: AbstractBaseUser,
    expense_id: int,
    amount: str,
    name: str = "",
    is_return: bool = False,
) -> dict[str, Any]:
    """Record a spend, or a return, against an expense line."""
    expense = _own_expense(user, expense_id)
    amount_dec = _decimal(amount, "amount")
    if amount_dec <= 0:
        raise ToolError("amount must be more than 0.")
    sub: SubExpense = (
        record_return(expense, amount_dec, name)
        if is_return
        else record_spend(expense, amount_dec, name)
    )
    return {
        "id": sub.id,
        "expense_id": expense.id,
        "name": sub.name,
        "amount": str(sub.amount),
        "is_return": sub.is_return,
    }


def upsert_category(user: AbstractBaseUser, name: str, color: str = "#000000") -> dict[str, Any]:
    """Create, or rename, a category."""
    existing = Category.objects.filter(user=user, name__iexact=name).first()
    form = CategoryForm(data={"name": name, "color": color}, user=user, instance=existing)
    if not form.is_valid():
        raise ToolError(form.errors.as_text())
    category = form.save()
    return {"id": category.id, "name": category.name, "color": category.color}


def upsert_tag(
    user: AbstractBaseUser, name: str, color: str = "#2196f3", is_active: bool = True
) -> dict[str, Any]:
    """Create, or rename, an account tag."""
    existing = Tag.objects.filter(user=user, name__iexact=name).first()
    form = AccountForm(
        data={"name": name, "color": color, "is_active": is_active}, user=user, instance=existing
    )
    if not form.is_valid():
        raise ToolError(form.errors.as_text())
    tag = form.save()
    return {"id": tag.id, "name": tag.name, "color": tag.color, "is_active": tag.is_active}


def list_goals(user: AbstractBaseUser) -> list[dict[str, Any]]:
    """List the user's savings goals."""
    goals = Goal.objects.filter(user=user).order_by("-is_active", "name")
    return [
        {
            "id": goal.id,
            "name": goal.name,
            "target_amount": str(goal.target_amount),
            "current_amount": str(goal.current_amount),
            "target_date": goal.target_date.isoformat() if goal.target_date else None,
            "is_active": goal.is_active,
            "progress_percentage": goal.progress_percentage,
        }
        for goal in goals
    ]


def upsert_goal(
    user: AbstractBaseUser,
    name: str,
    target_amount: str,
    goal_id: int | None = None,
    target_date: str | None = None,
) -> dict[str, Any]:
    """Create, or update, a savings goal."""
    target_dec = _decimal(target_amount, "target_amount")
    if target_dec <= 0:
        raise ToolError("target_amount must be more than 0.")
    target_date_obj: date | None = None
    if target_date:
        try:
            target_date_obj = date.fromisoformat(target_date)
        except ValueError as exc:
            raise ToolError("target_date must look like '2027-01-31'.") from exc

    if goal_id is not None:
        try:
            goal = Goal.objects.get(pk=goal_id, user=user)
        except Goal.DoesNotExist as exc:
            raise ToolError(f"No goal {goal_id} for this user.") from exc
        goal.name = name
        goal.target_amount = target_dec
        goal.target_date = target_date_obj
        goal.save(update_fields=["name", "target_amount", "target_date", "updated_at"])
    else:
        goal = Goal.objects.create(
            user=user, name=name, target_amount=target_dec, target_date=target_date_obj
        )
    return {
        "id": goal.id,
        "name": goal.name,
        "target_amount": str(goal.target_amount),
        "current_amount": str(goal.current_amount),
        "target_date": goal.target_date.isoformat() if goal.target_date else None,
    }


def add_goal_contribution(
    user: AbstractBaseUser, goal_id: int, amount: str, source: str = "", notes: str = ""
) -> dict[str, Any]:
    """Add money to a goal and refresh its saved total."""
    try:
        goal = Goal.objects.get(pk=goal_id, user=user)
    except Goal.DoesNotExist as exc:
        raise ToolError(f"No goal {goal_id} for this user.") from exc
    amount_dec = _decimal(amount, "amount")
    if amount_dec <= 0:
        raise ToolError("amount must be more than 0.")
    contribution = GoalContribution.objects.create(
        goal=goal, amount=amount_dec, source=source, notes=notes
    )
    sync_goal_amount(goal)
    goal.refresh_from_db(fields=["current_amount"])
    return {
        "id": contribution.id,
        "goal_id": goal.id,
        "amount": str(contribution.amount),
        "goal_current_amount": str(goal.current_amount),
    }
