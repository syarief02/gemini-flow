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
- The archetype is only the hook's ANGLE. Also vary its FORMAT (HOOK_FORMATS in generate_prompts.py:
  turn_reveal, dont_buy, honest_take, confession, numbered, detail_tease, scenario, this_not_that,
  myth_statement, identity_callout, direct_question). Hooks went stale in Oct-Nov 2026 because every
  one was a "Korang ...?" question (user feedback 2026-11-15).
- `python generate_prompts.py --hook-brief` shows what recent hooks share and which formats are fresh;
  `--audit-hook "<line>" ...` scores candidates for freshness (opening word, format, question streak,
  repeated and worn-out phrases, hook sentence over 12 words).
- After generating, ALWAYS log the new entry with save_generation_history(..., hook_format=...) from generate_prompts.py.
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

# NON-CLOTHING PRODUCTS (added 2026-11-21). The frames above assume the product IS the outfit, and
# they ban every bag. For a bag, hat or scarf that leaves the product tiny or missing: the school-bag
# run of 2026-11-20 put the bag on a side table at ~10% of the frame while she talked about straps
# nobody could see. Morphing comes from props that APPEAR, MOVE or CHANGE between frames, not from
# the product itself. So for a wearable product, replace the "no handbag/no tote bag" words with
# WORN_PRODUCT_LINE in all three frame prompts (same placement every time):
#   - she WEARS it, never holds it; her hands stay empty at her sides;
#   - Frame 3 (back to camera) shows a backpack's back and straps: a natural turn_reveal payoff.
# CHILD-SIZE products (kids' bags, kids' clothes): an adult wearing them misstates the size, and
# AI-generated children in ads are sensitive. Stop and ask the user how to present the product.
WORN_PRODUCT_LINE = ("She wears the {product} {placement} in all three frames, in exactly the same position, "
                     "clearly visible and large in the frame, as part of her outfit. Her hands stay empty and "
                     "relaxed at her sides. No other bag, purse, phone, cup or prop anywhere.")
PRODUCT_PLACEMENTS = {
    "backpack": "on both shoulders, straps adjusted evenly",
    "crossbody_bag": "across her body, strap over her left shoulder, bag resting at her right hip",
    "shoulder_bag": "on her left shoulder, bag resting at her left hip",
    "hat": "on her head over the hijab",
    "scarf_shawl": "draped around her shoulders over the outfit",
}


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
# - Spoken line (rule of 2026-10-20, user feedback): 2-3 NATURAL spoken sentences, 28-32 words
#   (hard limits 24-34). The old ~40-word conversational lines sounded natural but were sometimes
#   cut off; the 14-21-word "spec list" lines of 2026-10-19 sounded stretched and unnatural.
#   Write it the way a Malaysian creator talks to a friend ("dia", "je", "tau", "memang", "la"),
#   pick 1-2 details per scene and say why they matter, no colons/semicolons, no spec lists.
# - She talks continuously for the whole clip, including while she turns (no waiting to speak).
# - "No background music": the Suno instrumental is added later.
#
# PERSONALITY RULES FOR ALL SCENES:
# - She is a creator TALKING TO the viewer, not a narrator reading a product page.
# - Lively and expressive (see DELIVERY_STYLES below), never flat, shouting, hard-selling or
#   exaggerated whispering.
# - STRICTLY FORBID repetitive outro crutches (DO NOT always end with "...di bawah ya" or "...ya").
# - Anti-repetition is handled by generation_history.json — any opener/sign-off style is valid
#   as long as it differs from what was recently used.

