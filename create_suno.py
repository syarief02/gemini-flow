import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

SUNO_URL = "https://suno.com/create"
BGM_PROMPT = (
    "Upbeat lo-fi indie acoustic cafe pop, featuring bright fingerpicked acoustic guitar, "
    "subtle warm Rhodes electric piano chords, crisp lo-fi drum groove, soft shaker, and round "
    "warm melodic bass. Sunny, breezy, modern Malaysian aesthetic lifestyle vibe, relaxing and "
    "optimistic tempo at 110 BPM. Pure instrumental, strictly no vocals, loopable high quality production."
)
BGM_TITLE = "Baju Kuning Guest Blouse - Soft Yellow Chill BGM"

async def setup_suno():
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
    print(f"Page text snippet: {page_text[:300].replace('\n', ' ')}")

    # Check if Custom mode switch exists
    custom_toggle = suno_page.locator("button[role='switch']:has-text('Custom'), div:has-text('Custom') button[role='switch'], button:has-text('Custom')").first
    is_custom = False
    try:
        if await custom_toggle.is_visible(timeout=2000):
            # Check state
            checked = await custom_toggle.get_attribute("aria-checked")
            if checked != "true":
                print("Enabling Custom mode...")
                await custom_toggle.click()
                await suno_page.wait_for_timeout(1500)
            is_custom = True
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
        await style_input.fill(BGM_PROMPT)
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
            await title_input.fill(BGM_TITLE)
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
    success = asyncio.run(setup_suno())
    sys.exit(0 if success else 1)

