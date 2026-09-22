from app.customer_service.dialogue.planner import DialoguePlanner
from app.capabilities.executor import ActionExecutor
from app.customer_service.perception.service import PerceptionService
from app.customer_service.response.generator import ResponseGenerator
from app.schemas.chat import MessageResponse
from app.services.memory import memory_store


class CustomerServiceRuntime:
    def __init__(self) -> None:
        self.perception = PerceptionService()
        self.planner = DialoguePlanner()
        self.response = ResponseGenerator()
        self.executor = ActionExecutor()

    def handle_message(self, session_id: str, content: str) -> MessageResponse:
        memory_store.append(session_id, "customer", content)
        state = memory_store.get_state(session_id)
        perception = self.perception.perceive(content, state)
        state.current_intent = perception.intent
        state.requirements.update(perception.entities)
        state.missing_information = perception.missing_information
        action = self.planner.plan(perception, state)
        capability_result = self.executor.execute(action, state)
        if capability_result and capability_result.success:
            products = capability_result.data.get("products")
            if isinstance(products, list):
                state.candidate_products = [str(product["sku"]) for product in products if isinstance(product, dict) and "sku" in product]
            product = capability_result.data.get("product")
            if isinstance(product, dict) and "sku" in product:
                state.selected_product = str(product["sku"])
        reply = self.response.generate(perception, action, state, capability_result)
        state.last_action = action.action
        if action.action == "request_human_handoff":
            memory_store.set_status(session_id, "human_required")
        return memory_store.append(session_id, "assistant", reply, action=action.action, intent=perception.intent)

    def handoff(self, session_id: str) -> MessageResponse:
        memory_store.set_status(session_id, "human_required")
        return memory_store.append(
            session_id,
            "assistant",
            "I’ve marked this conversation for human support. A sales colleague will follow up with you shortly.",
            action="request_human_handoff",
        )


customer_service_runtime = CustomerServiceRuntime()
