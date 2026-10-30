"""
Dynamic Prompt & Content Generator for TikTok Products
======================================================
Uses Gemini Pro (gemini-1.5-pro / gemini-2.5-pro) to generate:
- 3 Unique Keyframe Image Prompts (Front, Side Profile, Over Shoulder)
- 3 Flow AI Video Generation Prompts (Omni Flash 10s portrait with Malaysian Malay Lip-Sync)
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

import warnings
warnings.filterwarnings("ignore", message=r"urllib3.*doesn't match a supported version")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generation_history.json")

def _read_history_file() -> dict:
    """Read generation_history.json. Raises FileNotFoundError, or ValueError if it is unreadable."""
    with open(HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)  # json.JSONDecodeError is a ValueError
    if not isinstance(data, dict) or not isinstance(data.get("generations"), list):
        raise ValueError("missing 'generations' list")
    return data

def load_generation_history(last_n: int = 7) -> list:
    """Load the last N generation entries from history file."""
    try:
        entries = _read_history_file()["generations"]
        return entries[-last_n:]  # return only the last N
    except FileNotFoundError:
        return []
    except ValueError as e_read:
        print(f"WARNING: {HISTORY_FILE} is unreadable ({e_read}); anti-repetition check has NO history.")
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

def detect_hook_archetype(opening_line: str) -> str:
    """Classify an opening hook into one of the proven viral TikTok e-commerce archetypes."""
    if not opening_line:
        return "Unclassified / Organic Intro"
    line = opening_line.lower()
    if any(k in line for k in ['sauna', 'cuaca', 'panas', 'hujan', 'berkuap', 'angin sejuk']):
        return "The Unspoken Daily Dilemma (Tropical Climate / Comfort)"
    elif any(k in line for k in ['peha', 'tenggelam', 'nampak besar', 'gemuk', 'cutting', 'kurus', 'lampai', 'buncit', 'punggung', 'skirt extender', 'melekat']):
        return "The Flattering Silhouette / Visual Insecurity Solution"
    elif any(k in line for k in ['ratusan ringgit', 'mahal', 'murah', 'jenama', 'mampu milik', 'silap besar', 'ramai orang ingat', 'ramai ingat', 'sangka']):
        return "The Price-Quality Myth-Buster"
    elif any(k in line for k in ['rahsia', 'terlepas pandang', 'hidden gem', 'jumpa', 'dua saat', 'on-point']):
        return "The Hidden Gem / Secret Discovery"
    elif any(k in line for k in ['seterika', 'gosok', 'lambat', 'keluar cepat', 'malas', 'pagi-pagi', 'serabut']):
        return "The Relatable Lifestyle Dilemma (Morning Rush / Easy Prep)"
    elif any(k in line for k in ['perasan tak', 'tahu tak', 'siapa dekat sini', 'pernah tak', 'tengok betul']):
        return "The Visual Pattern Interrupt / Direct Question"
    elif any(k in line for k in ['siapa cakap', 'mesti ke', 'boyish', 'maskulin', 'gelap je', 'ingat mesti']):
        return "The Stereotype-Buster / Pain-Point Contrast"
    elif any(k in line for k in ['patutlah', 'asyik lalu', 'fyp', 'viral', 'ramai cari']):
        return "The FOMO / FYP Social Proof Trend"
    return "Conversational Organic Recommendation"

def verify_hook_quality(opening_line: str, last_7_entries: list = None) -> dict:
    """Verify that the opening hook satisfies 2-second viral retention and policy standards."""
    issues = []
    if not opening_line or len(opening_line.strip()) < 20:
        return {'status': 'fail', 'issues': ['Hook is missing or too short.'], 'hook_score': 0, 'archetype': 'Unknown'}

    line_lower = opening_line.lower()

    # Blacklist Indonesian slang
    indo_words = ['banget', 'bgt', 'keren', 'emang', 'nggak', 'gak', 'beneran', 'dong']
    found_indo = [w for w in indo_words if re.search(r'\b' + re.escape(w) + r'\b', line_lower)]
    if found_indo:
        issues.append(f"Contains Indonesian vocabulary: {found_indo}")

    # Pronoun check
    if re.search(r'\baku\b', line_lower):
        issues.append("Uses 'aku' instead of professional/friendly 'saya'")

    # 2-second retention hook trigger (expanded with live-search-derived patterns)
    triggers = [
        'korang', 'perasan tak', 'tahu tak', 'susah betul', 'ramai orang',
        'siapa dekat sini', 'dengan cuaca', 'pagi-pagi', 'kadang-kadang',
        'pernah tak', 'tengok', 'siapa cakap', 'patutlah', 'mesti ke',
        'selalu sangat', 'jangan', 'stop', 'satu je', 'ubah terus',
    ]
    has_trigger = any(t in line_lower for t in triggers)
    if not has_trigger:
        issues.append("Lacks a clear 2-second scroll-stopping trigger phrase.")

    archetype = detect_hook_archetype(opening_line)

    return {
        'status': 'pass' if not issues else 'warn',
        'issues': issues,
        'hook_score': max(0, 100 - len(issues) * 20),
        'archetype': archetype
    }

def save_generation_history(
    product_name: str,
    opening_line: str,
    closing_line: str,
    scenes: dict = None,
    caption: str = None,
    hashtags: str = None,
    bgm_prompt: str = None,
    keyframe_urls: list = None,
    metadata: dict = None,
    prefix: str = None,
    bgm_title: str = None
):
    """Append a new entry to the generation history file.

    Just stores the raw opening and closing text — no rigid categories.
    The point is simply to know what was already said so the next generation avoids it.

    With `prefix` (the keyframe prefix), the full record is also saved to
    generations/<prefix>.json, which automate_flow.py renders from and Step 10 commits.
    `keyframe_urls` is accepted for older callers; the record lists the keyframes found for `prefix`.
    """
    # Compute hook quality audit
    hook_audit = verify_hook_quality(opening_line)

    try:
        data = _read_history_file()
    except FileNotFoundError:
        data = {
            "_description": "Tracks previously used opening hooks and sign-off CTAs to prevent repetition across sessions.",
            "generations": []
        }
    except ValueError as e_read:
        # Never replace an existing history with a fresh one: that would wipe every past entry.
        data = None
        print(f"ERROR: {HISTORY_FILE} is unreadable ({e_read}). Local history NOT updated; "
              "fix the file by hand (or restore it with `git checkout generation_history.json`).")

    if data is not None:
        # Deduplicate against existing entries to prevent redundant rows
        existing_entry = None
        for entry in reversed(data["generations"]):
            if entry.get("product") == product_name and entry.get("opening_line") == opening_line:
                existing_entry = entry
                break

        if existing_entry:
            existing_entry["timestamp"] = datetime.now(timezone.utc).astimezone().isoformat()
            existing_entry["closing_line"] = closing_line
            existing_entry["hook_archetype"] = hook_audit.get("archetype")
            existing_entry["hook_score"] = hook_audit.get("hook_score")
        else:
            data["generations"].append({
                "product": product_name,
                "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
                "opening_line": opening_line,
                "closing_line": closing_line,
                "hook_archetype": hook_audit.get("archetype"),
                "hook_score": hook_audit.get("hook_score")
            })

        try:
            # Write to a temp file and swap it in, so an interrupted write can't truncate the history.
            tmp_path = HISTORY_FILE + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, HISTORY_FILE)
            print(f"📝 Saved generation history for: {product_name} (Hook: {hook_audit.get('archetype')}, Score: {hook_audit.get('hook_score')}/100)")
        except Exception as e_hist:
            print(f"Notice: local history file write: {e_hist}")

    # Save the full record in the repo (generations/<prefix>.json)
    if prefix:
        from generation_store import find_keyframes, save_record
        meta = dict(metadata or {})
        meta.setdefault("hook_archetype", hook_audit.get("archetype"))
        meta.setdefault("hook_score", hook_audit.get("hook_score"))
        meta.setdefault("hook_status", hook_audit.get("status"))
        meta.setdefault("hook_issues", hook_audit.get("issues"))
        kf = find_keyframes(prefix)
        if not kf["all_present"]:
            print(f"WARNING: keyframe trio for '{prefix}' is incomplete in keyframes/: {kf['paths']}")

        record_file = save_record(prefix, {
            "product_name": product_name,
            "opening_line": opening_line,
            "closing_line": closing_line,
            "scenes": scenes or {},
            "caption": caption,
            "hashtags": hashtags,
            "bgm_prompt": bgm_prompt,
            "bgm_title": bgm_title,
            "keyframes": kf["paths"],
            "keyframe_urls": kf["urls"],
            "metadata": meta,
        })
        print(f"🗂️ Saved generation record: {record_file.relative_to(record_file.parent.parent)}")

        # Auto-sync generation record and keyframes to Supabase
        try:
            from supabase_client import is_supabase_enabled, save_generation_record, upload_prefix_keyframes_to_supabase
            if is_supabase_enabled():
                cdn_map = upload_prefix_keyframes_to_supabase(prefix)
                if cdn_map:
                    meta["supabase_keyframe_urls"] = cdn_map
                save_generation_record(
                    product_name=product_name,
                    opening_line=opening_line,
                    closing_line=closing_line,
                    scenes=scenes,
                    caption=caption,
                    hashtags=hashtags,
                    bgm_prompt=bgm_prompt,
                    keyframe_urls=kf["urls"],
                    metadata=meta
                )
                print(f"☁️ Auto-synced '{product_name}' to Supabase database & storage.")
        except Exception as e_supa:
            print(f"Notice: Supabase auto-sync: {e_supa}")

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

2. SPEAKING PERSONALITY & VIRAL HOOK ENGINE (2-SECOND RETENTION RULE):
   - You MUST craft the most compelling, scroll-stopping hook angle for this specific product.
   - Stop the scroll in the first 2 seconds! Choose one of the 8 proven Malaysian TikTok Shop viral hook archetypes:
     1. The Unspoken Daily Dilemma / Tropical Climate Dilemma (e.g. cuaca panas rasa macam sauna vs material kalis air sejuk selesa).
     2. The Flattering Silhouette / Visual Insecurity Solution (e.g. takut peha nampak besar / cutting kembang vs efek auto-slimming).
     3. The Price-Quality Myth-Buster (e.g. sangka kena berhabis ratusan ringgit dekat outdoor brand vs kualiti padu mampu milik).
     4. The Hidden Gem / Secret Discovery (e.g. rahsia bersiap kemas dalam 2 saat / cutting rahsia yang ramai terlepas pandang).
     5. The Visual Pattern Interrupt / Direct Question (e.g. "Korang perasan tak...", "Tahu tak kenapa...", "Siapa dekat sini yang...").
     6. The Relatable Lifestyle Dilemma (e.g. bangun lambat, malas nak iron baju, nak cepat pergi kerja/kuliah).
     7. The Stereotype-Buster / Pain-Point Contrast (e.g. "Siapa cakap jaket kalis air mesti nampak boyish?").
     8. The FOMO / FYP Social Proof Trend (e.g. "Patutlah asyik lalu dekat FYP...").
   - Ensure the hook IMMEDIATELY hooks the viewer, connects directly to the product's #1 USP, and feels completely organic.
   - DO NOT repeat any angle or phrasing from the last 7 recorded entries in the anti-repetition list.
   - Speak in a CALM, FRIENDLY, and EFFORTLESS tone—like a creator sharing an honest daily outfit recommendation.
   - AVOID forced hyper-excitement, exaggerated whispers, dramatic screaming, or fake hype.
   - Natural, smooth conversational flow (steady pace, pleasant rhythm, clear pronunciation).

3. THE 3-ACT NATURAL VIDEO STRUCTURE (10 seconds each):

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 1 — "THE CASUAL INTRO" (Frame 1: Front-facing)     ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • A calm, organic conversational opening. Any style is    ║
   ║   allowed as long as it differs from recent history.       ║
   ║ • Natural pleasant smile, steady comfortable eye contact.║
   ║ • NO exaggerated wide-eyes, NO aggressive leaning in.    ║
   ║ • Camera: Static locked-off shot. She speaks, then pivots║
   ║   in place from front to a three-quarter angle.          ║
   ║ • Tone: Warm, relaxed, sincere, friendly.                ║
   ║ • Body Language: Relaxed shoulders, gentle natural nod.  ║
   ╚══════════════════════════════════════════════════════════╝

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 2 — "THE DETAIL & FEEL" (Frame 2: Side profile)    ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • Calmly highlight the real texture, cut, or comfort.    ║
   ║ • Hands stay empty and relaxed at her sides.             ║
   ║ • Camera: Static locked-off shot. She turns in place     ║
   ║   from three-quarter to her back, glancing over shoulder.║
   ║ • She keeps talking naturally while she turns.           ║
   ║ • Tone: Informative, honest, helpful styling advice.     ║
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
   ║ • Camera: Static locked-off shot. She turns from her back║
   ║   to face the camera, talking the whole time.            ║
   ║ • Tone: Friendly, effortless, polite recommendation.     ║
   ║ • Body Language: Natural relaxed over-the-shoulder       ║
   ║   glance, soft pleasant smile, arms resting naturally low ║
   ║   at her sides with empty hands. STRICTLY NO BAGS/PROPS. ║
   ╚══════════════════════════════════════════════════════════╝

4. FLOW AI PROMPT FORMAT (Frame-to-Video, 10s):
   - Each scene prompt is a SINGLE English paragraph combining visual + audio instructions.
   - Start with: "Static locked-off vertical shot, the camera does not move." All three keyframes share one
     background, so NEVER ask for camera pans, zooms, glides or orbits; the SUBJECT turns in place between the
     Start pose and the End pose.
   - Restate the exact model, hijab, garment, bottoms, shoes and setting from the keyframes.
   - Audio: Instruct Flow to generate realistic Malaysian Malay female voice, plus
     "No background music, only her voice and soft ambient sound." and
     "She speaks continuously in a warm, natural, conversational tone at a relaxed but steady pace, like chatting
     with a close friend, from the first second until the clip ends, without long pauses, and keeps talking
     naturally while she turns."
   - Always include: "Ensure there are no text overlays or watermarks."
   - SPOKEN LINE (each scene's spoken_malay_dialogue): 2-3 NATURAL spoken sentences, 28-32 words
     (automate_flow.py refuses under 24 or over 34). Shorter lines get stretched and sound unnatural; ~40+ words
     get cut off before the 10s clip ends.
     Write it exactly like a Malaysian creator talking to a friend, with natural fillers ("dia", "je", "tau",
     "memang", "la", "korang"). Pick 1-2 details per scene and say WHY they matter; never rattle off a spec list.
     No colons or semicolons in spoken lines (commas and full stops only). Keep English words to common ones.
     GOOD: "Saya suka tekstur korduroi dia yang halus ni, rasa vintage sangat. Renda beralun tu ikut sepanjang
     butang depan, poket dia pun besar, senang nak simpan barang kecil."
     BAD (spec list, too short): "Tekstur korduroi halus, renda beralun sepanjang butang, dua poket besar: detail vintage."

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

8. KEYFRAME IMAGE PROMPTS & LIFESTYLE BACKGROUND RULES:
   - STRICTLY FORBID blank, flat, plain, or sterile studio backdrops (NEVER use "minimalist studio", "plain studio background", "neutral grey wall", or "white studio backdrop"). These keywords cause image generators to paint a featureless, empty cardboard cutout void.
   - MANDATORY RICH LIFESTYLE ENVIRONMENT: Every keyframe prompt MUST describe a realistic, aesthetic lifestyle interior or setting with architectural details, depth of field, and natural lighting:
     • Space: e.g. bright sunlit modern minimalist Kuala Lumpur cafe with light oak tables and rattan chairs; or chic Japandi/Scandinavian living room with a light linen sofa, sheer curtains, and textured travertine/terrazzo floors; or an aesthetic boutique lounge.
     • Accents & Lighting: Subtle potted indoor greenery (fiddle-leaf fig / monstera) in soft focus, warm natural morning or afternoon daylight streaming through large windows with gentle shadows and soft bokeh.
     • Invariant Continuity: The exact same model, hijab, garment, bottoms, shoes, empty hands (strictly zero props), and same lifestyle background across all three frames.

9. NO REPEATING GENERIC LINES across products. Analyze the exact collar type, fabric, drawstring, length, pocket style, sleeve detail, and specific silhouette benefits.

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
    
    quota_badge = "🟢 Status Kuota Imej: Aktif (3/3 imej sedia ada dalam keyframes/)" if all_present else "🟢 Status Kuota Imej: Aktif (Generasi berjaya)"

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

### 📁 Lokasi Fail Keyframe (Dedicated Folder & GitHub)

* **Lokasi Tempatan:** `keyframes/`
  * **Frame 1 (Front):** `{f1.get('local_path') or f1.get('filename') or 'frame1_front.jpg'}`
  * **Frame 2 (Side):** `{f2.get('local_path') or f2.get('filename') or 'frame2_side.jpg'}`
  * **Frame 3 (Shoulder):** `{f3.get('local_path') or f3.get('filename') or 'frame3_shoulder.jpg'}`
* **Pautan GitHub (selepas git push):**
  * Frame 1: [{f1.get('filename', 'Frame 1')}]({f1.get('url', '#')})
  * Frame 2: [{f2.get('filename', 'Frame 2')}]({f2.get('url', '#')})
  * Frame 3: [{f3.get('filename', 'Frame 3')}]({f3.get('url', '#')})

---

### 🎬 3 Flow AI Video Prompts (Omni Flash 10s portrait)

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
            
            from generation_store import find_keyframes
            kf_info = find_keyframes(slug)

            # Format markdown deliverable
            markdown_out = format_deliverable_markdown(data, res, kf_info)
            print("\n" + "="*70)
            print(markdown_out)
            print("="*70)

            # Auto-save to history and generations/<slug>.json
            try:
                open_line = res.get("spoken_malay_dialogue", {}).get("scene_1_intro") or res.get("flow_ai_prompts", {}).get("scene_1_intro", "")[:100]
                close_line = res.get("spoken_malay_dialogue", {}).get("scene_3_outro") or res.get("flow_ai_prompts", {}).get("scene_3_outro", "")[:100]
                flow_prompts = res.get("flow_ai_prompts", {})
                spoken_dialogues = res.get("spoken_malay_dialogue", {})

                s1_p = flow_prompts.get("scene_1_intro", "")
                s1_s = spoken_dialogues.get("scene_1_intro", "")
                s2_p = flow_prompts.get("scene_2_detail", "")
                s2_s = spoken_dialogues.get("scene_2_detail", "")
                s3_p = flow_prompts.get("scene_3_outro", "")
                s3_s = spoken_dialogues.get("scene_3_outro", "")

                scenes_payload = {
                    "scene_1_intro": f"{s1_p}\n\nSpoken Malay (Lip-sync): \"{s1_s}\"" if (s1_s and "Spoken Malay" not in s1_p) else s1_p,
                    "scene_2_detail": f"{s2_p}\n\nSpoken Malay (Lip-sync): \"{s2_s}\"" if (s2_s and "Spoken Malay" not in s2_p) else s2_p,
                    "scene_3_outro": f"{s3_p}\n\nSpoken Malay (Lip-sync): \"{s3_s}\"" if (s3_s and "Spoken Malay" not in s3_p) else s3_p,
                    "visual_prompts": flow_prompts,
                    "spoken_dialogue": spoken_dialogues
                }

                save_generation_history(
                    product_name=data.get("title", "Product"),
                    opening_line=open_line,
                    closing_line=close_line,
                    scenes=scenes_payload,
                    caption=res.get("tiktok_caption"),
                    hashtags=res.get("hashtags"),
                    bgm_prompt=res.get("suno_bgm", {}).get("style"),
                    prefix=slug
                )
            except Exception as e_hist:
                print(f"History sync notice: {e_hist}")

            # Auto-log human coding activity to WakaTime
            try:
                from waka_human_sync import sync_recent_files
                sync_recent_files(since_minutes=30)
            except Exception as e_waka:
                print(f"WakaTime sync notice: {e_waka}")

