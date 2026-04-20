from app.schemas.chat import ChatCompletionRequest


class RedactionResult:
    def __init__(self, sanitized_payload: ChatCompletionRequest, redactions_applied: int, risk_score: float):
        self.sanitized_payload = sanitized_payload
        self.redactions_applied = redactions_applied
        self.risk_score = risk_score


class RedactionService:
    async def sanitize(self, payload: ChatCompletionRequest) -> RedactionResult:
        return RedactionResult(
            sanitized_payload=payload,
            redactions_applied=0,
            risk_score=0.0,
        )