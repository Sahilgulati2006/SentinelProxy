import time
import httpx
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.providers.base import BaseProvider
from app.schemas.chat import ChatCompletionRequest


class OllamaProvider(BaseProvider):
    async def create_chat_completion(self, payload: ChatCompletionRequest) -> dict:
        url = f"{settings.OLLAMA_BASE_URL}/api/chat"

        body = {
            "model": payload.model or settings.DEFAULT_MODEL,
            "messages": [msg.model_dump() for msg in payload.messages],
            "stream": False,
            "options": {},
        }

        if payload.temperature is not None:
            body["options"]["temperature"] = payload.temperature
        if payload.max_tokens is not None:
            body["options"]["num_predict"] = payload.max_tokens

        timeout = httpx.Timeout(settings.REQUEST_TIMEOUT_SECONDS)

        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(url, json=body)

        if response.status_code >= 400:
            raise ProviderError(
                f"Ollama provider error {response.status_code}: {response.text}"
            )

        data = response.json()

        content = data.get("message", {}).get("content", "")

        prompt_eval_count = data.get("prompt_eval_count", 0)
        eval_count = data.get("eval_count", 0)

        return {
            "id": f"ollama_{data.get('created_at', 'unknown')}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": data.get("model", payload.model or settings.DEFAULT_MODEL),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": content,
                    },
                    "finish_reason": "stop" if data.get("done", True) else "length",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_eval_count,
                "completion_tokens": eval_count,
                "total_tokens": prompt_eval_count + eval_count,
            },
            "provider_raw": data,
        }