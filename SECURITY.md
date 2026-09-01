# Security Policy

## Supported Versions

Security fixes are applied to the default branch of this repository.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Report it privately via your repository’s **Security → Advisories** tab, or email the maintainer directly.

Include:

- A description of the vulnerability
- Steps to reproduce
- Impact assessment (if known)
- Suggested fix (optional)

## Secrets and credentials

**Never commit:**

- `config.yaml` (copy from `config.yaml.example` locally)
- `.env` files
- Android keystores (`*.jks`, `key.properties`)
- API keys or passwords

**Budget PDF email:** each user stores their own Resend API key and from address on their profile. These live in your database on self-hosted instances — protect database backups accordingly.

**Django system mail** (password reset, etc.) uses `email.backend` in `config.yaml` (`console` or `smtp`).

## Android signing

Release signing uses repo-root `keystore.properties` + `keystore/*.jks`
(same layout as budget-notes). Never commit those files. Published APK
SHA-256 is in [docs/OBTAINIUM.md](docs/OBTAINIUM.md).

If an upload keystore was ever committed to git history, treat it as compromised: rotate the key, update any deploy secrets, and verify removal with:

```bash
git log --all -- '*.jks'
```

Never commit `keystore.properties`, `mobile/budget_mobile/android/key.properties`, or `*.jks`.

## Production checklist

- Set `app.debug: false` and a 50+ character `app.secret_key` (or `SECRET_KEY` env var)
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for your HTTPS origin
- Use HTTPS in production (`DEBUG=false` enables secure cookies in settings)
- Run `python manage.py collectstatic` behind a proper WSGI server (e.g. gunicorn)

## If secrets were ever committed

Assume any secret that touched git is compromised, even after removal from the latest commit.

1. **Revoke/rotate immediately** — Resend API keys, Django `secret_key`, superuser passwords, SMTP credentials, and any other exposed values.
2. **Scrub git history before going public** — remove sensitive files from all commits:

   ```bash
   pip install git-filter-repo
   git clone --mirror . ../repo-backup.git   # backup first
   git filter-repo --path config.yaml --invert-paths --force
   ```

3. **Verify** — scan full history and tracked files:

   ```bash
   gitleaks detect --source . --verbose
   ./scripts/audit_public_repo.sh
   ```

4. **Force-push only when ready** — collaborators must re-clone after a history rewrite:

   ```bash
   git push --force-with-lease origin main
   ```

## Database and Docker

**Per-user Resend keys** are stored in the database on self-hosted instances. Treat database backups as sensitive.

**Docker builds:** `config.yaml` is excluded from the Docker build context (`.dockerignore`). Mount or copy your local `config.yaml` at runtime — e.g. `docker compose` bind-mounts the project directory. Never bake real secrets into an image layer.
