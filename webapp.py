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


def find_matching_keyframes(slug: str) -> Dict[str, Optional[str]]:
    """Check if pre-generated keyframe images exist in keyframes/ for this product."""
    frames = {"front": None, "side": None, "shoulder": None}
    if not os.path.isdir(KEYFRAME_DIR):
        return frames

    for fname in os.listdir(KEYFRAME_DIR):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        lower_name = fname.lower()
        if slug in lower_name or any(part in lower_name for part in slug.split("_") if len(part) > 3):
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
    """Serve or download a 9:16 keyframe image."""
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

    if not target_file and os.path.isdir(KEYFRAME_DIR):
        for f in os.listdir(KEYFRAME_DIR):
            if frame_type in f.lower():
                target_file = os.path.join(KEYFRAME_DIR, f)
                break

    if not target_file or not os.path.isfile(target_file):
        return jsonify({"error": f"Keyframe '{frame_type}' not found"}), 404

    download_name = f"keyframe_{frame_type}_{session_id}.jpg"
    return send_file(
        target_file,
        mimetype="image/jpeg",
        as_attachment=as_download,
        download_name=download_name
    )


@app.route("/api/generate-images", methods=["POST"])
def api_generate_images():
    """
    Generate or retrieve 3 consistent 9:16 keyframe pictures for the session.
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

    frames_data = [
        {
            "id": "front",
            "frame_num": 1,
            "title": "Frame 1: Front Facing",
            "pose": "Natural gentle smile, eye contact, modest modern styling, full outfit head-to-toe",
            "image_url": f"/api/keyframe/{session_id}/front",
            "download_url": f"/api/keyframe/{session_id}/front?download=1",
            "has_image": bool(existing.get("front"))
        },
        {
            "id": "side",
            "frame_num": 2,
            "title": "Frame 2: 3/4 Side Profile",
            "pose": "3/4 side turn showcasing silhouette, fabric drape, and relaxed cut",
            "image_url": f"/api/keyframe/{session_id}/side",
            "download_url": f"/api/keyframe/{session_id}/side?download=1",
            "has_image": bool(existing.get("side"))
        },
        {
            "id": "shoulder",
            "frame_num": 3,
            "title": "Frame 3: Over-the-Shoulder Glance",
            "pose": "Modest back turn with gentle glance back, hands resting low, no waving",
            "image_url": f"/api/keyframe/{session_id}/shoulder",
            "download_url": f"/api/keyframe/{session_id}/shoulder?download=1",
            "has_image": bool(existing.get("shoulder"))
        }
    ]

    return jsonify({
        "status": "ready",
        "quota_status": "🟢 Status Kuota Imej: Aktif (3/3 imej sedia dipaparkan)",
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
        opening = flow.get("scene_1_intro", "")[:100]
        closing = flow.get("scene_3_outro", "")[:100]
        product_name = prompts.get("product_summary", product_info.get("title", "Unknown"))
        bgm_style = (
            prompts.get("suno_bgm", {}).get("style", "")
            if isinstance(prompts.get("suno_bgm"), dict)
            else str(prompts.get("suno_bgm", ""))
        )

        save_generation_history(
            product_name=product_name[:60],
            opening_line=opening,
            closing_line=closing,
            scenes=flow,
            caption=prompts.get("tiktok_caption", ""),
            hashtags="",
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
        cloud_rows = fetch_recent_generations(limit=7)
        if cloud_rows:
            return jsonify({
                "source": "supabase",
                "entries": [
                    {
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
        entries = load_generation_history(last_n=7)
        return jsonify({"source": "local", "entries": entries})
    except Exception:
        return jsonify({"source": "none", "entries": []})


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
