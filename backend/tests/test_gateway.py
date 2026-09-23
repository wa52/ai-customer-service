from app.config.settings import Settings
import asyncio

from app.runtime.llm.gateway import DeterministicGateway, LLMGateway


def test_openai_compatible_payload_supports_deepseek_and_native_tools() -> None:
    gateway = LLMGateway(Settings(llm_base_url="https://api.deepseek.com/v1", llm_api_key="secret", llm_model="deepseek-chat"))
    payload = gateway._payload([{"role": "user", "content": "Find rings"}], [{"type": "function", "function": {"name": "search_products"}}], stream=True)
    assert payload["model"] == "deepseek-chat"
    assert payload["stream"] is True
    assert payload["tool_choice"] == "auto"


def test_malformed_tool_arguments_do_not_crash_parser() -> None:
    response = LLMGateway._parse_response({"choices": [{"message": {"content": "", "tool_calls": [{"id": "c1", "function": {"name": "search_products", "arguments": "not-json"}}]}}]})
    assert response.tool_calls[0].arguments["_invalid_json"] == "not-json"


def test_mock_gateway_routes_price_question_to_tool() -> None:
    response = asyncio.run(DeterministicGateway().complete(
        [{"role": "user", "content": "What is the price of R1001?"}],
        [{"type": "function", "function": {"name": "get_product_price"}}],
    ))
    assert response.tool_calls[0].name == "get_product_price"
