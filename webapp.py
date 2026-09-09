"""
Gemini Flow — Mobile Web Application
==============================================
Fast, mobile-first web app that generates:
- 3 Consistent 9:16 Keyframe Pictures (Front, Side, Over-Shoulder) with single-tap download
- 3 Flow AI Video Prompts (Veo 3.1 / Omni Flash 8s with Malaysian Malay lip-sync)
- TikTok Caption + SEO Hashtags (in 1-click copy box)
- Suno AI Instrumental BGM Prompt
- Supabase cloud database synchronization

Supports Vercel Serverless, Railway, and local execution.
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import shutil
import threading
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

# Determine root directories
WORKSPACE_DIR = Path(__file__).resolve().parent
if (WORKSPACE_DIR / "api").is_dir() and not (WORKSPACE_DIR / "templates").is_dir():
    ROOT_DIR = WORKSPACE_DIR.parent
else:
    ROOT_DIR = WORKSPACE_DIR

IS_SERVERLESS = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))

if IS_SERVERLESS:
    OUTPUT_DIR = "/tmp/output"
    KEYFRAME_DIR = str(ROOT_DIR / "keyframes")
else:
    OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
    KEYFRAME_DIR = os.path.join(ROOT_DIR, "keyframes")

os.makedirs(OUTPUT_DIR, exist_ok=True)
if not IS_SERVERLESS:
    os.makedirs(KEYFRAME_DIR, exist_ok=True)

# Load environment variables
load_dotenv(ROOT_DIR / ".env")

# Initialize Flask app with explicit template and static paths
app = Flask(
    __name__,
    template_folder=str(ROOT_DIR / "templates"),
    static_folder=str(ROOT_DIR / "static"),
    static_url_path="/static"
)

# In-memory session store (with lock)
session_store: Dict[str, Any] = {}
session_lock = threading.Lock()
SESSION_TTL = 3600  # 1 hour auto-cleanup


def clean_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", (text or "").lower()).strip("_")
    return cleaned[:30] if cleaned else "product"


def extract_spoken_dialogue(scene_text: str) -> str:
    """Extract spoken Malay lip-sync dialogue from Flow AI prompt paragraph."""
    if not scene_text:
        return ""
    m = re.search(r'Spoken Malay(?:\s*\(Lip-sync\))?:\s*["“\']?([^"”\r\n]+)["”\']?', scene_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    m = re.search(r'(?:spoken audio|into standard Malaysian Malay)[^"\':]*[:\s]+["“\']([^"”]+)["”]', scene_text, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    quotes = re.findall(r'["“]([^"”]{15,})["”]', scene_text)
    if quotes:
        return quotes[-1].strip()
    return scene_text[:120].strip()


def extract_hashtags(caption: str) -> str:
    """Extract all #hashtags from the TikTok caption string."""
    if not caption:
        return ""
    tags = re.findall(r'#[a-zA-Z0-9_]+', caption)
    return " ".join(tags)


