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
4. **Suno AI BGM Instrumental Prompt** (One comprehensive style prompt, no lyrics)

---

## End-to-End Workflow (Step by Step)

> ⛔ **MANDATORY PRE-FLIGHT GATE — NEVER SKIP STEP 0**:
> Under NO circumstances may an agent proceed directly to Step 1 (`scrape_product.py`) when given a TikTok product URL without completing Step 0.
> Skipping Step 0 is a critical workflow violation. Every deliverable package MUST start with the **Policy Compliance Badge**.

### Step 0: Policy Compliance Check (MANDATORY FIRST STEP)

Before generating ANY content or running scraper tools, you MUST verify that our output will comply with TikTok's latest policies.

**0a. Run the pre-flight policy check tool:**
```bash
python check_policy.py "[Product Category or Link Query]"
```
And open and review the local policy file:
```
Open and review: tiktok_policy_notes.md
```
This file contains our compiled understanding of TikTok Shop, Affiliate, AIGC, and Community policies.

**0b. Search online for the latest policy updates:**
Search the web for the latest TikTok Shop content policy, affiliate policy, and AIGC policy changes (mandatory if >7 days since the last verified date in `tiktok_policy_notes.md`).
Compare findings against what's in `tiktok_policy_notes.md`.

**0c. If new rules or changes are found:**
- Update `tiktok_policy_notes.md` with the new information.
- Add an entry to the **Change Log** table at the bottom of the file with the date, change description, and source.
- Commit and push the updated policy file:
```bash
git add tiktok_policy_notes.md
git commit -m "Update TikTok policy notes: <brief description of change>"
git push
```

**0d. Apply compliance to all content:**
Cross-check the product category against the prohibited/restricted categories in `tiktok_policy_notes.md`.
If the product falls into a prohibited category, STOP and inform the user immediately.

**Key policies to always verify:**
- Pricing rules (no misleading prices; we avoid direct prices entirely)
- AIGC disclosure requirements (remind user to toggle "AI-generated content" when posting)
- Product-content match (video must match linked product)
- No medical/weight-loss claims
- No prohibited product categories
- Hashtag rules (no spam tags)

### Step 1: Scrape the Product
```bash
python scrape_product.py "https://vt.tiktok.com/..."
```
- Pre-flight compliance check runs automatically during scraping.
- Resolves short URL → full TikTok Shop PDP page.
- Downloads all product listing images as `.jpg` into `output/<timestamp>/`.
- Extracts product title, description, policy status, and metadata.

### Step 2: View the Scraped Product Images
- Open `output/<timestamp>/product_1.jpg`, `product_2.jpg`, `product_3.jpg` to understand the product's exact visual details (fabric, color, cut, collar, buttons, etc.).

### Step 3: Generate 3 Keyframe Images (9:16)
- **MANDATORY**: ALWAYS attempt to generate the images first using the image generation tool (`generate_image`). Do not skip straight to giving prompts.
- Pass the scraped product images as visual reference (e.g. `product_1.jpg`, `product_2.jpg`).
- Pass Frame 1 as reference to Frame 2, and both to Frame 3, for character consistency.
- Save generated images to the dedicated `keyframes/` directory in the workspace root as `keyframes/<product_prefix>_frame1_front.jpg`, `keyframes/<product_prefix>_frame2_side.jpg`, `keyframes/<product_prefix>_frame3_shoulder.jpg` (create `keyframes/` directory automatically if it does not exist).

**Quota Tracking & Reporting Rules (MANDATORY EVERY RUN):**
- You MUST report the image generation quota status in EVERY generation response to the user:
  1. **Quota Status & Image Count**: State clearly how many images were successfully generated in the run (e.g. `3/3 images successfully generated`) and current operational capacity.
  2. **If Quota is Active/Available**: Inform the user that the image generation capacity is healthy/active for continuous runs.
  3. **If Quota Limit (429 RESOURCE_EXHAUSTED) is Hit**:
     - Clearly alert the user: "Image generation quota limit has been reached."
     - Report the exact reset countdown and timestamp extracted from the error message (e.g., `Resets in: X hours / Date: YYYY-MM-DD`).
     - State how many images could not be generated.
     - Provide the 3 ready-to-use 9:16 Keyframe Prompts as fallback for external generation (Midjourney, Flux, Imagen, Gemini Web).

