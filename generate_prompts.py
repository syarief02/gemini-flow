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
from datetime import datetime, timezone
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generation_history.json")

def load_generation_history(last_n: int = 5) -> list:
    """Load the last N generation entries from history file."""
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        entries = data.get("generations", [])
        return entries[-last_n:]  # return only the last N
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def get_recently_used_phrases(last_n: int = 5) -> str:
    """Build a summary of recently used hooks and sign-offs to inject into prompts."""
    recent = load_generation_history(last_n)
    if not recent:
        return ""
    
    lines = ["\n\n⚠️ PREVIOUSLY USED PHRASES — DO NOT REUSE OR CLOSELY PARAPHRASE ANY OF THESE:"]
    for i, entry in enumerate(recent, 1):
        lines.append(f"  {i}. [{entry.get('product', '?')}]")
        lines.append(f"     Opening used: \"{entry.get('opening_line', '?')}\"")
        lines.append(f"     Closing used: \"{entry.get('closing_line', '?')}\"")
    
    lines.append("")
    lines.append("IMPORTANT: You must write COMPLETELY FRESH opening and closing lines that are genuinely different from ALL of the above.")
    lines.append("Do NOT just rearrange the same words or swap synonyms. Create something a real human would naturally say differently.")
    lines.append("Think of it like a real TikTok creator who never scripts the same intro twice — each video just starts differently because that's how people naturally talk.")
    return "\n".join(lines)

def save_generation_history(product_name: str, opening_line: str, closing_line: str):
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
    
    data["generations"].append({
        "product": product_name,
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "opening_line": opening_line,
        "closing_line": closing_line
    })
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"📝 Saved generation history for: {product_name}")


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
   ║   glance, soft pleasant smile, arms resting naturally at  ║
   ║   her side or carrying bag casually. NO AWKWARD WAVING.  ║
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

7. SUNO BGM: Specific genre/instrument style + unique singable Malay lyrics.

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
  "tiktok_caption": "string",
  "suno_bgm": {
    "style": "string",
    "lyrics": "string"
  }
}"""

def generate_with_gemini_pro(product_info: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment. Using direct template engine.")
        return None
    
    # Load anti-repetition context from generation history
    anti_repetition = get_recently_used_phrases(last_n=5)
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        prompt = f"""Analyze this product and generate complete assets:
Product Title: {product_info.get('title', '')}
Product Details: {product_info.get('page_text', '')[:1500]}

Generate completely unique, non-repeating prompts and copy tailored specifically to this product's exact attributes.
{anti_repetition}"""

        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt,
            config={
                'system_instruction': SYSTEM_PROMPT,
                'response_mime_type': 'application/json'
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
        res = generate_with_gemini_pro(data)
        if res:
            print(json.dumps(res, indent=2, ensure_ascii=False))

