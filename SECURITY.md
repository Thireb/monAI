# Security Policy

## Supported Versions

Security fixes are applied to the default branch of this repository.

## Reporting a Vulnerability

If you discover a security vulnerability, please **do not** open a public GitHub issue.

Instead, report it privately by emailing the repository maintainer or opening a
[GitHub Security Advisory](https://github.com/Thireb/django_budget_tracker/security/advisories/new)
if you have access.

Include:

- A description of the vulnerability
- Steps to reproduce
- Impact assessment (if known)
- Suggested fix (optional)

We aim to acknowledge reports within 7 days.

## Android Keystore Rotation

A signing keystore (`.cursor/monai-upload.jks`) was previously committed to git
history and has been removed. **Treat that key as compromised.**

Before publishing to Google Play or distributing signed APKs:

1. Generate a new upload keystore locally (never commit it).
2. Update signing material locally if you use release builds (`android/key.properties`).
3. If the app is already on Play Store, follow Google's key upgrade process.

To verify the keystore is gone from history:

```bash
git log --all -- .cursor/monai-upload.jks
# Should return no commits
```

If history was rewritten with `git filter-repo`, re-add your remote:

```bash
git remote add origin git@github.com:Thireb/django_budget_tracker.git
git push --force-with-lease origin main
```

## Secrets in Development

- Copy `config.yaml.example` to `config.yaml` (gitignored).
- Never commit `config.yaml`, `.env`, keystores, or API keys.
- Use environment variables (`SECRET_KEY`) in production.
- Budget PDF emails use **per-user** Resend credentials saved in Profile → Edit Profile.
