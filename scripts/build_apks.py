#!/usr/bin/env python3
"""
Build both localhost and ngrok APKs in one command.

Usage:
    python scripts/build_apks.py           # Build both APKs
    python scripts/build_apks.py --local   # Build only localhost APK
    python scripts/build_apks.py --ngrok   # Build only ngrok APK

Output:
    capacitor-app/output/monai-local.apk
    capacitor-app/output/monai-ngrok.apk
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
CAPACITOR_DIR = PROJECT_ROOT / "capacitor-app"
WWW_DIR = CAPACITOR_DIR / "www"
OUTPUT_DIR = CAPACITOR_DIR / "output"
ANDROID_DIR = CAPACITOR_DIR / "android"
APK_SOURCE = ANDROID_DIR / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
INDEX_HTML = WWW_DIR / "index.html"
CONFIG_FILE = PROJECT_ROOT / "config.yaml"


def load_config():
    """Load configuration from config.yaml."""
    if not CONFIG_FILE.exists():
        print(f"❌ Error: {CONFIG_FILE} not found.")
        print("   Please create config.yaml from the template.")
        sys.exit(1)

    with open(CONFIG_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def update_index_html(server_url):
    """Update index.html with the server URL."""
    if not INDEX_HTML.exists():
        print(f"❌ Error: {INDEX_HTML} not found.")
        sys.exit(1)

    content = INDEX_HTML.read_text(encoding="utf-8")

    # Replace the placeholder or existing URL in the iframe src
    import re

    # Match iframe src attribute
    new_content = re.sub(
        r'(<iframe[^>]*\s+src=")[^"]*(")',
        rf'\1{server_url}\2',
        content
    )

    INDEX_HTML.write_text(new_content, encoding="utf-8")
    print(f"   ✅ Updated index.html with URL: {server_url}")


def run_command(cmd, cwd=None, check=True):
    """Run a shell command."""
    print(f"   Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if check and result.returncode != 0:
        print(f"   ❌ Command failed: {result.stderr}")
        sys.exit(1)
    return result


def sync_capacitor():
    """Run capacitor sync."""
    print("   📱 Syncing Capacitor...")
    run_command(["npx", "cap", "sync", "android"], cwd=CAPACITOR_DIR)
    print("   ✅ Capacitor synced")


def build_android_apk():
    """Build the Android APK using Gradle."""
    print("   🔨 Building Android APK...")

    # Check if gradlew exists and is executable
    gradlew = ANDROID_DIR / "gradlew"
    if not gradlew.exists():
        print(f"   ❌ Error: {gradlew} not found.")
        print("   Run 'npx cap add android' first.")
        sys.exit(1)

    # Make gradlew executable on Unix systems
    if os.name != "nt":
        os.chmod(gradlew, 0o755)

    # Build the APK
    gradlew_cmd = str(gradlew) if os.name != "nt" else "gradlew.bat"
    run_command([gradlew_cmd, "assembleDebug"], cwd=ANDROID_DIR)
    print("   ✅ APK built successfully")


def copy_apk(variant_name):
    """Copy the built APK to the output directory with the variant name."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if not APK_SOURCE.exists():
        print(f"   ❌ Error: APK not found at {APK_SOURCE}")
        sys.exit(1)

    output_apk = OUTPUT_DIR / f"monai-{variant_name}.apk"
    shutil.copy2(APK_SOURCE, output_apk)
    print(f"   ✅ Copied to: {output_apk}")

    return output_apk


def build_variant(variant_name, server_url):
    """Build a single APK variant."""
    print(f"\n{'='*60}")
    print(f"📦 Building {variant_name.upper()} variant")
    print(f"   URL: {server_url}")
    print(f"{'='*60}")

    if not server_url:
        print(f"   ⚠️  Skipping {variant_name}: URL not configured in config.yaml")
        return None

    # Update index.html with the server URL
    update_index_html(server_url)

    # Sync Capacitor
    sync_capacitor()

    # Build APK
    build_android_apk()

    # Copy APK to output
    apk_path = copy_apk(variant_name)

    return apk_path


def main():
    parser = argparse.ArgumentParser(
        description="Build monAI APKs for different server configurations"
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Build only the localhost APK"
    )
    parser.add_argument(
        "--ngrok",
        action="store_true",
        help="Build only the ngrok APK"
    )

    args = parser.parse_args()

    # If no specific variant is specified, build both
    build_local = args.local or (not args.local and not args.ngrok)
    build_ngrok = args.ngrok or (not args.local and not args.ngrok)

    print("\n🚀 monAI APK Builder")
    print("=" * 60)

    # Load configuration
    config = load_config()
    urls = config.get("urls", {})
    local_url = urls.get("local", "")
    ngrok_url = urls.get("ngrok", "")

    print(f"\n📋 Configuration loaded from: {CONFIG_FILE}")
    print(f"   Local URL: {local_url or '(not set)'}")
    print(f"   Ngrok URL: {ngrok_url or '(not set)'}")

    built_apks = []

    # Build variants
    if build_local and local_url:
        apk = build_variant("local", local_url)
        if apk:
            built_apks.append(apk)

    if build_ngrok and ngrok_url:
        apk = build_variant("ngrok", ngrok_url)
        if apk:
            built_apks.append(apk)

    # Summary
    print("\n" + "=" * 60)
    print("✅ BUILD COMPLETE")
    print("=" * 60)

    if built_apks:
        print("\n📱 Generated APKs:")
        for apk in built_apks:
            size_mb = apk.stat().st_size / (1024 * 1024)
            print(f"   • {apk.name} ({size_mb:.1f} MB)")
        print(f"\n📂 Output directory: {OUTPUT_DIR}")
    else:
        print("\n⚠️  No APKs were built. Check your config.yaml URLs.")

    print()


if __name__ == "__main__":
    main()

