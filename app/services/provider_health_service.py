import httpx

from app.core.config import settings
from app.core.exceptions import ProviderError


class ProviderHealthService:
    async def check(self) -> dict:
        if settings.PROVIDER_NAME == "ollama":
            return await self._check_ollama()

        if settings.PROVIDER_NAME == "openai_compatible":
            return await self._check_openai_compatible()

        raise ProviderError(f"Unsupported provider: {settings.PROVIDER_NAME}")

    async def _check_ollama(self) -> dict:
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"

        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)

            if response.status_code >= 400:
                return {
                    "status": "error",
                    "provider": "ollama",
                    "detail": f"Ollama returned {response.status_code}",
                }

            return {
                "status": "ok",
                "provider": "ollama",
            }

        except Exception as exc:
            return {
                "status": "error",
                "provider": "ollama",
                "detail": str(exc),
            }

    async def _check_openai_compatible(self) -> dict:
        if not settings.OPENAI_COMPATIBLE_BASE_URL:
            return {
                "status": "error",
                "provider": "openai_compatible",
                "detail": "OPENAI_COMPATIBLE_BASE_URL is not configured.",
            }

        return {
            "status": "ok",
            "provider": "openai_compatible",
            "detail": "Configuration present. Deep provider health check not implemented yet.",
        }