import asyncio
import os
import sys
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

GMAIL_THREAD_URL = "https://mail.google.com/mail/u/0/#inbox/KtbxLxGPlLGCfJCdlgnfRFLpkxZLPzQgrL"
BRAVE_EXE = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"

REPLY_TEXT = """Salam Syarief,

Berikut adalah kapsyen TikTok Shop dan maklumat promosi lengkap untuk produk Baju Kuning Guest Blouse Wanita:

========================================
KAPSYEN TIKTOK SHOP + HASHTAGS SEO
========================================
Bila dapat jemputan kenduri kahwin tema kuning, mesti ramai pening kepala takut nampak kusam kan? ✨

Korang tengok kemeja blaus jalur rona soft butter yellow ni: tona kuning pastel lembut ni memang auto naikkan seri wajah dan langsung tak buat kulit nampak malap! Ditambah pula dengan perincian jalur halus menegak dan potongan lengan gelembung tiga suku yang kembang beralun, terus bagi siluet ramping dan sopan terletak. Sesuai sangat untuk gayakan ke majlis kenduri, hari kerja di pejabat, mahupun santai hujung minggu.

Kelebihan blaus kemeja jalur kuning lembut ni yang buat saya suka:
✨ Tona Kuning Pastel Lembut: Warna butter yellow yang manis, menaikkan seri kulit tanpa nampak terlalu terang atau mencolok mata.
✨ Jalur Menegak Slimming Effect: Corak pinstripes halus yang memberi ilusi badan kelihatan lebih tinggi dan ramping.
✨ Lengan Gelembung Tiga Suku: Potongan 3/4 lantern puff sleeves yang selesa, menutup lengan dengan kemas dan bergaya ala Korean chic.
✨ Fabrik Sejuk Beralun: Material ringan dan breathable yang sangat selesa dan tidak melekit walau dipakai bawah cuaca panas terik Malaysia.
✨ Saiz Mesra S Hingga Plus Size: Potongan loose flowy yang terletak kemas pada pelbagai bentuk tubuh wanita.

Padankan dengan seluar tailored rona krim atau skirt pleated untuk penampilan yang eksklusif dan manis dipandang! 💛

Jom tekan beg kuning dekat bawah sekarang untuk dapatkan saiz pilihan korang sebelum stok habis licin! 👇💛

#BajuKuningGuest #BlouseWanitaPlusSize #KemejaStripe #OutfitKenduri #KoreanStyleBlouse #MuslimahStyleMY

========================================
PAUTAN VIDEO & KEYFRAME (FLOW AI)
========================================
• Projek Flow AI (10s Omni Flash):
  https://flow.google.com/u/5/project/5522d161-f8b0-47b4-9745-2330b7137108

• Supabase Keyframe CDN:
  - Frame 1: https://blqsgijvdvzwnqeltoje.supabase.co/storage/v1/object/public/gemini-flow-keyframes/soft_yellow_striped_blouse_frame1.jpg
  - Frame 2: https://blqsgijvdvzwnqeltoje.supabase.co/storage/v1/object/public/gemini-flow-keyframes/soft_yellow_striped_blouse_frame2.jpg
  - Frame 3: https://blqsgijvdvzwnqeltoje.supabase.co/storage/v1/object/public/gemini-flow-keyframes/soft_yellow_striped_blouse_frame3.jpg
"""

async def main():
    print("Step 1: Connecting to Brave over CDP...")
    p = await async_playwright().start()
    browser = None
    try:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222", timeout=4000)
        print("Connected directly to running Brave!")
    except Exception as e:
        print(f"Direct connection failed ({e}). Need restart with remote debugging.")
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
        await gmail_page.goto(GMAIL_THREAD_URL, wait_until="networkidle")
    else:
        await gmail_page.bring_to_front()
        if GMAIL_THREAD_URL not in gmail_page.url:
            print(f"Navigating to thread: {GMAIL_THREAD_URL}")
            await gmail_page.goto(GMAIL_THREAD_URL, wait_until="networkidle")

    await gmail_page.wait_for_timeout(3000)
    screenshot_before = Path("gmail_before_reply.png")
    await gmail_page.screenshot(path=str(screenshot_before))
    print(f"Saved initial screenshot: {screenshot_before}")

    # Inspect previous email text on page
    content_text = await gmail_page.inner_text("body")
    print(f"Gmail page snippet: {content_text[:300]}...")

    # Look for Reply button or press 'r'
    reply_btn = gmail_page.locator("span[role='button']:has-text('Reply'), div[role='button']:has-text('Reply'), [aria-label*='Reply']").first
    if await reply_btn.is_visible():
        print("Clicking Reply button...")
        await reply_btn.click()
    else:
        print("Pressing 'r' shortcut to trigger Reply...")
        await gmail_page.keyboard.press("r")

    await gmail_page.wait_for_timeout(2000)

    # Locate composer body
    body_box = gmail_page.locator("div[role='textbox'][aria-label*='Message Body'], div[role='textbox']").first
    if await body_box.is_visible():
        print("Composer body located. Entering reply content...")
        await body_box.click()
        # Insert text
        await body_box.fill(REPLY_TEXT)
        await gmail_page.wait_for_timeout(1000)
        screenshot_draft = Path("gmail_reply_drafted.png")
        await gmail_page.screenshot(path=str(screenshot_draft))
        print(f"Saved reply draft screenshot: {screenshot_draft}")

        # Locate Send button
        send_btn = gmail_page.locator("div[role='button']:has-text('Send'), [data-tooltip*='Send']").first
        if await send_btn.is_visible():
            print("Clicking Send button...")
            await send_btn.click()
            await gmail_page.wait_for_timeout(3000)
            screenshot_sent = Path("gmail_reply_sent.png")
            await gmail_page.screenshot(path=str(screenshot_sent))
            print(f"Saved sent confirmation screenshot: {screenshot_sent}")
            print("EMAIL REPLY SENT SUCCESSFULLY!")
            return True
        else:
            print("Send button not found directly. Draft is preserved in composer.")
            return True
    else:
        print("Composer textbox not found.")
        screenshot_err = Path("gmail_reply_error.png")
        await gmail_page.screenshot(path=str(screenshot_err))
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

