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
                    "opening_line": row.get("opening_line"),
                    "closing_line": row.get("closing_line"),
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

    async def attach_frame_by_search_or_upload(slot_index: int, frame_path: str | Path | None, query_tag: str):
        if not frame_path:
            return
        p_obj = Path(frame_path)
        triggers = page.locator("div.frame-trigger")
        trigger_btn = triggers.nth(slot_index).locator("button").first
        if not await trigger_btn.is_visible(timeout=3000):
            trigger_btn = page.locator("button:has-text('Start'), button:has-text('End')").nth(slot_index)

        print(f"Opening frame slot {slot_index} for: {p_obj.name}...")
        await trigger_btn.click()
        await page.wait_for_timeout(1500)

        # 1. First check if searching for the file tag finds an already uploaded asset
        search_input = page.locator("flow-add-menu-popover-content input, input[placeholder*='Search']").first
        found_in_search = False
        if await search_input.is_visible(timeout=2000):
            await search_input.fill("")
            await search_input.fill(query_tag)
            await page.wait_for_timeout(1500)

            filtered_item = page.locator(
                "flow-add-menu-popover-content flow-asset-list-item, "
                "flow-add-menu-popover-content .asset-list-item, "
                "flow-add-menu-popover-content div.item-row, "
                "flow-add-menu-popover-content [role='listbox'] > *"
            ).first
            if await filtered_item.is_visible(timeout=2000):
                print(f"Found asset for '{query_tag}' via search. Selecting...")
                await filtered_item.click()
                await page.wait_for_timeout(1000)
                found_in_search = True

        # 2. If not found via search, upload the file
        if not found_in_search and p_obj.is_file():
            upload_btn = page.locator("button:has-text('Upload media'), div:has-text('Upload media'), [aria-label*='Upload']").last
            if await upload_btn.is_visible(timeout=2000):
                print(f"Uploading file: {p_obj.name}...")
                async with page.expect_file_chooser(timeout=4000) as fc_info:
                    await upload_btn.click()
                fc = await fc_info.value
                await fc.set_files(str(p_obj))
                await page.wait_for_timeout(3500)

        # 3. Click 'Add to prompt' button (MANDATORY TO ATTACH FRAME TO COMPOSER SLOT)
        add_btn = page.locator("button:has-text('Add to prompt')").first
        if await add_btn.is_visible(timeout=3000):
            print(f"Clicking 'Add to prompt' for slot {slot_index}...")
            await add_btn.click()
            await page.wait_for_timeout(2000)
        else:
            print(f"Warning: 'Add to prompt' button not visible for slot {slot_index}.")

    # Attach Start Frame (slot 0)
    query_start = "frame1_front" if scene_index == 1 else ("frame2_side" if scene_index == 2 else "frame3_shoulder")
    await attach_frame_by_search_or_upload(0, start_frame_path, query_start)

    # Attach End Frame (slot 1)
    query_end = "frame2_side" if scene_index == 1 else ("frame3_shoulder" if scene_index == 2 else "frame1_front")
    await attach_frame_by_search_or_upload(1, end_frame_path, query_end)

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


def format_flow_prompt_with_lipsync(visual_prompt: str, spoken_dialogue: str = None) -> str:
    """Ensure the prompt contains both visual directions and explicit Spoken Malay lip-sync block."""
    prompt = visual_prompt.strip()
    if "Spoken Malay (Lip-sync):" in prompt:
        return prompt

    if spoken_dialogue:
        clean_spoken = spoken_dialogue.strip().strip('"')
        return f'{prompt}\n\nSpoken Malay (Lip-sync): "{clean_spoken}"'

    # If dialogue not provided separately, attempt to extract quoted speech from prompt
    quotes = re.findall(r'"([^"]{15,})"', prompt)
    if quotes:
        extracted_dialogue = quotes[-1]
        return f'{prompt}\n\nSpoken Malay (Lip-sync): "{extracted_dialogue}"'

    return prompt


