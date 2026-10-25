# AGENTS.md — Gemini Flow Workspace Instructions
# ================================================
# This file tells any AI agent (Antigravity, Gemini, etc.) exactly how this
# workspace operates.  Read this FIRST before doing anything in this repo.

## What This Workspace Does

This is an **autonomous end-to-end TikTok Shop Product Promo Generator** for the Malaysian market.
Given a single TikTok Shop product URL, the complete pipeline automatically executes:

1. **3 Consistent 9:16 Keyframe Images** (Front, Side, Over-Shoulder poses), saved in `keyframes/` and committed to GitHub
2. **TikTok Caption + SEO Hashtags** (Bahasa Melayu Malaysia, policy-safe, 1-click copy box)
3. **3 Flow AI Video Generations in Browser** (Omni Flash 10s portrait, Frame-to-Video via Brave CDP)
4. **Automated Gmail Promo Reply in Browser** (Instantly replies to the user's email thread in Brave with the full copy package)
5. **Suno AI Instrumental BGM Generation in Browser** (Configures and triggers pure instrumental BGM creation on `suno.com/create`)
6. **GitHub Record & Asset Tracking** (Full record in `generations/<prefix>.json`, keyframes in `keyframes/`, both committed and pushed)

---

## 🛑 MANDATORY ZERO-MISTAKE RULES (READ BEFORE RUNNING)

Every AI agent operating in this repository MUST memorize and adhere strictly to these critical rules. These rules prevent the most frequent past mistakes:

| Area | ❌ FATAL MISTAKE (NEVER DO THIS) | ✅ CORRECT BEHAVIOR (MANDATORY) |
|------|-----------------------------------|----------------------------------|
| **Gmail Promo Reply** | Composing a brand new email thread, replying to a random or top email without verifying the product link, adding greetings ("Salam Syarief"), section headers ("MAKLUMAT PRODUK"), Flow video prompts, Suno prompts, dividers (`===`), image or GitHub links, or leaving Gmail quoted text / previous thread content. | **ALWAYS CHECK EXACT PRODUCT LINK IN EMAIL FIRST, THEN REPLY.** Search Gmail for the exact product link/shortcode. If no email contains that exact link, **ABORT IMMEDIATELY** (never compose a new email, never reply to an unrelated email). Once opened, verify the thread body contains the link, expand and delete quoted text (`div.gmail_quote` / `div.ajR`), and enter **STRICTLY AND ONLY THE CLEAN TIKTOK CAPTION + HASHTAGS**. |
| **Brave CDP Connection** | Attempting to connect to an existing Brave instance without flags or launching without `--remote-allow-origins=*`, or calling `browser.close()` which kills the user's window. | Always launch with `--remote-debugging-port=9222 --remote-allow-origins=*`. **NEVER call `browser.close()`** so the user's visible interactive window stays open on desktop. |
| **Keyframe Consistency** | Adding handbags, totes, phones, coffee cups, tumblers, waving hands, or changing hijab/bottoms between frames. | **Strict Zero-Prop & Empty-Hands Rule.** Both hands empty at sides. Same model, same modest hijab, same outfit head-to-toe, same background across all 3 frames. |
| **Flow AI Parameters** | Using 5s/8s duration, landscape 16:9, or text-to-video mode. | **Duration = 10s**, **Orientation = Portrait (9:16)**, **Model = Omni 1.1 Flash**, **Mode = Video + Frames** (Frame 1➡️2, Frame 2➡️3, Frame 3➡️1), **720p**, **x1**. |
| **Flow Project per Product** | Rendering a new product's keyframes or videos into an existing project (e.g. the old shared "Oct 19 - 02:05" project), which mixes products, makes picker searches ambiguous, and hides which clip belongs to which product. | **Every new product gets its OWN new Flow project**, created once at the start of its first Flow step: `python automate_flow.py --create-project "<Short Product Name>" --prefix <prefix>`. The project URL is recorded in `flow_projects.json`; all keyframe generation (Flow Image mode), uploads and renders for that product happen only in that project. Re-renders reuse it; never create a second project for the same prefix. |
| **Flow AI Frame Attachment** | Submitting while a `Start`/`End` slot is still empty (Flow silently renders **text-to-video**: a different woman, no hijab, wrong garment). Searching a partial tag like `frame1_front` (matches EVERY product) or clicking picker rows by position (the list re-sorts by recent use). | Search the **full filename** (`<prefix>_frame1_front.jpg`), click the row whose text **exactly** equals it, and confirm the slot turned into an image chip showing the right pose. **Never click `Start generation` until BOTH slots are verified.** `automate_flow.py` enforces this with a pixel match against the local keyframes. |
| **Flow AI Frame Pairing** | Reversing Start/End frames (e.g. putting Side as Start in Scene 1), uploading mismatched files, or guessing frame order. | **STRICT DIRECTIONAL CONTINUITY:** **Scene 1:** Start = Frame 1 (Front) ➡️ End = Frame 2 (Side); **Scene 2:** Start = Frame 2 (Side) ➡️ End = Frame 3 (Shoulder); **Scene 3:** Start = Frame 3 (Shoulder) ➡️ End = Frame 1 (Front 360° Loop). |
| **Flow AI Spoken Lip-Sync** | Submitting English-only visual prompt to Flow AI without the spoken dialogue, or separating dialogue outside the composer. | **MANDATORY VERBATIM LIP-SYNC IN COMPOSER:** The prompt entered into Flow AI's composer MUST explicitly include BOTH the English visual instructions AND the verbatim Malaysian Malay dialogue block: `Spoken Malay (Lip-sync): "<dialogue>"`. Flow AI generates character lip-sync directly from this text. |
| **Flow AI Camera & Dialogue Fit** | "Camera glides / pans / zooms / orbits" (all 3 keyframes share one background, so camera moves cause warping). Spoken lines of ~40+ words (cut off before the clip ends) **or** short "spec list" lines of 14-21 words with colons (stretched, robotic, unnatural: the user rejected these on 2026-10-20). | Open every scene with **"Static locked-off vertical shot, the camera does not move."** and make the **model turn in place** from the Start pose to the End pose. Spoken line = **2-3 natural conversational sentences, 28-32 words** (hard limits 24-34), no colons, she **talks through the whole clip, including while turning**. Add **"No background music"** (Suno BGM is layered later). |
| **Suno AI BGM** | Generating songs with vocal lyrics or background singing. | **Instrumental mode MUST be toggled ON.** TikTok promos use spoken Malay lip-sync voiceovers; vocals clash with speech. |
| **Spoken Dialogue & Caption** | Using Indonesian words ("banget", "emang", "bgt"), em-dashes (`—`), or mentioning direct prices. | **Standard Malaysian Malay (KL accent)**, pronoun "saya" (never "aku"), zero em-dashes (use `:` or `,`), zero prices (direct to "beg kuning"). |
| **Hook Selection** | Banning valid hook formulas or reusing openers from the last 7 recorded entries. | **Never ban valid hooks.** Live search MY TikTok data, rank candidate hooks, audit with `verify_hook_quality()`, and avoid the last 7 entries. |
| **Saving to GitHub** | Leaving a product only on this PC (no `generations/<prefix>.json`, keyframes not committed), or relying on Supabase (Supabase is NOT used by Gemini Flow; the shared database is reserved strictly for other projects). | Save the full record with `save_generation_history(prefix=...)` (Step 9), then commit and push `generations/<prefix>.json`, `keyframes/<prefix>_*` and the history (Step 10). The repo is public: no credentials or tracking URLs in records. |

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
  5. **Google Flow Image mode (user-approved fallback, 2026-10-19)** when the Gemini API returns 429 or is otherwise unavailable. It uses **Nano Banana Pro** and cost **0 credits** as of 2026-10-19 (check the "Generating will use N credits" line). Agents with browser control may use it without asking again:
     - **First create this product's own Flow project** (`python automate_flow.py --create-project "<Short Product Name>" --prefix <prefix>`) and open the URL it records in `flow_projects.json` in your own tab. Generate the keyframes there, never in another product's project.
     - Composer settings: **Image** · **Nano Banana Pro** · **9:16** · **x1**.
     - Upload the main listing photo via **+** (`Add ingredients to the prompt box`) → **Upload media**, named `<prefix>_product.jpg`, and attach it (wide window: click the row, then **Add to prompt**; narrow window: clicking the row attaches it).
     - Frame 1: full keyframe prompt (exact garment details, hijab, inner top, bottoms, shoes, setting, empty hands, zero props). Frames 2 and 3: attach the **generated Frame 1** as the reference (search its generated title and click the exact row; the grid tile with the same name is NOT the picker row) and repeat every outfit and setting detail.
     - Click `Start generation` with a real click; Flow ignores a synthetic JS `.click()`. Each image takes about 20-30s.
     - Open each result and zoom on the garment before moving on. Save copies to `keyframes/<prefix>_frame1_front.jpg` etc. by downloading the open image's `src` (the largest `<img>` in the edit view) through Playwright `context.request`.
     - Report it in the quota badge, e.g. `🟢 Status Kuota Imej: Aktif (3/3 imej berjaya dijana)` + "Gemini API 429 (reset ...); generated in Flow Image mode, Nano Banana Pro, 0 credits".
  6. Do not use any other unconfigured external website, ask the user to paste a credential, or claim generation succeeded when it did not.
- A provider is "available" only when its tool or API is callable, its required credential is already configured or explicitly authorized, and its use is permitted by the active environment and instructions.
- Pass the scraped product images as visual reference (e.g. `product_1.jpg`, `product_2.jpg`).
- Pass Frame 1 as reference to Frame 2, and both to Frame 3, for character consistency.
- Save generated images to the dedicated `keyframes/` directory in the workspace root as `keyframes/<product_prefix>_frame1_front.jpg`, `keyframes/<product_prefix>_frame2_side.jpg`, `keyframes/<product_prefix>_frame3_shoulder.jpg` (create `keyframes/` directory automatically if it does not exist). Also keep the garment reference photo you used as `keyframes/<product_prefix>_product.jpg`. Everything in `keyframes/` is committed to the public GitHub repo (Step 10).

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
> **Length & style:** each scene's full spoken line (hook included) is **2-3 natural spoken sentences, 28-32 words** (`automate_flow.py` refuses under 24 or over 34). The hook is the first sentence; the next sentence explains it like a creator talking to a friend, not a spec list.

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

**Goal:** Automatically configure and trigger 3 consecutive 10-second 9:16 portrait video renders in Google Flow AI using the generated keyframe pairs.

1. **Launch Brave with Remote Debugging Enabled:**
   - Brave MUST be running with `--remote-debugging-port=9222` and `--remote-allow-origins=*` (Chromium 130+ requirement).
   - If Brave is already open without these flags, you MUST restart it using this exact PowerShell command:
     ```powershell
     Stop-Process -Name brave -Force -ErrorAction SilentlyContinue ; Start-Sleep -Seconds 2 ; Start-Process "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" -ArgumentList "--remote-debugging-port=9222", "--remote-allow-origins=*", "https://flow.google.com/?pli=1&authuser=5" ; Start-Sleep -Seconds 4
     ```
   - **CRITICAL:** NEVER call `browser.close()` in Playwright scripts when attaching to the user's browser, as that terminates the interactive desktop window. Call `await p.stop()` or simply exit Python without closing the browser.

2. **Connect via Playwright CDP (`automate_flow.py`):**
   ```python
   from playwright.async_api import async_playwright
   p = await async_playwright().start()
   browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
   context = browser.contexts[0]
   ```

3. **Verify Video Configuration Parameters (open the settings menu, never assume):**
   - The composer's settings button (`button[aria-label='Settings trigger']`) reads e.g. `Video · 720p · 10s ▯ x1`. Click it; the menu has toggle buttons (`button[role='radio']`, selected = `aria-checked="true"`) and a model dropdown (`button[aria-label='Select model family']`).
   - Required: **Video** (not Image) · **Frames** (not Ingredients) · **9:16** · **Omni 1.1 Flash** · **720p** · **10s** · **x1**. The menu shows the cost ("Generating will use 15 credits").
   - In **Frames** mode the composer shows two slots, `Start` and `End`, with a swap button between them.

4. **⛔ CRITICAL ZERO-MISTAKE RULES FOR FLOW AI (FRAMES & LIP-SYNC):**

   #### 4a. STRICT FRAME DIRECTIONAL CONTINUITY (360° SEAMLESS LOOP)
   Never reverse or guess the frame slots. The 3 scenes MUST follow this invariant circular progression:

   ```mermaid
   flowchart LR
     F1["Frame 1 (Front View)"] -->|"Scene 1 (10s)"| F2["Frame 2 (Side Profile)"]
     F2 -->|"Scene 2 (10s)"| F3["Frame 3 (Over-Shoulder)"]
     F3 -->|"Scene 3 (10s)"| F1
   ```

   | Scene | Start Frame Slot | End Frame Slot | Narrative & Visual Purpose |
   | :--- | :--- | :--- | :--- |
   | **Scene 1** | `keyframes/<prefix>_frame1_front.jpg` *(Front View)* | `keyframes/<prefix>_frame2_side.jpg` *(3/4 Side Profile)* | Establishes model identity, eye contact, and 2-second viral hook question. Transitions from front facing to 3/4 side angle. |
   | **Scene 2** | `keyframes/<prefix>_frame2_side.jpg` *(3/4 Side Profile)* | `keyframes/<prefix>_frame3_shoulder.jpg` *(Over-the-Shoulder)* | Demonstrates fabric texture, cut, waistline, and pockets. Transitions from side angle around to the back. |
   | **Scene 3** | `keyframes/<prefix>_frame3_shoulder.jpg` *(Over-the-Shoulder)* | `keyframes/<prefix>_frame1_front.jpg` *(Front View)* | Model glances warmly over shoulder, then turns smoothly back to face camera front-standing with yellow basket CTA. **Completes the 360° loop.** |

   > ❌ **CRITICAL MISTAKE TO AVOID:** Putting Frame 2 (Side) as Start in Scene 1! That causes the video to play backwards (Side ➡️ Front) and breaks viewer immersion.
   > ❌ **CRITICAL MISTAKE TO AVOID (EMPTY SLOT = TEXT-TO-VIDEO):** If either slot is still empty when you click `Start generation`, Flow does NOT warn you. It renders text-to-video and invents a different woman (no hijab, different top). This is exactly what ruined the striped split-cuff blouse run on 2026-10-19.
   > ❌ **CRITICAL MISTAKE TO AVOID (PARTIAL SEARCH / CLICK BY POSITION):** Searching `frame1_front` returns the frame 1 of EVERY product in the project, and the picker list re-sorts by recent use after every pick. Never click "the first row" or "the third row".
   > ✅ **MANDATORY ATTACHMENT PROCEDURE (Flow UI as of 2026-10-19):**
   > 1. Click **Clear prompt** (✕ on the composer) so both slots start empty.
   > 2. Click the empty `Start` slot (`.frame-trigger button.empty-chip`). An asset picker opens with a `Search` box, an `Images` filter, an **Upload media** button and a list of filenames.
   > 3. Type the **full filename**, e.g. `striped_split_cuff_blouse_frame1_front.jpg`.
   > 4. Click the row whose text **exactly** equals that filename. In the current UI this attaches immediately and closes the picker (no `Add to prompt` step; if an older preview dialog with `Add to prompt` ever appears, click it).
   > 5. If the file is not in the project, use **Upload media**, then search and click it as above.
   > 6. Confirm the slot changed from the word `Start`/`End` into an image chip (`button[aria-label='Image ingredient']` with `img.chip-image`) showing the **correct pose**: front = straight-on with collar and buttons; side = body angled, placket off-center; shoulder = back of the garment. Repeat for `End`.

   #### 4b. MANDATORY SPOKEN MALAY LIP-SYNC IN FLOW COMPOSER
   Google Flow AI / Veo generates character mouth lip-sync and audio directly from the prompt text entered into the composer. If you only provide visual descriptions, Flow generates a silent or muddled video!

   **The prompt entered into Flow AI's composer (`div.ProseMirror[role='textbox']`) MUST ALWAYS contain BOTH:**
   1. The English visual instructions: static camera, the model turning in place from the Start pose to the End pose, exact outfit and setting, audio direction.
   2. The explicit Malaysian Malay spoken lip-sync dialogue block formatted with the header `Spoken Malay (Lip-sync): "<dialogue>"`.

   **Fit rules (these decide whether the clip looks clean or messy):**
   - **Static camera.** Start with `Static locked-off vertical shot, the camera does not move.` All 3 keyframes share one background; "camera glides / pans / zooms / orbits" fights the frames and warps the scene.
   - **Spoken line = 2-3 natural conversational sentences, 28-32 words** (hard limits 24-34; `automate_flow.py` refuses outside them). History: the old ~40-word lines sounded natural but were sometimes cut off; the 14-21-word lines used on 2026-10-19 sounded stretched and unnatural (user feedback 2026-10-20).
   - **Write it the way a Malaysian creator talks to a friend**: natural fillers (`dia`, `je`, `tau`, `memang`, `la`, `korang`), pick 1-2 details per scene and say *why* they matter. Never rattle off a spec list. **No colons or semicolons** in spoken lines (they read as list pauses; the script refuses them). Keep English words to common ones.
     - ✅ `"Saya suka tekstur korduroi dia yang halus ni, rasa vintage sangat. Renda beralun tu ikut sepanjang butang depan, poket dia pun besar, senang nak simpan barang kecil."` (27 words)
     - ❌ `"Tekstur korduroi halus, renda beralun sepanjang butang, dua poket besar: detail vintage yang selesa dipakai harian."` (spec list, colon, 16 words)
   - **She talks through the whole clip, including while she turns.** Don't make her wait ("finishes speaking, then turns", "speaks once she faces the camera"); that squeezes the speech. The script adds a pace line automatically: *"She speaks continuously in a warm, natural, conversational tone at a relaxed but steady pace, like chatting with a close friend, from the first second until the clip ends, without long pauses, and keeps talking naturally while she turns."*
   - Include **"No background music, only her voice and soft ambient sound."** The Suno instrumental is added in editing.
   - Hands stay empty and relaxed at her sides; no gestures, no waving, no props.

   **Exact Template for Each Scene in Flow AI** (full per-scene versions in `prompt_templates.py`):
   ```text
   Static locked-off vertical shot, the camera does not move. {subject + hijab} stands in {keyframe setting}, wearing {exact outfit, bottoms, shoes}. {how she turns from the Start pose to the End pose and when she speaks}. Her hands stay empty and relaxed at her sides the whole time, no gestures, no props. The background, lighting, outfit and hijab stay identical throughout. Soft natural daylight, realistic fabric movement. For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. No background music, only her voice and soft ambient sound. Ensure there are no text overlays or watermarks.

   Spoken Malay (Lip-sync): "{2-3 natural spoken Malaysian Malay sentences, 28-32 words, no colons}"
   ```

   **Example, Scene 1 (Striped Split-Cuff Blouse).** The visual part rendered clean on 2026-10-19. The spoken line is rewritten to the 2026-10-20 natural-speech rule; the original 21-word line with a colon sounded stretched.
   ```text
   Static locked-off vertical shot, the camera does not move. A young Malaysian Muslim woman in a taupe chiffon hijab stands in a sunlit cafe courtyard with rattan chairs and potted palms, wearing a fitted beige blouse with thin latte-tan vertical pinstripes, a pointed collar, small white buttons, a curved hem and split cuffs, with straight navy trousers and cream pointed flats. She starts facing the camera with a warm natural smile and speaks directly to the camera, then slowly pivots in place into a three-quarter angle while keeping eye contact. Her hands stay empty and relaxed at her sides the whole time, no gestures, no props. The background, lighting, outfit and hijab stay identical throughout. Soft natural daylight, realistic fabric movement. For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. No background music, only her voice and soft courtyard ambience. Ensure there are no text overlays or watermarks.

   Spoken Malay (Lip-sync): "Korang pernah perasan tak, kemeja berjalur biasa selalu buat badan nampak lurus je macam pembaris? Blaus jalur latte ni lain sikit, pinggang dia berlekuk, jadi badan terus nampak lebih ramping."
   ```

5. **Automated Playwright Flow Execution (`automate_flow.py`):**
   - **One Flow project per product.** If the product has no project yet (it is not in `flow_projects.json`), create it first. This is usually already done in Step 3 when keyframes came from Flow Image mode:
     ```bash
     python automate_flow.py --create-project "OLOME Cropped Denim Jacket" --prefix olome_cropped_denim_jacket
     ```
     It opens Flow home in a new tab, clicks **New project**, renames the project (title field `input.editable-text-input`) to the given name, reloads to prove the name was saved, and records `prefix -> {name, url}` in `flow_projects.json`. Name it with a short readable product name (about 40 characters max). Running it again for the same prefix creates nothing; it just prints the existing project.
   - Every render goes to the project recorded for that prefix, opened in its own tab. A prefix with no recorded project is refused with the exact create command. `--project-url` overrides this only for deliberate exceptions.
   - Prompts come from this product's record, `generations/<prefix>.json` (never "whichever record is newest"). Save the record (Step 9) BEFORE rendering.
   - **Always dry-run first**, then render:
     ```bash
     # Every check + pre-submit screenshots, submits nothing:
     python automate_flow.py --all --prefix <prefix> --dry-run

     # Render all 3 scenes (Frame 1->2, 2->3, 3->1):
     python automate_flow.py --all --prefix <prefix>

     # Re-render one scene:
     python automate_flow.py --scene 2 --prefix <prefix>
     ```
     `--prefix` defaults to the newest complete keyframe trio, but always pass it explicitly so the right product (and its project) is used.
   - Per scene the script: clears the composer → forces Video / Frames / 9:16 / Omni 1.1 Flash / 720p / 10s / x1 → attaches Start and End by exact filename (uploads if missing) → types visual prompt + `Spoken Malay (Lip-sync)` → **downloads each slot's image and pixel-matches it against the local keyframes** (same file ≈ 0.05, wrong pose ≈ 8-10; limit 3.0) → saves `flow_scene<N>_ready.png` → clicks `Start generation` → confirms the composer reset (job accepted).
   - It refuses to run when a spoken line is missing, under 24 or over 34 words, or contains `:`/`;`. It warns on camera-motion words and on staging that delays her speech, and appends the conversational pace line if the prompt lacks one.
   - **If any check fails, the scene is ABORTED and nothing is submitted** (`ABORTED Scene N ...` plus `flow_scene<N>_aborted.png`). Fix the cause (shorten the line, upload the right file, select the right project). **Never bypass the gate by clicking `Start generation` yourself.**

6. **Post-Render QA (MANDATORY before Gmail/Suno steps):**
   - Renders take about 1 minute. For each new tile, open it and click ⓘ: it must say **Omni 1.1 Flash · 9:16 · 10s · 720p**.
   - Scrub the video at about 0s, 3s, 6s and 9.9s: same model, hijab, garment, bottoms and background as the keyframes; first frame = Start keyframe, last frame = End keyframe; no props, no waving, no warping.
   - A render with a **different woman / no hijab / different top** means the frames were not attached (text-to-video). Regenerate that scene; don't hand it to the user.
   - Agents cannot hear audio: tell the user to listen for Malaysian accent and lip-sync before posting.

7. **Interactive Browser Agents (e.g. Claude in Chrome):** The Claude in Chrome extension runs inside this same Brave profile (same Google sign-ins as `authuser=5`). An agent driving Flow by hand MUST apply the same gate: clear the composer, open the settings menu and check every value, search the full filename, zoom the screenshot on both slot chips to confirm the poses, then submit. Open **the product's own project** (URL from `flow_projects.json`; create it with `--create-project` if missing) in your own tab; don't take over the user's tab or work in another product's project.

---

### Step 7: Automate Gmail Promo Reply in Browser (Brave) — ⚠️ STRICT CLEAN FORMAT

**Goal:** Automatically reply to the user's promo email thread in Gmail with the ready-to-post TikTok caption and hashtags, allowing instant 1-tap copy-pasting on mobile.

1. **Locate Target Email Thread in Brave:**
   - Connect via CDP on port 9222.
   - Locate the Gmail tab (`https://mail.google.com/mail/u/0/#inbox`) or navigate directly to the thread.
   - The thread is typically sent by `Syarief Azman <hello@syariefazman.com>` with subject `(no subject)` containing the product name and TikTok link (`vt.tiktok.com`).

2. **Trigger Reply Composer:**
   - Click the Reply button:
     ```python
     reply_btn = gmail_page.locator("span[role='button']:has-text('Reply'), div[role='button']:has-text('Reply'), [aria-label*='Reply']").last
     await reply_btn.click()
     # Don't rely on the 'r' shortcut: Gmail keyboard shortcuts are OFF on this account (2026-10-20).
     ```
   - **Send automatically, every run.** The user gave a standing instruction on 2026-10-20 ("send it always"): don't ask before sending this caption reply. Still run every clean-format check below before clicking Send, and read the sent message back afterwards.
   - **Do NOT build the reply with the Gmail API (`create_draft` with `replyToMessageId`)**: it appends the quoted original (`gmail_extra` / `gmail_quote`) to the HTML body, and `update_draft` cannot remove it. Write the reply in the Gmail web composer instead.
   - The web reply often opens in **plain-text mode**, where the quote is `>` lines instead of a `blockquote`, so removing DOM quote elements does nothing. Click the body, press `Control+A`, then `Delete`, confirm the body is empty, then type the caption.
   - After sending, read the sent message back (Gmail API `get_thread`) and confirm it has no `gmail_quote`, `>` lines or `wrote:` line.

3. **⛔ CRITICAL ZERO-MISTAKE FORMAT RULE (NEVER VIOLATE):**
   - The email reply body MUST contain **EXCLUSIVELY AND ONLY THE CLEAN TIKTOK CAPTION + 4–6 SEO HASHTAGS**.
   - ❌ **ABSOLUTELY NO GREETINGS:** Do NOT write "Salam Syarief", "Hi", "Hello", etc.
   - ❌ **ABSOLUTELY NO SECTION HEADERS:** Do NOT write "MAKLUMAT PRODUK", "PAUTAN PROJEK", "KAPSYEN TIKTOK", etc.
   - ❌ **ABSOLUTELY NO VIDEO PROMPTS:** Do NOT include Flow AI prompts or English scene descriptions.
   - ❌ **ABSOLUTELY NO SUNO BGM PROMPTS:** Do NOT include music style prompts in the email.
   - ❌ **ABSOLUTELY NO MEDIA LINKS OR METADATA:** Do NOT include image URLs, PDP URLs, or timestamps.
   - ❌ **ABSOLUTELY NO DIVIDERS:** Do NOT use dashed lines or equals signs (`===`, `---`, `___`).
   - ✅ **ONLY THE PURE READY-TO-POST CAPTION:**
     ```text
     {relatable_hook_question} ✨

     {product_pitch_paragraph}

     Kelebihan [product] ni yang buat saya suka:
     ✨ Feature 1: Description
     ✨ Feature 2: Description
     ✨ Feature 3: Description
     ✨ Feature 4: Description
     ✨ Feature 5: Description

     {styling_tips} 💛

     {CTA pointing to beg kuning} 👇💛

     #Hashtag1 #Hashtag2 #Hashtag3 #Hashtag4 #Hashtag5 #Hashtag6
     ```
   - ❌ **ABSOLUTELY NO QUOTED TEXT:** Do NOT leave Gmail's default quoted message (`div.gmail_quote`, `blockquote`, or hidden trimmed content) in the reply body.
   - **WHY THIS RULE EXISTS:** The user receives this email on their mobile smartphone, taps "Select All" ➡️ "Copy", and pastes it straight into the TikTok app's video description box. Any greeting, divider, prompt metadata, or quoted past email forces the user to manually select and delete lines on a mobile touch screen, completely breaking their rapid workflow.

4. **Mandatory Quoted Text Removal Procedure (Before Typing):**
   - After clicking Reply, inspect for the "Show trimmed content" button (`div[aria-label*='Show trimmed content']`, `div.ajR`, `span[data-tooltip*='trimmed']`).
   - If present, click it to expand the quoted message block.
   - Remove any quote elements from the composer DOM:
     ```javascript
     const bodyBox = document.querySelector("div[role='textbox'][aria-label*='Message Body'], div[role='textbox']");
     if (bodyBox) {
       bodyBox.querySelectorAll("div.gmail_quote, div.gmail_extra, blockquote, .gmail_quote").forEach(q => q.remove());
     }
     ```
   - Click the textbox, press `Control+A`, and press `Backspace` to guarantee a 100% clean, blank slate.

5. **Insert Clean Caption and Send:**
   - Locate composer textbox: `div[role='textbox'][aria-label*='Message Body'], div[role='textbox']`.
   - Fill with the pure clean caption + hashtags string.
   - Click the Send button: `div[role='button']:has-text('Send'), [data-tooltip*='Send']`.
   - Wait 3-4 seconds and capture verification screenshot `gmail_reply_sent_clean.png`.

---

### Step 8: Automate Suno AI Instrumental BGM Generation in Browser (Brave)

**Goal:** Configure and trigger the creation of two custom instrumental background music tracks tailored specifically for the product promo on `suno.com/create`.

1. **Navigate to Suno in Brave:**
   - Connect via CDP on port 9222.
   - Open or bring to front `https://suno.com/create`.
   - Wait 4-5 seconds for page elements and user session to settle.
   - Dismiss any cookie banners, promotional dialogs, or popups if visible.

2. **⛔ CRITICAL ZERO-MISTAKE SUNO RULE — PURE INSTRUMENTAL ONLY:**
   - In responsive or mobile-width browser layouts, the composer is housed in a collapsible drawer. If collapsed, click the center orange Create button `a[href='/create'][aria-label='Create']` on the bottom navigation bar to expand it.
   - Toggle or select **Advanced** mode (`button:has-text('Advanced')`).
   - In Suno v6 Advanced mode, the Lyrics box explicitly states: *"Start writing lyrics, or leave this empty for instrumental"*. The **Lyrics editor (`div[contenteditable='true'][role='textbox']`) MUST BE KEPT COMPLETELY EMPTY** to guarantee pure instrumental BGM generation!
   - If a classic `Instrumental` toggle switch is present, verify that it is switched ON (`aria-checked="true"`).
   - **WHY:** TikTok Shop fashion promos rely on clear, spoken Malaysian Malay lip-sync voiceovers from Flow AI. Background music with vocal lyrics or singing clashes with the spoken audio and confuses the viewer.

3. **Input Tailored Style Prompt & Title:**
   - Locate the Styles textarea:
     `textarea[placeholder*='smooth female vocals'], textarea[placeholder*='techno dubstep'], textarea[placeholder*='Style of Music'], textarea[placeholder*='style'], div:has-text('Styles') textarea`
   - Paste the comprehensive style prompt (108–115 BPM, lo-fi indie acoustic cafe pop, bright fingerpicked guitar, Rhodes piano, soft shaker, Malaysian aesthetic lifestyle vibe, pure instrumental).
   - Enter descriptive title in Title input: `<Product Title> - BGM Instrumental` (scroll drawer to bring into view if needed).

4. **Trigger Generation & Verification:**
   - Click the **Create** button: `button:has-text('Create'), button[aria-label='Create']`.
   - Wait 5-6 seconds for the 2 new tracks with spinning loading rings to appear under the **Today** workspace section.
   - Capture verification screenshot `suno_generating.png`.

---

### Step 9: Save the Generation Record & History (in the repo)

**Goal:** Keep everything needed to re-render, resend or audit a product in the repo (pushed to GitHub in Step 10), and prevent hook fatigue across runs. **Supabase is NOT used by Gemini Flow:** the shared Supabase project is reserved solely for other programs (BubatRent/Rent2Go, forex, MQL) and must never be touched. All promotional data and keyframe images are stored 100% inside this repository.

**Save the record BEFORE rendering (Step 6):** `automate_flow.py` reads the prompts from it.

One call writes both the anti-repetition entry in `generation_history.json` and the full record in `generations/<prefix>.json`:
```python
from generate_prompts import save_generation_history
save_generation_history(
    prefix="<prefix>",                     # the keyframe prefix: writes generations/<prefix>.json
    product_name="Product Name Here",
    opening_line="<exact Scene 1 spoken line>",
    closing_line="<exact Scene 3 spoken line>",
    caption="...",
    hashtags="...",
    bgm_prompt="...",
    bgm_title="<Short Product Name> - BGM Instrumental",
    scenes={  # this exact shape is what automate_flow.py reads
        "visual_prompts": {"scene_1": "...", "scene_2": "...", "scene_3": "..."},     # English visual + audio paragraph
        "spoken_dialogue": {"scene_1": "...", "scene_2": "...", "scene_3": "..."},    # verbatim Malay, 28-32 natural words each
        "scene_1_intro": "<visual 1>\n\nSpoken Malay (Lip-sync): \"<dialogue 1>\"",
        "scene_2_detail": "<visual 2>\n\nSpoken Malay (Lip-sync): \"<dialogue 2>\"",
        "scene_3_outro": "<visual 3>\n\nSpoken Malay (Lip-sync): \"<dialogue 3>\""
    },
    metadata={
        "pdp_url": "https://shop.tiktok.com/my/pdp/<id>",   # no query string: the shared URL carries personal tracking IDs
        "tiktok_url": "https://vt.tiktok.com/...",
        "flow_project_url": "<this product's URL from flow_projects.json>",
        "reference_image": "keyframes/<prefix>_product.jpg",
        "keyframe_provider": "e.g. Google Flow Image mode, Nano Banana Pro, 0 credits",
        "colour": "<listing colour used>"
    }
)
```
- The record lists the keyframe trio it finds in `keyframes/` (`keyframes`) and their public GitHub links (`keyframe_urls`, live after `git push`). It prints a WARNING if the trio is incomplete.
- Save the garment reference photo used for the keyframes as `keyframes/<prefix>_product.jpg`, so the product can be regenerated later.
- `reply_gmail.py --prefix <prefix>` and `create_suno.py --prefix <prefix>` read the caption and BGM prompt from the same record. Without a record they stop with an error; they never fall back to a sample caption.
- **Changing dialogue after a record exists (e.g. a re-render):** call `save_generation_history()` again with the same `prefix`; the record file is updated in place (`created_at` is kept). The history file matches entries on `product_name` + `opening_line`, so a new opening line APPENDS a second entry: edit the old `generation_history.json` entry in place instead, so both files hold the lines that were actually rendered.
- **The GitHub repo is public.** Everything in `generations/` and `keyframes/` is visible to anyone. Never put credentials, email addresses or full shared TikTok URLs (they carry user and tracking IDs) into a record.

---

### Step 10: Git Commit & Push

**Goal:** Back up this product's record, keyframes, reference photo and history on GitHub.

```bash
git add generations/<prefix>.json keyframes/<prefix>_* generation_history.json flow_projects.json
git commit -m "feat: <product name> promo in its own Flow project"
git push
```
- Add only this run's files (plus any script or doc you deliberately changed); never sweep unrelated working-tree changes into the commit.
- `keyframes/` is committed on purpose (`.gitignore` re-includes `keyframes/*.jpg` after ignoring images elsewhere). `output/` (raw scrapes) stays ignored.

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
| `automate_flow.py` | Flow AI renderer in Brave via Playwright CDP. Enforces settings, attaches frames by exact filename, pixel-verifies both slots, and refuses to submit on any failed check (`--dry-run` to test) |
| `reply_gmail.py` | Automated Gmail reply script in Brave browser to dispatch copy packages via CDP |
| `create_suno.py` | Automated Suno AI BGM instrumental generator in Brave browser via CDP |
| `open_brave.bat` | Launcher batch script to start Brave with remote debugging on port 9222 |
| `generation_history.json` | Tracks last used opening/closing lines to prevent repetition (window: last 7) |
| `flow_projects.json` | Keyframe prefix → that product's own Google Flow project (`name`, `url`, `created`). Written by `automate_flow.py --create-project`; read by every render. Commit it. |
| `generation_store.py` | Reads and writes `generations/<prefix>.json` and finds each product's keyframe trio in `keyframes/` |
| `generations/` | One full record per product (prompts, spoken lines, caption, hashtags, BGM prompt, keyframes, Flow project, metadata). Written in Step 9, read by `automate_flow.py`, `reply_gmail.py` and `create_suno.py`. Commit it. |
| `keyframes/` | Every product's 3 keyframes and garment reference photo (`<prefix>_product.jpg`). Committed to the public GitHub repo. |
| `supabase_client.py` | Supabase client used only by the unused web app (`webapp.py`). The pipeline no longer uses Supabase. |
| `publish_to_wordpress.py` | WordPress.com publishing integration for promo articles and affiliate links |
| `tiktok_policy_notes.md` | **TikTok policy tracker**: compiled rules, violations, AIGC requirements, and change log |
| `scrape_product.py` | Scrapes TikTok Shop product page → images + metadata |
| `.env` | Contains `GEMINI_API_KEY`, old Supabase keys and WordPress credentials (gitignored, never commit) |
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

- **File:** `generation_history.json` (committed to GitHub)
- **Window:** Last **7** entries only. Older entries can be freely reused.
- **How it works:**
  1. **Zero Banned Hooks**: NEVER ban any hook styles or formulas. All hook techniques (pain-point questions, relatable confessions, visual pattern interrupts, curiosity gap) are valid.
  2. **Search Internet Data for Best Hooks**: Before writing, search current TikTok e-commerce data and viral retail trends for high-converting hook formulas in Malaysia.
  3. **Record to Avoid Repetition**: `get_recently_used_phrases(last_n=7)` retrieves the last 7 recorded openers and closers. The new dialogue simply avoids repeating those 7.
  4. **Auto-Logging**: After generation, `save_generation_history()` logs the newly created hook and CTA to `generation_history.json` and, with `prefix=`, the full record to `generations/<prefix>.json`.
- **No fixed rotation scripts.** No banned hooks. Data-driven viral hooks with recent history awareness.

---

## Flow AI Video Prompt Structure

Each scene prompt is **one English paragraph + one verbatim Malay line** (full rules and a verified example in Step 6 §4b; templates in `prompt_templates.py`):
- **Visual:** `Static locked-off vertical shot, the camera does not move.` + model, hijab, exact outfit and setting from the keyframes + how she turns in place from the Start pose to the End pose + empty relaxed hands.
- **Audio:** "For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. No background music, only her voice and soft ambient sound. Ensure there are no text overlays or watermarks. She speaks continuously in a warm, natural, conversational tone at a relaxed but steady pace, like chatting with a close friend, from the first second until the clip ends, without long pauses, and keeps talking naturally while she turns."
- **Dialogue:** `Spoken Malay (Lip-sync): "<verbatim Malaysian Malay, 2-3 natural spoken sentences, 28-32 words, no colons>"`. Write the Malay yourself; never ask Flow to translate English.

**CRITICAL PACKAGING RULE — WRAP IN SAME CODE BOX FOR 1-CLICK COPY:**
ALWAYS wrap the Flow AI prompt AND the spoken Malay lip-sync dialogue in the **SAME text / code box**.
Do NOT separate the spoken Malay into an external quote below the box. This allows the user to click the copy button (`📋`) on the code box once to copy everything needed for that scene cleanly.

Example layout:
```text
Static locked-off vertical shot, the camera does not move. A young Malaysian Muslim woman in a ... hijab stands in ..., wearing .... She starts ..., then slowly turns in place .... Her hands stay empty and relaxed at her sides the whole time, no gestures, no props. ... For the audio, generate a highly realistic female voice with a standard Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. No background music, only her voice and soft ambient sound. Ensure there are no text overlays or watermarks.

Spoken Malay (Lip-sync): "Dua atau tiga ayat santai macam bercakap dengan kawan, lebih kurang 28 hingga 32 patah perkataan, tanpa tanda titik bertindih."
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
   - Tab: the product's own project from `flow_projects.json` (created with `--create-project` for each new product).
   - Forces Video / Frames / 9:16 / Omni 1.1 Flash / 720p / 10s / x1.
   - Attaches and pixel-verifies Frame 1 ➡️ 2 (Scene 1), Frame 2 ➡️ 3 (Scene 2), Frame 3 ➡️ 1 (Scene 3).
   - Types visual prompt + `Spoken Malay (Lip-sync)` line and starts renders only after every check passes. Then do Post-Render QA (Step 6 §6).
2. **Gmail Promo Package Reply (`reply_gmail.py`)**:
   - Tab: `https://mail.google.com/mail/u/0/#inbox`
   - Checks and verifies the email thread containing the **exact TikTok product link** first. If not found, aborts immediately (never replies to wrong threads, never composes new emails).
   - Once verified, clicks **Reply**, fills **STRICTLY AND ONLY THE CLEAN TIKTOK CAPTION + HASHTAGS** (zero greetings, zero metadata headers, zero prompts, zero quoted text), and clicks **Send**.
3. **Suno AI Instrumental BGM (`create_suno.py`)**:
   - Tab: `https://suno.com/create`
   - Sets mode to **Instrumental** (strictly no vocals).
   - Pastes the generated acoustic/lo-fi style prompt and title, then clicks **Create**.

---

## 🛠️ Troubleshooting & Zero-Mistake Recovery Playbook

### 1. Brave CDP Connection Refused / 404 Not Found on `/json/version`
* **Symptoms:** `BrowserType.connect_over_cdp: Unexpected status 404` or `connect ECONNREFUSED 127.0.0.1:9222`.
* **Root Cause:** Brave was launched normally (e.g. from taskbar or desktop) without debugging flags, or an unflagged background process is holding the user profile lock.
* **Guaranteed Solution:** Force-stop all running Brave processes and relaunch with both `--remote-debugging-port=9222` AND `--remote-allow-origins=*`:
  ```powershell
  Stop-Process -Name brave -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
  Start-Process "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe" -ArgumentList "--remote-debugging-port=9222", "--remote-allow-origins=*", "<target_url>"
  Start-Sleep -Seconds 4
  ```

### 1b. Brave Keeps Asking to "Allow Remote Debugging" / 403 Forbidden
* **Symptoms:** `/json/version` returns 404, connections time out, or `ws://.../devtools/browser/<id>` returns `403 Forbidden`; the user has to click an approval prompt in Brave for each script run.
* **Root Cause:** Brave was started normally and remote debugging was switched on from inside the browser. That mode asks the user to approve each new script connection. (The Claude in Chrome extension is a separate channel and never needs this.)
* **Guaranteed Solution:** Start Brave with `--remote-debugging-port=9222 --remote-allow-origins=*` (restart command above). The user's taskbar Brave shortcut has carried these flags since 2026-10-20; the shared desktop and Start-menu shortcuts need admin rights to change. If Brave was already running without the flag (e.g. opened by a link), the flag is ignored until every Brave window is closed. `automate_flow.connect_to_brave()` falls back to the `DevToolsActivePort` websocket when the flag is missing, but then every connection needs the user's approval.

### 2. Accidental Browser Window Closure
* **Symptoms:** The user complains that Brave disappeared or closed after automation ran.
* **Root Cause:** Calling `await browser.close()` in Playwright CDP scripts.
* **Guaranteed Solution:** NEVER call `browser.close()` on CDP sessions. Simply let the Python script end or call `await p.stop()`. This cleanly detaches the automation listener while keeping the user's interactive browser window alive and visible on their desktop.

### 3. Gmail Reply Thread Matching & Formatting Violations
* **Symptoms:** The user rejects the email reply because it is a new email thread, was sent to an unrelated thread (broker statement, newsletter), or contains greetings, headers, prompt boxes, or dividers.
* **Root Cause:** Blindly clicking the top thread in inbox when the search fails, calling compose to send a new email, or confusing chat layout with email content.
* **Guaranteed Solution:**
  1. **Check exact product link first:** Search Gmail for the exact TikTok product link or shortcode (`ZS...`).
  2. **Verify thread content:** Once opened, inspect the email body. It MUST contain the exact product link.
  3. **Strict Abort Gate:** If no email contains that exact link, **ABORT IMMEDIATELY**. Never reply to an unrelated email and never compose a new email thread.
  4. The email reply MUST contain **ONLY THE RAW TIKTOK CAPTION + HASHTAGS** inside the user's original thread.
     - No "Salam Syarief"
     - No "MAKLUMAT PRODUK"
     - No "FLOW AI PROMPT"
     - No "SUNO BGM"
     - No "===" or "---"
     - Pure, direct copy box content only.

### 4. Suno AI Generating Songs with Vocals
* **Symptoms:** Suno generates songs with singing, which clashes with the Flow AI voiceover.
* **Root Cause:** Instrumental mode was not toggled ON before clicking Create.
* **Guaranteed Solution:** Always inspect and verify the `aria-checked` attribute on the Instrumental switch (`button[role='switch']:has-text('Instrumental')`). If `aria-checked != "true"`, click it before entering the prompt or clicking Create.

### 5. Record Missing or Wrong Product in `generations/`
* **Symptoms:** `automate_flow.py` says `No generation record at generations/<prefix>.json`, or `reply_gmail.py` / `create_suno.py` stop with `No caption found` / `No BGM prompt found`.
* **Root Cause:** Step 9 was skipped, or it was run with a different `prefix` than the keyframe files use.
* **Guaranteed Solution:** Run Step 9 with the exact keyframe prefix (the part before `_frame1_front.jpg`), then retry. Pass `--prefix <prefix>` to `reply_gmail.py` and `create_suno.py` rather than `--latest`, so a re-saved older record can't be picked by mistake. (Supabase is no longer used, so its old `ConnectionTerminated` / 401 errors don't apply.)

