"""
Hard Checks on a Product's Copy (refuse instead of warn)
========================================================
AGENTS.md states these rules in prose, and agents drifted from them anyway: in Nov 2026 every
caption was the three spoken lines pasted together with 10-11 hashtags, lines asked her to do
things her empty hands can't ("Bila saya usap bulu..."), and a kids' bag "protects the spine".
The hook and script audits only cost points, and every product scored 100/100.

So the rules that must never break live here as ERRORS, and the pipeline refuses to continue:
  * save_generation_history() refuses to save a record with errors (Step 9),
  * automate_flow.py refuses to render dialogue with errors (Step 6),
  * reply_gmail.py refuses to send a caption with errors (Step 7).
WARNINGS are printed but don't block.

    python record_checks.py --prefix <prefix>      # check a saved record; exit 1 on errors
"""

from __future__ import annotations

import re
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

HASHTAGS_MIN, HASHTAGS_MAX = 4, 6
BANNED_HASHTAGS = {"#fyp", "#fypシ", "#foryou", "#foryoupage", "#viral", "#racuntiktok", "#trending"}
CAPTION_MIN_FEATURES = 3  # "✨ Feature: description" lines (AGENTS.md caption structure)
DIALOGUE_MIN_WORDS, DIALOGUE_MAX_WORDS = 24, 34

INDONESIAN = r"\b(banget|bgt|emang|keren|nggak|gak|beneran|dong|aku)\b"
PRICE = r"\bRM\s?\d|\b\d+(\.\d+)?\s?(ringgit|sen)\b|\bharga\s+(cuma|hanya|serendah)\b"
DASHES = "—–"  # em dash, en dash
# Her hands stay empty and at her sides in every keyframe; a line that has HER do something with
# her hands can't match the picture (and asking Flow for it morphs her hands).
HAND_ACTIONS = (r"\bsaya\s+(nak\s+|akan\s+|boleh\s+)?(usap|pegang|sentuh|tarik|ikat|buka|angkat|selak|lipat|"
                r"gulung|zip|tunjuk(kan)?|tekan|picit|ramas|regang(kan)?)\b"
                r"|\b(tengok|lihat)\s+(saya|bila saya)\s+(usap|pegang|sentuh|tarik|ikat|buka|angkat|selak)\b")
# TikTok Shop: no medical, body-changing or health claims for clothing/accessories.
# ("ilusi postur tegap", a visual effect, is fine; correcting posture is a health claim.)
HEALTH_CLAIMS = (r"\btulang\s+belakang\b|\bsakit\s+(belakang|pinggang|bahu|sendi)\b|"
                 r"\b(betulkan|baiki|perbaiki|bantu|jaga)\s+postur\b|\bubat\b|"
                 r"\b(me)?rawat\b|\bsembuh\b|\bturun(kan)?\s+berat\b|\b(hilang|bakar)\s+lemak\b|\bdetoks\b|"
                 r"\bkurus(kan)?\s+badan\b|\bmelangsingkan\s+badan\b")
# Accurate Claims / Fake Stories: no invented reactions, counts or stock levels.
INVENTED_PROOF = (r"\bkawan(-kawan)?\s+saya\s+(tanya|cakap|puji|terus beli)\b|\bramai\s+(orang\s+)?(tanya|puji|komen)\b|"
                  r"\b(ribu|ratus)\s+(orang\s+)?(dah\s+)?beli\b|\bstok\s+(dah\s+|nak\s+)?(tinggal|habis)\b|"
                  r"\bterjual\s+\d|\bsold\s+out\b")


def _hashtags(text: str) -> list[str]:
    return re.findall(r"#[^\s#]+", text or "")


def check_caption(caption: str, hashtags: str = "", spoken: dict | None = None) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    caption, hashtags = caption or "", hashtags or ""
    full = caption + "\n" + hashtags
    if not caption.strip():
        return ["Caption is empty."], []
    tags = list(dict.fromkeys(t.lower() for t in _hashtags(full)))
    if not HASHTAGS_MIN <= len(tags) <= HASHTAGS_MAX:
        errors.append(f"{len(tags)} hashtags; use {HASHTAGS_MIN}-{HASHTAGS_MAX} high-intent ones "
                      "(product keyword, occasion/pain point, niche community).")
    banned = [t for t in tags if t in BANNED_HASHTAGS]
    if banned:
        errors.append(f"Banned spam hashtags: {', '.join(banned)}.")
    if any(d in full for d in DASHES):
        errors.append("Em/en dash in the caption; use a colon or comma.")
    if re.search(PRICE, full, re.I):
        errors.append("Mentions a price; point to the beg kuning instead.")
    if re.search(INDONESIAN, full, re.I):
        errors.append(f"Indonesian word or 'aku': {re.search(INDONESIAN, full, re.I).group(0)}.")  # type: ignore[union-attr]
    features = [ln for ln in caption.splitlines() if ln.strip().startswith("✨")]
    if len(features) < CAPTION_MIN_FEATURES:
        errors.append(f"Caption has {len(features)} '✨ Feature: description' lines; the caption structure needs "
                      f"{CAPTION_MIN_FEATURES}-5 (hook, pitch, 'Kelebihan ... ni yang buat saya suka:', features, "
                      "styling tip, CTA). Don't paste the spoken lines as the caption.")
    lines = [v for v in (spoken or {}).values() if isinstance(v, str) and len(v) > 40]
    if lines and sum(line.strip() in caption for line in lines) >= 2:
        errors.append("Caption repeats the spoken script word for word; write it for reading, not listening.")
    if "beg kuning" not in full.lower():
        warnings.append("Caption has no 'beg kuning' call to action.")
    return errors, warnings


