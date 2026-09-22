import json
from collections.abc import AsyncIterator
from typing import Any

from app.capabilities.executor import ActionExecutor
from app.runtime.llm.gateway import LLMGateway, LLMResponse, ToolCall
from app.schemas.chat import MessageResponse
from app.services.memory import memory_store


class CustomerServiceRuntime:
    """Thin orchestration layer around GPT/DeepSeek and the native tool registry."""

    def __init__(self, gateway: LLMGateway | None = None, executor: ActionExecutor | None = None) -> None:
        self.gateway = gateway or LLMGateway()
        self.executor = executor or ActionExecutor()

    async def handle_message(self, session_id: str, content: str) -> MessageResponse:
        memory_store.append(session_id, "customer", content)
        messages = memory_store.build_llm_messages(session_id)
        response = await self.gateway.complete(messages, self.executor.definitions())
        response = await self._resolve_tool_calls(session_id, messages, response)
        reply = response.content or "I’m sorry, I couldn’t complete that request. I can connect you with a human colleague."
        return memory_store.append(session_id, "assistant", reply)

    async def stream_message(self, session_id: str, content: str) -> AsyncIterator[str]:
        memory_store.append(session_id, "customer", content)
        messages = memory_store.build_llm_messages(session_id)
        collected: list[str] = []
        for _ in range(3):
            tool_calls: list[ToolCall] = []
            async for event in self.gateway.stream(messages, self.executor.definitions()):
                if event.text:
                    collected.append(event.text)
                    yield event.text
                tool_calls.extend(event.tool_calls)
            if not tool_calls:
                break
            messages = self._append_tool_turn(messages, tool_calls, session_id)
        reply = "".join(collected).strip() or "I’m sorry, I couldn’t complete that request. I can connect you with a human colleague."
        memory_store.append(session_id, "assistant", reply)

    async def _resolve_tool_calls(self, session_id: str, messages: list[dict[str, Any]], response: LLMResponse) -> LLMResponse:
        for _ in range(3):
            if not response.tool_calls:
                return response
            messages = self._append_tool_turn(messages, response.tool_calls, session_id)
            response = await self.gateway.complete(messages, self.executor.definitions())
        return response

    def _append_tool_turn(self, messages: list[dict[str, Any]], calls: list[ToolCall], session_id: str) -> list[dict[str, Any]]:
        next_messages = list(messages)
        next_messages.append({"role": "assistant", "content": None, "tool_calls": [{"id": call.id, "type": "function", "function": {"name": call.name, "arguments": json.dumps(call.arguments)}} for call in calls]})
        state = memory_store.get_state(session_id)
        for call in calls:
            result = self.executor.execute(call.name, call.arguments, state)
            self._apply_result(state, result.data)
            if result.data.get("human_handoff"):
                memory_store.set_status(session_id, "human_required")
            next_messages.append({"role": "tool", "tool_call_id": call.id, "content": json.dumps(result.model_dump(), ensure_ascii=False)})
        return next_messages

    @staticmethod
    def _apply_result(state, data: dict[str, object]) -> None:
        products = data.get("products")
        if isinstance(products, list):
            state.candidate_products = [str(item["sku"]) for item in products if isinstance(item, dict) and "sku" in item]
        product = data.get("product")
        if isinstance(product, dict) and "sku" in product:
            state.selected_product = str(product["sku"])

    def handoff(self, session_id: str) -> MessageResponse:
        memory_store.set_status(session_id, "human_required")
        return memory_store.append(session_id, "assistant", "I’ll connect you with a human sales colleague.", action="request_human_handoff")


customer_service_runtime = CustomerServiceRuntime()
