from collections.abc import Callable
from typing import Any

from app.schemas.runtime import CapabilityResult
from app.services.memory import ConversationState


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[dict[str, Any], Callable[[dict[str, Any], ConversationState], CapabilityResult]]] = {}

    def register(self, definition: dict[str, Any], handler: Callable[[dict[str, Any], ConversationState], CapabilityResult]) -> None:
        self._tools[definition["function"]["name"]] = (definition, handler)

    def definitions(self) -> list[dict[str, Any]]:
        return [definition for definition, _ in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any], state: ConversationState) -> CapabilityResult:
        registered = self._tools.get(name)
        if registered is None:
            return CapabilityResult(success=False, error={"code": "UNKNOWN_TOOL", "message": name})
        return registered[1](arguments, state)

