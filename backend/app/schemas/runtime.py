from typing import Literal

from pydantic import BaseModel, Field


class PerceptionResult(BaseModel):
    intent: str
    entities: dict[str, object] = Field(default_factory=dict)
    references: list[dict[str, object]] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    sentiment: str = "neutral"
    confidence: float = Field(ge=0, le=1)


class DialogueAction(BaseModel):
    action: Literal[
        "answer_directly",
        "ask_clarification",
        "ask_requirement",
        "search_product",
        "search_similar_product",
        "get_product_information",
        "get_price_information",
        "search_knowledge",
        "recommend_product",
        "request_human_handoff",
        "finish",
    ]
    field: str | None = None
    reason_code: str | None = None

