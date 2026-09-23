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

The current seed package contains 1000 synthetic product records, 1000 synthetic reference-price records, 200 synthetic material/process/compliance/care records, 100 synthetic FAQ records, 75 synthetic MOQ/procurement records, and 6157 synthetic vision metadata records. These make the Phase 2–4 flows testable without claiming that synthetic rows are company inventory or public-market facts. `data_kind=synthetic_demo` and `is_external_reference=false` identify them.
