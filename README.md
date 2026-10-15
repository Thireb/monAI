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
git clone https://github.com/Thireb/monAI.git
cd monAI

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

## Self-host with Docker

This is the easiest way to run monAI on a home server for you and your family.
You need Docker with the `compose` plugin. You do not need `config.yaml`.

1. Get the code and make the settings file:

   ```bash
   git clone https://github.com/Thireb/monAI.git
   cd monAI
   cp .env.example .env
   ```

2. Edit `.env`. Set `SECRET_KEY` and `DB_PASSWORD` to long random strings.
   The file tells you how to make them. Git ignores `.env`, so it stays on your machine.

3. Start monAI:

   ```bash
   docker compose up -d --build
   ```

   This starts 3 services: `web` (the app), `db` (MariaDB) and `alerts` (the daily
   bill alerts). The app applies the database migrations when it starts.

4. Put HTTPS in front of the app. Login, the PWA and Web Push need HTTPS.
   With Tailscale, on the same machine:

   ```bash
   tailscale serve --bg 8000
   ```

   Then add the Tailscale host name to `ALLOWED_HOSTS`, and its `https://` address to
   `CSRF_TRUSTED_ORIGINS`, in `.env`. Run `docker compose up -d` again.

   To try monAI first without HTTPS, set `HTTPS_ONLY=false` and open http://localhost:8000.

5. Open the app and sign up. Make an account for each person in the family.
   Then set `ALLOW_SIGNUP=false` in `.env` and run `docker compose up -d`.
   Nobody else can make an account after that.

**Admin user (optional):** `docker compose exec web python manage.py setup_superuser`

**Update:** `git pull`, then `docker compose up -d --build`.

**Backup:** this command saves the whole database to `monai.sql` on your machine:

```bash
docker compose exec db sh -c 'mariadb-dump -u monai -p"$MARIADB_PASSWORD" monai' > monai.sql
```

The data is in the Docker volume `monai_db-data`. `docker compose down` keeps it.
`docker compose down -v` **deletes it**.

## Project layout

```
monAI/
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
| `Dockerfile` / `docker-compose.yml` / `.env.example` | Self-host with Docker (see above) |
| `Procfile` | Generic Heroku-style `gunicorn` start command |

## License

MIT — see [LICENSE](LICENSE).
