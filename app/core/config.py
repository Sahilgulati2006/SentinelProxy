from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SentinelProxy"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    PROVIDER_NAME: str = "ollama"
    DEFAULT_MODEL: str = "llama3.1:8b"

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    OPENAI_COMPATIBLE_BASE_URL: str | None = None
    OPENAI_COMPATIBLE_API_KEY: str | None = None

    REQUEST_TIMEOUT_SECONDS: int = 120
    MAX_REQUEST_CHARS: int = 20000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()