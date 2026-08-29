"""
Dynamic Prompt & Content Generator for TikTok Products
======================================================
Uses Gemini Pro (gemini-1.5-pro / gemini-2.5-pro) to generate:
- 3 Unique Keyframe Image Prompts (Front, Side Profile, Over Shoulder)
- 3 Flow AI Video Generation Prompts (Veo 3.1 / Omni Flash 8s with Malaysian Malay Lip-Sync)
- TikTok Caption + Hashtags (Bahasa Melayu Malaysia, policy-safe)
- Suno BGM Style + Lyrics (Bahasa Melayu)

Usage:
    python generate_prompts.py <path_to_product_info.json>
"""

import os
import sys
import json
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert Malaysian TikTok e-commerce content strategist and creative AI prompter.
Your goal is to analyze the given product details and generate unique, high-converting promotional assets for the Malaysian Muslimah / TikTok Shop audience.

Always adhere to these strict rules:
1. NO REPEATING GENERIC LINES: Do NOT reuse the same old lines (e.g. "masuk office rasa macam peti ais") unless specifically relevant. Every product has unique features—analyze the collar type, fabric, drawstring, length, colors, sizes, and specific styling benefits.
2. AUDIENCE: Malaysian audience (Bahasa Melayu Malaysia, standard KL/urban accent—strictly NOT Indonesian).
3. FLOW AI PROMPTS: 3 separate 8-second scenes (Scene 1: Intro, Scene 2: Product Detail, Scene 3: Outro/CTA). Each prompt must be a single combined English prompt that instructs Flow AI / Veo 3.1 to lip-sync spoken audio translated into standard Malaysian Malay.
4. TIKTOK CAPTION: High-value Malaysian copywriting with relatable hook, feature breakdown, styling tips for hijab wearers, beg kuning CTA, and zero direct price mentions (TikTok policy compliance).
5. SUNO BGM: Style prompt + unique singable Malay lyrics matching the product's mood.

Return the result as a valid JSON object with the following schema:
{
  "product_summary": "string",
  "keyframe_prompts": {
    "frame_1_front": "string",
    "frame_2_side": "string",
    "frame_3_shoulder": "string"
  },
  "flow_ai_prompts": {
    "scene_1_intro": "string",
    "scene_2_detail": "string",
    "scene_3_outro": "string"
  },
  "tiktok_caption": "string",
  "suno_bgm": {
    "style": "string",
    "lyrics": "string"
  }
}
"""

def generate_with_gemini_pro(product_info: dict) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment. Using direct template engine.")
        return None
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        prompt = f"""Analyze this product and generate complete assets:
Product Title: {product_info.get('title', '')}
Product Details: {product_info.get('page_text', '')[:1500]}

Generate completely unique, non-repeating prompts and copy tailored specifically to this product's exact attributes."""

        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt,
            config={
                'system_instruction': SYSTEM_PROMPT,
                'response_mime_type': 'application/json'
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
        res = generate_with_gemini_pro(data)
        if res:
            print(json.dumps(res, indent=2, ensure_ascii=False))
