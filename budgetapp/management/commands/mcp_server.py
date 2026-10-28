"""Run the monAI MCP server over stdio, for 1 user, for a local client such as LM Studio.

See ``docs/mcp_server.md`` for how to point LM Studio at this command. It never opens a
network port: stdio only, so it is safe to run next to a self-hosted instance whose repo
is public. Each tool call acts as the 1 user named by ``--email``, with the same forms and
services the web UI uses (``budgetapp/services/mcp_tools.py``).
"""

from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractBaseUser
from django.core.management.base import BaseCommand, CommandError, CommandParser

from budgetapp.services import mcp_tools


class Command(BaseCommand):
    """Start the stdio MCP server that exposes monAI's budget tools."""

    help = "Run the monAI MCP server over stdio for 1 user (for LM Studio or another MCP client)."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add the ``--email`` option naming which user the session acts as."""
        parser.add_argument(
            "--email",
            required=True,
            help="Email of the monAI user this MCP session acts as.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Look up the user, build the tool server, and run it over stdio."""
        email = options["email"]
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
        except user_model.DoesNotExist as exc:
            raise CommandError(f"No monAI user with email {email!r}.") from exc
        server = build_server(user)
        server.run(transport="stdio")


def build_server(user: AbstractBaseUser) -> Any:
    """Build the ``FastMCP`` server with its tools bound to ``user``.

    Each tool is a thin async wrapper: it runs the matching
    ``budgetapp.services.mcp_tools`` function in a worker thread with
    ``sync_to_async``, since Django's ORM cannot run on the stdio event loop thread.
    """
    from mcp.server.fastmcp import FastMCP

    server = FastMCP(
        "monAI",
        instructions=(
            "Tools for 1 monAI budget tracker user. Amounts are plain decimal strings "
            "('2500.00'), months are 'YYYY-MM'. There are no delete tools: ask the user "
            "to delete things in the web UI."
        ),
    )

    @server.tool()
    async def budget_list() -> list[dict[str, Any]]:
        """List the user's budgets, newest month first."""
        return await sync_to_async(mcp_tools.list_budgets)(user)

    @server.tool()
    async def budget_get(budget_id: int) -> dict[str, Any]:
        """Return 1 budget with its expenses and sub-expenses."""
        return await sync_to_async(mcp_tools.get_budget)(user, budget_id)

    @server.tool()
    async def budget_upsert(month: str, income: str, currency: str = "PKR") -> dict[str, Any]:
        """Create, or update, the user's 1 budget for a month ('YYYY-MM')."""
        return await sync_to_async(mcp_tools.upsert_budget)(user, month, income, currency)

    @server.tool()
    async def budget_export_json(budget_id: int) -> dict[str, Any]:
        """Export 1 budget as a portable JSON document (for backup or another app)."""
        return await sync_to_async(mcp_tools.export_budget_json)(user, budget_id)

    @server.tool()
    async def expense_upsert(
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
        return await sync_to_async(mcp_tools.upsert_expense)(
            user,
            budget_id,
            name,
            amount,
            expense_id,
            category_name,
            account_name,
            is_daily,
            is_recurring,
        )

    @server.tool()
    async def subexpense_add(
        expense_id: int, amount: str, name: str = "", is_return: bool = False
    ) -> dict[str, Any]:
        """Record a spend, or a return, against an expense line."""
        return await sync_to_async(mcp_tools.add_subexpense)(
            user, expense_id, amount, name, is_return
        )

    @server.tool()
    async def category_upsert(name: str, color: str = "#000000") -> dict[str, Any]:
        """Create, or recolor, a category."""
        return await sync_to_async(mcp_tools.upsert_category)(user, name, color)

    @server.tool()
    async def tag_upsert(
        name: str, color: str = "#2196f3", is_active: bool = True
    ) -> dict[str, Any]:
        """Create, or change, an account tag."""
        return await sync_to_async(mcp_tools.upsert_tag)(user, name, color, is_active)

    @server.tool()
    async def goal_list() -> list[dict[str, Any]]:
        """List the user's savings goals."""
        return await sync_to_async(mcp_tools.list_goals)(user)

    @server.tool()
    async def goal_upsert(
        name: str, target_amount: str, goal_id: int | None = None, target_date: str = ""
    ) -> dict[str, Any]:
        """Create, or update, a savings goal."""
        return await sync_to_async(mcp_tools.upsert_goal)(
            user, name, target_amount, goal_id, target_date or None
        )

    @server.tool()
    async def goal_contribution_add(
        goal_id: int, amount: str, source: str = "", notes: str = ""
    ) -> dict[str, Any]:
        """Add money to a goal and refresh its saved total."""
        return await sync_to_async(mcp_tools.add_goal_contribution)(
            user, goal_id, amount, source, notes
        )

    return server
