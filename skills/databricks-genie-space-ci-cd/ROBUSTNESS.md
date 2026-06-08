# ROBUSTNESS NOTES — what makes this production-grade

This file documents the hardening decisions so a reviewer (or future agent)
understands *why* the code looks the way it does, and what was verified vs. what
still needs environment confirmation.

## Verified against current Databricks docs (June 2026)

These API shapes were confirmed against the Databricks SDK for Python `w.genie`
reference and the Statement Execution docs — they are NOT guesses:

| Call | Verified detail | Why it matters |
|------|-----------------|----------------|
| `genie.get_space(space_id, include_serialized_space=True)` | The serialized export is **omitted by default**; the flag requires **CAN EDIT**. | Earlier drafts didn't pass the flag and would have gotten an empty export. |
| `genie.update_space(space_id, serialized_space=, warehouse_id=, etag=)` | Supports an **etag** for optimistic concurrency. | We read the live etag, then update with it — a concurrent UI edit makes the update **fail loudly instead of clobbering**. |
| `genie.create_space(warehouse_id, serialized_space, title=, parent_path=)` | Required positional args; not a single blob. | Deploy uses the correct signature. |
| `genie.start_conversation_and_wait(space_id, content)` then `get_message_attachment_query_result(...)` | Result rows at `result.data_array`; generated SQL on the attachment's `query`. | L2b reads both defensively across SDK shapes. |
| `genie.genie_create_eval_run / genie_get_eval_run / genie_list_eval_results` | **Native benchmark evaluation** exists in the platform. | `run_benchmarks.py --native` uses it; the custom harness is the alternative. |
| `statement_execution.execute_statement(... wait_timeout="50s")` | INLINE/JSON_ARRAY caps ~16–25 MiB; status at `.status.state`. | `run_sql` checks state and fails non-SUCCEEDED as PermanentError; DESCRIBE output fits INLINE. |

## Still needs environment confirmation (marked `# >>> ADAPT` in code)

- Exact REST paths in the fallback (`/api/2.0/genie/spaces/...`) — only used if
  the installed SDK lacks a method. Confirm for your API version.
- Native eval result field names (`passed` / `score` / `status`) — read
  defensively, but verify against your SDK build before trusting `--native`.
- UC lineage system-table name for auto-deriving the dependency map.
- Azure DevOps work-item type / area path for your process template.

## Hardening applied in this pass

1. **Typed exceptions** (`_core.py`): `ConfigError` (exit 2, human must fix),
   `TransientError` (retried), `PermanentError` (not retried). Exit codes are
   consistent across all four scripts.
2. **Retry with backoff + jitter** on every network call, only for transient
   classes — `PermanentError`/`ConfigError` never retry (verified by tests).
3. **HTTP status classification** — 429/5xx → transient; 4xx → permanent.
4. **Config validation** — required keys, placeholder detection, and
   **referential integrity** (a space can't depend on an undefined metric view).
   Fails early with a precise message instead of a deep AttributeError.
5. **SQL-injection guard** — catalog/schema/view names are validated as simple
   identifiers before being interpolated into `DESCRIBE` (identifiers can't be
   parameterized).
6. **etag-safe deploys** — concurrent out-of-band edits cause a deploy to fail
   rather than silently overwrite.
7. **Structured logging** via `get_logger` (honors `LOG_LEVEL`), replacing ad-hoc
   prints; CI-friendly format.
8. **Partial-failure exit code** in L2 (code 7) so "no drift, but some objects
   errored" is distinct from "all good" and from "drift found".
9. **Dependency-injectable adapter** — `DatabricksAdapter(client=...)` lets the
   whole suite run against a fake, offline.
10. **72-test pytest suite** — retry logic, error classification, config
    validation, normalization, identifier safety, adapter behavior (incl. etag
    conflict), L1 violation logic, L2b grading, determinism guard, and an L2
    drift-detection integration test.

## Running the tests

```bash
pip install -r requirements-dev.txt
PYTHONPATH=ci python -m pytest          # 72 tests, no live workspace needed
```

The PR pipeline runs this suite as a gate, so a regression in the drift-defense
logic itself blocks merges too.

## Exit-code reference (consistent across scripts)

| Code | Meaning |
|------|---------|
| 0 | success / clean |
| 1 | L1: colocation violations (block the PR) |
| 2 | setup/config error (human must fix config.yaml, env, or layout) |
| 3 | L2: drift found |
| 4 | deploy/export: one or more calls failed |
| 5 | L2b: real benchmark failures (regression/error/bad bench config) |
| 6 | L2b: ONLY non-deterministic benchmarks blocked (pin the date) |
| 7 | L2: no drift, but some objects errored — investigate |
