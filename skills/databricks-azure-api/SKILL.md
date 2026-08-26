---
name: databricks-azure-api
description: >-
  Build Next.js / Node.js (Azure Web Apps) features on top of the Azure Databricks
  REST API: run SQL via the Statement Execution API, query materialized views and
  metric views (MEASURE syntax), power "ask your data" chat with the Genie
  Conversation API, manage SQL warehouses, saved Queries, and Alerts V2, read/write
  files in Unity Catalog volumes, and write app data back to Lakebase (managed
  Postgres) with synced tables. Use this skill whenever the user mentions
  Databricks, Genie, Lakebase, SQL warehouses, Unity Catalog, metric views,
  materialized views, statement execution, or wants a web app / API route /
  dashboard / chat feature that reads or writes Databricks data — even if they
  don't name a specific Databricks API. Also use it for Databricks auth questions
  (Entra service principal OAuth, managed identity, PATs) from server-side apps.
compatibility: Requires network access to the Databricks workspace. Examples are TypeScript (Node 18+, native fetch).
---

# Azure Databricks REST API for Next.js / Node.js apps

This skill documents the **current, non-deprecated** Azure Databricks workspace REST API surface for building data-backed web apps. Everything here assumes server-side code (Next.js API routes / server actions / Node services) — **never call Databricks from the browser**; tokens must not reach the client.

## How to use this skill

The `references/` folder contains eight deep-dive documents. Read only the ones the task needs — each is self-contained with endpoint tables, TypeScript examples, and a Gotchas section:

| Task involves | Read |
|---|---|
| Auth setup: service principal OAuth (Databricks-native or Entra), managed identity, PATs, granting permissions | `references/auth.md` |
| Running SQL, parameterized queries, fetching large results, querying materialized/metric views | `references/statement-execution.md` |
| Creating/starting/sizing SQL warehouses, serverless config, CAN_USE permissions, cold-start handling | `references/warehouses.md` |
| Natural-language Q&A / chat over data (Genie spaces, conversations, messages, attachments, result download) | `references/genie.md` |
| Saved queries CRUD, alert rules (thresholds, schedules, notifications) | `references/queries-alerts.md` |
| Uploading/downloading files in Unity Catalog volumes; what metric & materialized views are and how they refresh | `references/files-views.md` |
| App writeback to Postgres (Lakebase): instances, OAuth-token credentials, `pg` pooling, synced tables | `references/lakebase.md` |
| Cross-cutting: retry/429 handling, pagination, error mapping, caching, env-var checklist, security checklist | `references/app-architecture.md` |

For any multi-part build (e.g. "dashboard + chat + writeback"), read `references/app-architecture.md` first — it has the client wrapper and the decision matrix — then the per-API docs.

## Choosing the right API (summary)

- **App-defined SQL** (dashboards, reports, exports) → Statement Execution API. The default read path.
- **Natural-language questions** from users → Genie Conversation API (poll message status → read attachments → fetch query result).
- **Analyst-curated SQL** managed in the Databricks UI → Queries API for CRUD, then execute the query text via Statement Execution (the Queries API does not execute).
- **Low-latency / high-QPS operational reads or app-owned writable state** → Lakebase Postgres over the `pg` wire protocol, with synced tables mirroring UC data.
- **Raw files** (uploads, artifacts) ≤5 GiB → Files API against `/Volumes/...` paths.
- **Threshold monitoring with notifications** → Alerts V2.

Materialized views and metric views are queried like tables through Statement Execution; metric views use `SELECT dim, MEASURE(measure_name) ... GROUP BY dim`.

## Core rules (apply to every integration)

1. **Auth**: prefer a Microsoft Entra service principal with OAuth M2M. Two flavors — Databricks-native (`POST https://<workspace>/oidc/v1/token`, `scope=all-apis`) or Entra `client_credentials` with scope `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default`. Managed identity works from Azure Web Apps with no secret. PATs are a dev shortcut only. Always cache tokens with expiry slack (helper in `references/auth.md` §4).
2. **Parameterize SQL** with the Statement Execution API's typed named `parameters` field — never string-interpolate user input into SQL.
3. **Handle 429/503** with `Retry-After` + exponential backoff; Databricks publishes no numeric rate limits. Use the `DatabricksClient` wrapper in `references/app-architecture.md` §3.
4. **Expect async**: statements and Genie messages are poll-until-terminal. Results expire (statement results ~1 h, external links ≤15 min, Genie results can return `QUERY_RESULT_EXPIRED`). Fetch promptly; re-execute when expired.
5. **Avoid deprecated surfaces**: legacy `/api/2.0/preview/sql/queries|alerts|dashboards`, DBFS file APIs, and Jobs 2.0/2.1 are out. Each reference doc lists the legacy API it replaces.
6. **Least privilege**: the SP needs warehouse `CAN_USE`, Genie space `CAN_RUN`, UC `USE CATALOG`/`USE SCHEMA`/`SELECT` on queried objects, and volume `READ/WRITE VOLUME` for files. Grant recipes in `references/auth.md` §7.

## Quickstart shape

Every call follows this pattern (full wrapper in `references/app-architecture.md`):

```typescript
const host = process.env.DATABRICKS_HOST!; // https://adb-....azuredatabricks.net
const res = await fetch(`${host}/api/2.0/sql/statements`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    statement: "SELECT region, MEASURE(total_deposits) AS deposits FROM finance.metrics.deposit_metrics WHERE as_of_date = :as_of GROUP BY region",
    parameters: [{ name: "as_of", value: "2026-08-08", type: "DATE" }],
    warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID!,
    wait_timeout: "30s",
    on_wait_timeout: "CONTINUE",
  }),
});
```

Standard env vars: `DATABRICKS_HOST`, `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET` (or managed identity), `DATABRICKS_WAREHOUSE_ID`, `DATABRICKS_GENIE_SPACE_ID`, `LAKEBASE_HOST`/`LAKEBASE_DATABASE` as applicable — full checklist in `references/app-architecture.md` §10.
