# MCP server (talk to monAI from an AI chat)

monAI ships a small [MCP](https://modelcontextprotocol.io/) server so a local
AI chat client, such as LM Studio, can list budgets, add expenses, and record
spends and goal contributions by talking to it directly. It reuses the same
forms and services as the web UI and the REST API
(`budgetapp/app/forms.py`, `budgetapp/services/quick_add.py`,
`budgetapp/services/goals.py`), so the money rules and the ownership checks
are identical. This follows the design sketch in `docs/agent_intent/README.md`:
models propose, code disposes.

## How it runs

The server is a Django management command, `mcp_server`. It talks to its MCP
client over **stdio only** (standard input/output): it never opens a network
port, so it stays safe to run next to a self-hosted instance whose repo is
public. It acts as 1 monAI user, named by `--email`.

```fish
.venv/bin/python manage.py mcp_server --email you@example.com
```

LM Studio starts this command itself; you do not run it by hand. Add it to
LM Studio's `mcp.json` (Program → Integrations → Edit `mcp.json`):

```json
{
  "mcpServers": {
    "monai": {
      "command": "/mnt/xraydisk/Programming/monAI/.venv/bin/python",
      "args": ["manage.py", "mcp_server", "--email", "you@example.com"],
      "cwd": "/mnt/xraydisk/Programming/monAI"
    }
  }
}
```

Use the absolute path to this repo's `.venv/bin/python` and the email of the
monAI account the chat should act as. Restart LM Studio's MCP connection
after editing `mcp.json`.

## Tools

| Tool | Does |
|------|------|
| `budget_list` | List the user's budgets, newest month first. |
| `budget_get` | 1 budget with its expenses and sub-expenses. |
| `budget_upsert` | Create, or update, the 1 budget for a month (`YYYY-MM`). |
| `budget_export_json` | Export 1 budget as portable JSON (see below). |
| `expense_upsert` | Add, or edit, an expense line. Category and account names are created if they do not exist yet. |
| `subexpense_add` | Record a spend, or a return, against an expense line. |
| `category_upsert` | Create, or recolor, a category. |
| `tag_upsert` | Create, or change, an account tag. |
| `goal_list` | List the user's savings goals. |
| `goal_upsert` | Create, or update, a savings goal. |
| `goal_contribution_add` | Add money to a goal; its saved total is refreshed. |

Amounts are plain decimal strings, such as `"2500.00"`. Months are
`"YYYY-MM"`. There are **no delete tools**: ask the chat to tell you what it
would delete, then delete it yourself in the web UI. Most MCP clients,
including LM Studio, also ask you to approve each tool call before it runs.

## JSON export

`budget_export_json` (an MCP tool) and `GET /api/budgets/{id}/export/` (a
REST endpoint, token-authenticated like the rest of `/api/`) return the same
shape, built by `budgetapp/services/export.py`:

```json
{
  "schema_version": "1.0",
  "app": "monAI",
  "exported_at": "2026-10-28T10:00:00+00:00",
  "budget": {
    "id": 12,
    "month": "2026-10-01",
    "income": "150000.00",
    "currency": "PKR",
    "is_archived": false,
    "summary": {"gross": "90000.00", "returns": "500.00", "net": "89500.00", "remaining": "60500.00"}
  },
  "expenses": [
    {
      "id": 101,
      "name": "House",
      "amount": "30000.00",
      "is_recurring": true,
      "is_daily": false,
      "category": "Housing",
      "account": "Cash",
      "bill_reminder": null,
      "sub_expenses": [
        {"id": 501, "name": "Rent", "amount": "28000.00", "is_return": false},
        {"id": 502, "name": "Deposit back", "amount": "500.00", "is_return": true}
      ]
    }
  ]
}
```

This is meant as a companion-app export, for example for
[budget-notes](https://github.com/Thireb/budget-notes): a budget-notes
importer can turn the month's `expenses` into the items of 1 note (the
month), and, for an expense that has `sub_expenses`, make a second note
named after that expense with its sub-expenses as items. That mapping is
budget-notes' job; this export only gives it faithful data.

## Adding a tool

1. Write the plain function in `budgetapp/services/mcp_tools.py`. It takes
   the acting user as its first argument, reuses the matching form or
   service, and raises `mcp_tools.ToolError` with a message safe to show the
   model on bad input.
2. Add a test in `budgetapp/tests/test_mcp_tools.py` that calls the function
   directly (no MCP transport needed).
3. Wire it into `budgetapp/management/commands/mcp_server.py` as a thin
   `async def` tool that calls the function with `sync_to_async` (Django's
   ORM cannot run on the stdio event loop thread directly).
4. Add it to the table above.
