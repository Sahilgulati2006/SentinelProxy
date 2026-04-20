from pydantic import BaseModel


class RedactionItem(BaseModel):
    entity_type: str
    placeholder: str
    original_value: str


class RedactionSummary(BaseModel):
    redactions_applied: int
    entity_counts: dict[str, int]
    items: list[RedactionItem]