### 6. Flow Render Shows a Different Woman / No Hijab / Wrong Garment
* **Symptoms:** The video looks nothing like the keyframes. Its ⓘ panel still says Omni 1.1 Flash · 9:16 · 10s.
* **Root Cause:** The `Start`/`End` slots were empty at submit, so Flow rendered text-to-video. (Old `automate_flow.py` clicked the first element containing the filename, often a grid tile instead of a picker row, and submitted without checking the slots.)
* **Guaranteed Solution:** Re-render with the current `automate_flow.py` (dry-run first). It refuses to submit unless both slots pixel-match the expected keyframes. If doing it by hand, follow Step 6 §4a and zoom on both chips before submitting.

### 7. Flow Clip Is Rushed, Cut Off, Warped or Has Music
* **Symptoms:** Speech is too fast or stops mid-sentence, lips don't match, the background bends, or music plays under the voice.
* **Root Cause:** Spoken line too long for 10s, camera-motion instructions fighting a shared static background, or no "No background music" instruction.
* **Guaranteed Solution:** 2-3 natural conversational sentences of 28-32 words (not a spec list, no colons), she talks through the whole clip including the turn, `Static locked-off vertical shot, the camera does not move.`, the model turns in place, and `No background music, only her voice and soft ambient sound.` See Step 6 §4b.
* **Voice sounds stretched, slow, robotic or "weird":** the line is too short or written like a spec list (this happened with the 14-21-word lines of 2026-10-19). Rewrite it as natural speech of 28-32 words.

### 8. `automate_flow.py` Prints `ABORTED Scene N`
* **Meaning:** A pre-submit check failed and nothing was rendered (no credits spent). Read the reason line and `flow_scene<N>_aborted.png`.
* **Common causes:** spoken line outside 24-34 words or containing `:`/`;` (rewrite it and re-save the record with the same `prefix`, Step 9), no `generations/<prefix>.json` record (run Step 9 first), or a slot holding the wrong image (check the project for duplicate or mislabeled uploads).
* **`No Flow project recorded for '<prefix>'`:** the product has no project yet. Run the printed `--create-project` command, then render again.
* **`Flow project creation error`:** the home page had no **New project** button (signed out or UI changed), or the rename didn't save. Create or rename the project by hand in Flow, then add `"<prefix>": {"name": ..., "url": "https://flow.google.com/u/5/project/<id>", "created": ...}` to `flow_projects.json`.
* **Never** bypass the gate by clicking `Start generation` manually without performing the same checks.


