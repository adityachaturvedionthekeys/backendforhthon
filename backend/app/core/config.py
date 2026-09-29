from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8"
    }

settings = Settings()
