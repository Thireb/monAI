# monAI Budget (Flutter)

Offline-first companion for the Django budget app. Sync runs over HTTP when your home server is reachable.

## Django (server)

1. Create or activate a venv and install deps (`requirements.txt`).
2. Apply migrations (`authtoken`, and `Category.updated_at` for incremental category sync):

   ```bash
   python manage.py migrate
   ```

3. Bind to the LAN so the phone can connect:

   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

4. Enter your PC LAN URL in the app (e.g. `http://192.168.1.10:8000`) under **Settings**, then **Save URL & sign in**.

## Mobile API

All authenticated routes use header: `Authorization: Token <token>`  
Token from: `POST /api/mobile/auth/token/` with JSON `{"email","password"}`.

| Method | Path | Body / query |
|--------|------|----------------|
| GET | `/api/health/` | none |
| POST | `/api/mobile/auth/token/` | `email`, `password` |
| GET | `/api/mobile/categories/pull/` | optional `updated_after` |
| POST | `/api/mobile/categories/push/` | `{ "categories": [ … ] }` |
| GET | `/api/mobile/tags/pull/` | optional `updated_after` |
| POST | `/api/mobile/tags/push/` | `{ "tags": [ … ] }` |
| GET | `/api/mobile/budgets/pull/` | optional `updated_after` |
| POST | `/api/mobile/budgets/push/` | `{ "budgets": [ … ] }` |
| GET | `/api/mobile/expenses/pull/` | optional `updated_after` |
| POST | `/api/mobile/expenses/push/` | `{ "expenses": [ … ] }` |
| GET | `/api/mobile/sub-expenses/pull/` | optional `updated_after` |
| POST | `/api/mobile/sub-expenses/push/` | `{ "sub_expenses": [ … ] }` |

Push responses include `server_ids` in the **same order** as the request list.

**Sync order (app):** push categories → tags → budgets → expenses → sub-expenses, then pull the same.

## Download APK (GitHub Actions — no local Flutter)

When this workflow is on your default branch, each qualifying push builds an APK. You can also run it manually.

1. Open the repo on GitHub → **Actions**.
2. Select **Build Android APK**.
3. Open the latest successful run.
4. Scroll to **Artifacts** → download **`monai-budget-release-apk`** (zip contains `app-release.apk`).

**Manual run:** Actions → **Build Android APK** → **Run workflow**.

Retention follows your org/repo artifact settings (often ~90 days).

### "App not installed" / conflicting package (signature)

Android only **updates over an existing install** if the **new APK is signed with the same certificate** as the one already on the phone.

Until you set **one release keystore** for both local builds and CI, this often happens:

| **`flutter build apk`** / **`flutter run`** on your PC | APK from **GitHub Actions** | **Fails** — different keys |
| Older **GitHub Actions** APK | New **Actions** APK **without** upload keystore in CI | **Often fails** — runner debug keystores usually **differ per job** |
| APK signed with **your** upload keystore | Next APK with the **same** keystore (local or CI with secrets) | **Works** |

**Quick fix:** uninstall **monAI Budget**, then install the new APK (you **lose local unsynced data** unless it was synced to the server first).

**Quick fix:** uninstall **monAI Budget**, then install the new APK (you **lose local unsynced data** unless it was synced to the server first).

**Proper fix (recommended):** create an **upload keystore**, use it for every release build:

1. Copy `android/key.properties.example` to `android/key.properties` and set passwords and alias.
2. Put your `.jks` under `android/app/` (path in `storeFile` is relative to `android/app/`).
3. Run `flutter build apk --release` locally — installs from this APK can be updated by **the next** APK signed with the **same** keystore.
4. Optional **Git add** `ANDROID_UPLOAD_KEYSTORE_BASE64` and related secrets in GitHub so Actions builds with the same key (workflow file documents the secret names).

Without `key.properties`, `release` still uses **debug** signing so **local PC** and **GitHub runner** produce **different** signatures — updates across those sources will keep failing.

## Garuda Linux: install Flutter and build APK

Garuda is Arch-based. Use either **AUR** or the **official Flutter tarball** (below uses the tarball so versions match easily).

1. **Dependencies** (Arch / Garuda):

   ```bash
   sudo pacman -S --needed base-devel git curl unzip jdk17-openjdk xz ninja cmake clang
   ```

2. **Android command-line tools** (pick one):

   - Install **Android Studio** from AUR or Flatpak, open it once, and let it install the SDK; OR  
   - Download “Command line tools only” from  
     https://developer.android.com/studio#command-line-tools-only  
     Unzip into e.g. `~/Android/Sdk/cmdline-tools/latest/` (see  
     https://developer.android.com/studio/command-line for layout).

3. **Environment** (add to `~/.bashrc` or `~/.config/fish/config.fish`):

   ```bash
   export ANDROID_HOME="$HOME/Android/Sdk"
   export JAVA_HOME="/usr/lib/jvm/java-17-openjdk"
   export PATH="$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools"
   ```

   Accept licenses and install API 34:

   ```bash
   yes | sdkmanager --sdk_root="$ANDROID_HOME" --licenses
   yes | sdkmanager --sdk_root="$ANDROID_HOME" "platform-tools" "platforms;android-34" "build-tools;34.0.0"
   ```

4. **Flutter**:

   ```bash
   git clone https://github.com/flutter/flutter.git -b stable ~/flutter
   export PATH="$HOME/flutter/bin:$PATH"
   flutter doctor
   ```

5. **Build release APK** (from repo root):

   ```bash
   cd mobile/budget_mobile
   flutter pub get
   flutter build apk --release
   ```

   Output: `build/app/outputs/flutter-apk/app-release.apk`

   Release signing uses `android/key.properties` when present; see **Conflicting package** above  
   and `android/key.properties.example`.

## Tests

- Django: `python manage.py test budgetapp.tests.test_mobile_sync`
- Flutter: `flutter test` (widget test uses stubs; no device SDK required)
