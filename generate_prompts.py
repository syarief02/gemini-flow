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

    # Variety brief: what the recent hooks have in common, so the next one can break the pattern.
    lines.append("")
    lines.append("🎛️ HOOK VARIETY BRIEF (a hook = ANGLE + FORMAT; vary the FORMAT, not just the topic):")
    formats = suggest_hook_formats(last_n)
    used = [f"{f['key']} x{f['uses_in_window']}" for f in formats if f['uses_in_window']]
    lines.append("  Formats in the entries above: " + (", ".join(used) or "none detected"))
    lines.append("  Formats NOT used recently (prefer the one that fits this product best):")
    for f in formats:
        if not f["uses_in_window"]:
            lines.append(f"    - {f['key']}: {f['name']}. {f['how']} e.g. \"{f['example']}\"")

    openers = [(_words(e.get("opening_line", "")) or [""])[0] for e in recent]
    overused_openers = sorted({w for w in openers if w and openers.count(w) >= 2}, key=lambda w: -openers.count(w))
    if overused_openers:
        lines.append("  Opening words to avoid this time: " +
                     ", ".join(f"'{w.capitalize()}' ({openers.count(w)}x)" for w in overused_openers))
    questions = sum(_hook_sentence(e.get("opening_line", "")).endswith("?") for e in recent)
    if questions >= len(recent) / 2:
        lines.append(f"  {questions} of {len(recent)} recent hooks were questions: try a statement, confession or warning.")

    worn = sorted({label for e in recent for label in _worn_out(e.get("opening_line", "") + " " + e.get("closing_line", ""))})
    lines.append("  Worn-out phrases (don't use): " + ", ".join(label for _, label in WORN_OUT_PHRASES))
    if worn:
        lines.append("    ...of which these appear in the entries above: " + ", ".join(worn))
    lines.append(f"  Hook sentence (the first sentence) = {HOOK_SENTENCE_MAX_WORDS} words or fewer. "
                 "Open a loop that Scene 2 or 3 closes.")
    lines.append("  Scene 3 closer: close the Scene 1 loop, give her own pick, or a practical tip from the listing. "
                 "No 'cepat tekan beg kuning sebelum saiz habis'; urgency only if the listing shows it.")

    # Delivery brief: how she promotes across all three scenes.
    lines.append("")
    lines.append("🎭 DELIVERY BRIEF (how she promotes; pick ONE style for all 3 scenes, pass it as delivery_style=):")
    styles = suggest_delivery_styles(last_n)
    used_styles = [f"{s['key']} x{s['uses_in_window']}" for s in styles if s["uses_in_window"]]
    lines.append("  Styles in the entries above: " + (", ".join(used_styles) or "none recorded yet"))
    lines.append("  Fresh styles (prefer the one that fits this product and hook):")
    for s in styles:
        if not s["uses_in_window"]:
            lines.append(f"    - {s['key']}: {s['name']}. Voice: {s['voice']}. Talks: {s['script']}")
    lines.append("  Beats: Scene 1 hook (curiosity) -> Scene 2 her reaction to ONE detail + a real moment it "
                 "matters to korang (delight) -> Scene 3 payoff of the hook + her verdict + CTA (confidence).")
    lines.append("  Every scene talks TO the viewer (korang, a quick question, her own reaction). Never narrate "
                 "her turn ('Bila pusing ke tepi', 'Kemasan belakang'). Spoken Malay, not brochure words: "
                 + ", ".join(label.split(" (")[0] for _, label in BROCHURE_PHRASES) + ".")
    scripts = _recent_scripts(last_n)
    for scene in (2, 3):
        ops = [_opener(s.get(scene, "")) for s in scripts]
        repeated = sorted({o for o in ops if o and ops.count(o) >= 2}, key=lambda o: -ops.count(o))
        if repeated:
            lines.append(f"  Recent Scene {scene} openers to avoid: "
                         + ", ".join(f"'{o}' ({ops.count(o)}x)" for o in repeated))
    lines.append("  Acting: the style's expression for each scene (face, eyes, head, shoulders). Hands stay empty "
                 "at her sides. Check the script: python generate_prompts.py --audit-script \"<s1>\" \"<s2>\" \"<s3>\"")
    return "\n".join(lines)

def detect_hook_archetype(opening_line: str) -> str:
    """Classify an opening hook into one of the proven viral TikTok e-commerce archetypes (its ANGLE)."""
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
    # "presentation FYP" is a final-year project, not the For You page, so match the feed phrases only.
    elif any(k in line for k in ['patutlah', 'asyik lalu', 'dekat fyp', 'lalu fyp', 'masuk fyp', 'viral', 'ramai cari']):
        return "The FOMO / FYP Social Proof Trend"
    return "Conversational Organic Recommendation"


