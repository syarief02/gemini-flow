# AGENTS.md — Gemini Flow Workspace Instructions
# ================================================
# This file tells any AI agent (Antigravity, Gemini, etc.) exactly how this
# workspace operates.  Read this FIRST before doing anything in this repo.

## What This Workspace Does

This is a **TikTok Shop Product Promo Generator** for the Malaysian market.
Given a single TikTok Shop product URL, the pipeline produces:

1. **3 Consistent 9:16 Keyframe Images** (Front, Side, Over-Shoulder poses)
2. **3 Flow AI Video Prompts** (Veo 3.1 / Omni Flash 8s with Malaysian Malay lip-sync)
3. **TikTok Caption + SEO Hashtags** (Bahasa Melayu Malaysia, policy-safe)
4. **Suno AI BGM Prompt + Lyrics** (Bahasa Melayu)

---

## End-to-End Workflow (Step by Step)

When the user gives you a TikTok product link, follow this exact sequence:

### Step 1: Scrape the Product
```bash
python scrape_product.py "https://vt.tiktok.com/..."
```
- Resolves short URL → full TikTok Shop PDP page.
- Downloads all product listing images as `.jpg` into `output/<timestamp>/`.
- Extracts product title, description, and metadata.

### Step 2: View the Scraped Product Images
- Open `output/<timestamp>/product_1.jpg`, `product_2.jpg`, `product_3.jpg` to understand the product's exact visual details (fabric, color, cut, collar, buttons, etc.).

### Step 3: Generate 3 Keyframe Images (9:16)
- Use the image generation tool with the scraped product images as reference.
- Pass Frame 1 as reference to Frame 2, and both to Frame 3, for character consistency.
- Save generated images to the workspace root as `<product_prefix>_frame1_front.jpg`, `<product_prefix>_frame2_side.jpg`, `<product_prefix>_frame3_shoulder.jpg`.

**CRITICAL KEYFRAME RULES:**
- Frame 1: Front-facing, relaxed natural smile, comfortable eye contact.
- Frame 2: 3/4 side profile, showing fabric drape and cut.
- Frame 3: Over-the-shoulder glance. Arms and hands rest naturally at sides or holding bag casually. **NO WAVING. NO RAISED HANDS.**
- All frames: Same model, same hijab, same outfit, same background. Full outfit head-to-toe visible.

### Step 4: Write Organic Spoken Dialogue (Check History First!)
Before writing ANY dialogue:
```python
from generate_prompts import get_recently_used_phrases
print(get_recently_used_phrases())
```
This shows the last 7 used opening lines and closing lines. The new dialogue **MUST differ from all 7**.  Phrases older than 7 entries are fine to reuse.

**Any opener style is valid** — "Kalau korang", "Hari ni saya nak share", "Saya baru je cuba", etc. — as long as it's not in the recent 7 history.

### Step 5: Compose the Full Deliverable Package
Deliver to the user in this order:
1. **3 Keyframe Images** (embedded or linked)
2. **3 Flow AI Video Prompts** (Scene 1, 2, 3 with spoken dialogue in English for Flow to translate)
3. **TikTok Caption + Hashtags**
4. **Suno AI BGM Prompt + Lyrics**

### Step 6: Log to Generation History
After EVERY generation, you MUST log the new entry:
```python
from generate_prompts import save_generation_history
save_generation_history(
    product_name="Product Name Here",
    opening_line="The exact Scene 1 opening line used",
    closing_line="The exact Scene 3 closing line used"
)
```

### Step 7: Commit & Push
```bash
git add generation_history.json
git commit -m "Log generation history for <product name>"
git push
```

---

## Strict Content Rules

### Language
- ALL spoken dialogue: **Standard Malaysian Malay (Bahasa Melayu Malaysia, KL/urban accent)**.
- **STRICTLY NOT Indonesian** (no "banget", "emang", "keren", "bgt").
- Natural Malaysian slang is OK: "korang", "gila", "serious", "tau tak", "eh", "kan".
- First-person pronoun: Always **"saya"** (NOT "aku").

### Banned Characters
- **NEVER** use em-dash `—` or en-dash `–` anywhere in TikTok captions.
- Use colon `:`, comma `,`, or natural phrasing instead.

### Pricing
- **NEVER** mention direct prices in captions (violates TikTok Shop policy).

### Hashtags
- **BANNED:** `#RacunTikTok`, `#fyp`, `#viral`, or any generic spam tags.
- Use only **4–6 high-intent, targeted SEO hashtags** in format:
  - Product keyword (e.g. `#BlazerWanita`)
  - Occasion/Pain Point (e.g. `#OutfitKePejabat`)
  - Niche Community (e.g. `#MuslimahStyleMY`)

### Scene 3 Body Language
- Arms rest naturally at sides or holding bag casually.
- **NO awkward waving. NO raised hands.**

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `generate_prompts.py` | Core engine: SYSTEM_PROMPT, anti-repetition functions, Gemini API caller |
| `prompt_templates.py` | Reusable templates for keyframes, Flow AI prompts, caption, and Suno BGM |
| `generation_history.json` | Tracks last used opening/closing lines to prevent repetition (window: last 7) |
| `scrape_product.py` | Scrapes TikTok Shop product page → images + metadata |
| `.env` | Contains `GEMINI_API_KEY` and `GOOGLE_API_KEY` (gitignored, never commit) |
| `.gitignore` | Excludes `.env`, images, output dir, and temp files from git |

---

## Anti-Repetition System

- **File:** `generation_history.json`
- **Window:** Last **7** entries only.  Older entries can be freely reused.
- **How it works:**
  1. `get_recently_used_phrases(last_n=7)` loads the 7 most recent entries.
  2. The output is injected into the Gemini prompt as context.
  3. The AI must write dialogue that differs from all 7.
  4. After generation, `save_generation_history()` appends the new entry.
- **No fixed rotation scripts.** No banned phrases.  Just awareness of what was recently said.

---

## Flow AI Video Prompt Structure

Each scene prompt is a **single English paragraph** combining:
- **Visual:** Camera movement, subject action, body language, clothing details.
- **Audio:** "For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent."
- **Dialogue:** "Explicitly translate the following English text into standard Malaysian Malay for the spoken audio: ..."

The English dialogue text provided will be auto-translated by Flow's audio engine into natural spoken Malaysian Malay with lip-sync.

---

## TikTok Caption Structure

```
{relatable_hook_question} {emoji}

{product_pitch_paragraph}

Kelebihan [product] ni yang buat saya suka:
✨ Feature 1: Description
✨ Feature 2: Description
✨ Feature 3: Description
✨ Feature 4: Description
✨ Feature 5: Description

{styling_tips} {emoji}

{CTA pointing to beg kuning} 👇💛

#Hashtag1 #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5 #Hashtag6
```

---

## Suno AI BGM Structure

- **Style Prompt:** Specific genre + instruments + mood (tailored to the product vibe).
- **Lyrics:** Bahasa Melayu, structured as `[Verse]`, `[Chorus]`, `[Outro]`.
  - Always end with a line about "beg kuning" (yellow basket CTA).
