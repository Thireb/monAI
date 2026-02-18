# PWA Icons Required

The following icon files are required for full PWA functionality:

## Required Icons

1. **android-chrome-192x192.png** - 192x192 pixels PNG
   - Used for Android home screen icons
   - Required for PWA installation

2. **android-chrome-512x512.png** - 512x512 pixels PNG
   - Used for Android splash screens and high-res icons
   - Required for PWA installation

3. **apple-touch-icon.png** - 180x180 pixels PNG
   - Used for iOS home screen icons
   - Referenced in base templates

4. **favicon-32x32.png** - 32x32 pixels PNG
   - Standard favicon size
   - Referenced in base templates

5. **favicon-16x16.png** - 16x16 pixels PNG
   - Small favicon size
   - Referenced in base templates

6. **favicon.ico** - Multi-size ICO file
   - Traditional favicon format
   - Referenced in base templates

## Current Status

- ✅ icon.svg exists (can be used as source for generating PNGs)
- ❌ All PNG/ICO files need to be generated

## Generation Instructions

You can generate these icons from the existing `icon.svg` file using:

1. **Online tools**: Use services like https://realfavicongenerator.net/ or https://www.pwabuilder.com/imageGenerator
2. **Command line**: Use ImageMagick or similar tools to convert SVG to PNG at required sizes
3. **Design tools**: Use Figma, Adobe Illustrator, or similar to export PNGs at required sizes

## Note

The PWA will still function without these icons, but:
- Installation prompts may not show proper icons
- Home screen icons may appear generic
- Some browsers may not recognize the app as installable
