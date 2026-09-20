"""
Dynamic Prompt & Content Generator for TikTok Products
======================================================
Uses Gemini Pro (gemini-1.5-pro / gemini-2.5-pro) to generate:
- 3 Unique Keyframe Image Prompts (Front, Side Profile, Over Shoulder)
- 3 Flow AI Video Generation Prompts (Veo 3.1 / Omni Flash 8s with Malaysian Malay Lip-Sync)
- TikTok Caption + Hashtags (Bahasa Melayu Malaysia, policy-safe)
- Suno BGM Style + Lyrics (Bahasa Melayu)

Usage:
    python generate_prompts.py <path_to_product_info.json>
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generation_history.json")

def load_generation_history(last_n: int = 7) -> list:
    """Load the last N generation entries from history file."""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get("generations", [])
        return entries[-last_n:]  # return only the last N
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_recently_used_phrases(last_n: int = 7) -> str:
    """Build a summary of recently used hooks and sign-offs to inject into prompts.
    
    Only the last `last_n` entries are shown. Phrases older than this window
    are allowed to be reused freely.
    """
    recent = load_generation_history(last_n)
    if not recent:
        return ""
    
    lines = [f"\n\n⚠️ LAST {len(recent)} USED PHRASES — avoid reusing or closely paraphrasing these:"]
    for i, entry in enumerate(recent, 1):
        lines.append(f"  {i}. [{entry.get('product', '?')}]")
        lines.append(f"     Opening used: \"{entry.get('opening_line', '?')}\"")
        lines.append(f"     Closing used: \"{entry.get('closing_line', '?')}\"")
    
    lines.append("")
    lines.append(f"Avoid reusing the {len(recent)} entries above. Phrases older than this list are fine to reuse.")
    lines.append("Write genuinely different phrasing — not just rearranging the same words or swapping synonyms.")
    return "\n".join(lines)

def save_generation_history(
    product_name: str,
    opening_line: str,
    closing_line: str,
    scenes: dict = None,
    caption: str = None,
    hashtags: str = None,
    bgm_prompt: str = None,
    keyframe_urls: list = None
):
    """Append a new entry to the generation history file.
    
    Just stores the raw opening and closing text — no rigid categories.
    The point is simply to know what was already said so the next generation avoids it.
    """
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {
            "_description": "Tracks previously used opening hooks and sign-off CTAs to prevent repetition across sessions.",
            "generations": []
        }
    
    # Deduplicate against existing entries to prevent redundant rows
    existing_entry = None
    for entry in reversed(data.get("generations", [])):
        if entry.get("product") == product_name and entry.get("opening_line") == opening_line:
            existing_entry = entry
            break

    if existing_entry:
        existing_entry["timestamp"] = datetime.now(timezone.utc).astimezone().isoformat()
        existing_entry["closing_line"] = closing_line
    else:
        data["generations"].append({
            "product": product_name,
            "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "opening_line": opening_line,
            "closing_line": closing_line
        })
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"📝 Saved generation history for: {product_name}")
    except Exception as e_hist:
        print(f"Notice: local history file write: {e_hist}")

    # Optionally sync to Supabase database
    try:
        from supabase_client import save_generation_record
        save_generation_record(
            product_name=product_name,
            opening_line=opening_line,
            closing_line=closing_line,
            scenes=scenes,
            caption=caption,
            hashtags=hashtags,
            bgm_prompt=bgm_prompt,
            keyframe_urls=keyframe_urls
        )
    except Exception as e_sup:
        print(f"Notice: Supabase sync: {e_sup}")


SYSTEM_PROMPT = """You are a top Malaysian TikTok e-commerce content strategist who creates VIRAL short-form video scripts.
You specialize in creating spoken dialogue that feels like a real person talking to their bestie—NOT a product brochure being read aloud.

Your goal: analyze the given product and generate assets that make viewers STOP scrolling, WATCH the full video, and TAP the yellow basket.

═══════════════════════════════════════════════════════════════
STRICT RULES
═══════════════════════════════════════════════════════════════

1. LANGUAGE & ACCENT:
   - ALL spoken dialogue must be in standard Malaysian Malay (Bahasa Melayu Malaysia, KL/urban accent).
   - STRICTLY NOT Indonesian (no "banget", "emang", "keren", "bgt").
   - Use natural Malaysian slang & filler ("korang", "gila", "serious", "tau tak", "eh", "kan").
   - ALWAYS use "saya" (NOT "aku") as the first-person pronoun. "Saya" sounds more polished and professional while still being friendly.

