import json
import re
from collections.abc import AsyncIterator
from typing import Any

from app.capabilities.executor import ActionExecutor
from app.runtime.llm.gateway import LLMGateway, LLMResponse, ToolCall
from app.schemas.chat import MessageResponse
from app.services.memory import detect_language, memory_store


_PRODUCT_CATEGORIES = (
    (("手镯", "手链", "手环", "脚链", "bracelet", "bangle", "anklet"), "bracelet"),
    (("项链", "吊坠", "necklace"), "necklace"),
    (("戒指", "指环", "ring"), "ring"),
    (("耳环", "耳钉", "耳饰", "earring", "earrings"), "jewelry"),
)
_PRODUCT_STYLE_KEYWORDS = (("脚链", "anklet"), ("anklet", "anklet"))
_PRODUCT_COLORS = (
    (("银色", "银白", "silver"), "silver"),
    (("玫瑰金", "rose gold"), "rose gold"),
    (("金色", "黄金色", "gold"), "gold"),
    (("黑色", "black"), "black"),
    (("白色", "white"), "white"),
)


def _recommendation_requirements(content: str) -> dict[str, object] | None:
    text = content.casefold()
    if any(term in text for term in ("品类", "类别", "分类", "有哪些产品", "what categories")):
        return None
    intent_terms = ("有哪些", "有什麼", "推荐", "推薦", "推荐款", "找", "看看", "款式", "有没有", "有什么", "show me", "recommend", "find", "options", "styles", "available")
    if not any(term in text for term in intent_terms):
        return None
    category = next((slug for aliases, slug in _PRODUCT_CATEGORIES if any(alias in text for alias in aliases)), None)
    if category is None:
        return None
    query_terms = [value for aliases, value in _PRODUCT_COLORS if any(alias in text for alias in aliases)]
    query_terms.extend(value for alias, value in _PRODUCT_STYLE_KEYWORDS if alias in text)
    query = " ".join(dict.fromkeys(query_terms)) or None
    return {"category": category, "query": query, "limit": 3}


def _top_three_styles(products: list[dict[str, object]]) -> list[dict[str, object]]:
    unique: list[dict[str, object]] = []
    seen: set[str] = set()
    for product in products:
        name = str(product.get("name", ""))
        style_name = re.sub(r"\s*/\s*[^/]*$", "", name).casefold().strip() or str(product.get("sku", ""))
        if style_name in seen:
            continue
        seen.add(style_name)
        unique.append(product)
        if len(unique) == 3:
            break
    return unique


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
        state = memory_store.get_state(session_id)
        state.last_action = None
        search_requirements = _recommendation_requirements(content)
        available_tools = self.executor.definitions()
        if search_requirements and any(tool["function"]["name"] == "search_products" for tool in available_tools):
            result = self.executor.product.search(
                {"category": search_requirements["category"]},
                query=str(search_requirements["query"]) if search_requirements["query"] else None,
                limit=60,
            )
            products = _top_three_styles(result.data.get("products", []))
            state.candidate_products = [str(item["sku"]) for item in products if item.get("sku")]
            state.last_action = "search_products"
            if not products:
                reply = (
                    "我查了当前公开目录，暂时没有找到银色脚链。可以改看银色手链，或金色脚链；你更想看哪一种？"
                    if detect_language(content) == "zh"
                    else "I couldn't find silver anklets in the current public catalog. I can show silver bracelets or gold anklets instead—which would you prefer?"
                )
                memory_store.append(session_id, "assistant", reply)
                yield reply
                return
            product_context = json.dumps(products, ensure_ascii=False)
            guidance = (
                "A product-catalog search has already been run for this customer's request. "
                + ("Recommend only up to three distinct styles from these exact results. Do not say you will search; show the options now. " if products else "No exact catalog matches were found. Say that clearly, and ask whether the customer would consider a nearby alternative; never label an alternative as the requested product. ")
                + "Do not invent product facts. These are public reference products, not company inventory or a formal quote. "
                + f"Search results: {product_context}"
            )
            messages.insert(1, {"role": "system", "content": guidance})
            available_tools = [tool for tool in available_tools if tool["function"]["name"] != "search_products"]
        collected: list[str] = []
        for _ in range(3):
            tool_calls: list[ToolCall] = []
            async for event in self.gateway.stream(messages, available_tools):
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
            state.last_action = call.name
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
