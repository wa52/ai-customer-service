from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "openai_compatible"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_temperature: float = Field(default=0.3, ge=0, le=2)
    product_capability_enabled: bool = True
    product_data_source: str = "postgres"
    pricing_capability_enabled: bool = True
    pricing_data_source: str = "postgres"
    pricing_base_url: str = ""
    knowledge_capability_enabled: bool = True
    knowledge_data_source: str = "postgres"
    knowledge_base_url: str = ""
    vision_capability_enabled: bool = True
    vision_data_source: str = "postgres"
    vision_base_url: str = ""
    memory_provider: str = "memory"
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/customer_service"


@lru_cache
def get_settings() -> Settings:
    return Settings()
