"""Generate consistent TikTok Shop keyframes using an already configured Gemini API key."""

from __future__ import annotations

import base64
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai


WORKSPACE = Path(__file__).resolve().parent
SOURCE_DIR = WORKSPACE / "output" / "20260907_160155"
KEYFRAME_DIR = WORKSPACE / "keyframes"
MODEL_CANDIDATES = (
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
    "gemini-3-pro-image",
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image",
)


def image_input(path: Path) -> dict[str, str]:
    return {
        "type": "image",
        "data": base64.b64encode(path.read_bytes()).decode("ascii"),
        "mime_type": "image/jpeg",
    }


BASE_PRODUCT_DETAILS = """Use the supplied listing photos as exact product references. The promoted garment is a deep indigo-blue long-sleeve denim blouse with a pointed polo collar, full front placket of small brown buttons, button cuffs, and a rounded hem. Preserve the pink butterfly embroidery precisely: one small butterfly on the viewer-left upper chest, one on the viewer-left lower torso, and one large outlined butterfly near the viewer-left lower hem. Do not add or remove product details. Do not reproduce the marketplace graphic banners or brand wordmarks from the references."""

FRAME_PROMPTS = (
    """Create Frame 1 for a 9:16 TikTok Shop keyframe. Photorealistic full-body lifestyle fashion photo of an adult Malaysian Muslim woman wearing the exact blouse described in the product references, cream wide-leg trousers, and a neat light-ivory chiffon bawal hijab. She faces the camera with relaxed shoulders, a natural gentle smile, and comfortable eye contact. Modern Kuala Lumpur covered walkway with a neutral cafe facade softly blurred behind her. Soft golden-hour daylight, natural skin texture, editorial realism, full outfit visible head to toe. Her hands rest naturally by her sides. No text overlay, no logo, no watermark, no price, no raised hands, no waving. """ + BASE_PRODUCT_DETAILS,
    """Create Frame 2 for a 9:16 TikTok Shop keyframe. Keep the same adult Malaysian Muslim woman, face, light-ivory chiffon bawal hijab, cream wide-leg trousers, exact blouse, and Kuala Lumpur covered-walkway background as Frame 1. Turn her gently to her left into a 3/4 side profile, showing the relaxed silhouette, denim drape, cuff and curved hem. Full outfit visible head to toe. One hand can lightly touch the blouse side seam, with the other resting naturally. Soft golden-hour daylight, photorealistic editorial lifestyle image. No text overlay, no logo, no watermark, no price, no raised hands, no waving. """ + BASE_PRODUCT_DETAILS,
    """Create Frame 3 for a 9:16 TikTok Shop keyframe. Keep the same adult Malaysian Muslim woman, face, light-ivory chiffon bawal hijab, cream wide-leg trousers, exact blouse, and Kuala Lumpur covered-walkway background as Frames 1 and 2. She faces mostly away from the camera, then gives a gentle glance back over her right shoulder with a soft natural smile. Show the blouse back silhouette and modest relaxed fit. Full outfit visible head to toe. Her arms remain naturally low by her sides; she may hold a small plain cream tote bag casually at one side. Soft golden-hour daylight, photorealistic editorial lifestyle image. No text overlay, no logo, no watermark, no price, no raised hands, no waving. """ + BASE_PRODUCT_DETAILS,
)

OUTPUT_NAMES = (
    "bgm_polo_denim_butterfly_frame1_front.jpg",
    "bgm_polo_denim_butterfly_frame2_side.jpg",
    "bgm_polo_denim_butterfly_frame3_shoulder.jpg",
)


def generate_one(client: genai.Client, prompt: str, references: list[Path], output_path: Path) -> str:
    last_error: Exception | None = None
    inputs = [{"type": "text", "text": prompt}, *(image_input(path) for path in references)]
    for model in MODEL_CANDIDATES:
        try:
            print(f"Generating {output_path.name} with {model}...", flush=True)
            interaction = client.interactions.create(
                model=model,
                input=inputs,
                response_format={
                    "type": "image",
                    "mime_type": "image/jpeg",
                    "aspect_ratio": "9:16",
                    "image_size": "1K",
                },
            )
            generated = interaction.output_image
            if not generated or not generated.data:
                raise RuntimeError("The model returned no image data.")
            output_path.write_bytes(base64.b64decode(generated.data))
            print(f"SUCCESS {model}: {output_path}", flush=True)
            return model
        except Exception as error:
            last_error = error
            print(f"FAILED {model}: {error}", flush=True)
    raise RuntimeError(f"All configured Gemini image models failed for {output_path.name}: {last_error}")


def main() -> None:
    load_dotenv(WORKSPACE / ".env")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No configured GEMINI_API_KEY or GOOGLE_API_KEY was found.")

    source_references = [SOURCE_DIR / "product_1.jpg", SOURCE_DIR / "product_2.jpg"]
    missing = [str(path) for path in source_references if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing product reference images: {', '.join(missing)}")

    KEYFRAME_DIR.mkdir(exist_ok=True)
    outputs = [KEYFRAME_DIR / name for name in OUTPUT_NAMES]
    existing = [str(path) for path in outputs if path.exists()]
    if existing:
        raise RuntimeError(f"Refusing to overwrite existing keyframes: {', '.join(existing)}")

    client = genai.Client(api_key=api_key)
    completed: list[Path] = []
    for prompt, output_path in zip(FRAME_PROMPTS, outputs, strict=True):
        references = [*source_references, *completed][-3:]
        generate_one(client, prompt, references, output_path)
        completed.append(output_path)


if __name__ == "__main__":
    main()
