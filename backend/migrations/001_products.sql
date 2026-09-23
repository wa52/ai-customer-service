CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    material TEXT,
    plating TEXT,
    color TEXT,
    size TEXT,
    style TEXT,
    gender TEXT,
    stone TEXT,
    moq INTEGER,
    reference_price NUMERIC(12, 2),
    currency TEXT,
    image_url TEXT,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    data_kind TEXT NOT NULL,
    is_external_reference BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_category_material ON products (category, material);
CREATE INDEX IF NOT EXISTS idx_products_source ON products (source_name, data_kind);
