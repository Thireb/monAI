#!/usr/bin/env python3
"""
Generate PWA icon files from SVG sources.

This script converts SVG logo files to the required PNG sizes for PWA icons.
Requires: cairosvg or svglib + reportlab

Install dependencies:
    pip install cairosvg
    # OR
    pip install svglib reportlab

Usage:
    python scripts/generate_pwa_icons.py
"""
# flake8: noqa: E601
import sys
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Try cairosvg first (preferred)
try:
    import cairosvg

    USE_CAIROSVG = True
except ImportError:
    USE_CAIROSVG = False
    try:
        from reportlab.graphics import renderPM
        from svglib.svglib import svg2rlg

        USE_SVGLIB = True
    except ImportError:
        USE_SVGLIB = False
        print("Error: No SVG conversion library found.")
        print("Please install one of:")
        print("  pip install cairosvg")
        print("  pip install svglib reportlab")
        sys.exit(1)

# Icon sizes required for PWA
ICON_SIZES = [
    (192, 192, "android-chrome-192x192.png"),
    (512, 512, "android-chrome-512x512.png"),
    (180, 180, "apple-touch-icon.png"),
    (32, 32, "favicon-32x32.png"),
    (16, 16, "favicon-16x16.png"),
]

# Source SVG files
SVG_SOURCES = {
    "monai-icon.svg": "android-chrome-192x192.png",  # noqa: E601 # Use icon version for Android
    "monai-icon.svg": "android-chrome-512x512.png",  # noqa: E601
    "monai-icon.svg": "apple-touch-icon.png",  # noqa: E601
    "monai-logo-simple.svg": "favicon-32x32.png",  # noqa: E601 # Use simple version for small favicons
    "monai-logo-simple.svg": "favicon-16x16.png",  # noqa: E601
}


def convert_svg_to_png(svg_path, png_path, width, height):
    """Convert SVG to PNG at specified size."""
    if USE_CAIROSVG:
        cairosvg.svg2png(
            url=str(svg_path), write_to=str(png_path), output_width=width, output_height=height
        )
    elif USE_SVGLIB:
        drawing = svg2rlg(str(svg_path))
        if drawing:
            drawing.width = width
            drawing.height = height
            drawing.scale(width / drawing.width, height / drawing.height)
            renderPM.drawToFile(drawing, str(png_path), fmt="PNG")
        else:
            raise ValueError(f"Could not parse SVG: {svg_path}")


def generate_icons():
    """Generate all required PWA icon files."""
    favicon_dir = BASE_DIR / "budgetapp" / "static" / "material" / "favicon"

    if not favicon_dir.exists():
        print(f"Error: Favicon directory not found: {favicon_dir}")
        return False

    # Source mapping for different sizes
    source_mapping = {
        (192, 192): "monai-icon.svg",
        (512, 512): "monai-icon.svg",
        (180, 180): "monai-icon.svg",
        (32, 32): "monai-logo-simple.svg",
        (16, 16): "monai-logo-simple.svg",
    }

    success_count = 0
    error_count = 0

    for width, height, filename in ICON_SIZES:
        source_svg = source_mapping.get((width, height), "monai-icon.svg")
        svg_path = favicon_dir / source_svg
        png_path = favicon_dir / filename

        if not svg_path.exists():
            print(f"Warning: Source SVG not found: {svg_path}")
            error_count += 1
            continue

        try:
            print(f"Generating {filename} ({width}x{height}) from {source_svg}...")
            convert_svg_to_png(svg_path, png_path, width, height)
            print(f"  ✓ Created {png_path}")
            success_count += 1
        except Exception as e:
            print(f"  ✗ Error creating {filename}: {e}")
            error_count += 1

    print(f"\nSummary: {success_count} icons created, {error_count} errors")
    return error_count == 0


if __name__ == "__main__":
    print("Generating PWA icons from SVG sources...")
    print("=" * 50)

    if generate_icons():
        print("\n✓ All icons generated successfully!")
        print("\nNext steps:")
        print("1. Verify icons in: budgetapp/static/material/favicon/")
        print("2. Test PWA installation in browser")
        print("3. Icons should now appear when installing the app")
    else:
        print("\n✗ Some icons failed to generate. Please check errors above.")
        sys.exit(1)
