# Contributing

Thank you for contributing to monAI Budget Tracker.

## Setup

1. Clone the repository and create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -e ".[dev]"
   ```

   Or with uv:

   ```bash
   uv sync --extra dev
   ```

2. Copy configuration:

   ```bash
   cp config.yaml.example config.yaml
   ```

   For local development, keep `app.debug: true` in `config.yaml`.

3. Run migrations and create a superuser:

   ```bash
   python manage.py migrate
   python manage.py setup_superuser
   ```

4. Install pre-commit hooks:

   ```bash
   pre-commit install
   ```

## Code Quality

Run before submitting a pull request:

```bash
# Format
python -m black --line-length=100 budgetapp/ budget_tracker/ accounts/ script_runner/

# Lint
python -m flake8 --max-line-length=100 budgetapp/ budget_tracker/ accounts/

# Type check
python -m mypy budgetapp budget_tracker accounts script_runner

# Tests
python manage.py test budgetapp.tests

# All pre-commit hooks
pre-commit run --all-files
```

## Style Guidelines

- Follow PEP 8 with a 100-character line limit.
- Add type hints and docstrings to all public functions, classes, and modules.
- Use `from __future__ import annotations` in Python modules you edit.
- Keep templates, JS, and CSS in separate files (see `.cursor/rules/structuring.mdc`).
- Do not commit secrets, keystores, or local `config.yaml`.

## Before publishing (maintainers)

Run these checks before making the repository public or cutting a release:

```bash
./scripts/audit_public_repo.sh
gitleaks detect --source . --verbose
```

If secrets were ever committed, follow [SECURITY.md](SECURITY.md#if-secrets-were-ever-committed) (rotate credentials and scrub git history).

## Pull Requests

- Keep changes focused and minimal.
- Update documentation when behavior changes.
- Ensure CI passes (Python lint, type check, tests; Flutter if mobile code changed).