# =============================================================================
# CHARACTER DELIVERY STYLES (how she promotes)
# =============================================================================
# Until 2026-11-17 every clip had the same performance: "pleasant, friendly smile, warm facial
# expressions, turns 45 degrees, hands at her sides", a "calm, relaxed" voice, and lines that read
# like a brochure ("Bila pusing ke tepi, perincian...", "Kemasan belakang..."). The user found it
# boring. Pick ONE style per product (prefer one the brief lists as fresh:
# `python generate_prompts.py --hook-brief`) and use it in all three scenes:
#   - `voice` goes into every scene's audio direction ("Her delivery is {voice}."),
#   - `acting[n]` goes into scene n's visual direction,
#   - `script` shapes how she talks in the spoken lines.
# Expression lives in her face, eyes, head and shoulders. Her hands stay empty and low at her sides
# (no hand gestures, no waving, no props): hands are where Flow morphs most, and every end keyframe
# has her hands at her sides.
DELIVERY_STYLES = {
    "excited_bestie": {
        "name": "Kawan Baik Teruja (Excited Bestie)",
        "voice": ("bright, lively and genuinely excited, like telling her best friend about a great find, "
                  "with a quick light laugh on the fun part and real stress on the key words"),
        "acting": {
            1: "her eyebrows lift and her eyes light up on the first line, and she breaks into a big genuine smile",
            2: ("she glances down at the detail she is talking about and back up at the camera, delighted, "
                "with a small impressed nod and a quick laugh"),
            3: "she turns back to the camera beaming, with a happy little shrug of her shoulders and a firm nod on her last words",
        },
        "script": "Reacts out loud (serius, eh, gila), short punchy sentences, talks to korang a lot.",
    },
    "honest_sister": {
        "name": "Kakak Jujur (Honest Big Sister)",
        "voice": ("warm, confident and matter-of-fact with a playful edge, like an older sister giving honest "
                  "advice, with firm emphasis on her verdict"),
        "acting": {
            1: "she gives a knowing half-smile and a slight head tilt, as if she is about to tell the truth",
            2: "she looks at the detail she is talking about with an approving little nod and satisfied, narrowed eyes",
            3: "she turns back with a decisive nod and a warm, trust-me grin",
        },
        "script": "Gives a clear verdict and one honest 'this is NOT for you if...' aside, then 'percaya la' energy.",
    },
    "playful_tease": {
        "name": "Usik Manja (Playful Tease)",
        "voice": ("playful and teasing, with a cheeky smile you can hear, rising intonation on the tease, "
                  "then a warm little laugh when she reveals it"),
        "acting": {
            1: "she raises one eyebrow with a cheeky smirk, as if she knows something the viewer doesn't",
            2: "she gives a teasing grin and a little told-you head tilt, letting the viewer in on it",
            3: "she turns back with a light laugh and a satisfied told-you-so nod",
        },
        "script": "Teases and opens loops (tunggu, kan saya dah cakap), pays them off, light humour.",
    },
    "insider_tip": {
        "name": "Kongsi Rahsia (Insider Tip)",
        "voice": ("intimate and confident, she drops her voice slightly on the key tip as if sharing a secret, "
                  "then brightens again, never a whisper"),
        "acting": {
            1: "she leans a little toward the camera with a conspiratorial smile",
            2: "she glances at the detail she is talking about, then back at the camera with raised eyebrows as if saying 'see?'",
            3: "she straightens up as she turns back, with a pleased, knowing smile and a small nod",
        },
        "script": "Shares a tip or styling trick (tip saya, ramai tak tahu), specific and a little exclusive.",
    },
    "confident_stylist": {
        "name": "Stylist Yakin (Confident Stylist)",
        "voice": "poised, upbeat and confident, crisp and clear, like a stylist who knows exactly what works",
        "acting": {
            1: "she lifts her chin slightly with a confident smile and holds strong eye contact",
            2: "she pulls her shoulders back and gives an approving nod at the silhouette as she turns",
            3: "she settles into the front pose with a confident grin and a small decisive nod",
        },
        "script": "Styling advice (padan dengan, pakai dengan), clear contrasts, decisive statements, no hedging.",
    },
}

# {subject} = model + hijab, e.g. "A young Malaysian Muslim woman in a taupe chiffon hijab"
# {outfit}  = garment details + bottoms + shoes, exactly as in the keyframes
# {setting} = the shared keyframe background, e.g. "a sunlit cafe courtyard with rattan chairs and potted palms"
# {voice}, {acting_1}, {acting_2}, {acting_3} = from the product's DELIVERY_STYLES entry

# automate_flow.py appends this when a prompt has no pace line ("continuously") of its own.
PACE_LINE = ("She talks continuously from the first second until the clip ends, with lively, expressive "
             "intonation that rises and falls naturally, stressing the key words and reacting with real feeling "
             "like telling a close friend about a great find, never flat or monotone, never shouting or "
             "hard-selling, and keeps talking while she turns.")

EXPRESSIVE_LINE = ("Her face, eyes, head and shoulders stay expressive and alive the whole time, reacting to what "
                   "she says, while her hands stay empty and relaxed at her sides, no hand gestures, no props.")

FLOW_AUDIO = """For the audio, generate a highly realistic female voice with a standard \
Malaysian Malay (Bahasa Melayu Malaysia) accent, strictly NOT an Indonesian accent. \
Her delivery is {voice}. \
No background music, only her voice and soft ambient sound. \
Ensure there are no text overlays or watermarks. """ + PACE_LINE

# Scene 1: Start = Frame 1 (front) -> End = Frame 2 (3/4 side). Beat: the hook (curiosity).
FLOW_SCENE_1_INTRO = """Static locked-off vertical shot, the camera does not move. \
{subject} stands in {setting}, wearing {outfit}. \
She starts facing the camera and talks straight to it like a creator talking to her followers, and {acting_1}. \
She keeps talking as she slowly pivots in place into a three-quarter angle, keeping eye contact. \
""" + EXPRESSIVE_LINE + """ \
The background, lighting, outfit and hijab stay identical throughout. \
Soft natural daylight, realistic fabric movement. """ + FLOW_AUDIO + """

Spoken Malay (Lip-sync): "{dialogue_scene_1}\""""

# Scene 2: Start = Frame 2 (3/4 side) -> End = Frame 3 (back, glancing over shoulder). Beat: her reaction (delight).
FLOW_SCENE_2_PRODUCT = """Static locked-off vertical shot, the camera does not move. \
The same {subject_short}, wearing {outfit}, in the same {setting}. \
She starts at a three-quarter angle talking to the camera, and {acting_2}, \
and keeps talking as she slowly turns in place until her back faces the camera, glancing back over her \
shoulder so her face stays visible in profile, showing off {back_detail}. \
""" + EXPRESSIVE_LINE + """ \
The background, lighting, outfit and hijab stay identical throughout. \
Soft natural daylight, realistic fabric movement. """ + FLOW_AUDIO + """

Spoken Malay (Lip-sync): "{dialogue_scene_2}\""""

# Scene 3: Start = Frame 3 (back) -> End = Frame 1 (front), closing the 360° loop. Beat: payoff + verdict (confidence).
FLOW_SCENE_3_OUTRO = """Static locked-off vertical shot, the camera does not move. \
The same {subject_short}, wearing {outfit}, in the same {setting}. \
She starts with her back to the camera glancing over her shoulder and starts talking right away, \
slowly turning in place all the way back to face the camera while she talks directly to it, \
and {acting_3}, ending in a relaxed front-facing standing pose. \
""" + EXPRESSIVE_LINE + """ No waving, no raised hands. \
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

