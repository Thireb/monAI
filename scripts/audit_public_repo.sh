#!/usr/bin/env bash
# Quick scan for patterns that should not appear in a public repo (tracked files only).
# Usage: ./scripts/audit_public_repo.sh

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

FAIL=0

tracked_files() {
  git ls-files | grep -v '^scripts/audit_public_repo\.sh$'
}

check_rg() {
  local label="$1"
  local pattern="$2"
  local matches
  matches="$(tracked_files | xargs rg -l "$pattern" 2>/dev/null || true)"
  if [[ -n "$matches" ]]; then
    echo "FAIL ($label):" >&2
    echo "$matches" >&2
    FAIL=1
  fi
}

# Hardcoded personal / deployment identifiers
check_rg "personal hostname" 'monai-42qk|preinstructive-dilan'
check_rg "dev credentials" 'admin@monai\.dev|change-me-dev-password'
check_rg "insecure secret fallback" 'django-insecure-fallback'
check_rg "removed capacitor" 'capacitor-app/'
check_rg "removed render blueprint" '^render\.yaml$'

# Binary secrets
if git ls-files '*.jks' '*.keystore' 2>/dev/null | grep -q .; then
  echo "FAIL: keystore files are tracked:" >&2
  git ls-files '*.jks' '*.keystore' >&2
  FAIL=1
fi

if git ls-files config.yaml .env 'budget_tracker/.env' 2>/dev/null | grep -q .; then
  echo "FAIL: local config/env files are tracked:" >&2
  git ls-files config.yaml .env 'budget_tracker/.env' >&2
  FAIL=1
fi

if [[ "$FAIL" -ne 0 ]]; then
  exit 1
fi

echo "OK: tracked files look safe for a public repo."
echo "Local-only (gitignored): config.yaml, .env, db.sqlite3, keystores."
