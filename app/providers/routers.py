from app.core.config import settings
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_compatible import OpenAICompatibleProvider


def get_provider():
    if settings.PROVIDER_NAME == "ollama":
        return OllamaProvider()

    if settings.PROVIDER_NAME == "openai_compatible":
        return OpenAICompatibleProvider()

    raise ValueError(f"Unsupported provider: {settings.PROVIDER_NAME}")