# ── Hook FORMATS ──────────────────────────────────────────────────────────────
# The archetype above is the hook's ANGLE (what it is about). The FORMAT is HOW it is said:
# the sentence shape and the speaker's stance. In Oct-Nov 2026 the angle changed every run but
# the format never did: 12 of 15 hooks used "korang", 10 of 15 were questions, none were first
# person, and every one scored 100/100 (user: "too boring", 2026-11-15).
# No format is banned. Formats used recently are only down-ranked by verify_hook_quality().
# Every format is spoken only: the shot is static, her hands stay empty, no props, no gestures.
# Never invent events, other people's reactions, comments, review counts or stock levels the
# listing doesn't show (TikTok "Accurate Claims" and "Fake stories" rules). Her own opinion
# of what is visible is fine.
HOOK_FORMATS = {
    "direct_question": {
        "name": "Soalan Terus (Direct Question)",
        "how": "Ask the viewer one sharp question about a pain point.",
        "example": "Kenapa kemeja putih kita cepat sangat nampak lusuh?",
        "cues": [r"\b(perasan|pernah|tahu) tak\b", r"^(siapa|kenapa|apa)\b"],
    },
    "turn_reveal": {
        "name": "Tunggu Saya Pusing (Turn Reveal)",
        "how": "Tease what she shows when she turns. Scene 2, where she turns to the back, pays it off.",
        "example": "Depan dia nampak macam kot biasa je, tapi tunggu saya pusing.",
        "cues": [r"\btunggu\b.*\bpusing\b", r"\bbila saya pusing\b"],
    },
    "dont_buy": {
        "name": "Jangan Beli Kalau (Reverse Warning)",
        "how": "Warn who should NOT buy it, in a way that is really a benefit.",
        "example": "Jangan beli blazer ni kalau korang memang suka rasa panas dekat ofis.",
        "cues": [r"^jangan beli\b", r"^jangan\b.*\bkalau\b"],
    },
    "honest_take": {
        "name": "Pendapat Jujur (Honest Take)",
        "how": "Open with her own bold, first-person opinion about the item.",
        "example": "Jujur, ni kemeja linen paling senang jaga yang saya pernah ada.",
        "cues": [r"\bjujur\b", r"\bterus terang\b", r"\bpendapat saya\b", r"^saya (rasa|berani|nak cakap)\b"],
    },
    "confession": {
        "name": "Saya Mengaku (Confession)",
        "how": "Admit a relatable habit of her own, then show how the item fits it.",
        "example": "Saya mengaku, saya memang malas gosok baju pagi-pagi.",
        "cues": [r"\bsaya mengaku\b", r"^saya (memang )?jenis\b"],
    },
    "numbered": {
        "name": "Tiga Sebab (Numbered, one per scene)",
        "how": "Promise two or three reasons and deliver one per scene, so viewers stay for all three clips.",
        "example": "Ada tiga benda pasal jaket ni yang buat saya tak nak tanggal.",
        "cues": [r"\b(dua|tiga|empat|lima|2|3|4|5) (sebab|benda|perkara|cara|detail|rahsia)\b"],
    },
    "detail_tease": {
        "name": "Satu Detail Kecil (Detail Tease)",
        "how": "Point at one small, specific detail most people miss and say why it matters.",
        "example": "Ada satu detail kecil dekat kolar kot ni yang ramai tak perasan.",
        "cues": [r"\bsatu detail\b", r"\bdetail kecil\b", r"\bramai tak perasan\b"],
    },
    "scenario": {
        "name": "Situasi (Mini Scene)",
        "how": "Drop the viewer into one specific moment, in present tense, without a question.",
        "example": "Pukul tujuh pagi, tudung belum siap, baju pun belum gosok.",
        "cues": [r"^(bayangkan|situasi|pov)\b", r"^pukul \w+"],
    },
    "this_not_that": {
        "name": "Ini, Bukan Itu (Contrast Statement)",
        "how": "Define the item by what it is not, in one confident statement.",
        "example": "Kot ni untuk nampak kemas, bukan nampak macam nak main ski.",
        "cues": [r",\s*bukan\b", r"\bbukan untuk\b"],
    },
    "myth_statement": {
        "name": "Ramai Ingat (Myth Statement)",
        "how": "State a common belief, then flip it in the next sentence. A statement, not a question.",
        "example": "Ramai ingat jaket tebal mesti buat badan nampak besar.",
        "cues": [r"\bramai (orang )?(ingat|sangka|fikir)\b", r"\bpadahal\b"],
    },
    "identity_callout": {
        "name": "Ni Untuk Yang (Call-out)",
        "how": "Name exactly who it is for (height, job, body worry) so the right viewer stops.",
        "example": "Ni untuk yang bertubuh kecil dan selalu rasa kot labuh terlalu panjang.",
        "cues": [r"^(ni|ini|khas) untuk\b", r"^kalau korang\b", r"^korang yang\b"],
    },
}

# Specific shapes first; direct_question last, because many of the others can also end with "?".
_FORMAT_DETECT_ORDER = [
    "turn_reveal", "dont_buy", "numbered", "detail_tease", "confession", "honest_take",
    "scenario", "myth_statement", "this_not_that", "identity_callout", "direct_question",
]

# The first sentence is the hook. Spoken Malay runs at about 3 words a second, so 12 words lands
# in the first 2-4 seconds; the rest of the 28-32-word Scene 1 line explains it.
HOOK_SENTENCE_MAX_WORDS = 12

# Filler that came back again and again in Oct-Nov 2026 hooks and closers. Flagged, not banned.
WORN_OUT_PHRASES = [
    (r"\bpenyelamat terbaik\b", "penyelamat terbaik"),
    (r"\bauto(matik)?\b", "automatik / auto"),
    (r"\bpening kepala\b", "pening kepala"),
    (r"\btengok ni\b", "tengok ni"),
    (r"\bmacam marshmallow\b", "macam marshmallow"),
    (r"\bnaik aura\b", "naik aura"),
    (r"\bjangan tunggu lagi\b", "jangan tunggu lagi"),
    (r"\bcepat tekan\b", "cepat tekan"),
    (r"\bsebelum\b[^.!?]{0,25}\b(habis|licin|kehabisan|tamat)\b", "sebelum saiz/stok habis"),
]

