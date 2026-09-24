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
        timeout = httpx.Timeout(connect=10, read=45, write=15, pool=10)
        async with httpx.AsyncClient(timeout=timeout) as client:
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
        raw_user = next((item["content"] for item in reversed(messages) if item["role"] == "user"), "")
        user = raw_user.lower()
        chinese = any("\u4e00" <= char <= "\u9fff" for char in user)
        tool_names = {tool["function"]["name"] for tool in tools}
        tool_messages = [item for item in messages if item["role"] == "tool"]
        if tool_messages:
            try:
                result = json.loads(str(tool_messages[-1]["content"]))
                data = result.get("data", {})
            except (json.JSONDecodeError, TypeError):
                data = {}
            if "unit_price" in data:
                return LLMResponse(content=f"该产品的公开参考价为 {data['currency']} {data['unit_price']} / 件，最终价格需要销售确认。" if chinese else f"The public reference price is {data['currency']} {data['unit_price']} per piece. Final pricing requires sales confirmation.")
            if "matches" in data:
                identifiers = ", ".join(str(item.get("sku") or item.get("image_id")) for item in data["matches"])
                return LLMResponse(content=f"根据图片描述，匹配到：{identifiers}。请上传图片或告诉我更多细节。" if chinese else f"The visual search matched: {identifiers}. Please upload an image or share more details.")
            if "answer" in data:
                return LLMResponse(content="我们的不锈钢饰品默认使用 316L 材质，样品和生产细节可以由销售进一步确认。" if chinese else data["answer"])
            if "products" in data:
                products = data["products"]
                category_question = any(word in user for word in ("品类", "类别", "分类", "有哪些产品", "什么产品", "categories", "what products"))
                if category_question:
                    categories = dict.fromkeys(str(item.get("category", "")) for item in products if item.get("category"))
                    labels = {"ring": "戒指", "necklace": "项链", "bracelet": "手链", "jewelry": "其他饰品"}
                    if chinese:
                        names = "、".join(labels.get(category, category) for category in categories)
                        return LLMResponse(content=f"目前可以查询这些品类：{names}。你想先看哪一类？")
                    return LLMResponse(content=f"I can help you browse: {', '.join(categories)}. Which category would you like to see?")
                examples = products[:3]
                if chinese:
                    lines = "；".join(f"{item.get('name') or item['sku']}（{item['sku']}）" for item in examples)
                    suffix = "这些是公开目录参考款，具体供货信息可再确认。" if examples and any(item.get("is_external_reference") for item in examples) else ""
                    return LLMResponse(content=f"我先给你看几款匹配的：{lines}。{suffix}" if examples else "当前目录里暂时没有匹配款。你可以换个品类或描述再试试。")
                skus = ", ".join(str(item.get("sku", "")) for item in examples)
                return LLMResponse(content=f"Here are a few matching catalog items: {skus}.")

        greetings = ("你好", "您好", "嗨", "早上好", "下午好", "晚上好", "hello", "hi", "hey", "good morning")
        if user.strip().strip("!！。,. ") in greetings:
            return LLMResponse(content="你好！我可以帮你查产品品类、款式、材质和公开参考价。你想先了解什么？" if chinese else "Hi! I can help you browse styles, materials, and public reference prices. What are you looking for?")

        category_aliases = {
            "ring": ("ring", "rings", "戒指", "指环"),
            "necklace": ("necklace", "necklaces", "项链"),
            "bracelet": ("bracelet", "bracelets", "手链", "手镯"),
            "jewelry": ("jewelry", "饰品", "珠宝"),
        }
        category = next((name for name, aliases in category_aliases.items() if any(alias in user for alias in aliases)), None)
        category_request = category is not None and any(word in user for word in ("想", "找", "看看", "看", "有没有", "推荐", "要", "需要", "show", "find", "looking", "want", "need"))
        category_question = any(word in user for word in ("品类", "类别", "分类", "有哪些产品", "什么产品", "categories", "what products"))
        if "search_products" in tool_names and (category_request or category_question):
            arguments = {"category": category} if category_request else {}
            return LLMResponse(tool_calls=[ToolCall("fallback_search", "search_products", arguments)])
        if any(word in user for word in ("价格", "多少钱", "报价", "price", "quote")):
            return LLMResponse(content="把产品编号或款式图片发给我，我就可以帮你查公开参考价。" if chinese else "Share the product SKU or a photo and I can look up its public reference price.")
        if chinese and any(word in user for word in ("产品", "款式", "饰品", "珠宝")) and "search_products" in tool_names:
            return LLMResponse(content="可以帮你查产品目录。目前可查戒指、项链、手链等品类，你想先看哪一类？")
        import re
        sku_match = re.search(r"(?:r\d{4}|jw-[a-f0-9]{8}-\d{2})", user)
        if any(word in user for word in ("price", "报价", "价格", "多少钱")) and "get_product_price" in tool_names and sku_match:
            return LLMResponse(tool_calls=[ToolCall("fallback_price", "get_product_price", {"sku": sku_match.group(0).upper()})])
        if any(word in user for word in ("image", "photo", "图片", "照片", "找款", "相似")) and "search_similar_product_by_image" in tool_names:
            return LLMResponse(tool_calls=[ToolCall("fallback_vision", "search_similar_product_by_image", {"description": raw_user})])
        if any(word in user for word in ("material", "specification", "材质", "材料", "316l")) and "search_knowledge" in tool_names:
            return LLMResponse(tool_calls=[ToolCall("fallback_knowledge", "search_knowledge", {"question": raw_user})])
        if any(word in user for word in ("human", "sales", "人工")):
            return LLMResponse(content="我会为您转接人工销售同事。" if chinese else "I’ll connect you with a human sales colleague.")
        return LLMResponse(content="感谢您的咨询。请告诉我您想了解的产品或 SKU。" if chinese else "Thanks for reaching out. Could you share the product or SKU you’re asking about?")

    async def stream(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> AsyncIterator[StreamEvent]:
        response = await self.complete(messages, tools)
        if response.tool_calls:
            yield StreamEvent(tool_calls=response.tool_calls)
            return
        for word in response.content.split(" "):
            yield StreamEvent(text=word + " ")
