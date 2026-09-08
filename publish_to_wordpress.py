"""
WordPress Publisher Module for Gemini Flow
==========================================
Publishes generated TikTok product promos, keyframe visuals, and affiliate
copywriting directly to WordPress.com as blog posts or product showcases.

Usage:
    python publish_to_wordpress.py --test
    python publish_to_wordpress.py --latest --status draft
    python publish_to_wordpress.py --session output/20260907_160155
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parent
load_dotenv(WORKSPACE / ".env")

WP_SITE_URL = os.getenv("WP_SITE_URL", "https://bubatresources.wordpress.com")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "").replace(" ", "")


def get_site_domain() -> str:
    """Extract clean domain/slug for WordPress.com REST API endpoint."""
    domain = WP_SITE_URL.replace("http://", "").replace("https://", "").strip("/")
    return domain


def get_auth_header() -> Optional[str]:
    """Generate Basic auth header from user and application password."""
    if not WP_USER or not WP_APP_PASSWORD:
        return None
    token = f"{WP_USER}:{WP_APP_PASSWORD}"
    encoded = base64.b64encode(token.encode("utf-8")).decode("ascii")
    return f"Basic {encoded}"


def test_connection() -> Dict[str, Any]:
    """Test connection and read access to the WordPress.com site."""
    auth = get_auth_header()
    if not auth:
        return {
            "status": "error",
            "message": "Missing WP_USER or WP_APP_PASSWORD in .env"
        }
    site = get_site_domain()
    url = f"https://public-api.wordpress.com/wp/v2/sites/{site}/posts"
    headers = {
        "Authorization": auth,
        "User-Agent": "GeminiFlow-Antigravity/1.0"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            posts = json.loads(resp.read().decode("utf-8"))
            return {
                "status": "connected",
                "site": site,
                "http_status": resp.getcode(),
                "existing_posts_count": len(posts)
            }
    except urllib.error.HTTPError as e:
        return {
            "status": "failed",
            "site": site,
            "http_code": e.code,
            "error": e.read().decode("utf-8", errors="replace")[:300]
        }
    except Exception as e:
        return {
            "status": "failed",
            "site": site,
            "error": str(e)
        }


def format_html_post(
    product_title: str,
    caption_text: str,
    product_url: Optional[str] = None,
    spoke_dialogue: Optional[str] = None,
    image_names: Optional[List[str]] = None
) -> str:
    """Format structured HTML content for the WordPress post."""
    html_parts = []

    # Intro banner
    html_parts.append(
        f'<div class="promo-header" style="background:#f8f9fa; padding:20px; border-left:5px solid #fe2c55; border-radius:8px; margin-bottom:24px;">'
        f'<h2 style="margin-top:0;">{product_title}</h2>'
        f'<p style="color:#666; font-size:14px; margin-bottom:0;">Promosi Produk TikTok Shop Malaysia &bull; Kurasi Gaya & Pilihan Terbaik</p>'
        f'</div>'
    )

    # TikTok Copywriting / Highlights
    if caption_text:
        formatted_caption = caption_text.replace("\n", "<br>")
        html_parts.append(
            f'<div class="promo-caption" style="line-height:1.8; font-size:16px; margin-bottom:24px;">'
            f'<h3>Kelebihan & Tips Penggayaan</h3>'
            f'<div style="background:#ffffff; border:1px solid #e5e7eb; border-radius:8px; padding:18px;">'
            f'{formatted_caption}'
            f'</div>'
            f'</div>'
        )

    # Spoken Dialogue & Script Concept
    if spoke_dialogue:
        html_parts.append(
            f'<div class="promo-script" style="margin-bottom:24px;">'
            f'<h3>Konsep Skrip Video (Flow AI Promo)</h3>'
            f'<blockquote style="border-left:4px solid #000; padding-left:14px; color:#444; font-style:italic;">'
            f'{spoke_dialogue}'
            f'</blockquote>'
            f'</div>'
        )

    # CTA Button to TikTok Shop
    target_link = product_url or "https://www.tiktok.com"
    html_parts.append(
        f'<div class="promo-cta" style="text-align:center; margin:35px 0;">'
        f'<a href="{target_link}" target="_blank" rel="noopener noreferrer" style="background:#fe2c55; color:#fff; font-weight:bold; padding:14px 28px; text-decoration:none; border-radius:50px; font-size:17px; display:inline-block; box-shadow:0 4px 14px rgba(254,44,85,0.4);">'
        f'🛒 Dapatkan Di TikTok Shop (Beg Kuning)'
        f'</a>'
        f'<p style="font-size:12px; color:#888; margin-top:8px;">Ketik pautan di atas untuk semak pilihan saiz dan promosi terkini.</p>'
        f'</div>'
    )

    # Policy & AIGC Disclosure
    html_parts.append(
        f'<hr style="border:none; border-top:1px solid #eee; margin:30px 0;">'
        f'<p style="font-size:12px; color:#999; text-align:center;">'
        f'<em>Kandungan ini disediakan melalui Gemini Flow AI Assistant bagi tujuan promosi produk TikTok Shop secara patuh polisi.</em>'
        f'</p>'
    )

    return "\n".join(html_parts)


def create_post(
    title: str,
    content_html: str,
    status: str = "draft",
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Submit a new post to the WordPress REST API."""
    auth = get_auth_header()
    if not auth:
        return {"error": "Missing WordPress credentials."}

    site = get_site_domain()
    url = f"https://public-api.wordpress.com/wp/v2/sites/{site}/posts"
    headers = {
        "Authorization": auth,
        "User-Agent": "GeminiFlow-Antigravity/1.0",
        "Content-Type": "application/json"
    }

    payload = {
        "title": title,
        "content": content_html,
        "status": status,
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "post_id": data.get("id"),
                "post_url": data.get("link"),
                "status": data.get("status"),
                "title": data.get("title", {}).get("rendered")
            }
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        return {
            "success": False,
            "http_code": e.code,
            "error": err_msg
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Publish TikTok promos to WordPress")
    parser.add_argument("--test", action="store_true", help="Test WordPress credentials and connection")
    parser.add_argument("--session", type=str, help="Path to scraped output session folder")
    parser.add_argument("--latest", action="store_true", help="Publish latest output session")
    parser.add_argument("--status", type=str, default="draft", choices=["draft", "publish", "pending"], help="Post status")
    args = parser.parse_args()

    if args.test:
        print(f"Connecting to {WP_SITE_URL} as {WP_USER}...")
        res = test_connection()
        print(json.dumps(res, indent=2))
        return

    output_dir = WORKSPACE / "output"
    target_session = None

    if args.session:
        target_session = Path(args.session)
    elif args.latest:
        subdirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)
        if subdirs:
            target_session = subdirs[0]

    if not target_session or not target_session.exists():
        print("Usage: python publish_to_wordpress.py [--test | --latest | --session <path>]")
        return

    info_file = target_session / "product_info.json"
    if not info_file.exists():
        print(f"No product_info.json found in {target_session}")
        return

    with open(info_file, "r", encoding="utf-8") as f:
        info = json.load(f)

    title = info.get("title", "TikTok Shop Promosi Produk")
    caption = info.get("page_text", "")
    url = info.get("url")

    html = format_html_post(
        product_title=title,
        caption_text=caption,
        product_url=url
    )

    print(f"Publishing post for '{title[:50]}' as {args.status}...")
    res = create_post(title=title, content_html=html, status=args.status)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
