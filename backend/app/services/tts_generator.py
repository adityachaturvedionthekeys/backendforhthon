"""
TTSGenerator service — Milestone 4.

Uses the `edge-tts` library to synthesise voiceover audio from scene narration
text without requiring an API key. Audio is written as MP3 to
temp_assets/{job_id}_scene_{scene_id}.mp3.

Architecture notes
------------------
* This is the ONLY module that imports edge_tts. All other modules receive
  file paths or raise TTSGenerationError.
* `generate_scene_audio` is an async method because edge_tts.Communicate.save()
  is a coroutine (it streams audio from Microsoft's servers).
* Designed to consume ContentPlan.scenes[n].narration directly.

Downstream pipeline
-------------------
  scene.narration  →  TTSGenerator.generate_scene_audio()
                   →  MP3 file path
                   →  Milestone 5: FFmpeg compositor mixes audio with video
                   →  Milestone 6: faster-whisper reads the same MP3 for captions
"""

import asyncio
import logging
from pathlib import Path

import edge_tts

from app.services.image_generator import TEMP_ASSETS_DIR  # reuse same output dir

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "en-US-ChristopherNeural"


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class TTSGenerationError(Exception):
    """Raised for any failure during TTS synthesis.  Never exposes credentials."""


# ---------------------------------------------------------------------------
# TTSGenerator
# ---------------------------------------------------------------------------

class TTSGenerator:
    """Converts scene narration text to MP3 audio using Microsoft Edge TTS."""

    async def generate_scene_audio(
        self,
        job_id: str,
        scene_id: int,
        text: str,
        voice: str = DEFAULT_VOICE,
    ) -> str:
        """
        Synthesise `text` to speech and save the result as an MP3.

        Parameters
        ----------
        job_id   : Unique job identifier (used to namespace the file name).
        scene_id : Scene number within the job.
        text     : Narration text from ContentPlan.scenes[n].narration.
        voice    : Edge TTS voice name (default: en-US-ChristopherNeural).

        Returns
        -------
        str — Absolute path to the saved MP3 file.

        Raises
        ------
        TTSGenerationError — on empty text, network failure, or I/O error.
        """
        if not text or not text.strip():
            raise TTSGenerationError(
                f"narration text for scene {scene_id} must not be empty."
            )

        logger.info(
            "Synthesising audio: job=%s scene=%d voice=%s chars=%d",
            job_id, scene_id, voice, len(text),
        )

        # Ensure output directory exists.
        TEMP_ASSETS_DIR.mkdir(parents=True, exist_ok=True)

        output_path = TEMP_ASSETS_DIR / f"{job_id}_scene_{scene_id}.mp3"

        try:
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(str(output_path))
        except TTSGenerationError:
            raise  # never swallow our own errors
        except Exception as exc:
            raise TTSGenerationError(
                f"Edge TTS failed for scene {scene_id}: {type(exc).__name__}: {exc}"
            ) from exc

        logger.info("Scene audio saved: %s", output_path)
        return str(output_path.resolve())


# Module-level singleton — mirrors the pattern used in job_store, groq_client, image_generator.
tts_generator = TTSGenerator()
