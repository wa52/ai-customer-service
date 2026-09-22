from app.schemas.runtime import CapabilityResult
from app.runtime.tool_calling.registry import ToolRegistry
from app.capabilities.product import ProductCapability
from app.config.settings import Settings, get_settings


class ActionExecutor:
    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        self.registry = ToolRegistry()
        self.product = ProductCapability()
        if settings.product_capability_enabled:
            self.registry.register({"type": "function", "function": {"name": "search_products", "description": "Search products by structured requirements. Return factual catalog matches only.", "parameters": {"type": "object", "properties": {"category": {"type": "string"}, "material": {"type": "string"}, "color": {"type": "string"}, "style": {"type": "string"}, "gender": {"type": "string"}}, "additionalProperties": False}}}, self.product.search_tool)
            self.registry.register({"type": "function", "function": {"name": "get_product_information", "description": "Get factual specifications and MOQ for one SKU.", "parameters": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"], "additionalProperties": False}}}, self.product.get_tool)
        self.registry.register({"type": "function", "function": {"name": "request_human_handoff", "description": "Mark the current conversation for human sales support when the customer requests a person or the model cannot safely answer.", "parameters": {"type": "object", "properties": {"reason": {"type": "string"}}, "additionalProperties": False}}}, self._handoff_tool)

    def definitions(self) -> list[dict[str, object]]:
        return self.registry.definitions()

    def execute(self, name: str, arguments: dict[str, object], state) -> CapabilityResult:
        return self.registry.execute(name, arguments, state)

    @staticmethod
    def _handoff_tool(arguments: dict[str, object], _state) -> CapabilityResult:
        return CapabilityResult(success=True, data={"human_handoff": True, "reason": arguments.get("reason", "model_decision")}, confidence=1.0, sources=["customer_service_policy"])
