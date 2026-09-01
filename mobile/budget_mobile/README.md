# monAI Budget (Flutter)

Offline-first companion for the Django budget app. Sync runs over HTTP when your home server is reachable.

## Django (server)

1. Create or activate a venv and install deps (`requirements.txt`).
2. Apply migrations (`authtoken`, and `Category.updated_at` for incremental category sync):

   ```bash
   python manage.py migrate
   ```

3. Bind to the LAN so the phone can connect:

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. Enter your PC LAN URL in the app (e.g. `http://192.168.1.10:8000`) under **Settings**, then **Save URL & sign in**.

## Mobile API

All authenticated routes use header: `Authorization: Token <token>`  
Token from: `POST /api/mobile/auth/token/` with JSON `{"email","password"}`.

| Method | Path | Body / query |
|--------|------|----------------|
| GET | `/api/health/` | none |
| POST | `/api/mobile/auth/token/` | `email`, `password` |
| GET | `/api/mobile/categories/pull/` | optional `updated_after` |
| POST | `/api/mobile/categories/push/` | `{ "categories": [ … ] }` |
| GET | `/api/mobile/tags/pull/` | optional `updated_after` |
| POST | `/api/mobile/tags/push/` | `{ "tags": [ … ] }` |
| GET | `/api/mobile/budgets/pull/` | optional `updated_after` |
| POST | `/api/mobile/budgets/push/` | `{ "budgets": [ … ] }` |
| GET | `/api/mobile/expenses/pull/` | optional `updated_after` |
| POST | `/api/mobile/expenses/push/` | `{ "expenses": [ … ] }` |
| GET | `/api/mobile/sub-expenses/pull/` | optional `updated_after` |
| POST | `/api/mobile/sub-expenses/push/` | `{ "sub_expenses": [ … ] }` |
| GET | `/api/mobile/tag-transfers/pull/` | optional `updated_after` |
| POST | `/api/mobile/tag-transfers/push/` | `{ "tag_transfers": [ … ] }` |

Push responses include `server_ids` in the **same order** as the request list.

**Deletes:** include items with `"deleted": true` and the existing server **`id`** in `expenses`, `sub_expenses`, or `tag_transfers` push payloads. Validation and cascade behavior live in `MobileExpensePushView` / `MobileSubExpensePushView` / `MobileTagTransferPushView` (`budgetapp/api_mobile_catalog.py`).

**Sync order (app):** push categories → tags → budgets → expenses → sub-expenses → tag-transfers, then pull the same.

### Budget summary vs Django

The budget detail summary cards (gross budgeted expenses, returns, net, remaining) follow **`Budget`** in `budgetapp/models.py`: gross = sum of expense amounts, returns from sub-expenses with `is_return`, remaining = **income − gross + returns**. Same rules as the minimal web UI and PDF context built from `get_summary_display_strings`.

## FOSS release (GitHub + Obtainium)

Same pattern as [budget-notes](https://github.com/Thireb/budget-notes)
(`./gradlew clean assembleRelease` → attach `BudgetNotes-<version>.apk`):

```fish
# One-time signing: docs/PLAY_STORE.md (keystore.properties at monAI repo root)
set -x JAVA_HOME /usr/lib/jvm/java-21-openjdk
set -x ANDROID_HOME $HOME/Android/Sdk
cd mobile/budget_mobile
flutter clean
flutter build apk --release
# Signed when keystore.properties is present:
# build/app/outputs/flutter-apk/app-release.apk
# Attach to a GitHub Release as MonAIBudget-<version>.apk
```

Or from repo root: `./scripts/release_mobile_apk.sh` (copies to `dist/MonAIBudget-<version>.apk`).

Release cert SHA-256:
`A7:E7:08:56:62:FA:D2:1B:BF:1F:A3:3B:CB:F3:1E:BA:CD:72:4D:C0:BC:50:A6:F4:BC:BB:E4:5C:F6:5D:74:ED`

User install: [docs/OBTAINIUM.md](../../docs/OBTAINIUM.md). Play / AAB: [docs/PLAY_STORE.md](../../docs/PLAY_STORE.md).

## Tests

- Django: `python manage.py test budgetapp.tests.test_mobile_sync`
- Flutter: `flutter test` (widget test uses stubs; no device SDK required)
