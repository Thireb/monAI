# AGENTS.md

## Cursor Cloud specific instructions

### Services

| Service | How to run | Notes |
|---------|-----------|-------|
| Django dev server | `source venv/bin/activate && python manage.py runserver 0.0.0.0:8000` | Main app at http://127.0.0.1:8000, UI at /minimal/ |
| Celery worker | `celery -A budget_tracker worker -l info` | Optional; requires Redis |
| Redis | Not pre-installed | Only needed for Celery async tasks |

### Development quick-reference

- **Virtual environment**: `/workspace/venv` (activate with `source /workspace/venv/bin/activate`)
- **Configuration**: `config.yaml` at project root (copied from `config.yaml.example`; gitignored). Uses SQLite and console email backend by default.
- **Superuser credentials** (dev): `admin@monai.dev` / `admin1234`
- **Auth note**: The API token endpoint (`/api-token-auth/`) uses email as the username field, not the `username` attribute.

### Running lint / tests / build

- **Lint (flake8):** `python -m flake8 --max-line-length=100 budgetapp/ budget_tracker/ accounts/`
- **Lint (black check):** `python -m black --check --line-length=100 budgetapp/ budget_tracker/ accounts/`
- **Tests:** `python manage.py test budgetapp.tests.test_goals budgetapp.tests.test_debt_tag_and_pdf_context budgetapp.tests.test_mobile_sync`
  - Note: `python manage.py test` with no label discovers zero tests; always specify the module path.
- **Build (collectstatic):** `python manage.py collectstatic --noinput`
- **Pre-commit (all hooks):** `pre-commit run --all-files`

### Gotchas

- Python packages must be installed in the venv (`/workspace/venv`); the system Python is externally-managed (PEP 668).
- WeasyPrint system libraries (Cairo, Pango, GDK-Pixbuf) are already available in the VM image.
- The `staticfiles/` directory warning during tests is harmless; tests still pass.
- The root URL `/` redirects (302) to login; use `/accounts/login/` for the login form or `/minimal/` after authentication.
