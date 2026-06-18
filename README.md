# monAI — Django Budget Tracker

A self-hosted personal budget tracker built with Django. Manage monthly budgets, categorize expenses, track tags and debts, set savings goals, and optionally sync with a Flutter mobile companion.

**Full documentation:** [docs/README.md](docs/README.md) (configuration, APIs, mobile sync, scripts).

## Features

- Monthly budgets with income, expenses, sub-expenses, and returns
- Categories, tags, debts, bill reminders, and savings goals
- Minimal web UI (Bootstrap, Alpine.js, Anime.js)
- Budget PDF export and email (via your own [Resend](https://resend.com) account)
- Flutter Android app with offline-first sync (`mobile/budget_mobile/`)

## Quick start (personal use)

### 1. Clone and install

```bash
git clone https://github.com/Thireb/django_budget_tracker.git
cd django_budget_tracker

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
# or: uv sync
```

### 2. Configure

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` for local use:

- `app.debug: true` — required for comfortable local development
- `app.secret_key` — any string while `debug` is true; use a long random string for production
- `email.backend: console` — prints system mail (password reset, etc.) to the terminal

`config.yaml` is **gitignored**. Never commit it.

### 3. Database and admin user

```bash
python manage.py migrate
python manage.py setup_superuser
```

### 4. Run the web app

```bash
python manage.py runserver
```

Open **http://127.0.0.1:8000/** — log in, then use **/minimal/** for the dashboard.

For phone access on your LAN:

```bash
python manage.py runserver 0.0.0.0:8000
```

Optional: set `urls.local` in `config.yaml` to your machine’s LAN URL for CSRF (e.g. `http://192.168.1.10:8000`).

### 5. Email budget PDFs (optional)

Each user configures their **own** Resend credentials:

1. Create a [Resend](https://resend.com) account and verify a sender domain or address.
2. In the app: **Profile → Edit Profile** → set **Resend API key** and **from email**.
3. On a budget page, use **Email PDF**.

Without Resend on your profile, PDF email is disabled (system mail still uses `console` or SMTP from `config.yaml`).

### 6. Flutter mobile app (optional)

See [mobile/budget_mobile/README.md](mobile/budget_mobile/README.md).

**Build APK without installing Flutter** (Docker only):

```bash
chmod +x scripts/build_flutter_apk.sh
./scripts/build_flutter_apk.sh
```

APK output: `mobile/budget_mobile/build/app/outputs/flutter-apk/app-release.apk`

## Docker (optional)

With `config.yaml` in the project root:

```bash
docker compose up --build
```

App at **http://localhost:8000**. Redis is started for calendar cache; SQLite is mounted from the host by default.

## Project layout

```
django_budget_tracker/
├── accounts/           # User model and profile (incl. per-user Resend)
├── budgetapp/          # Models, minimal UI, REST + mobile APIs
├── budget_tracker/     # Django settings and config loader
├── mobile/budget_mobile/   # Flutter companion app
├── script_runner/      # Versioned management scripts
├── static/ templates/  # Web assets
├── config.yaml.example # Copy to config.yaml (gitignored)
├── docs/               # Detailed documentation
└── manage.py
```

## Security (public / self-hosted)

- Do **not** commit `config.yaml`, `.env`, keystores (`.jks`), or API keys.
- Budget PDF email uses **per-user** Resend keys stored in the database — not shared in `config.yaml`.
- See [SECURITY.md](SECURITY.md) for reporting vulnerabilities and keystore rotation notes.

## Development

```bash
pre-commit install
pre-commit run --all-files

python -m mypy budgetapp budget_tracker accounts script_runner
python manage.py test budgetapp.tests.test_goals \
  budgetapp.tests.test_debt_tag_and_pdf_context \
  budgetapp.tests.test_mobile_sync
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Optional deploy files

| File | Purpose |
|------|---------|
| `Dockerfile` / `docker-compose.yml` | Containerized local or server run |
| `Procfile` | Generic Heroku-style `gunicorn` start command |

## License

MIT — see [LICENSE](LICENSE).
