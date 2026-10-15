# AGENTS.md

## Agent / LLM integration sketch

For **voice or text → structured actions** (English-first), see
`docs/agent_intent/README.md` and JSON Schemas under
`docs/agent_intent/schema/`. The sketch maps stable `action` ids to existing
`/api/mobile/…` and `/api/…` REST endpoints; it does not add a server-side LLM.

## Cursor Cloud specific instructions

### Services

| Service | How to run | Notes |
|---------|-----------|-------|
| Django dev server | `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000` | Main app at http://127.0.0.1:8000, UI at /app/ |
| Flutter mobile app | `cd mobile/budget_mobile && flutter pub get && flutter analyze` | Offline-first companion; runs tests headlessly |
| Celery worker | `celery -A budget_tracker worker -l info` | Optional; requires Redis |
| Redis | Not pre-installed | Only needed for Celery async tasks |

### Development quick-reference

- **Virtual environment**: `/workspace/venv` (activate with `source /workspace/venv/bin/activate`)
- **Configuration**: `config.yaml` at project root (copied from `config.yaml.example`; gitignored). Set `app.debug: true` for local development.
- **Superuser**: Run `python manage.py setup_superuser` or set `DJANGO_SUPERUSER_*` env vars.
- **Auth note**: The API token endpoint (`/api-token-auth/`) uses email as the username field, not the `username` attribute.

### Running lint / tests / build

**Django (Python):**
- **Lint (flake8):** `python -m flake8 --max-line-length=100 budgetapp/ budget_tracker/ accounts/ script_runner/`
- **Lint (black check):** `python -m black --check --line-length=100 budgetapp/ budget_tracker/ accounts/ script_runner/`
- **Type check (mypy):** `python -m mypy budgetapp budget_tracker accounts script_runner`
- **Tests:** `python manage.py test budgetapp.tests`
  - Note: `python manage.py test` with no label discovers zero tests; give the `budgetapp.tests` label.
- **Build (collectstatic):** `python manage.py collectstatic --noinput`
- **Pre-commit (all hooks):** `pre-commit run --all-files`

**Flutter mobile:**
- **Lint:** `cd mobile/budget_mobile && flutter analyze`
- **Tests:** `cd mobile/budget_mobile && flutter test`
- Flutter SDK at `/opt/flutter/bin` (added to PATH via `~/.bashrc`). Current version: 3.41.5 (Dart 3.11.3).

### Gotchas

- Python packages must be installed in the venv (`/workspace/venv`); the system Python is externally-managed (PEP 668).
- WeasyPrint system libraries (Cairo, Pango, GDK-Pixbuf) are already available in the VM image.
- The `staticfiles/` directory warning during tests is harmless; tests still pass.
- The root URL `/` redirects (302) to `/app/`, which asks for login first; the login form is at `/accounts/login/`.
- Flutter requires `git config --global --add safe.directory /opt/flutter` (already done in setup).
- Flutter `pubspec.yaml` requires Dart ^3.9.0; the installed Flutter 3.41.5 ships Dart 3.11.3 which satisfies this.
- `DEBUG` defaults to `false` when `config.yaml` is absent; set `app.debug: true` in config or `DEBUG=true` for local dev.
- Never commit `config.yaml`, keystores, or API keys. See `SECURITY.md`.
