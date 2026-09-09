"""
WordPress Publisher Module for Gemini Flow
==========================================
Publishes generated TikTok product promos, keyframe visuals, and the Gemini Flow
Webapp landing portal directly to WordPress.com using XML-RPC and REST API.

Usage:
    python publish_to_wordpress.py --test
    python publish_to_wordpress.py --webapp --status publish
    python publish_to_wordpress.py --latest --status publish
    python publish_to_wordpress.py --session output/20260907_160155
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import xmlrpc.client
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

WP_SITE_URL = os.getenv("WP_SITE_URL", "")
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "").replace(" ", "")
WP_BLOG_ID = int(os.getenv("WP_BLOG_ID", "0")) if os.getenv("WP_BLOG_ID") else 0


def get_site_domain() -> str:
    """Extract clean domain/slug for WordPress.com endpoint."""
    domain = WP_SITE_URL.replace("http://", "").replace("https://", "").strip("/")
    return domain


def get_xmlrpc_server() -> xmlrpc.client.ServerProxy:
    """Initialize XML-RPC server proxy."""
    xmlrpc_url = f"https://{get_site_domain()}/xmlrpc.php"
    return xmlrpc.client.ServerProxy(xmlrpc_url)


def test_connection() -> Dict[str, Any]:
    """Test connection and read access to the WordPress.com site via XML-RPC."""
    try:
        server = get_xmlrpc_server()
        blogs = server.wp.getUsersBlogs(WP_USER, WP_APP_PASSWORD)
        target_blog = next((b for b in blogs if str(b.get("blogid")) == str(WP_BLOG_ID) or get_site_domain() in b.get("url", "")), None)
        if not target_blog and blogs:
            target_blog = blogs[0]

        posts = server.wp.getPosts(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, {"number": 5, "post_type": "post"})
        return {
            "status": "connected",
            "site": get_site_domain(),
            "user": WP_USER,
            "blog_name": target_blog.get("blogName") if target_blog else "N/A",
            "blog_id": target_blog.get("blogid") if target_blog else WP_BLOG_ID,
            "existing_posts_count": len(posts)
        }
    except Exception as e:
        return {
            "status": "failed",
            "site": get_site_domain(),
            "error": str(e)
        }


def upload_media_file(image_path: Path) -> Optional[str]:
    """Upload an image file to WordPress Media Library via XML-RPC."""
    if not image_path.exists():
        return None
    try:
        server = get_xmlrpc_server()
        with open(image_path, "rb") as f:
            data = f.read()

        file_payload = {
            "name": image_path.name,
            "type": "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png",
            "bits": xmlrpc.client.Binary(data),
            "overwrite": True
        }
        res = server.wp.uploadFile(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, file_payload)
        url = res.get("url")
        print(f"  📤 Uploaded {image_path.name} -> {url}")
        return url
    except Exception as e:
        print(f"  ⚠️ Media upload failed for {image_path.name}: {e}")
        return None


def format_webapp_html() -> str:
    """Build a comprehensive, modern landing page for the Gemini Flow Webapp."""
    return """
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 860px; margin: 0 auto; color: #1e293b; line-height: 1.7;">

  <!-- Hero Header -->
  <div style="background: linear-gradient(135deg, #18181b 0%, #09090b 100%); color: #ffffff; padding: 48px 36px; border-radius: 16px; margin-bottom: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.15); text-align: center;">
    <div style="display: inline-block; background: rgba(254,44,85,0.15); border: 1px solid rgba(254,44,85,0.4); color: #fe2c55; font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; padding: 6px 16px; border-radius: 50px; margin-bottom: 16px;">
      ✨ AI TikTok Shop Automation
    </div>
    <h1 style="font-size: 38px; font-weight: 800; margin: 0 0 16px 0; color: #ffffff; letter-spacing: -0.5px;">
      Gemini Flow Webapp
    </h1>
    <p style="font-size: 18px; color: #94a3b8; max-width: 620px; margin: 0 auto 28px auto;">
      Sistem penjana video promosi, visual konsisten 9:16, dan salinan iklan TikTok Shop khas untuk pasaran Malaysia.
    </p>
    <div style="display: flex; justify-content: center; gap: 12px; flex-wrap: wrap;">
      <span style="background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;">⚡ 1-Click PDP Scraper</span>
      <span style="background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;">🛡️ TikTok Policy Shield</span>
      <span style="background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;">🎬 Flow AI 3-Act Video</span>
      <span style="background: rgba(255,255,255,0.1); padding: 8px 18px; border-radius: 8px; font-size: 14px; font-weight: 600;">🎵 Suno Instrumental BGM</span>
    </div>
  </div>

  <!-- Highlights Grid -->
  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 40px;">
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;">
      <h3 style="margin-top: 0; color: #0f172a; font-size: 18px;">📸 3 Keyframe Visual Konsisten</h3>
      <p style="font-size: 14px; color: #64748b; margin-bottom: 0;">Menghasilkan 3 pose konsisten (Depan, Sisi, dan Pandangan Bahu) model Muslimah Malaysia berhijab moden mengikut perincian fabrik dan potongan produk sebenar.</p>
    </div>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;">
      <h3 style="margin-top: 0; color: #0f172a; font-size: 18px;">🗣️ Skrip Lip-Sync Bahasa Melayu</h3>
      <p style="font-size: 14px; color: #64748b; margin-bottom: 0;">Skrip perbualan natural 3-babak (8 saat setiap babak) dialek KL Malaysia tulen. Tiada bahasa Indonesia, tiada 'fake hype' — persis syor ikhlas seorang rakan.</p>
    </div>
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px;">
      <h3 style="margin-top: 0; color: #0f172a; font-size: 18px;">🎯 Kapsyen & Hashtag SEO Beg Kuning</h3>
      <p style="font-size: 14px; color: #64748b; margin-bottom: 0;">Salinan iklan patuh dasar TikTok Shop (tiada sebutan harga langsung untuk elak sekatan) dengan 4-6 hashtag berimpak tinggi dan CTA jelas ke Beg Kuning.</p>
    </div>
  </div>

  <!-- End-to-End Workflow Section -->
  <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; margin-bottom: 40px;">
    <h2 style="margin-top: 0; font-size: 24px; color: #0f172a; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px;">
      🔄 Aliran Kerja End-to-End Webapp
    </h2>
    <ol style="padding-left: 20px; font-size: 15px; color: #334155;">
      <li style="margin-bottom: 16px;">
        <strong>Langkah 0: Pre-Flight Policy Gate</strong> — Sistem menyemak pautan dan kategori produk dengan pangkalan data polisi TikTok Shop Malaysia bagi memastikan pematuhan penuh AIGC, tiada tuntutan kesihatan melampau, dan kategori dibenarkan.
      </li>
      <li style="margin-bottom: 16px;">
        <strong>Langkah 1: Scrape Produk Automatik</strong> — Menukarkan pautan pendek <code>vt.tiktok.com</code> kepada halaman penuh, mengekstrak maklumat fabrik, warna, potongan serta memuat turun gambar katalog definisi tinggi.
      </li>
      <li style="margin-bottom: 16px;">
        <strong>Langkah 2: Penjanaan Imej Keyframe (9:16)</strong> — Menjana 3 imej berkualiti tinggi yang mengekalkan konsistensi watak, pakaian, dan pencahayaan 'golden-hour daylight'.
      </li>
      <li style="margin-bottom: 16px;">
        <strong>Langkah 3: Skrip Dialog Organik & Anti-Pengulangan</strong> — Mengimbas rekod 7 promosi terdahulu bagi memastikan setiap ayat pembuka dan penutup adalah segar dan tidak berulang.
      </li>
      <li style="margin-bottom: 16px;">
        <strong>Langkah 4: Prompt Muzik Latar Suno AI</strong> — Prompt instrumental lengkap (105-115 BPM, Lo-Fi acoustic/chill pop) tanpa vokal agar tidak mengganggu audio suara Melayu Flow AI.
      </li>
      <li style="margin-bottom: 0;">
        <strong>Langkah 5: Pakej Siap Salin 1-Klik & Eksport ZIP</strong> — Semua prompt dan kapsyen dibungkus di dalam kotak kod yang mudah disalin sekali klik, atau dimuat turun sebagai fail ZIP.
      </li>
    </ol>
  </div>

  <!-- Quickstart & Access -->
  <div style="background: #f1f5f9; border-radius: 12px; padding: 24px; margin-bottom: 40px; text-align: center;">
    <h3 style="margin-top: 0; color: #0f172a;">🚀 Akses & Penggunaan Aplikasi Tempatan</h3>
    <p style="font-size: 15px; color: #475569; max-width: 580px; margin: 0 auto 20px auto;">
      Webapp ini boleh dijalankan secara setempat di komputer atau diakses melalui telefon pintar dalam rangkaian Wi-Fi yang sama:
    </p>
    <div style="background: #0f172a; color: #38bdf8; font-family: monospace; padding: 14px; border-radius: 8px; font-size: 15px; display: inline-block; margin-bottom: 14px;">
      python webapp.py
    </div>
    <p style="font-size: 13px; color: #64748b; margin-bottom: 0;">Buka pelayar web: <strong>http://localhost:5000</strong></p>
  </div>

  <!-- Footer Disclaimer -->
  <div style="text-align: center; border-top: 1px solid #e2e8f0; padding-top: 24px; color: #94a3b8; font-size: 13px;">
    <p style="margin-bottom: 4px;">🛡️ <em>Semua kandungan yang dijana diselaraskan dengan garis panduan AIGC TikTok Shop Malaysia.</em></p>
    <p style="margin: 0;">Gemini Flow &bull; Automasi Pemasaran TikTok Shop Berkuasa AI</p>
  </div>