def check_dialogue(spoken: dict) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    for i in (1, 2, 3):
        line = (spoken or {}).get(f"scene_{i}") or (spoken or {}).get(
            {1: "scene_1_intro", 2: "scene_2_detail", 3: "scene_3_outro"}[i]) or ""
        low = line.lower()
        if not line.strip():
            errors.append(f"Scene {i}: spoken line is missing.")
            continue
        words = len(re.findall(r"[\w'-]+", line))
        if not DIALOGUE_MIN_WORDS <= words <= DIALOGUE_MAX_WORDS:
            errors.append(f"Scene {i}: {words} words; spoken lines must be {DIALOGUE_MIN_WORDS}-{DIALOGUE_MAX_WORDS}.")
        if re.search(r"[:;]", line):
            errors.append(f"Scene {i}: contains ':' or ';' (reads like a list).")
        if any(d in line for d in DASHES):
            errors.append(f"Scene {i}: em/en dash.")
        if m := re.search(INDONESIAN, low):
            errors.append(f"Scene {i}: Indonesian word or 'aku': '{m.group(0)}'.")
        if m := re.search(HAND_ACTIONS, low):
            errors.append(f"Scene {i}: '{m.group(0)}' has her do something with her hands, but her hands stay "
                          "empty at her sides in every frame. Say why the detail matters instead.")
        if m := re.search(HEALTH_CLAIMS, low):
            errors.append(f"Scene {i}: health/body claim '{m.group(0)}' (TikTok Shop prohibits medical claims).")
        if m := re.search(INVENTED_PROOF, low):
            errors.append(f"Scene {i}: '{m.group(0)}' invents other people's reactions, sales or stock "
                          "(TikTok Accurate Claims / Fake Stories). Use her own opinion of what is visible.")
        if re.search(PRICE, line, re.I):
            errors.append(f"Scene {i}: mentions a price.")
    return errors, warnings


def check_record(record: dict) -> tuple[list[str], list[str]]:
    from generate_prompts import HOOK_FORMATS
    from prompt_templates import DELIVERY_STYLES
    meta = record.get("metadata") or {}
    spoken = (record.get("scenes") or {}).get("spoken_dialogue") or {}
    errors, warnings = check_dialogue(spoken)
    cap_err, cap_warn = check_caption(record.get("caption") or "", record.get("hashtags") or "", spoken)
    errors += cap_err
    warnings += cap_warn
    fmt = meta.get("hook_format") or record.get("hook_format")
    style = meta.get("delivery_style") or record.get("delivery_style")
    if fmt not in HOOK_FORMATS:
        errors.append(f"hook_format '{fmt}' is not a HOOK_FORMATS key; pass hook_format= to save_generation_history.")
    if style not in DELIVERY_STYLES:
        errors.append(f"delivery_style '{style}' is not a DELIVERY_STYLES key; pass delivery_style=.")
    if not any("tiktok.com" in str(meta.get(k) or "") for k in ("tiktok_url", "source_url", "url")):
        warnings.append("metadata has no tiktok_url: reply_gmail.py then finds the thread by title, not the link.")
    return errors, warnings


def report(errors: list[str], warnings: list[str], what: str) -> None:
    for e in errors:
        print(f"  ❌ {e}")
    for w in warnings:
        print(f"  ⚠️ {w}")
    if not errors and not warnings:
        print(f"  ✅ {what}: all checks passed")


if __name__ == "__main__":
    import argparse
    from generation_store import load_record
    ap = argparse.ArgumentParser(description="Check a saved product record against the hard rules.")
    ap.add_argument("--prefix", required=True)
    args = ap.parse_args()
    rec = load_record(args.prefix)
    if not rec:
        print(f"No generations/{args.prefix}.json")
        sys.exit(1)
    errs, warns = check_record(rec)
    print(f"{args.prefix}: {len(errs)} error(s), {len(warns)} warning(s)")
    report(errs, warns, args.prefix)
    sys.exit(1 if errs else 0)
