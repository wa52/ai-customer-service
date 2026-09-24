# Project State

Last reviewed: 2026-09-24 (Loop iterations: gateway price routing; test isolation)

Current Phase: Phase 3 — Vision Product Search (acceptance in progress)

Current Goal: 证明 SKU 关联商品图向量检索在真实 PostgreSQL 上可重复索引、可搜索、可评估，并能对低置信度/非珠宝输入安全拒绝。

## Completed implementation (not phase acceptance)

- SKU 关联的 `product_image_embeddings` PostgreSQL migration，CLIP 向量检索和旧视觉向量回退路径。
- 图片向量索引脚本、缓存图片路径及上传搜索结果商品卡片/购买链接。
- Phase 3 相关单元/接口测试已添加。

## Verified evidence and gaps

- Latest repository commit: `9e8f3dd` (`SmartCustomerService: 图片找款关联商品SKU`).
- Earlier targeted verification: 22 Phase 3 backend tests passed; frontend production build passed; local cached CLIP successfully produced one 512-dimensional normalized embedding.
- Current Gateway/Chat regression command: `backend\\.venv313\\Scripts\\python.exe -m pytest tests/test_gateway.py tests/test_chat.py -q` — 27 passed, including exact SKU boundaries, Chinese-adjacent SKU strings, `quote`, no-SKU and mixed category/price cases. Independent Verifier accepted the fix.
- Admin API-key test now points `LOCALAPPDATA` at pytest's per-test `tmp_path`; full backend suite using `.venv313` and `--basetemp=.pytest-loop-tmp` passed 34/34. Independent Verifier accepted the test-isolation change; FAIL-0002 is closed.
- Running the full suite using `.venv` is not a valid baseline in this checkout: that environment lacks `psycopg`, causing three Vision test setup failures; use `.venv313` for current verification.
- `FAIL-0004` tracks the stale `.venv`; `psycopg[binary]` is declared in `backend/pyproject.toml`, and `.venv313` is the verified environment for this run.
- Read-only local PostgreSQL probe still fails password authentication for user `postgres`; migration and actual SKU image-vector indexing therefore remain unverified/not completed. No database writes were attempted and no credentials were recorded.
- No 100-image labeled retrieval evaluation, low-confidence rejection evaluation, performance report, or full image-search E2E evidence is recorded yet.

## Current status

- Phase 1: implementation substantially present; not re-audited under this independent acceptance process.
- Phase 2: PostgreSQL repositories/import paths present; environment-level data readiness is not fully evidenced.
- Phase 3: `ACTIVE`, not complete. Database authentication is a blocker for live migration/indexing until credentials are restored/configured.
- Phase 4: `PLANNED`; current Knowledge search is not full RAG.

## Next Task

Next: human action required — restore/configure PostgreSQL credentials outside tracked files. After that, perform a read-only identity check and only then ask for approval to run the product-image migration/indexing. No database write is authorized by this loop turn.

## Known risks

- In-memory or local environment readiness can be mistaken for production readiness.
- CLIP cosine similarity has not yet been calibrated as a rejection threshold on a labeled jewelry/non-jewelry evaluation set.
- Public reference prices and dataset images must retain source/licensing labels and must not be presented as company-authoritative data.
- Legacy dataset-vector fallback can return dataset matches that are not purchasable product SKUs; UI and response must preserve this distinction.
