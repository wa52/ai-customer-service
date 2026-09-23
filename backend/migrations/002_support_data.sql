CREATE TABLE IF NOT EXISTS product_prices (
    sku TEXT PRIMARY KEY,
    reference_price NUMERIC(12, 2),
    currency TEXT NOT NULL,
    price_basis TEXT NOT NULL,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    retrieved_at DATE,
    data_kind TEXT NOT NULL,
    is_external_reference BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS knowledge_documents (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    is_external_reference BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS vision_metadata (
    image_id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    license TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    image_path TEXT NOT NULL,
    description TEXT NOT NULL,
    source_url TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    is_external_reference BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_knowledge_topic ON knowledge_documents (topic);
CREATE INDEX IF NOT EXISTS idx_vision_category ON vision_metadata (category);
