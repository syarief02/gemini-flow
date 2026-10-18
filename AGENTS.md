# AGENTS.md — Gemini Flow Workspace Instructions
# ================================================
# This file tells any AI agent (Antigravity, Gemini, etc.) exactly how this
# workspace operates.  Read this FIRST before doing anything in this repo.

## What This Workspace Does

This is an **autonomous end-to-end TikTok Shop Product Promo Generator** for the Malaysian market.
Given a single TikTok Shop product URL, the complete pipeline automatically executes:

1. **3 Consistent 9:16 Keyframe Images** (Front, Side, Over-Shoulder poses) & Supabase CDN upload
2. **TikTok Caption + SEO Hashtags** (Bahasa Melayu Malaysia, policy-safe, 1-click copy box)
3. **3 Flow AI Video Generations in Browser** (Omni Flash 10s portrait, Frame-to-Video via Brave CDP)
4. **Automated Gmail Promo Reply in Browser** (Instantly replies to the user's email thread in Brave with the full copy package)
5. **Suno AI Instrumental BGM Generation in Browser** (Configures and triggers pure instrumental BGM creation on `suno.com/create`)
6. **Supabase Cloud Sync & Git Tracking** (Full record stored in `gemini_flow_generations` and pushed to GitHub)

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
- **MANDATORY HYBRID GENERATION**: ALWAYS attempt to generate the images before giving prompts. Do not stop after a single image-model failure.
- Use the following fallback order, continuing until all three images are generated or no usable option remains:
  1. Use the session's native image-generation tool (`generate_image` / ImageGen) when it is callable.
  2. If it is unavailable, disabled, or quota-limited, inspect the tools and models available in the current session for another image-capable provider.
  3. Use an already configured workspace provider next, such as Gemini or Imagen through `GEMINI_API_KEY` or `GOOGLE_API_KEY` in `.env`, when it can generate images. Never expose secret values.
  4. Use an OpenAI Images API fallback only when an `OPENAI_API_KEY` is already configured or the user explicitly authorizes setting one up. Follow any active image-generation skill restrictions.
  5. Do not use an unconfigured external website, ask the user to paste a credential, or claim generation succeeded when it did not.
- A provider is "available" only when its tool or API is callable, its required credential is already configured or explicitly authorized, and its use is permitted by the active environment and instructions.
- Pass the scraped product images as visual reference (e.g. `product_1.jpg`, `product_2.jpg`).
- Pass Frame 1 as reference to Frame 2, and both to Frame 3, for character consistency.
- Save generated images to the dedicated `keyframes/` directory in the workspace root as `keyframes/<product_prefix>_frame1_front.jpg`, `keyframes/<product_prefix>_frame2_side.jpg`, `keyframes/<product_prefix>_frame3_shoulder.jpg` (create `keyframes/` directory automatically if it does not exist).

**Quota Tracking & Reporting Rules (MANDATORY EVERY RUN):**
- You MUST report the image generation quota status in EVERY generation response to the user:
  1. **Quota Status & Image Count**: State clearly how many images were successfully generated in the run (e.g. `3/3 images successfully generated`) and current operational capacity.
  2. **If Any Provider Is Active/Available**: Inform the user which provider completed the images and that its capacity is active for continuous runs, subject to that provider's limits.
  3. **If a Provider Hits 429 RESOURCE_EXHAUSTED**:
     - Clearly report that provider's quota limit, including the exact reset countdown and timestamp when present in the error.
     - Immediately continue with the next available provider. Do not provide prompt-only output while a viable configured image provider remains.
  4. **If a Provider Is Unavailable for Another Reason**: State the provider and cause, such as tool not exposed, unsupported model, missing credential, or permission restriction. Do not call it a quota limit or invent a reset time.
  5. **Only When All Options Are Exhausted**: State how many images could not be generated and provide the three ready-to-use 9:16 fallback prompts for external generation. Include the attempted providers and the actual reason each was unavailable.

**CRITICAL KEYFRAME RULES (INVARIANT CONTINUITY ARCHITECTURE):**
- Model styling: Malaysian Muslimah wearing a neat, matching modern hijab (e.g. chiffon/bawal) and modest chic outfit.
- Frame 1: Front-facing, relaxed natural smile, comfortable eye contact. Empty hands resting naturally at sides.
- Frame 2: 3/4 side profile, showing fabric drape and cut. Empty hands (one hand may lightly touch garment seam).
- Frame 3: Over-the-shoulder glance. Both arms resting naturally low at sides with EMPTY hands.
- **STRICT ZERO-PROP & EMPTY-HANDS RULE**: Never introduce any handbag, tote bag, purse, tumbler, cup, phone, or props in ANY frame. Inconsistent props between Frame 1 and Frame 3 ruin video generation and create popping/morphing artifacts.
- **ALL FRAMES INVARIANT ANCHOR**: Same model face, same hijab wrap & color, same garment details, same bottoms (pants/skirt), same shoes, same empty hands, and same background environment across all 3 frames. Full outfit head-to-toe visible.
- **NO WAVING. NO RAISED HANDS.**

### Step 4: Craft Viral Hooks & Organic Spoken Dialogue (Search Internet Data First!)

**Strict Rule: NEVER BAN ANY HOOKS**:
- **Do NOT ban any hooks, opener styles, or formulas.** All hook structures are valid (e.g. relatable dilemma, direct question, visual pattern interrupt, bold confession, viral curiosity gap, aesthetic lifestyle comparison).
- **We simply record every used hook so they do not repeat within the recent 7-entry window.**
- Hooks older than the 7-entry window can be freely reused and refreshed.

**MANDATORY: Live Search → Rank → Pick Top 1 (NEVER SKIP)**:
Before writing Scene 1 dialogue, the agent MUST follow this exact 3-step process:

> **Step 4a. Live Web Search (MANDATORY EVERY RUN)**:
> Search the internet for **at least 2 different queries** tailored to the specific product:
> - Query 1: Top-performing TikTok e-commerce hooks for the specific product category in Malaysia / Southeast Asia.
> - Query 2: Highest retention rate hook formulas for fashion/outerwear/[product type] TikTok 2026.
> The agent MUST NOT skip the live search and rely solely on the internal archetype list.

> **Step 4b. Rank Candidate Hooks (MANDATORY EVERY RUN)**:
> From the live search results combined with the 8 proven archetypes below, create **at least 3 candidate hooks** in Malaysian Malay. Rank them by:
> 1. **Immediacy** (30%): Does it deliver value in <2 seconds?
> 2. **Specificity** (25%): Does it name a concrete pain point + product differentiator?
> 3. **Social proof / pattern interrupt power** (20%)
> 4. **Malaysian locale resonance** (15%): Relatable local scenario
> 5. **Non-repetition vs last 7 entries** (10%)
> Run `verify_hook_quality()` on each candidate and display results.

> **Step 4c. Select Winner (MANDATORY EVERY RUN)**:
> Pick the **#1 ranked hook** as the Scene 1 opening line. Display the ranking table to the user.

**8 Proven Viral Hook Archetypes (2-Second Retention Rule)**:
1. **The Unspoken Daily Dilemma (Tropical Climate / Comfort)**: e.g. Hot weather sauna effect, humid sweat, stuffy fabrics vs breathable water-resistant protection.
2. **The Flattering Silhouette / Visual Insecurity Solution**: e.g. Afraid loose cut looks frumpy or thighs look wide vs auto-slimming elongating drape.
3. **The Price-Quality Myth-Buster**: e.g. Expecting to pay hundreds at branded outdoor stores vs premium durable quality at affordable price.
4. **The Hidden Gem / Secret Discovery**: e.g. Effortless 2-second styling secret, the hidden gem cutting nobody is talking about.
5. **The Visual Pattern Interrupt / Direct Question**: e.g. "Korang perasan tak...", "Tahu tak kenapa...", "Siapa dekat sini yang...".
6. **The Relatable Lifestyle Dilemma**: e.g. Waking up late, rushing to office/campus, hating ironing clothes.
7. **The Stereotype-Buster / Pain-Point Contrast**: e.g. "Siapa cakap jaket kalis air mesti nampak boyish?" challenging common assumptions about the product category.
8. **The FOMO / FYP Social Proof Trend**: e.g. "Patutlah asyik lalu dekat FYP..." leveraging social proof and trend awareness.

**Check History Window & Verify Hook Quality**:
```python
from generate_prompts import get_recently_used_phrases, verify_hook_quality, detect_hook_archetype
print(get_recently_used_phrases())

# Audit hook before finalizing
audit = verify_hook_quality(selected_scene_1_opening)
print("Hook Archetype:", audit["archetype"])
print("Quality Audit:", audit)
```
Ensure the selected hook and closing line differ from the last 7 recorded entries and achieve a passing quality score.


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

### Step 6: Automate Flow AI Video Generation in Browser (Brave)
- Connect to Brave running with `--remote-debugging-port=9222 --remote-allow-origins=*` using Playwright CDP (`automate_flow.py`).
- If Brave is not currently running with debugging flags, restart it with debugging enabled:
  ```powershell
  Stop-Process -Name brave -Force -ErrorAction SilentlyContinue ; Start-Sleep -Seconds 2 ; Start-Process "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" -ArgumentList "--remote-debugging-port=9222", "--remote-allow-origins=*", "https://flow.google.com/?pli=1&authuser=5" ; Start-Sleep -Seconds 4
  ```
- Navigate to Google Flow AI project (`https://flow.google.com/`).
- Set video parameters: **Duration = 10s**, **Orientation = Portrait (9:16)**, **Model = Omni Flash**, **Mode = Frame to Video**.
- Configure the 3 scene sequences:
  - **Scene 1**: Start = `Frame 1 (Front)`, End = `Frame 2 (Side)` + Scene 1 Prompt
  - **Scene 2**: Start = `Frame 2 (Side)`, End = `Frame 3 (Shoulder)` + Scene 2 Prompt
  - **Scene 3**: Start = `Frame 3 (Shoulder)`, End = `Frame 1 (Front)` [Seamless 360 Loop] + Scene 3 Prompt
- Trigger video rendering and capture progress screenshot (`flow_renders_progress.png`).

### Step 7: Automate Gmail Promo Reply in Browser (Brave)
- Connect to Brave on port 9222 using `reply_gmail.py`.
- Find or navigate to the user's active promo email thread (`(no subject)` or promo email with the TikTok link in `syarief.azman@gmail.com`).
- Click **Reply** button or press keyboard shortcut `r`.
- Insert the complete promo package in clean formatted text:
  - Product title & TikTok Shop links
  - Flow AI Project URL & settings
  - Complete TikTok Caption + Hashtags (zero em-dashes, zero direct prices)
  - Spoken Malay Lip-sync breakdown
  - Supabase CDN keyframe image links
  - Suno AI Instrumental BGM prompt
- Click **Send** to immediately dispatch the reply inside the browser.
- Capture sent confirmation screenshot (`gmail_reply_sent.png`).

### Step 8: Automate Suno AI Instrumental BGM Generation in Browser (Brave)
- Connect to Brave on port 9222 using `create_suno.py`.
- Navigate to `https://suno.com/create`.
- Ensure **Instrumental mode is toggled ON** (strictly no vocals to avoid clashing with Flow AI spoken dialogue).
- Enter the tailored BGM style prompt into the style textarea.
- Enter a clear descriptive title for the track.
- Click **Create** to initiate song generation.
- Capture generation confirmation screenshot (`suno_generating.png`).

### Step 9: Sync to Supabase & Log Generation History
- Log the new entry to `generation_history.json` to prevent repetition in the recent 7-entry window:
  ```python
  from generate_prompts import save_generation_history
  save_generation_history(
      product_name="Product Name Here",
      opening_line="The exact Scene 1 opening line used",
      closing_line="The exact Scene 3 closing line used"
  )
  ```
- Sync generation record, scenes, caption, hashtags, and Supabase CDN keyframe URLs to Supabase `gemini_flow_generations`:
  ```python
  import supabase_client
  supabase_client.save_generation_record(
      product_name="Product Name Here",
      opening_line="...",
      closing_line="...",
      caption="...",
      hashtags="...",
      bgm_prompt="...",
      keyframe_urls=[...],
      metadata={...}
  )
  ```

### Step 10: Commit & Push
```bash
git add generation_history.json automate_flow.py reply_gmail.py create_suno.py
git commit -m "feat: complete end-to-end promo generation for <product name>"
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
- Both arms rest naturally low at sides with EMPTY hands.
- **STRICTLY NO bags, NO totes, NO props, NO awkward waving, NO raised hands.**

### AIGC Compliance
- All keyframe images and Flow AI videos are AI-generated synthetic media.
- User MUST enable TikTok's "AI-generated content" toggle when posting.
- Always include the AIGC disclosure reminder in every deliverable package.

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `generate_prompts.py` | Core engine: SYSTEM_PROMPT, anti-repetition functions, Gemini API caller |
| `generate_keyframes.py` | Generates 3 consistent 9:16 keyframe images dynamically for any product session |
| `prompt_templates.py` | Reusable templates for keyframes, Flow AI prompts, caption, and Suno BGM |
| `automate_flow.py` | Flow AI video generation operator in Brave browser via Playwright CDP |
| `reply_gmail.py` | Automated Gmail reply script in Brave browser to dispatch copy packages via CDP |
| `create_suno.py` | Automated Suno AI BGM instrumental generator in Brave browser via CDP |
| `open_brave.bat` | Launcher batch script to start Brave with remote debugging on port 9222 |
| `generation_history.json` | Tracks last used opening/closing lines to prevent repetition (window: last 7) |
| `supabase_client.py` | Supabase cloud database client, health monitoring, and remote generation sync |
| `publish_to_wordpress.py` | WordPress.com publishing integration for promo articles and affiliate links |
| `tiktok_policy_notes.md` | **TikTok policy tracker**: compiled rules, violations, AIGC requirements, and change log |
| `scrape_product.py` | Scrapes TikTok Shop product page → images + metadata |
| `.env` | Contains `GEMINI_API_KEY`, Supabase, and WordPress credentials (gitignored, never commit) |
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

## Anti-Repetition & Viral Hook System

- **File:** `generation_history.json` & Supabase Database
- **Window:** Last **7** entries only. Older entries can be freely reused.
- **How it works:**
  1. **Zero Banned Hooks**: NEVER ban any hook styles or formulas. All hook techniques (pain-point questions, relatable confessions, visual pattern interrupts, curiosity gap) are valid.
  2. **Search Internet Data for Best Hooks**: Before writing, search current TikTok e-commerce data and viral retail trends for high-converting hook formulas in Malaysia.
  3. **Record to Avoid Repetition**: `get_recently_used_phrases(last_n=7)` retrieves the last 7 recorded openers and closers. The new dialogue simply avoids repeating those 7.
  4. **Auto-Logging**: After generation, `save_generation_history()` logs the newly created hook and CTA to both local history and Supabase.
- **No fixed rotation scripts.** No banned hooks. Data-driven viral hooks with recent history awareness.

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

---

## Browser Automation Architecture via Playwright CDP (Brave)

To ensure seamless, hands-free generation directly inside the user's desktop browser without requiring credentials or session tokens, the workspace uses **Chrome DevTools Protocol (CDP)** attached to **Brave Browser**:

### 1. Launching Brave with Debugging
- Brave executable path: `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`
- When starting or restarting Brave for automation, ALWAYS pass:
  ```powershell
  Stop-Process -Name brave -Force -ErrorAction SilentlyContinue ; Start-Sleep -Seconds 2 ; Start-Process "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" -ArgumentList "--remote-debugging-port=9222", "--remote-allow-origins=*", "<target_url>" ; Start-Sleep -Seconds 4
  ```
- **Port 9222**: Dedicated remote debugging listener.
- **`--remote-allow-origins=*`**: Mandatory flag for Chromium 130+ to permit Playwright websocket connections.

### 2. Playwright Attachment Pattern
In any browser automation script:
```python
from playwright.async_api import async_playwright

p = await async_playwright().start()
browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
context = browser.contexts[0]
# Use existing tab or create new tab
# NEVER call browser.close() so the user's browser window remains open and visible!
await p.stop()
```

### 3. Automated Browser Tasks Sequence
Whenever the user supplies a TikTok Shop product link:
1. **Google Flow AI (`automate_flow.py`)**:
   - Tab: `https://flow.google.com/`
   - Configures 10s portrait, Omni Flash, Frame-to-Video.
   - Uploads Frame 1 ➡️ 2 (Scene 1), Frame 2 ➡️ 3 (Scene 2), Frame 3 ➡️ 1 (Scene 3).
   - Pastes bilingual spoken dialogue prompts and starts renders.
2. **Gmail Promo Package Reply (`reply_gmail.py`)**:
   - Tab: `https://mail.google.com/mail/u/0/#inbox`
   - Finds the active promo thread (`(no subject)` or product link thread).
   - Clicks **Reply**, fills the formatted caption + hashtag package + video links, and clicks **Send**.
3. **Suno AI Instrumental BGM (`create_suno.py`)**:
   - Tab: `https://suno.com/create`
   - Sets mode to **Instrumental** (strictly no vocals).
   - Pastes the generated acoustic/lo-fi style prompt and title, then clicks **Create**.

