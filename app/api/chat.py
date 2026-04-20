import time
import uuid
from fastapi import APIRouter, HTTPException
from app.core.config import settings
from app.core.exceptions import ProviderError
from app.schemas.chat import (
    AssistantMessage,
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    SentinelMetadata,
    Usage,
)
from app.services.provider_service import ProviderService
from app.services.redaction_service import RedactionService

router = APIRouter()
provider_service = ProviderService()
redaction_service = RedactionService()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(payload: ChatCompletionRequest):
    request_id = f"req_{uuid.uuid4().hex[:12]}"

    total_chars = sum(len(msg.content) for msg in payload.messages)
    if total_chars > settings.MAX_REQUEST_CHARS:
        raise HTTPException(status_code=400, detail="Request exceeds max allowed size.")

    if payload.stream:
        raise HTTPException(status_code=400, detail="Streaming not supported yet.")

    try:
        redaction_result = await redaction_service.sanitize(payload)
        provider_response = await provider_service.forward(redaction_result.sanitized_payload)

        choice0 = provider_response.get("choices", [{}])[0]
        message = choice0.get("message", {})
        usage_data = provider_response.get("usage", {})

        return ChatCompletionResponse(
            id=provider_response.get("id", f"chatcmpl_{uuid.uuid4().hex[:12]}"),
            created=provider_response.get("created", int(time.time())),
            model=provider_response.get("model", payload.model or settings.DEFAULT_MODEL),
            choices=[
                ChatChoice(
                    index=choice0.get("index", 0),
                    message=AssistantMessage(content=message.get("content", "")),
                    finish_reason=choice0.get("finish_reason", "stop"),
                )
            ],
            usage=Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
            sentinel=SentinelMetadata(
                request_id=request_id,
                redactions_applied=redaction_result.redactions_applied,
                risk_score=redaction_result.risk_score,
                provider_used=provider_service.provider_name,
                entity_counts=redaction_result.entity_counts,
            ),
            raw_provider_response=provider_response.get("provider_raw"),
        )

    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(exc)}") from exc