#!/usr/bin/env bash
# Alias for ./scripts/release_mobile_apk.sh (named Release asset).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec "$ROOT/scripts/release_mobile_apk.sh"
