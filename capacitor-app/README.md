# monAI Android App (Capacitor)

This is a Capacitor wrapper that turns your Django budget tracker into an Android app.

## Setup

### 1. Configure Environment
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your URLs
nano .env
```

Set your URLs in `.env`:
- `LOCAL_SERVER_URL` - Your local IP (e.g., `http://192.168.1.16:8000/minimal/`)
- `NGROK_SERVER_URL` - Your ngrok URL (e.g., `https://xxx.ngrok-free.dev/minimal/`)
- `SERVER_MODE` - Which to use: `local` or `ngrok`

### 2. Configure and Sync
```bash
# Use local network URL
node configure.js local

# OR use ngrok URL (for external access)
node configure.js ngrok

# OR use whatever SERVER_MODE is set to in .env
node configure.js
```

## Building the APK

### Option A: Using Android Studio (Recommended)
```bash
npx cap open android
```
Then in Android Studio:
1. Wait for Gradle sync to complete
2. Build → Build Bundle(s) / APK(s) → Build APK(s)
3. APK will be at: `android/app/build/outputs/apk/debug/app-debug.apk`

### Option B: Command Line (Requires Android SDK)
```bash
cd android
./gradlew assembleDebug
```
APK location: `android/app/build/outputs/apk/debug/app-debug.apk`

## Installing on Your Phone

1. Copy the APK to your phone
2. Enable "Install from unknown sources" in Settings
3. Open the APK file to install

## Running Django Server

Make sure Django is accessible from your network:
```bash
cd /home/xraydisk/Programming/django_budget_tracker
python manage.py runserver 0.0.0.0:8000
```

## Updating the App

After changing the server URL or making updates:
```bash
npx cap sync android
# Then rebuild the APK
```

## Troubleshooting

### App shows blank screen
- Check Django server is running
- Verify the IP address is correct
- Ensure phone and computer are on same network

### Connection refused
- Make sure Django is bound to `0.0.0.0:8000` not `127.0.0.1:8000`
- Check firewall settings on your computer

### App icon
To customize the app icon, replace files in:
- `android/app/src/main/res/mipmap-*/ic_launcher.png`
- `android/app/src/main/res/mipmap-*/ic_launcher_round.png`
