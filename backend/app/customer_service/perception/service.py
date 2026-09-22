import re

import httpx

from app.schemas.runtime import PerceptionResult
from app.customer_service.perception.provider import OpenAICompatiblePerceptionProvider, StructuredPerceptionProvider


class PerceptionService:
    def __init__(self, provider: StructuredPerceptionProvider | None = None) -> None:
        self.provider = provider or OpenAICompatiblePerceptionProvider()

    def perceive(self, content: str, state) -> PerceptionResult:
        context = state.context()
        if isinstance(self.provider, OpenAICompatiblePerceptionProvider) and self.provider.is_configured():
            try:
                result = self.provider.perceive(content, context)
                return self._merge_with_memory(result, state)
            except (httpx.HTTPError, RuntimeError, ValueError, KeyError):
                pass
        return self._rule_based_perception(content, state)

    def _rule_based_perception(self, content: str, state) -> PerceptionResult:
        text = content.lower().strip()
        entities: dict[str, object] = {}
        if any(word in text for word in ("price", "cost", "how much", "报价", "价格")):
            intent = "price_question"
        elif any(word in text for word in ("material", "316l", "304", "材质")):
            intent = "material_question"
        elif any(word in text for word in ("moq", "minimum order", "起订")):
            intent = "moq_question"
        elif any(word in text for word in ("similar", "like this", "找款", "相似")):
            intent = "similar_product_search"
        elif any(word in text for word in ("human", "sales", "人工", "客服")):
            intent = "human_service"
        elif any(word in text for word in ("ring", "bracelet", "necklace", "earring", "戒指", "手链", "项链")):
            intent = "product_search"
        else:
            intent = "general_chat"
        if re.search(r"\b(316l|304)\b", text):
            entities["material"] = re.search(r"\b(316l|304)\b", text).group(1).upper()
        if any(word in text for word in ("men's", "mens", "男", "男性")):
            entities["gender"] = "men"
        if "black" in text or "黑" in text:
            entities["color"] = "black"
        elif "gold" in text or "金" in text:
            entities["color"] = "gold"
        if any(word in text for word in ("simple", "简约", "简单")):
            entities["style"] = "simple"
        elif any(word in text for word in ("decorative", "ornate", "装饰")):
            entities["style"] = "decorative"
        quantity = re.search(r"\b(\d{2,6})\s*(pcs|pieces)?\b", text)
        if quantity:
            entities["quantity"] = int(quantity.group(1))
        if "ring" in text or "戒指" in text:
            entities["category"] = "ring"
        elif "bracelet" in text or "手链" in text:
            entities["category"] = "bracelet"
        elif "necklace" in text or "项链" in text:
            entities["category"] = "necklace"
        elif state.requirements.get("category") and entities:
            intent = "product_search"
        if entities.get("category") and any(phrase in text for phrase in ("i need", "i want", "looking for", "find me", "需要", "想要")):
            intent = "product_search"
        references = self._references(text, state)
        missing = []
        if intent in {"product_search", "similar_product_search"}:
            known = {**state.requirements, **entities}
            missing = [field for field in ("style", "color") if field not in known]
        return PerceptionResult(intent=intent, entities=entities, references=references, missing_information=missing, confidence=0.88)

    @staticmethod
    def _references(text: str, state) -> list[dict[str, object]]:
        positions = {"first": 0, "second": 1, "third": 2}
        for word, index in positions.items():
            if re.search(rf"\b{word}\b", text) and len(state.candidate_products) > index:
                return [{"type": "candidate_product", "position": index + 1, "sku": state.candidate_products[index]}]
        if any(phrase in text for phrase in ("this one", "that one", "this product", "that product")) and state.selected_product:
            return [{"type": "current_product", "sku": state.selected_product}]
        return []

    @staticmethod
    def _merge_with_memory(result: PerceptionResult, state) -> PerceptionResult:
        known = {**state.requirements, **result.entities}
        result.missing_information = [field for field in result.missing_information if field not in known]
        return result
