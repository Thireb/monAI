#!/usr/bin/env node
/**
 * Configure Capacitor with environment-based server URLs
 * The app will automatically try ngrok first, then fall back to local
 *
 * Usage: node configure.js
 */

const fs = require('fs');
const path = require('path');

// Load .env file
function loadEnv() {
  const envPath = path.join(__dirname, '.env');
  if (!fs.existsSync(envPath)) {
    console.error('Error: .env file not found. Copy .env.example to .env and configure it.');
    process.exit(1);
  }

  const env = {};
  const content = fs.readFileSync(envPath, 'utf8');
  content.split('\n').forEach(line => {
    const match = line.match(/^([^#=]+)=(.*)$/);
    if (match) {
      env[match[1].trim()] = match[2].trim();
    }
  });
  return env;
}

// Main
const env = loadEnv();

const localUrl = env.LOCAL_SERVER_URL || '';
const ngrokUrl = env.NGROK_SERVER_URL || '';

console.log('🔧 Configuring monAI Android App\n');
console.log('   URLs configured:');
if (ngrokUrl) console.log(`   🌐 Ngrok: ${ngrokUrl}`);
if (localUrl) console.log(`   🏠 Local: ${localUrl}`);
console.log('\n   App will try Ngrok first, then fall back to Local\n');

// Update www/index.html with URLs
const htmlPath = path.join(__dirname, 'www', 'index.html');
let html = fs.readFileSync(htmlPath, 'utf8');

// Replace placeholders or update existing URLs
html = html.replace(
  /const SERVERS = \[[\s\S]*?\]\.filter/,
  `const SERVERS = [
            { name: 'Ngrok', url: '${ngrokUrl}' },
            { name: 'Local', url: '${localUrl}' }
        ].filter`
);

fs.writeFileSync(htmlPath, html);
console.log('✅ Updated www/index.html with server URLs');

// Update capacitor.config.json (use local as default for cleartext)
const configPath = path.join(__dirname, 'capacitor.config.json');
const config = {
  appId: 'com.monai.budgettracker',
  appName: 'monAI',
  webDir: 'www',
  android: {
    allowMixedContent: true,
  },
};

fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log('✅ Updated capacitor.config.json');

// Sync with Android
console.log('📱 Syncing with Android...');
const { execSync } = require('child_process');
try {
  execSync('npx cap sync android', { cwd: __dirname, stdio: 'inherit' });
  console.log('✅ Android project synced');
  console.log('\n📦 Now rebuild APK:');
  console.log('   cd android && ./gradlew assembleDebug');
  console.log('\n📍 APK location:');
  console.log('   android/app/build/outputs/apk/debug/app-debug.apk');
} catch (e) {
  console.error('Failed to sync:', e.message);
}
