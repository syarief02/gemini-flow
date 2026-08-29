# 🎬 TikTok Product Promo Generator — Gemini Pro + Flow AI Pipeline

> **One TikTok Shop link → 3 AI-generated keyframes, Flow AI video prompts, TikTok caption, and Suno BGM — all automated.**

This workflow automates the creation of TikTok product promotion content for the Malaysian market. It takes a single TikTok Shop product link and generates everything you need to produce a professional-looking TikTok video ad featuring a Malaysian hijab model.

---

## 📋 What This Workflow Produces

From a **single TikTok Shop product URL**, you get:

| # | Output | Description |
|---|--------|-------------|
| 1 | **3 Keyframe Images (9:16)** | Front pose, side profile, over-the-shoulder — consistent character, outfit, and background |
| 2 | **3 Flow AI Video Prompts** | Ready-to-paste prompts for Veo 3.1 / Omni Flash 8-second frame-to-video generation with Malaysian Malay lip-sync |
| 3 | **TikTok Caption & Hashtags** | Engaging Bahasa Melayu Malaysia copy with relatable hooks, styling tips, CTA — no price mentioned (TikTok policy compliant) |
| 4 | **Suno BGM Prompt & Lyrics** | Style tags + Malay lyrics for generating TikTok-ready background music |

---

## 🔄 Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  INPUT: TikTok Shop Product Link                                │
│  e.g. https://vt.tiktok.com/ZS9BPhWgnmMJh-HKAvy/              │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Product Scraping (Playwright + BeautifulSoup)          │
│  • Resolves short URL → TikTok Shop PDP page                   │
│  • Extracts product title, description, features, colors       │
│  • Downloads all high-res product images (webp → jpg)          │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Keyframe Generation (Gemini Pro Image Generation)      │
│  • Frame 1: Front-facing full outfit portrait                   │
│  • Frame 2: Side profile (3/4 view) showing fabric drape       │
│  • Frame 3: Over-the-shoulder look showing back silhouette     │
│  • All 9:16 aspect ratio, consistent character & background    │
│  • Malaysian hijab woman, outdoor urban KL setting             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Content Generation (Gemini Pro Text Generation)        │
│  • 3x Flow AI prompts (Veo 3.1 / Omni Flash, 8s each)         │
│  • Malaysian Malay lip-sync audio instructions                  │
│  • TikTok caption with hooks, tips, CTA & hashtags             │
│  • Suno BGM style prompt + Malay lyrics                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  OUTPUT: Ready-to-use assets in workspace folder                │
│  • frame_1_front.jpg                                            │
│  • frame_2_side.jpg                                             │
│  • frame_3_over_shoulder.jpg                                    │
│  • Flow AI prompts (Scene 1, 2, 3)                             │
│  • TikTok caption + hashtags                                    │
│  • Suno BGM prompt + lyrics                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Requirements

### Software
- **Python 3.10+**
- **Playwright** (Python) with Edge/Chromium browser
- **Pillow** (PIL) for image conversion
- **BeautifulSoup4** for HTML parsing

### Install Dependencies
```bash
pip install playwright pillow beautifulsoup4
python -m playwright install
```

