"""
Prompt Templates for TikTok Product Promo Generator
=====================================================
Templates used to generate:
- Keyframe image prompts (for Gemini Pro)
- Flow AI video prompts (for Veo 3.1 / Omni Flash 8s)
- TikTok caption & hashtags (Bahasa Melayu Malaysia)
- Suno BGM prompt & lyrics
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
# Each prompt is a single combined prompt (no separate audio prompt).
# Replace {product_description} with the actual product details.
# Replace {dialogue_scene_X} with the scene-specific dialogue.

FLOW_SCENE_1_INTRO = """Generate an 8-second video from the provided frame of an adult \
Malaysian woman wearing a hijab and {product_description} outdoors. \
The camera slowly zooms in to highlight the outfit's details. \
Ensure there are no text overlays or watermarks in the video. \
The subject must look directly at the camera with accurate lip-syncing. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_1}" """

FLOW_SCENE_2_PRODUCT = """Generate an 8-second video from the provided frame of the woman \
in {product_description} posing to her left. \
The camera performs a subtle slow pan to emphasize the fabric quality and cut of the outfit. \
Ensure there are no text overlays or watermarks in the video. \
The subject subtly turns her head to speak with accurate lip-syncing. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_2}" """

FLOW_SCENE_3_OUTRO = """Generate an 8-second video from the provided frame of the woman \
in {product_description} turning to look over her shoulder, \
showcasing the back details of the outfit. \
Add a subtle cinematic slow-motion effect as she smiles. \
Ensure there are no text overlays or watermarks in the video. \
The subject must speak with accurate lip-syncing. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_3}" """


# =============================================================================
# TIKTOK CAPTION TEMPLATE (Bahasa Melayu Malaysia)
# =============================================================================
# Rules:
# - No price mentioned (violates TikTok policy)
# - Relatable Malaysian hooks
# - Styling tips for hijab-wearing women
# - CTA pointing to yellow bag / link in bio
# - Malaysian-focused hashtags

CAPTION_TEMPLATE = """{hook}

{product_pitch}

{styling_tips}

{cta}

{hashtags}"""

DEFAULT_HASHTAGS = (
    "#RacunTikTok #OOTDHijab #FashionMalaysia #GayaTiktok "
    "#OutfitKePejabat #TiktokFashion #OOTDMalaysia "
    "#OOTDGenting #GayaHijabi #FypMalaysia"
)


# =============================================================================
# SUNO BGM TEMPLATE
# =============================================================================

SUNO_STYLE = (
    "Upbeat, trendy, lo-fi hip hop, chill pop, modern, rhythmic, catchy, bright, "
    "sophisticated, subtle electronic elements, confident, relaxing but with a good "
    "tempo for TikTok, fashionable."
)

SUNO_LYRICS_TEMPLATE = """[Verse]
{verse}

[Chorus]
{chorus}

[Outro]
{outro}"""