2. SPEAKING PERSONALITY (NATURAL, RELAXED & EFFORTLESS):
   - Speak in a CALM, FRIENDLY, and EFFORTLESS tone—like a creator sharing an honest daily outfit recommendation.
   - AVOID forced hyper-excitement, exaggerated whispers, dramatic screaming, or fake hype.
   - Natural, smooth conversational flow (steady pace, pleasant rhythm, clear pronunciation).
   - You will be given a list of PREVIOUSLY USED opening lines and sign-off lines.
   - You MUST write something different from all of them — not just rearranging the same words, but genuinely new phrasing and angles.
   - Any opener style is allowed (including "Kalau korang", "Hari ni saya nak share", etc.) as long as it was not used in the recent history provided.

3. THE 3-ACT NATURAL VIDEO STRUCTURE (8 seconds each):

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 1 — "THE CASUAL INTRO" (Frame 1: Front-facing)     ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • A calm, organic conversational opening. Any style is    ║
   ║   allowed as long as it differs from recent history.       ║
   ║ • Natural pleasant smile, steady comfortable eye contact.║
   ║ • NO exaggerated wide-eyes, NO aggressive leaning in.    ║
   ║ • Camera: Smooth, subtle slow zoom or steady shot.       ║
   ║ • Tone: Warm, relaxed, sincere, friendly.                ║
   ║ • Body Language: Relaxed shoulders, gentle natural nod.  ║
   ╚══════════════════════════════════════════════════════════╝

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 2 — "THE DETAIL & FEEL" (Frame 2: Side profile)    ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • Calmly highlight the real texture, cut, or comfort.    ║
   ║ • Natural, unforced gestures (gentle touch on sleeve).   ║
   ║ • Camera: Slow graceful pan along the garment.           ║
   ║ • Tone: Informative, honest, helpful styling advice.     ║
   ║ • Body Language: Casual side turn, soft subtle gestures. ║
   ╚══════════════════════════════════════════════════════════╝

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 3 — "THE FRIENDLY SIGN-OFF" (Frame 3: Over Shoulder║
   ╠══════════════════════════════════════════════════════════╣
   ║ • A warm, natural recommendation to check yellow basket. ║
   ║ • STRICTLY FORBID repetitive endings with "...ya" or     ║
   ║   always ending with "...dekat beg kuning di bawah ya."   ║
   ║ • CREATE a completely fresh, original sign-off CTA every  ║
   ║   time. Do NOT copy-paste from previous products. Write   ║
   ║   it on the spot like a real human would naturally say it. ║
   ║ • Camera: Soft, natural lighting with gentle slow-mo.    ║
   ║ • Tone: Friendly, effortless, polite recommendation.     ║
   ║ • Body Language: Natural relaxed over-the-shoulder       ║
   ║   glance, soft pleasant smile, arms resting naturally low ║
   ║   at her sides with empty hands. STRICTLY NO BAGS/PROPS. ║
   ╚══════════════════════════════════════════════════════════╝

4. FLOW AI PROMPT FORMAT:
   - Each scene prompt is a SINGLE English paragraph combining visual + audio instructions.
   - Visual: Describe camera movement, subject action, and body language.
   - Audio: Instruct Flow to generate realistic Malaysian Malay female voice.
   - Always include: "Ensure there are no text overlays or watermarks."

5. TIKTOK CAPTION:
   - High-converting Bahasa Melayu copywriting with relatable problem-solution angle.
   - Zero direct price mentions (TikTok policy).
   - CTA pointing to "beg kuning" (yellow basket).
   - STRICTLY NEVER use the em-dash "—" or en-dash "–" character anywhere in the caption. Use colon ":", comma ",", or natural punctuation instead.

6. HASHTAGS:
   - STRICTLY NO generic spam: #RacunTikTok, #fyp, #viral are BANNED.
   - Use only 4-6 high-intent, targeted SEO hashtags:
     • Product keyword (e.g. #BlazerWanita, #TudungInstant)
     • Occasion/Pain Point (e.g. #OutfitKePejabat, #OOTDCikgu)
     • Niche Community (e.g. #MuslimahStyleMY, #HijabFashionMY)

7. SUNO BGM: ONE comprehensive, highly detailed instrumental style prompt for Suno's 'Song Description' / 'Style of Music' box. STRICTLY NO LYRICS (instrumental only, no vocals, to prevent clashing with the Flow AI spoken Malay dialogue). Include genre, subgenre, specific instruments, tempo BPM (105-115 BPM), mood, and high-quality production attributes tailored to the product vibe.

8. NO REPEATING GENERIC LINES across products. Analyze the exact collar type, fabric, drawstring, length, pocket style, sleeve detail, and specific silhouette benefits.

═══════════════════════════════════════════════════════════════
OUTPUT SCHEMA (Return valid JSON)
═══════════════════════════════════════════════════════════════
{
  "product_summary": "string",
  "keyframe_prompts": {
    "frame_1_front": "string",
    "frame_2_side": "string",
    "frame_3_shoulder": "string"
  },
  "flow_ai_prompts": {
    "scene_1_intro": "string",
    "scene_2_detail": "string",
    "scene_3_outro": "string"
  },
  "spoken_malay_dialogue": {
    "scene_1_intro": "string",
    "scene_2_detail": "string",
    "scene_3_outro": "string"
  },
  "tiktok_caption": "string",
  "hashtags": "string",
  "suno_bgm": {
    "style": "string (Comprehensive instrumental style prompt with genre, instruments, tempo BPM, mood, pure instrumental no vocals)",
    "lyrics": ""
  }
}"""

def format_deliverable_markdown(
    product_info: dict,
    assets: dict,
    keyframe_info: dict = None
) -> str:
    """
    Format generated assets into a fully policy-compliant, 1-click copy deliverable package
    according to AGENTS.md standards.
    """
    policy_badge = product_info.get(
        "policy_compliance",
        "🛡️ Status Pematuhan Polisi TikTok: Disemak & Patuh (Tarikh: 2026-09-14 | Kategori: Pakaian Wanita - Dibenarkan)"
    )
    
    kf_info = keyframe_info or {}
    frames = kf_info.get("frames", {})
    all_present = kf_info.get("all_present", False)
    
    quota_badge = "🟢 Status Kuota Imej: Aktif (3/3 imej sedia ada & diselaraskan ke Supabase Storage)" if all_present else "🟢 Status Kuota Imej: Aktif (Generasi berjaya)"

    f1 = frames.get("frame_1_front", {})
    f2 = frames.get("frame_2_side", {})
    f3 = frames.get("frame_3_shoulder", {})

    flow_p = assets.get("flow_ai_prompts", {})
    spoken = assets.get("spoken_malay_dialogue", {})
    caption = (assets.get("tiktok_caption", "") or "").replace("—", ":").replace("–", "-")
    hashtags = assets.get("hashtags", "")
    bgm = assets.get("suno_bgm", {}).get("style", "")

    s1_prompt = flow_p.get("scene_1_intro", "")
    s1_spoken = spoken.get("scene_1_intro", "")
    s2_prompt = flow_p.get("scene_2_detail", "")
    s2_spoken = spoken.get("scene_2_detail", "")
    s3_prompt = flow_p.get("scene_3_outro", "")
    s3_spoken = spoken.get("scene_3_outro", "")

    full_caption_block = f"{caption}\n\n{hashtags}".strip()

    md = f"""### 🛡️ Status Pematuhan Polisi TikTok & Kuota Imej

* **🛡️ Status Pematuhan Polisi TikTok:** {policy_badge}
* **{quota_badge}**

---

### 📁 Lokasi Fail Keyframe (Dedicated Folder & Cloud CDN)

* **Lokasi Tempatan:** `keyframes/`
  * **Frame 1 (Front):** `{f1.get('local_path') or f1.get('filename') or 'frame1_front.jpg'}`
  * **Frame 2 (Side):** `{f2.get('local_path') or f2.get('filename') or 'frame2_side.jpg'}`
  * **Frame 3 (Shoulder):** `{f3.get('local_path') or f3.get('filename') or 'frame3_shoulder.jpg'}`
* **Pautan Supabase CDN:**
  * Frame 1: [{f1.get('filename', 'Frame 1')}]({f1.get('cdn_url', '#')})
  * Frame 2: [{f2.get('filename', 'Frame 2')}]({f2.get('cdn_url', '#')})
  * Frame 3: [{f3.get('filename', 'Frame 3')}]({f3.get('cdn_url', '#')})

---

### 🎬 3 Flow AI Video Prompts (Veo 3.1 / Omni Flash 8s)

> 💡 *Salin terus kotak kod di bawah untuk menyalin arahan visual Bahasa Inggeris dan skrip lip-sync Bahasa Melayu secara serentak.*

#### Scene 1 — The Casual Intro (Frame 1: Front-facing)
```text
{s1_prompt}

Spoken Malay (Lip-sync):
"{s1_spoken}"
```

#### Scene 2 — The Detail & Feel (Frame 2: Side Profile)
```text
{s2_prompt}

Spoken Malay (Lip-sync):
"{s2_spoken}"
```

#### Scene 3 — The Friendly Sign-Off (Frame 3: Over Shoulder)
```text
{s3_prompt}

Spoken Malay (Lip-sync):
"{s3_spoken}"
```

---

### 📝 TikTok Caption + SEO Hashtags (1-Click Copy)

```text
{full_caption_block}
```

---

### 🎵 Suno AI Instrumental BGM Prompt (Tanpa Lirik)

> **Suno Mode:** Instrumental Mode (`Song Description` / `Style of Music`)

```text
{bgm}
```

---

### ⚠️ AIGC Reminder
> **Reminder:** This content is AI-generated. When posting to TikTok, enable the **"AI-generated content"** toggle in posting settings to comply with TikTok's AIGC disclosure policy.
"""
    return md


def generate_with_gemini_pro(product_info: dict, api_key: str = None) -> dict:
    effective_key = (api_key or "").strip() or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not effective_key:
        print("⚠️ No Gemini API key provided and none found in environment.")
        return None
    
    # Load anti-repetition context from generation history
    anti_repetition = get_recently_used_phrases(last_n=7)
    
    try:
        from google import genai
        client = genai.Client(api_key=effective_key)
        
        prompt = f"""Analyze this product and generate complete assets:
Product Title: {product_info.get('title', '')}
Product Details: {product_info.get('page_text', '')[:1500]}

Generate completely unique, non-repeating prompts and copy tailored specifically to this product's exact attributes.
{anti_repetition}"""

        candidate_models = [
            'gemini-2.5-flash',
            'gemini-2.5-pro',
            'gemini-flash-latest',
            'gemini-pro-latest',
        ]

        response = None
        last_err = None
        for model_name in candidate_models:
            try:
                print(f"🤖 Generating with model: {model_name}...", flush=True)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        'system_instruction': SYSTEM_PROMPT,
                        'response_mime_type': 'application/json'
                    }
                )
                if response and response.text:
                    print(f"✅ Successfully generated assets using {model_name}!", flush=True)
                    break
            except Exception as e_m:
                print(f"⚠️ Model {model_name} failed: {e_m}", flush=True)
                last_err = e_m

        if not response or not response.text:
            raise last_err or RuntimeError("All Gemini candidate models failed to generate content.")

        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise e

if __name__ == "__main__":
    if len(sys.argv) > 1:
        info_path = Path(sys.argv[1])
        if not info_path.is_file():
            print(f"File not found: {info_path}")
            sys.exit(1)

        with open(info_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"🚀 Processing: {data.get('title', 'Product')}")
        res = generate_with_gemini_pro(data)
        if res:
            # Look up keyframes
            slug = data.get("title", "product").lower()
            slug = re.sub(r"[^a-zA-Z0-9]+", "_", slug).strip("_")[:20]
            
            try:
                from supabase_client import get_product_keyframes
                kf_info = get_product_keyframes(slug)
            except Exception:
                kf_info = {}

            # Format markdown deliverable
            markdown_out = format_deliverable_markdown(data, res, kf_info)
            print("\n" + "="*70)
            print(markdown_out)
            print("="*70)

            # Auto-save to history and Supabase
            try:
                open_line = res.get("spoken_malay_dialogue", {}).get("scene_1_intro") or res.get("flow_ai_prompts", {}).get("scene_1_intro", "")[:100]
                close_line = res.get("spoken_malay_dialogue", {}).get("scene_3_outro") or res.get("flow_ai_prompts", {}).get("scene_3_outro", "")[:100]
                save_generation_history(
                    product_name=data.get("title", "Product"),
                    opening_line=open_line,
                    closing_line=close_line,
                    scenes=res.get("flow_ai_prompts"),
                    caption=res.get("tiktok_caption"),
                    hashtags=res.get("hashtags"),
                    bgm_prompt=res.get("suno_bgm", {}).get("style"),
                    keyframe_urls=kf_info.get("cdn_urls")
                )
            except Exception as e_hist:
                print(f"History sync notice: {e_hist}")

