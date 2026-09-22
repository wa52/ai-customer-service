from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    id: str
    role: Literal["customer", "assistant", "system"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    action: str | None = None
    intent: str | None = None


class SessionResponse(BaseModel):
    id: str
    status: Literal["active", "human_required", "closed"]
    language: str
    summary: str
    requirements: dict[str, object]
    candidate_products: list[str]
    selected_product: str | None
    missing_information: list[str]
    messages: list[MessageResponse]


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    message: MessageResponse
    session: SessionResponse | None

