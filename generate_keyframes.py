"""
Generate consistent 9:16 TikTok Shop keyframes dynamically for any product
using configured Gemini image generation models.

Usage:
    python generate_keyframes.py --latest
    python generate_keyframes.py --session output/20260908_210526
    python generate_keyframes.py --source-dir output/20260907_160155 --prefix my_product
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google import genai

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

WORKSPACE = Path(__file__).resolve().parent
load_dotenv(WORKSPACE / ".env")

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


def clean_slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return cleaned[:30] if cleaned else "product"


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


def run_generation(source_dir: Path, prefix: Optional[str] = None, force: bool = False):
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No configured GEMINI_API_KEY or GOOGLE_API_KEY was found in .env.")

    if not source_dir.is_dir():
        raise RuntimeError(f"Source directory does not exist: {source_dir}")

    # Load product metadata if present
    product_title = "Muslimah Fashion Product"
    product_details = ""
    info_file = source_dir / "product_info.json"
    if info_file.is_file():
        try:
            with open(info_file, "r", encoding="utf-8") as f:
                info_data = json.load(f)
                product_title = info_data.get("title", product_title)
                product_details = info_data.get("page_text", "")[:400]
        except Exception:
            pass

    if not prefix:
        prefix = clean_slug(product_title)

    # Locate source product images
    source_images = sorted(list(source_dir.glob("product_*.jpg")))
    if not source_images:
        source_images = sorted(list(source_dir.glob("*.jpg")))
    if not source_images:
        raise RuntimeError(f"No reference images (.jpg) found in {source_dir}")

    source_references = source_images[:2]

    KEYFRAME_DIR.mkdir(exist_ok=True)
    output_names = (
        f"{prefix}_frame1_front.jpg",
        f"{prefix}_frame2_side.jpg",
        f"{prefix}_frame3_shoulder.jpg",
    )
    outputs = [KEYFRAME_DIR / name for name in output_names]

    if not force:
        existing = [str(p) for p in outputs if p.exists()]
        if existing:
            print(f"⚠️ Keyframes already exist: {', '.join(existing)}")
            print("Use --force to overwrite if desired.")
            return

    base_desc = (
        f"Use the supplied listing photos as exact product references for: {product_title}. "
        f"{product_details} "
        f"Do not add or remove product details. Do not reproduce marketplace graphic banners or wordmarks."
    )

    frame_prompts = (
        f"Create Frame 1 for a 9:16 TikTok Shop keyframe. Photorealistic full-body lifestyle fashion photo of an adult Malaysian Muslim woman wearing the exact product described, paired with modern modest trousers and a neat light-ivory chiffon bawal hijab. She faces the camera with relaxed shoulders, a natural gentle smile, and comfortable eye contact. Modern Kuala Lumpur covered walkway with a neutral cafe facade softly blurred behind her. Soft golden-hour daylight, natural skin texture, editorial realism, full outfit visible head to toe. Her hands rest naturally by her sides. No text overlay, no logo, no watermark, no price, no raised hands, no waving. {base_desc}",
        f"Create Frame 2 for a 9:16 TikTok Shop keyframe. Keep the same adult Malaysian Muslim woman, face, hijab, outfit, and Kuala Lumpur background as Frame 1. Turn her gently to her left into a 3/4 side profile, showing the relaxed silhouette and drape. Full outfit visible head to toe. One hand can lightly touch the side seam, with the other resting naturally. Soft daylight, photorealistic editorial lifestyle image. No text overlay, no logo, no watermark, no price, no raised hands, no waving. {base_desc}",
        f"Create Frame 3 for a 9:16 TikTok Shop keyframe. Keep the same adult Malaysian Muslim woman, face, hijab, outfit, and Kuala Lumpur background as Frames 1 and 2. She faces mostly away from the camera, then gives a gentle glance back over her right shoulder with a soft natural smile. Show the back silhouette and modest relaxed fit. Full outfit visible head to toe. Her arms remain naturally low by her sides; she may hold a small plain cream tote bag casually at one side. Soft daylight. No text overlay, no logo, no watermark, no price, no raised hands, no waving. {base_desc}",
    )

    client = genai.Client(api_key=api_key)
    completed: list[Path] = []
    success_count = 0

    for prompt, output_path in zip(frame_prompts, outputs, strict=True):
        references = [*source_references, *completed][-3:]
        try:
            generate_one(client, prompt, references, output_path)
            completed.append(output_path)
            success_count += 1
        except Exception as err:
            print(f"❌ Could not generate {output_path.name}: {err}")
            break

    print(f"\n🎉 Generation complete: {success_count}/3 keyframes created in {KEYFRAME_DIR}/")


def main():
    parser = argparse.ArgumentParser(description="Generate 9:16 Keyframe images dynamically")
    parser.add_argument("--latest", action="store_true", help="Use the latest output session")
    parser.add_argument("--session", type=str, help="Specific output session folder or name")
    parser.add_argument("--source-dir", type=str, help="Full path to source folder containing images")
    parser.add_argument("--prefix", type=str, help="Custom prefix for generated frame files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing keyframe files")
    args = parser.parse_args()

    output_dir = WORKSPACE / "output"
    target_dir = None

    if args.source_dir:
        target_dir = Path(args.source_dir)
    elif args.session:
        session_p = Path(args.session)
        target_dir = session_p if session_p.is_dir() else (output_dir / args.session)
    elif args.latest:
        subdirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)
        if subdirs:
            target_dir = subdirs[0]
    else:
        # Default to latest if no argument passed
        subdirs = sorted([d for d in output_dir.iterdir() if d.is_dir()], reverse=True)
        if subdirs:
            target_dir = subdirs[0]

    if not target_dir or not target_dir.exists():
        print("Usage: python generate_keyframes.py [--latest | --session <folder> | --source-dir <path>]")
        return

    print(f"🚀 Generating keyframes from session: {target_dir.name}")
    run_generation(target_dir, prefix=args.prefix, force=args.force)


if __name__ == "__main__":
    main()
