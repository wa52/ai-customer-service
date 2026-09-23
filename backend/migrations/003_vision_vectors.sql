CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE vision_metadata ADD COLUMN IF NOT EXISTS embedding vector(512);
CREATE INDEX IF NOT EXISTS idx_vision_embedding ON vision_metadata USING hnsw (embedding vector_cosine_ops) WHERE embedding IS NOT NULL;
