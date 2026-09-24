# Failure and Blocker Ledger

Entries are append-only in spirit: close with evidence; do not erase history. `OPEN` includes unresolved environmental blockers and failures awaiting triage. Dates use ISO format.

## FAIL-0001

- Task: Phase 3 product-image embedding database activation
- Date: 2026-09-24
- Stage: Integration / Deployment
- Type: `DEPLOYMENT`
- Failure: Local PostgreSQL connection failed password authentication for user `postgres`; migration `004_product_image_embeddings.sql` and actual product-image vector indexing were not run against the target database.
- Root cause: Local database credential is unknown, invalid, or out of sync; exact cause not established. Never store the password in this repository.
- Evidence: Connection attempt returned password authentication failure; no migration/index write was performed.
- Required next step: Project owner restores/configures credentials outside tracked files; operator confirms the target database identity and connectivity before any write.
- Regression / closure evidence: Successful authenticated read-only identity check, followed by owner-approved migration/index run with indexed/skipped/failed counts and a repeat run proving idempotent skip behavior.
- Status: `OPEN — requires project owner credential recovery`

## FAIL-0002

- Task: Admin settings test isolation
- Date: 2026-09-24
- Stage: Test
- Type: `TEST`
- Failure: `test_admin_config_never_exposes_api_key` writes to `C:\Users\feng\AppData\Local\SmartCustomerService\admin-config.json` and raises `PermissionError` in this environment.
- Root cause: The test uses the real per-user persistence path rather than an isolated temporary config path; the destination is not writable in this host.
- Evidence: Before the patch, isolated and full-suite runs failed at `save_admin_settings` with `PermissionError`. The test now sets `LOCALAPPDATA` to its pytest `tmp_path`; isolated test passed, and the full suite passed 34 tests using a dedicated project-local pytest temp root.
- Fix: Isolate only the test's persistence directory; production settings persistence is unchanged.
- Regression test: `backend\\.venv313\\Scripts\\python.exe -m pytest -q --basetemp=.pytest-loop-tmp` — 34 passed.
- Status: `RESOLVED — independent acceptance PASS`

## FAIL-0003

- Task: Deterministic gateway SKU price routing
- Date: 2026-09-24
- Stage: Test / Functional
- Type: `FUNCTIONAL`
- Failure: A request asking “What is the price of R1001?” returned the generic prompt asking for a SKU instead of invoking `get_product_price`.
- Root cause: Generic price-question response ran before SKU extraction and tool routing.
- Evidence: Original isolated test failed with `IndexError` because no tool call was returned. Independent reviews additionally found substring SKU matching (`R1001` inside `R10010`), `quote` synonym handling, category routing precedence, and Unicode `\\b` rejecting Chinese-adjacent SKUs. Regression tests initially failed for each reported case; after fixes, `test_gateway.py` and `test_chat.py` passed 27 tests. Full `.venv313` suite now passes 34 tests.
- Fix: Prioritize SKU-specific price lookup ahead of category browsing; use ASCII-only SKU boundaries so Chinese text can touch the identifier without making a false prefix match; support `quote`; assert the exact SKU argument and add no-SKU/longer-identifier/mixed-intent/Chinese cases.
- Regression test: `backend\\.venv313\\Scripts\\python.exe -m pytest tests/test_gateway.py tests/test_chat.py -q` — 27 passed.
- Status: `RESOLVED — independent acceptance PASS`

## FAIL-0004

- Task: Backend development environment parity
- Date: 2026-09-24
- Stage: Test
- Type: `DEPLOYMENT`
- Failure: Running the full suite from `backend\\.venv` produced three Vision test setup failures because `psycopg` is not installed in that virtual environment.
- Root cause: The local `.venv` is stale/incompletely provisioned; `psycopg[binary]` is declared in `backend/pyproject.toml`. The `.venv313` environment has the required dependency and runs the suite successfully.
- Evidence: `.venv` emitted `ModuleNotFoundError: No module named 'psycopg'`; `.venv313` full suite passed 34 tests.
- Required next step: Re-sync or recreate `.venv` from the declared project dependencies if it remains the documented developer environment; until then use `.venv313`.
- Regression test: Full backend suite in the selected canonical virtual environment.
- Status: `OPEN — local environment drift; non-blocking while .venv313 is used`