### AI Services Used
| Service | Purpose | Access |
|---------|---------|--------|
| **Gemini Pro** | Product analysis, image generation, prompt writing | Always use Gemini Pro model |
| **Google Flow** | Frame-to-video generation (Veo 3.1 / Omni Flash 8s) | [flow.google](https://flow.google) |
| **Suno AI** | Background music generation | [suno.com](https://suno.com) |

---

## 📖 Detailed Workflow

### Step 1: Product Scraping

The script uses **Playwright** (headless Edge) to:
1. Navigate to the TikTok short URL (e.g. `https://vt.tiktok.com/...`)
2. Follow redirects to the full TikTok Shop PDP page
3. Extract the product title, description, features, colors
4. Download all product listing images (converted from webp to jpg)

**Key product details extracted:**
- Product name and type (e.g., "Kot trench panjang sederhana wanita")
- Available colors (e.g., Khaki, Light Green, Pink)
- Style features (e.g., POLO collar, cinched waist, Korean style)
- Material and cut details

### Step 2: Keyframe Generation

Using **Gemini Pro image generation**, 3 consistent keyframes are created:

| Frame | Pose | Purpose |
|-------|------|---------|
| **Frame 1** | Front-facing, looking at camera | **Intro** — establish the product and grab attention |
| **Frame 2** | Side profile / 3/4 view, facing left | **Product focus** — showcase fabric drape, slim-fit cut, material quality |
| **Frame 3** | Turned around, looking over shoulder | **Outro & CTA** — show back silhouette, warm smile for call-to-action |

**Consistency rules applied across all frames:**
- Same adult Malaysian woman wearing hijab
- Same product outfit (exact coat from the listing)
- Same outdoor urban street background (KL setting)
- 9:16 vertical aspect ratio (TikTok-native)
- No text overlays or watermarks
- Cinematic golden hour lighting

### Step 3: Flow AI Prompts

Each prompt is a **single combined prompt** (no separate audio prompt) designed for **Veo 3.1 / Omni Flash 8-second** frame-to-video generation on [flow.google](https://flow.google).

**Prompt structure for each scene:**
```
Generate an 8-second video from the provided frame of [character description].
[Camera movement instruction].
Ensure there are no text overlays or watermarks in the video.
[Lip-sync instruction].
For the audio, generate a highly realistic female voice with a standard
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent.
Explicitly translate the following English text into standard Malaysian Malay
for the spoken audio: "[dialogue in English for translation]"
```

**Key rules for the Flow AI prompts:**
- Each scene is **8 seconds** (can't talk too long)
- Audio must be **Malaysian Malay** (Bahasa Melayu Malaysia), NOT Indonesian
- Lip-sync must be accurate
- No text overlay on the video
- Camera movement varies per scene (zoom in, slow pan, slow motion)

### Step 4: TikTok Caption

The caption is written in **Bahasa Melayu Malaysia** targeting Malaysian audiences:
- Relatable hooks (e.g., "Pernah tak korang masuk office rasa macam peti ais? 🥶")
- Styling tips for hijab-wearing women
- Entertainment/info value (not just a hard sell)
- Call-to-action ("Tekan beg kuning kat bawah!")
- **No price mentioned** (violates TikTok policy)
- Malaysian-focused hashtags (#RacunTikTok #OOTDHijab #FypMalaysia etc.)

### Step 5: Suno BGM

**Style prompt** for instrumental or vocal background music:
```
Upbeat, trendy, lo-fi hip hop, chill pop, modern, rhythmic, catchy, bright,
sophisticated, subtle electronic elements, confident, relaxing but with a good
tempo for TikTok, fashionable.
```

**Lyrics** are written in Bahasa Melayu Malaysia with a catchy, singable structure (verse/chorus/outro).

---

## 📂 Output File Structure

After running the pipeline on a product link, your workspace will contain:

```
gemini flow/
├── product_image_1.jpg          # Downloaded product listing images
├── product_image_2.jpg
├── product_image_3.jpg
├── ...
├── frame_1_front.jpg            # Generated keyframe: front pose (9:16)
├── frame_2_side.jpg             # Generated keyframe: side profile (9:16)
├── frame_3_over_shoulder.jpg    # Generated keyframe: over shoulder (9:16)
└── (prompts & captions are provided in the chat output)
```

---

## 🚀 How to Use

### Quick Start
1. Provide a **TikTok Shop product link** (e.g., `https://vt.tiktok.com/...`)
2. The pipeline automatically:
   - Scrapes the product page and downloads images
   - Generates 3 consistent keyframe photos (9:16)
   - Writes Flow AI video prompts for each scene
   - Writes TikTok caption with hashtags
   - Writes Suno BGM prompt with lyrics
3. Take the 3 keyframe images to [flow.google](https://flow.google)
4. Use "Frame to Video" generation with each frame + its corresponding prompt
5. Select **Veo 3.1** or **Omni Flash**, set duration to **8 seconds**
6. Download the 3 generated video scenes
7. Post on TikTok with the generated caption!

### Manual Flow AI Steps
For each scene (1, 2, 3):
1. Open [flow.google](https://flow.google)
2. Create a new project or use existing
3. Upload the corresponding keyframe image
4. Paste the Flow AI prompt for that scene
5. Select model: **Veo 3.1** (or Gemini Omni Flash)
6. Set duration: **8 seconds**
7. Generate and download the MP4

---

## 📝 Example: Trench Coat Product

### Input
```
https://vt.tiktok.com/ZS9BPhWgnmMJh-HKAvy/
```

### Generated Flow AI Prompts

**Scene 1: Intro (Frame 1 — Front Pose)**
> Generate an 8-second video from the provided frame of an adult Malaysian woman
> wearing a hijab and a beige trench coat outdoors. The camera slowly zooms in to
> highlight the coat's details. Ensure there are no text overlays or watermarks in
> the video. The subject must look directly at the camera with accurate lip-syncing.
> For the audio, generate a highly realistic female voice with a standard Malaysian
> Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Explicitly
> translate the following English text into standard Malaysian Malay for the spoken
> audio: "Ever felt freezing in the office? You need this trench coat!"

**Scene 2: Product Focus (Frame 2 — Side Profile)**
> Generate an 8-second video from the provided frame of the woman in the beige trench
> coat posing to her left. The camera performs a subtle slow pan to emphasize the silky,
> draping fabric and the slim-fit cut of the coat. Ensure there are no text overlays or
> watermarks in the video. The subject subtly turns her head to speak with accurate
> lip-syncing. For the audio, generate a highly realistic female voice with a standard
> Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent.
> Explicitly translate the following English text into standard Malaysian Malay for the
> spoken audio: "The material is soft, flowy, and the slim-fit cutting makes you look
> perfectly styled."

**Scene 3: Outro & CTA (Frame 3 — Over Shoulder)**
> Generate an 8-second video from the provided frame of the woman in the beige trench
> coat turning to look over her shoulder, showcasing the back details of the coat. Add
> a subtle cinematic slow-motion effect as she smiles. Ensure there are no text overlays
> or watermarks in the video. The subject must speak with accurate lip-syncing. For the
> audio, generate a highly realistic female voice with a standard Malaysian Malay
> (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. Explicitly translate
> the following English text into standard Malaysian Malay for the spoken audio: "Perfect
> for the office or your weekend OOTD. Grab yours now from the yellow bag below!"

### Generated TikTok Caption
```
Pernah tak korang masuk office terus rasa macam masuk peti ais? 🥶
Kot panjang gaya Korea ni memang penyelamat!
Potongan slim-fit dia bagi ilusi badan lebih tinggi dan ramping.

Tips Gayakan Long Coat untuk Hijabi:
✨ Biar terbuka (unbuttoned) untuk efek flowy!
✨ Padankan dengan ankle boots atau sneakers.
✨ Sesuai untuk office, presentation, atau cafe hunting. ☕

Tekan beg kuning kat bawah cepat sebelum sold out! 👇💛

#RacunTikTok #OOTDHijab #TrenchCoatMalaysia #FashionMalaysia
#GayaTiktok #OutfitKePejabat #TiktokFashion #OOTDMalaysia
#OOTDGenting #GayaHijabi #FypMalaysia
```

### Generated Suno BGM Prompt
**Style:** `Upbeat, trendy, lo-fi hip hop, chill pop, modern, rhythmic, catchy, bright, sophisticated, subtle electronic elements, confident, TikTok-ready.`

**Lyrics (Bahasa Melayu):**
```
[Verse]
Masuk office sejuk gigil / OOTD takkan fail
Gaya stylo nampak chill / Trench coat ini memang real

[Chorus]
Labuh cantik, kain flowy / Jalan yakin macam K-drama
Slim fit cutting nampak tinggi / Gaya hijab paling gempak!

[Outro]
Beg kuning ada di bawah / Grab sekarang jangan lambat!
```

---

## ⚙️ Configuration & Customization

### Target Audience
Currently configured for **Malaysian TikTok audiences**:
- Language: Bahasa Melayu Malaysia (NOT Indonesian)
- Model: Malaysian hijab-wearing woman
- Hashtags: Malaysian market focused
- Hooks: Malaysian cultural references (office aircond, Genting, K-Drama)

### Adjustable Parameters
| Parameter | Current Default | Can Change To |
|-----------|----------------|---------------|
| Model character | Malaysian hijab woman | Any ethnicity/style |
| Scene count | 3 scenes (8s each) | 2-5 scenes |
| Aspect ratio | 9:16 (TikTok) | 16:9 (YouTube), 1:1 (Instagram) |
| Language | Bahasa Melayu Malaysia | Any language |
| Video duration | 8 seconds per scene | 4s, 6s, 8s |
| Background | Outdoor urban KL | Indoor, studio, cafe, etc. |

---

## 🔗 Original Workflow Reference

This pipeline was reverse-engineered from a manual Gemini Pro + Google Flow workflow:
- [Original Gemini conversation](https://share.gemini.google/acPGgNqdqowG)
- Model used: **Gemini Pro** (always)
- Video generation: **Google Flow** with **Veo 3.1 / Omni Flash** frame-to-video, 8-second duration

---

## 📜 License

Personal use. This workflow is designed for TikTok affiliate product promotion.
