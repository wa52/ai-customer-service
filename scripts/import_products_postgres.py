"""Import the source-backed CSV catalog into PostgreSQL after applying migrations."""

import csv
import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "products" / "products_public.csv"
MIGRATION = ROOT / "backend" / "migrations" / "001_products.sql"


def main() -> None:
    database_url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/customer_service")
    with psycopg.connect(database_url) as connection:
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
        with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            connection.execute(
                """INSERT INTO products (sku, name, category, material, plating, color, size, style, gender, stone, moq, reference_price, currency, image_url, source_url, source_name, data_kind, is_external_reference)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (sku) DO UPDATE SET name=EXCLUDED.name, category=EXCLUDED.category, material=EXCLUDED.material, plating=EXCLUDED.plating, color=EXCLUDED.color, size=EXCLUDED.size, style=EXCLUDED.style, gender=EXCLUDED.gender, stone=EXCLUDED.stone, moq=EXCLUDED.moq, reference_price=EXCLUDED.reference_price, currency=EXCLUDED.currency, image_url=EXCLUDED.image_url, source_url=EXCLUDED.source_url, source_name=EXCLUDED.source_name, data_kind=EXCLUDED.data_kind, is_external_reference=EXCLUDED.is_external_reference, updated_at=now()""",
                [row.get(field) or None for field in ("external_id", "name", "category", "material", "plating", "color", "size", "style", "gender", "stone", "moq", "reference_price", "currency", "image_url", "source_url", "source_name", "data_kind", "is_external_reference")],
            )
    print(f"Imported {len(rows)} products into PostgreSQL.")


if __name__ == "__main__":
    main()
