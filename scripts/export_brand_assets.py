"""Export Home Assistant brand images from the shared Puzzary SVG master."""
from __future__ import annotations

import base64
from pathlib import Path

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "branding" / "puzzary-mark.svg"
OUTPUT = ROOT / "custom_components" / "puzzary" / "brand"
SIZES = {"icon.png": 256, "icon@2x.png": 512}


def main() -> None:
    svg = MASTER.read_text(encoding="utf-8")
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        for filename, size in SIZES.items():
            page.set_viewport_size({"width": size, "height": size})
            page.set_content(
                '<style>html,body{margin:0;width:100%;height:100%;overflow:hidden}</style>'
                f'<img alt="" src="data:image/svg+xml;base64,{encoded}" '
                'style="display:block;width:100%;height:100%">'
            )
            page.locator("img").screenshot(path=str(OUTPUT / filename), omit_background=True)
        browser.close()
    print("Exported Puzzary Home Assistant brand images.")


if __name__ == "__main__":
    main()
