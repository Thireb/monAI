# Play Store / signed release guide (Flutter companion)

Release signing follows the same layout as
[budget-notes](https://github.com/Thireb/budget-notes): `keystore.properties` +
`keystore/*.jks` at the **monAI repo root** (never committed).

FOSS sideload path remains **GitHub Releases + Obtainium** — see [OBTAINIUM.md](OBTAINIUM.md).

## Requirements

- Flutter SDK (`flutter` on `PATH`)
- JDK 17+ (21 recommended)
- Android SDK (`ANDROID_HOME`, typically `~/Android/Sdk`)

## One-time: create an upload keystore

From the **repository root**:

```fish
mkdir -p keystore
keytool -genkeypair -v \
  -keystore keystore/monai-budget-upload.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias monai_budget
cp keystore.properties.example keystore.properties
# edit keystore.properties with real passwords
```

`keystore/`, `*.jks`, and `keystore.properties` are gitignored.

Prefer **Play App Signing** if you upload to Play: upload the AAB; let Google manage
the app-signing key. Keep your upload keystore backed up offline.

Print SHA-256 for Obtainium / README:

```fish
keytool -list -v -keystore keystore/monai-budget-upload.jks -alias monai_budget
```

Current release cert SHA-256:

`A7:E7:08:56:62:FA:D2:1B:BF:1F:A3:3B:CB:F3:1E:BA:CD:72:4D:C0:BC:50:A6:F4:BC:BB:E4:5C:F6:5D:74:ED`

## FOSS release APK (GitHub + Obtainium)

Same steps as budget-notes (`./gradlew clean assembleRelease`), Flutter equivalent:

```fish
set -x JAVA_HOME /usr/lib/jvm/java-21-openjdk
set -x ANDROID_HOME $HOME/Android/Sdk
cd mobile/budget_mobile
flutter clean
flutter build apk --release
```

Signed when repo-root `keystore.properties` is present:

```text
mobile/budget_mobile/build/app/outputs/flutter-apk/app-release.apk
```

Attach to a GitHub Release as `MonAIBudget-<version>.apk`.

Or from repo root (copies/renames the asset for you):

```fish
./scripts/release_mobile_apk.sh
# → mobile/budget_mobile/dist/MonAIBudget-<versionName>.apk
```

## Build Play Store bundle (AAB)

```fish
cd mobile/budget_mobile
flutter build appbundle --release
```

Output:

```text
build/app/outputs/bundle/release/app-release.aab
```

## Versioning

In [`mobile/budget_mobile/pubspec.yaml`](../mobile/budget_mobile/pubspec.yaml):

```yaml
version: 1.0.0+1
#          ^^^^^  versionName (user-visible)
#                ^^ versionCode (must increase every Play / Obtainium upload)
```

Bump **both** before each store or Obtainium release.

## Debug vs release package names

- Release: `com.monai.budget.budget_mobile`
- Debug: `com.monai.budget.budget_mobile.debug` (sideload without clobbering release)

## What not to commit

- `keystore.properties`, `keystore/*.jks`, `mobile/budget_mobile/android/key.properties`
- `*.aab`, `*.apk`, `dist/`
- `local.properties`
