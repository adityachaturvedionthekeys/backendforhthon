"""
ImageGenerator service — Milestone 3.

Uses the Google GenAI SDK (google-genai) with the gemini-3.1-flash-image model
(Nano Banana 2) to generate 9:16 vertical images from visual prompts produced
by the ContentPlanner.

Architecture notes
------------------
* This module is the ONLY place in the codebase that imports from google.genai.
  All other modules receive file paths or raise ImageGenerationError.
* The Gemini client is initialised lazily on first use so config errors are
  surfaced at call time, not at import time.
* Temporary assets are written to temp_assets/{job_id}_scene_{scene_id}.png
  relative to the backend root.  The caller is responsible for clean-up.

Downstream pipeline
-------------------
  scene.visual_prompt  →  ImageGenerator.generate_scene_image()
                       →  PNG file path
                       →  Milestone 5: FFmpeg compositor reads the file
"""

import logging
import os
from pathlib import Path

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

# Resolved once at module load so tests can patch it easily.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
TEMP_ASSETS_DIR = _BACKEND_ROOT / "temp_assets"

IMAGE_MODEL = "gemini-3.1-flash-image"
ASPECT_RATIO = "9:16"
IMAGE_SIZE = "2K"


# ---------------------------------------------------------------------------
# Custom exception — callers never need to import google.genai.errors
# ---------------------------------------------------------------------------

class ImageGenerationError(Exception):
    """Raised for any failure during image generation.  Never exposes secrets."""


# ---------------------------------------------------------------------------
# Gemini client singleton
# ---------------------------------------------------------------------------

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = settings.gemini_api_key
        if not api_key:
            raise ImageGenerationError(
                "GEMINI_API_KEY is not configured. "
                "Set it in your .env file or as an environment variable."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ---------------------------------------------------------------------------
# ImageGenerator
# ---------------------------------------------------------------------------

class ImageGenerator:
    """Generates individual scene images and persists them as PNG files."""

    def generate_scene_image(self, job_id: str, scene_id: int, prompt: str) -> str:
        """
        Generate a 9:16 vertical image from `prompt` and save it locally.

        Parameters
        ----------
        job_id   : Unique job identifier (used to namespace the file name).
        scene_id : Scene number within the job.
        prompt   : Rich visual-generation prompt from ContentPlan.scenes[n].visual_prompt.

        Returns
        -------
        str — Absolute path to the saved PNG file.

        Raises
        ------
        ImageGenerationError — on any provider, network, or I/O failure.
        """
        if not prompt or not prompt.strip():
            raise ImageGenerationError("visual_prompt must not be empty.")

        client = _get_client()

        logger.info(
            "Generating scene image: job=%s scene=%d model=%s aspect=%s",
            job_id, scene_id, IMAGE_MODEL, ASPECT_RATIO,
        )

        try:
            response = client.models.generate_content(
                model=IMAGE_MODEL,
                contents=[prompt],
                config=types.GenerateContentConfig(
                    image_config=types.ImageConfig(
                        aspect_ratio=ASPECT_RATIO,
                        image_size=IMAGE_SIZE,
                    )
                ),
            )
        except Exception as exc:
            # Never include the exception repr directly as it may contain headers.
            raise ImageGenerationError(
                f"Gemini image generation failed for scene {scene_id}: {type(exc).__name__}: {exc}"
            ) from exc

        # Extract the first image part from the response.
        image_part = None
        for part in response.parts:
            if part.inline_data is not None:
                image_part = part
                break

        if image_part is None:
            raise ImageGenerationError(
                f"Gemini returned no image data for scene {scene_id}. "
                "The model may have refused the prompt."
            )

        # Ensure output directory exists.
        TEMP_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

        output_path = TEMP_ASSETS_DIR / f"{job_id}_scene_{scene_id}.png"

        try:
            pil_image = image_part.as_image()
            pil_image.save(str(output_path))
        except Exception as exc:
            raise ImageGenerationError(
                f"Failed to save image for scene {scene_id}: {type(exc).__name__}"
            ) from exc

        logger.info("Scene image saved: %s", output_path)
        return str(output_path.resolve())


# Module-level singleton — mirrors the pattern used in job_store.py and groq_client.py.
image_generator = ImageGenerator()
