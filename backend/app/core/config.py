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

    # Milestone 4 (not implemented yet): ElevenLabs — TTS voiceover
    # elevenlabs_api_key: str = ""
    # elevenlabs_voice_id: str = ""
    # elevenlabs_model_id: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


settings = Settings()
