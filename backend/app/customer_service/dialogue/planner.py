from app.schemas.runtime import DialogueAction, PerceptionResult


class DialoguePlanner:
    def plan(self, perception: PerceptionResult, state) -> DialogueAction:
        if perception.intent == "human_service" or perception.sentiment == "dissatisfied":
            return DialogueAction(action="request_human_handoff", reason_code="CUSTOMER_REQUEST")
        if perception.intent in {"product_search", "similar_product_search"} and perception.missing_information:
            return DialogueAction(action="ask_requirement", field=perception.missing_information[0], reason_code="MISSING_FILTER")
        if perception.references:
            state.selected_product = perception.references[0].get("sku")
        if perception.intent in {"price_question", "moq_question", "material_question"} and not state.selected_product:
            return DialogueAction(action="ask_clarification", field="product", reason_code="MISSING_PRODUCT_REFERENCE")
        if perception.intent == "product_search":
            return DialogueAction(action="search_product")
        if perception.intent == "similar_product_search":
            return DialogueAction(action="search_similar_product")
        if perception.intent in {"price_question", "moq_question", "material_question"}:
            return DialogueAction(action="get_product_information")
        return DialogueAction(action="answer_directly")
