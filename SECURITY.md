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

If an upload keystore was ever committed to git history, treat it as compromised: rotate the key, update any deploy secrets, and verify removal with:

```bash
git log --all -- '*.jks'
```

Never commit `mobile/budget_mobile/android/key.properties` or `*.jks`.

## Production checklist

- Set `app.debug: false` and a 50+ character `app.secret_key` (or `SECRET_KEY` env var)
- Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for your HTTPS origin
- Use HTTPS in production (`DEBUG=false` enables secure cookies in settings)
- Run `python manage.py collectstatic` behind a proper WSGI server (e.g. gunicorn)
