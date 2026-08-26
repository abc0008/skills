# Databricks SQL Statement Execution API (Azure) — Reference for Node.js / Next.js apps

> Scope: the **current** Statement Execution API at `/api/2.0/sql/statements` on Azure Databricks.
> This is the primary, supported way for a web backend to run SQL against a **SQL warehouse** over REST.
> Do **not** use the legacy Command Execution API 1.2 (`/api/1.2/commands/*`, cluster-based) — it is a legacy
> predecessor and must not be used for new apps. There is no other deprecated variant of this API; `2.0` is current.

All examples assume:

```ts
const HOST = process.env.DATABRICKS_HOST!; // e.g. "https://adb-1234567890123456.7.azuredatabricks.net"
declare function getToken(): Promise<string>; // returns an AAD/Entra or PAT bearer token
```

---

## Table of contents

1. [Concepts: the hybrid sync/async execution model](#concepts-the-hybrid-syncasync-execution-model)
2. [POST /api/2.0/sql/statements — execute a statement](#post-api20sqlstatements--execute-a-statement)
3. [GET /api/2.0/sql/statements/{statement_id} — poll status / get first chunk](#get-api20sqlstatementsstatement_id--poll-status--get-first-chunk)
4. [GET /api/2.0/sql/statements/{statement_id}/result/chunks/{chunk_index} — fetch result chunks](#get-api20sqlstatementsstatement_idresultchunkschunk_index--fetch-result-chunks)
5. [POST /api/2.0/sql/statements/{statement_id}/cancel — cancel](#post-api20sqlstatementsstatement_idcancel--cancel)
6. [Statement status lifecycle](#statement-status-lifecycle)
7. [Result manifest, schema metadata, and typed row parsing](#result-manifest-schema-metadata-and-typed-row-parsing)
8. [Complete TypeScript helper: `executeStatement(sql, params)`](#complete-typescript-helper-executestatementsql-params)
9. [Parameterized queries (SQL-injection safe)](#parameterized-queries-sql-injection-safe)
10. [Querying materialized views](#querying-materialized-views)
11. [Querying metric views (MEASURE syntax)](#querying-metric-views-measure-syntax)
12. [Limits, timeouts, and polling patterns](#limits-timeouts-and-polling-patterns)
13. [Gotchas](#gotchas)

---

## Concepts: the hybrid sync/async execution model

One POST call can behave synchronously, asynchronously, or as a hybrid, controlled by `wait_timeout` + `on_wait_timeout`:

| Mode | Settings | Behavior |
|---|---|---|
| Synchronous | `wait_timeout: "30s"`, `on_wait_timeout: "CANCEL"` | Call blocks up to 30 s. If the statement finishes in time you get `SUCCEEDED` + results in the same response. If not, the statement is **canceled** and the call returns state `CANCELED`. |
| Asynchronous | `wait_timeout: "0s"` | Returns immediately with a `statement_id` and state `PENDING`. You poll. |
| Hybrid (default) | `wait_timeout: "10s"`, `on_wait_timeout: "CONTINUE"` | Blocks up to 10 s. Fast queries return results directly; slow ones return `statement_id` with `PENDING`/`RUNNING` and keep executing — you poll. |

`wait_timeout` accepts `"0s"` or any value from `"5s"` to `"50s"` (string with `s` suffix). Wait timeouts are approximate, not exact.

Results are fetched either **inline** in the JSON response (`disposition: "INLINE"`) or via **presigned cloud-storage URLs** (`disposition: "EXTERNAL_LINKS"` — on Azure these are Azure storage SAS URLs). Both dispositions return results in **chunks** for large sets.

---

## POST /api/2.0/sql/statements — execute a statement

**Purpose:** submit a SQL statement to a SQL warehouse; optionally wait for the result.

### Request body

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `statement` | string | **yes** | — | The SQL text. May contain named parameter markers `:param_name`. Max query text size: **16 MiB**. |
| `warehouse_id` | string | **yes** | — | ID of the SQL warehouse (pro or serverless). Not a cluster ID. |
| `catalog` | string | no | — | Sets the default catalog for execution (like `USE CATALOG`). |
| `schema` | string | no | — | Sets the default schema (like `USE SCHEMA`). |
| `parameters` | array of `{name, value?, type?}` | no | — | Typed named parameters; see below. |
| `wait_timeout` | string | no | `"10s"` | `"0s"` or `"5s"`–`"50s"`. How long the call blocks waiting for completion. |
| `on_wait_timeout` | string enum | no | `"CONTINUE"` | `"CONTINUE"` (return `statement_id`, keep executing) or `"CANCEL"` (cancel the statement if `wait_timeout` elapses). Only meaningful when `wait_timeout` > 0. |
| `disposition` | string enum | no | `"INLINE"` | `"INLINE"` or `"EXTERNAL_LINKS"`. |
| `format` | string enum | no | `"JSON_ARRAY"` | `"JSON_ARRAY"`, `"ARROW_STREAM"`, `"CSV"`. `ARROW_STREAM` and `CSV` are **only** valid with `EXTERNAL_LINKS`. `JSON_ARRAY` works with both dispositions. |
| `row_limit` | int64 | no | — | Caps the result row count. Unlike SQL `LIMIT`, when the cap trims the result the response manifest sets `truncated: true`. |
| `byte_limit` | int64 | no | — | Caps result size in bytes. Byte counts are based on internal representation and may not match final size in the requested `format`. Sets `truncated: true` when applied. |
| `query_tags` | array of `{key, value}` | no | — | **Public Preview.** Key-value tags for cost attribution / tracing, e.g. `"query_tags": [{"key": "team", "value": "finance"}]`. Each tag object has `key` (string) and `value` (string; omit for a key-only tag, which surfaces with a `null` value). Tags appear in the `query_tags` MAP column of `system.query.history` (query as `query_tags['team']`) and in the Query History UI. Limits: max **20** user tags per statement, key/value each ≤ **128 chars**, keys must not contain `,` `:` `-` `/` `=` `.`, and the `@@` prefix is reserved; violations get sentinel tags (`tag_invalid`, `tag_truncated`, `tags_dropped`) rather than failing the statement. |

Each entry of `parameters`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | Matches `:name` marker in `statement`. |
| `value` | string | no | Always sent as a **string**. Omit it (or send `null`) to bind SQL `NULL`. |
| `type` | string | no | SQL type, e.g. `"INT"`, `"BIGINT"`, `"DOUBLE"`, `"DECIMAL(18,2)"`, `"DATE"`, `"TIMESTAMP"`, `"BOOLEAN"`, `"STRING"`. Defaults to `STRING` if omitted. The value string must be castable to this type (checked with SQL `CAST` semantics); otherwise the statement fails. |

### Disposition / format matrix

| | `INLINE` | `EXTERNAL_LINKS` |
|---|---|---|
| `JSON_ARRAY` | yes (default) | yes (each chunk is a JSON array file at a presigned URL) |
| `ARROW_STREAM` | **no** | yes (Arrow IPC stream — fastest for bulk extraction) |
| `CSV` | **no** | yes (RFC-4180, first line is the header) |
| Max total result size | **25 MiB** — a statement whose result exceeds this is **aborted** and no result is available | **100 GiB** |

### Response body (200)

```jsonc
{
  "statement_id": "01f0-...-uuid",
  "status": { "state": "SUCCEEDED" },          // or PENDING/RUNNING/FAILED/CANCELED/CLOSED
  "manifest": { /* present once SUCCEEDED — see manifest section */ },
  "result":   { /* first chunk (INLINE) or external_links (EXTERNAL_LINKS) */ }
}
```

- Timeout path (hybrid/async): only `statement_id` + `status` are present; poll GET until terminal.
- Failure path: `status.state = "FAILED"` and `status.error = { "error_code": "...", "message": "..." }`.
- The HTTP status is 200 even for SQL failures — inspect `status.state`. HTTP 4xx/5xx indicates request-level problems (bad JSON, bad warehouse ID, auth, rate limit).

### Example (TypeScript, fetch)

```ts
const res = await fetch(`${HOST}/api/2.0/sql/statements`, {
  method: "POST",
  headers: {
    Authorization: `Bearer ${await getToken()}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
    catalog: "main",
    schema: "analytics",
    statement:
      "SELECT o_orderkey, o_totalprice FROM orders WHERE o_totalprice > :min_price AND o_orderdate > :cutoff",
    parameters: [
      { name: "min_price", value: "60000", type: "DECIMAL(18,2)" },
      { name: "cutoff", value: "2024-01-01", type: "DATE" },
    ],
    wait_timeout: "30s",
    on_wait_timeout: "CONTINUE",
    format: "JSON_ARRAY",
    disposition: "INLINE",
    row_limit: 10000,
  }),
});
if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
const body = await res.json();
// body.status.state, body.statement_id, and (if finished) body.manifest / body.result
```

---

## GET /api/2.0/sql/statements/{statement_id} — poll status / get first chunk

**Purpose:** get current status; once `SUCCEEDED`, the response also carries the `manifest` and the **first result chunk** (same shape as the POST response).

- No query parameters; no request body.
- Can be called repeatedly (idempotent). Poll this until `status.state` is terminal.
- After a statement has been in a terminal state for **at least 12 hours**, it is removed and this endpoint returns **HTTP 404**.
- Only the user who executed the statement can fetch its status/results.

```ts
const res = await fetch(`${HOST}/api/2.0/sql/statements/${statementId}`, {
  headers: { Authorization: `Bearer ${await getToken()}` },
});
const body = await res.json();
if (body.status.state === "FAILED") {
  throw new Error(`${body.status.error?.error_code}: ${body.status.error?.message}`);
}
```

---

## GET /api/2.0/sql/statements/{statement_id}/result/chunks/{chunk_index} — fetch result chunks

**Purpose:** fetch chunk `chunk_index` (0-based) of a successful statement's result. Valid only after `SUCCEEDED`.

Response shape is identical to the nested `result` element of the GET-statement response:

- **INLINE:** `{ chunk_index, row_offset, row_count, data_array, next_chunk_index?, next_chunk_internal_link? }`
- **EXTERNAL_LINKS:** `{ external_links: [{ chunk_index, row_offset, row_count, byte_count, external_link, expiration, next_chunk_index?, next_chunk_internal_link? }] }`

Iteration options:

1. Follow `next_chunk_internal_link` (a ready-made relative path like `/api/2.0/sql/statements/{id}/result/chunks/1?row_offset=188416`) until it's absent.
2. Or read `manifest.total_chunk_count` and fetch indexes `0..n-1` — chunk endpoints support **parallel** fetching, which is much faster for big EXTERNAL_LINKS results.

External-link specifics:

- `external_link` is a presigned Azure storage SAS URL. Download it with a plain GET and **no `Authorization` header** — sending your Databricks bearer token to the storage URL will fail the request (and leaks the token).
- Links are short-lived: valid **≤ 15 minutes**; the exact deadline is in `expiration` (ISO timestamp). If a link expires before you downloaded it, call the chunk endpoint again for that `chunk_index` to obtain a fresh link (works while the statement is still open, i.e. within the 1-hour result window).
- Treat SAS URLs as credentials: don't log them, don't send them to the browser unless you intend the client to download directly.

```ts
// EXTERNAL_LINKS: fetch chunk metadata, then download the presigned URL
const meta = await fetch(
  `${HOST}/api/2.0/sql/statements/${statementId}/result/chunks/${i}`,
  { headers: { Authorization: `Bearer ${await getToken()}` } },
).then(r => r.json());

const link = meta.external_links[0];
const data = await fetch(link.external_link); // NOTE: no Authorization header!
const text = await data.text();               // CSV text, or JSON.parse for JSON_ARRAY
```

---

## POST /api/2.0/sql/statements/{statement_id}/cancel — cancel

**Purpose:** request cancellation. Response body is empty; HTTP 200 means the cancel request was received and forwarded — **not** that the statement was canceled.

- Cancellation is best-effort and can silently lose a race with completion: the statement may already have `SUCCEEDED` when the cancel arrives.
- Always poll GET afterwards until a terminal state to learn the true outcome (`CANCELED` vs `SUCCEEDED`/`FAILED`).
- Important: **stopping polling does not cancel a statement.** If your HTTP handler times out or the user navigates away, explicitly call cancel, otherwise the query keeps running (and billing) on the warehouse.

```ts
await fetch(`${HOST}/api/2.0/sql/statements/${statementId}/cancel`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}` },
});
```

---

## Statement status lifecycle

`status.state` values:

| State | Meaning | Terminal? |
|---|---|---|
| `PENDING` | Accepted; waiting for warehouse/queue (warehouse may be auto-starting). | no |
| `RUNNING` | Executing. | no |
| `SUCCEEDED` | Done; result available (manifest + chunks). | yes |
| `FAILED` | Execution error; details in `status.error.error_code` / `status.error.message`. | yes |
| `CANCELED` | Canceled by user request or by `on_wait_timeout: "CANCEL"`. | yes |
| `CLOSED` | Execution succeeded but the result is **no longer available** for fetching (result window expired or statement closed). Re-execute if you still need the data. | yes |

Lifetime rules:

- While a statement is executing, poll its status **at least every 15 minutes** to keep it alive; an abandoned statement can be canceled by the system.
- After success, results are fetchable for **1 hour**; polling does not extend this window. After that the statement transitions toward `CLOSED`.
- After ≥ 12 hours in a terminal state, the statement id disappears entirely (HTTP 404).

---

## Result manifest, schema metadata, and typed row parsing

`manifest` (present when `SUCCEEDED`):

```jsonc
{
  "format": "JSON_ARRAY",
  "schema": {
    "column_count": 3,
    "columns": [
      { "name": "l_orderkey", "position": 0, "type_name": "LONG", "type_text": "BIGINT" },
      { "name": "l_extendedprice", "position": 1, "type_name": "DECIMAL",
        "type_precision": 18, "type_scale": 2, "type_text": "DECIMAL(18,2)" },
      { "name": "l_shipdate", "position": 2, "type_name": "DATE", "type_text": "DATE" }
    ]
  },
  "chunks": [ { "chunk_index": 0, "row_offset": 0, "row_count": 188416, "byte_count": 123 } ],
  "total_chunk_count": 2,
  "total_row_count": 300000,
  "total_byte_count": 94845304,   // EXTERNAL_LINKS
  "truncated": false               // true if row_limit/byte_limit trimmed the result
}
```

Key facts for parsing `JSON_ARRAY` data:

- `result.data_array` is an **array of arrays**; every cell is a **string or `null`** — numbers, booleans, dates, timestamps all arrive as strings. Complex types (`ARRAY`, `STRUCT`, `MAP`) arrive as JSON-encoded strings.
- Column order in each row matches `manifest.schema.columns[i].position`.
- `type_name` values include: `BOOLEAN, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, DECIMAL, STRING, CHAR, BINARY, DATE, TIMESTAMP, INTERVAL, ARRAY, STRUCT, MAP, NULL`. `type_text` is the full SQL type text (use it for display; use `type_name` for conversion logic).
- Beware JS precision: `LONG` (BIGINT) and high-precision `DECIMAL` values can exceed `Number.MAX_SAFE_INTEGER` — keep them as strings or use `BigInt` when exactness matters.

---

## Complete TypeScript helper: `executeStatement(sql, params)`

Submits with a hybrid wait, polls to terminal, fetches **all** chunks, converts values using the manifest schema, and returns rows as objects keyed by column name. Uses only `fetch`.

```ts
// databricks.ts
const HOST = process.env.DATABRICKS_HOST!;            // https://adb-....azuredatabricks.net
const WAREHOUSE_ID = process.env.DATABRICKS_WAREHOUSE_ID!;
declare function getToken(): Promise<string>;          // your AAD / PAT token helper

export interface SqlParam {
  name: string;
  value: string | number | boolean | null;
  type?: string; // "INT", "BIGINT", "DOUBLE", "DECIMAL(18,2)", "DATE", "TIMESTAMP", "BOOLEAN", "STRING"...
}

interface ColumnInfo {
  name: string; position: number; type_name: string; type_text: string;
  type_precision?: number; type_scale?: number;
}
interface ResultChunk {
  chunk_index: number; row_offset: number; row_count: number;
  data_array?: (string | null)[][];
  next_chunk_index?: number; next_chunk_internal_link?: string;
}
interface StatementResponse {
  statement_id: string;
  status: { state: "PENDING"|"RUNNING"|"SUCCEEDED"|"FAILED"|"CANCELED"|"CLOSED";
            error?: { error_code?: string; message?: string } };
  manifest?: { schema: { columns: ColumnInfo[] }; total_chunk_count: number;
               total_row_count: number; truncated: boolean; format: string };
  result?: ResultChunk;
}

export type Row = Record<string, unknown>;

async function dbxFetch(path: string, init?: RequestInit): Promise<any> {
  const res = await fetch(`${HOST}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (res.status === 429 || res.status === 503) {
    const retryAfter = Number(res.headers.get("Retry-After") ?? "2");
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return dbxFetch(path, init);                       // simple retry on throttling
  }
  if (!res.ok) throw new Error(`Databricks ${res.status}: ${await res.text()}`);
  return res.json();
}

function convertCell(raw: string | null, col: ColumnInfo): unknown {
  if (raw === null) return null;
  switch (col.type_name) {
    case "BYTE": case "SHORT": case "INT":
    case "FLOAT": case "DOUBLE":
      return Number(raw);
    case "LONG": {                                     // BIGINT: guard precision
      const n = Number(raw);
      return Number.isSafeInteger(n) ? n : BigInt(raw);
    }
    case "DECIMAL":
      return Number(raw);                              // or keep string / use a Decimal lib
    case "BOOLEAN":
      return raw === "true";
    case "DATE": case "TIMESTAMP":
      return raw;                                      // ISO strings; new Date(raw) if desired
    case "ARRAY": case "STRUCT": case "MAP":
      try { return JSON.parse(raw); } catch { return raw; }
    default:
      return raw;                                      // STRING, CHAR, BINARY(base64), INTERVAL...
  }
}

export async function executeStatement(
  sql: string,
  params: SqlParam[] = [],
  opts: { catalog?: string; schema?: string; rowLimit?: number; timeoutMs?: number } = {},
): Promise<Row[]> {
  const deadline = Date.now() + (opts.timeoutMs ?? 120_000);

  // 1. Submit (hybrid mode: fast queries return inline immediately)
  let st: StatementResponse = await dbxFetch("/api/2.0/sql/statements", {
    method: "POST",
    body: JSON.stringify({
      warehouse_id: WAREHOUSE_ID,
      statement: sql,
      catalog: opts.catalog,
      schema: opts.schema,
      parameters: params.map(p => ({
        name: p.name,
        value: p.value === null ? undefined : String(p.value), // omit => SQL NULL
        type: p.type ?? (typeof p.value === "number" ? "DOUBLE"
              : typeof p.value === "boolean" ? "BOOLEAN" : "STRING"),
      })),
      wait_timeout: "30s",
      on_wait_timeout: "CONTINUE",
      format: "JSON_ARRAY",
      disposition: "INLINE",
      row_limit: opts.rowLimit,
    }),
  });

  // 2. Poll until terminal (statement keeps running server-side meanwhile)
  let delay = 1000;
  while (st.status.state === "PENDING" || st.status.state === "RUNNING") {
    if (Date.now() > deadline) {
      await dbxFetch(`/api/2.0/sql/statements/${st.statement_id}/cancel`, { method: "POST" })
        .catch(() => {});
      throw new Error(`Statement ${st.statement_id} timed out after ${opts.timeoutMs}ms`);
    }
    await new Promise(r => setTimeout(r, delay));
    delay = Math.min(delay * 1.5, 5000);               // capped exponential backoff
    st = await dbxFetch(`/api/2.0/sql/statements/${st.statement_id}`);
  }

  if (st.status.state !== "SUCCEEDED") {
    const e = st.status.error;
    throw new Error(`Statement ${st.status.state}: ${e?.error_code ?? ""} ${e?.message ?? ""}`);
  }

  // 3. Collect all chunks (first chunk rides along with the SUCCEEDED response)
  const columns = st.manifest!.schema.columns;
  const raw: (string | null)[][] = [];
  let chunk: ResultChunk | undefined = st.result;
  while (chunk) {
    if (chunk.data_array) raw.push(...chunk.data_array);
    chunk = chunk.next_chunk_internal_link
      ? await dbxFetch(chunk.next_chunk_internal_link)  // link already includes the path+query
      : undefined;
  }

  // 4. Convert to objects keyed by column name, with type conversion
  return raw.map(cells => {
    const row: Row = {};
    for (const col of columns) row[col.name] = convertCell(cells[col.position], col);
    return row;
  });
}
```

Usage in a Next.js route handler:

```ts
// app/api/orders/route.ts
import { NextResponse } from "next/server";
import { executeStatement } from "@/lib/databricks";

export async function GET(req: Request) {
  const minPrice = new URL(req.url).searchParams.get("minPrice") ?? "0";
  const rows = await executeStatement(
    "SELECT o_orderkey, o_totalprice, o_orderdate FROM main.analytics.orders WHERE o_totalprice > :min_price ORDER BY o_orderdate DESC",
    [{ name: "min_price", value: minPrice, type: "DECIMAL(18,2)" }],
    { rowLimit: 500, timeoutMs: 60_000 },
  );
  return NextResponse.json(rows); // [{ o_orderkey: 7, o_totalprice: 86152.02, o_orderdate: "1996-01-15" }, ...]
}
```

For results larger than 25 MiB, switch the submit body to `disposition: "EXTERNAL_LINKS"` (keep `format: "JSON_ARRAY"` for easy parsing) and in step 3 fetch each chunk's `external_links[0].external_link` **without** the Authorization header, `JSON.parse` the downloaded text, and concatenate.

---

## Parameterized queries (SQL-injection safe)

Never interpolate user input into `statement`. Use `:name` markers plus the `parameters` array — values are bound server-side, typed, and cannot alter query structure:

```ts
// UNSAFE — do not do this:
// const sql = `SELECT * FROM users WHERE email = '${email}'`;

// SAFE:
const rows = await executeStatement(
  "SELECT * FROM main.app.users WHERE email = :email AND created_at >= :since",
  [
    { name: "email", value: email },                       // type defaults to STRING
    { name: "since", value: "2025-01-01", type: "DATE" },
  ],
);
```

Rules:

- `value` is always a JSON string; the server casts it to `type` using SQL `CAST` semantics. An uncastable value fails the statement with an error (it does not silently coerce).
- Omit `value` (or send `null`) to bind SQL `NULL`.
- Markers can appear only where **constants** are allowed. You cannot parameterize identifiers (table/column names) or keywords — validate those against an allow-list in your code instead.
- Named markers only (`:name`); this API does not use positional `?` markers.

---

## Querying materialized views

Materialized views (Unity Catalog MVs created with `CREATE MATERIALIZED VIEW`) are queried **exactly like tables** — no special API features needed:

```ts
const rows = await executeStatement(
  "SELECT region, total_sales FROM main.gold.daily_sales_mv WHERE sale_date = :d",
  [{ name: "d", value: "2026-08-10", type: "DATE" }],
);
```

Notes:

- Query them through a SQL warehouse (which this API always uses) — that's the standard supported path for MVs.
- The querying principal needs `SELECT` on the MV and `USE CATALOG`/`USE SCHEMA` on its parents. You do **not** need access to the MV's underlying base tables.
- Reads reflect the last completed refresh; freshness depends on the MV's refresh schedule, not on your query.

## Querying metric views (MEASURE syntax)

Metric views (Unity Catalog semantic layer) are queried through the same API, but measures must be evaluated with the **`MEASURE()`** aggregate function; dimensions are selected normally and you group by them:

```sql
SELECT
  `Order Month`,
  `Order Status`,
  MEASURE(`Order Count`)   AS order_count,
  MEASURE(`Total Revenue`) AS total_revenue
FROM main.gold.orders_metric_view
GROUP BY ALL
ORDER BY `Order Month`;
```

Confirmed rules (from current docs):

- Every measure reference must be wrapped in `MEASURE(measure_name)`; selecting a measure column directly fails. (On Databricks Runtime 18.1+ compute, `AGG()` is an accepted alias — for SQL-warehouse apps, use `MEASURE()`.)
- `SELECT *` is **not supported** on metric views — list dimensions explicitly and wrap each measure in `MEASURE()`.
- `WHERE` filters on dimensions work normally (filtering happens before measure aggregation): `WHERE \`Order Status\` = 'Fulfilled'`.
- `GROUP BY ALL` is the convenient way to group by all selected dimensions; explicit `GROUP BY dim1, dim2` also works.
- Metric views cannot be **directly joined** to other tables — wrap the metric-view aggregation in a CTE, then join the CTE result to other tables.
- Parameterized metric views are called as table-valued functions with named arguments: `FROM mv_name(param => value)`.
- `DESCRIBE TABLE EXTENDED catalog.schema.mv AS JSON` returns the full YAML definition (useful for discovering measure/dimension names at runtime to build UIs).

Via the API it's just another statement:

```ts
const rows = await executeStatement(
  `SELECT \`Order Month\`, MEASURE(\`Total Revenue\`) AS revenue
   FROM main.gold.orders_metric_view
   WHERE \`Order Status\` = :status
   GROUP BY ALL ORDER BY \`Order Month\``,
  [{ name: "status", value: "Fulfilled" }],
);
```

Note the backticks around display-style names with spaces — escape them properly in TS template strings.

---

## Limits, timeouts, and polling patterns

| Limit / behavior | Value |
|---|---|
| Max query text size | 16 MiB |
| `INLINE` max result size | 25 MiB total — exceeding it **aborts** the statement (no partial result); use `row_limit`/`byte_limit` or `EXTERNAL_LINKS` |
| `EXTERNAL_LINKS` max result size | 100 GiB |
| Presigned (SAS) URL validity | ≤ 15 minutes (`expiration` field per link); re-fetch the chunk for fresh links |
| `wait_timeout` | `0s` or `5s`–`50s` (default `10s`); approximate |
| Keep-alive while executing | poll status at least every **15 minutes** or the statement may be canceled |
| Result availability after success | **1 hour** (not extended by polling); then state becomes `CLOSED` |
| Statement id retention | ≥ 12 hours after terminal state, then HTTP 404 |
| Throttling | 429 (with `Retry-After`) under platform REST rate limits; also expect queuing (`PENDING`) when the warehouse is saturated or auto-starting |

Recommended polling pattern (implemented in the helper above): submit with `wait_timeout: "30s"` + `on_wait_timeout: "CONTINUE"`, then poll GET with ~1 s initial delay and capped exponential backoff (max 5 s), enforce your own overall deadline, and **cancel explicitly** when you give up.

---

### Recommended timeout budgets

Pick the route-level budget from the warehouse type, not a universal constant:

- **Serverless warehouse**: warm queries return in seconds; cold start is typically 5-10 s. A 60 s total budget per route is a sensible default for interactive endpoints.
- **Pro/Classic warehouse**: cold start can take ~4-6 min. Either accept a ~300 s worker budget (background jobs only) or start the warehouse ahead of traffic. Never let an interactive HTTP request ride out a classic cold start.
- **Azure App Service** closes idle HTTP responses at ~230 s — any wait that could exceed that must use the async pattern (return `statement_id`, poll from a second endpoint).
- Always `cancel` the statement when abandoning a wait (client disconnect, budget exceeded) so the warehouse isn't burning compute on a result nobody will read.

### Using `executeStatement` with EXTERNAL_LINKS

The helper above uses `INLINE` for simplicity. For results that may exceed 25 MiB, switch `disposition: "EXTERNAL_LINKS"` and change the chunk step: iterate `manifest.chunks`, GET each `/result/chunks/{index}` to obtain `external_links[0].external_link`, and fetch those URLs **without** the Authorization header (they are presigned SAS URLs; sending a Bearer header to Azure storage fails the request). Links expire in ≤15 min — if a fetch returns 403, re-request that chunk once to get a fresh link (works any time within the 1 h result window). Chunks may be fetched in parallel; keep concurrency modest (4-8) to avoid memory spikes.

## Gotchas

1. **HTTP 200 ≠ success.** SQL errors come back as `200` with `status.state = "FAILED"` and `status.error`. Always branch on `status.state`.
2. **Cold warehouses:** the first query against a stopped serverless/pro warehouse sits in `PENDING` while it starts (seconds for serverless, minutes for pro). Budget your polling deadline accordingly; don't treat a long `PENDING` as failure.
3. **All JSON_ARRAY cells are strings.** `1`, `true`, dates — everything is a string or `null`. Convert using `manifest.schema`; watch `LONG`/`DECIMAL` precision vs. JS `number`.
4. **INLINE over-limit aborts the whole statement.** A >25 MiB result doesn't get truncated — the execution is aborted with no result. Defensive `row_limit`/`byte_limit` on user-facing queries is the cheap fix; `truncated: true` in the manifest tells you a cap fired.
5. **No Authorization header on external links.** Downloading a SAS URL with your Bearer header attached fails. Conversely, chunk-metadata calls to the Databricks host DO need the header. Easy to get wrong with a shared fetch wrapper.
6. **Links expire in ≤ 15 min** and results in 1 hour. Don't stash `external_link` URLs in a job queue for later; fetch promptly, or re-request the chunk to mint fresh links while the statement is open.
7. **Format/disposition are immutable per statement.** You can't re-fetch an INLINE statement's result as CSV; re-execute with the desired settings.
8. **`on_wait_timeout: "CANCEL"` gives you clean sync semantics** for cheap queries (≤ 50 s ceiling), but for anything user-triggered prefer `CONTINUE` + polling so a slow warehouse start doesn't kill the query.
9. **Abandoning ≠ canceling.** If your serverless function times out mid-poll, the statement keeps running and billing. Wire cancellation into request-abort handling (`AbortSignal`) where possible.
10. **Cancel is best-effort.** A 200 from `/cancel` doesn't mean `CANCELED`; poll to a terminal state to learn what actually happened.
11. **`row_limit` vs SQL `LIMIT`:** identical trimming, but only `row_limit` sets `truncated: true` — useful for showing a "results truncated" banner in the UI.
12. **Parameter markers can't replace identifiers.** `:table_name` in `FROM :table_name` is invalid; allow-list identifiers in app code.
13. **Only the submitting principal can read results.** Run all statements as one service principal if multiple app instances/processes need to share statement ids.
14. **Metric views:** no `SELECT *`, no direct joins (CTE first), measures only via `MEASURE()`. Materialized views: plain `SELECT`, permissions on the MV itself suffice.
15. **12-hour 404:** persisted `statement_id`s go stale; handle 404 from GET by treating the statement as gone, not as a transient error.

---

### Sources

- [Statement Execution API reference (Azure)](https://docs.databricks.com/api/azure/workspace/statementexecution)
- [Azure Databricks SQL Statement Execution tutorial (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial)
- [Databricks SDK for Python — StatementExecution docs (mirrors API prose)](https://databricks-sdk-py.readthedocs.io/en/latest/workspace/sql/statement_execution.html)
- [Query metric views (Microsoft Learn)](https://learn.microsoft.com/en-us/azure/databricks/business-semantics/metric-views/query)
- [Statement Execution API GA announcement (Databricks blog)](https://databricks.com/blog/announcing-general-availability-databricks-sql-statement-execution-api)
