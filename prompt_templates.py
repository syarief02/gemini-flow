"""
Prompt Templates for TikTok Product Promo Generator
=====================================================
Templates used to generate:
- Keyframe image prompts (for Gemini Pro)
- Flow AI video prompts (for Omni Flash 10s portrait)
- TikTok caption & hashtags (Bahasa Melayu Malaysia)
- Suno BGM prompt & lyrics

ANTI-REPETITION & VIRAL HOOK SYSTEM (generation_history.json):
- Tracks all previously used opening hooks and sign-off CTAs across sessions.
- Before generating new content, check the last 7 entries in the history file
  and ensure the new generation uses genuinely different phrasing and angles.
- 8 Proven Viral Hook Archetypes (2-Second Retention Rule):
  1. The Unspoken Daily Dilemma (Tropical Climate / Comfort / Sauna Effect)
  2. The Flattering Silhouette / Visual Insecurity Solution (Auto-slimming, hiding tummy, thigh cuts)
  3. The Price-Quality Myth-Buster (Expensive outdoor brands vs high-quality affordable items)
  4. The Hidden Gem / Secret Discovery (Effortless 2-second styling secret, overlooked cut)
  5. The Visual Pattern Interrupt / Direct Question ("Korang perasan tak...", "Tahu tak kenapa...")
  6. The Relatable Lifestyle Dilemma (Waking up late, rushed mornings, ironless prep)
  7. The Stereotype-Buster / Pain-Point Contrast (Challenging category assumptions)
  8. The FOMO / FYP Social Proof Trend (FYP trend awareness, viral discovery)
- After generating, ALWAYS log the new entry with save_generation_history() from generate_prompts.py.
- NO fixed rotation scripts — just be aware of what was already used and create fresh words on the spot.
"""

# =============================================================================
# KEYFRAME IMAGE GENERATION PROMPTS (Gemini Pro)
# =============================================================================
# These are used to generate 3 consistent 9:16 keyframe images.
# Replace {product_description} with the actual product details.

FRAME_1_FRONT = """Photorealistic portrait photo of a cute adult 25-year-old Malaysian woman \
wearing a modern stylish hijab and {product_description}. \
She is standing outdoors on a clean modern urban street in Kuala Lumpur, \
looking directly at the camera with a warm smile. \
Both arms rest naturally and relaxed by her sides with empty hands. \
Full outfit visible from head to toe, 9:16 vertical portrait, \
shot on 35mm lens, natural golden hour daylight, photorealistic, \
cinematic lighting, sharp focus, no handbag, no tote bag, no purse, no props, no text overlay, no watermark."""

FRAME_2_SIDE = """The same Malaysian woman wearing the exact same hijab and \
{product_description} from the reference image. \
She is now turned to her left in a 3/4 side profile view, \
showcasing how the outfit drapes and the cut creates a flattering silhouette. \
Same outdoor KL urban street background. \
Arms rest relaxed at her sides with empty hands, one hand may lightly touch the side garment seam. \
Full outfit visible from head to toe, 9:16 vertical portrait, \
consistent face, outfit, and styling, cinematic golden hour lighting, \
sharp focus, no handbag, no tote bag, no purse, no props, no text overlay, no watermark."""

FRAME_3_SHOULDER = """The same Malaysian woman wearing the exact same hijab and \
{product_description} from the reference images. \
She has turned around with her back to the camera, \
looking over her right shoulder towards the viewer with a charming warm smile. \
Showcasing the back structure and silhouette of the outfit. \
Same outdoor KL urban street background. \
Both arms remain naturally low by her sides with empty hands. Strictly zero props. \
Full outfit visible, 9:16 vertical portrait, \
consistent face, identical outfit, and styling, cinematic golden hour lighting, \
sharp focus, no handbag, no tote bag, no purse, no tumbler, no props, no text overlay, no watermark."""


# =============================================================================
# FLOW AI VIDEO PROMPTS (Omni Flash 10s portrait)
# =============================================================================
# Each prompt = one English visual/audio paragraph + a verbatim Spoken Malay line.
# The dialogue follows a natural 3-Act structure (Intro → Detail → Sign-off).
#
# FRAME-TO-VIDEO RULES (proven 2026-10-19; automate_flow.py enforces the hard ones):
# - "Static locked-off vertical shot, the camera does not move." All 3 keyframes share one
#   background, so camera pans/zooms/orbits fight the frames and cause warping.
#   The SUBJECT turns in place between the Start pose and the End pose instead.
# - Spoken line: max 22 words (aim 16-20), 1-2 short sentences. Longer lines get rushed,
#   cut off, or lose lip-sync in a 10s clip.
# - Scene 2 ends with her back to camera: the line must be finished before she turns away.
#   Scene 3 starts from the back: she speaks once she faces the camera.
# - "No background music": the Suno instrumental is added later.
#
# PERSONALITY RULES FOR ALL SCENES:
# - Speak in a calm, relaxed, and effortless tone—like a creator chatting casually with followers.
# - AVOID exaggerated gestures, frantic whispers, or wide-eyed hyper-excitement.
# - STRICTLY FORBID repetitive outro crutches (DO NOT always end with "...di bawah ya" or "...ya").
# - Anti-repetition is handled by generation_history.json — any opener/sign-off style is valid
#   as long as it differs from what was recently used.
# - Natural, smooth delivery with relaxed micro-expressions and clear lip-syncing.