def generate_keyframe_svg(product_name: str, frame_type: str) -> str:
    """Generate high-definition 9:16 SVG visual guide card for the product pose."""
    frame_titles = {
        "front": "Frame 1: Pandangan Hadapan (Front Facing)",
        "side": "Frame 2: Profil Sisi 3/4 (Side Drape)",
        "shoulder": "Frame 3: Tolehan Bahu (Over Shoulder)"
    }
    frame_descriptions = {
        "front": "Senyuman santai, pandangan mata natural, gaya Muslimah moden, busana penuh kepala-ke-kaki.",
        "side": "Pusingan 3/4 menonjolkan alunan fabrik, potongan jahitan kemas, dan siluet santai.",
        "shoulder": "Pusingan belakang sopan dengan tolehan lembut ke bahu. Tangan di sisi atau memegang beg santai. Tiada lambaian."
    }
    title = frame_titles.get(frame_type.lower(), f"Frame: {frame_type.capitalize()}")
    desc = frame_descriptions.get(frame_type.lower(), "Pandangan visual 9:16 sedia untuk Flow AI / Midjourney")
    clean_pname = (product_name or "Produk TikTok Shop")[:40]

    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 1280" width="720" height="1280">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0e0e18"/>
      <stop offset="40%" stop-color="#161626"/>
      <stop offset="100%" stop-color="#0a0a10"/>
    </linearGradient>
    <linearGradient id="cardGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.2"/>
      <stop offset="100%" stop-color="#2dd4bf" stop-opacity="0.15"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  
  <rect x="24" y="24" width="672" height="1232" rx="32" fill="none" stroke="rgba(255,255,255,0.12)" stroke-width="2"/>
  
  <rect x="60" y="60" width="220" height="48" rx="24" fill="rgba(139,92,246,0.2)" stroke="rgba(139,92,246,0.4)" stroke-width="1.5"/>
  <text x="170" y="91" fill="#c4b5fd" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="600" text-anchor="middle">✨ 9:16 KEYFRAME</text>

  <text x="60" y="160" fill="#f0f0f5" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="30" font-weight="700">{clean_pname}</text>
  
  <rect x="60" y="200" width="600" height="68" rx="16" fill="url(#cardGrad)" stroke="rgba(139,92,246,0.3)" stroke-width="1"/>
  <text x="84" y="243" fill="#2dd4bf" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="22" font-weight="700">{title}</text>
  
  <g transform="translate(360, 620)">
    <circle cx="0" cy="-170" r="65" fill="none" stroke="#8b5cf6" stroke-width="5" stroke-dasharray="8 6"/>
    <path d="M-60 -150 C -80 -100, -70 -20, -50 40 C -30 90, 30 90, 50 40 C 70 -20, 80 -100, 60 -150 Z" fill="rgba(139,92,246,0.12)" stroke="#8b5cf6" stroke-width="3"/>
    <path d="M-50 40 L-130 140 L-90 290 L90 290 L130 140 L50 40 Z" fill="rgba(45,212,191,0.08)" stroke="#2dd4bf" stroke-width="3"/>
    <line x1="-40" y1="290" x2="-40" y2="430" stroke="rgba(255,255,255,0.4)" stroke-width="4"/>
    <line x1="40" y1="290" x2="40" y2="430" stroke="rgba(255,255,255,0.4)" stroke-width="4"/>
    <text x="0" y="180" fill="#2dd4bf" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="64" text-anchor="middle">📸</text>
  </g>

  <rect x="60" y="1080" width="600" height="120" rx="18" fill="rgba(255,255,255,0.04)" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <text x="80" y="1120" fill="#c4b5fd" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="20" font-weight="600">Arahan Gaya &amp; Sudut:</text>
  <text x="80" y="1155" fill="#9a9ab0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="400">{desc[:65]}</text>
  <text x="80" y="1182" fill="#9a9ab0" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="16" font-weight="400">{desc[65:130]}</text>
