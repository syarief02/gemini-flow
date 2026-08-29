import asyncio
import json
import urllib.request
import os
from PIL import Image
from playwright.async_api import async_playwright

async def inspect_and_download():
    url = "https://vt.tiktok.com/ZS9Ba3ftm4wmL-0LD3i/"
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        print("Navigating to TikTok link...", flush=True)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            final_url = page.url
            print("Final URL:", final_url, flush=True)
            title = await page.title()
            print("Page title:", title, flush=True)
            
            body_text = await page.evaluate("() => document.body.innerText")
            with open("tiktok_new_product_text.txt", "w", encoding="utf-8") as f:
                f.write(body_text)
                
            imgs = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('img')).map(i => ({
                    src: i.src,
                    alt: i.alt,
                    width: i.naturalWidth,
                    height: i.naturalHeight
                }));
            }''')
            
            with open("tiktok_new_images.json", "w", encoding="utf-8") as f:
                json.dump(imgs, f, indent=2)
                
            print(f"Extracted {len(imgs)} images.", flush=True)
            
            # Download product images
            seen = set()
            count = 0
            for i in imgs:
                src = i['src']
                if ('p16-oec' in src or 'tos-maliva' in src or 'tos-alisg' in src) and i['width'] >= 300:
                    base = src.split('~')[0]
                    if base not in seen:
                        seen.add(base)
                        count += 1
                        filename = f"new_product_{count}.webp"
                        try:
                            urllib.request.urlretrieve(src, filename)
                            # Convert to jpg
                            im = Image.open(filename)
                            im.convert('RGB').save(f"new_product_{count}.jpg", "JPEG")
                            print(f"Downloaded and converted new_product_{count}.jpg ({im.size})", flush=True)
                        except Exception as err:
                            print(f"Error downloading {src}: {err}", flush=True)
            print(f"Total product images downloaded: {count}", flush=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_and_download())
