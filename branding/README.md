# Puzzary integration branding

`puzzary-mark.svg` is the same editable master used by Puzzary core. Its
maze-like **P**, start circle, and finish diamond identify Puzzary without using
Home Assistant artwork or any third-party trademark.

Palette:

- Evergreen: `#0d3b36`
- Warm white: `#f7f3e8`
- Mint: `#63d5c3`

Regenerate the shipped integration images from the repository root:

```console
python -m pip install playwright
python -m playwright install chromium
python scripts/export_brand_assets.py
```

The output follows Home Assistant's local custom-integration brand convention:
`icon.png` is 256×256 and `icon@2x.png` is 512×512 under
`custom_components/puzzary/brand/`. The contained evergreen field has sufficient
contrast on light and dark Home Assistant surfaces, so separate dark variants
would be identical and are intentionally omitted. Home Assistant uses the square
icon as the logo fallback; a duplicate wordmark is unnecessary.

This integration has no standalone web interface, so it intentionally ships no
favicon, touch icon, or web manifest. The artwork is licensed with this project
under Apache-2.0.
