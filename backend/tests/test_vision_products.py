from app.repositories.support_repository import PostgresVisionCapability
from app.vision.product_images import cached_product_image_path


class FakeQueryResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, product_rows, dataset_rows=(), missing_product_table=False):
        self.product_rows = product_rows
        self.dataset_rows = dataset_rows
        self.missing_product_table = missing_product_table
        self.statements = []
        self.rollbacks = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, statement, _params):
        self.statements.append(statement)
        if "product_image_embeddings" in statement:
            if self.missing_product_table:
                import psycopg

                raise psycopg.errors.UndefinedTable("product_image_embeddings")
            return FakeQueryResult(self.product_rows)
        return FakeQueryResult(self.dataset_rows)

    def rollback(self):
        self.rollbacks += 1


def test_image_vector_search_returns_top_three_product_skus(monkeypatch):
    rows = [
        {"sku": "SKU-1-A", "name": "Silver ring / Gold", "category": "ring", "similarity": 0.99},
        {"sku": "SKU-1-B", "name": "Silver ring / Silver", "category": "ring", "similarity": 0.98},
        {"sku": "SKU-2", "name": "Shell bracelet", "category": "bracelet", "similarity": 0.97},
        {"sku": "SKU-3", "name": "Heart necklace", "category": "necklace", "similarity": 0.96},
        {"sku": "SKU-4", "name": "Floral bangle", "category": "bracelet", "similarity": 0.95},
    ]
    connection = FakeConnection(rows)
    monkeypatch.setattr("psycopg.connect", lambda *_args, **_kwargs: connection)

    result = PostgresVisionCapability("postgresql://test")._search_embedding([0.1] * 512, "test upload", "test")

    assert result.success
    assert result.data["mode"] == "pgvector_product_catalog"
    assert [item["sku"] for item in result.data["matches"]] == ["SKU-1-A", "SKU-2", "SKU-3"]
    assert "JOIN products" in connection.statements[0]
    assert "vision_metadata" not in connection.statements[0]


def test_product_vector_search_falls_back_to_legacy_dataset_if_catalog_not_indexed(monkeypatch):
    connection = FakeConnection([], [{"image_id": "DATASET-1", "category": "ring", "similarity": 0.8}])
    monkeypatch.setattr("psycopg.connect", lambda *_args, **_kwargs: connection)

    result = PostgresVisionCapability("postgresql://test")._search_embedding([0.1] * 512, "test upload", "test")

    assert result.success
    assert result.data["mode"] == "pgvector_dataset_fallback"
    assert result.data["matches"][0]["image_id"] == "DATASET-1"
    assert len(connection.statements) == 2


def test_product_vector_search_uses_dataset_when_product_vector_migration_is_pending(monkeypatch):
    connection = FakeConnection([], [{"image_id": "DATASET-2", "category": "ring", "similarity": 0.7}], missing_product_table=True)
    monkeypatch.setattr("psycopg.connect", lambda *_args, **_kwargs: connection)

    result = PostgresVisionCapability("postgresql://test")._search_embedding([0.1] * 512, "test upload", "test")

    assert result.data["mode"] == "pgvector_dataset_fallback"
    assert result.data["matches"][0]["image_id"] == "DATASET-2"
    assert connection.rollbacks == 1


def test_product_index_uses_downloaders_content_addressed_image_cache(tmp_path, monkeypatch):
    import hashlib

    image_url = "https://catalog.example/ring.webp?variant=1"
    image_path = tmp_path / (hashlib.sha256(image_url.encode()).hexdigest() + ".webp")
    image_path.write_bytes(b"image")
    assert cached_product_image_path(image_url, tmp_path) == image_path
    assert cached_product_image_path("https://catalog.example/no-image", tmp_path) is None
