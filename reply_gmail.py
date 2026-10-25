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


def get_record_info(prefix: str = None) -> tuple[str, str, str]:
    """Retrieve (caption, tiktok_url, product_name) from record."""
    from generation_store import latest_record, load_record

    record = load_record(prefix) if prefix else latest_record()
    if not record or not (record.get("caption") or "").strip():
        where = f"generations/{prefix}.json" if prefix else "generations/"
        raise RuntimeError(f"No caption found in {where}. Pass --caption or --file instead.")
    
    product_name = record.get("product_name", "")
    prefix_str = record.get("prefix", "")
    print(f"Loaded record: {product_name} ({prefix_str})")
    
    cap = record["caption"].strip()
    tags = (record.get("hashtags") or "").strip()
    full_caption = f"{cap}\n\n{tags}".strip() if tags and tags not in cap else cap
    
    meta = record.get("metadata") or {}
    tiktok_url = meta.get("tiktok_url") or meta.get("source_url") or ""
    
    return full_caption, tiktok_url, product_name


async def reply_with_clean_format(
    caption_text: str = None,
    thread_url: str = None,
    search_query: str = None
):
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

    await gmail_page.bring_to_front()

    if thread_url:
        print(f"Navigating directly to specified thread: {thread_url}")
        await gmail_page.goto(thread_url.strip(), wait_until="domcontentloaded")
        await gmail_page.wait_for_timeout(3000)
    else:
        # Always navigate to inbox first to clear any stale open thread
        print("Navigating to Gmail inbox to find target thread...")
        await gmail_page.goto(DEFAULT_INBOX_URL, wait_until="domcontentloaded")
        await gmail_page.wait_for_timeout(3000)

        target_row = None

        # Clean search query (e.g. extract shortcode if it's a URL)
        clean_search = (search_query or "").strip()
        url_match = re.search(r"vt\.tiktok\.com/([A-Za-z0-9_-]+)", clean_search)
        query_token = url_match.group(1) if url_match else clean_search

        if query_token:
            print(f"Looking for thread containing: '{query_token}'...")
            # Step A: Scan top inbox rows
            rows = await gmail_page.locator("tr.zA").all()
            for i, r in enumerate(rows[:25]):
                txt = await r.inner_text()
                if query_token in txt:
                    print(f"Match found in inbox Row {i}!")
                    target_row = r
                    break

            # Step B: If not in top rows, search Gmail search bar
            if not target_row:
                print(f"Not in top visible rows. Using Gmail search bar for '{query_token}'...")
                search_input = gmail_page.locator("input[aria-label*='Search mail'], input[name='q']").first
                if await search_input.is_visible(timeout=3000):
                    await search_input.click()
                    await search_input.fill(clean_search)
                    await gmail_page.keyboard.press("Enter")
                    await gmail_page.wait_for_timeout(3000)
                    result_rows = await gmail_page.locator("tr.zA, div[role='main'] table tbody tr").all()
                    if result_rows:
                        print(f"Found {len(result_rows)} search result(s). Selecting first match...")
                        target_row = result_rows[0]
                    else:
                        print("WARNING: Search returned no results.")

        if target_row:
            print("Opening matched thread...")
            await target_row.click()
            await gmail_page.wait_for_timeout(3000)
        else:
            # Fallback only if no search query was given: top thread
            print("Notice: No specific search query matched. Opening top thread in inbox...")
            top_thread = gmail_page.locator("tr.zA, div[role='main'] table tbody tr").first
            if await top_thread.is_visible(timeout=5000):
                await top_thread.click()
                await gmail_page.wait_for_timeout(3000)

    print(f"Active thread URL: {gmail_page.url}")

    # Double check that thread is open
    is_inside_thread = bool(re.search(r'#(?:inbox|all|sent|search)/[A-Za-z0-9_-]+', gmail_page.url))
    if not is_inside_thread:
        print("Notice: May not be inside a thread, attempting reply trigger anyway.")

    await gmail_page.wait_for_timeout(1500)

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
                const quotes = bodyBox.querySelectorAll("div.gmail_quote, blockquote, div.ajR");
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
        await body_box.fill(caption_text)
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
            await p.stop()
            return True
        else:
            print("Send button not found directly.")
            await p.stop()
            return False
    else:
        print("Composer textbox not found.")
        await p.stop()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automate Gmail promo reply via Brave CDP")
    parser.add_argument("--caption", type=str, help="Specific clean caption string to send")
    parser.add_argument("--file", type=str, help="Path to text or JSON file containing caption")
    parser.add_argument("--prefix", type=str, help="Send the caption from generations/<prefix>.json")
    parser.add_argument("--latest", action="store_true", help="Send the caption from the newest record in generations/")
    parser.add_argument("--thread-url", type=str, help="Target Gmail thread URL")
    parser.add_argument("--search", type=str, help="Search query or product link to find the exact email thread")
    args = parser.parse_args()

    chosen_caption = None
    search_q = args.search

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
        cap, link, title = get_record_info(args.prefix)
        chosen_caption = cap
        if not search_q:
            search_q = link or title

    success = asyncio.run(reply_with_clean_format(
        caption_text=chosen_caption,
        thread_url=args.thread_url,
        search_query=search_q
    ))
    sys.exit(0 if success else 1)
