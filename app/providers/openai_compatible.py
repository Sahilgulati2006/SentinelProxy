import httpx
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.base import BaseProvider
from app.schemas.chat import ChatCompletionRequest


class OpenAICompatibleProvider(BaseProvider):
    async def create_chat_completion(self, payload: ChatCompletionRequest) -> dict:
        if not settings.OPENAI_COMPATIBLE_BASE_URL or not settings.OPENAI_COMPATIBLE_API_KEY:
            raise ProviderError("OpenAI-compatible provider is not configured.")

        url = f"{settings.OPENAI_COMPATIBLE_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_COMPATIBLE_API_KEY}",
            "Content-Type": "application/json",
        }

        body = payload.model_dump()
        if not body.get("model"):
            body["model"] = settings.DEFAULT_MODEL

        timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, headers=headers, json=body)

        if response.status_code >= 400:
            raise ProviderError(
                f"OpenAI-compatible provider error {response.status_code}: {response.text}"
            )

        data = response.json()
        data["provider_raw"] = data.copy()
        return data