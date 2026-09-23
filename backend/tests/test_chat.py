from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.capabilities.executor import ActionExecutor
from app.capabilities.public_seed import PublicKnowledgeCapability, PublicProductCapability, PublicPricingCapability
from app.config.settings import Settings
from app.customer_service.runtime import CustomerServiceRuntime
from app.main import app
from app.runtime.llm.gateway import LLMResponse, StreamEvent, ToolCall
from app.schemas.runtime import CapabilityResult
from app.services.memory import memory_store
from app.services.memory import detect_language
import app.api.chat as chat_api
import app.api.upload as upload_api


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
    runtime = CustomerServiceRuntime(fake, ActionExecutor(Settings(product_capability_enabled=True, product_data_source="mock", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock")))
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
    assert isolated_runtime.calls[0][0][-1]["role"] == "user"


def test_tool_configuration_controls_registry() -> None:
    disabled = Settings(product_capability_enabled=False, pricing_capability_enabled=False, knowledge_capability_enabled=False, vision_capability_enabled=False)
    assert {tool["function"]["name"] for tool in ActionExecutor(disabled).definitions()} == {"request_human_handoff"}
    assert len(ActionExecutor(Settings(product_capability_enabled=True)).definitions()) == 6


def test_mock_capabilities_return_structured_results() -> None:
    executor = ActionExecutor(Settings(product_data_source="mock", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock"))
    session = client.post("/api/v1/chat/sessions").json()
    state = memory_store.get_state(session["id"])
    assert executor.execute("get_product_price", {"sku": "R1001", "quantity": 100}, state).data["unit_price"] == 2.8
    assert executor.execute("search_knowledge", {"question": "What material?"}, state).data["mode"] == "mock"
    assert executor.execute("search_similar_product_by_image", {"description": "black simple ring"}, state).data["mode"] == "mock"


def test_invalid_tool_arguments_are_returned_as_structured_error() -> None:
    executor = ActionExecutor(Settings(product_capability_enabled=True))
    result = executor.execute("get_product_information", {"sku": ""}, memory_store.get_state(client.post("/api/v1/chat/sessions").json()["id"]))
    assert result.success is False
    assert result.error is not None
    assert result.error["code"] == "INVALID_ARGUMENTS"


def test_public_seed_capabilities_keep_external_provenance() -> None:
    public = ActionExecutor(Settings(product_data_source="public_seed", pricing_data_source="public_seed", knowledge_data_source="public_seed", vision_data_source="public_seed"))
    products = public.execute("search_products", {"category": "ring"}, memory_store.get_state(client.post("/api/v1/chat/sessions").json()["id"]))
    assert products.success is True
    assert products.sources == ["public_product_catalog"]
    assert products.data["products"][0]["data_kind"] == "external_reference"
    assert products.data["products"][0]["is_external_reference"] is True
    price = public.execute("get_product_price", {"sku": "unknown"}, memory_store.get_state(client.post("/api/v1/chat/sessions").json()["id"]))
    assert price.success is False
    assert price.error["code"] == "PRICE_NOT_FOUND"
    assert isinstance(public.product, PublicProductCapability)
    assert isinstance(public.pricing, PublicPricingCapability)
    assert isinstance(public.knowledge, PublicKnowledgeCapability)


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


def test_customer_language_is_detected_and_added_to_model_context() -> None:
    session = client.post("/api/v1/chat/sessions").json()
    client.post("/api/v1/chat/messages", json={"session_id": session["id"], "content": "我想找黑色戒指"})
    stored = memory_store.get_session(session["id"])
    assert detect_language("我想找黑色戒指") == "zh"
    assert stored is not None and stored.language == "zh"
    assert "same language" in str(memory_store.build_llm_messages(session["id"])[0]["content"])


def test_upload_image_runs_vision_capability(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVision:
        def search_image_bytes(self, content: bytes, filename: str) -> CapabilityResult:
            assert content.startswith(b"fake-image")
            assert filename == "reference.jpg"
            return CapabilityResult(
                success=True,
                data={"matches": [{"image_id": "HF-JEWELRY-0001"}], "mode": "pgvector"},
                sources=["postgres_pgvector_vision"],
            )

    class RuntimeStub:
        class Executor:
            vision = FakeVision()

        executor = Executor()

    monkeypatch.setattr(upload_api, "customer_service_runtime", RuntimeStub())
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post(
        "/api/v1/chat/upload-image",
        data={"session_id": session["id"]},
        files={"image": ("reference.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    assert response.json()["data"]["matches"][0]["image_id"] == "HF-JEWELRY-0001"
