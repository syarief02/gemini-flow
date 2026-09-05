"""
Prompt Templates for TikTok Product Promo Generator
=====================================================
Templates used to generate:
- Keyframe image prompts (for Gemini Pro)
- Flow AI video prompts (for Veo 3.1 / Omni Flash 8s)
- TikTok caption & hashtags (Bahasa Melayu Malaysia)
- Suno BGM prompt & lyrics

ANTI-REPETITION SYSTEM (generation_history.json):
- Tracks all previously used opening hooks and sign-off CTAs across sessions.
- Before generating new content, check the last 7 entries in the history file
  and ensure the new generation uses genuinely different phrasing and angles.
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
Full outfit visible from head to toe, 9:16 vertical portrait, \
shot on 35mm lens, natural golden hour daylight, photorealistic, \
cinematic lighting, sharp focus, no text overlay, no watermark."""

FRAME_2_SIDE = """The same Malaysian woman wearing the exact same hijab and \
{product_description} from the reference image. \
She is now turned to her left in a 3/4 side profile view, \
showcasing how the outfit drapes and the cut creates a flattering silhouette. \
Same outdoor KL urban street background. \
Full outfit visible from head to toe, 9:16 vertical portrait, \
consistent face, outfit, and styling, cinematic golden hour lighting, \
sharp focus, no text overlay, no watermark."""

FRAME_3_SHOULDER = """The same Malaysian woman wearing the exact same hijab and \
{product_description} from the reference images. \
She has turned around with her back to the camera, \
looking over her right shoulder towards the viewer with a charming warm smile. \
Showcasing the back structure and silhouette of the outfit. \
Same outdoor KL urban street background. \
Full outfit visible, 9:16 vertical portrait, \
consistent face and styling, cinematic golden hour lighting, \
sharp focus, no text overlay, no watermark."""


# =============================================================================
# FLOW AI VIDEO PROMPTS (Veo 3.1 / Omni Flash 8s)
# =============================================================================
# Each prompt combines visual direction + audio/dialogue in one paragraph.
# The dialogue follows a natural 3-Act structure (Intro → Detail → Sign-off).
#
# PERSONALITY RULES FOR ALL SCENES:
# - Speak in a calm, relaxed, and effortless tone—like a creator chatting casually with followers.
# - AVOID exaggerated gestures, frantic whispers, or wide-eyed hyper-excitement.
# - STRICTLY FORBID repetitive outro crutches (DO NOT always end with "...di bawah ya" or "...ya").
# - Anti-repetition is handled by generation_history.json — any opener/sign-off style is valid
#   as long as it differs from what was recently used.
# - Natural, smooth delivery with relaxed micro-expressions and clear lip-syncing.

FLOW_SCENE_1_INTRO = """Generate an 8-second video from the provided frame of an adult \
Malaysian woman wearing a hijab and {product_description}. \
The camera maintains a stable, smooth framing with a gentle subtle zoom towards her. \
She has a relaxed, confident posture and gives a natural, pleasant smile with comfortable eye contact towards the camera. \
Ensure there are no text overlays or watermarks in the video. \
The subject speaks with subtle, natural facial expressions and accurate lip-syncing. \
Her tone is calm, warm, and conversational—effortless and relatable. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice must sound natural, polished, and friendly, using 'saya'. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_1}" """

FLOW_SCENE_2_PRODUCT = """Generate an 8-second video from the provided frame of the woman \
in {product_description} turned to a 3/4 side profile view. \
The camera performs a slow, smooth cinematic pan across the outfit to showcase the clean silhouette and fabric texture. \
She gestures naturally and casually towards the garment with relaxed, subtle hand movements. \
Ensure there are no text overlays or watermarks in the video. \
The subject speaks towards the camera with a calm, friendly, and informative tone with accurate lip-syncing. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice should sound genuine and helpful, like giving casual styling advice, using 'saya'. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_2}" """

FLOW_SCENE_3_OUTRO = """Generate an 8-second video from the provided frame of the woman \
in {product_description} turning to glance back over her shoulder with a relaxed, soft smile. \
Add a gentle cinematic soft-focus effect with natural lighting. \
Her arms and hands rest naturally at her side or hold her bag casually without any awkward waving gestures. \
Ensure there are no text overlays or watermarks in the video. \
The subject speaks with warm, friendly sincerity and accurate lip-syncing. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice should sound warm, inviting, and natural, using 'saya'. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_3}" """



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

