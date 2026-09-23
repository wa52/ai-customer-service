from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.capabilities.executor import ActionExecutor
from app.config.settings import Settings, get_settings
from app.customer_service.runtime import customer_service_runtime

router = APIRouter(prefix="/admin", tags=["admin"])
_runtime_settings = get_settings()


class AdminConfigRequest(BaseModel):
    llm_provider: str = Field(default="openai_compatible", min_length=1, max_length=64)
    llm_base_url: str = Field(default="", max_length=500)
    llm_api_key: str | None = Field(default=None, max_length=500)
    llm_model: str = Field(default="", max_length=200)
    llm_temperature: float = Field(default=0.3, ge=0, le=2)
    product_capability_enabled: bool = True
    product_data_source: str = "mock"
    pricing_capability_enabled: bool = True
    pricing_data_source: str = "mock"
    pricing_base_url: str = ""
    knowledge_capability_enabled: bool = True
    knowledge_data_source: str = "mock"
    knowledge_base_url: str = ""
    vision_capability_enabled: bool = True
    vision_data_source: str = "mock"
    vision_base_url: str = ""


def _masked_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "•" * len(api_key)
    return f"{api_key[:3]}{'•' * 8}{api_key[-3:]}"


def _public_config(settings: Settings) -> dict[str, Any]:
    return {
        "llm_provider": settings.llm_provider,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
        "llm_temperature": settings.llm_temperature,
        "configured": bool(settings.llm_base_url and settings.llm_api_key and settings.llm_model),
        "api_key_set": bool(settings.llm_api_key),
        "api_key_masked": _masked_key(settings.llm_api_key),
        "memory_provider": settings.memory_provider,
        "product_capability_enabled": settings.product_capability_enabled,
        "capabilities": {
            "product": {"enabled": settings.product_capability_enabled, "source": settings.product_data_source},
            "pricing": {"enabled": settings.pricing_capability_enabled, "source": settings.pricing_data_source, "base_url": settings.pricing_base_url},
            "knowledge": {"enabled": settings.knowledge_capability_enabled, "source": settings.knowledge_data_source, "base_url": settings.knowledge_base_url},
            "vision": {"enabled": settings.vision_capability_enabled, "source": settings.vision_data_source, "base_url": settings.vision_base_url},
        },
        "storage_note": "模型配置仅保存在当前后端进程内存中，重启后需要重新填写。",
    }


@router.get("/config")
def get_admin_config() -> dict[str, Any]:
    return _public_config(_runtime_settings)


@router.post("/config")
def update_admin_config(request: AdminConfigRequest) -> dict[str, Any]:
    global _runtime_settings
    updates = request.model_dump(exclude={"llm_api_key"})
    if request.llm_api_key is not None and request.llm_api_key.strip():
        updates["llm_api_key"] = request.llm_api_key.strip()
    _runtime_settings = _runtime_settings.model_copy(update=updates)
    customer_service_runtime.gateway.settings = _runtime_settings
    customer_service_runtime.executor = ActionExecutor(_runtime_settings)
    return _public_config(_runtime_settings)
