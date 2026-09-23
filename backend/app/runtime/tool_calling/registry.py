from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError
from app.schemas.runtime import CapabilityResult
from app.services.memory import ConversationState


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, tuple[dict[str, Any], Callable[[dict[str, Any], ConversationState], CapabilityResult], type[BaseModel] | None]] = {}

    def register(self, definition: dict[str, Any], handler: Callable[[dict[str, Any], ConversationState], CapabilityResult], arguments_model: type[BaseModel] | None = None) -> None:
        self._tools[definition["function"]["name"]] = (definition, handler, arguments_model)

    def definitions(self) -> list[dict[str, Any]]:
        return [definition for definition, _, _ in self._tools.values()]

    def execute(self, name: str, arguments: dict[str, Any], state: ConversationState) -> CapabilityResult:
        registered = self._tools.get(name)
        if registered is None:
            return CapabilityResult(success=False, error={"code": "UNKNOWN_TOOL", "message": name})
        try:
            validated = registered[2].model_validate(arguments).model_dump(exclude_none=True) if registered[2] else arguments
        except ValidationError as error:
            return CapabilityResult(success=False, error={"code": "INVALID_ARGUMENTS", "message": error.json()})
        return registered[1](validated, state)
