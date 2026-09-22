from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.capabilities.executor import ActionExecutor
from app.config.settings import Settings
from app.customer_service.runtime import CustomerServiceRuntime
from app.main import app
from app.runtime.llm.gateway import LLMResponse, StreamEvent, ToolCall
from app.services.memory import memory_store
import app.api.chat as chat_api


class FakeGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[list[dict], list[dict]]] = []

    async def complete(self, messages: list[dict], tools: list[dict]) -> LLMResponse:
        self.calls.append((messages, tools))
        if len(self.calls) == 1:
            return LLMResponse(tool_calls=[ToolCall("call-1", "search_products", {"category": "ring"})])
        return LLMResponse(content="I found three ring options in our catalog.")

    async def stream(self, messages: list[dict], tools: list[dict]) -> AsyncIterator[StreamEvent]:
        yield StreamEvent(text="The ")
        yield StreamEvent(text="catalog ")
        yield StreamEvent(text="has ")
        yield StreamEvent(text="three options.")


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch: pytest.MonkeyPatch):
    fake = FakeGateway()
    runtime = CustomerServiceRuntime(fake, ActionExecutor(Settings(product_capability_enabled=True)))
    monkeypatch.setattr(chat_api, "customer_service_runtime", runtime)
    yield fake


client = TestClient(app)


def test_native_tool_calling_executes_product_tool(isolated_runtime: FakeGateway) -> None:
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages", json={"session_id": session["id"], "content": "I need rings"})
    assert response.status_code == 200
    assert response.json()["message"]["content"] == "I found three ring options in our catalog."
    assert response.json()["session"]["candidate_products"] == ["R1001", "R1002", "R1003"]
    assert "search_products" in {tool["function"]["name"] for tool in isolated_runtime.calls[0][1]}
    assert isolated_runtime.calls[1][0][-1]["role"] == "tool"


def test_tool_configuration_controls_registry() -> None:
    assert {tool["function"]["name"] for tool in ActionExecutor(Settings(product_capability_enabled=False)).definitions()} == {"request_human_handoff"}
    assert len(ActionExecutor(Settings(product_capability_enabled=True)).definitions()) == 3


def test_streaming_forwards_gateway_chunks() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages/stream", json={"session_id": session["id"], "content": "Hello"})
    assert response.status_code == 200
    assert response.text.count("event: token") == 4
    assert '"text": "The "' in response.text
    assert "event: done" in response.text


def test_session_context_is_sent_to_next_model_turn(isolated_runtime: FakeGateway) -> None:
    session = client.post("/api/v1/chat/sessions").json()
    client.post("/api/v1/chat/messages", json={"session_id": session["id"], "content": "I need rings"})
    client.post("/api/v1/chat/messages", json={"session_id": session["id"], "content": "Show me the options"})
    stored = memory_store.get_session(session["id"])
    assert stored is not None
    assert len(stored.messages) == 4
    assert any("I need rings" in str(message.get("content")) for message in isolated_runtime.calls[-1][0])


def test_handoff_marks_session() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/handoff", json={"session_id": session["id"], "content": "human please"})
    assert response.status_code == 200
    assert response.json()["action"] == "request_human_handoff"
