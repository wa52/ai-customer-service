import json
import os
from typing import Protocol

import httpx

from app.schemas.runtime import PerceptionResult


class StructuredPerceptionProvider(Protocol):
    def perceive(self, message: str, context: dict[str, object]) -> PerceptionResult: ...


class OpenAICompatiblePerceptionProvider:
    """Optional structured-output provider; activated only when endpoint and key are configured."""

    def __init__(self) -> None:
        self.endpoint = os.getenv("LLM_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.model = os.getenv("LLM_MODEL", "")

    def is_configured(self) -> bool:
        return bool(self.endpoint and self.api_key and self.model)

    def perceive(self, message: str, context: dict[str, object]) -> PerceptionResult:
        if not self.is_configured():
            raise RuntimeError("Structured LLM perception is not configured")
        schema = PerceptionResult.model_json_schema()
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Extract customer-service intent, product requirements, and references. Never answer the customer."},
                {"role": "user", "content": json.dumps({"message": message, "session_context": context}, ensure_ascii=False)},
            ],
            "response_format": {"type": "json_schema", "json_schema": {"name": "perception", "strict": True, "schema": schema}},
        }
        with httpx.Client(timeout=20) as client:
            response = client.post(f"{self.endpoint}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return PerceptionResult.model_validate_json(content)