</div>
"""


def format_promo_html(
    product_title: str,
    caption_text: str,
    product_url: Optional[str] = None,
    spoke_dialogue: Optional[str] = None,
    image_urls: Optional[List[str]] = None
) -> str:
    """Format structured HTML content for a product promo post."""
    html_parts = []

    # Header
    html_parts.append(
        f'<div style="background:#f8fafc; padding:24px; border-left:6px solid #fe2c55; border-radius:12px; margin-bottom:28px;">'
        f'<h2 style="margin-top:0; color:#0f172a; font-size:24px;">{product_title}</h2>'
        f'<p style="color:#64748b; font-size:14px; margin-bottom:0;">Kurasi Promosi TikTok Shop Malaysia &bull; Visual Patuh Polisi & Gaya Moden</p>'
        f'</div>'
    )

    # Keyframes Gallery
    if image_urls:
        html_parts.append('<div style="display:flex; gap:12px; justify-content:center; flex-wrap:wrap; margin:28px 0;">')
        for i, url in enumerate(image_urls, 1):
            label = "Frame 1: Pandangan Hadapan" if i == 1 else ("Frame 2: Profil Sisi" if i == 2 else "Frame 3: Pandangan Bahu")
            html_parts.append(
                f'<div style="flex:1; min-width:220px; max-width:270px; text-align:center;">'
                f'<img src="{url}" alt="{label}" style="width:100%; border-radius:10px; box-shadow:0 4px 12px rgba(0,0,0,0.08); aspect-ratio:9/16; object-fit:cover;" />'
                f'<p style="font-size:12px; color:#64748b; margin-top:6px; font-weight:600;">{label}</p>'
                f'</div>'
            )
        html_parts.append('</div>')

    # Caption & Highlights
    if caption_text:
        formatted_caption = caption_text.replace("\n", "<br>")
        html_parts.append(
            f'<div style="margin:28px 0;">'
            f'<h3 style="color:#0f172a; font-size:18px; margin-bottom:12px;">✨ Sorotan Produk & Tips Penggayaan</h3>'
            f'<div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:20px; font-size:15px; line-height:1.8; color:#334155;">'
            f'{formatted_caption}'
            f'</div>'
            f'</div>'
        )

    # Spoken Script Concept
    if spoke_dialogue:
        html_parts.append(
            f'<div style="margin:28px 0;">'
            f'<h3 style="color:#0f172a; font-size:18px; margin-bottom:12px;">🎬 Konsep Skrip Video Lip-Sync (Bahasa Melayu)</h3>'
            f'<blockquote style="background:#f1f5f9; border-left:4px solid #0f172a; padding:16px; border-radius:6px; font-size:15px; color:#1e293b; margin:0; font-style:italic;">'
            f'{spoke_dialogue}'
            f'</blockquote>'
            f'</div>'
        )

    # CTA
    target_link = product_url or "https://www.tiktok.com"
    html_parts.append(
        f'<div style="text-align:center; margin:36px 0;">'
        f'<a href="{target_link}" target="_blank" rel="noopener noreferrer" style="background:#fe2c55; color:#ffffff; font-weight:bold; padding:16px 36px; text-decoration:none; border-radius:50px; font-size:16px; display:inline-block; box-shadow:0 6px 18px rgba(254,44,85,0.35);">'
        f'🛒 Semak Pilihan Di Beg Kuning TikTok Shop'
        f'</a>'
        f'<p style="font-size:12px; color:#94a3b8; margin-top:8px;">Ketik pautan untuk saiz dan warna terkini di TikTok Shop.</p>'
        f'</div>'
    )

    return "\n".join(html_parts)


def publish_webapp_page(status: str = "publish") -> Dict[str, Any]:
    """Publish or update the main Gemini Flow Webapp landing presentation."""
    server = get_xmlrpc_server()
    title = "Gemini Flow — TikTok Shop Product Promo Generator Webapp"
    content = format_webapp_html()

    # Check if a page or post with this title already exists
    existing_posts = server.wp.getPosts(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, {"number": 20, "post_type": "post"})
    existing_post = next((p for p in existing_posts if "Gemini Flow" in p.get("post_title", "")), None)

    post_payload = {
        "post_type": "post",
        "post_status": status,
        "post_title": title,
        "post_content": content,
        "terms_names": {
            "category": ["Aplikasi Web", "TikTok Shop"],
            "post_tag": ["Gemini Flow", "TikTok Affiliate", "AIGC", "Video Generator"]
        }
    }

    if existing_post:
        post_id = existing_post.get("post_id")
        server.wp.editPost(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, post_id, post_payload)
        link = existing_post.get("link")
        print(f"✅ Updated existing Webapp feature post ID {post_id} -> {link}")
        return {"success": True, "action": "updated", "post_id": post_id, "url": link}
    else:
        post_id = server.wp.newPost(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, post_payload)
        new_post = server.wp.getPost(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, post_id)
        link = new_post.get("link") if new_post else f"https://{get_site_domain()}/?p={post_id}"
        print(f"✅ Created new Webapp feature post ID {post_id} -> {link}")
        return {"success": True, "action": "created", "post_id": post_id, "url": link}


def publish_session_promo(session_dir: Path, status: str = "publish") -> Dict[str, Any]:
    """Publish a single scraped output session to WordPress."""
    info_file = session_dir / "product_info.json"
    if not info_file.exists():
        return {"error": f"No product_info.json in {session_dir}"}

    with open(info_file, "r", encoding="utf-8") as f:
        info = json.load(f)

    title = info.get("title", "TikTok Shop Promosi Produk")
    caption = info.get("page_text", "")
    url = info.get("url")

    # Locate keyframe images matching this session or product
    import glob
    kf_dir = WORKSPACE / "keyframes"
    # Find matching images or take top 3
    kf_matches = sorted(list(kf_dir.glob("*.jpg")))[:3]
    uploaded_urls = []
    for kf in kf_matches:
        img_url = upload_media_file(kf)
        if img_url:
            uploaded_urls.append(img_url)

    html = format_promo_html(
        product_title=title,
        caption_text=caption,
        product_url=url,
        image_urls=uploaded_urls
    )

    server = get_xmlrpc_server()
    post_payload = {
        "post_type": "post",
        "post_status": status,
        "post_title": title,
        "post_content": html,
        "terms_names": {
            "category": ["Koleksi Fesyen", "TikTok Shop"],
            "post_tag": ["Beg Kuning", "Muslimah Style", "OOTD Malaysia"]
        }
    }

    post_id = server.wp.newPost(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, post_payload)
    new_post = server.wp.getPost(WP_BLOG_ID, WP_USER, WP_APP_PASSWORD, post_id)
    link = new_post.get("link") if new_post else f"https://{get_site_domain()}/?p={post_id}"
    print(f"🎉 Published promo post ID {post_id} -> {link}")
    return {"success": True, "post_id": post_id, "url": link}


def main():
    parser = argparse.ArgumentParser(description="Publish Gemini Flow to WordPress")
    parser.add_argument("--test", action="store_true", help="Test WordPress credentials and connection")
    parser.add_argument("--webapp", action="store_true", help="Publish the complete Webapp landing presentation")
    parser.add_argument("--latest", action="store_true", help="Publish latest scraped product promo")
    parser.add_argument("--session", type=str, help="Path to specific output session folder")
    parser.add_argument("--status", type=str, default="publish", choices=["publish", "draft", "pending"], help="Post status")
    args = parser.parse_args()

    if args.test:
        print(f"Connecting to {WP_SITE_URL} via XML-RPC as {WP_USER}...")
        res = test_connection()
        print(json.dumps(res, indent=2))
        return

    if args.webapp:
        print(f"Publishing Gemini Flow Webapp landing presentation to {WP_SITE_URL} ({args.status})...")
        res = publish_webapp_page(status=args.status)
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

    if target_session and target_session.exists():
        print(f"Publishing promo from session {target_session.name} to {WP_SITE_URL} ({args.status})...")
        res = publish_session_promo(target_session, status=args.status)
        print(json.dumps(res, indent=2))
        return

    # If no flag specified, default to publishing webapp
    print(f"No specific flag passed. Publishing Gemini Flow Webapp portal to {WP_SITE_URL}...")
    res = publish_webapp_page(status=args.status)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
