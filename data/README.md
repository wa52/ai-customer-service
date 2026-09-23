# Public demo data

This directory contains public-reference data for Phase 2–4 demonstrations.
It is never treated as the company's own SKU, inventory, formal quote, or delivery promise.

Every imported record must keep `source_name`, `source_url`, `retrieved_at`, and `is_external_reference=true`.

## Layout

- `products/products_public.csv`: public catalog records and reference prices
- `products/external_prices.csv`: market reference prices kept separate from product facts
- `vision/image_metadata.csv`: image IDs, labels, dataset license, and source URL
- `knowledge/*.jsonl`: material, process, compliance, care, and FAQ chunks
- `sources/sources.json`: source registry and usage notes

Replace these files with company exports later; Runtime and ToolRegistry should not need to change.

The current package uses source-backed records only: the Jewena merchant feed supplies the product and public-price rows, Outokumpu and Jewena pages supply knowledge records, and the Hugging Face dataset supplies 6,156 downloaded image files and metadata. The image archive is intentionally ignored by Git because it is about 405 MB; `scripts/import_real_vision_metadata.py` indexes the local download. The first vision search is metadata keyword matching; embeddings can be added later without replacing the source data.
