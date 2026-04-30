# AGENTS.md

## Cursor Cloud specific instructions

### Services

| Service | How to run | Notes |
|---------|-----------|-------|
| Django dev server | `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000` | Main app at http://127.0.0.1:8000, UI at /minimal/ |
| Capacitor app (npm) | `cd capacitor-app && npx cap sync` | WebView Android wrapper; no Android SDK needed for sync |
| Flutter mobile app | `cd mobile/budget_mobile && flutter pub get && flutter analyze` | Offline-first companion; runs tests headlessly |
| Celery worker | `celery -A budget_tracker worker -l info` | Optional; requires Redis |
| Redis | Not pre-installed | Only needed for Celery async tasks |

### Development quick-reference

- **Virtual environment**: `/workspace/venv` (activate with `source /workspace/venv/bin/activate`)
- **Configuration**: `config.yaml` at project root (copied from `config.yaml.example`; gitignored). Uses SQLite and console email backend by default.
- **Superuser credentials** (dev): `admin@monai.dev` / `admin1234`
- **Auth note**: The API token endpoint (`/api-token-auth/`) uses email as the username field, not the `username` attribute.

### Running lint / tests / build

**Django (Python):**
- **Lint (flake8):** `python -m flake8 --max-line-length=100 budgetapp/ budget_tracker/ accounts/`
- **Lint (black check):** `python -m black --check --line-length=100 budgetapp/ budget_tracker/ accounts/`
- **Tests:** `python manage.py test budgetapp.tests.test_goals budgetapp.tests.test_debt_tag_and_pdf_context budgetapp.tests.test_mobile_sync`
  - Note: `python manage.py test` with no label discovers zero tests; always specify the module path.
- **Build (collectstatic):** `python manage.py collectstatic --noinput`
- **Pre-commit (all hooks):** `pre-commit run --all-files`

**Capacitor (Node.js):**
- **Install:** `cd capacitor-app && npm install`
- **Sync:** `cd capacitor-app && npx cap sync`
- Node.js 20 is installed system-wide.

**Flutter mobile:**
- **Lint:** `cd mobile/budget_mobile && flutter analyze`
- **Tests:** `cd mobile/budget_mobile && flutter test`
- Flutter SDK at `/opt/flutter/bin` (added to PATH via `~/.bashrc`). Current version: 3.41.5 (Dart 3.11.3).

### Gotchas

- Python packages must be installed in the venv (`/workspace/venv`); the system Python is externally-managed (PEP 668).
- WeasyPrint system libraries (Cairo, Pango, GDK-Pixbuf) are already available in the VM image.
- The `staticfiles/` directory warning during tests is harmless; tests still pass.
- The root URL `/` redirects (302) to login; use `/accounts/login/` for the login form or `/minimal/` after authentication.
- Flutter requires `git config --global --add safe.directory /opt/flutter` (already done in setup).
- The Capacitor app cannot build APKs without Android SDK, but `npx cap sync` works for validating web assets and config.
- Flutter `pubspec.yaml` requires Dart ^3.9.0; the installed Flutter 3.41.5 ships Dart 3.11.3 which satisfies this.
