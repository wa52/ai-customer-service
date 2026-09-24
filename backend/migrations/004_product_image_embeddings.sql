CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS product_image_embeddings (
    sku TEXT PRIMARY KEY REFERENCES products (sku) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_revision TEXT NOT NULL,
    embedding vector(512) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_product_image_embedding_hnsw
    ON product_image_embeddings USING hnsw (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_product_image_embedding_model
    ON product_image_embeddings (model_name, model_revision);
