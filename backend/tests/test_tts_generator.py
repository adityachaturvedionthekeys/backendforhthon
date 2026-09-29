"""
Unit tests for TTSGenerator.

ALL tests are fully mocked — no network calls, no API key required.
edge_tts.Communicate is patched so no Microsoft TTS servers are contacted.
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixture: redirect TEMP_ASSETS_DIR to a pytest tmp_path and mock Communicate
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_tts(tmp_path):
    """
    Patch:
      - app.services.tts_generator.edge_tts.Communicate  (the import used by the service)
      - app.services.tts_generator.TEMP_ASSETS_DIR        (redirect writes to tmp_path)

    The mocked Communicate.save() is an AsyncMock that writes a tiny MP3-like
    placeholder so Path(path).exists() assertions pass.
    """
    async def _fake_save(output_path: str):
        Path(output_path).write_bytes(b"ID3FAKEMP3DATA")

    mock_communicate_instance = MagicMock()
    mock_communicate_instance.save = _fake_save

    with patch("app.services.tts_generator.edge_tts") as mock_edge_tts, \
         patch("app.services.tts_generator.TEMP_ASSETS_DIR", tmp_path):
        mock_edge_tts.Communicate.return_value = mock_communicate_instance
        yield mock_edge_tts, tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateSceneAudio:

    @pytest.mark.asyncio
    async def test_returns_path_string_on_success(self, mock_tts):
        """Happy path: edge_tts saves a file → absolute path string returned."""
        from app.services.tts_generator import TTSGenerator
        tts = TTSGenerator()
        path = await tts.generate_scene_audio(
            "job-001", 1, "The sun delivers more energy in one hour than humanity uses in a year."
        )
        assert isinstance(path, str)
        assert path.endswith(".mp3")
        assert "job-001" in path
        assert "scene_1" in path

    @pytest.mark.asyncio
    async def test_saved_file_exists(self, mock_tts):
        """The returned path must point to a file that actually exists on disk."""
        from app.services.tts_generator import TTSGenerator
        tts = TTSGenerator()
        path = await tts.generate_scene_audio(
            "job-002", 3, "Solar panel costs have fallen over 90% in the last decade."
        )
        assert Path(path).exists(), f"Expected MP3 at {path}"

    @pytest.mark.asyncio
    async def test_filename_format(self, mock_tts):
        """File must be named {job_id}_scene_{scene_id}.mp3."""
        from app.services.tts_generator import TTSGenerator
        tts = TTSGenerator()
        path = await tts.generate_scene_audio(
            "abc-xyz-99", 5, "Countries now generate over 50% from renewables."
        )
        assert Path(path).name == "abc-xyz-99_scene_5.mp3"

    @pytest.mark.asyncio
    async def test_raises_on_empty_text(self, mock_tts):
        """Whitespace-only text must raise TTSGenerationError before calling the SDK."""
        mock_edge_tts, tmp_path = mock_tts
        from app.services.tts_generator import TTSGenerator, TTSGenerationError
        tts = TTSGenerator()

        with pytest.raises(TTSGenerationError, match="must not be empty"):
            await tts.generate_scene_audio("job-003", 1, "   ")

        # Communicate must never be instantiated for empty text
        mock_edge_tts.Communicate.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_on_blank_string(self, mock_tts):
        """Truly empty string must also raise TTSGenerationError."""
        mock_edge_tts, tmp_path = mock_tts
        from app.services.tts_generator import TTSGenerator, TTSGenerationError
        tts = TTSGenerator()

        with pytest.raises(TTSGenerationError, match="must not be empty"):
            await tts.generate_scene_audio("job-004", 2, "")

    @pytest.mark.asyncio
    async def test_raises_on_sdk_network_error(self, mock_tts):
        """Network/SDK exceptions must be wrapped as TTSGenerationError."""
        mock_edge_tts, tmp_path = mock_tts

        async def _broken_save(output_path: str):
            raise ConnectionError("TTS server unreachable")

        mock_edge_tts.Communicate.return_value.save = _broken_save

        from app.services.tts_generator import TTSGenerator, TTSGenerationError
        tts = TTSGenerator()

        with pytest.raises(TTSGenerationError, match="TTS server unreachable"):
            await tts.generate_scene_audio("job-005", 1, "A valid narration sentence.")

    @pytest.mark.asyncio
    async def test_communicate_receives_correct_voice(self, mock_tts):
        """The voice parameter must be forwarded to edge_tts.Communicate."""
        mock_edge_tts, tmp_path = mock_tts
        from app.services.tts_generator import TTSGenerator
        tts = TTSGenerator()

        custom_voice = "en-GB-RyanNeural"
        await tts.generate_scene_audio("job-006", 1, "Test narration text.", voice=custom_voice)

        mock_edge_tts.Communicate.assert_called_once_with(
            "Test narration text.", custom_voice
        )

    @pytest.mark.asyncio
    async def test_different_scenes_produce_different_paths(self, mock_tts):
        """Each scene_id must produce a unique file name."""
        from app.services.tts_generator import TTSGenerator
        tts = TTSGenerator()

        path1 = await tts.generate_scene_audio("job-007", 1, "First scene narration.")
        path2 = await tts.generate_scene_audio("job-007", 2, "Second scene narration.")

        assert path1 != path2
        assert "scene_1" in path1
        assert "scene_2" in path2

    @pytest.mark.asyncio
    async def test_default_voice_is_christopher(self, mock_tts):
        """Default voice must be en-US-ChristopherNeural."""
        mock_edge_tts, tmp_path = mock_tts
        from app.services.tts_generator import TTSGenerator, DEFAULT_VOICE
        tts = TTSGenerator()

        await tts.generate_scene_audio("job-008", 1, "Default voice test narration.")

        mock_edge_tts.Communicate.assert_called_once_with(
            "Default voice test narration.", DEFAULT_VOICE
        )
        assert DEFAULT_VOICE == "en-US-ChristopherNeural"
