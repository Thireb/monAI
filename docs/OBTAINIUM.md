# Install & update with Obtainium (mobile companion)

The Flutter companion (`mobile/budget_mobile`) is distributed via **GitHub Releases**,
matching the [budget-notes](https://github.com/Thireb/budget-notes) FOSS pattern.
[Obtainium](https://github.com/ImranR98/Obtainium) can install the app and notify you
when a new tagged release ships.

## For users

### 1. Install Obtainium

- GitHub: https://github.com/ImranR98/Obtainium/releases
- Or F-Droid / IzzyOnDroid listing for Obtainium itself

### 2. Add monAI Budget

1. Open Obtainium → **Add App**
2. **App source URL:** your monAI GitHub repo URL (same place Releases are published)
3. Recommended options (if shown):
   - Leave **Include pre-releases** off
   - **APK filter** (optional): `MonAIBudget` — matches `MonAIBudget-*.apk`
4. Tap **Add**, then install when prompted

Latest APK: your repo → **Releases** → latest → `MonAIBudget-*.apk`

### 3. Verify the signing certificate (optional but recommended)

Release builds are signed with this certificate. Compare in Obtainium /
[AppVerifier](https://github.com/soupslurpr/AppVerifier) after install:

| Digest | Value |
|--------|--------|
| **SHA-256** | `A7:E7:08:56:62:FA:D2:1B:BF:1F:A3:3B:CB:F3:1E:BA:CD:72:4D:C0:BC:50:A6:F4:BC:BB:E4:5C:F6:5D:74:ED` |
| Package | `com.monai.budget.budget_mobile` |

If the SHA-256 differs, do not trust that APK.

### Manual install (without Obtainium)

1. Download `MonAIBudget-*.apk` from Releases
2. Open the file on your phone and install
3. For updates, repeat or switch to Obtainium

## For maintainers

Each update users receive through Obtainium requires:

1. Bump `version:` in [`mobile/budget_mobile/pubspec.yaml`](../mobile/budget_mobile/pubspec.yaml)
   (`versionName+versionCode`, e.g. `1.0.1+2`)
2. Ensure repo-root `keystore.properties` exists and points at `keystore/*.jks`
3. Build (budget-notes style):

   ```fish
   set -x JAVA_HOME /usr/lib/jvm/java-21-openjdk
   set -x ANDROID_HOME $HOME/Android/Sdk
   cd mobile/budget_mobile
   flutter clean
   flutter build apk --release
   # → build/app/outputs/flutter-apk/app-release.apk
   # Attach as MonAIBudget-<version>.apk
   ```

   Or: `./scripts/release_mobile_apk.sh` (same build + copies to `dist/`)

4. Tag + GitHub Release and attach **`MonAIBudget-<version>.apk`**
   (same signing key as the previous release)
5. Prefer one primary `.apk` asset per mobile release so Obtainium does not need a filter

Do **not** rotate the release keystore; Android / Obtainium treat a new signer as a different app.

See also [PLAY_STORE.md](PLAY_STORE.md) for AAB / Play Console.