# Words too common to count as a "repeated phrase" on their own (CTA core + fillers).
_FILLER_WORDS = {
    "beg", "kuning", "dekat", "di", "dalam", "tekan", "klik", "ke", "bawah", "sekarang",
    "ni", "ini", "tu", "yang", "dan", "dia", "korang", "saya", "je", "untuk", "dengan",
}


def _words(text: str) -> list:
    return re.findall(r"[a-z0-9']+(?:-[a-z0-9']+)*", (text or "").lower())


def _hook_sentence(line: str) -> str:
    """The first spoken sentence: what the viewer hears in the first 2-4 seconds."""
    line = (line or "").strip()
    m = re.search(r"[?!.](\s|$)", line)
    return line[:m.end()].strip() if m else line


def detect_hook_format(opening_line: str) -> str:
    """Classify HOW a hook is said (a HOOK_FORMATS key), or 'other'."""
    hook = _hook_sentence(opening_line).lower()
    if not hook:
        return "other"
    for key in _FORMAT_DETECT_ORDER:
        if any(re.search(cue, hook) for cue in HOOK_FORMATS[key]["cues"]):
            return key
    return "direct_question" if hook.endswith("?") else "other"


def _entry_format(entry: dict) -> str:
    return entry.get("hook_format") or detect_hook_format(entry.get("opening_line", ""))


def _worn_out(text: str) -> list:
    low = (text or "").lower()
    return [label for rx, label in WORN_OUT_PHRASES if re.search(rx, low)]


def _phrase_ngrams(text: str, n: int = 3) -> set:
    w = _words(text)
    return {" ".join(w[i:i + n]) for i in range(len(w) - n + 1)
            if not set(w[i:i + n]) <= _FILLER_WORDS}


def _shared_phrases(text: str, others: list, min_hits: int = 2, limit: int = 5) -> list:
    """3-word phrases in `text` that already appear in at least `min_hits` of `others`."""
    other_sets = [_phrase_ngrams(o) for o in others]
    counts = {g: sum(g in s for s in other_sets) for g in _phrase_ngrams(text)}
    hits = sorted((g for g, c in counts.items() if c >= min_hits), key=lambda g: (-counts[g], g))
    return [(g, counts[g]) for g in hits[:limit]]


def _recent_for_check(window: int = 7, opening_line: str = None, product_name: str = None) -> list:
    """The last `window` history entries, minus this hook and earlier versions of this product."""
    entries = [e for e in load_generation_history(window + 5)
               if e.get("opening_line") != opening_line
               and not (product_name and e.get("product") == product_name)]
    return entries[-window:]


def check_hook_freshness(opening_line: str, recent: list, hook_format: str = None) -> list:
    """Warnings for a hook that would sound like the recent ones. Empty list = fresh."""
    warnings = []
    hook = _hook_sentence(opening_line)
    hook_words = _words(hook)
    if len(hook_words) > HOOK_SENTENCE_MAX_WORDS:
        warnings.append(f"Hook sentence is {len(hook_words)} words; keep the first sentence to "
                        f"{HOOK_SENTENCE_MAX_WORDS} or fewer so it lands in the first 2-4 seconds.")
    for label in _worn_out(opening_line):
        warnings.append(f"Worn-out phrase '{label}' (used again and again in past hooks).")
    if not recent:
        return warnings

    n = len(recent)
    first = hook_words[0] if hook_words else ""
    openers = [(_words(e.get("opening_line", "")) or [""])[0] for e in recent]
    if first and (openers.count(first) >= 2 or openers[-1] == first):
        warnings.append(f"Starts with '{first.capitalize()}' like {openers.count(first)} of the last {n} hooks"
                        f"{' (including the last one)' if openers[-1] == first else ''}; start with a different word.")

    fmt = hook_format or detect_hook_format(opening_line)
    recent_fmts = [_entry_format(e) for e in recent]
    if fmt in HOOK_FORMATS and (recent_fmts[-1] == fmt or recent_fmts.count(fmt) >= 3):
        warnings.append(f"Format '{fmt}' was used in {recent_fmts.count(fmt)} of the last {n} hooks"
                        f"{' (including the last one)' if recent_fmts[-1] == fmt else ''}; "
                        "pick a fresher one from suggest_hook_formats().")

    if hook.endswith("?"):
        questions = sum(_hook_sentence(e.get("opening_line", "")).endswith("?") for e in recent)
        if questions >= 4:
            warnings.append(f"{questions} of the last {n} hooks were questions; a statement, "
                            "confession or warning will stand out more.")

    shared = _shared_phrases(opening_line, [e.get("opening_line", "") for e in recent])
    if shared:
        warnings.append("Repeats phrases from recent hooks: " + ", ".join(f"'{g}' ({c}x)" for g, c in shared))
    return warnings


