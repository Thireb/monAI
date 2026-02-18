# PWA Installation Guide

This guide explains how to install the monAI Budget Tracker as a Progressive Web App (PWA) on various devices and browsers.

**Note:** The app uses the minimal theme by default. When installed, it will open at `/minimal/` and all navigation stays within the minimal theme routes.

## Prerequisites

1. **Generate Icon Files** (First Time Only)

   Before installing, you need to generate the PNG icon files from the SVG logos:

   ```bash
   # Install dependencies (choose one method)
   pip install cairosvg
   # OR
   pip install svglib reportlab

   # Generate all required icon files
   python scripts/generate_pwa_icons.py
   ```

   This will create the following files in `budgetapp/static/material/favicon/`:
   - `android-chrome-192x192.png`
   - `android-chrome-512x512.png`
   - `apple-touch-icon.png`
   - `favicon-32x32.png`
   - `favicon-16x16.png`

2. **HTTPS Required** (Production Only)

   - PWA requires HTTPS in production environments
   - Localhost (127.0.0.1) works without HTTPS for development
   - For production, ensure your Django app is served over HTTPS

## Installation Methods

### Desktop Browsers

#### Chrome / Edge (Windows, macOS, Linux)

1. **Open the app** in Chrome or Edge browser at `http://localhost:8000/minimal/` (or your production URL)
2. **Look for the install icon** in the address bar (usually appears as a "+" or download icon)
3. **Click the install icon** or look for "Install" button in the address bar
4. **Click "Install"** in the popup dialog
5. The app will open in its own window at `/minimal/` without browser UI

**Alternative Method:**
- Click the three-dot menu (⋮) in the browser
- Select "Install monAI - Budget Tracker" or "Install app"
- Confirm installation

#### Firefox (Windows, macOS, Linux)

1. **Open the app** in Firefox
2. Click the **three-line menu** (☰)
3. Look for **"Install Site as App"** or **"Install"** option
4. Click to install
5. The app will appear in your applications menu

#### Safari (macOS)

1. **Open the app** in Safari
2. Click **File** → **Add to Dock**
3. The app icon will appear in your Dock
4. Click the icon to launch the app in standalone mode

### Mobile Devices

#### Android (Chrome)

1. **Open the app** in Chrome browser on your Android device at `/minimal/`
2. **Tap the menu** (three dots) in the top right
3. Select **"Add to Home screen"** or **"Install app"**
4. **Customize the name** if desired (default: "monAI")
5. **Tap "Add"** or **"Install"**
6. The app icon will appear on your home screen
7. Tap the icon to launch the app in fullscreen mode at `/minimal/`

**Alternative Method:**
- A banner may appear at the bottom saying "Add monAI to Home screen"
- Tap "Add" on the banner

#### iOS (Safari)

1. **Open the app** in Safari on your iPhone/iPad at `/minimal/`
2. **Tap the Share button** (square with arrow pointing up)
3. Scroll down and tap **"Add to Home Screen"**
4. **Customize the name** if desired (default: "monAI")
5. **Tap "Add"** in the top right
6. The app icon will appear on your home screen
7. Tap the icon to launch the app in standalone mode at `/minimal/`

**Note:** iOS requires the app to be added to home screen manually - there's no automatic install prompt.

## Verifying Installation

### Check Service Worker

1. Open the installed app
2. Open browser DevTools (F12)
3. Go to **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Click **Service Workers** in the left sidebar
5. You should see the service worker registered and running

### Check Manifest

1. In DevTools, go to **Application** tab
2. Click **Manifest** in the left sidebar
3. You should see:
   - Name: "monAI - Budget Tracker"
   - Short name: "monAI"
   - Icons: 192x192 and 512x512 icons
   - Display: standalone

### Test Offline Functionality

1. Install the app
2. Open the installed app
3. Open DevTools → **Network** tab
4. Check **"Offline"** checkbox
5. Refresh the page
6. The app should still load from cache (basic pages and static assets)

## Troubleshooting

### Install Button Not Appearing

**Possible causes:**
1. **Icons missing**: Run `python scripts/generate_pwa_icons.py` to generate icons
2. **Not HTTPS**: PWA requires HTTPS in production (localhost is OK)
3. **Service worker not registered**: Check browser console for errors
4. **Manifest errors**: Check DevTools → Application → Manifest for validation errors

### Service Worker Not Registering

1. Open DevTools → **Console** tab
2. Look for errors starting with `[PWA]` or `[Service Worker]`
3. Check that `/service-worker.js` is accessible (visit the URL directly)
4. Verify the service worker file exists in `budgetapp/static/js/service-worker.js`

### Icons Not Showing

1. Verify PNG files exist in `budgetapp/static/material/favicon/`
2. Check file permissions (should be readable)
3. Clear browser cache and try again
4. Verify manifest icon paths are correct

### App Not Working Offline

- Service worker caches static assets and basic pages
- API calls always require network connection
- Some dynamic content may not work offline
- This is expected behavior for a basic PWA implementation

## Uninstalling

### Desktop

**Windows:**
- Settings → Apps → Find "monAI - Budget Tracker" → Uninstall

**macOS:**
- Remove from Applications folder or use Launchpad

**Linux:**
- Remove from applications menu or delete desktop entry

### Mobile

**Android:**
- Long press app icon → Uninstall or Remove

**iOS:**
- Long press app icon → Remove App → Delete App

## Features

Once installed, the PWA provides:

✅ **Standalone App Experience**: Runs in its own window without browser UI
✅ **Home Screen Icon**: Quick access from device home screen
✅ **Offline Support**: Basic pages and assets work offline
✅ **Fast Loading**: Cached assets load instantly
✅ **App-like Feel**: Fullscreen experience on mobile devices

## Development Notes

- Service worker updates automatically when new version is deployed
- Cache version is managed in `service-worker.js` (CACHE_VERSION)
- Manifest is located at `/static/material/favicon/site.webmanifest`
- Service worker is served from `/service-worker.js`

## Support

For issues or questions:
1. Check browser console for errors
2. Verify all files are in place (icons, manifest, service worker)
3. Test in different browsers to isolate issues
4. Ensure HTTPS is enabled in production
