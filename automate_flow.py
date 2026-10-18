"""
Flow AI Automation Script for Brave Browser via Playwright CDP
=============================================================
Connects to Brave running on port 9222, navigates to Google Flow AI,
and configures the 3-scene video promo generation.
"""

import asyncio
import os
import sys
import json
import argparse
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FLOW_URL = "https://flow.google.com/?pli=1&authuser=5"

KEYFRAMES_DIR = Path(__file__).resolve().parent / "keyframes"
FRAME_1 = str(KEYFRAMES_DIR / "soft_yellow_striped_blouse_frame1_front.jpg")
FRAME_2 = str(KEYFRAMES_DIR / "soft_yellow_striped_blouse_frame2_side.jpg")
FRAME_3 = str(KEYFRAMES_DIR / "soft_yellow_striped_blouse_frame3_shoulder.jpg")

DEFAULT_SCENES = [
    {
        "index": 1,
        "name": "Scene 1 (Front to Side)",
        "start_frame": FRAME_1,
        "end_frame": FRAME_2,
        "prompt": (
            'A smooth front-facing medium camera shot transitioning gracefully into a three-quarter side profile '
            'of the Malaysian Muslim woman wearing the soft butter yellow striped blouse and cream trousers in the sunlit courtyard. '
            'Natural motion, empty hands resting at sides. For the audio, generate a highly realistic female voice with a standard '
            'Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Explicitly translate the following '
            'English text into standard Malaysian Malay for the spoken audio: "When you get a wedding invitation with a yellow theme, '
            'many worry about looking dull or washed out, right? Look at this striped blouse in soft butter yellow: this gentle pastel '
            'yellow instantly brightens your skin tone, and the modest three-quarter puff sleeves look so graceful and flattering!" '
            'Ensure there are no text overlays or watermarks.'
        )
    },
    {
        "index": 2,
        "name": "Scene 2 (Side to Shoulder)",
        "start_frame": FRAME_2,
        "end_frame": FRAME_3,
        "prompt": (
            'A smooth camera glide continuing from the three-quarter side profile into an over-the-shoulder view '
            'of the Malaysian Muslim woman in the courtyard, showcasing the breezy fabric drape, 3/4 lantern sleeves, and back yoke '
            'with empty hands resting low at sides. For the audio, generate a highly realistic female voice with a standard Malaysian '
            'Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Explicitly translate the following English text '
            'into standard Malaysian Malay for the spoken audio: "The lightweight material feels so breezy and cooling under the hot '
            'Malaysian sun without clinging to your body. Plus, the vertical pinstripes and gathered lantern sleeves give such an '
            'effortless slimming silhouette for any body shape from size S to plus size!" Ensure there are no text overlays or watermarks.'
        )
    },
    {
        "index": 3,
        "name": "Scene 3 (Shoulder to Front)",
        "start_frame": FRAME_3,
        "end_frame": FRAME_1,
        "prompt": (
            'A seamless circular camera motion transitioning from the over-the-shoulder angle as she turns back gracefully to face front '
            'towards the camera with a warm smile, returning cleanly to the front standing pose in the sunlit courtyard. Arms resting low '
            'with empty hands. For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) '
            'accent—strictly NOT an Indonesian accent. Explicitly translate the following English text into standard Malaysian Malay for '
            'the spoken audio: "Whether you wear it to a wedding, for office meetings, or casual weekend outings, it matches effortlessly '
            'with pants or skirts. Click the yellow basket down below right now to grab your size before popular stocks run out!" '
            'Ensure there are no text overlays or watermarks.'
        )
    }
]


async def connect_to_brave(port: int = 9222):
    """Attempt connection to Brave CDP."""
    p = await async_playwright().start()
    try:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=5000)
        return p, browser
    except Exception as err:
        await p.stop()
        raise RuntimeError(f"Could not connect to Brave on port {port}: {err}")


async def find_or_open_flow_tab(browser):
    """Find existing Flow AI tab or open a new one."""
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    for page in context.pages:
        if "flow.google.com" in page.url or "labs.google" in page.url:
            await page.bring_to_front()
            return page

    # Open new page if none exists
    page = await context.new_page()
    await page.goto(FLOW_URL, wait_until="networkidle")
    return page


async def inspect_flow_page(scenes=None):
    """Inspect current Flow AI page structure to identify UI controls and verify session."""
    p, browser = await connect_to_brave()
    page = await find_or_open_flow_tab(browser)
    print("Active page title:", await page.title())
    print("Active page URL:", page.url)

    screenshot_path = Path(__file__).resolve().parent / "flow_tab_preview.png"
    await page.screenshot(path=str(screenshot_path))
    print(f"Captured screenshot to: {screenshot_path}")

    active_scenes = scenes or DEFAULT_SCENES
    print(f"Loaded {len(active_scenes)} scenes for Flow AI generation.")
    for sc in active_scenes:
        print(f"  - {sc.get('name')}: Start={Path(sc.get('start_frame','')).name}, End={Path(sc.get('end_frame','')).name}")

    return browser, page


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Flow AI via Brave CDP")
    parser.add_argument("--json", type=str, help="Path to product JSON or scenes file")
    args = parser.parse_args()

    custom_scenes = None
    if args.json:
        jp = Path(args.json)
        if jp.is_file():
            try:
                data = json.loads(jp.read_text(encoding="utf-8"))
                if "scenes" in data and isinstance(data["scenes"], list):
                    custom_scenes = data["scenes"]
            except Exception as ej:
                print(f"Notice reading scenes JSON: {ej}")

    try:
        asyncio.run(inspect_flow_page(scenes=custom_scenes))
    except Exception as e:
        print("Inspection error:", e)
