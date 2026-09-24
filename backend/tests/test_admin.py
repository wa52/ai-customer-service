from fastapi.testclient import TestClient

from app.api import admin as admin_api
from app.customer_service.runtime import customer_service_runtime
from app.main import app


def test_admin_config_never_exposes_api_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    original_settings = admin_api._runtime_settings
    original_gateway = customer_service_runtime.gateway.settings
    original_executor = customer_service_runtime.executor
    try:
        client = TestClient(app)
        response = client.post("/api/v1/admin/config", json={"llm_base_url": "https://example.com/v1", "llm_model": "demo", "llm_api_key": "secret-key-123"})
        assert response.status_code == 200
        assert response.json()["api_key_masked"] != "secret-key-123"
        assert response.json()["api_key_set"] is True
        assert customer_service_runtime.gateway.settings.llm_model == "demo"

        response = client.get("/api/v1/admin/config")
        assert response.json()["api_key_set"] is True
        assert "secret-key-123" not in response.text
    finally:
        admin_api._runtime_settings = original_settings
        customer_service_runtime.gateway.settings = original_gateway
        customer_service_runtime.executor = original_executor


def test_admin_page_is_available() -> None:
    response = TestClient(app).get("/admin")
    assert response.status_code == 200
    assert "连接你的云端大脑" in response.text
