from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.capabilities.executor import ActionExecutor
from app.capabilities.public_seed import PublicKnowledgeCapability, PublicProductCapability, PublicPricingCapability
from app.config.settings import Settings
from app.customer_service.runtime import CustomerServiceRuntime, _recommendation_requirements
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
        self.calls.append((messages, tools))
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


def test_chinese_recommendation_searches_and_limits_to_three_distinct_styles() -> None:
    settings = Settings(product_data_source="public_seed", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock")
    runtime = CustomerServiceRuntime(FakeGateway(), ActionExecutor(settings))
    session = client.post("/api/v1/chat/sessions").json()

    async def collect() -> list[str]:
        return [chunk async for chunk in runtime.stream_message(session["id"], "银色的手镯有哪些")]

    import asyncio

    asyncio.run(collect())
    candidates = memory_store.get_state(session["id"]).candidate_products
    products = [runtime.executor.product.get(sku).data["product"] for sku in candidates]
    assert len(products) == 3
    assert all(item["category"] == "bracelet" and "silver" in str(item["name"]).casefold() for item in products)
    assert len({str(item["name"]).split(" / ")[0] for item in products}) == 3


def test_silver_anklet_request_maps_both_category_and_specific_style_keyword() -> None:
    assert _recommendation_requirements("推荐三个银色脚链") == {"category": "bracelet", "query": "silver anklet", "limit": 3}


def test_silver_anklet_with_no_exact_match_shows_three_labeled_bracelet_alternatives() -> None:
    settings = Settings(product_data_source="public_seed", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock")
    gateway = FakeGateway()
    runtime = CustomerServiceRuntime(gateway, ActionExecutor(settings))
    session = client.post("/api/v1/chat/sessions").json()

    async def collect() -> str:
        return "".join([chunk async for chunk in runtime.stream_message(session["id"], "推荐三个银色脚链")])

    import asyncio

    reply = asyncio.run(collect())
    state = memory_store.get_state(session["id"])
    products = [runtime.executor.product.get(sku).data["product"] for sku in state.candidate_products]
    assert len(products) == 3
    assert all(item["category"] == "bracelet" and "silver" in str(item["name"]).casefold() for item in products)
    assert "没有银色脚链" in reply
    assert "替代参考（不是脚链）" in reply
    assert gateway.calls == []


def test_silver_anklet_fallback_stream_exposes_three_product_page_links(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(product_data_source="public_seed", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock")
    runtime = CustomerServiceRuntime(FakeGateway(), ActionExecutor(settings))
    monkeypatch.setattr(chat_api, "customer_service_runtime", runtime)
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages/stream", json={"session_id": session["id"], "content": "推荐三个银色脚链"})

    product_event = next(event for event in response.text.split("\n\n") if event.startswith("event: products"))
    payload = __import__("json").loads(next(line[6:] for line in product_event.splitlines() if line.startswith("data: ")))
    assert len(payload) == 3
    assert all(item["category"] == "bracelet" and item.get("source_url", "").startswith("http") for item in payload)


def test_recommendation_stream_includes_three_translated_product_cards(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(product_data_source="public_seed", pricing_data_source="mock", knowledge_data_source="mock", vision_data_source="mock")
    runtime = CustomerServiceRuntime(FakeGateway(), ActionExecutor(settings))
    monkeypatch.setattr(chat_api, "customer_service_runtime", runtime)
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages/stream", json={"session_id": session["id"], "content": "银色的手镯有哪些"})

    product_event = next(event for event in response.text.split("\n\n") if event.startswith("event: products"))
    payload = __import__("json").loads(next(line[6:] for line in product_event.splitlines() if line.startswith("data: ")))
    assert len(payload) == 3
    assert all(item["category"] == "bracelet" and item["display_name"] for item in payload)


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


def test_streaming_reports_runtime_errors_as_sse_events(monkeypatch: pytest.MonkeyPatch) -> None:
    async def broken_stream(session_id: str, content: str) -> AsyncIterator[str]:
        raise TimeoutError("upstream stalled")
        yield "unreachable"

    monkeypatch.setattr(chat_api.customer_service_runtime, "stream_message", broken_stream)
    session = client.post("/api/v1/chat/sessions").json()
    response = client.post("/api/v1/chat/messages/stream", json={"session_id": session["id"], "content": "推荐银色网球链"})
    assert response.status_code == 200
    assert "event: error" in response.text
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


def test_upload_image_returns_product_sku_card_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVision:
        def search_image_bytes(self, _content: bytes, _filename: str) -> CapabilityResult:
            return CapabilityResult(
                success=True,
                data={
                    "matches": [{
                        "sku": "JW-TEST-01",
                        "name": "Silver stainless steel ring",
                        "category": "ring",
                        "reference_price": 3.25,
                        "currency": "USD",
                        "image_url": "https://catalog.example/ring.webp",
                        "source_url": "https://catalog.example/products/ring",
                        "similarity": 0.91,
                    }],
                    "mode": "pgvector_product_catalog",
                },
                sources=["postgres_product_image_embeddings"],
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
    product = response.json()["data"]["matches"][0]
    assert product["sku"] == "JW-TEST-01"
    assert product["display_name"] == product["name"]
    assert product["source_url"].endswith("/products/ring")
    assert product["similarity"] == 0.91
