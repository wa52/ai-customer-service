import csv
import json
from pathlib import Path
from typing import Any

from app.schemas.runtime import CapabilityResult


class PostgresPricingCapability:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def quote(self, sku: str, quantity: int | None = None) -> CapabilityResult:
        import psycopg

        with psycopg.connect(self.database_url, row_factory=psycopg.rows.dict_row) as connection:
            row = connection.execute("SELECT sku, reference_price, currency, price_basis, source_url, source_name, data_kind, is_external_reference FROM product_prices WHERE upper(sku)=upper(%s)", [sku]).fetchone()
        if not row:
            return CapabilityResult(success=False, error={"code": "PRICE_NOT_FOUND", "message": "No PostgreSQL reference price is available for this SKU"}, sources=["postgres_reference_price"])
        data = dict(row)
        if data["reference_price"] is not None:
            data["reference_price"] = float(data["reference_price"])
        data.update({"sku": sku.upper(), "unit_price": data.pop("reference_price"), "quantity": quantity, "is_external_reference": True, "note": "Public reference price only; not a company quote."})
        return CapabilityResult(success=True, data=data, confidence=0.8, sources=["postgres_reference_price"])

    def quote_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        quantity = arguments.get("quantity")
        return self.quote(str(arguments.get("sku", "")), int(quantity) if quantity is not None else None)


class PostgresKnowledgeCapability:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url

    def answer(self, question: str) -> CapabilityResult:
        import psycopg

        terms = [term for term in question.split() if len(term) > 2]
        terms = sorted(terms[:8] or [question], key=len, reverse=True)
        patterns = [f"%{term}%" for term in terms]
        predicates = " OR ".join(["question ILIKE %s", "answer ILIKE %s"] * len(patterns))
        values = [value for pattern in patterns for value in (pattern, pattern)]
        ranking = "CASE " + " ".join("WHEN question ILIKE %s OR answer ILIKE %s THEN %s" for _ in patterns) + " ELSE 999 END"
        ranking_values = [value for index, pattern in enumerate(patterns) for value in (pattern, pattern, index)]
        with psycopg.connect(self.database_url, row_factory=psycopg.rows.dict_row) as connection:
            row = connection.execute(f"SELECT answer, topic, source_name, source_url, data_kind, is_external_reference FROM knowledge_documents WHERE {predicates} ORDER BY {ranking}, id LIMIT 1", values + ranking_values).fetchone()
        if not row:
            return CapabilityResult(success=False, error={"code": "KNOWLEDGE_NOT_FOUND", "message": "No PostgreSQL knowledge record matched"}, sources=["postgres_knowledge"])
        return CapabilityResult(success=True, data=dict(row), confidence=0.8, sources=["postgres_knowledge"])

    def answer_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.answer(str(arguments.get("question", "")))


class PostgresVisionCapability:
    def __init__(self, database_url: str) -> None:
        self.database_url = database_url
        self._embedder = None

    def search(self, description: str) -> CapabilityResult:
        import psycopg

        try:
            from app.vision.clip_embeddings import ClipEmbedder

            if self._embedder is None:
                self._embedder = ClipEmbedder()
            embedding = self._embedder.text(description)
            with psycopg.connect(self.database_url, row_factory=psycopg.rows.dict_row) as connection:
                rows = connection.execute("SELECT image_id, category, image_path, description, source_url, data_kind, is_external_reference, 1 - (embedding <=> %s::vector) AS similarity FROM vision_metadata WHERE embedding IS NOT NULL ORDER BY embedding <=> %s::vector LIMIT 10", [str(embedding), str(embedding)]).fetchall()
            return CapabilityResult(success=True, data={"matches": [dict(row) for row in rows], "description": description, "mode": "pgvector", "note": "CLIP text-to-image vector search."}, confidence=0.8 if rows else 0.2, sources=["postgres_pgvector_vision"])
        except (ImportError, ModuleNotFoundError, FileNotFoundError):
            pass

        terms = [term for term in description.split() if len(term) > 2][:8] or [description]
        patterns = [f"%{term}%" for term in terms]
        predicates = " OR ".join(["category ILIKE %s", "description ILIKE %s"] * len(patterns))
        values = [value for pattern in patterns for value in (pattern, pattern)]
        with psycopg.connect(self.database_url, row_factory=psycopg.rows.dict_row) as connection:
            rows = connection.execute(f"SELECT image_id, category, image_path, description, source_url, data_kind, is_external_reference FROM vision_metadata WHERE {predicates} LIMIT 10", values).fetchall()
        return CapabilityResult(success=True, data={"matches": [dict(row) for row in rows], "description": description, "mode": "postgres_metadata", "note": "PostgreSQL metadata search is active; vector embedding search is a later optimization."}, confidence=0.45 if rows else 0.1, sources=["postgres_vision_metadata"])

    def search_tool(self, arguments: dict[str, object], _state) -> CapabilityResult:
        return self.search(str(arguments.get("description", "")))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
