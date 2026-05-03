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

    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    DATABASE_URL: str = "sqlite+aiosqlite:///./sentinelproxy.db"

    BOOTSTRAP_ADMIN_EMAIL: str = "admin@example.com"
    BOOTSTRAP_MONTHLY_TOKEN_LIMIT: int = 100000

    API_KEY_PEPPER: str = "change_this_in_env"
    SENTINEL_ADMIN_KEY: str

    REQUEST_TIMEOUT_SECONDS: int = 120
    MAX_REQUEST_CHARS: int = 20000

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.CORS_ALLOWED_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()