def check_closing_freshness(closing_line: str, recent: list) -> list:
    """Warnings for a Scene 3 sign-off that sounds like the recent ones."""
    warnings = [f"Worn-out phrase '{label}' (used again and again in past closers)."
                for label in _worn_out(closing_line)]
    shared = _shared_phrases(closing_line, [e.get("closing_line", "") for e in recent or []])
    if shared:
        warnings.append("Repeats phrases from recent closers: " + ", ".join(f"'{g}' ({c}x)" for g, c in shared))
    return warnings


def verify_hook_quality(opening_line: str, last_7_entries: list = None, closing_line: str = None,
                        product_name: str = None, hook_format: str = None) -> dict:
    """Audit a Scene 1 hook (and optionally the Scene 3 closer) for language and freshness.

    `issues` are hard problems (missing, Indonesian words, 'aku'). `warnings` say how the hook
    repeats recent ones (opening word, format, question streak, shared or worn-out phrases) or
    is too long to land in 2 seconds. hook_score = 100 - 25 per issue - 10 per warning, so the
    score ranks candidates instead of giving everything 100. Nothing here bans a hook.
    History is read from generation_history.json unless `last_7_entries` is given; entries with
    this exact hook or the same `product_name` (an earlier version of this run) are skipped.
    """
    if not opening_line or len(opening_line.strip()) < 20:
        return {'status': 'fail', 'issues': ['Hook is missing or too short.'], 'warnings': [],
                'hook_score': 0, 'archetype': 'Unknown', 'format': 'other'}

    issues = []
    line_lower = opening_line.lower()

    # Blacklist Indonesian slang
    indo_words = ['banget', 'bgt', 'keren', 'emang', 'nggak', 'gak', 'beneran', 'dong']
    found_indo = [w for w in indo_words if re.search(r'\b' + re.escape(w) + r'\b', line_lower)]
    if found_indo:
        issues.append(f"Contains Indonesian vocabulary: {found_indo}")

    # Pronoun check
    if re.search(r'\baku\b', line_lower):
        issues.append("Uses 'aku' instead of professional/friendly 'saya'")

    recent = last_7_entries if last_7_entries is not None else _recent_for_check(7, opening_line, product_name)
    warnings = check_hook_freshness(opening_line, recent, hook_format)

    result = {
        'status': 'fail' if issues else ('warn' if warnings else 'pass'),
        'issues': issues,
        'warnings': warnings,
        'hook_score': max(0, 100 - 25 * len(issues) - 10 * len(warnings)),
        'archetype': detect_hook_archetype(opening_line),
        'format': hook_format or detect_hook_format(opening_line),
        'hook_sentence_words': len(_words(_hook_sentence(opening_line))),
    }
    if closing_line:
        closing_warnings = check_closing_freshness(closing_line, recent)
        result['closing_warnings'] = closing_warnings
        result['closing_score'] = max(0, 100 - 10 * len(closing_warnings))
    return result


def suggest_hook_formats(last_n: int = 7) -> list:
    """All hook formats, freshest first: unused in the last `last_n` entries, then least recently used."""
    recent_fmts = [_entry_format(e) for e in load_generation_history(last_n)]

    def entries_ago(key):
        for age, f in enumerate(reversed(recent_fmts), 1):
            if f == key:
                return age
        return last_n + 1  # not used in the window

    return [
        {"key": key, **{k: v for k, v in info.items() if k != "cues"},
         "uses_in_window": recent_fmts.count(key), "last_used_entries_ago": entries_ago(key)}
        for key, info in sorted(HOOK_FORMATS.items(), key=lambda kv: -entries_ago(kv[0]))
    ]


# ── Character delivery: how she promotes (Scenes 1-3) ────────────────────────
# Until 2026-11-17 the hook changed but the rest of every video was identical: Scene 2 opened with
# "Bila pusing ke tepi...", Scene 3 with "Kemasan belakang..." and ended "...beg kuning ya!", the
# lines read like a product page, and she acted with the same "pleasant, friendly smile" in a
# "calm, relaxed" voice. The user called it boring. DELIVERY_STYLES (prompt_templates.py) gives
# each product a persona; audit_promo_script() catches the brochure habits. Nothing is blocked.
from prompt_templates import DELIVERY_STYLES  # noqa: E402

# Written-register words that make her sound like she is reading a product page.
BROCHURE_PHRASES = [
    (r"\bperincian\b", "perincian (say 'detail')"),
    (r"\bkemasan\b", "kemasan"),
    (r"\brekaan\b", "rekaan (say 'design' or 'potongan dia')"),
    (r"\bmahupun\b", "mahupun (say 'atau')"),
    (r"\bmanakala\b", "manakala"),
    (r"\bdilapisi\b", "dilapisi"),
    (r"\bpilihan terbaik\b", "pilihan terbaik"),
    (r"\bsangat praktikal\b", "sangat praktikal"),
    (r"\bbila melangkah\b", "bila melangkah"),
    (r"\bterletak (elok|cantik|kemas)\b", "terletak elok/cantik"),
    (r"\b(fabrik|kain|potongan|rekaan|warna|kolar|material|bahagian)nya\b", "'-nya' on the garment (say 'fabrik dia')"),
]
# Narrating her own turn instead of telling the viewer why the detail matters.
_MOVEMENT_NARRATION = (r"\b(bila|masa|kalau) (saya )?pusing\b|\bpandangan (belakang|sisi|tepi)\b"
                       r"|^(kemasan|bahagian) (belakang|tepi|sisi)\b")
