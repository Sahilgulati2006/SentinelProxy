import copy
import re
from collections import defaultdict
from dataclasses import dataclass

from app.schemas.chat import ChatCompletionRequest, ChatMessage


@dataclass
class RedactionMatch:
    entity_type: str
    original_value: str
    placeholder: str


class RedactionResult:
    def __init__(
        self,
        sanitized_payload: ChatCompletionRequest,
        redactions_applied: int,
        risk_score: float,
        entity_counts: dict[str, int],
        mappings: dict[str, str],
        items: list[RedactionMatch],
    ):
        self.sanitized_payload = sanitized_payload
        self.redactions_applied = redactions_applied
        self.risk_score = risk_score
        self.entity_counts = entity_counts
        self.mappings = mappings
        self.items = items


class RedactionService:
    PATTERNS = {
        "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "PHONE": re.compile(r"(?<!\w)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\w)"),
        "SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
        "IP_ADDRESS": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
        "API_KEY": re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z\-_]{20,})\b"),
    }

    RISK_WEIGHTS = {
        "EMAIL": 0.10,
        "PHONE": 0.10,
        "SSN": 0.40,
        "CREDIT_CARD": 0.45,
        "IP_ADDRESS": 0.08,
        "API_KEY": 0.50,
    }

    async def sanitize(self, payload: ChatCompletionRequest) -> RedactionResult:
        sanitized_payload = copy.deepcopy(payload)

        counters = defaultdict(int)
        entity_counts = defaultdict(int)
        mappings: dict[str, str] = {}
        items: list[RedactionMatch] = []

        sanitized_messages: list[ChatMessage] = []

        for message in sanitized_payload.messages:
            sanitized_text = message.content

            for entity_type, pattern in self.PATTERNS.items():
                sanitized_text = self._replace_pattern(
                    text=sanitized_text,
                    entity_type=entity_type,
                    pattern=pattern,
                    counters=counters,
                    entity_counts=entity_counts,
                    mappings=mappings,
                    items=items,
                )

            sanitized_messages.append(
                ChatMessage(role=message.role, content=sanitized_text)
            )

        sanitized_payload.messages = sanitized_messages

        redactions_applied = sum(entity_counts.values())

        if redactions_applied > 0:
            instruction = ChatMessage(
                role="system",
                content=(
                    "Protected markers like <<SP_EMAIL_1>>, <<SP_PHONE_1>>, <<SP_SSN_1>>, "
                    "<<SP_CREDIT_CARD_1>>, <<SP_IP_ADDRESS_1>>, and similar are confidential "
                    "placeholders inserted by the system. Treat them as opaque stand-ins for "
                    "private values. Do not explain the placeholder names, do not guess the "
                    "original values, and do not give instructions about replacing placeholders. "
                    "Just complete the user's task naturally using the placeholders as references "
                    "to hidden private data."
                ),
            )
            sanitized_payload.messages = [instruction] + sanitized_payload.messages
            
        risk_score = self._calculate_risk_score(entity_counts)

        return RedactionResult(
            sanitized_payload=sanitized_payload,
            redactions_applied=redactions_applied,
            risk_score=risk_score,
            entity_counts=dict(entity_counts),
            mappings=mappings,
            items=items,
        )

    def _replace_pattern(
        self,
        text: str,
        entity_type: str,
        pattern: re.Pattern,
        counters: defaultdict,
        entity_counts: defaultdict,
        mappings: dict[str, str],
        items: list[RedactionMatch],
    ) -> str:
        seen_values: dict[str, str] = {}

        def replacer(match: re.Match) -> str:
            original = match.group(0)

            if original in seen_values:
                return seen_values[original]

            counters[entity_type] += 1
            entity_counts[entity_type] += 1
            placeholder = f"<<SP_{entity_type}_{counters[entity_type]}>>"

            mappings[placeholder] = original
            items.append(
                RedactionMatch(
                    entity_type=entity_type,
                    original_value=original,
                    placeholder=placeholder,
                )
            )
            seen_values[original] = placeholder
            return placeholder

        return pattern.sub(replacer, text)

    def _calculate_risk_score(self, entity_counts: dict[str, int]) -> float:
        score = 0.0
        for entity_type, count in entity_counts.items():
            score += self.RISK_WEIGHTS.get(entity_type, 0.05) * count

        return min(round(score, 3), 1.0)