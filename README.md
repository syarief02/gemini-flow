# 🎬 TikTok Product Promo Generator

> **One TikTok Shop link → 3 AI keyframes + Flow AI prompts + TikTok caption + Suno BGM — ready for manual Flow video generation.**

Automates creation of TikTok product promotion content for the **Malaysian hijab fashion market**. You provide a product link, the pipeline generates everything you need — then you manually paste into [Google Flow](https://flow.google) to create the final videos.

---

## 📋 What You Get

| # | Output | Description |
|---|--------|-------------|
| 1 | **3 Keyframe Images (9:16)** | Front pose, side profile, over-the-shoulder — consistent character, outfit, and background |
| 2 | **3 Flow AI Video Prompts** | Ready-to-paste prompts for Veo 3.1 / Omni Flash 8s with Malaysian Malay lip-sync |
| 3 | **TikTok Caption & Hashtags** | Bahasa Melayu Malaysia copy — hooks, styling tips, CTA — no price (TikTok policy compliant) |
| 4 | **Suno BGM Prompt & Lyrics** | Style tags + Malay lyrics for background music generation |

---

## 🔄 Pipeline

```
 TikTok Shop Link
       │
       ▼
 ┌─────────────────────────────────────────┐
 │  1. SCRAPE PRODUCT                      │
 │     • Resolve short URL → PDP page      │
 │     • Extract title, colors, features   │
 │     • Download product images (.jpg)    │
 │     python scrape_product.py <url>      │
 └──────────────┬──────────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────────┐
 │  2. GENERATE 3 KEYFRAMES               │  ← Gemini Pro
 │     • Frame 1: Front (intro)            │
 │     • Frame 2: Side profile (details)   │
 │     • Frame 3: Over shoulder (CTA)      │
 │     9:16, consistent character & scene  │
 └──────────────┬──────────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────────┐
 │  3. GENERATE ALL TEXT CONTENT           │  ← Gemini Pro
 │     • 3x Flow AI video prompts          │
 │     • TikTok caption + hashtags         │
 │     • Suno BGM style + lyrics           │
 └──────────────┬──────────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────────┐
 │  OUTPUT FOLDER                          │
 │  output/<timestamp>/                    │
 │  ├── product_1.jpg ... product_N.jpg    │
 │  ├── product_info.json                  │
 │  ├── frame_1_front.jpg                  │
 │  ├── frame_2_side.jpg                   │
 │  ├── frame_3_shoulder.jpg               │
 │  ├── flow_prompts.txt                   │
 │  ├── tiktok_caption.txt                 │
 │  └── suno_prompt.txt                    │
 └─────────────────────────────────────────┘
                │
                ▼
 ┌─────────────────────────────────────────┐
 │  YOU: Manual Flow Video Generation      │
 │     1. Open flow.google                 │
 │     2. Upload frame + paste prompt      │
 │     3. Veo 3.1 / Omni Flash, 8 seconds │
 │     4. Download 3 scene MP4s            │
 │     5. Post on TikTok with caption!     │
 └─────────────────────────────────────────┘
```

---

## 🛠️ Requirements

```bash
pip install playwright pillow beautifulsoup4
python -m playwright install
```

| Dependency | Purpose |
|------------|---------|
| `playwright` | Headless browser for TikTok scraping |
| `pillow` | Image format conversion (webp → jpg) |
| `beautifulsoup4` | HTML parsing |

---

## 🚀 Usage

### Step 1: Scrape the Product

```bash
python scrape_product.py "https://vt.tiktok.com/ZS9BPhWgnmMJh-HKAvy/"
```

This creates `output/<timestamp>/` with product images and `product_info.json`.

### Step 2: Generate Frames + Prompts (via Antigravity / Gemini Pro)

Provide the TikTok link in chat. The AI will:
1. Run the scraper automatically
2. Generate 3 consistent keyframe images (9:16)
3. Write all Flow AI prompts, TikTok caption, and Suno prompts
4. Save everything to the output folder

### Step 3: Manual Flow Video Generation

For each scene (1, 2, 3):
1. Open [flow.google](https://flow.google)
2. Upload the corresponding keyframe image
3. Paste the Flow AI prompt from `flow_prompts.txt`
4. Select **Veo 3.1** or **Omni Flash**, duration **8 seconds**
5. Generate → Download MP4

### Step 4: Post on TikTok

Copy the caption from `tiktok_caption.txt` and post with the video!

---

## 📂 Project Structure

```
gemini-flow/
├── README.md              # This file
├── scrape_product.py      # TikTok product page scraper
├── prompt_templates.py    # All prompt templates (parameterized)
├── .gitignore
└── output/                # Generated output (gitignored)
    └── <timestamp>/
        ├── product_info.json
        ├── product_1.jpg ... product_N.jpg
        ├── frame_1_front.jpg
        ├── frame_2_side.jpg
        ├── frame_3_shoulder.jpg
        ├── flow_prompts.txt
        ├── tiktok_caption.txt
        └── suno_prompt.txt
```

---

## 📝 Prompt Rules

### Keyframe Images
- **Character**: Adult Malaysian woman, hijab, 25 y/o
- **Outfit**: Exact product from the listing
- **Background**: Outdoor urban KL street
- **Aspect ratio**: 9:16 (TikTok vertical)
- **Lighting**: Cinematic golden hour
- **No**: Text overlays, watermarks

### Flow AI Video
- **Duration**: 8 seconds per scene
- **Audio**: Malaysian Malay (Bahasa Melayu Malaysia) — NOT Indonesian
- **Lip-sync**: Accurate
- **Camera**: Scene 1 zoom in, Scene 2 slow pan, Scene 3 slow motion
- **No**: Text overlays, watermarks

### TikTok Caption
- **Language**: Bahasa Melayu Malaysia
- **Hooks**: Relatable Malaysian references (office aircond, Genting, K-Drama)
- **Content**: Styling tips, entertainment/info value
- **CTA**: "Tekan beg kuning kat bawah!"
- **No**: Price (violates TikTok policy)

### Suno BGM
- **Style**: Lo-fi hip hop, chill pop, upbeat, TikTok-tempo
- **Lyrics**: Bahasa Melayu Malaysia, catchy verse/chorus/outro

---

## ⚙️ Customization

| Parameter | Default | Options |
|-----------|---------|---------|
| Model character | Malaysian hijab woman | Any ethnicity/style |
| Scene count | 3 (8s each = 24s total) | 2–5 scenes |
| Aspect ratio | 9:16 (TikTok) | 16:9, 1:1 |
| Language | Bahasa Melayu Malaysia | Any |
| Video model | Veo 3.1 / Omni Flash | Any Flow model |
| Background | Outdoor urban KL | Indoor, cafe, studio |

Edit `prompt_templates.py` to customize the templates.

---

## 🔗 References

- [Original Gemini workflow](https://share.gemini.google/acPGgNqdqowG)
- [Google Flow](https://flow.google) — Veo 3.1 / Omni Flash frame-to-video
- [Suno AI](https://suno.com) — BGM generation
- Model: **Gemini Pro** (always)