# {subject} = model + hijab, e.g. "A young Malaysian Muslim woman in a taupe chiffon hijab"
# {outfit}  = garment details + bottoms + shoes, exactly as in the keyframes
# {setting} = the shared keyframe background, e.g. "a sunlit cafe courtyard with rattan chairs and potted palms"

FLOW_AUDIO = """For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. \
No background music, only her voice and soft ambient sound. \
Ensure there are no text overlays or watermarks."""

# Scene 1: Start = Frame 1 (front) -> End = Frame 2 (3/4 side)
FLOW_SCENE_1_INTRO = """Static locked-off vertical shot, the camera does not move. \
{subject} stands in {setting}, wearing {outfit}. \
She starts facing the camera with a warm natural smile and speaks directly to the camera, \
then slowly pivots in place into a three-quarter angle while keeping eye contact. \
Her hands stay empty and relaxed at her sides the whole time, no gestures, no props. \
The background, lighting, outfit and hijab stay identical throughout. \
Soft natural daylight, realistic fabric movement. """ + FLOW_AUDIO + """

Spoken Malay (Lip-sync): "{dialogue_scene_1}\""""

# Scene 2: Start = Frame 2 (3/4 side) -> End = Frame 3 (back, glancing over shoulder)
FLOW_SCENE_2_PRODUCT = """Static locked-off vertical shot, the camera does not move. \
The same {subject_short}, wearing {outfit}, in the same {setting}. \
She starts at a three-quarter angle speaking warmly to the camera, then slowly keeps turning in place \
until her back faces the camera, glancing back over her shoulder with a smile so her face stays visible \
in profile, showing off {back_detail}. \
Her hands stay empty and relaxed at her sides the whole time, no gestures, no props. \
The background, lighting, outfit and hijab stay identical throughout. \
Soft natural daylight, realistic fabric movement. """ + FLOW_AUDIO + """

Spoken Malay (Lip-sync): "{dialogue_scene_2}\""""

# Scene 3: Start = Frame 3 (back) -> End = Frame 1 (front), closing the 360° loop
FLOW_SCENE_3_OUTRO = """Static locked-off vertical shot, the camera does not move. \
The same {subject_short}, wearing {outfit}, in the same {setting}. \
She starts with her back to the camera glancing over her shoulder with a smile, then slowly turns in place \
all the way back to face the camera and speaks warmly and directly to the camera, \
ending in a relaxed front-facing standing pose. \
Her hands stay empty and relaxed at her sides the whole time, no waving, no raised hands, no props. \
The background, lighting, outfit and hijab stay identical throughout. \
Soft natural daylight, realistic fabric movement. """ + FLOW_AUDIO + """

Spoken Malay (Lip-sync): "{dialogue_scene_3}\""""



# =============================================================================
# TIKTOK CAPTION TEMPLATE (Bahasa Melayu Malaysia)
# =============================================================================
# Rules:
# - No price mentioned (violates TikTok policy)
# - Relatable Malaysian hooks (problem-solution or aesthetic lifestyle)
# - Styling/usage tips tailored specifically to the item
# - CTA pointing to yellow basket
# - STRICTLY NEVER use the em-dash "—" or en-dash "–" character anywhere in the caption (use colon, comma, or natural phrasing)
# - NO generic spam tags (#RacunTikTok, #fyp, #viral)
# - Use 4-6 targeted, high-intent SEO hashtags (Product + Occasion + Community)

CAPTION_TEMPLATE = """{hook}

{product_pitch}

{styling_tips}

{cta}

{targeted_seo_hashtags}"""

# Example high-intent niche hashtags (no #RacunTikTok / #fyp)
# Format: [Product Name/Type] + [Occasion/Problem] + [Target Community]



# =============================================================================
# SUNO BGM TEMPLATE (INSTRUMENTAL ONLY — NO LYRICS)
# =============================================================================
# Instrumental only so it doesn't clash with Flow AI spoken Malay lip-sync.
# Use directly in Suno with 'Instrumental' toggle enabled.

SUNO_STYLE_TEMPLATE = (
    "Upbeat, breezy lo-fi indie chill pop, bright fingerpicked acoustic guitar, "
    "smooth Rhodes electric piano chords, crisp lo-fi hip-hop drum beat, warm synth bass, "
    "uplifting and stylish modern Malaysian cafe lifestyle vibe, 110 BPM, pure instrumental, "
    "no vocals, high-production polish, seamless loopable feel"
)

