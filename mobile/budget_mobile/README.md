# monAI Budget (Flutter)

Offline-first companion for the Django budget app. Sync runs over HTTP when your home server is reachable (budgets only in v1).

## Django (server)

1. Create / activate a venv and install deps (`requirements.txt`).
2. Apply migrations (adds `authtoken` and existing app tables):

   ```bash
   python manage.py migrate
   ```

3. Bind to the LAN so the phone can connect:

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. Note your PC LAN IP (e.g. `http://192.168.1.10:8000`) and enter it in the app under **Settings**.

## Mobile API (v1)

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/health/` | none |
| POST | `/api/mobile/auth/token/` | body `email`, `password` → `{ "token": "..." }` |
| GET | `/api/mobile/budgets/pull/?updated_after=` | `Authorization: Token …` |
| POST | `/api/mobile/budgets/push/` | `Authorization: Token …`, body `{ "budgets": [ … ] }` |

Push response includes `server_ids` in the same order as the request list (needed to map new local rows to server IDs).

## Flutter app

```bash
cd mobile/budget_mobile
flutter pub get
flutter test
flutter run
```

Release APK (after configuring signing in `android/app/build.gradle`):

```bash
flutter build apk --release
```

## Tests

- **Django:** `python manage.py test budgetapp.tests.test_mobile_sync`
- **Flutter:** `flutter test` (uses in-memory stubs; does not open SQLite FFI on Linux CI)
