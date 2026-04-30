import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import (
    MappingStoreError,
    ProviderError,
    RateLimitExceededError,
)
from app.schemas.auth import AuthenticatedUser
from app.schemas.chat import (
    AssistantMessage,
    ChatChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    SentinelMetadata,
    Usage,
)
from app.services.audit_service import AuditService
from app.services.budget_service import BudgetExceededError, BudgetService
from app.services.mapping_store_service import MappingStoreService
from app.services.provider_service import ProviderService
from app.services.rate_limit_service import RateLimitService
from app.services.redaction_service import RedactionService
from app.services.reidentification_service import ReidentificationService

router = APIRouter()

provider_service = ProviderService()
redaction_service = RedactionService()
reidentification_service = ReidentificationService()
mapping_store_service = MappingStoreService()
audit_service = AuditService()
budget_service = BudgetService()
rate_limit_service = RateLimitService()


@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    payload: ChatCompletionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    request_id = f"req_{uuid.uuid4().hex[:12]}"
    started_at = time.time()

    total_chars = sum(len(msg.content) for msg in payload.messages)
    if total_chars > settings.MAX_REQUEST_CHARS:
        raise HTTPException(
            status_code=400,
            detail="Request exceeds max allowed size.",
        )

    if payload.stream:
        raise HTTPException(
            status_code=400,
            detail="Streaming not supported yet.",
        )

    try:
        # 1. Check short-term API key rate limit before provider work
        rate_limit_info = await rate_limit_service.check_rate_limit(
            current_user.api_key_prefix
        )

        # 2. Check monthly user token budget before provider work
        budget_before = await budget_service.check_budget(
            user_id=current_user.user_id,
            monthly_token_limit=current_user.monthly_token_limit,
        )

        # 3. Redact sensitive data locally before sending anything to the model
        redaction_result = await redaction_service.sanitize(payload)

        # 4. Store request-scoped mappings in Redis before provider call
        await mapping_store_service.store_mapping(
            request_id=request_id,
            mappings=redaction_result.mappings,
            entity_counts=redaction_result.entity_counts,
        )

        # 5. Send only sanitized payload to the selected provider
        provider_response = await provider_service.forward(
            redaction_result.sanitized_payload
        )

        choice0 = provider_response.get("choices", [{}])[0]
        message = choice0.get("message", {})
        usage_data = provider_response.get("usage", {})
        model_content = message.get("content", "")

        total_tokens = usage_data.get("total_tokens", 0)

        # 6. Increment user usage after successful provider response
        budget_after = await budget_service.increment_usage(
            user_id=current_user.user_id,
            monthly_token_limit=current_user.monthly_token_limit,
            tokens=total_tokens,
        )

        # 7. Fetch mappings back from Redis for re-identification
        stored_mappings = await mapping_store_service.get_mapping(request_id)

        # 8. Restore placeholders in model output using Redis-backed mappings
        reidentification_result = reidentification_service.restore(
            text=model_content,
            mappings=stored_mappings,
        )

        latency_ms = int((time.time() - started_at) * 1000)

        # 9. PII-safe audit log. Do not log raw prompt, raw response, or mappings.
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "model": provider_response.get(
                    "model",
                    payload.model or settings.DEFAULT_MODEL,
                ),
                "status": "success",
                "latency_ms": latency_ms,
                "redactions_applied": redaction_result.redactions_applied,
                "risk_score": redaction_result.risk_score,
                "entity_counts": redaction_result.entity_counts,
                "reidentification_applied": (
                    reidentification_result.reidentification_applied
                ),
                "unreplaced_placeholders": (
                    reidentification_result.unreplaced_placeholders
                ),
                "repaired_placeholders": (
                    reidentification_result.repaired_placeholders
                ),
                "usage": {
                    "prompt_tokens": usage_data.get("prompt_tokens", 0),
                    "completion_tokens": usage_data.get("completion_tokens", 0),
                    "total_tokens": total_tokens,
                },
                "budget_before": budget_before,
                "budget_after": budget_after,
                "rate_limit": rate_limit_info,
            }
        )

        return ChatCompletionResponse(
            id=provider_response.get("id", f"chatcmpl_{uuid.uuid4().hex[:12]}"),
            created=provider_response.get("created", int(time.time())),
            model=provider_response.get(
                "model",
                payload.model or settings.DEFAULT_MODEL,
            ),
            choices=[
                ChatChoice(
                    index=choice0.get("index", 0),
                    message=AssistantMessage(
                        content=reidentification_result.restored_text
                    ),
                    finish_reason=choice0.get("finish_reason", "stop"),
                )
            ],
            usage=Usage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=total_tokens,
            ),
            sentinel=SentinelMetadata(
                request_id=request_id,
                user_id=current_user.user_id,
                api_key_prefix=current_user.api_key_prefix,
                redactions_applied=redaction_result.redactions_applied,
                risk_score=redaction_result.risk_score,
                provider_used=provider_service.provider_name,
                entity_counts=redaction_result.entity_counts,
                reidentification_applied=(
                    reidentification_result.reidentification_applied
                ),
                unreplaced_placeholders=(
                    reidentification_result.unreplaced_placeholders
                ),
                repaired_placeholders=(
                    reidentification_result.repaired_placeholders
                ),
                mapping_store="redis",
                budget=budget_after,
                rate_limit=rate_limit_info,
            ),
            raw_provider_response=(
                provider_response.get("provider_raw")
                if settings.APP_DEBUG
                else None
            ),
        )

    except RateLimitExceededError as exc:
        latency_ms = int((time.time() - started_at) * 1000)
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "status": "rate_limit_exceeded",
                "latency_ms": latency_ms,
                "error_type": "RateLimitExceededError",
                "error_message": str(exc),
            }
        )
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc

    except BudgetExceededError as exc:
        latency_ms = int((time.time() - started_at) * 1000)
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "status": "budget_exceeded",
                "latency_ms": latency_ms,
                "error_type": "BudgetExceededError",
                "error_message": str(exc),
            }
        )
        raise HTTPException(
            status_code=429,
            detail=str(exc),
        ) from exc

    except ProviderError as exc:
        latency_ms = int((time.time() - started_at) * 1000)
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "status": "provider_error",
                "latency_ms": latency_ms,
                "error_type": "ProviderError",
                "error_message": str(exc),
            }
        )
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    except MappingStoreError as exc:
        latency_ms = int((time.time() - started_at) * 1000)
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "status": "mapping_store_error",
                "latency_ms": latency_ms,
                "error_type": "MappingStoreError",
                "error_message": str(exc),
            }
        )
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        latency_ms = int((time.time() - started_at) * 1000)
        await audit_service.record(
            {
                "request_id": request_id,
                "user_id": current_user.user_id,
                "api_key_prefix": current_user.api_key_prefix,
                "provider_used": provider_service.provider_name,
                "status": "internal_error",
                "latency_ms": latency_ms,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            }
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(exc)}",
        ) from exc