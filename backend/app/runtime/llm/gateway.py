import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import httpx

from app.config.settings import Settings, get_settings


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


@dataclass
class StreamEvent:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMGateway:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    @property
    def configured(self) -> bool:
        return bool(self.settings.llm_base_url and self.settings.llm_api_key and self.settings.llm_model)

    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        if not self.configured:
            return await DeterministicGateway().complete(messages, tools)
        payload = self._payload(messages, tools, stream=False)
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(self._url(), headers=self._headers(), json=payload)
            response.raise_for_status()
        return self._parse_response(response.json())

    async def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[StreamEvent]:
        if not self.configured:
            async for event in DeterministicGateway().stream(messages, tools):
                yield event
            return
        payload = self._payload(messages, tools, stream=True)
        tool_buffers: dict[int, dict[str, Any]] = {}
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", self._url(), headers=self._headers(), json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[5:].strip()
                    if raw == "[DONE]":
                        break
                    event = json.loads(raw)
                    delta = event.get("choices", [{}])[0].get("delta", {})
                    if delta.get("content"):
                        yield StreamEvent(text=delta["content"])
                    for item in delta.get("tool_calls", []):
                        index = item.get("index", 0)
                        buffer = tool_buffers.setdefault(index, {"id": "", "name": "", "arguments": ""})
                        buffer["id"] += item.get("id", "")
                        function = item.get("function", {})
                        buffer["name"] += function.get("name", "")
                        buffer["arguments"] += function.get("arguments", "")
        calls = [ToolCall(id=item["id"] or f"call_{index}", name=item["name"], arguments=json.loads(item["arguments"] or "{}")) for index, item in tool_buffers.items()]
        if calls:
            yield StreamEvent(tool_calls=calls)

    def _url(self) -> str:
        return f"{self.settings.llm_base_url.rstrip('/')}/chat/completions"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.llm_api_key}", "Content-Type": "application/json"}

    def _payload(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], stream: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {"model": self.settings.llm_model, "messages": messages, "temperature": self.settings.llm_temperature, "stream": stream}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        return payload

    @staticmethod
    def _parse_response(payload: dict[str, Any]) -> LLMResponse:
        message = payload["choices"][0]["message"]
        calls = [ToolCall(id=item["id"], name=item["function"]["name"], arguments=LLMGateway._parse_arguments(item["function"].get("arguments", "{}"))) for item in message.get("tool_calls", [])]
        return LLMResponse(content=message.get("content") or "", tool_calls=calls)

    @staticmethod
    def _parse_arguments(raw: str) -> dict[str, Any]:
        try:
            parsed = json.loads(raw or "{}")
        except json.JSONDecodeError:
            return {"_invalid_json": raw}
        return parsed if isinstance(parsed, dict) else {"_invalid_arguments": parsed}


class DeterministicGateway(LLMGateway):
    """Local-only fallback; production uses LLMGateway when credentials are configured."""

    def __init__(self) -> None:
        pass

    async def complete(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> LLMResponse:
        user = next((item["content"].lower() for item in reversed(messages) if item["role"] == "user"), "")
        tool_names = {tool["function"]["name"] for tool in tools}
        if "ring" in user and "search_products" in tool_names and any(word in user for word in ("need", "want", "looking")):
            return LLMResponse(tool_calls=[ToolCall("fallback_search", "search_products", {"category": "ring"})])
        if any(word in user for word in ("human", "sales", "人工")):
            return LLMResponse(content="I’ll connect you with a human sales colleague.")
        return LLMResponse(content="Thanks for reaching out. Could you share the product or SKU you’re asking about?")

    async def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[StreamEvent]:
        response = await self.complete(messages, tools)
        if response.tool_calls:
            yield StreamEvent(tool_calls=response.tool_calls)
            return
        for word in response.content.split(" "):
            yield StreamEvent(text=word + " ")
