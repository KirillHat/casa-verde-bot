"""Render mockups.html into PNG screenshots via Playwright.

Each `.phone`, `.sheet`, or `.slack` element with an `id="screen-<name>"`
becomes `screenshots/<name>.png`.

Run:
    python screenshots/render.py
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
HTML = HERE / "mockups.html"

# Element id → output filename. The element is screenshotted in isolation,
# so the HTML page can host as many mockups as you want.
TARGETS: dict[str, str] = {
    "screen-whatsapp-es": "01_whatsapp_es.png",
    "screen-whatsapp-en": "02_whatsapp_en.png",
    "screen-sheet": "03_sheet.png",
    "screen-slack": "04_slack.png",
}


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = await context.new_page()
        await page.goto(HTML.as_uri(), wait_until="networkidle")

        for sel_id, fname in TARGETS.items():
            element = page.locator(f"#{sel_id}")
            out = HERE / fname
            await element.screenshot(path=str(out), omit_background=False)
            print(f"✓ {fname}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