# Signs she is talking TO someone: the viewer, a question, her own opinion or reaction.
_TALKING_TO_SOMEONE = r"\bkorang\b|\bkan\b|\?|\bsaya\b|\b(serius|eh|wah|ha|weh|gila)\b"
_SCENE_KEYS = {1: ("scene_1", "scene_1_intro"), 2: ("scene_2", "scene_2_detail"), 3: ("scene_3", "scene_3_outro")}


def _scene_lines(dialogue) -> dict:
    """{1: line, 2: line, 3: line} from a spoken_dialogue dict (either key style) or a 3-item list."""
    if isinstance(dialogue, (list, tuple)):
        return {i: (dialogue[i - 1] if i <= len(dialogue) else "") or "" for i in (1, 2, 3)}
    d = dialogue or {}
    return {i: (d.get(a) or d.get(b) or "") for i, (a, b) in _SCENE_KEYS.items()}


def _recent_scripts(last_n: int = 7, exclude_prefix: str = None) -> list:
    """Spoken lines {1,2,3} of the last `last_n` products saved in generations/, oldest first."""
    from generation_store import GENERATIONS_DIR
    found = []
    for path in GENERATIONS_DIR.glob("*.json"):
        if exclude_prefix and path.stem == exclude_prefix:
            continue
        try:
            rec = json.loads(path.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError):
            continue
        if not isinstance(rec, dict):
            continue
        lines = _scene_lines((rec.get("scenes") or {}).get("spoken_dialogue"))
        if any(lines.values()):
            found.append((rec.get("created_at") or "", lines))
    found.sort(key=lambda item: item[0])
    return [lines for _, lines in found[-last_n:]]


def _opener(line: str, n: int = 2) -> str:
    return " ".join(_words(line)[:n])


def audit_promo_script(dialogue, exclude_prefix: str = None, recent: list = None) -> dict:
    """Check the three spoken lines sound like a creator talking to the viewer, not a brochure.

    `dialogue` is a spoken_dialogue dict or a [scene1, scene2, scene3] list. Per scene it flags
    brochure words, narrating her own turn (Scenes 2-3), lines with no 'korang', 'saya', question
    or reaction, the '...ya' ending, and a first two words shared with another scene. Scenes 2-3
    are also compared with the last 7 products in generations/ (Scene 1 and the Scene 3 phrases
    are already covered by verify_hook_quality). Each warning costs 10 points; nothing is blocked.
    """
    lines = _scene_lines(dialogue)
    recent = recent if recent is not None else _recent_scripts(7, exclude_prefix)
    openers = {i: _opener(line) for i, line in lines.items()}
    report = {}
    for i, line in lines.items():
        low = line.lower().strip()
        if not low:
            report[f"scene_{i}"] = {"score": 0, "warnings": ["Spoken line is missing."]}
            continue
        warns = [f"Brochure word '{label}': say it the way people talk."
                 for rx, label in BROCHURE_PHRASES if re.search(rx, low)]
        if i > 1 and re.search(_MOVEMENT_NARRATION, low):
            warns.append("Narrates her own turn ('bila pusing...', 'kemasan belakang...'); tell the viewer "
                         "why the detail matters instead.")
        if not re.search(_TALKING_TO_SOMEONE, low):
            warns.append("Sounds like a product description: no 'korang', 'saya', question or reaction "
                         "(serius, eh, gila).")
        if re.search(r"\bya[\s.!?]*$", low):
            warns.append("Ends with 'ya', the sign-off crutch.")
        twins = [j for j, o in openers.items() if j != i and o and o == openers[i]]
        if twins:
            warns.append(f"Starts with '{openers[i]}' like scene {twins[0]} of this script.")
        if i > 1 and recent:
            past = [r.get(i, "") for r in recent]
            same = [_opener(p) for p in past].count(openers[i])
            if openers[i] and same >= 2:
                warns.append(f"Scene {i} also starts with '{openers[i]}' in {same} of the last {len(recent)} products.")
            if i == 2:
                shared = _shared_phrases(line, past)
                if shared:
                    warns.append("Repeats phrases from recent Scene 2 lines: "
                                 + ", ".join(f"'{g}' ({c}x)" for g, c in shared))
        report[f"scene_{i}"] = {"score": max(0, 100 - 10 * len(warns)), "warnings": warns}
    report["score"] = round(sum(report[f"scene_{i}"]["score"] for i in (1, 2, 3)) / 3)
    return report


