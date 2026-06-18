#!/usr/bin/env bash
# Build the Flutter release APK using Docker (no local Flutter/Android SDK required).
#
# Prerequisites: Docker installed and running.
#
# Usage (from repo root):
#   ./scripts/build_flutter_apk.sh
#
# Output:
#   mobile/budget_mobile/build/app/outputs/flutter-apk/app-release.apk

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT/mobile/budget_mobile"
IMAGE="${FLUTTER_DOCKER_IMAGE:-ghcr.io/cirruslabs/flutter:stable}"
APK_PATH="$APP_DIR/build/app/outputs/flutter-apk/app-release.apk"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is not installed or not in PATH." >&2
  exit 1
fi

echo "Building Flutter APK with image: $IMAGE"
echo "App directory: $APP_DIR"

docker run --rm \
  -v "$APP_DIR:/app" \
  -w /app \
  "$IMAGE" \
  bash -lc "flutter pub get && flutter build apk --release"

echo ""
echo "Done. APK: $APK_PATH"
