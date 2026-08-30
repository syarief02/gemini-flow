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
# Each prompt combines visual direction + audio/dialogue in one paragraph.
# The dialogue follows a 3-Act storytelling arc (Hook → Reveal → Close).
#
# PERSONALITY RULES FOR ALL SCENES:
# - Speak like a close bestie sharing a discovery, NOT a salesperson.
# - Use dramatic vocal dynamics (whisper → normal → excited).
# - Natural pauses, gasps, and emphasis make it feel real.
# - NEVER just list product features. Paint scenes the viewer can feel.

FLOW_SCENE_1_INTRO = """Generate an 8-second video from the provided frame of an adult \
Malaysian woman wearing a hijab and {product_description} outdoors. \
The camera starts at a medium shot and slowly zooms in to a close-up of her face. \
She leans in slightly with wide, excited eyes as if sharing a juicy secret with her best friend. \
Ensure there are no text overlays or watermarks in the video. \
The subject must look directly at the camera with expressive, animated facial movements and accurate lip-syncing. \
Her tone starts as an excited whisper that builds into curiosity. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice should sound warm, personal, and genuinely excited—like a real person talking to a close friend, \
NOT like someone reading a script. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_1}" """

FLOW_SCENE_2_PRODUCT = """Generate an 8-second video from the provided frame of the woman \
in {product_description} turned to a side profile view. \
The camera performs a smooth, slow cinematic pan across the outfit to emphasize texture and cut. \
She naturally touches and adjusts the product with genuine delight—running her fingers along the fabric, \
adjusting a collar, or gently pulling at a feature to show it off. \
Ensure there are no text overlays or watermarks in the video. \
The subject subtly turns her head to speak towards the camera with confident, warm energy and accurate lip-syncing. \
Her tone is like a trusted friend giving honest styling advice. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice should use sensory descriptive language that makes the viewer FEEL the product through words. \
Explicitly translate the following English text into standard Malaysian Malay \
for the spoken audio: "{dialogue_scene_2}" """

FLOW_SCENE_3_OUTRO = """Generate an 8-second video from the provided frame of the woman \
in {product_description} turning to glance back over her shoulder with a knowing, confident smile. \
Add a subtle cinematic soft-focus glow effect with gentle slow-motion. \
She gives a casual, friendly wave or gentle thumbs-up as she delivers the final line. \
Ensure there are no text overlays or watermarks in the video. \
The subject speaks with warm urgency and accurate lip-syncing—like a friend giving a last-minute warning \
before something sells out. \
For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent—strictly NOT an Indonesian accent. \
The voice should sound warm but urgent—creating a sense of FOMO and making the purchase feel like a smart decision. \
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
