# 🎬 TikTok Product Promo Generator (Gemini Pro + Flow AI Pipeline)

> **From a single TikTok Shop product link $\rightarrow$ AI scraped images, 3 keyframe prompts, Gemini Pro content generation, Flow AI video prompts (Veo 3.1 / Omni Flash), policy-compliant TikTok SEO caption, and Suno AI background music.**

This repository provides an automated, end-to-end content production pipeline designed specifically for **TikTok Shop affiliate marketing and e-commerce in Malaysia**.

---

## 📌 Table of Contents
1. [Pipeline Architecture](#-pipeline-architecture)
2. [What This Workflow Produces](#-what-this-workflow-produces)
3. [Prerequisites & Installation](#-prerequisites--installation)
4. [Step-by-Step Execution Guide](#-step-by-step-execution-guide)
   - [Step 1: Scrape Product Listing](#step-1-scrape-product-listing)
   - [Step 2: Generate Prompts & Copy via Gemini Pro](#step-2-generate-prompts--copy-via-gemini-pro)
   - [Step 3: Generate 9:16 Keyframe Images](#step-3-generate-916-keyframe-images)
   - [Step 4: Generate Videos on Google Flow](#step-4-generate-videos-on-google-flow)
   - [Step 5: Generate Background Music on Suno AI](#step-5-generate-background-music-on-suno-ai)
5. [Prompting Rules & Strategy](#-prompting-rules--strategy)
   - [Flow AI Multi-Modal Prompt Format](#flow-ai-multi-modal-prompt-format)
   - [TikTok SEO Hashtag Strategy (No Spam Tags)](#tiktok-seo-hashtag-strategy-no-spam-tags)
6. [Repository Structure](#-repository-structure)
7. [Customization Guide](#-customization-guide)

---

## 🔄 Pipeline Architecture

```
 ┌─────────────────────────────────────────────────────────────┐
 │ 1. INPUT: TikTok Shop URL                                   │
 │    e.g. https://vt.tiktok.com/ZS9B.../                      │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 2. SCRAPE & EXTRACT (`scrape_product.py`)                   │
 │    • Resolves short URL $\rightarrow$ Full PDP listing page │
 │    • Extracts product title, features, colors, & body text  │
 │    • Downloads & converts listing images to high-res .jpg   │
 │    • Saves metadata to `output/<timestamp>/product_info.json│
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 3. PROMPT GENERATION (`generate_prompts.py` - Gemini Pro)   │
 │    • Analyzes product attributes & solves buyer pain points │
 │    • Generates 3 Keyframe Image Prompts (9:16 vertical)     │
 │    • Generates 3 Flow AI Video Prompts (8s with Malay audio)│
 │    • Generates High-Converting TikTok Caption (SEO tags)    │
 │    • Generates Suno AI Style Prompt & Malay Lyrics          │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 4. IMAGE GENERATION (Gemini Pro / Imagen 3)                 │
 │    • Frame 1: Front-facing hook & intro                     │
 │    • Frame 2: Side profile showing fabric drape & cut       │
 │    • Frame 3: Over-the-shoulder CTA look                    │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │ 5. MANUAL VIDEO GENERATION (Google Flow - Veo 3.1)          │
 │    • Upload Frame 1, 2, 3 + paste generated scene prompts   │
 │    • 8-second frame-to-video with Malaysian Malay lip-sync  │
 │    • Download the 3 final MP4 clips & post to TikTok!       │
 └─────────────────────────────────────────────────────────────┘
```

---

## 📋 What This Workflow Produces

For every single product link provided, the system generates:

| # | Asset | Description |
|---|---|---|
| 1 | **Downloaded Product Photos** | High-resolution listing images converted to `.jpg` in an `output/<timestamp>/` directory. |
| 2 | **3 Keyframe Images (9:16)** | Consistent Malaysian hijab model showcasing the exact product in Front, Side, and Over-the-Shoulder poses. |
| 3 | **3 Flow AI Video Prompts** | Tailored 8-second scene prompts for Veo 3.1 / Omni Flash with explicit instructions for Malaysian Malay spoken lip-sync. |
| 4 | **TikTok Caption & Hashtags** | High-converting Bahasa Melayu copy with relatable hooks, problem-solution angles, styling tips, "beg kuning" CTA, and zero price mentions (TikTok policy safe). |
| 5 | **Suno AI Prompt & Lyrics** | Upbeat music genre tags + singable Bahasa Melayu lyrics matching the product vibe. |

---

## 🛠️ Prerequisites & Installation

### 1. System Requirements
- **Python 3.10+**
- **Microsoft Edge** or **Google Chrome** installed (used by Playwright)

### 2. Install Python Dependencies
```bash
pip install playwright pillow beautifulsoup4 google-genai python-dotenv
python -m playwright install
```

### 3. Setup Gemini API Key
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY="your_google_gemini_api_key_here"
```

---

## 📖 Step-by-Step Execution Guide

### Step 1: Scrape Product Listing

Run `scrape_product.py` with your TikTok Shop link:

```bash
python scrape_product.py "https://vt.tiktok.com/ZS9Bmw6opErnP-latdI/"
```

**What it does:**
1. Automatically launches a headless browser and follows redirects to the TikTok Shop product page.
2. Extracts product title, full specifications, fabric type, colors, and reviews.
3. Downloads all product images, converts them from WebP to high-quality JPG, and saves everything into a timestamped folder:
   ```
   output/20260830_000436/
   ├── product_info.json
   ├── product_1.jpg
   ├── product_2.jpg
   └── ...
   ```

---

### Step 2: Generate Prompts & Copy via Gemini Pro

Run `generate_prompts.py` pointing to the scraped `product_info.json`:

```bash
python generate_prompts.py output/20260830_000436/product_info.json
```

**What it does:**
- Sends the extracted product data to **Gemini Pro** (`gemini-1.5-pro` via `google-genai`).
- Returns a structured JSON payload containing:
  - `keyframe_prompts`: 3 image generation prompts (Front, Side, Over-the-Shoulder).
  - `flow_ai_prompts`: 3 video prompts tailored for 8-second Veo 3.1 generation.
  - `tiktok_caption`: SEO-optimized post copy with 4–6 high-intent hashtags (no generic spam tags).
  - `suno_bgm`: Style prompt and catchy Malay lyrics.

---

### Step 3: Generate 9:16 Keyframe Images

Use the 3 prompts generated in Step 2 with Gemini Pro image generation / Antigravity:

1. **Frame 1 (Front View - Intro Hook):**
   - Establishes the full outfit, setting (e.g. modern cafe / urban KL), and subject looking directly at the camera.
2. **Frame 2 (Side 3/4 Profile - Product Focus):**
   - References Frame 1 to maintain character consistency while highlighting specific fabric drape, cuts, collars, pockets, or waistlines.
3. **Frame 3 (Over-the-Shoulder - Outro & CTA):**
   - References Frames 1 & 2 to showcase back silhouette and a warm, inviting smile pointing towards the call-to-action.

---

### Step 4: Generate Videos on Google Flow

1. Open **[flow.google](https://flow.google)** in your browser.
2. Create or select a project.
3. For each of the 3 scenes:
   - **Upload the Image**: Attach `frame_1_front.jpg` for Scene 1, `frame_2_side.jpg` for Scene 2, and `frame_3_shoulder.jpg` for Scene 3.
   - **Model Selection**: Select **Veo 3.1** (or Gemini Omni Flash).
   - **Duration**: Set to **8 seconds**.
   - **Paste the Scene Prompt**: Paste the corresponding prompt from `generate_prompts.py`.
4. Click **Generate** and download the 3 `.mp4` video clips.

---

### Step 5: Generate Background Music on Suno AI

1. Open **[suno.com](https://suno.com)**.
2. Switch to **Custom Mode**.
3. Paste the generated **Style Prompt** (e.g. *Acoustic pop, warm guitar, cheerful TikTok tempo*).
4. Paste the generated **Malay Lyrics** into the lyrics box (or leave blank for instrumental).
5. Click **Create** and download your custom audio track.

---

## 🎯 Prompting Rules & Strategy

### Flow AI Multi-Modal Prompt Format
Every Flow AI prompt is written as a single self-contained prompt adhering to these rules:
- **Duration**: Explicitly specifies 8 seconds (matching Veo 3.1 duration limits).
- **Camera Dynamics**: Scene 1 uses slow zoom-in; Scene 2 uses slow pan; Scene 3 uses subtle slow-motion.
- **Audio & Language Instruction**: Explicitly commands standard **Malaysian Malay (Bahasa Melayu Malaysia)** spoken audio with accurate lip-syncing, strictly forbidding Indonesian accents.
- **Visual Cleanliness**: Commands no text overlays and no watermarks.

### TikTok SEO Hashtag Strategy (No Spam Tags)
Generic spam tags like `#RacunTikTok`, `#fyp`, and `#viral` are **strictly excluded**. Modern TikTok algorithms reward search intent. Captions use a **3-tier SEO hashtag framework (4–6 tags total)**:

```
[Product Keyword]      + [Occasion / Pain Point]  + [Niche Community]
#BlazerWanita           #OutfitKePejabat           #HijabFashionMY
#TudungInstant          #TudungMalas               #MuslimahStyleMY
#SmartScaleMalaysia     #TipKurusSihat             #DietMalaysia
```

---

## 📂 Repository Structure

```
gemini-flow/
├── README.md              # Comprehensive documentation and pipeline manual
├── scrape_product.py      # Automated TikTok Shop product scraper & image downloader
├── generate_prompts.py    # Gemini Pro prompt & content generation engine
├── prompt_templates.py    # Parameterized prompt templates and SEO rules
├── .gitignore             # Automatically ignores all image binaries (*.jpg, *.webp, *.png) & output/
└── output/                # (Local only) Timestamped folders with scraped assets & metadata
    └── 20260830_XXXXXX/
        ├── product_info.json
        ├── product_1.jpg
        └── ...
```

---

## ⚙️ Customization Guide

All generation behavior can be customized in `prompt_templates.py` or via `generate_prompts.py`:

| Parameter | Default Setting | Alternative Options |
|---|---|---|
| **Model Character** | Malaysian 24-25 y/o woman wearing modern hijab | Any demographic, age, or modest fashion style |
| **Scene Count** | 3 scenes $\times$ 8 seconds (24s total ad) | 2 to 5 scenes |
| **Aspect Ratio** | 9:16 (TikTok Vertical) | 16:9 (YouTube), 1:1 (Instagram) |
| **Spoken Accent** | Standard Malaysian Malay (KL / Urban) | English (MY), Mandarin, etc. |
| **Location Setting** | Modern KL cafe / Urban high-rise / Studio | Outdoor garden, office, home gym |

---

## 📜 License

Personal & commercial affiliate promotion use.
