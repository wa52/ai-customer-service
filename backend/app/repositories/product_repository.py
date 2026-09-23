import csv
from pathlib import Path
from typing import Protocol


class ProductRepository(Protocol):
    def search(self, conditions: dict[str, object]) -> list[dict[str, object]]: ...

    def get(self, sku: str) -> dict[str, object] | None: ...


class CsvProductRepository:
    def __init__(self, path: Path) -> None:
        self.products = self._load(path)

    @staticmethod
    def _load(path: Path) -> list[dict[str, object]]:
        if not path.exists():
            return []
        with path.open(newline="", encoding="utf-8-sig") as handle:
            products: list[dict[str, object]] = []
            for row in csv.DictReader(handle):
                products.append({
                    "sku": row.get("external_id", ""),
                    "name": row.get("name", ""),
                    "category": row.get("category", ""),
                    "material": row.get("material", ""),
                    "plating": row.get("plating", ""),
                    "color": row.get("color", ""),
                    "size": row.get("size", ""),
                    "style": row.get("style", ""),
                    "gender": row.get("gender", ""),
                    "stone": row.get("stone", ""),
                    "moq": int(row["moq"]) if row.get("moq", "").isdigit() else None,
                    "reference_price": float(row["reference_price"]) if row.get("reference_price") else None,
                    "currency": row.get("currency", ""),
                    "image_url": row.get("image_url", ""),
                    "source_url": row.get("source_url", ""),
                    "source_name": row.get("source_name", ""),
                    "data_kind": row.get("data_kind", "external_reference"),
                    "is_external_reference": row.get("is_external_reference", "true").lower() == "true",
                })
            return products

    def search(self, conditions: dict[str, object]) -> list[dict[str, object]]:
        return [product for product in self.products if all(product.get(key) == value for key, value in conditions.items() if value is not None and key in product)]

    def get(self, sku: str) -> dict[str, object] | None:
        return next((product for product in self.products if str(product.get("sku", "")).upper() == sku.upper()), None)


class PostgresProductRepository:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def search(self, conditions: dict[str, object]) -> list[dict[str, object]]:
        clauses = ["TRUE"]
        values: list[object] = []
        for key in ("category", "material", "color", "style", "gender"):
            if conditions.get(key) is not None:
                clauses.append(f"{key} = %s")
                values.append(conditions[key])
        query = "SELECT sku, name, category, material, plating, color, size, style, gender, stone, moq, reference_price, currency, image_url, source_url, source_name, data_kind, is_external_reference FROM products WHERE " + " AND ".join(clauses) + " ORDER BY sku LIMIT 100"
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, values)
            return [self._normalize(dict(row)) for row in cursor.fetchall()]

    def get(self, sku: str) -> dict[str, object] | None:
        query = "SELECT sku, name, category, material, plating, color, size, style, gender, stone, moq, reference_price, currency, image_url, source_url, source_name, data_kind, is_external_reference FROM products WHERE upper(sku) = upper(%s)"
        with self._connect() as connection, connection.cursor() as cursor:
            cursor.execute(query, [sku])
            row = cursor.fetchone()
            return self._normalize(dict(row)) if row else None

    @staticmethod
    def _normalize(row: dict[str, object]) -> dict[str, object]:
        if row.get("reference_price") is not None:
            row["reference_price"] = float(row["reference_price"])
        return row

    def _connect(self):
        import psycopg

        return psycopg.connect(self.database_url, row_factory=psycopg.rows.dict_row)