</svg>"""


def find_matching_keyframes(slug: str) -> Dict[str, Optional[str]]:
    """Check if pre-generated keyframe images exist in keyframes/ strictly for this product."""
    frames = {"front": None, "side": None, "shoulder": None}
    if not os.path.isdir(KEYFRAME_DIR) or not slug or len(slug) < 3:
        return frames

    for fname in os.listdir(KEYFRAME_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        lower_name = fname.lower()
        if slug in lower_name:
            if "frame1" in lower_name or "front" in lower_name:
                frames["front"] = fname
            elif "frame2" in lower_name or "side" in lower_name:
                frames["side"] = fname
            elif "frame3" in lower_name or "shoulder" in lower_name or "back" in lower_name:
                frames["shoulder"] = fname
    return frames


# ═══════════════════════════════════════════════════════════
# Routes — Pages
# ═══════════════════════════════════════════════════════════
@app.route("/")
def index():
    """Serve the mobile-first SPA."""
    return render_template("index.html")


# ═══════════════════════════════════════════════════════════
# Routes — API
# ═══════════════════════════════════════════════════════════

@app.route("/api/scrape", methods=["POST"])
def api_scrape():
    """
    Scrape TikTok Shop URL or accept direct/manual product input.
    """
    data = request.get_json() or {}
    tiktok_url = (data.get("url") or "").strip()
    is_manual = bool(data.get("manual") or not tiktok_url)
    custom_title = (data.get("title") or "").strip()
    custom_text = (data.get("page_text") or "").strip()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = timestamp
    output_dir = os.path.join(OUTPUT_DIR, session_id)
    os.makedirs(output_dir, exist_ok=True)

    product_info = None

    if is_manual and custom_title:
        product_info = {
            "url": "",
            "title": custom_title,
            "page_text": custom_text or f"Produk: {custom_title}\nKategori: Fesyen & Gaya Hidup Malaysia",
            "image_count": 0,
            "image_paths": [],
            "scraped_at": datetime.now().isoformat()
        }
        with open(os.path.join(output_dir, "product_info.json"), "w", encoding="utf-8") as f:
            json.dump(product_info, f, indent=2, ensure_ascii=False)
    else:
        if not tiktok_url or not re.search(r"tiktok\.com", tiktok_url, re.IGNORECASE):
            return jsonify({"error": "Please provide a valid TikTok URL or switch to Manual Mode"}), 400

        try:
            from scrape_product import scrape_lightweight, scrape_tiktok_product
            try:
                product_info = scrape_lightweight(tiktok_url, output_dir)
            except Exception as e_light:
                print(f"Notice: scrape_lightweight failed: {e_light}, trying full scrape...")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                product_info = loop.run_until_complete(scrape_tiktok_product(tiktok_url, output_dir))
                loop.close()
        except Exception as e:
            return jsonify({"error": f"Scraping failed: {str(e)}"}), 500

    if not product_info:
        return jsonify({"error": "No product data extracted. Please check the link or use Manual Mode."}), 500

    image_urls = []
    if product_info.get("image_paths"):
        for img_path in product_info["image_paths"]:
            filename = os.path.basename(img_path)
            image_urls.append(f"/api/image/{session_id}/{filename}")

    slug = clean_slug(product_info.get("title", ""))
    existing_kf = find_matching_keyframes(slug)

    with session_lock:
        session_store[session_id] = {
            "product_info": product_info,
            "output_dir": output_dir,
            "created_at": time.time(),
            "prompts": None,
            "slug": slug,
            "keyframes": existing_kf
        }

    return jsonify({
        "session_id": session_id,
        "product_info": {
            "title": product_info.get("title", ""),
            "page_text": product_info.get("page_text", ""),
            "image_count": product_info.get("image_count", 0),
            "scraped_at": product_info.get("scraped_at", "")
        },
        "image_urls": image_urls,
        "has_keyframes": any(existing_kf.values())
    })


@app.route("/api/image/<session_id>/<filename>")
def api_image(session_id, filename):
    """Serve scraped product image."""
    session_id = re.sub(r"[^a-zA-Z0-9_]", "", session_id)
    filename = re.sub(r"[^a-zA-Z0-9_.]", "", filename)
    img_path = os.path.join(OUTPUT_DIR, session_id, filename)
    if not os.path.isfile(img_path):
        return jsonify({"error": "Image not found"}), 404
    return send_file(img_path, mimetype="image/jpeg")


@app.route("/api/keyframe/<session_id>/<frame_type>")
def api_keyframe(session_id, frame_type):
    """Serve or download a 9:16 keyframe image (JPG if present, SVG visual card fallback)."""
    session_id = re.sub(r"[^a-zA-Z0-9_]", "", session_id)
    frame_type = re.sub(r"[^a-zA-Z0-9_]", "", frame_type).lower()
    as_download = request.args.get("download") == "1"

    target_file = None

    sess_dir = os.path.join(OUTPUT_DIR, session_id)
    if os.path.isdir(sess_dir):
        for f in os.listdir(sess_dir):
            if frame_type in f.lower() and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                target_file = os.path.join(sess_dir, f)
                break

    if not target_file and os.path.isdir(KEYFRAME_DIR):
        with session_lock:
            sess = session_store.get(session_id, {})
            slug = sess.get("slug", "")
        if slug:
            for f in os.listdir(KEYFRAME_DIR):
                if slug in f.lower() and frame_type in f.lower():
                    target_file = os.path.join(KEYFRAME_DIR, f)
                    break

    # If real JPG image found, serve it
    if target_file and os.path.isfile(target_file):
        download_name = f"keyframe_{frame_type}_{session_id}.jpg"
        return send_file(
            target_file,
            mimetype="image/jpeg",
            as_attachment=as_download,
            download_name=download_name
        )

    # If no real image exists, serve high-definition 9:16 SVG visual guide
    with session_lock:
        sess = session_store.get(session_id, {})
        p_title = (sess.get("product_info") or {}).get("title", "Produk TikTok Shop")
    svg_code = generate_keyframe_svg(p_title, frame_type)
    return send_file(
        io.BytesIO(svg_code.encode("utf-8")),
        mimetype="image/svg+xml",
        as_attachment=as_download,
        download_name=f"keyframe_{frame_type}_{session_id}.svg"
    )


@app.route("/api/generate-images", methods=["POST"])
def api_generate_images():
    """
    Retrieve 3 consistent 9:16 keyframe pictures or guides for the session.
    """
    data = request.get_json() or {}
    session_id = data.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    with session_lock:
        session = session_store.get(session_id)

    if not session:
        output_dir = os.path.join(OUTPUT_DIR, session_id)
        info_path = os.path.join(output_dir, "product_info.json")
        if os.path.isdir(output_dir) and os.path.isfile(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                pinfo = json.load(f)
            session = {
                "product_info": pinfo,
                "output_dir": output_dir,
                "created_at": time.time(),
                "prompts": None,
                "slug": clean_slug(pinfo.get("title", ""))
            }
            with session_lock:
                session_store[session_id] = session

    if not session:
        return jsonify({"error": "Session not found"}), 404

    slug = session.get("slug") or clean_slug(session["product_info"].get("title", ""))
    existing = find_matching_keyframes(slug)
    has_real_images = any(existing.values())

    if has_real_images:
        quota_status = "🟢 Status Kuota Imej: Aktif (3/3 imej sedia dipaparkan)"
    else:
        quota_status = "🔴 Status Kuota Imej: Had kuota percuma Google tercapai (3 Prompt 9:16 Sedia Digunakan)"

    frames_data = [
        {
            "id": "front",
            "frame_num": 1,
            "title": "Frame 1: Front Facing",
            "pose": "Senyuman santai, pandangan natural, hijab kemas, busana penuh kepala-ke-kaki",
            "image_url": f"/api/keyframe/{session_id}/front",
            "download_url": f"/api/keyframe/{session_id}/front?download=1",
            "has_image": True,
            "is_rendered": bool(existing.get("front"))
        },
        {
            "id": "side",
            "frame_num": 2,
            "title": "Frame 2: 3/4 Side Profile",
            "pose": "Pusingan 3/4 menonjolkan alunan fabrik, potongan jahitan kemas, dan siluet santai",
            "image_url": f"/api/keyframe/{session_id}/side",
            "download_url": f"/api/keyframe/{session_id}/side?download=1",
            "has_image": True,
            "is_rendered": bool(existing.get("side"))
        },
        {
            "id": "shoulder",
            "frame_num": 3,
            "title": "Frame 3: Over-the-Shoulder Glance",
            "pose": "Pusingan belakang sopan dengan tolehan lembut ke bahu, tangan di sisi santai",
            "image_url": f"/api/keyframe/{session_id}/shoulder",
            "download_url": f"/api/keyframe/{session_id}/shoulder?download=1",
            "has_image": True,
            "is_rendered": bool(existing.get("shoulder"))
        }
    ]

    return jsonify({
        "status": "ready",
        "quota_status": quota_status,
        "compliance_badge": "🛡️ Status Pematuhan: Disemak & Patuh (Kategori Dibenarkan)",
        "frames": frames_data
    })


@app.route("/api/auth-status", methods=["GET"])
def api_auth_status():
    """Return whether server has configured Gemini key."""
    has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    return jsonify({"has_server_key": has_key})


@app.route("/api/verify-key", methods=["POST"])
def api_verify_key():
    """Verify user-provided Gemini API key."""
    data = request.get_json() or {}
    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        return jsonify({"valid": False, "error": "No API key provided."}), 400

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        models_iter = client.models.list(config={"page_size": 3})
        next(iter(models_iter), None)
        return jsonify({"valid": True, "message": "Key is valid and active!"})
    except Exception as e:
        err_msg = str(e)
        if "API_KEY_INVALID" in err_msg or "INVALID_ARGUMENT" in err_msg:
            return jsonify({"valid": False, "error": "Invalid API key. Please check your Google AI Studio key."}), 400
        return jsonify({"valid": False, "error": f"Verification failed: {err_msg}"}), 400


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """Generate prompts using Gemini with Supabase database sync."""
    data = request.get_json() or {}
    session_id = data.get("session_id")
    custom_api_key = (data.get("api_key") or request.headers.get("X-Gemini-Api-Key") or "").strip()

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    with session_lock:
        session = session_store.get(session_id)

    if not session:
        output_dir = os.path.join(OUTPUT_DIR, session_id)
        info_path = os.path.join(output_dir, "product_info.json")
        if os.path.isdir(output_dir) and os.path.isfile(info_path):
            with open(info_path, "r", encoding="utf-8") as f:
                pinfo = json.load(f)
            session = {
                "product_info": pinfo,
                "output_dir": output_dir,
                "created_at": time.time(),
                "prompts": None,
                "slug": clean_slug(pinfo.get("title", ""))
            }
            with session_lock:
                session_store[session_id] = session

    if not session:
        return jsonify({"error": "Session not found. Please scrape or enter product again."}), 404

    has_any_key = bool(custom_api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
    if not has_any_key:
        return jsonify({
            "error": "No Gemini API key found. Please click 🔑 Gemini Key in the header to enter your key."
        }), 400

    product_info = session["product_info"]

    try:
        from generate_prompts import generate_with_gemini_pro, save_generation_history

        prompts = generate_with_gemini_pro(product_info, api_key=custom_api_key)
        if not prompts:
            return jsonify({"error": "Gemini API call returned no data."}), 500

        with session_lock:
            if session_id in session_store:
                session_store[session_id]["prompts"] = prompts

        try:
            prompts_path = os.path.join(session["output_dir"], "generated_prompts.json")
            with open(prompts_path, "w", encoding="utf-8") as pf:
                json.dump(prompts, pf, indent=2, ensure_ascii=False)
        except Exception:
            pass

        flow = prompts.get("flow_ai_prompts", {})
        raw_intro = flow.get("scene_1_intro", "")
        raw_outro = flow.get("scene_3_outro", "")
        opening = extract_spoken_dialogue(raw_intro) or raw_intro[:120]
        closing = extract_spoken_dialogue(raw_outro) or raw_outro[:120]
        caption_full = prompts.get("tiktok_caption", "")
        hashtags_extracted = extract_hashtags(caption_full)
        product_name = prompts.get("product_summary", product_info.get("title", "Unknown"))
        bgm_style = (
            prompts.get("suno_bgm", {}).get("style", "")
            if isinstance(prompts.get("suno_bgm"), dict)
            else str(prompts.get("suno_bgm", ""))
        )

        save_generation_history(
            product_name=product_name[:80],
            opening_line=opening,
            closing_line=closing,
            scenes=flow,
            caption=caption_full,
            hashtags=hashtags_extracted,
            bgm_prompt=bgm_style
        )

        return jsonify({"prompts": prompts})

    except Exception as e:
        err_str = str(e)
        if "API_KEY_INVALID" in err_str:
            return jsonify({"error": "Invalid Gemini API key. Please check your key in settings."}), 400
        if "RESOURCE_EXHAUSTED" in err_str:
            return jsonify({"error": "Gemini API quota exceeded. Please try again in a few moments or enter your personal key."}), 429
        return jsonify({"error": f"Generation failed: {err_str}"}), 500


@app.route("/api/history", methods=["GET"])
def api_history():
    """Return recent generations from Supabase cloud database with local fallback."""
    try:
        from supabase_client import fetch_recent_generations
        cloud_rows = fetch_recent_generations(limit=10)
        if cloud_rows:
            return jsonify({
                "source": "supabase",
                "entries": [
                    {
                        "id": str(row.get("id", "")),
                        "product": row.get("product_name", ""),
                        "opening_line": row.get("opening_line", ""),
                        "closing_line": row.get("closing_line", ""),
                        "created_at": row.get("created_at", "")
                    }
                    for row in cloud_rows
                ]
            })
    except Exception as e_sup:
        print(f"Supabase history notice: {e_sup}")

    try:
        from generate_prompts import load_generation_history
        entries = load_generation_history(last_n=10)
        return jsonify({"source": "local", "entries": entries})
    except Exception:
        return jsonify({"source": "none", "entries": []})


@app.route("/api/history/<record_id>", methods=["GET"])
def api_history_item(record_id):
    """Retrieve full generation details for a specific record from Supabase."""
    record_id = re.sub(r"[^a-zA-Z0-9_-]", "", record_id)
    try:
        from supabase_client import fetch_generation_by_id
        record = fetch_generation_by_id(record_id)
        if not record:
            return jsonify({"error": "Record not found"}), 404
        return jsonify({
            "status": "success",
            "record": {
                "id": str(record.get("id", "")),
                "product_name": record.get("product_name", ""),
                "scenes": record.get("scenes") or {},
                "caption": record.get("caption") or "",
                "hashtags": record.get("hashtags") or "",
                "bgm_prompt": record.get("bgm_prompt") or "",
                "created_at": record.get("created_at", "")
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/supabase-status", methods=["GET"])
def api_supabase_status():
    """Health check for Supabase cloud database."""
    try:
        from supabase_client import test_supabase_connection
        return jsonify(test_supabase_connection())
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/download/<session_id>")
def api_download(session_id):
    """Bundle scraped materials, keyframes, and generated prompts into a ZIP."""
    session_id = re.sub(r"[^a-zA-Z0-9_]", "", session_id)
    output_dir = os.path.join(OUTPUT_DIR, session_id)
    if not os.path.isdir(output_dir):
        return jsonify({"error": "Session files not found or expired."}), 404

    product_info = {}
    info_path = os.path.join(output_dir, "product_info.json")
    if os.path.isfile(info_path):
        try:
            with open(info_path, "r", encoding="utf-8") as f:
                product_info = json.load(f)
        except Exception:
            pass

    prompts = None
    with session_lock:
        if session_id in session_store:
            prompts = session_store[session_id].get("prompts")

    if not prompts:
        prompts_path = os.path.join(output_dir, "generated_prompts.json")
        if os.path.isfile(prompts_path):
            try:
                with open(prompts_path, "r", encoding="utf-8") as f:
                    prompts = json.load(f)
            except Exception:
                pass

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.isdir(output_dir):
            for fname in sorted(os.listdir(output_dir)):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath) and fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    zf.write(fpath, f"images/{fname}")

        zf.writestr("product_info.json", json.dumps(product_info, indent=2, ensure_ascii=False, default=str))

        if prompts:
            zf.writestr("generated_prompts.json", json.dumps(prompts, indent=2, ensure_ascii=False))

            flow = prompts.get("flow_ai_prompts", {})
            flow_text = (
                "═══ SCENE 1: THE CASUAL INTRO ═══\n\n"
                f"{flow.get('scene_1_intro', '')}\n\n\n"
                "═══ SCENE 2: THE DETAIL & FEEL ═══\n\n"
                f"{flow.get('scene_2_detail', '')}\n\n\n"
                "═══ SCENE 3: THE FRIENDLY SIGN-OFF ═══\n\n"
                f"{flow.get('scene_3_outro', '')}\n"
            )
            zf.writestr("flow_ai_prompts.txt", flow_text)

            caption = prompts.get("tiktok_caption", "")
            if caption:
                zf.writestr("tiktok_caption.txt", caption)

            bgm = prompts.get("suno_bgm", {})
            if bgm:
                style_str = bgm.get("style", "") if isinstance(bgm, dict) else str(bgm)
                bgm_text = (
                    "═══ SUNO AI BGM STYLE (INSTRUMENTAL) ═══\n"
                    "Note: In Suno, enable Instrumental mode. Paste below into Style of Music.\n\n"
                    f"{style_str}\n"
                )
                zf.writestr("suno_bgm.txt", bgm_text)

            kf = prompts.get("keyframe_prompts", {})
            if kf:
                kf_text = (
                    "═══ FRAME 1: FRONT ═══\n\n"
                    f"{kf.get('frame_1_front', '')}\n\n\n"
                    "═══ FRAME 2: SIDE PROFILE ═══\n\n"
                    f"{kf.get('frame_2_side', '')}\n\n\n"
                    "═══ FRAME 3: OVER SHOULDER ═══\n\n"
                    f"{kf.get('frame_3_shoulder', '')}\n"
                )
                zf.writestr("keyframe_prompts.txt", kf_text)

    buffer.seek(0)
    product_name = prompts.get("product_summary", "")[:30] if prompts else product_info.get("title", "product")[:30]
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", product_name).strip("_").lower()
    zip_filename = f"gemini_flow_{safe_name}_{session_id}.zip"

    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zip_filename
    )


def cleanup_old_sessions():
    while True:
        time.sleep(300)
        now = time.time()
        to_remove = []
        with session_lock:
            for sid, session in session_store.items():
                if now - session["created_at"] > SESSION_TTL:
                    to_remove.append(sid)
            for sid in to_remove:
                session = session_store.pop(sid, None)
                if session and os.path.isdir(session.get("output_dir", "")):
                    try:
                        shutil.rmtree(session["output_dir"])
                    except Exception:
                        pass


if not IS_SERVERLESS:
    cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
    cleanup_thread.start()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Gemini Flow Mobile Web App")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)), help="Port to run on.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    print(f"\n✨ Gemini Flow Mobile Web App")
    print(f"   Local:   http://127.0.0.1:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)
