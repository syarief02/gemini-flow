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
    "Warm acoustic lo-fi indie cafe pop, breezy fingerpicked acoustic guitar, "
    "subtle Rhodes electric piano chords, smooth mellow bassline, light brushed drums, "
    "108 BPM, modern minimalist aesthetic lifestyle vibe, relaxing, sunny, chic, "
    "pure instrumental, strictly no vocals"
)
BGM_TITLE = "TikTok Product Promo - BGM Instrumental"


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
            for g in reversed(gens):
                if g.get("bgm_prompt"):
                    p_name = g.get("product", "Product Promo")
                    return g["bgm_prompt"], f"{p_name[:35]} - BGM Instrumental"
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
    await suno_page.wait_for_timeout(3000)

    # 1. Dismiss any non-critical cookie popups (do NOT click generic close button as that closes drawer)
    for close_sel in [
        "button:has-text('Accept All')",
        "button:has-text('I Agree')",
        "div:has-text('Create your own lyricist') button:has-text('Got it')",
        "button:has-text('Got it')",
    ]:
        try:
            btn = suno_page.locator(close_sel).first
            if await btn.is_visible(timeout=1000):
                await btn.click(force=True)
                print(f"Dismissed popup via {close_sel}")
        except:
            pass

    # 2. Check if drawer is closed (in responsive/mobile layout) and open it if needed
    adv_mode_btn = suno_page.locator("button:has-text('Advanced'), span:has-text('Advanced')").first
    custom_toggle = suno_page.locator("button[role='switch']:has-text('Custom'), div:has-text('Custom') button[role='switch']").first
    drawer_open = await adv_mode_btn.is_visible(timeout=1000) or await custom_toggle.is_visible(timeout=1000)

    if not drawer_open:
        print("Create drawer collapsed. Opening via bottom navigation...")
        create_nav = suno_page.locator("a[href='/create'][aria-label='Create'], a[aria-label='Create']").first
        if await create_nav.is_visible(timeout=2000):
            await create_nav.click(force=True)
            await suno_page.wait_for_timeout(2000)

    # 3. Ensure Advanced mode / Custom mode is active
    if await adv_mode_btn.is_visible(timeout=2000):
        print("Enabling Advanced mode...")
        await adv_mode_btn.click(force=True)
        await suno_page.wait_for_timeout(1000)
    elif await custom_toggle.is_visible(timeout=2000):
        checked = await custom_toggle.get_attribute("aria-checked")
        if checked != "true":
            print("Enabling Custom mode...")
            await custom_toggle.click(force=True)
            await suno_page.wait_for_timeout(1000)

    # 4. Instrumental Mode: Ensure Lyrics are EMPTY, or toggle Instrumental switch
    instrumental_toggle = suno_page.locator(
        "button[role='switch']:has-text('Instrumental'), "
        "label:has-text('Instrumental') input[type='checkbox'], "
        "div:has-text('Instrumental') button[role='switch']"
    ).first
    try:
        if await instrumental_toggle.is_visible(timeout=1500):
            checked = await instrumental_toggle.get_attribute("aria-checked")
            if checked != "true":
                print("Toggling Instrumental mode ON...")
                await instrumental_toggle.click(force=True)
                await suno_page.wait_for_timeout(500)
    except Exception as e_inst:
        print(f"Instrumental toggle notice: {e_inst}")

    # Also ensure lyrics editor is empty (Suno v6: empty lyrics = pure instrumental)
    lyrics_editor = suno_page.locator("div[contenteditable='true'][role='textbox']").first
    try:
        if await lyrics_editor.is_visible(timeout=1500):
            print("Clearing lyrics editor to guarantee instrumental BGM...")
            await lyrics_editor.click(force=True)
            await suno_page.keyboard.press("Control+A")
            await suno_page.keyboard.press("Backspace")
            await suno_page.wait_for_timeout(500)
    except Exception as e_lyr:
        print(f"Lyrics editor clear notice: {e_lyr}")

    # 5. Fill Styles of Music textarea
    styles_ta = suno_page.locator(
        "textarea[placeholder*='smooth female vocals'], "
        "textarea[placeholder*='techno dubstep'], "
        "textarea[placeholder*='dance floor'], "
        "textarea[placeholder*='Style of Music'], "
        "textarea[placeholder*='style'], "
        "div:has-text('Styles') textarea"
    ).first

    if await styles_ta.is_visible(timeout=3000):
        print("Typing BGM style prompt into Suno...")
        await styles_ta.click(force=True)
        await styles_ta.fill("")
        await styles_ta.fill(target_prompt)
        await suno_page.wait_for_timeout(1000)
    else:
        print("Warning: Direct Styles textarea not matched by selector.")

    # 6. Fill Song Title
    title_inp = suno_page.locator(
        "input[placeholder*='Title'], "
        "input[placeholder*='title'], "
        "input[aria-label*='Title']"
    ).first
    try:
        if not await title_inp.is_visible(timeout=1000):
            await suno_page.evaluate("""() => {
                const el = document.querySelector('input[placeholder*="Title"], input[placeholder*="title"]');
                if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }""")
            await suno_page.wait_for_timeout(800)

        if await title_inp.is_visible(timeout=2000):
            print(f"Entering Title: {target_title}...")
            await title_inp.click(force=True)
            await title_inp.fill("")
            await title_inp.fill(target_title)
            await suno_page.wait_for_timeout(500)
    except Exception as e_title:
        print(f"Title input notice: {e_title}")

    # Capture configured state
    await suno_page.screenshot(path="suno_configured.png")
    print("Saved suno_configured.png")

    # 7. Locate and Click Create Button
    create_btn = suno_page.locator(
        "button:has-text('Create'), "
        "button[aria-label='Create']"
    ).last

    if await create_btn.is_visible(timeout=3000):
        is_disabled = await create_btn.get_attribute("disabled")
        aria_disabled = await create_btn.get_attribute("aria-disabled")
        if is_disabled or aria_disabled == "true":
            print("Create button currently disabled. Checking fields...")
            return False

        print("Clicking Create button to generate instrumental BGM...")
        await create_btn.click(force=True)
        await suno_page.wait_for_timeout(6000)
        await suno_page.screenshot(path="suno_generating.png")
        print("Saved suno_generating.png - BGM generation successfully initiated!")
        await p.stop()
        return True
    else:
        print("Create button not visible. Screenshot captured.")
        await p.stop()
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