async def run_flow_pipeline(
    scene_num: int = 1,
    render_all: bool = False,
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

        def get_clean_scene_prompt(scene_idx: int, default_str: str) -> str:
            keys = {
                1: ["scene_1_intro", "scene_1", "1"],
                2: ["scene_2_detail", "scene_2", "2"],
                3: ["scene_3_outro", "scene_3", "3"]
            }.get(scene_idx, [])
            for k in keys:
                val = scenes.get(k)
                if isinstance(val, str) and len(val.strip()) > 30 and not re.match(r"^scene\s*\d+$", val.strip(), re.I):
                    return val.strip()
            return default_str

        # Default prompts
        raw_prompts = {
            1: get_clean_scene_prompt(
                1,
                'A smooth front-facing medium camera shot transitioning gracefully into a three-quarter side profile '
                'of the Malaysian Muslim woman wearing the chic modest outfit in the sunlit courtyard. '
                'Natural motion, empty hands resting at sides. For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Ensure there are no text overlays or watermarks.'
            ),
            2: get_clean_scene_prompt(
                2,
                'A smooth camera glide continuing from three-quarter side profile into an over-the-shoulder view '
                'in the courtyard, showcasing the fabric drape and styling details with empty hands resting low at sides. '
                'For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Ensure there are no text overlays or watermarks.'
            ),
            3: get_clean_scene_prompt(
                3,
                'A seamless circular camera motion from the over-the-shoulder angle turning back gracefully to face front '
                'towards the camera with a warm smile. Empty hands resting low. For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Ensure there are no text overlays or watermarks.'
            )
        }

        # Frame pairings: Scene 1: F1->F2 | Scene 2: F2->F3 | Scene 3: F3->F1
        pairings = {
            1: (f1, f2),
            2: (f2, f3),
            3: (f3, f1)
        }

        scenes_to_run = [1, 2, 3] if render_all else [scene_num]

        for s_idx in scenes_to_run:
            start_f = Path(start_frame_override) if (start_frame_override and not render_all) else pairings[s_idx][0]
            end_f = Path(end_frame_override) if (end_frame_override and not render_all) else pairings[s_idx][1]
            base_prompt = prompt_override if (prompt_override and not render_all) else raw_prompts.get(s_idx)

            fallback_spoken = {
                1: scenes.get("spoken_dialogue", {}).get("scene_1") or gen_data.get("opening_line"),
                2: scenes.get("spoken_dialogue", {}).get("scene_2"),
                3: scenes.get("spoken_dialogue", {}).get("scene_3") or gen_data.get("closing_line")
            }.get(s_idx)

            active_prompt = format_flow_prompt_with_lipsync(base_prompt, spoken_dialogue=fallback_spoken)

            success = await configure_and_render_scene(
                page=page,
                scene_index=s_idx,
                prompt=active_prompt,
                start_frame_path=start_f,
                end_frame_path=end_f,
                wait_after_submit=6000
            )
            if not success:
                print(f"Failed to queue Scene {s_idx}.")
                return False

            if render_all and s_idx < 3:
                print("Waiting 8 seconds before queuing next scene...")
                await asyncio.sleep(8)

        return True
    finally:
        # Never close the user's browser
        await p.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Flow AI 10s portrait video rendering in Brave")
    parser.add_argument("--scene", type=int, default=1, choices=[1, 2, 3], help="Scene number to render (1, 2, or 3)")
    parser.add_argument("--all", action="store_true", help="Queue all 3 scenes sequentially (Frame 1->2, 2->3, 3->1)")
    parser.add_argument("--prompt", type=str, help="Custom scene prompt")
    parser.add_argument("--start-frame", type=str, help="Path to start frame image")
    parser.add_argument("--end-frame", type=str, help="Path to end frame image")
    parser.add_argument("--latest", action="store_true", help="Automatically pull latest keyframes and prompts")
    args = parser.parse_args()

    try:
        ok = asyncio.run(run_flow_pipeline(
            scene_num=args.scene,
            render_all=args.all,
            prompt_override=args.prompt,
            start_frame_override=args.start_frame,
            end_frame_override=args.end_frame
        ))
        sys.exit(0 if ok else 1)
    except Exception as exc:
        print("Flow automation error:", exc)
        sys.exit(1)

