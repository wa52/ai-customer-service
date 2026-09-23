import csv
import json
from pathlib import Path
from typing import Any

from app.capabilities.product import ProductCapability
from app.schemas.runtime import CapabilityResult


DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


def _source_name(row: dict[str, Any], fallback: str) -> str:
    return str(row.get("source_name") or fallback)


def load_public_products() -> list[dict[str, object]]:
    path = DATA_ROOT / "products" / "products_public.csv"
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        rows: list[dict[str, object]] = []
        for row in csv.DictReader(handle):
            rows.append(
                {
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
                    "source_name": _source_name(row, "public_seed"),
                    "data_kind": row.get("data_kind", "external_reference"),
                    "is_external_reference": row.get("is_external_reference", "true").lower() == "true",
                }
            )
        return rows


class PublicProductCapability(ProductCapability):
    def __init__(self) -> None:
        super().__init__(load_public_products(), source="public_product_catalog")


class PublicPricingCapability:
    def __init__(self) -> None:
        self.prices: dict[str, dict[str, object]] = {}
        path = DATA_ROOT / "products" / "external_prices.csv"
        if path.exists():
            with path.open(newline="", encoding="utf-8-sig") as handle:
                for row in csv.DictReader(handle):
                    if row.get("external_id") and row.get("reference_price"):
                        self.prices[row["external_id"].upper()] = {
                            "unit_price": float(row["reference_price"]),
                            "currency": row.get("currency") or "USD",
                            "source_name": _source_name(row, "public_seed"),
                            "source_url": row.get("source_url", ""),
                            "data_kind": row.get("data_kind", "external_reference"),
                            "is_external_reference": row.get("is_external_reference", "true").lower() == "true",
                        }

    def quote(self, sku: str, quantity: int | None = None) -> CapabilityResult:
        price = self.prices.get(sku.upper())
        if price is None:
            return CapabilityResult(success=False, error={"code": "PRICE_NOT_FOUND", "message": "No public reference price is available for this SKU"}, sources=["public_reference_price"])
        return CapabilityResult(success=True, data={**price, "sku": sku.upper(), "quantity": quantity, "is_external_reference": True, "note": "Public reference price only; not a company quote."}, confidence=0.7, sources=["public_reference_price"])

    def quote_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        quantity = arguments.get("quantity")
        return self.quote(str(arguments.get("sku", "")), int(quantity) if quantity is not None else None)


def _load_jsonl(filename: str) -> list[dict[str, Any]]:
    path = DATA_ROOT / "knowledge" / filename
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class PublicKnowledgeCapability:
    def __init__(self) -> None:
        self.entries = [entry for path in sorted((DATA_ROOT / "knowledge").glob("*.jsonl")) for entry in _load_jsonl(path.name)]

    def answer(self, question: str) -> CapabilityResult:
        terms = {term.lower() for term in question.split() if len(term) > 2}
        matches = [entry for entry in self.entries if terms & {term.lower() for term in str(entry.get("question", "")).split()}]
        if not matches:
            return CapabilityResult(success=False, error={"code": "KNOWLEDGE_NOT_FOUND", "message": "No public reference answer matched"}, sources=["public_knowledge"])
        entry = matches[0]
        return CapabilityResult(success=True, data={"answer": entry.get("answer", ""), "topic": entry.get("topic", ""), "source_name": entry.get("source_name", ""), "source_url": entry.get("source_url", ""), "is_external_reference": True}, confidence=0.8, sources=["public_knowledge"])

    def answer_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.answer(str(arguments.get("question", "")))


class PublicVisionCapability:
    def __init__(self) -> None:
        self.rows: list[dict[str, str]] = []
        path = DATA_ROOT / "vision" / "image_metadata.csv"
        if path.exists():
            with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
                self.rows = list(csv.DictReader(handle))

    def search(self, description: str) -> CapabilityResult:
        terms = {term.lower() for term in description.split() if len(term) > 2}
        matches = []
        for row in self.rows:
            haystack = f"{row.get('category', '')} {row.get('description', '')}".lower()
            score = sum(term in haystack for term in terms)
            if score:
                matches.append({"image_id": row.get("image_id", ""), "category": row.get("category", ""), "image_path": row.get("image_path", ""), "description": row.get("description", ""), "similarity": round(score / max(len(terms), 1), 2), "source_url": row.get("source_url", ""), "is_external_reference": True})
        matches.sort(key=lambda item: item["similarity"], reverse=True)
        return CapabilityResult(success=True, data={"matches": matches[:10], "description": description, "mode": "public_seed", "note": "Metadata keyword matching is active; vector embedding search is a later optimization."}, confidence=0.45 if matches else 0.1, sources=["public_vision_metadata"])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.search(str(arguments.get("description", "")))
