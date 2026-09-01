#!/usr/bin/env bash
# Convenience wrapper that mirrors budget-notes' FOSS release flow:
#   ./gradlew clean assembleRelease
#   → attach BudgetNotes-<version>.apk
#
# For Flutter (monAI):
#   flutter clean && flutter build apk --release
#   → attach MonAIBudget-<version>.apk
#
# Usage (from monAI repo root):
#   ./scripts/release_mobile_apk.sh
#
# Requires: Flutter SDK + Android SDK on PATH (same idea as budget-notes
# needing JDK + ANDROID_HOME). No Docker path — keep one pattern.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_DIR="$ROOT/mobile/budget_mobile"
PUBSPEC="$APP_DIR/pubspec.yaml"
RAW_APK="$APP_DIR/build/app/outputs/flutter-apk/app-release.apk"
DIST_DIR="$APP_DIR/dist"

if [[ ! -f "$PUBSPEC" ]]; then
  echo "Error: missing $PUBSPEC" >&2
  exit 1
fi

if ! command -v flutter >/dev/null 2>&1; then
  cat >&2 <<'EOF'
Error: flutter is not on PATH.

budget-notes builds with:  ./gradlew clean assembleRelease
monAI builds with:         flutter build apk --release

Install the Flutter SDK, then ensure `flutter` works (and ANDROID_HOME
points at your SDK — typically ~/Android/Sdk). See docs/PLAY_STORE.md.
EOF
  exit 1
fi

if [[ ! -f "$ROOT/keystore.properties" ]]; then
  echo "warning: no keystore.properties at repo root — release will not be upload-signed" >&2
  echo "  cp keystore.properties.example keystore.properties" >&2
fi

VERSION_LINE="$(grep -E '^version:' "$PUBSPEC" | head -1 | awk '{print $2}')"
VERSION_NAME="${VERSION_LINE%%+*}"
OUT_NAME="MonAIBudget-${VERSION_NAME}.apk"
OUT_PATH="$DIST_DIR/$OUT_NAME"

# Match budget-notes: clean + release assemble, then name the asset.
(
  cd "$APP_DIR"
  flutter clean
  flutter pub get
  flutter build apk --release
)

if [[ ! -f "$RAW_APK" ]]; then
  echo "Error: expected APK missing: $RAW_APK" >&2
  exit 1
fi

mkdir -p "$DIST_DIR"
cp -f "$RAW_APK" "$OUT_PATH"

echo ""
echo "Signed when keystore.properties is present:"
echo "  $RAW_APK"
echo "Attach to a GitHub Release as:"
echo "  $OUT_PATH"
echo "  (asset name: $OUT_NAME)"
