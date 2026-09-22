import re

from app.schemas.runtime import PerceptionResult


class PerceptionService:
    def perceive(self, content: str, state) -> PerceptionResult:
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
        quantity = re.search(r"\b(\d{2,6})\s*(pcs|pieces)?\b", text)
        if quantity:
            entities["quantity"] = int(quantity.group(1))
        if "ring" in text or "戒指" in text:
            entities["category"] = "ring"
        elif "bracelet" in text or "手链" in text:
            entities["category"] = "bracelet"
        elif "necklace" in text or "项链" in text:
            entities["category"] = "necklace"
        missing = []
        if intent in {"product_search", "similar_product_search"}:
            missing = [field for field in ("style", "color") if field not in entities]
        return PerceptionResult(intent=intent, entities=entities, missing_information=missing, confidence=0.88)

