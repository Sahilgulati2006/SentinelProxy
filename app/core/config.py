from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "SentinelProxy"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    PROVIDER_NAME: str = "ollama"
    DEFAULT_MODEL: str = "qwen2.5:3b"

    OLLAMA_BASE_URL: str = "http://localhost:11434"

    OPENAI_COMPATIBLE_BASE_URL: str | None = None
    OPENAI_COMPATIBLE_API_KEY: str | None = None

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_TTL_SECONDS: int = 1800

    REQUEST_TIMEOUT_SECONDS: int = 120
    MAX_REQUEST_CHARS: int = 20000
    SENTINEL_API_KEY: str = "sp_dev_key_123"


settings = Settings()