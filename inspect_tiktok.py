import asyncio
import json
import urllib.request
from playwright.async_api import async_playwright

async def inspect_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        print("Navigating to TikTok link...", flush=True)
        try:
            response = await page.goto("https://vt.tiktok.com/ZS9Ba3ftm4wmL-0LD3i/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            url = page.url
            print("Final URL:", url, flush=True)
            
            title = await page.title()
            print("Page title:", title, flush=True)
            
            # Take screenshot
            await page.screenshot(path="tiktok_product_screenshot.png", full_page=False)
            print("Saved screenshot to tiktok_product_screenshot.png", flush=True)
            
            # Extract text & images
            body_text = await page.evaluate("() => document.body.innerText")
            with open("tiktok_page_text.txt", "w", encoding="utf-8") as f:
                f.write(body_text)
                
            imgs = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('img')).map(i => ({src: i.src, alt: i.alt, width: i.naturalWidth, height: i.naturalHeight}));
            }''')
            
            with open("tiktok_images.json", "w", encoding="utf-8") as f:
                json.dump(imgs, f, indent=2)
                
            print(f"Extracted {len(imgs)} images and {len(body_text)} chars of text.", flush=True)
        except Exception as e:
            print("Error navigating:", e, flush=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_tiktok())
