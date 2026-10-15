# monAI — Django Budget Tracker

A self-hosted personal budget tracker built with Django. Manage monthly budgets, categorize expenses, track tags and debts, and set savings goals. Install it on a phone as a PWA; it also works offline.

**Full documentation:** [docs/README.md](docs/README.md) (configuration, APIs, scripts).

## Features

- Monthly budgets with income, expenses, sub-expenses, and returns
- Categories, tags, debts, bill reminders, and savings goals
- Web app and PWA at `/app/` (HTMX, anime.js): quick add, offline use, goals, bill alerts by Web Push
- Budget PDF export and email (via your own [Resend](https://resend.com) account)

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

Open **http://127.0.0.1:8000/** and log in. The app opens at **/app/**.

For phone access on your LAN:

```bash
python manage.py runserver 0.0.0.0:8000
```

Optional: set `urls.local` in `config.yaml` to your machine’s LAN URL for CSRF (e.g. `http://192.168.1.10:8000`).

### 5. Email budget PDFs (optional)

Each user configures their **own** Resend credentials:

1. Create a [Resend](https://resend.com) account and verify a sender domain or address.
2. In the app: **Profile → Edit Profile** → set **Resend API key** and **from email**.
3. On a month page, open **Month settings** and use **Email me the PDF report**.

Without Resend on your profile, PDF email is disabled (system mail still uses `console` or SMTP from `config.yaml`).

### 6. Phone (PWA)

Open the app on the phone over HTTPS (for example with `tailscale serve`) and use
**Add to Home screen**. Bill alerts by Web Push need a daily timer: see
[docs/WEB_PUSH.md](docs/WEB_PUSH.md).

The Flutter Android app was removed on 2026-10-15. Its last code is at the git tag
`flutter-final`.

## Docker (optional)

Create `config.yaml` from the example (see step 2 above). It is **not** copied into the image at build time; `docker compose` bind-mounts your project directory so the container reads `config.yaml` from the host.

```bash
docker compose up --build
```

App at **http://localhost:8000**. Redis is started for calendar cache; SQLite is mounted from the host by default.

## Project layout

```
django_budget_tracker/
├── accounts/           # User model and profile (incl. per-user Resend)
├── budgetapp/          # Models, the web UI (app/), services, REST API
├── budget_tracker/     # Django settings and config loader
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
python manage.py test budgetapp.tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Optional deploy files

| File | Purpose |
|------|---------|
| `Dockerfile` / `docker-compose.yml` | Containerized local or server run |
| `Procfile` | Generic Heroku-style `gunicorn` start command |

## License

MIT — see [LICENSE](LICENSE).
