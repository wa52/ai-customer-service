from app.schemas.runtime import CapabilityResult, DialogueAction
from app.services.memory import ConversationState
from app.capabilities.product import ProductCapability


class ActionExecutor:
    def __init__(self) -> None:
        self.product = ProductCapability()

    def execute(self, action: DialogueAction, state: ConversationState) -> CapabilityResult | None:
        if action.action == "search_product":
            return self.product.search(state.requirements)
        if action.action == "get_product_information" and state.selected_product:
            return self.product.get(state.selected_product)
        return None

