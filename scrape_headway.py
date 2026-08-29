import asyncio
import json
import urllib.request
import os
import sys
from PIL import Image
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

async def scrape_general_website(url: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        print(f"Navigating to {url}...", flush=True)
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(5)
            final_url = page.url
            title = await page.title()
            print(f"Page Title: {title}", flush=True)
            print(f"Final URL: {final_url}", flush=True)
            
            body_text = await page.evaluate("() => document.body.innerText")
            with open(os.path.join(output_dir, "page_text.txt"), "w", encoding="utf-8") as f:
                f.write(body_text)
                
            await page.screenshot(path=os.path.join(output_dir, "screenshot.png"), full_page=False)
            
            imgs = await page.evaluate('''() => {
                return Array.from(document.querySelectorAll('img')).map(i => ({
                    src: i.src,
                    alt: i.alt,
                    width: i.naturalWidth,
                    height: i.naturalHeight
                }));
            }''')
            
            with open(os.path.join(output_dir, "images.json"), "w", encoding="utf-8") as f:
                json.dump(imgs, f, indent=2)
                
            print(f"Extracted {len(imgs)} images and {len(body_text)} chars of text.", flush=True)
            
            seen = set()
            count = 0
            for i in imgs:
                src = i['src']
                if src.startswith('http') and i['width'] >= 200 and i['height'] >= 200:
                    if src not in seen:
                        seen.add(src)
                        count += 1
                        ext = 'jpg' if 'jpg' in src or 'jpeg' in src else ('png' if 'png' in src else 'webp')
                        out_path = os.path.join(output_dir, f"site_img_{count}.{ext}")
                        try:
                            req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
                            data = urllib.request.urlopen(req, timeout=10).read()
                            with open(out_path, "wb") as img_f:
                                img_f.write(data)
                            print(f"Saved {out_path} ({i['width']}x{i['height']})", flush=True)
                        except Exception as e:
                            print(f"Failed {src}: {e}", flush=True)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_general_website("https://headway-malaysia.com/", "output/headway"))
