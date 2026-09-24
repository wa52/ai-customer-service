from fastapi.testclient import TestClient

import app.api.products as products_api
from app.capabilities.public_seed import PublicProductCapability
from app.main import app


def test_public_product_catalog_filters_and_paginates(monkeypatch) -> None:
    monkeypatch.setattr(products_api.customer_service_runtime.executor, "product", PublicProductCapability())
    response = TestClient(app).get("/api/v1/products", params={"category": "ring", "page": 2, "page_size": 3})

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] > 3
    assert payload["page"] == 2
    assert len(payload["items"]) == 3
    assert all(item["category"] == "ring" for item in payload["items"])
    assert all(any("\u4e00" <= char <= "\u9fff" for char in item["display_name"]) for item in payload["items"])
    assert payload["is_external_reference"] is True
