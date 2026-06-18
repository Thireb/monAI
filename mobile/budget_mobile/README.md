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

Push responses include `server_ids` in the **same order** as the request list.

**Deletes:** include items with `"deleted": true` and the existing server **`id`** in `expenses` or `sub_expenses` push payloads. Validation and cascade behavior live in `MobileExpensePushView` / `MobileSubExpensePushView` (`budgetapp/api_mobile_catalog.py`).

**Sync order (app):** push categories → tags → budgets → expenses → sub-expenses, then pull the same.

### Budget summary vs Django

The budget detail summary cards (gross budgeted expenses, returns, net, remaining) follow **`Budget`** in `budgetapp/models.py`: gross = sum of expense amounts, returns from sub-expenses with `is_return`, remaining = **income − gross + returns**. Same rules as the minimal web UI and PDF context built from `get_summary_display_strings`.

## Build APK with Docker (no local Flutter SDK)

You only need **Docker** — no Flutter, Android SDK, or Java on your machine.

From the **repository root**:

```bash
chmod +x scripts/build_flutter_apk.sh
./scripts/build_flutter_apk.sh
```

The first run downloads the Flutter Docker image (`ghcr.io/cirruslabs/flutter:stable`, ~2 GB). Later builds reuse the cache.

**Output:** `mobile/budget_mobile/build/app/outputs/flutter-apk/app-release.apk`

Copy the APK to your phone and install (enable “Install unknown apps” if prompted).

### Release signing (optional)

Debug builds work for personal use. For release signing, copy `android/key.properties.example` to `android/key.properties` and place your keystore beside it. See `android/key.properties.example` for field names. Never commit `key.properties` or `*.jks`.

### Alternate image

Override the Flutter image if needed:

```bash
FLUTTER_DOCKER_IMAGE=cirrusci/flutter:stable ./scripts/build_flutter_apk.sh
```

## Local Flutter build (optional)

If you already have Flutter and the Android SDK installed:

```bash
cd mobile/budget_mobile
flutter pub get
flutter build apk --release
```

Output: `build/app/outputs/flutter-apk/app-release.apk`

## Tests

- Django: `python manage.py test budgetapp.tests.test_mobile_sync`
- Flutter: `flutter test` (widget test uses stubs; no device SDK required)
