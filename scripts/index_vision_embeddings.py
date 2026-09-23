"""Generate CLIP image embeddings for the downloaded real dataset and store them in pgvector."""

import csv
import os
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

from app.vision.clip_embeddings import ClipEmbedder

ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = ROOT / "data" / "vision" / "jewelry-design-dataset" / "dataset"


def main() -> None:
    url = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/customer_service")
    embedder = ClipEmbedder()
    with psycopg.connect(url) as connection:
        connection.execute((ROOT / "backend" / "migrations" / "003_vision_vectors.sql").read_text(encoding="utf-8"))
        connection.commit()
        register_vector(connection)
        with (ROOT / "data" / "vision" / "image_metadata.csv").open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            rows = list(csv.DictReader(handle))
        for index, row in enumerate(rows, start=1):
            path = IMAGE_ROOT / row["image_path"]
            if not path.exists():
                continue
            embedding = embedder.image(path)
            connection.execute("UPDATE vision_metadata SET embedding=%s WHERE image_id=%s", [embedding, row["image_id"]])
            if index % 100 == 0:
                connection.commit()
                print(f"Indexed {index}/{len(rows)} images")
        connection.commit()
    print(f"Completed CLIP indexing for {len(rows)} metadata rows.")


if __name__ == "__main__":
    main()