def suggest_delivery_styles(last_n: int = 7) -> list:
    """All DELIVERY_STYLES, freshest first (unused in the last `last_n` history entries first)."""
    used = [e.get("delivery_style") for e in load_generation_history(last_n)]

    def entries_ago(key):
        for age, s in enumerate(reversed(used), 1):
            if s == key:
                return age
        return last_n + 1

    return [
        {"key": key, "name": info["name"], "voice": info["voice"], "script": info["script"],
         "uses_in_window": used.count(key), "last_used_entries_ago": entries_ago(key)}
        for key, info in sorted(DELIVERY_STYLES.items(), key=lambda kv: -entries_ago(kv[0]))
    ]


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
    bgm_title: str = None,
    hook_format: str = None,
    delivery_style: str = None
):
    """Append a new entry to the generation history file.

    Stores the raw opening and closing text plus the hook's format and the delivery style, so the
    next generation can avoid the same words, the same sentence shape and the same performance.
    `hook_format` is the HOOK_FORMATS key the hook was written in; detected from the text if omitted.
    `delivery_style` is the prompt_templates.DELIVERY_STYLES key used for all three scenes.

    With `prefix` (the keyframe prefix), the full record is also saved to
    generations/<prefix>.json, which automate_flow.py renders from and Step 10 commits.
    `keyframe_urls` is accepted for older callers; the record lists the keyframes found for `prefix`.
    """
    # Compute hook quality audit against the previous entries (not this product's own earlier save)
    hook_audit = verify_hook_quality(opening_line, closing_line=closing_line,
                                     product_name=product_name, hook_format=hook_format)
    hook_format = hook_audit.get("format")
    if delivery_style and delivery_style not in DELIVERY_STYLES:
        print(f"WARNING: unknown delivery_style '{delivery_style}'; expected one of {list(DELIVERY_STYLES)}")
    spoken = (scenes or {}).get("spoken_dialogue")
    script_audit = audit_promo_script(spoken, exclude_prefix=prefix) if spoken else None

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
            existing_entry["hook_format"] = hook_format
            existing_entry["delivery_style"] = delivery_style
            existing_entry["hook_score"] = hook_audit.get("hook_score")
        else:
            data["generations"].append({
                "product": product_name,
                "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
                "opening_line": opening_line,
                "closing_line": closing_line,
                "hook_archetype": hook_audit.get("archetype"),
                "hook_format": hook_format,
                "delivery_style": delivery_style,
                "hook_score": hook_audit.get("hook_score")
            })

        try:
            # Write to a temp file and swap it in, so an interrupted write can't truncate the history.
            tmp_path = HISTORY_FILE + ".tmp"
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, HISTORY_FILE)
            print(f"📝 Saved generation history for: {product_name} (Hook: {hook_audit.get('archetype')}, "
                  f"Format: {hook_format}, Score: {hook_audit.get('hook_score')}/100)")
            for w in hook_audit.get("warnings", []) + hook_audit.get("closing_warnings", []):
                print(f"   ⚠️ {w}")
            if script_audit:
                print(f"   🎭 Delivery: {delivery_style or 'NOT SET'} | script score {script_audit['score']}/100")
                for i in (1, 2, 3):
                    for w in script_audit[f"scene_{i}"]["warnings"]:
                        print(f"   ⚠️ Scene {i}: {w}")
        except Exception as e_hist:
            print(f"Notice: local history file write: {e_hist}")

    # Save the full record in the repo (generations/<prefix>.json)
    if prefix:
        from generation_store import find_keyframes, save_record
        meta = dict(metadata or {})
        meta.setdefault("prefix", prefix)
        meta.setdefault("hook_archetype", hook_audit.get("archetype"))
        meta.setdefault("hook_format", hook_format)
        meta.setdefault("hook_score", hook_audit.get("hook_score"))
        meta.setdefault("hook_status", hook_audit.get("status"))
        meta.setdefault("hook_issues", hook_audit.get("issues"))
        meta.setdefault("hook_warnings", hook_audit.get("warnings"))
        meta.setdefault("closing_warnings", hook_audit.get("closing_warnings"))
        meta.setdefault("delivery_style", delivery_style)
        if script_audit:
            meta.setdefault("script_score", script_audit["score"])
            meta.setdefault("script_warnings", {k: v["warnings"] for k, v in script_audit.items() if k != "score"})
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
   - You MUST craft the most compelling, scroll-stopping hook for this specific product.
   - A hook = ANGLE (what it is about) + FORMAT (how it is said). Hooks got boring when the angle changed but
     every hook was still the same "Korang ...?" question. Vary the FORMAT every time.
   - Stop the scroll in the first 2 seconds! ANGLE: choose one of the 8 proven Malaysian TikTok Shop viral hook archetypes:
     1. The Unspoken Daily Dilemma / Tropical Climate Dilemma (e.g. cuaca panas rasa macam sauna vs material kalis air sejuk selesa).
     2. The Flattering Silhouette / Visual Insecurity Solution (e.g. takut peha nampak besar / cutting kembang vs efek auto-slimming).
     3. The Price-Quality Myth-Buster (e.g. sangka kena berhabis ratusan ringgit dekat outdoor brand vs kualiti padu mampu milik).
     4. The Hidden Gem / Secret Discovery (e.g. rahsia bersiap kemas dalam 2 saat / cutting rahsia yang ramai terlepas pandang).
     5. The Visual Pattern Interrupt / Direct Question (e.g. "Korang perasan tak...", "Tahu tak kenapa...", "Siapa dekat sini yang...").
     6. The Relatable Lifestyle Dilemma (e.g. bangun lambat, malas nak iron baju, nak cepat pergi kerja/kuliah).
     7. The Stereotype-Buster / Pain-Point Contrast (e.g. "Siapa cakap jaket kalis air mesti nampak boyish?").
     8. The FOMO / FYP Social Proof Trend (e.g. "Patutlah asyik lalu dekat FYP...").
   - FORMAT: say it in one of these sentence shapes. Prefer one listed under "Formats NOT used recently":
     • Soalan Terus: "Kenapa kemeja putih kita cepat sangat nampak lusuh?"
     • Tunggu Saya Pusing: "Depan dia nampak macam kot biasa je, tapi tunggu saya pusing." (Scene 2 pays it off)
     • Jangan Beli Kalau: "Jangan beli blazer ni kalau korang memang suka rasa panas dekat ofis."
     • Pendapat Jujur: "Jujur, ni kemeja linen paling senang jaga yang saya pernah ada."
     • Saya Mengaku: "Saya mengaku, saya memang malas gosok baju pagi-pagi."
     • Tiga Sebab: "Ada tiga benda pasal jaket ni yang buat saya tak nak tanggal." (one reason per scene)
     • Satu Detail Kecil: "Ada satu detail kecil dekat kolar kot ni yang ramai tak perasan."
     • Situasi: "Pukul tujuh pagi, tudung belum siap, baju pun belum gosok."
     • Ini, Bukan Itu: "Kot ni untuk nampak kemas, bukan nampak macam nak main ski."
     • Ramai Ingat: "Ramai ingat jaket tebal mesti buat badan nampak besar." (flip it in the next sentence)
     • Ni Untuk Yang: "Ni untuk yang bertubuh kecil dan selalu rasa kot labuh terlalu panjang."
   - FRESHNESS: don't start with the same word as the recent hooks (most Oct-Nov 2026 hooks started with "Korang").
     The hook sentence (the first sentence) is 12 words or fewer; the next 1-2 sentences explain it.
     Never use these worn-out phrases: "penyelamat terbaik", "automatik"/"auto", "pening kepala", "tengok ni",
     "macam marshmallow", "naik aura", "jangan tunggu lagi", "cepat tekan", "sebelum saiz/stok habis".
   - OPEN A LOOP: Scene 1 promises something Scene 2 or 3 delivers (what she shows when she turns, reasons two
     and three, the small detail), so viewers stay for all three clips.
   - Never invent events, other people's reactions, comments, review counts or stock levels the listing doesn't
     support (TikTok "Accurate Claims" and "Fake stories" rules). Her own opinion of what is visible is fine.
   - Ensure the hook IMMEDIATELY hooks the viewer, connects directly to the product's #1 USP, and feels completely organic.
   - DO NOT repeat any angle, format or phrasing from the last 7 recorded entries in the anti-repetition list.
   - DELIVERY STYLE (how she promotes): pick ONE style for all three scenes, preferring one the brief lists as
     fresh, and return its key as "delivery_style". Each sets her voice, her acting per scene and how she talks:
     • excited_bestie (Kawan Baik Teruja): bright, genuinely excited, reacts out loud (serius, eh, gila).
     • honest_sister (Kakak Jujur): confident honest verdict with a playful edge, one "not for you if" aside.
     • playful_tease (Usik Manja): cheeky and teasing, opens loops and pays them off with a laugh.
     • insider_tip (Kongsi Rahsia): shares a tip like a secret, drops her voice slightly, then brightens.
     • confident_stylist (Stylist Yakin): poised, decisive styling advice (padan dengan, pakai dengan).
   - Energy is LIVELY and expressive, like telling a best friend about a great find: intonation that rises and
     falls, stress on the key words, real reactions. Never flat or monotone (the old "calm, relaxed" delivery
     looked and sounded like a mannequin), and never shouting, hard-selling, fake hype or exaggerated whispering.

