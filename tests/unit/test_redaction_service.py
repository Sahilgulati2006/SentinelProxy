import pytest

from app.schemas.chat import ChatCompletionRequest, ChatMessage
from app.services.redaction_service import RedactionService


@pytest.mark.asyncio
async def test_redacts_email_and_phone():
    service = RedactionService()

    payload = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="My email is sahil@example.com and my phone is 413-555-0199.",
            )
        ],
        temperature=0.2,
    )

    result = await service.sanitize(payload)

    sanitized_content = result.sanitized_payload.messages[-1].content

    assert "<<SP_EMAIL_1>>" in sanitized_content
    assert "<<SP_PHONE_1>>" in sanitized_content
    assert "sahil@example.com" not in sanitized_content
    assert "413-555-0199" not in sanitized_content

    assert result.redactions_applied == 2
    assert result.entity_counts["EMAIL"] == 1
    assert result.entity_counts["PHONE"] == 1
    assert result.mappings["<<SP_EMAIL_1>>"] == "sahil@example.com"
    assert result.mappings["<<SP_PHONE_1>>"] == "413-555-0199"


@pytest.mark.asyncio
async def test_redacts_ssn_and_credit_card():
    service = RedactionService()

    payload = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="SSN is 123-45-6789 and card is 4111 1111 1111 1111.",
            )
        ],
        temperature=0.2,
    )

    result = await service.sanitize(payload)

    sanitized_content = result.sanitized_payload.messages[-1].content

    assert "<<SP_SSN_1>>" in sanitized_content
    assert "<<SP_CREDIT_CARD_1>>" in sanitized_content
    assert "123-45-6789" not in sanitized_content
    assert "4111 1111 1111 1111" not in sanitized_content

    assert result.redactions_applied == 2
    assert result.entity_counts["SSN"] == 1
    assert result.entity_counts["CREDIT_CARD"] == 1


@pytest.mark.asyncio
async def test_repeated_same_email_uses_same_placeholder():
    service = RedactionService()

    payload = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Email sahil@example.com twice: sahil@example.com.",
            )
        ],
        temperature=0.2,
    )

    result = await service.sanitize(payload)

    sanitized_content = result.sanitized_payload.messages[-1].content

    assert sanitized_content.count("<<SP_EMAIL_1>>") == 2
    assert result.redactions_applied == 1
    assert result.entity_counts["EMAIL"] == 1


@pytest.mark.asyncio
async def test_no_pii_has_no_redactions():
    service = RedactionService()

    payload = ChatCompletionRequest(
        messages=[
            ChatMessage(
                role="user",
                content="Explain what an API gateway does.",
            )
        ],
        temperature=0.2,
    )

    result = await service.sanitize(payload)

    sanitized_content = result.sanitized_payload.messages[-1].content

    assert sanitized_content == "Explain what an API gateway does."
    assert result.redactions_applied == 0
    assert result.entity_counts == {}
    assert result.mappings == {}