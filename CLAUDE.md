# CLAUDE.md

Working notes for Claude Code in this repo. Read `AGENTS.md` too. It has the
lint, test and build commands.

@AGENTS.md

## What this project is

monAI is a self-hosted personal budget tracker:

- A Django web app (Django 5.1, DRF, allauth). The UI is at `/app/` (`/` opens it). It is a PWA
  that also works offline. The classic UI (`/minimal/`) was removed on 2026-10-15.
- The Flutter Android app was removed on 2026-10-15, with the `/api/mobile/*` sync.
  Its last code is at the git tag `flutter-final`. The untracked `mobile/` folder on
  this machine is leftover build output and signing keys: do not read or commit it.

The owner uses it with PKR as the default currency.

## Current work

Follow `docs/REDESIGN_PLAN.md`. Tick its boxes when work is merged.

## Local machine (not Cursor Cloud)

The `AGENTS.md` paths (`/workspace/venv`) are for Cursor Cloud. On this machine:

- The shell is **fish**. Use `set -x VAR value`, not `export`.
- The venv is `.venv/` (made by `uv`). Use `.venv/bin/python` directly.
- Python is 3.13.1.
- `config.yaml` uses the **MySQL** engine. The test database is MySQL too.
- Do not read or print the values in `config.yaml`, `keystore.properties` or
  `keystore/`. They hold secrets.

## Repo map

| Path | Content |
|------|---------|
| `budget_tracker/` | Settings. `config.py` loads `config.yaml`. |
| `accounts/` | Custom user model and profile. Each user has a Resend key, encrypted in the database (`accounts/fields.py`). |
| `budgetapp/models.py` | All domain models. |
| `budgetapp/app/` | **New UI** at `/app/` (namespace `app`): views, forms, urls. New UI work goes here. |
| `budgetapp/services/` | Money logic for the new UI: `month.py` (month figures, Safe to spend today), `quick_add.py`, `months.py`, `goals.py` (goals, debt payoff), `bills.py` (bill timeline), `push.py` (Web Push bill alerts), `recap.py` (month recap), `report.py` (PDF report email), `home.py`. |
| `budgetapp/api_urls.py` | REST routes under `/api/` (budgets, goals) and `/api/health/`. |
| `budgetapp/tests/` | Django tests. |
| `script_runner/` | Versioned management scripts. `registry.py` lists them. |
| `templates/app/`, `static/app/` | New UI templates (components, partials, `pdf/`) and its CSS tokens and JS. |
| `static/js/service-worker.js`, `static/js/pwa-register.js` | The PWA service worker (offline pages, Web Push) and its registration. |
| `docs/` | Project docs. `docs/agent_intent/` has the LLM action schemas. |

## Domain model

- `Budget`: 1 per user per month. It has `income`, `currency`, `is_archived`.
- `Expense`: a line in a budget. It has an optional `category`, an optional
  `tag_foreign_key` (the account tag) and an optional `bill_reminder`.
- `SubExpense`: a spend against an expense. If `is_return=True`, it is a refund.
- `Category`, `Tag`: owned by a user. A tag is an "account".
- `TagTransfer`: a zero-sum move of money between 2 tags in 1 budget. It does
  not change the remaining budget. `save()` calls `full_clean()`.
- `BillReminder`: a non-monthly bill. It can add an expense to the budget of
  its due month.
- `Goal` and `GoalContribution`, `Debt` and `DebtTransaction`: savings and debts.
- `BudgetLog`, `RecentUpdate`, `IncomeHistory`, `ArchivedBudget`: history.

**Money rules.** These rules are the same in the web UI, the PDF and the REST API:

- gross = the sum of the expense amounts
- returns = the sum of the sub-expenses with `is_return=True`
- net = gross − returns
- remaining = income − gross + returns

Use `Budget.get_summary_display_strings()` and
`Budget.get_tag_account_breakdown()`. Do not calculate these values again in
views or templates. Use `Decimal` for money in Python.

The new UI gets every figure from `build_month_snapshot()` in
`budgetapp/services/month.py`. Its docstring defines a line's `left`
(amount − spent − returned) and **Safe to spend today**, which uses only lines
with `is_daily=True`. Add new figures there, with a test in `test_services.py`.

## Project rules

These rules come from `.cursorrules`, `.cursor/rules/*.mdc` and
`CONTRIBUTING.md`.

1. Read the full file and 2 or 3 similar features before you write new code.
   Follow the pattern that most of the code uses.
2. Make the smallest change that solves the problem. Do not delete code unless
   the user tells you to.
3. Use class-based views for web views and for API views.
4. Always filter data by the owner (`user=request.user`). For child objects,
   filter by `budget__user`. Use `get_object_or_404` with the user filter.
5. Keep backend lines at 100 characters or fewer. Black uses 100.
6. Add `from __future__ import annotations`, type hints and docstrings to the
   Python modules that you edit.
7. Use a plain string when there is no variable. Do not use an f-string then.
8. Keep HTML, JS and CSS in separate files. Exception: WeasyPrint PDF
   templates keep the styles in the HTML file.
9. Templates only show data. Do calculations in the backend and send the
   result in the context.
10. Web pages extend `app/base.html`. Use HTMX for server requests and anime.js
    for animation. Put reusable parts in `templates/app/components/` and
    `templates/app/partials/`. Use the CSS tokens in `static/app/css/tokens.css`.
11. Use `blank=True` (not `null=True`) for `CharField` and `TextField`.
12. Use the `TextChoices` enum values, not string literals.

## Tests

Run all tests:

```fish
.venv/bin/python manage.py test budgetapp.tests
```

To run 1 module, give its name, for example `budgetapp.tests.test_services`.

On 2026-10-15, all 150 tests passed (about 80 seconds).
Logs with `🔴 400` or `🔥 EXCEPTION` (404) in the output are normal. Some tests check
error responses.

`test_pwa_offline` and `test_app_browser` drive headless Chromium with Playwright.
The UI loads HTMX and anime.js from `static/app/vendor/`, so no network is needed.
These tests are skipped when Playwright is missing. To set it up: `uv sync --extra dev`, then
`.venv/bin/python -m playwright install chromium`.

## Before you finish a change

1. Run the Django tests above.
2. Run black, flake8 and mypy on the files that you changed (see `AGENTS.md`).
3. If you changed a model, run `.venv/bin/python manage.py makemigrations budgetapp`.
   Read the new migration before you keep it.
4. Update the docs if the behavior changed.

## Git

- Commit only when the user asks. The main branch is `main`.
- Never commit `config.yaml`, `keystore*`, `*.jks`, `app.log`, `debug.log`
  or `backup_*.json`.
- `.cursor/rules/career-log.mdc` is untracked. Do not add it unless the user
  asks.
