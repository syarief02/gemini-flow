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

SUNO_URL = "https://suno.com/create"
BGM_PROMPT = (
    "Upbeat lo-fi indie acoustic cafe pop, featuring bright fingerpicked acoustic guitar, "
    "subtle warm Rhodes electric piano chords, crisp lo-fi drum groove, soft shaker, and round "
    "warm melodic bass. Sunny, breezy, modern Malaysian aesthetic lifestyle vibe, relaxing and "
    "optimistic tempo at 110 BPM. Pure instrumental, strictly no vocals, loopable high quality production."
)
BGM_TITLE = "Baju Kuning Guest Blouse - Soft Yellow Chill BGM"


def get_latest_bgm_info() -> tuple[str, str]:
    """Fetch latest generated BGM prompt and title from Supabase or generation history."""
    try:
        from supabase_client import get_supabase_client
        client = get_supabase_client()
        if client:
            res = client.table("gemini_flow_generations").select("product_name, bgm_prompt").order("created_at", desc=True).limit(1).execute()
            if res.data and res.data[0].get("bgm_prompt"):
                p_name = res.data[0].get("product_name", "Product Promo")
                prompt = res.data[0]["bgm_prompt"]
                title = f"{p_name[:35]} - BGM Instrumental"
                return prompt, title
    except Exception as e:
        print(f"Notice fetching latest BGM from Supabase: {e}")

    try:
        hist_path = Path(__file__).resolve().parent / "generation_history.json"
        if hist_path.is_file():
            with open(hist_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            gens = data.get("generations", [])
            if gens and gens[-1].get("bgm_prompt"):
                p_name = gens[-1].get("product", "Product Promo")
                return gens[-1]["bgm_prompt"], f"{p_name[:35]} - BGM Instrumental"
    except Exception as e_hist:
        print(f"Notice reading history: {e_hist}")

    return BGM_PROMPT, BGM_TITLE


async def setup_suno(prompt_text: str = None, title_text: str = None):
    if not prompt_text or not title_text:
        latest_prompt, latest_title = get_latest_bgm_info()
        target_prompt = (prompt_text or latest_prompt).strip()
        target_title = (title_text or latest_title).strip()
    else:
        target_prompt = prompt_text.strip()
        target_title = title_text.strip()

    print("Step 1: Connecting to Brave over CDP...")
    p = await async_playwright().start()
    browser = None
    try:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
        print("Connected to Brave!")
    except Exception as e:
        print(f"Connection failed: {e}")
        await p.stop()
        return False

    context = browser.contexts[0]
    suno_page = None
    for page in context.pages:
        if "suno.com" in page.url or "suno.ai" in page.url:
            suno_page = page
            print(f"Found existing Suno page: {page.url}")
            break

    if not suno_page:
        print("Opening new Suno tab...")
        suno_page = await context.new_page()
        await suno_page.goto(SUNO_URL, wait_until="domcontentloaded")
    else:
        await suno_page.bring_to_front()
        if "/create" not in suno_page.url:
            await suno_page.goto(SUNO_URL, wait_until="domcontentloaded")

    print("Waiting for Suno page to settle...")
    await suno_page.wait_for_timeout(5000)

    # Dismiss any cookie or popup if present
    for close_sel in [
        "button:has-text('Accept All')",
        "button:has-text('I Agree')",
        "button:has-text('Got it')",
        "button[aria-label='Close']",
        "button:has-text('Dismiss')"
    ]:
        try:
            btn = suno_page.locator(close_sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click()
                print(f"Dismissed popup via {close_sel}")
        except:
            pass

    # Save initial screenshot
    await suno_page.screenshot(path="suno_initial.png")
    print("Saved suno_initial.png")

    page_text = await suno_page.inner_text("body")
    print(f"Page text snippet: {page_text[:300].replace(chr(10), ' ')}")

    # Check if Custom mode switch exists
    custom_toggle = suno_page.locator("button[role='switch']:has-text('Custom'), div:has-text('Custom') button[role='switch'], button:has-text('Custom')").first
    try:
        if await custom_toggle.is_visible(timeout=2000):
            checked = await custom_toggle.get_attribute("aria-checked")
            if checked != "true":
                print("Enabling Custom mode...")
                await custom_toggle.click()
                await suno_page.wait_for_timeout(1500)
            print("Custom mode active!")
    except Exception as e:
        print(f"Custom toggle check notice: {e}")

    # Ensure Instrumental mode is ON
    instrumental_toggle = suno_page.locator(
        "button[role='switch']:has-text('Instrumental'), "
        "label:has-text('Instrumental') input[type='checkbox'], "
        "div:has-text('Instrumental') button[role='switch']"
    ).first
    try:
        if await instrumental_toggle.is_visible(timeout=2000):
            checked = await instrumental_toggle.get_attribute("aria-checked")
            if checked != "true":
                print("Toggling Instrumental mode ON...")
                await instrumental_toggle.click()
                await suno_page.wait_for_timeout(1000)
            print("Instrumental mode confirmed ON!")
    except Exception as e:
        print(f"Instrumental toggle notice: {e}")

    # Locate Style of Music or Song Description input
    style_input = suno_page.locator(
        "textarea[placeholder*='Style of Music'], "
        "textarea[placeholder*='style'], "
        "textarea[placeholder*='Song Description'], "
        "textarea[placeholder*='prompt'], "
        "textarea"
    ).first

    if await style_input.is_visible(timeout=3000):
        print("Found prompt textarea. Typing style prompt...")
        await style_input.click()
        await style_input.fill("")
        await style_input.fill(target_prompt)
        await suno_page.wait_for_timeout(1000)
    else:
        print("Could not find style textarea directly!")

    # Locate Title input if in custom mode
    title_input = suno_page.locator(
        "input[placeholder*='Title'], "
        "input[placeholder*='title'], "
        "input[aria-label*='Title']"
    ).first
    try:
        if await title_input.is_visible(timeout=1500):
            print("Found Title input. Entering title...")
            await title_input.click()
            await title_input.fill("")
            await title_input.fill(target_title)
            await suno_page.wait_for_timeout(1000)
    except Exception as e:
        print(f"Title input notice: {e}")

    # Capture configured state
    await suno_page.screenshot(path="suno_configured.png")
    print("Saved suno_configured.png")

    # Locate Create button
    create_btn = suno_page.locator(
        "button:has-text('Create'), "
        "button[aria-label='Create']"
    ).first

    if await create_btn.is_visible(timeout=3000):
        print("Clicking Create button to generate song...")
        await create_btn.click()
        await suno_page.wait_for_timeout(6000)
        await suno_page.screenshot(path="suno_generating.png")
        print("Saved suno_generating.png - Generation initiated!")
        return True
    else:
        print("Create button not visible or needs sign in. Screenshot captured.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Suno AI instrumental BGM generation via Brave CDP")
    parser.add_argument("--prompt", type=str, help="BGM style prompt")
    parser.add_argument("--title", type=str, help="Song title")
    parser.add_argument("--file", type=str, help="Path to JSON file containing BGM prompt")
    parser.add_argument("--latest", action="store_true", help="Fetch latest BGM prompt from Supabase / history")
    args = parser.parse_args()

    chosen_prompt = None
    chosen_title = None

    if args.prompt:
        chosen_prompt = args.prompt
        chosen_title = args.title or "TikTok Promo BGM"
    elif args.file:
        file_path = Path(args.file)
        if file_path.is_file():
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                chosen_prompt = data.get("suno_bgm", {}).get("style") or data.get("bgm_prompt")
                chosen_title = f"{data.get('title', 'Product')[:35]} - BGM"
            except Exception:
                chosen_prompt = file_path.read_text(encoding="utf-8")
    else:
        chosen_prompt, chosen_title = get_latest_bgm_info()

    if args.title and not chosen_title:
        chosen_title = args.title

    success = asyncio.run(setup_suno(prompt_text=chosen_prompt, title_text=chosen_title))
    sys.exit(0 if success else 1)
