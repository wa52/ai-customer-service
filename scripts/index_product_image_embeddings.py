"""Index cached public product images as SKU-linked CLIP vectors in PostgreSQL."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

from app.config.settings import get_settings
from app.vision.clip_embeddings import ClipEmbedder
from app.vision.product_images import cached_product_image_path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "data" / "products" / "images"
MIGRATION = ROOT / "backend" / "migrations" / "004_product_image_embeddings.sql"
BATCH_SIZE = 32
UPSERT_SQL = """INSERT INTO product_image_embeddings
    (sku, image_url, model_name, model_revision, embedding)
    VALUES (%s, %s, %s, %s, %s)
    ON CONFLICT (sku) DO UPDATE SET
        image_url=EXCLUDED.image_url,
        model_name=EXCLUDED.model_name,
        model_revision=EXCLUDED.model_revision,
        embedding=EXCLUDED.embedding,
        updated_at=now()"""


def main() -> None:
    database_url = os.environ.get("DATABASE_URL") or get_settings().database_url
    embedder = ClipEmbedder()
    indexed = skipped_missing = skipped_current = 0

    with psycopg.connect(database_url) as connection:
        connection.execute(MIGRATION.read_text(encoding="utf-8"))
        connection.commit()
        products = connection.execute(
            """SELECT p.sku, p.image_url,
                      (e.sku IS NOT NULL AND e.image_url = p.image_url
                       AND e.model_name = %s AND e.model_revision = %s) AS is_current
               FROM products AS p
               LEFT JOIN product_image_embeddings AS e ON e.sku = p.sku
               WHERE p.image_url IS NOT NULL AND btrim(p.image_url) <> ''
               ORDER BY p.sku""",
            [embedder.model_name, embedder.revision],
        ).fetchall()
        connection.commit()

    pending_rows: list[tuple[object, ...]] = []
    for sku, image_url, is_current in products:
        if is_current:
            skipped_current += 1
            continue
        path = cached_product_image_path(image_url, IMAGE_DIR)
        if path is None:
            skipped_missing += 1
            continue
        embedding = embedder.image(path)
        pending_rows.append(
            (sku, image_url, embedder.model_name, embedder.revision, embedding)
        )
        indexed += 1
        if len(pending_rows) >= BATCH_SIZE:
            _write_batch(database_url, pending_rows)
            pending_rows.clear()
            print(f"indexed {indexed}; current {skipped_current}; missing cached image {skipped_missing}", flush=True)

    if pending_rows:
        _write_batch(database_url, pending_rows)

    print(
        f"Done: indexed {indexed}, already current {skipped_current}, "
        f"missing cached image {skipped_missing}; product rows {len(products)}."
    )


def _write_batch(database_url: str, rows: list[tuple[object, ...]]) -> None:
    with psycopg.connect(database_url) as connection:
        register_vector(connection)
        with connection.cursor() as cursor:
            cursor.executemany(UPSERT_SQL, rows)
        connection.commit()


if __name__ == "__main__":
    main()
