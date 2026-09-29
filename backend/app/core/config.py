from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Milestone 2: Groq — scripting / content planning
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # Milestone 3: Google AI Studio / Gemini — visual generation
    gemini_api_key: str = ""
    gemini_image_model: str = "gemini-3.1-flash-image"
    # gemini_video_model: str = ""  # reserved for Milestone 5 video generation

    # Milestone 4: ElevenLabs — TTS voiceover
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "pNInz6obpgDQGcFmaJgB"
    elevenlabs_model_id: str = "eleven_multilingual_v2"

    # Milestone 9: Cloud Storage (optional)
    s3_bucket_name: str | None = None
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str | None = None
    s3_endpoint_url: str | None = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
