# CLAUDE.md

Working notes for Claude Code in this repo. Read `AGENTS.md` too. It has the
lint, test and build commands.

@AGENTS.md

## What this project is

monAI is a self-hosted personal budget tracker. It has 2 clients:

- A Django web app (Django 5.1, DRF, allauth). The new UI is at `/app/` (`/` opens it). The classic UI is at `/minimal/`.
- A Flutter Android app in `mobile/budget_mobile/`. It is offline-first. It
  keeps data in SQLite (`sqflite`) and syncs with Django over HTTP.

The owner uses it with PKR as the default currency.

## Current work

Follow `docs/REDESIGN_PLAN.md`. Tick its boxes when work is merged.
The Flutter app is being retired: do not improve it or the `/api/mobile/*` sync.

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
| `accounts/` | Custom user model and profile. Each user has a Resend key. |
| `budgetapp/models.py` | All domain models. |
| `budgetapp/app/` | **New UI** at `/app/` (namespace `app`): views, forms, urls. New UI work goes here. |
| `budgetapp/services/` | Money logic for the new UI: `month.py` (month figures, Safe to spend today), `quick_add.py`, `months.py`, `goals.py` (goals, debt payoff), `bills.py` (bill timeline), `home.py`. |
| `budgetapp/minimal/views/` | Classic web UI views (`/minimal/`), 1 file per feature. |
| `budgetapp/minimal/urls.py` | Web UI routes, namespace `minimal`. |
| `budgetapp/api_urls.py` | REST and mobile sync routes under `/api/`. |
| `budgetapp/api_mobile_*.py` | Mobile pull/push views. |
| `budgetapp/serializers_mobile.py` | Mobile sync serializers and `save_*_for_user` helpers. |
| `budgetapp/tests/` | Django tests. |
| `script_runner/` | Versioned management scripts. `registry.py` lists them. |
| `templates/app/`, `static/app/` | New UI templates (components, partials) and its CSS tokens and JS. |
| `templates/minimal/`, `static/{css,js}/minimal-*/` | Classic UI templates and assets, by feature. |
| `mobile/budget_mobile/lib/` | Flutter: `database/`, `repositories/`, `services/`, `screens/`. |
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

**Money rules.** These rules are the same in the web UI, the PDF and the app:

- gross = the sum of the expense amounts
- returns = the sum of the sub-expenses with `is_return=True`
- net = gross − returns
- remaining = income − gross + returns

Use `Budget.get_summary_display_strings()` and
`Budget.get_tag_account_breakdown()`. Do not calculate these values again in
views, templates or Dart. Use `Decimal` for money in Python.

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
10. Web pages extend `minimal/base.html`. Use Alpine.js for state and
    anime.js for animation. Put reusable parts in `templates/minimal/components/`.
11. Use `blank=True` (not `null=True`) for `CharField` and `TextField`.
12. Use the `TextChoices` enum values, not string literals.

## Add a new entity to mobile sync

Use `TagTransfer` as the model to copy. Commit `62f0a7e` shows the full change.

1. Make sure that the Django model has `updated_at` (`auto_now=True`).
2. In `serializers_mobile.py`, add a `Mobile<X>SyncSerializer` and a
   `Mobile<X>PushItemSerializer`.
3. In `api_mobile_catalog.py`, add a pull view and a push view. The pull view
   accepts `?updated_after=`. The push view supports `"deleted": true`. It
   returns `server_ids` in the same order as the request.
4. Add the 2 routes to `budgetapp/api_urls.py`.
5. In Flutter, add the table in `database/app_database.dart`. Increase
   `_dbVersion` by 1 and add an `if (oldVersion < N)` step in `onUpgrade`.
6. Add a repository in `lib/repositories/`. Add client methods in
   `services/mobile_budget_api_client.dart`.
7. Add the entity to `services/budget_sync_service.dart` in the correct order.
   The order is: categories → tags → budgets → expenses → sub-expenses →
   tag-transfers. The app pushes first, then pulls.
8. Add tests to `budgetapp/tests/test_mobile_sync.py` or a new test module.
9. Update the API table in `mobile/budget_mobile/README.md`.

## Tests

**Warning:** `manage.py test budgetapp.tests` fails with a `TypeError`.
The cause is that `budgetapp/tests.py` and `budgetapp/tests/` both exist.
Give each module by name:

```fish
.venv/bin/python manage.py test budgetapp.tests.test_goals \
  budgetapp.tests.test_debt_tag_and_pdf_context budgetapp.tests.test_mobile_sync \
  budgetapp.tests.test_tag_transfers budgetapp.tests.test_bill_reminders \
  budgetapp.tests.test_budget_summary budgetapp.tests.test_user_resend_email \
  budgetapp.tests.test_budget_month_unique budgetapp.tests.test_budget_page_browser \
  budgetapp.tests.test_pwa_offline budgetapp.tests.test_services budgetapp.tests.test_app_views \
  budgetapp.tests.test_app_goals budgetapp.tests.test_app_manage budgetapp.tests.test_app_browser
```

On 2026-10-15, all 179 tests passed (about 2 minutes).
Logs with `🔴 400` in the output are normal. Some tests check error responses.

`test_budget_page_browser`, `test_pwa_offline` and `test_app_browser` drive headless Chromium with Playwright. The classic pages need network
access, because they load jQuery and anime.js from CDNs. The new UI loads HTMX and
anime.js from `static/app/vendor/`. It is skipped when
Playwright is missing. To set it up: `uv sync --extra dev`, then
`.venv/bin/python -m playwright install chromium`.

For Flutter: `cd mobile/budget_mobile; and flutter analyze; and flutter test`.

## Before you finish a change

1. Run the Django tests above. If you changed Dart code, run the Flutter checks.
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
