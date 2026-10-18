import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

GMAIL_THREAD_URL = "https://mail.google.com/mail/u/0/#inbox/KtbxLxGPlLGCfJCdlgnfRFLpkxZLPzQgrL"

# The email reply format must be ONLY the clean TikTok caption and hashtags
CLEAN_KAPSYEN = """Bila dapat jemputan kenduri kahwin tema kuning, mesti ramai pening kepala takut nampak kusam kan? ✨

Korang tengok kemeja blaus jalur rona soft butter yellow ni: tona kuning pastel lembut ni memang auto naikkan seri wajah dan langsung tak buat kulit nampak malap! Ditambah pula dengan perincian jalur halus menegak dan potongan lengan gelembung tiga suku yang kembang beralun, terus bagi siluet ramping dan sopan terletak. Sesuai sangat untuk gayakan ke majlis kenduri, hari kerja di pejabat, mahupun santai hujung minggu.

Kelebihan blaus kemeja jalur kuning lembut ni yang buat saya suka:
✨ Tona Kuning Pastel Lembut: Warna butter yellow yang manis, menaikkan seri kulit tanpa nampak terlalu terang atau mencolok mata.
✨ Jalur Menegak Slimming Effect: Corak pinstripes halus yang memberi ilusi badan kelihatan lebih tinggi dan ramping.
✨ Lengan Gelembung Tiga Suku: Potongan 3/4 lantern puff sleeves yang selesa, menutup lengan dengan kemas dan bergaya ala Korean chic.
✨ Fabrik Sejuk Beralun: Material ringan dan breathable yang sangat selesa dan tidak melekit walau dipakai bawah cuaca panas terik Malaysia.
✨ Saiz Mesra S Hingga Plus Size: Potongan loose flowy yang terletak kemas pada pelbagai bentuk tubuh wanita.

Padankan dengan seluar tailored rona krim atau skirt pleated untuk penampilan yang eksklusif dan manis dipandang! 💛

Jom tekan beg kuning dekat bawah sekarang untuk dapatkan saiz pilihan korang sebelum stok habis licin! 👇💛

#BajuKuningGuest #BlouseWanitaPlusSize #KemejaStripe #OutfitKenduri #KoreanStyleBlouse #MuslimahStyleMY"""

async def reply_with_clean_format():
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
        print("Opening new tab to Gmail thread...")
        gmail_page = await context.new_page()
        await gmail_page.goto(GMAIL_THREAD_URL, wait_until="domcontentloaded")
    else:
        await gmail_page.bring_to_front()
        if GMAIL_THREAD_URL not in gmail_page.url:
            print(f"Navigating to thread: {GMAIL_THREAD_URL}")
            await gmail_page.goto(GMAIL_THREAD_URL, wait_until="domcontentloaded")

    await gmail_page.wait_for_timeout(3500)

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
        print("Composer body located. Entering pure caption content...")
        await body_box.click()
        await body_box.fill("")
        await body_box.fill(CLEAN_KAPSYEN)
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
    success = asyncio.run(reply_with_clean_format())
    sys.exit(0 if success else 1)
