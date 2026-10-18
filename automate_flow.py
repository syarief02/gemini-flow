"""
Flow AI Automation Script for Brave Browser via Playwright CDP
=============================================================
Connects to Brave running on port 9222 with remote debugging,
navigates to Google Flow AI, sets up Frame-to-Video parameters,
uploads/selects keyframes, inputs prompts, and triggers 10s portrait renders.

Usage:
    python automate_flow.py --latest
    python automate_flow.py --scene 1
    python automate_flow.py --prompt "..." --start-frame path/to/frame1.jpg --end-frame path/to/frame2.jpg
"""

from __future__ import annotations

import asyncio
import os
import sys
import json
import re
import argparse
from pathlib import Path
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

FLOW_URL = "https://flow.google.com/?pli=1&authuser=5"
KEYFRAMES_DIR = Path(__file__).resolve().parent / "keyframes"


def get_latest_generation_data() -> dict:
    """Fetch the latest generation record from Supabase or generation_history.json."""
    try:
        from supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            res = client.table("gemini_flow_generations").select("*").order("created_at", desc=True).limit(1).execute()
            if res.data:
                row = res.data[0]
                return {
                    "product": row.get("product_name"),
                    "scenes": row.get("scenes") or {},
                    "keyframe_urls": row.get("keyframe_urls") or [],
                }
    except Exception as e:
        print(f"Notice querying Supabase for latest generation: {e}")

    try:
        hist_path = Path(__file__).resolve().parent / "generation_history.json"
        if hist_path.is_file():
            with open(hist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            gens = data.get("generations", [])
            if gens:
                last_g = gens[-1]
                return {
                    "product": last_g.get("product"),
                    "scenes": last_g.get("scenes") or {},
                    "opening_line": last_g.get("opening_line"),
                    "closing_line": last_g.get("closing_line")
                }
    except Exception as e_hist:
        print(f"Notice reading history: {e_hist}")

    return {}


def find_latest_keyframes() -> tuple[Path | None, Path | None, Path | None]:
    """Find the most recently generated trio of keyframe images in keyframes/."""
    if not KEYFRAMES_DIR.is_dir():
        return None, None, None

    f1_candidates = sorted(list(KEYFRAMES_DIR.glob("*frame1*.jpg")), key=os.path.getmtime, reverse=True)
    f2_candidates = sorted(list(KEYFRAMES_DIR.glob("*frame2*.jpg")), key=os.path.getmtime, reverse=True)
    f3_candidates = sorted(list(KEYFRAMES_DIR.glob("*frame3*.jpg")), key=os.path.getmtime, reverse=True)

    f1 = f1_candidates[0] if f1_candidates else None
    f2 = f2_candidates[0] if f2_candidates else None
    f3 = f3_candidates[0] if f3_candidates else None
    return f1, f2, f3


async def connect_to_brave(port: int = 9222):
    """Connect to Brave via Chrome DevTools Protocol."""
    p = await async_playwright().start()
    try:
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{port}", timeout=6000)
        return p, browser
    except Exception as err:
        await p.stop()
        raise RuntimeError(
            f"Could not connect to Brave CDP on port {port}: {err}\n"
            "Please ensure Brave is launched with: --remote-debugging-port=9222 --remote-allow-origins=*"
        )


async def get_or_create_flow_tab(browser):
    """Find existing Flow AI tab or navigate to Flow."""
    context = browser.contexts[0] if browser.contexts else await browser.new_context()
    for page in context.pages:
        if "flow.google.com" in page.url or "labs.google" in page.url:
            await page.bring_to_front()
            return page

    page = await context.new_page()
    await page.goto(FLOW_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    return page


async def ensure_active_flow_project(page):
    """Ensure the user is inside a Flow project canvas (not stuck on home list)."""
    # If on home / project list, click into the first project or new project
    if "/project/" not in page.url:
        print("Not inside a specific project. Checking for existing project cards or New button...")
        proj_link = page.locator("a[href*='/project/'], div[role='button']:has-text('New project'), button:has-text('New project')").first
        if await proj_link.is_visible(timeout=4000):
            await proj_link.click()
            await page.wait_for_timeout(3000)
        elif "/project/" not in page.url:
            # Try clicking top project item
            card = page.locator("div[role='gridcell'], div.project-card, flow-project-card").first
            if await card.is_visible(timeout=3000):
                await card.click()
                await page.wait_for_timeout(3000)

    print(f"Active Flow canvas URL: {page.url}")


async def configure_and_render_scene(
    page,
    scene_index: int,
    prompt: str,
    start_frame_path: str | Path | None = None,
    end_frame_path: str | Path | None = None,
    wait_after_submit: int = 6000
) -> bool:
    """
    Set Start and End frames in Flow composer, type prompt into ProseMirror,
    and trigger generation.
    """
    print(f"\n--- Initiating Flow AI Video Generation for Scene {scene_index} ---")
    await page.wait_for_timeout(2000)

    # 1. Attach / Select Start Frame
    if start_frame_path and Path(start_frame_path).is_file():
        start_btn = page.locator("button:has-text('Start')").first
        if await start_btn.is_visible(timeout=3000):
            print(f"Setting Start Frame: {Path(start_frame_path).name}")
            await start_btn.click()
            await page.wait_for_timeout(1500)

            # Check if upload button is needed or file chooser can be triggered
            upload_btn = page.locator("button:has-text('Upload media'), div:has-text('Upload media'), [aria-label*='Upload']").last
            if await upload_btn.is_visible(timeout=2000):
                try:
                    async with page.expect_file_chooser(timeout=3000) as fc_info:
                        await upload_btn.click()
                    fc = await fc_info.value
                    await fc.set_files(str(start_frame_path))
                    print(f"Uploaded Start Frame: {Path(start_frame_path).name}")
                    await page.wait_for_timeout(3500)
                except Exception as e_up:
                    print(f"Direct file chooser notice: {e_up}. Checking modal asset list...")
                    # Select from modal if already present
                    asset_item = page.locator("div[role='dialog'] img, div[aria-modal='true'] img, div[role='listbox'] img").first
                    if await asset_item.is_visible(timeout=2000):
                        await asset_item.click()
                        await page.wait_for_timeout(1000)

            # Close picker modal if open
            close_btn = page.locator("button[aria-label='Close'], button:has-text('Close')").first
            if await close_btn.is_visible(timeout=1500):
                await close_btn.click()
                await page.wait_for_timeout(1000)

    # 2. Attach / Select End Frame
    if end_frame_path and Path(end_frame_path).is_file():
        end_btn = page.locator("button:has-text('End')").first
        if await end_btn.is_visible(timeout=3000):
            print(f"Setting End Frame: {Path(end_frame_path).name}")
            await end_btn.click()
            await page.wait_for_timeout(1500)

            upload_btn = page.locator("button:has-text('Upload media'), div:has-text('Upload media'), [aria-label*='Upload']").last
            if await upload_btn.is_visible(timeout=2000):
                try:
                    async with page.expect_file_chooser(timeout=3000) as fc_info:
                        await upload_btn.click()
                    fc = await fc_info.value
                    await fc.set_files(str(end_frame_path))
                    print(f"Uploaded End Frame: {Path(end_frame_path).name}")
                    await page.wait_for_timeout(3500)
                except Exception as e_up:
                    print(f"Direct file chooser notice: {e_up}. Checking modal asset list...")
                    asset_item = page.locator("div[role='dialog'] img, div[aria-modal='true'] img, div[role='listbox'] img").nth(1)
                    if await asset_item.is_visible(timeout=2000):
                        await asset_item.click()
                        await page.wait_for_timeout(1000)

            close_btn = page.locator("button[aria-label='Close'], button:has-text('Close')").first
            if await close_btn.is_visible(timeout=1500):
                await close_btn.click()
                await page.wait_for_timeout(1000)

    # 3. Enter Scene Prompt into ProseMirror Editor
    editor = page.locator("div.ProseMirror[role='textbox'], div[contenteditable='true'][role='textbox']").first
    if not await editor.is_visible(timeout=3000):
        editor = page.locator("div[contenteditable='true'], textarea").last

    if await editor.is_visible(timeout=3000):
        print(f"Typing Scene {scene_index} prompt into Flow composer...")
        await editor.click()
        await page.wait_for_timeout(500)
        # Clear existing text
        await page.keyboard.press("Control+A")
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(300)
        # Insert prompt
        await page.keyboard.insert_text(prompt.strip())
        await page.wait_for_timeout(1500)
    else:
        print("ERROR: Could not locate Flow prompt editor.")
        return False

    # 4. Trigger Render
    generate_btn = page.locator("button[aria-label='Start generation'], button[aria-label*='generate'], button.send-btn").first
    is_disabled = await generate_btn.get_attribute("disabled") if await generate_btn.is_visible(timeout=2000) else True

    if not is_disabled or is_disabled == "false":
        print(f"Clicking 'Start generation' for Scene {scene_index}...")
        await generate_btn.click()
    else:
        print(f"Submitting via Enter key for Scene {scene_index}...")
        await page.keyboard.press("Enter")

    await page.wait_for_timeout(wait_after_submit)
    screenshot_p = Path(__file__).resolve().parent / "flow_renders_progress.png"
    await page.screenshot(path=str(screenshot_p))
    print(f"Captured render progress screenshot: {screenshot_p}")
    print(f"Scene {scene_index} generation successfully queued!")
    return True


async def run_flow_pipeline(
    scene_num: int = 1,
    prompt_override: str | None = None,
    start_frame_override: str | None = None,
    end_frame_override: str | None = None
):
    """Main pipeline execution entry point."""
    print("Connecting to Brave on port 9222...")
    p, browser = await connect_to_brave()
    try:
        page = await get_or_create_flow_tab(browser)
        await ensure_active_flow_project(page)

        # Determine frames and prompts
        f1, f2, f3 = find_latest_keyframes()
        gen_data = get_latest_generation_data()
        scenes = gen_data.get("scenes") or {}

        # Default prompts
        scene_prompts = {
            1: scenes.get("scene_1_intro") or (
                'A smooth front-facing medium camera shot transitioning gracefully into a three-quarter side profile '
                'of the Malaysian Muslim woman wearing the chic modest outfit in the sunlit courtyard. '
                'Natural motion, empty hands resting at sides. Clear natural Malaysian Malay voiceover lip-sync.'
            ),
            2: scenes.get("scene_2_detail") or (
                'A smooth camera glide continuing from three-quarter side profile into an over-the-shoulder view '
                'in the courtyard, showcasing the fabric drape and styling details with empty hands resting low at sides. '
                'Clear natural Malaysian Malay voiceover lip-sync.'
            ),
            3: scenes.get("scene_3_outro") or (
                'A seamless circular camera motion from the over-the-shoulder angle turning back gracefully to face front '
                'towards the camera with a warm smile. Empty hands resting low. Clear natural Malaysian Malay voiceover lip-sync.'
            )
        }

        # Frame pairings
        pairings = {
            1: (f1, f2),
            2: (f2, f3),
            3: (f3, f1)
        }

        start_f = Path(start_frame_override) if start_frame_override else pairings.get(scene_num, (f1, f2))[0]
        end_f = Path(end_frame_override) if end_frame_override else pairings.get(scene_num, (f1, f2))[1]
        active_prompt = prompt_override or scene_prompts.get(scene_num)

        success = await configure_and_render_scene(
            page=page,
            scene_index=scene_num,
            prompt=active_prompt,
            start_frame_path=start_f,
            end_frame_path=end_f
        )
        return success
    finally:
        # Never close the user's browser
        await p.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Flow AI 10s portrait video rendering in Brave")
    parser.add_argument("--scene", type=int, default=1, choices=[1, 2, 3], help="Scene number to render (1, 2, or 3)")
    parser.add_argument("--prompt", type=str, help="Custom scene prompt")
    parser.add_argument("--start-frame", type=str, help="Path to start frame image")
    parser.add_argument("--end-frame", type=str, help="Path to end frame image")
    parser.add_argument("--latest", action="store_true", help="Automatically pull latest keyframes and prompts")
    args = parser.parse_args()

    try:
        ok = asyncio.run(run_flow_pipeline(
            scene_num=args.scene,
            prompt_override=args.prompt,
            start_frame_override=args.start_frame,
            end_frame_override=args.end_frame
        ))
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print("Flow automation error:", exc)
        sys.exit(1)
