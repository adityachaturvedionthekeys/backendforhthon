"""
Unit tests for ImageGenerator.

ALL tests are fully mocked — no GEMINI_API_KEY required, no network calls made.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image as PILImage


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pil_image(width: int = 10, height: int = 18) -> PILImage.Image:
    """Return a tiny valid PIL image (not real Gemini output)."""
    return PILImage.new("RGB", (width, height), color=(42, 42, 42))


def _make_mock_part_with_image(pil_img=None) -> MagicMock:
    """Simulate a response Part that contains inline image data."""
    part = MagicMock()
    part.text = None
    part.inline_data = MagicMock()
    part.as_image.return_value = pil_img or _make_pil_image()
    return part


def _make_mock_part_text(text: str = "Some text") -> MagicMock:
    """Simulate a response Part that contains only text (no image)."""
    part = MagicMock()
    part.text = text
    part.inline_data = None
    return part


def _make_mock_response(parts) -> MagicMock:
    """Simulate a GenerateContentResponse with a list of parts."""
    response = MagicMock()
    response.parts = parts
    return response


# ---------------------------------------------------------------------------
# Fixture: patches the genai.Client inside the image_generator module,
# settings, and TEMP_ASSETS_DIR so every test is fully isolated.
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_module_client():
    """Reset the module-level _client singleton before/after each test."""
    import app.services.image_generator as ig_module
    original = ig_module._client
    ig_module._client = None
    yield
    ig_module._client = original


@pytest.fixture()
def mock_genai(tmp_path):
    """
    Patch:
      - app.services.image_generator.genai.Client  (the actual import used)
      - app.services.image_generator.settings       (so no .env is needed)
      - app.services.image_generator.TEMP_ASSETS_DIR (redirect writes to tmp_path)
    """
    with patch("app.services.image_generator.genai") as mock_genai_module, \
         patch("app.services.image_generator.settings") as mock_settings, \
         patch("app.services.image_generator.TEMP_ASSETS_DIR", tmp_path):

        mock_settings.gemini_api_key = "fake-key-for-testing"

        mock_client_instance = MagicMock()
        mock_genai_module.Client.return_value = mock_client_instance

        yield mock_client_instance, tmp_path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerateSceneImage:

    def test_returns_path_string_on_success(self, mock_genai):
        """Happy path: Gemini returns an image part → file saved → path returned."""
        mock_client, tmp_path = mock_genai
        mock_client.models.generate_content.return_value = _make_mock_response(
            [_make_mock_part_with_image()]
        )

        from app.services.image_generator import ImageGenerator
        ig = ImageGenerator()
        path = ig.generate_scene_image("job-001", 1, "A sunny solar farm at dawn")

        assert isinstance(path, str)
        assert path.endswith(".png")
        assert "job-001" in path
        assert "scene_1" in path

    def test_saved_file_exists(self, mock_genai):
        """The returned path must point to a file that actually exists on disk."""
        mock_client, tmp_path = mock_genai
        pil_img = _make_pil_image()
        mock_client.models.generate_content.return_value = _make_mock_response(
            [_make_mock_part_with_image(pil_img)]
        )

        from app.services.image_generator import ImageGenerator
        ig = ImageGenerator()
        path = ig.generate_scene_image("job-002", 3, "A futuristic city skyline at dusk")

        assert Path(path).exists(), f"Expected file at {path}"

    def test_filename_format(self, mock_genai):
        """File must be named {job_id}_scene_{scene_id}.png."""
        mock_client, tmp_path = mock_genai
        mock_client.models.generate_content.return_value = _make_mock_response(
            [_make_mock_part_with_image()]
        )

        from app.services.image_generator import ImageGenerator
        ig = ImageGenerator()
        path = ig.generate_scene_image("abc-xyz-123", 7, "Underwater coral reef, teal water")

        assert Path(path).name == "abc-xyz-123_scene_7.png"

    def test_raises_when_api_key_missing(self, tmp_path):
        """Missing GEMINI_API_KEY must raise ImageGenerationError with a clear message."""
        with patch("app.services.image_generator.settings") as mock_settings, \
             patch("app.services.image_generator.TEMP_ASSETS_DIR", tmp_path):
            mock_settings.gemini_api_key = ""

            from app.services.image_generator import ImageGenerator, ImageGenerationError
            ig = ImageGenerator()
            with pytest.raises(ImageGenerationError, match="GEMINI_API_KEY"):
                ig.generate_scene_image("job-003", 1, "Mountain landscape at sunset")

    def test_raises_when_no_image_in_response(self, mock_genai):
        """If Gemini returns only text parts (prompt refused), raise ImageGenerationError."""
        mock_client, tmp_path = mock_genai
        mock_client.models.generate_content.return_value = _make_mock_response(
            [_make_mock_part_text("I cannot generate that image.")]
        )

        from app.services.image_generator import ImageGenerator, ImageGenerationError
        ig = ImageGenerator()
        with pytest.raises(ImageGenerationError, match="no image data"):
            ig.generate_scene_image("job-004", 2, "Some refused prompt")

    def test_raises_on_sdk_network_error(self, mock_genai):
        """SDK network exceptions must be wrapped in ImageGenerationError."""
        mock_client, tmp_path = mock_genai
        mock_client.models.generate_content.side_effect = ConnectionError("Network unreachable")

        from app.services.image_generator import ImageGenerator, ImageGenerationError
        ig = ImageGenerator()
        with pytest.raises(ImageGenerationError, match="Network unreachable"):
            ig.generate_scene_image("job-005", 1, "Clear blue sky with clouds")

    def test_raises_on_empty_prompt(self, mock_genai):
        """An empty visual prompt must raise ImageGenerationError before calling the API."""
        mock_client, tmp_path = mock_genai

        from app.services.image_generator import ImageGenerator, ImageGenerationError
        ig = ImageGenerator()
        with pytest.raises(ImageGenerationError, match="must not be empty"):
            ig.generate_scene_image("job-006", 1, "   ")

        # Ensure we never even called the API
        mock_client.models.generate_content.assert_not_called()

    def test_different_scenes_produce_different_paths(self, mock_genai):
        """Each scene_id should produce a unique file name."""
        mock_client, tmp_path = mock_genai
        mock_client.models.generate_content.return_value = _make_mock_response(
            [_make_mock_part_with_image()]
        )

        from app.services.image_generator import ImageGenerator
        ig = ImageGenerator()
        path1 = ig.generate_scene_image("job-007", 1, "Dense forest canopy at midday")
        path2 = ig.generate_scene_image("job-007", 2, "Open grassland plains at dusk")

        assert path1 != path2
        assert "scene_1" in path1
        assert "scene_2" in path2