**CRITICAL KEYFRAME RULES:**
- Model styling: Malaysian Muslimah wearing a neat, matching modern hijab (e.g. chiffon/bawal) and modest chic outfit.
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
Deliver to the user in this exact order:
1. **Verification Badges & 3 Keyframe Images**:
   - **MANDATORY Policy Badge**: Always display policy verification status:
     `🛡️ Status Pematuhan Polisi TikTok: Disemak & Patuh (Tarikh: YYYY-MM-DD | Kategori: [Kategori] - Dibenarkan)`
   - **MANDATORY Quota Badge**: Always display quota status:
     `🟢 Status Kuota Imej: Aktif (3/3 imej berjaya dijana)` OR `🔴 Status Kuota Imej: Had kuota tercapai (Reset dalam: X jam)`.
   - **MANDATORY Frame Filenames & Dedicated Location**: Always explicitly list the exact filenames and full path inside the dedicated `keyframes/` folder (`c:\Users\User\OneDrive\Desktop\gemini flow\keyframes\`) so the user can immediately locate and upload them to Flow AI.
   - Embed the 3 generated images from `keyframes/` (Frame 1 Front, Frame 2 Side, Frame 3 Shoulder).
   - If quota was exhausted, clearly state the quota limit and supply the 3 detailed 9:16 fallback prompts.
2. **3 Flow AI Video Prompts** (Scene 1, 2, 3):
   - **MANDATORY**: Each scene prompt AND its exact spoken Malay lip-sync dialogue MUST be enclosed together in the **SAME code box** for easy 1-click copying. Do NOT separate the lip-sync dialogue outside the box.
3. **TikTok Caption + Hashtags**:
   - **MANDATORY**: Enclose the entire caption AND hashtags together in a single code/text box (`text`) for easy 1-click copying. Do NOT leave as unboxed markdown.
4. **Suno AI Instrumental BGM Prompt** (One comprehensive style prompt tailored for Suno Instrumental mode — strictly no lyrics)
5. **⚠️ AIGC Reminder** — Always include this note at the end:
   > **Reminder:** This content is AI-generated. When posting to TikTok, enable the "AI-generated content" toggle in posting settings to comply with TikTok's AIGC disclosure policy.

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
- **NEVER** mention direct prices in captions (violates TikTok Shop policy on conditional pricing).
- Direct viewers to "beg kuning" (yellow basket) instead.

### Hashtags
- **BANNED:** `#RacunTikTok`, `#fyp`, `#viral`, or any generic spam tags.
- Use only **4–6 high-intent, targeted SEO hashtags** in format:
  - Product keyword (e.g. `#BlazerWanita`)
  - Occasion/Pain Point (e.g. `#OutfitKePejabat`)
  - Niche Community (e.g. `#MuslimahStyleMY`)

### Scene 3 Body Language
- Arms rest naturally at sides or holding bag casually.
- **NO awkward waving. NO raised hands.**

### AIGC Compliance
- All keyframe images and Flow AI videos are AI-generated synthetic media.
- User MUST enable TikTok's "AI-generated content" toggle when posting.
- Always include the AIGC disclosure reminder in every deliverable package.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `generate_prompts.py` | Core engine: SYSTEM_PROMPT, anti-repetition functions, Gemini API caller |
| `prompt_templates.py` | Reusable templates for keyframes, Flow AI prompts, caption, and Suno BGM |
| `generation_history.json` | Tracks last used opening/closing lines to prevent repetition (window: last 7) |
| `tiktok_policy_notes.md` | **TikTok policy tracker**: compiled rules, violations, AIGC requirements, and change log |
| `scrape_product.py` | Scrapes TikTok Shop product page → images + metadata |
| `.env` | Contains `GEMINI_API_KEY` and `GOOGLE_API_KEY` (gitignored, never commit) |
| `.gitignore` | Excludes `.env`, images, output dir, and temp files from git |

---

## TikTok Policy Compliance System

- **File:** `tiktok_policy_notes.md`
- **Purpose:** Single source of truth for all TikTok Shop, Affiliate, AIGC, and Community policies.
- **How it works:**
  1. AI reads the file at the START of every generation session (Step 0).
  2. AI searches online for any policy updates or changes.
  3. If new rules are found, AI updates the file and adds to the Change Log.
  4. AI cross-checks the product category against prohibited categories.
  5. AI ensures all generated content complies with documented rules.
  6. Updated policy file is committed and pushed to Git for version tracking.
- **Change Log:** Bottom of `tiktok_policy_notes.md` — records date, change, and source for every policy update detected.

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

**CRITICAL PACKAGING RULE — WRAP IN SAME CODE BOX FOR 1-CLICK COPY:**
ALWAYS wrap the Flow AI prompt AND the spoken Malay lip-sync dialogue in the **SAME text / code box**.
Do NOT separate the spoken Malay into an external quote below the box. This allows the user to click the copy button (`📋`) on the code box once to copy everything needed for that scene cleanly.

Example layout:
```text
A smooth front-facing medium camera shot with subtle slow zoom-in on an aesthetic Malaysian Muslim woman... For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Explicitly translate the following English text into standard Malaysian Malay for the spoken audio: "..." Ensure there are no text overlays or watermarks.

Spoken Malay (Lip-sync):
"Ayat dialog bahasa Melayu di sini..."
```

---

## TikTok Caption Structure

**CRITICAL PACKAGING RULE — WRAP IN CODE BOX FOR 1-CLICK COPY:**
ALWAYS deliver the full caption and hashtags inside a single code box (`text`) so the user can copy everything in 1 click.

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

## Suno AI BGM Structure (Instrumental Only)

- **NO LYRICS NEEDED**: TikTok Shop video promos use spoken Malay lip-sync voiceovers from Flow AI. Background music with singing/lyrics clashes with the spoken audio. Suno is set to **Instrumental** mode.
- **Single Comprehensive Style Prompt**: Provide ONE detailed, highly descriptive prompt for Suno's "Song Description" / "Style of Music" box.
- **Components to Include in the Style Prompt**:
  - **Genre & Subgenre**: e.g. Upbeat lo-fi indie chill pop, modern acoustic groove, chillout synthwave, cheerful cafe pop.
  - **Instrumentation**: Specific instruments (e.g. fingerpicked acoustic guitar, subtle Rhodes piano, crisp lo-fi drum snare, warm analog synth bass).
  - **Mood & Atmosphere**: e.g. breezy, optimistic, fashionable, relaxing, modern Malaysian lifestyle vibe.
  - **Tempo/Pacing**: BPM guidance (e.g. 108–115 BPM, smooth rhythm matched for short-form video pacing).
  - **Production Quality**: "pure instrumental, no vocals, high-quality production, warm acoustic mixing, seamless loopable feel".
