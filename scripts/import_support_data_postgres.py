"""Import source-backed prices, knowledge and vision metadata into PostgreSQL."""

import csv
import json
import os
from pathlib import Path

import psycopg

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/customer_service")
    with psycopg.connect(url) as connection:
        connection.execute((ROOT / "backend" / "migrations" / "002_support_data.sql").read_text(encoding="utf-8"))
        with (ROOT / "data" / "products" / "external_prices.csv").open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                connection.execute("INSERT INTO product_prices (sku, reference_price, currency, price_basis, source_url, source_name, retrieved_at, data_kind, is_external_reference) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (sku) DO UPDATE SET reference_price=EXCLUDED.reference_price, currency=EXCLUDED.currency, source_url=EXCLUDED.source_url, retrieved_at=EXCLUDED.retrieved_at", [row.get("external_id"), row.get("reference_price") or None, row.get("currency") or "USD", row.get("price_basis") or "", row.get("source_url") or "", row.get("source_name") or "", row.get("retrieved_at") or None, row.get("data_kind") or "external_reference", row.get("is_external_reference", "true").lower() == "true"])
        for path in sorted((ROOT / "data" / "knowledge").glob("*.jsonl")):
            for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()):
                connection.execute("INSERT INTO knowledge_documents (id, topic, question, answer, source_name, source_url, data_kind, is_external_reference) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE SET answer=EXCLUDED.answer, source_url=EXCLUDED.source_url", [row["id"], row.get("topic", ""), row.get("question", ""), row.get("answer", ""), row.get("source_name", ""), row.get("source_url", ""), row.get("data_kind", "external_reference"), bool(row.get("is_external_reference", True))])
        with (ROOT / "data" / "vision" / "image_metadata.csv").open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            for row in csv.DictReader(handle):
                connection.execute("INSERT INTO vision_metadata (image_id, category, license, dataset_name, image_path, description, source_url, data_kind, is_external_reference) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (image_id) DO UPDATE SET description=EXCLUDED.description, image_path=EXCLUDED.image_path", [row.get("image_id"), row.get("category", ""), row.get("license", ""), row.get("dataset_name", ""), row.get("image_path", ""), row.get("description", ""), row.get("source_url", ""), row.get("data_kind", "external_reference"), row.get("is_external_reference", "true").lower() == "true"])
    print("Imported prices, knowledge and vision metadata into PostgreSQL.")


if __name__ == "__main__":
    main()
