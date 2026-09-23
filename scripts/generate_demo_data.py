"""Generate deterministic, clearly labelled demo data for local acceptance tests."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE_NAME = "Synthetic demo seed"
SOURCE_URL = "https://github.com/wa52/ai-customer-service/tree/main/data"
CATEGORIES = ["ring", "necklace", "earring", "bracelet"]
COLORS = ["silver", "black", "gold", "rose gold"]
STYLES = ["simple", "vintage", "geometric", "minimal", "statement"]
MATERIALS = ["316L", "304 stainless steel"]


def products() -> list[dict[str, object]]:
    rows = []
    for index in range(1, 121):
        category = CATEGORIES[(index - 1) % len(CATEGORIES)]
        color = COLORS[(index - 1) % len(COLORS)]
        rows.append({
            "external_id": f"DEMO-{category[:3].upper()}-{index:04d}",
            "name": f"Demo {STYLES[(index - 1) % len(STYLES)].title()} {category.title()} {index:04d}",
            "category": category,
            "material": MATERIALS[(index - 1) % len(MATERIALS)],
            "plating": "PVD" if color != "silver" else "none",
            "color": color,
            "size": "adjustable" if category in {"ring", "bracelet"} else "standard",
            "style": STYLES[(index - 1) % len(STYLES)],
            "gender": "unisex",
            "stone": "none",
            "moq": 50 + ((index - 1) % 6) * 50,
            "reference_price": round(1.8 + ((index * 37) % 190) / 10, 2),
            "currency": "USD",
            "image_url": "",
            "source_url": SOURCE_URL,
            "source_name": SOURCE_NAME,
            "data_kind": "synthetic_demo",
            "is_external_reference": "false",
        })
    return rows


def write_products(rows: list[dict[str, object]]) -> None:
    path = DATA / "products" / "products_public.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with (DATA / "products" / "external_prices.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["external_id", "reference_price", "currency", "price_basis", "source_url", "source_name", "retrieved_at", "data_kind", "is_external_reference"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({"external_id": row["external_id"], "reference_price": row["reference_price"], "currency": "USD", "price_basis": "synthetic demo reference", "source_url": SOURCE_URL, "source_name": SOURCE_NAME, "retrieved_at": "2026-09-24", "data_kind": "synthetic_demo", "is_external_reference": "false"})


def write_knowledge() -> None:
    knowledge_dir = DATA / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    materials = []
    for index in range(1, 61):
        material = "316L" if index % 2 else "304 stainless steel"
        materials.append({"id": f"demo-material-{index:03d}", "topic": "materials", "question": f"What should I confirm about {material} jewelry?", "answer": "Demo guidance: confirm the material grade, finish, dimensions, and test documents with sales before making a compliance or performance claim. This is synthetic demo knowledge, not a certificate.", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_kind": "synthetic_demo", "is_external_reference": False})
    faq = []
    for index in range(1, 41):
        faq.append({"id": f"demo-faq-{index:03d}", "topic": "faq", "question": f"Can sample request {index} be confirmed?", "answer": "Demo guidance: collect the target SKU, quantity, finish, delivery destination, and requested date, then route the request to sales for confirmation.", "source_name": SOURCE_NAME, "source_url": SOURCE_URL, "data_kind": "synthetic_demo", "is_external_reference": False})
    for filename, rows in (("materials.jsonl", materials), ("faq.jsonl", faq)):
        with (knowledge_dir / filename).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_vision() -> None:
    path = DATA / "vision" / "image_metadata.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        fields = ["image_id", "category", "license", "dataset_name", "source_url", "data_kind", "is_external_reference"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for index in range(1, 201):
            writer.writerow({"image_id": f"DEMO-IMAGE-{index:04d}", "category": CATEGORIES[(index - 1) % len(CATEGORIES)], "license": "synthetic_demo", "dataset_name": "Synthetic demo metadata", "source_url": SOURCE_URL, "data_kind": "synthetic_demo", "is_external_reference": "false"})


if __name__ == "__main__":
    rows = products()
    write_products(rows)
    write_knowledge()
    write_vision()
    print(f"Generated {len(rows)} products, 100 knowledge/FAQ entries, and 200 vision metadata rows.")
