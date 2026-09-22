from app.schemas.runtime import DialogueAction, PerceptionResult
from app.schemas.runtime import CapabilityResult


class ResponseGenerator:
    def generate(self, perception: PerceptionResult, action: DialogueAction, state, capability_result: CapabilityResult | None = None) -> str:
        if action.action == "request_human_handoff":
            return "I’ll connect you with a human sales colleague so we can help you properly."
        if action.action == "ask_requirement":
            prompts = {"style": "Are you looking for simple everyday designs or more decorative styles?", "color": "Do you prefer silver, gold, black, or another finish?"}
            return prompts.get(action.field or "", "Could you share a little more about the design you prefer?")
        if action.action == "ask_clarification":
            return "Which product or SKU are you asking about? I’ll check the exact details for you."
        if action.action == "search_product":
            products = capability_result.data.get("products", []) if capability_result else []
            if products:
                listed = "\n".join(f"{index}. {product['sku']} — {product['name']}" for index, product in enumerate(products, start=1))
                return f"I found these options based on your requirements:\n{listed}\nWhich one would you like to know more about?"
            return "I couldn’t find a matching product in the current catalog. Would you like to adjust the style or finish?"
        if action.action == "search_similar_product":
            return "I can help look for similar designs. Please upload a clear product image so I can compare it with our catalog."
        if action.action == "get_product_information":
            product = capability_result.data.get("product") if capability_result else None
            if isinstance(product, dict):
                if perception.intent == "moq_question":
                    return f"The MOQ for {product['sku']} is {product['moq']} pcs."
                if perception.intent == "material_question":
                    return f"{product['sku']} is made from {product['material']} stainless steel."
                return f"{product['sku']} is {product['name']}, made from {product['material']} stainless steel, with a MOQ of {product['moq']} pcs."
            return "I can’t confirm that product detail yet. Please share the SKU or select a product from the recommendations."
        if perception.intent == "general_chat":
            return "Thanks for reaching out. I can help with products, materials, MOQ, specifications, and quotation requests."
        return "I understand. Could you share the product name or SKU so I can give you an accurate answer?"
