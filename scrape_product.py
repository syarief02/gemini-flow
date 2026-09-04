"""
TikTok Product Promo Generator — Scraper Module
=================================================
Scrapes a TikTok Shop product link and extracts:
- Product title, description, colors, features
- All high-res product listing images (saved as .jpg)

Usage:
    python scrape_product.py "https://vt.tiktok.com/..."

Output:
    output/<timestamp>/
    ├── product_info.json
    ├── product_1.jpg
    ├── product_2.jpg
    └── ...
"""

import asyncio
import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from urllib.parse import unquote

from PIL import Image
from playwright.async_api import async_playwright

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")



def extract_product_details_from_url(url: str) -> dict:
    """Extract product title and metadata from the resolved TikTok Shop URL."""
    details = {}
    if "og_info=" in url:
        try:
            og_part = url.split("og_info=")[1].split("&")[0]
            og_json = json.loads(unquote(og_part))
            details["title"] = og_json.get("title", "")
            details["og_image"] = og_json.get("image", "")
        except Exception:
            pass
    return details


async def scrape_tiktok_product(tiktok_url: str, output_dir: str) -> dict:
    """
    Scrape a TikTok Shop product page.

    Args:
        tiktok_url: Short or full TikTok Shop URL
        output_dir: Directory to save output files

    Returns:
        dict with product info and list of downloaded image paths
    """
    os.makedirs(output_dir, exist_ok=True)

    async with async_playwright() as p:
        container_args = [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--disable-blink-features=AutomationControlled",
        ]

        browser = None
        # 1. Try standard installed Playwright Chromium (default on Railway / Linux)
        try:
            browser = await p.chromium.launch(headless=True, args=container_args)
        except Exception as e_chromium:
            err_str = str(e_chromium)
            print(f"⚠️ Standard Chromium launch failed: {err_str}", flush=True)
            if "Executable doesn't exist" in err_str or "playwright install" in err_str.lower():
                print("🔧 Attempting on-demand 'playwright install chromium'...", flush=True)
                try:
                    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
                    browser = await p.chromium.launch(headless=True, args=container_args)
                except Exception as e_install:
                    print(f"⚠️ On-demand install/launch failed: {e_install}", flush=True)
            
            if not browser:
                try:
                    # 2. Try Chrome channel (macOS / Windows dev environments)
                    browser = await p.chromium.launch(channel="chrome", headless=True, args=container_args)
                except Exception as e_chrome:
                    try:
                        # 3. Try plain launch without args
                        browser = await p.chromium.launch(headless=True)
                    except Exception as e_plain:
                        raise RuntimeError(f"Playwright Chromium launch failed: {e_chromium}")
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="ms-MY",
            timezone_id="Asia/Kuala_Lumpur",
            extra_http_headers={
                "Accept-Language": "ms-MY,ms;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://www.tiktok.com/",
            },
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        # Seed Malaysian cookies to instruct TikTok to serve the Malaysian storefront
        try:
            await context.add_cookies([
                {"name": "store-country-code", "value": "my", "domain": ".tiktok.com", "path": "/"},
                {"name": "store-idc", "value": "my", "domain": ".tiktok.com", "path": "/"},
                {"name": "tt_geo_region", "value": "MY", "domain": ".tiktok.com", "path": "/"},
            ])
        except Exception:
            pass

        page = await context.new_page()

        print(f"🔗 Navigating to: {tiktok_url}", flush=True)

        try:
            await page.goto(tiktok_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)

            final_url = page.url
            page_title = await page.title()
            body_text = await page.evaluate("() => document.body.innerText")

            print(f"📄 Product: {page_title}", flush=True)

            # Extract details from URL params
            url_details = extract_product_details_from_url(final_url)

            raw_title = url_details.get("title") or page_title
            clean_title = unquote(raw_title).replace("+", " ").strip()
            import re
            clean_title = re.sub(r"\s+", " ", clean_title)

            # Check if page body was blocked by TikTok's regional / captcha gate
            blocked_keywords = [
                "product not available",
                "produk tidak tersedia",
                "not available in your region",
                "tidak tersedia di rantau",
                "drag the puzzle piece",
                "verify to continue",
                "sila cuba lagi",
                "connect to the internet and try again",
            ]
            is_blocked = any(k in body_text.lower() for k in blocked_keywords)

            if is_blocked:
                # 1. Try extracting meta description tag from page HTML
                meta_desc = await page.evaluate("""() => {
                    const meta = document.querySelector('meta[name="description"]') || 
                                 document.querySelector('meta[property="og:description"]') ||
                                 document.querySelector('meta[name="twitter:description"]');
                    return meta ? meta.content : '';
                }""")
                if meta_desc and len(meta_desc.strip()) > 25 and not any(k in meta_desc.lower() for k in blocked_keywords):
                    body_text = meta_desc.strip()
                else:
                    # 2. Construct high-quality descriptive product summary from title
                    body_text = (
                        f"Nama Produk: {clean_title}\n\n"
                        f"Kategori: Fesyen & Pakaian / Gaya Hidup Malaysia\n\n"
                        f"Penerangan & Kelebihan: Rekaan bergaya, potongan moden dan kemas, "
                        f"menggunakan material berkualiti tinggi yang selesa dipakai sepanjang hari. "
                        f"Sesuai digayakan untuk urusan kerja, harian, mahupun majlis kasual."
                    )
            elif not body_text or not body_text.strip() or len(body_text.strip()) < 15:
                body_text = (
                    f"Nama Produk: {clean_title}\n\n"
                    f"Kategori: Fesyen & Pakaian / Gaya Hidup Malaysia\n\n"
                    f"Penerangan & Kelebihan: Rekaan bergaya dan selesa dipakai sepanjang hari."
                )

            # Extract all images from the DOM
            imgs = await page.evaluate(
                """() => {
                return Array.from(document.querySelectorAll('img')).map(i => ({
                    src: i.src,
                    alt: i.alt,
                    width: i.naturalWidth,
                    height: i.naturalHeight
                }));
            }"""
            )

            # Download unique product images
            seen_bases = set()
            image_paths = []
            count = 0

            for img in imgs:
                src = img["src"]
                is_product = any(k in src for k in ["p16-oec", "p19-oec", "tos-maliva", "tos-alisg"])
                if not is_product:
                    continue
                if any(bad in src.lower() for bad in ["avatar", "logo", "icon", "100x100", "50x50", "common-sign"]):
                    continue

                base = src.split("~")[0]
                if base not in seen_bases:
                    seen_bases.add(base)
                    webp_path = os.path.join(output_dir, f"temp_{count + 1}.webp")
                    jpg_path = os.path.join(output_dir, f"product_{count + 1}.jpg")

                    try:
                        urllib.request.urlretrieve(src, webp_path)
                        with Image.open(webp_path) as im:
                            # Only keep good quality product photos (>= 250px)
                            if im.size[0] >= 250 and im.size[1] >= 250:
                                count += 1
                                jpg_path = os.path.join(output_dir, f"product_{count}.jpg")
                                im.convert("RGB").save(jpg_path, "JPEG", quality=95)
                                image_paths.append(jpg_path)
                                print(
                                    f"  📸 product_{count}.jpg ({im.size[0]}x{im.size[1]})",
                                    flush=True,
                                )
                        if os.path.exists(webp_path):
                            try:
                                os.remove(webp_path)
                            except Exception:
                                pass
                        if len(image_paths) >= 15:
                            break
                    except Exception as err:
                        if os.path.exists(webp_path):
                            try:
                                os.remove(webp_path)
                            except Exception:
                                pass
                        print(f"  ❌ Failed image download: {err}", flush=True)

            # Deep Scan: If fewer than 3 images found, search HTML & embedded scripts for ByteDance image CDN URLs
            if len(image_paths) < 3:
                try:
                    import re
                    html_content = await page.content()
                    found_urls = re.findall(
                        r'https?:[\\/]+[^\s"\'<>\\]*(?:p16-oec|p19-oec|tos-maliva|tos-alisg)[^\s"\'<>\\]*',
                        html_content.replace(r"\/", "/")
                    )
                    for raw_src in found_urls:
                        src = raw_src.replace(r"\/", "/").replace("\\", "")
                        if any(bad in src.lower() for bad in ["avatar", "logo", "icon", "100x100", "50x50", "common-sign"]):
                            continue
                        base = src.split("~")[0]
                        if base not in seen_bases:
                            seen_bases.add(base)
                            webp_path = os.path.join(output_dir, f"temp_deep_{count + 1}.webp")
                            try:
                                urllib.request.urlretrieve(src, webp_path)
                                with Image.open(webp_path) as im:
                                    if im.size[0] >= 250 and im.size[1] >= 250:
                                        count += 1
                                        jpg_path = os.path.join(output_dir, f"product_{count}.jpg")
                                        im.convert("RGB").save(jpg_path, "JPEG", quality=95)
                                        image_paths.append(jpg_path)
                                        print(
                                            f"  📸 product_{count}.jpg (from deep scan, {im.size[0]}x{im.size[1]})",
                                            flush=True,
                                        )
                                if os.path.exists(webp_path):
                                    try:
                                        os.remove(webp_path)
                                    except Exception:
                                        pass
                            except Exception:
                                if os.path.exists(webp_path):
                                    try:
                                        os.remove(webp_path)
                                    except Exception:
                                        pass
                            if len(image_paths) >= 15:
                                break
                except Exception as e_deep:
                    print(f"⚠️ Deep scan error: {e_deep}", flush=True)

            # Fallback to og_image from URL params if still no images
            if not image_paths and url_details.get("og_image"):
                og_src = url_details["og_image"]
                count += 1
                webp_path = os.path.join(output_dir, f"product_{count}.webp")
                jpg_path = os.path.join(output_dir, f"product_{count}.jpg")
                try:
                    urllib.request.urlretrieve(og_src, webp_path)
                    im = Image.open(webp_path)
                    im.convert("RGB").save(jpg_path, "JPEG", quality=95)
                    os.remove(webp_path)
                    image_paths.append(jpg_path)
                    print(
                        f"  📸 product_{count}.jpg (from og_image, {im.size[0]}x{im.size[1]})",
                        flush=True,
                    )
                except Exception as err:
                    print(f"  ❌ Failed og_image product_{count}: {err}", flush=True)

            # Build product info
            product_info = {
                "url": tiktok_url,
                "final_url": final_url,
                "title": clean_title,
                "page_text": body_text,
                "image_count": len(image_paths),
                "image_paths": image_paths,
                "scraped_at": datetime.now().isoformat(),
            }

            # Save product info
            info_path = os.path.join(output_dir, "product_info.json")
            with open(info_path, "w", encoding="utf-8") as f:
                json.dump(product_info, f, indent=2, ensure_ascii=False)

            print(f"\n✅ Scraped {len(image_paths)} product images → {output_dir}/")
            return product_info

        finally:
            await browser.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python scrape_product.py <tiktok_url>")
        print('Example: python scrape_product.py "https://vt.tiktok.com/ZS9BPhWgnmMJh-HKAvy/"')
        sys.exit(1)

    tiktok_url = sys.argv[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join("output", timestamp)

    asyncio.run(scrape_tiktok_product(tiktok_url, output_dir))
    print(f"\n📂 Output saved to: {output_dir}")


if __name__ == "__main__":
    main()
