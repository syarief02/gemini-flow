"""
Gemini Flow — Web Application
==============================================
Flask web app that wraps the existing scraper + prompt generator
into a mobile-friendly interface with ZIP download.

Usage:
    python webapp.py                  # Dev mode (localhost:5000)
    python webapp.py --host 0.0.0.0   # LAN access (phone via WiFi)

No database needed — everything lives in temporary output directories
and downloads as a ZIP file.
"""

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

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

# Load .env for local development (Railway sets env vars directly)
load_dotenv()

# Import existing modules
from generate_prompts import generate_with_gemini_pro, save_generation_history
from generate_prompts import get_recently_used_phrases, load_generation_history
from scrape_product import scrape_tiktok_product

app = Flask(__name__)

# ═══════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SESSION_TTL = 3600  # 1 hour before auto-cleanup

# Store generated prompts in memory keyed by session_id
# (lightweight — no database needed)
session_store = {}
session_lock = threading.Lock()


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
    Scrape a TikTok Shop product URL.

    Request JSON: { "url": "https://vt.tiktok.com/..." }
    Response JSON: { "session_id": "...", "product_info": {...}, "image_urls": [...] }
    """
    data = request.get_json()
    if not data or not data.get("url"):
        return jsonify({"error": "Missing 'url' parameter"}), 400

    tiktok_url = data["url"].strip()

    # Basic URL validation
    if not re.search(r"tiktok\.com", tiktok_url, re.IGNORECASE):
        return jsonify({"error": "Please provide a valid TikTok URL"}), 400

    # Create session directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = timestamp
    output_dir = os.path.join(OUTPUT_DIR, session_id)

    try:
        # Run the existing async scraper
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        product_info = loop.run_until_complete(
            scrape_tiktok_product(tiktok_url, output_dir)
        )
        loop.close()

        if not product_info:
            return jsonify({"error": "Scraping returned no data. The URL may be invalid."}), 500

        # Build image URLs for the frontend
        image_urls = []
        if product_info.get("image_paths"):
            for img_path in product_info["image_paths"]:
                # Convert absolute path to relative URL
                filename = os.path.basename(img_path)
                image_urls.append(f"/api/image/{session_id}/{filename}")

        # Store in session
        with session_lock:
            session_store[session_id] = {
                "product_info": product_info,
                "output_dir": output_dir,
                "created_at": time.time(),
                "prompts": None,
            }

        return jsonify({
            "session_id": session_id,
            "product_info": {
                "title": product_info.get("title", ""),
                "page_text": product_info.get("page_text", ""),
                "image_count": product_info.get("image_count", 0),
                "scraped_at": product_info.get("scraped_at", ""),
            },
            "image_urls": image_urls,
        })

    except Exception as e:
        return jsonify({"error": f"Scraping failed: {str(e)}"}), 500


@app.route("/api/image/<session_id>/<filename>")
def api_image(session_id, filename):
    """Serve a scraped product image."""
    # Sanitize inputs
    session_id = re.sub(r"[^a-zA-Z0-9_]", "", session_id)
    filename = re.sub(r"[^a-zA-Z0-9_.]", "", filename)

    img_path = os.path.join(OUTPUT_DIR, session_id, filename)
    if not os.path.isfile(img_path):
        return jsonify({"error": "Image not found"}), 404

    return send_file(img_path, mimetype="image/jpeg")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """
    Generate prompts using Gemini for a scraped product.

    Request JSON: { "session_id": "..." }
    Response JSON: { "prompts": { ... } }
    """
    data = request.get_json()
    session_id = data.get("session_id") if data else None

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    with session_lock:
        session = session_store.get(session_id)

    if not session:
        return jsonify({"error": "Session not found. Please scrape again."}), 404

    product_info = session["product_info"]

    try:
        # Call the existing Gemini generator
        prompts = generate_with_gemini_pro(product_info)

        if not prompts:
            return jsonify({
                "error": "Gemini API call failed. Check your GEMINI_API_KEY in .env"
            }), 500

        # Store prompts in session
        with session_lock:
            session_store[session_id]["prompts"] = prompts

        # Save to generation history
        flow = prompts.get("flow_ai_prompts", {})
        opening = flow.get("scene_1_intro", "")[:100]
        closing = flow.get("scene_3_outro", "")[:100]
        product_name = prompts.get("product_summary", product_info.get("title", "Unknown"))

        save_generation_history(
            product_name=product_name[:60],
            opening_line=opening,
            closing_line=closing,
        )

        return jsonify({"prompts": prompts})

    except Exception as e:
        return jsonify({"error": f"Generation failed: {str(e)}"}), 500


@app.route("/api/download/<session_id>")
def api_download(session_id):
    """
    Bundle all scraped materials + generated prompts into a ZIP file
    and stream it to the device for download.
    """
    session_id = re.sub(r"[^a-zA-Z0-9_]", "", session_id)

    with session_lock:
        session = session_store.get(session_id)

    if not session:
        return jsonify({"error": "Session not found"}), 404

    output_dir = session["output_dir"]
    product_info = session["product_info"]
    prompts = session.get("prompts")

    # Build the ZIP in memory
    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Product images
        if os.path.isdir(output_dir):
            for fname in sorted(os.listdir(output_dir)):
                fpath = os.path.join(output_dir, fname)
                if os.path.isfile(fpath) and fname.lower().endswith(
                    (".jpg", ".jpeg", ".png", ".webp")
                ):
                    zf.write(fpath, f"images/{fname}")

        # 2. Product info JSON
        zf.writestr(
            "product_info.json",
            json.dumps(product_info, indent=2, ensure_ascii=False, default=str),
        )

        # 3. Generated prompts (if available)
        if prompts:
            zf.writestr(
                "generated_prompts.json",
                json.dumps(prompts, indent=2, ensure_ascii=False),
            )

            # Flow AI prompts as easy-to-paste text file
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

            # TikTok caption
            caption = prompts.get("tiktok_caption", "")
            if caption:
                zf.writestr("tiktok_caption.txt", caption)

            # Suno BGM
            bgm = prompts.get("suno_bgm", {})
            if bgm:
                bgm_text = (
                    "═══ SUNO AI BGM STYLE ═══\n\n"
                    f"{bgm.get('style', '')}\n\n\n"
                    "═══ LYRICS ═══\n\n"
                    f"{bgm.get('lyrics', '')}\n"
                )
                zf.writestr("suno_bgm.txt", bgm_text)

            # Keyframe prompts
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

    # Build a clean filename
    product_name = (
        prompts.get("product_summary", "")[:30] if prompts
        else product_info.get("title", "product")[:30]
    )
    safe_name = re.sub(r"[^a-zA-Z0-9]+", "_", product_name).strip("_").lower()
    zip_filename = f"gemini_flow_{safe_name}_{session_id}.zip"

    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zip_filename,
    )


@app.route("/api/history")
def api_history():
    """Return the last 7 generation history entries."""
    entries = load_generation_history(last_n=7)
    return jsonify({"entries": entries})


# ═══════════════════════════════════════════════════════════
# Session Cleanup (Background Thread)
# ═══════════════════════════════════════════════════════════
def cleanup_old_sessions():
    """Periodically remove sessions older than SESSION_TTL."""
    while True:
        time.sleep(300)  # Check every 5 minutes
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
                        print(f"🧹 Cleaned up session: {sid}")
                    except Exception as e:
                        print(f"⚠️ Cleanup error for {sid}: {e}")


# Start cleanup thread
cleanup_thread = threading.Thread(target=cleanup_old_sessions, daemon=True)
cleanup_thread.start()


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gemini Flow Web App")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to. Use 0.0.0.0 for LAN access from phone.",
    )
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5000)), help="Port to run on.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    args = parser.parse_args()

    print(f"\n✨ Gemini Flow Web App")
    print(f"   Local:   http://127.0.0.1:{args.port}")
    if args.host == "0.0.0.0":
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            print(f"   Network: http://{local_ip}:{args.port}")
        except Exception:
            print(f"   Network: http://0.0.0.0:{args.port}")
    print(f"   Press Ctrl+C to quit\n")

    app.run(host=args.host, port=args.port, debug=args.debug)