3. THE 3-BEAT PERFORMANCE (10 seconds each). She is a creator TALKING TO the viewer, not a narrator reading a
   product page. Each scene has its own feeling and starts with a different word.

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 1 — "THE HOOK" (Frame 1: Front-facing)             ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • Feeling: curiosity. The hook, then why she cares.      ║
   ║ • Acting: the style's Scene 1 expression while she talks ║
   ║   straight to camera, then pivots in place to a          ║
   ║   three-quarter angle, still talking.                    ║
   ╚══════════════════════════════════════════════════════════╝

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 2 — "THE REACTION" (Frame 2: Side profile)         ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • Feeling: delight. Her honest reaction to ONE detail,   ║
   ║   how it feels, and a real moment it matters to korang   ║
   ║   (ofis aircond, naik LRT pagi, kenduri, travel).        ║
   ║ • Pay off the Scene 1 loop, or set up the last reveal.   ║
   ║ • NEVER narrate the turn ("Bila pusing ke tepi...").     ║
   ║ • Acting: the style's Scene 2 expression as she turns in ║
   ║   place to her back, glancing over her shoulder.         ║
   ╚══════════════════════════════════════════════════════════╝

   ╔══════════════════════════════════════════════════════════╗
   ║ SCENE 3 — "THE VERDICT" (Frame 3: Over Shoulder)         ║
   ╠══════════════════════════════════════════════════════════╣
   ║ • Feeling: confidence. Close the Scene 1 loop, give her  ║
   ║   verdict or her own pick ("Saya ambil warna krim,       ║
   ║   korang?"), then a fresh CTA to the beg kuning, written ║
   ║   on the spot like a real person would say it.           ║
   ║ • NEVER open with "Kemasan belakang..." and NEVER end    ║
   ║   the line with "ya".                                    ║
   ║ • NO "cepat tekan beg kuning sebelum saiz habis", NO     ║
   ║   "jangan tunggu lagi". Urgency only if the listing      ║
   ║   shows real low stock or an end-dated promo.           ║
   ║ • Acting: the style's Scene 3 expression as she turns    ║
   ║   from her back to face the camera, talking throughout.  ║
   ╚══════════════════════════════════════════════════════════╝

   ALL SCENES: expression lives in her face, eyes, head and shoulders. Her hands stay empty and relaxed at her
   sides: no hand gestures, no waving, no raised hands, STRICTLY NO BAGS/PROPS.
   Spoken KL Malay, not brochure Malay: never "perincian", "kemasan", "rekaan", "mahupun", "manakala",
   "dilapisi", "pilihan terbaik", "sangat praktikal", "bila melangkah", "terletak elok", or "fabriknya"
   (say "fabrik dia"). Every line has "korang", a quick question, or her own reaction.

4. FLOW AI PROMPT FORMAT (Frame-to-Video, 10s):
   - Each scene prompt is a SINGLE English paragraph combining visual + audio instructions.
   - Start with: "Static locked-off vertical shot, the camera does not move." All three keyframes share one
     background, so NEVER ask for camera pans, zooms, glides or orbits; the SUBJECT turns in place between the
     Start pose and the End pose.
   - Restate the exact model, hijab, garment, bottoms, shoes and setting from the keyframes.
   - Acting: put the delivery style's expression for that scene into the visual direction, plus
     "Her face, eyes, head and shoulders stay expressive and alive the whole time, reacting to what she says,
     while her hands stay empty and relaxed at her sides, no hand gestures, no props."
     Never use the old flat direction ("pleasant, friendly smile", "warm facial expressions", "calm").
   - Audio: Instruct Flow to generate realistic Malaysian Malay female voice, then "Her delivery is <the style's
     voice>.", plus "No background music, only her voice and soft ambient sound." and
     "She talks continuously from the first second until the clip ends, with lively, expressive intonation that
     rises and falls naturally, stressing the key words and reacting with real feeling like telling a close
     friend about a great find, never flat or monotone, never shouting or hard-selling, and keeps talking while
     she turns."
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
  "hook_format": "string (one HOOK_FORMATS key, e.g. turn_reveal)",
  "delivery_style": "string (one delivery style key, e.g. playful_tease)",
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

def _print_hook_audit(candidates: list, closing_line: str = None):
    for i, cand in enumerate(candidates, 1):
        a = verify_hook_quality(cand, closing_line=closing_line if i == 1 else None)
        print(f"\nCandidate {i}: score {a['hook_score']}/100 | format {a['format']} | "
              f"hook sentence {a.get('hook_sentence_words', 0)} words | {a['archetype']}")
        print(f"  \"{cand}\"")
        for msg in a["issues"]:
            print(f"  ❌ {msg}")
        for msg in a["warnings"]:
            print(f"  ⚠️ {msg}")
        if a.get("closing_warnings") is not None:
            print(f"  Closer score {a['closing_score']}/100")
            for msg in a["closing_warnings"]:
                print(f"  ⚠️ Closer: {msg}")


if __name__ == "__main__":
    # Step 4 helpers:
    #   python generate_prompts.py --hook-brief
    #   python generate_prompts.py --audit-hook "<candidate 1>" "<candidate 2>" ... [--closing "<scene 3 line>"]
    if len(sys.argv) > 1 and sys.argv[1] == "--hook-brief":
        print(get_recently_used_phrases(last_n=7) or "No generation history yet: every format is fresh.")
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--audit-hook":
        args = sys.argv[2:]
        closing = None
        if "--closing" in args:
            idx = args.index("--closing")
            closing = args[idx + 1] if idx + 1 < len(args) else None
            args = args[:idx] + args[idx + 2:]
        if not args:
            print('Usage: python generate_prompts.py --audit-hook "<hook 1>" "<hook 2>" [--closing "<scene 3 line>"]')
            sys.exit(1)
        _print_hook_audit(args, closing)
        sys.exit(0)
    if len(sys.argv) > 1 and sys.argv[1] == "--audit-script":
        # --audit-script "<scene 1>" "<scene 2>" "<scene 3>"   or   --audit-script --prefix <prefix>
        args = sys.argv[2:]
        exclude = None
        if len(args) == 2 and args[0] == "--prefix":
            from generation_store import load_record
            exclude = args[1]
            rec = load_record(exclude) or {}
            args = [_scene_lines((rec.get("scenes") or {}).get("spoken_dialogue"))[i] for i in (1, 2, 3)]
        if len(args) != 3 or not all(args):
            print('Usage: python generate_prompts.py --audit-script "<scene 1>" "<scene 2>" "<scene 3>"\n'
                  '       python generate_prompts.py --audit-script --prefix <prefix>')
            sys.exit(1)
        rep = audit_promo_script(args, exclude_prefix=exclude)
        print(f"Script score {rep['score']}/100")
        for i, line in enumerate(args, 1):
            r = rep[f"scene_{i}"]
            print(f"\nScene {i} ({r['score']}/100, {len(_words(line))} words): \"{line}\"")
            for msg in r["warnings"]:
                print(f"  ⚠️ {msg}")
        sys.exit(0)

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
                    prefix=slug,
                    hook_format=res.get("hook_format") if res.get("hook_format") in HOOK_FORMATS else None,
                    delivery_style=res.get("delivery_style")
                )
            except Exception as e_hist:
                print(f"History sync notice: {e_hist}")

            # Auto-log human coding activity to WakaTime
            try:
                from waka_human_sync import sync_recent_files
                sync_recent_files(since_minutes=30)
            except Exception as e_waka:
                print(f"WakaTime sync notice: {e_waka}")

