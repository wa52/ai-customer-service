from app.schemas.runtime import DialogueAction, PerceptionResult


class ResponseGenerator:
    def generate(self, perception: PerceptionResult, action: DialogueAction, state) -> str:
        if action.action == "request_human_handoff":
            return "I’ll connect you with a human sales colleague so we can help you properly."
        if action.action == "ask_requirement":
            prompts = {"style": "Are you looking for simple everyday designs or more decorative styles?", "color": "Do you prefer silver, gold, black, or another finish?"}
            return prompts.get(action.field or "", "Could you share a little more about the design you prefer?")
        if action.action == "ask_clarification":
            return "Which product or SKU are you asking about? I’ll check the exact details for you."
        if action.action == "search_product":
            return "Thanks, I’ve understood the main requirements. I’m checking the closest products now."
        if action.action == "search_similar_product":
            return "I can help look for similar designs. Please upload a clear product image so I can compare it with our catalog."
        if action.action == "get_product_information":
            return "I can confirm the exact product details once you share the SKU or select a product from the recommendations."
        if perception.intent == "general_chat":
            return "Thanks for reaching out. I can help with products, materials, MOQ, specifications, and quotation requests."
        return "I understand. Could you share the product name or SKU so I can give you an accurate answer?"

