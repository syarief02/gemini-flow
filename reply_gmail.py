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

DEFAULT_INBOX_URL = "https://mail.google.com/mail/u/0/#inbox"


def get_latest_caption(prefix: str = None) -> str:
    """Caption + hashtags from generations/<prefix>.json, or from the newest record without a prefix.

    Never falls back to a stored sample caption: sending another product's caption is worse than not sending.
    """
    from generation_store import latest_record, load_record

    record = load_record(prefix) if prefix else latest_record()
    if not record or not (record.get("caption") or "").strip():
        where = f"generations/{prefix}.json" if prefix else "generations/"
        raise RuntimeError(f"No caption found in {where}. Pass --caption or --file instead.")
    print(f"Caption from record: {record.get('product_name')} ({record.get('prefix')})")
    cap = record["caption"].strip()
    tags = (record.get("hashtags") or "").strip()
    if tags and tags not in cap:
        return f"{cap}\n\n{tags}"
    return cap


async def reply_with_clean_format(caption_text: str = None, thread_url: str = None):
    target_caption = (caption_text or get_latest_caption()).strip()

    print("Step 1: Connecting to Brave over CDP on port 9222...")
    p = await async_playwright().start()
    browser = None
    try:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=5000)
        print("Connected to Brave!")
    except Exception as e:
        print(f"Could not connect to Brave: {e}")
        await p.stop()
        return False

    context = browser.contexts[0]
    gmail_page = None
    for page in context.pages:
        if "mail.google.com" in page.url:
            gmail_page = page
            print(f"Found existing Gmail tab: {page.url}")
            break

    if not gmail_page:
        print("Opening new tab to Gmail...")
        gmail_page = await context.new_page()
        if thread_url:
            await gmail_page.goto(thread_url.strip(), wait_until="domcontentloaded")
        else:
            await gmail_page.goto(DEFAULT_INBOX_URL, wait_until="domcontentloaded")
    else:
        await gmail_page.bring_to_front()
        if thread_url and thread_url.strip() not in gmail_page.url:
            print(f"Navigating to specified thread: {thread_url}")
            await gmail_page.goto(thread_url.strip(), wait_until="domcontentloaded")

    await gmail_page.wait_for_timeout(3000)

    # If we are on inbox list (not inside an active thread), open the top/latest email thread
    is_inside_thread = bool(re.search(r'#(?:inbox|all|sent)/[A-Za-z0-9_-]+', gmail_page.url))
    if not is_inside_thread:
        print("Currently on inbox list or overview. Opening the latest email thread...")
        top_thread = gmail_page.locator("tr.zA, div[role='main'] table tbody tr").first
        if await top_thread.is_visible(timeout=5000):
            await top_thread.click()
            await gmail_page.wait_for_timeout(3000)
            print(f"Opened thread: {gmail_page.url}")
        else:
            print("Notice: No visible thread rows found in inbox table, attempting to stay on current page.")

    await gmail_page.wait_for_timeout(2000)

    # Click Reply button or press 'r'
    reply_btn = gmail_page.locator("span[role='button']:has-text('Reply'), div[role='button']:has-text('Reply'), [aria-label*='Reply']").last
    if await reply_btn.is_visible(timeout=3000):
        print("Clicking Reply button...")
        await reply_btn.click()
    else:
        print("Pressing 'r' shortcut to trigger Reply...")
        await gmail_page.keyboard.press("r")

    await gmail_page.wait_for_timeout(2000)

    # Locate composer body
    body_box = gmail_page.locator("div[role='textbox'][aria-label*='Message Body'], div[role='textbox']").last
    if await body_box.is_visible(timeout=4000):
        print("Composer body located.")

        # Step 2a: Check and click "Show trimmed content" button (the '...' button) to expose any quoted text
        trimmed_btn = gmail_page.locator("div[aria-label*='Show trimmed content'], div[aria-label*='trimmed'], div[aria-label*='potong'], div.ajR").last
        if await trimmed_btn.is_visible(timeout=1500):
            print("Found 'Show trimmed content' button. Clicking to expand quoted text...")
            try:
                await trimmed_btn.click()
                await gmail_page.wait_for_timeout(1000)
            except Exception as e_trim:
                print(f"Notice expanding trimmed content: {e_trim}")

        # Step 2b: Remove all quoted text elements from the composer DOM
        await gmail_page.evaluate("""() => {
            const bodyBox = document.querySelector("div[role='textbox'][aria-label*='Message Body'], div[role='textbox']");
            if (bodyBox) {
                const quotes = Array.from(bodyBox.querySelectorAll("div.gmail_quote, div.gmail_extra, blockquote, .gmail_quote, [class*='quote']"));
                quotes.forEach(q => q.remove());
            }
        }""")

        # Step 2c: Focus and select all to completely wipe any residual text or quotes
        print("Clearing composer completely of any quoted text...")
        await body_box.click()
        await gmail_page.wait_for_timeout(300)
        await gmail_page.keyboard.press("Control+A")
        await gmail_page.wait_for_timeout(300)
        await gmail_page.keyboard.press("Backspace")
        await gmail_page.wait_for_timeout(500)

        # Step 2d: Enter pure clean caption content
        print("Entering pure clean caption content...")
        await body_box.fill(target_caption)
        await gmail_page.wait_for_timeout(1000)

        # Locate Send button
        send_btn = gmail_page.locator("div[role='button']:has-text('Send'), [data-tooltip*='Send']").last
        if await send_btn.is_visible(timeout=3000):
            print("Clicking Send button...")
            await send_btn.click()
            await gmail_page.wait_for_timeout(4000)
            screenshot_sent = Path("gmail_reply_sent_clean.png")
            await gmail_page.screenshot(path=str(screenshot_sent))
            print(f"Saved sent confirmation screenshot: {screenshot_sent}")
            print("CLEAN EMAIL REPLY SENT SUCCESSFULLY!")
            return True
        else:
            print("Send button not found directly.")
            return False
    else:
        print("Composer textbox not found.")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Gmail promo reply via Brave CDP")
    parser.add_argument("--caption", type=str, help="Specific clean caption string to send")
    parser.add_argument("--file", type=str, help="Path to text or JSON file containing caption")
    parser.add_argument("--prefix", type=str, help="Send the caption from generations/<prefix>.json")
    parser.add_argument("--latest", action="store_true", help="Send the caption from the newest record in generations/")
    parser.add_argument("--thread-url", type=str, help="Target Gmail thread URL")
    args = parser.parse_args()

    chosen_caption = None
    if args.caption:
        chosen_caption = args.caption
    elif args.file:
        file_path = Path(args.file)
        if file_path.is_file():
            content = file_path.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
                cap = data.get("tiktok_caption") or data.get("caption") or ""
                tags = data.get("hashtags") or ""
                chosen_caption = f"{cap}\n\n{tags}".strip() if tags and tags not in cap else cap
            except Exception:
                chosen_caption = content
    else:
        chosen_caption = get_latest_caption(args.prefix)

    success = asyncio.run(reply_with_clean_format(caption_text=chosen_caption, thread_url=args.thread_url))
    sys.exit(0 if success else 1)
