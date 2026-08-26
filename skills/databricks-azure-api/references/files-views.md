# Azure Databricks: Files API (Unity Catalog Volumes) + Materialized Views & Metric Views

Reference for building Next.js / Node.js server-side apps (Azure Web Apps) that talk to an
Azure Databricks workspace over plain `fetch()`. Verified against current (August 2026)
Databricks / Microsoft Learn documentation. All examples assume:

```ts
const HOST = process.env.DATABRICKS_HOST!; // e.g. "https://adb-1234567890123456.7.azuredatabricks.net"
// getToken(): Promise<string> — returns a valid Bearer token (PAT or Entra ID OAuth token). Assumed to exist.
```

> **Legacy note:** the old **DBFS API** (`/api/2.0/dbfs/...`) and DBFS root/mounts are
> **deprecated** — do not use them for new code. The current API for non-tabular file
> storage is the **Files API** (`/api/2.0/fs/...`) against **Unity Catalog volumes**.

---

## Table of Contents

1. [Volume paths and prerequisites](#1-volume-paths-and-prerequisites)
2. [Files API — file endpoints (`/api/2.0/fs/files/{path}`)](#2-files-api--file-endpoints)
   - PUT upload, GET download, HEAD metadata, DELETE
3. [Files API — directory endpoints (`/api/2.0/fs/directories/{path}`)](#3-files-api--directory-endpoints)
   - GET list (paginated), PUT create, DELETE, HEAD metadata
4. [Streaming upload/download in Node](#4-streaming-uploaddownload-in-node)
5. [Files API vs SQL `read_files()` — when to use which](#5-files-api-vs-sql-read_files)
6. [Materialized views (app developer's view)](#6-materialized-views)
7. [Metric views (definition, MEASURE() queries, discovery)](#7-metric-views)
8. [Gotchas](#8-gotchas)

---

## 1. Volume paths and prerequisites

Unity Catalog **volumes** are the recommended location for non-tabular data. Every file in
a volume has a POSIX-style path:

```
/Volumes/<catalog>/<schema>/<volume>/<optional/sub/dirs>/<file>
```

In the Files API the volume path is embedded **directly in the URL path** (no leading
slash duplication — the API path already ends in `/`):

```
{HOST}/api/2.0/fs/files/Volumes/<catalog>/<schema>/<volume>/<path-to-file>
{HOST}/api/2.0/fs/directories/Volumes/<catalog>/<schema>/<volume>/<path-to-dir>/
```

**Permissions** (Unity Catalog grants, on the principal your token represents — for a web
app this is usually a service principal):

| Operation | Required grants |
|---|---|
| Read/download/list/metadata | `READ VOLUME` on the volume + `USE SCHEMA` on schema + `USE CATALOG` on catalog |
| Upload/delete/create dirs | `WRITE VOLUME` (plus the same `USE SCHEMA`/`USE CATALOG`) |

**Path encoding:** URL-encode each path segment (spaces, `#`, `?`, `%`, non-ASCII).
Encode segment-by-segment so `/` separators survive:

```ts
const encodePath = (p: string) => p.split("/").map(encodeURIComponent).join("/");
const fileUrl = (p: string) => `${HOST}/api/2.0/fs/files/${encodePath(p.replace(/^\//, ""))}`;
const dirUrl  = (p: string) => `${HOST}/api/2.0/fs/directories/${encodePath(p.replace(/^\//, ""))}`;
// usage: fileUrl("Volumes/main/default/my_volume/reports/q3 report.pdf")
```

---

## 2. Files API — file endpoints

All four operations are plain HTTP file semantics (octet streams and headers), **not**
JSON-RPC. Auth header on every call: `Authorization: Bearer <token>`.

### 2.1 Upload a file — `PUT /api/2.0/fs/files/{file_path}`

- **Purpose:** create or overwrite a single file of **up to 5 GiB**.
- **Request:**
  - Path param `file_path` (string, required): absolute path incl. `/Volumes/...`.
  - Query param `overwrite` (boolean, optional, default `false`): overwrite an existing file.
  - Header `Content-Type: application/octet-stream` (recommended; the body is always
    treated as raw bytes — do **not** base64-encode or otherwise transform contents).
  - Body: raw file bytes.
- **Response:** `204 No Content` on success, empty body.
- **Errors / edge cases:**
  - `409` if the file already exists and `overwrite=false` (or the path is a directory).
  - `404` if the parent volume doesn't exist; `403` if missing `WRITE VOLUME`.
  - Parent directories inside the volume are created implicitly by upload in practice,
    but creating them explicitly with `PUT /fs/directories` is the documented, safe route.
  - **No append / random writes**: a file is written whole. To "append", download,
    modify, re-upload (or write dated files instead).
  - Files > 5 GiB cannot be uploaded through this endpoint (the official SDKs work
    around this with parallel/multipart logic; with raw REST, split your data or use the
    Python/Go SDK from a job).

```ts
// Upload a Buffer / Uint8Array (e.g. from a Next.js route handler receiving a form upload)
export async function uploadToVolume(volumePath: string, data: Uint8Array): Promise<void> {
  const res = await fetch(`${fileUrl(volumePath)}?overwrite=true`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/octet-stream",
    },
    body: data,
  });
  if (res.status !== 204) {
    // Error bodies are JSON: { "error_code": "...", "message": "..." }
    const err = await res.json().catch(() => ({}));
    throw new Error(`Upload failed ${res.status}: ${err.message ?? res.statusText}`);
  }
}
```

### 2.2 Download a file — `GET /api/2.0/fs/files/{file_path}`

- **Purpose:** download a file of **up to 5 GiB**; the file contents are the response body.
- **Request:** path param `file_path` (required). Supports standard HTTP conditional /
  partial headers: **`Range`** (partial download, gets `206`) and **`If-Unmodified-Since`**.
- **Response `200`** (or `206` for ranges). Useful response headers:
  - `Content-Length` (int64): size in bytes
  - `Content-Type` (string): usually `application/octet-stream`
  - `Last-Modified` (string, RFC 7231 date)
- **Errors:** `404` if no file at path (also if the path is a directory), `403` on
  missing `READ VOLUME`, `412` if `If-Unmodified-Since` precondition fails.

```ts
// Small file → Buffer in memory
export async function downloadFromVolume(volumePath: string): Promise<Buffer> {
  const res = await fetch(fileUrl(volumePath), {
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  return Buffer.from(await res.arrayBuffer());
}

// Proxying a volume file to the browser from a Next.js Route Handler — stream, don't buffer
export async function GET(req: Request, { params }: { params: { path: string[] } }) {
  const volumePath = `Volumes/${params.path.join("/")}`;
  const upstream = await fetch(fileUrl(volumePath), {
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (!upstream.ok) return new Response("Not found", { status: upstream.status });
  return new Response(upstream.body, {           // pass the ReadableStream straight through
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/octet-stream",
      "Content-Length": upstream.headers.get("content-length") ?? "",
    },
  });
}
```

### 2.3 Get file metadata — `HEAD /api/2.0/fs/files/{file_path}`

- **Purpose:** existence / size / freshness check without transferring content.
  Metadata comes back **in HTTP headers only; there is no response body**.
- **Response `200`** headers: `Content-Length`, `Content-Type`, `Last-Modified`
  (same shapes as download).
- **Errors:** `404` if the file doesn't exist. Also handy as a cheap access-check probe.

```ts
export async function statVolumeFile(volumePath: string) {
  const res = await fetch(fileUrl(volumePath), {
    method: "HEAD",
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`HEAD failed: ${res.status}`);
  return {
    size: Number(res.headers.get("content-length")),
    contentType: res.headers.get("content-type"),
    lastModified: new Date(res.headers.get("last-modified")!),
  };
}
```

### 2.4 Delete a file — `DELETE /api/2.0/fs/files/{file_path}`

- **Purpose:** permanently delete a single file.
- **Response:** `204 No Content`, empty body.
- **Errors:** `404` if the file doesn't exist (treat as idempotent success if you like);
  `403` on missing `WRITE VOLUME`. Cannot delete a directory via this endpoint — use
  the directories endpoint.

```ts
export async function deleteVolumeFile(volumePath: string): Promise<void> {
  const res = await fetch(fileUrl(volumePath), {
    method: "DELETE",
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (res.status !== 204 && res.status !== 404) {
    throw new Error(`Delete failed: ${res.status}`);
  }
}
```

---

## 3. Files API — directory endpoints

Directory paths conventionally end with a trailing `/` (the API tolerates both).

### 3.1 List directory contents — `GET /api/2.0/fs/directories/{directory_path}`

- **Purpose:** list files and subdirectories (one level, non-recursive).
- **Query params:**
  - `page_size` (int, optional): entries per page. **Default 1000, max 1000** (larger
    values are coerced down).
  - `page_token` (string, optional): opaque cursor from a previous response.
- **Response `200`** JSON:

```json
{
  "contents": [
    {
      "path": "/Volumes/main/default/my_volume/reports/q3.pdf",
      "name": "q3.pdf",
      "is_directory": false,
      "file_size": 204800,
      "last_modified": 1723371600000
    }
  ],
  "next_page_token": "eyJ..."
}
```

  `DirectoryEntry` fields: `path` (string, absolute), `name` (string, last path
  component), `is_directory` (bool), `file_size` (int64 bytes — absent for
  directories), `last_modified` (int64, **milliseconds** since Unix epoch).
- **Pagination:** loop while `next_page_token` is present, passing it back as
  `page_token`. Fields with zero/false/empty values may be omitted from JSON
  (`is_directory` absent ⇒ `false`).
- **Errors:** `404` if there is no directory at the path.

```ts
interface DirectoryEntry {
  path: string; name: string; is_directory?: boolean;
  file_size?: number; last_modified?: number;
}

export async function listVolumeDir(dirPath: string): Promise<DirectoryEntry[]> {
  const entries: DirectoryEntry[] = [];
  let pageToken: string | undefined;
  do {
    const url = new URL(dirUrl(dirPath));
    url.searchParams.set("page_size", "1000");
    if (pageToken) url.searchParams.set("page_token", pageToken);
    const res = await fetch(url, { headers: { Authorization: `Bearer ${await getToken()}` } });
    if (!res.ok) throw new Error(`List failed: ${res.status}`);
    const body = (await res.json()) as { contents?: DirectoryEntry[]; next_page_token?: string };
    entries.push(...(body.contents ?? []));
    pageToken = body.next_page_token;
  } while (pageToken);
  return entries;
}
```

### 3.2 Create a directory — `PUT /api/2.0/fs/directories/{directory_path}`

- **Purpose:** create an empty directory, **including any missing parents**
  (`mkdir -p` semantics). **Idempotent** — succeeds if it already exists.
- **Request:** no body, no query params.
- **Response:** `204 No Content`.
- Note: since PUT is idempotent-create, "ensure directory exists" is just this call.

### 3.3 Delete a directory — `DELETE /api/2.0/fs/directories/{directory_path}`

- **Purpose:** delete an **empty** directory only.
- **Response:** `204 No Content`.
- **Errors:** `404` if it doesn't exist; deleting a **non-empty** directory fails with an
  error — you must recursively list and delete contents (files via `DELETE /fs/files`,
  then subdirectories bottom-up). There is no recursive-delete flag.

### 3.4 Get directory metadata — `HEAD /api/2.0/fs/directories/{directory_path}`

- **Purpose:** check that a directory exists and the caller can access it. Headers only,
  no body. `200` = exists, `404` = does not.
- Tip from the docs: if your next step would be to create the directory anyway, skip the
  HEAD and just PUT (idempotent).

```ts
export async function ensureDir(dirPath: string) {
  const res = await fetch(dirUrl(dirPath), {
    method: "PUT",
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (res.status !== 204) throw new Error(`mkdir failed: ${res.status}`);
}
```

---

## 4. Streaming upload/download in Node

For large files, avoid `arrayBuffer()`/`Buffer` round-trips — stream.

```ts
import { createReadStream } from "node:fs";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import { createWriteStream } from "node:fs";

// STREAMING UPLOAD from disk (Node 18+ undici fetch).
// `duplex: "half"` is REQUIRED when the request body is a stream.
export async function uploadStream(volumePath: string, localFile: string, size: number) {
  const res = await fetch(`${fileUrl(volumePath)}?overwrite=true`, {
    method: "PUT",
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/octet-stream",
      "Content-Length": String(size), // avoids chunked transfer; know the size up front
    },
    body: Readable.toWeb(createReadStream(localFile)) as ReadableStream,
    // @ts-expect-error - undici extension, mandatory for streamed bodies
    duplex: "half",
  });
  if (res.status !== 204) throw new Error(`Upload failed: ${res.status}`);
}

// STREAMING DOWNLOAD to disk
export async function downloadStream(volumePath: string, localFile: string) {
  const res = await fetch(fileUrl(volumePath), {
    headers: { Authorization: `Bearer ${await getToken()}` },
  });
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  await pipeline(Readable.fromWeb(res.body as any), createWriteStream(localFile));
}
```

Practical notes:

- A 5 GiB transfer over HTTPS takes minutes; make sure your platform request timeout
  (Azure Web Apps front end ~230 s default for inbound requests to *your* app; outbound
  fetches are governed by your own AbortController) allows it. For very large transfers
  prefer background jobs.
- The `Range` header on download lets you resume partial downloads or read file tails.
- Retry on `429` (honor `Retry-After`) and on 5xx with exponential backoff. Databricks
  applies per-workspace API rate limits; bursty per-file operations on thousands of
  small files can be throttled — batch, parallelize modestly (e.g. 8–16 concurrent), and
  back off.

---

## 5. Files API vs SQL `read_files()`

| Need | Use |
|---|---|
| Ship bytes in/out of the platform (user uploads, PDF/image serving, exports, ML artifacts) | **Files API** |
| List/manage files, existence checks, app-managed folder structures | **Files API** |
| Query the *content* of CSV/JSON/Parquet/text files as rows (filter, aggregate, join) | **SQL** via Statement Execution API with `read_files()` |
| File inventory with metadata as a table | SQL: `SELECT * EXCEPT (content), _metadata FROM read_files('/Volumes/c/s/v', format => 'binaryFile')` |

`read_files()` is a SQL table function that reads files under a volume path directly:

```sql
SELECT * FROM read_files('/Volumes/main/default/my_volume/landing/', format => 'csv', header => true);
-- or shorthand for a single format:
SELECT * FROM csv.`/Volumes/main/default/my_volume/data.csv`;
```

Run these through the **Statement Execution API** (`POST /api/2.0/sql/statements`) on a
SQL warehouse — that returns structured rows/JSON, which is what an app usually wants
from data files. Use the Files API only when you actually need the raw bytes.

---

## 6. Materialized views

**What they are:** Unity Catalog **managed tables that physically store pre-computed
query results**. Unlike normal views (computed at query time), an MV caches its result
and updates it when sources change — on a schedule, on trigger, or manually. Refreshes
run on **serverless Lakeflow pipelines** managed by Databricks (billed separately from
your SQL warehouse); the warehouse only coordinates.

**Why an app developer cares:** your Next.js app should treat an MV as **just a table**.
You `SELECT` from it via the Statement Execution API on a SQL warehouse — fast, cheap,
pre-aggregated. The app never triggers computation of the underlying query.

### Creation & refresh (done by data engineers, but know the shapes)

```sql
-- Manual-refresh MV
CREATE OR REPLACE MATERIALIZED VIEW main.analytics.daily_sales AS
SELECT date, SUM(sales) AS sum_of_sales FROM main.raw.orders GROUP BY date;

-- Refresh automatically when sources update
CREATE OR REPLACE MATERIALIZED VIEW main.analytics.mv_trigger TRIGGER ON UPDATE AS SELECT ...;

-- Scheduled (Quartz cron: sec min hour day-of-month month day-of-week)
CREATE OR REPLACE MATERIALIZED VIEW main.analytics.daily_revenue
  SCHEDULE CRON '0 30 3 * * ?' AT TIME ZONE 'UTC' AS SELECT ...;
-- or: SCHEDULE EVERY 1 HOUR

-- Manual refresh (sync blocks; ASYNC returns immediately and runs in background)
REFRESH MATERIALIZED VIEW main.analytics.daily_sales;
REFRESH MATERIALIZED VIEW main.analytics.daily_sales ASYNC;
```

Refreshes are **incremental** when possible (requires Delta sources with
`delta.enableRowTracking = true`; change data feed helps) and fall back to **full**
recompute; Databricks picks the cheaper option automatically.

### Querying from the app

```ts
// SELECT from an MV exactly like a table, via Statement Execution API
export async function queryMV() {
  const res = await fetch(`${HOST}/api/2.0/sql/statements`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      statement: "SELECT date, sum_of_sales FROM main.analytics.daily_sales ORDER BY date DESC LIMIT 30",
      wait_timeout: "30s",
    }),
  });
  const body = await res.json();
  if (body.status?.state !== "SUCCEEDED") throw new Error(`Query ${body.status?.state}`);
  return body.result?.data_array as string[][]; // rows as arrays of strings
}
```

**App-relevant facts:**

- **Permissions:** querying needs standard `SELECT` on the MV (+ `USE SCHEMA`/`USE CATALOG`).
  `REFRESH` privilege (or ownership) is needed to trigger refreshes.
- **Freshness:** data is as of the last refresh. To surface freshness, query
  `information_schema` / `DESCRIBE EXTENDED`, or store a timestamp column in the MV.
- **No time travel** on MVs; sum over nullable columns can return `0` instead of `NULL`
  when only NULLs remain.
- Discovery: `information_schema.tables` with `table_type = 'MATERIALIZED_VIEW'`
  (documented value; `STREAMING_TABLE`, `VIEW`, `MANAGED`, `EXTERNAL`, `FOREIGN` are the
  other main types).

---

## 7. Metric views

**What they are:** Unity Catalog objects that define a **semantic layer** — dimensions
and *measures* declared once in **YAML**, queried by everyone (dashboards, Genie, and
your app) with guaranteed-identical results. Because the aggregation logic lives in the
view (not in each consumer's SQL), a "Total Revenue" number in your Next.js app is
computed by the exact same expression as in every dashboard — that's the consistency
guarantee. Requires a SQL warehouse (or DBR 17.3+ compute) to create; any compute with
`SELECT` can query.

### Definition (YAML, created via SQL)

```sql
CREATE OR REPLACE VIEW main.semantics.orders_metric_view WITH METRICS LANGUAGE YAML AS
$$
  version: 1.1
  comment: "Orders KPIs"
  source: samples.tpch.orders          -- table, view, or inline SQL query
  filter: o_orderdate > '1990-01-01'   -- applied to every query

  fields:                               -- a.k.a. dimensions
    - name: Order Month
      expr: DATE_TRUNC('MONTH', o_orderdate)
    - name: Order Status
      expr: CASE WHEN o_orderstatus = 'O' THEN 'Open' ELSE 'Fulfilled' END

  measures:                             -- aggregate expressions, no fixed grain
    - name: Order Count
      expr: COUNT(1)
    - name: Total Revenue
      expr: SUM(o_totalprice)
    - name: Open Order Revenue
      expr: SUM(o_totalprice) FILTER (WHERE o_orderstatus = 'O')
$$
```

Key YAML fields (version 1.1): `version` (required), `source` (required — table name or
SQL), `filter`, `joins` (star/snowflake with `name`/`source`/`on`|`using`,
`cardinality: many_to_one|one_to_many`, `rely: {at_most_one_match: true}` for
optimization), `fields`/`dimensions` and `measures` (each: `name`, `expr`, optional
`comment`, `display_name`, `format`, `synonyms`), `parameters` (name/data_type/default —
queried as a table-valued function), `window` on measures (experimental:
`order`/`range: current|cumulative|trailing N day|leading N month|all`/`semiadditive:
first|last`), and `materialization` (`schedule: every 6 hours`, `mode: relaxed`,
`materialized_views: [{name, type: aggregated|unaggregated, dimensions, measures}]`) to
transparently accelerate metric-view queries with MVs. Edit with
`ALTER VIEW <name> AS $$ ...full YAML... $$`; drop with `DROP VIEW`.

### Querying — the `MEASURE()` syntax

Measures **must** be wrapped in the `MEASURE()` aggregate function; dimensions are
selected/grouped normally. `SELECT *` does **not** work on a metric view.

```sql
SELECT
  `Order Month`,
  `Order Status`,
  MEASURE(`Order Count`)   AS order_count,
  MEASURE(`Total Revenue`) AS total_revenue
FROM main.semantics.orders_metric_view
WHERE `Order Status` = 'Fulfilled'
GROUP BY ALL
ORDER BY `Order Month`;
```

- `GROUP BY ALL` groups by every non-measure column — the idiomatic pattern.
- `WHERE` on dimensions is fine; the view's own `filter:` is always applied on top.
- Metric views **cannot be joined directly** with other tables — wrap the metric query
  in a CTE, then join the CTE's result.
- Parameterized metric views are called like table-valued functions:
  `FROM orders_metric_view(discount => 0.1)`.
- (DBR 18.1+ also accepts `agg()` as an alias for `MEASURE()` — prefer `MEASURE()`.)

```ts
// Consistent KPI endpoint for the app — same numbers as the BI dashboards
export async function revenueByMonth() {
  const res = await fetch(`${HOST}/api/2.0/sql/statements`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      statement: `
        SELECT \`Order Month\` AS month,
               MEASURE(\`Total Revenue\`) AS revenue,
               MEASURE(\`Order Count\`)  AS orders
        FROM main.semantics.orders_metric_view
        GROUP BY ALL ORDER BY month`,
      wait_timeout: "30s",
    }),
  });
  const body = await res.json();
  if (body.status?.state !== "SUCCEEDED") throw new Error(body.status?.error?.message);
  const cols: string[] = body.manifest.schema.columns.map((c: any) => c.name);
  return (body.result?.data_array ?? []).map((row: string[]) =>
    Object.fromEntries(row.map((v, i) => [cols[i], v])));
}
```

### Discovering metric views and their measures

- **Read the full definition (dimensions + measures) programmatically:**

  ```sql
  DESCRIBE TABLE EXTENDED main.semantics.orders_metric_view AS JSON
  ```

  returns the YAML definition, fields, measures, and metadata as JSON — ideal for
  building a dynamic metric picker in your app.
- **Catalog Explorer** is the documented UI discovery path; grants use the standard UC
  model (`GRANT SELECT ON <metric view> TO principal`).
- `information_schema.tables` documents `table_type` values `VIEW`, `MANAGED`,
  `EXTERNAL`, `FOREIGN`, `STREAMING_TABLE`, `MATERIALIZED_VIEW`, shallow clones — a
  dedicated `METRIC_VIEW` type is **not** listed in current docs (see gaps); metric
  views surface as views, so introspect with `DESCRIBE ... AS JSON` to distinguish them.
- Limitations: ownership transfer to groups is unsupported for *materialized* metric
  views; Delta Sharing (open sharing) and data profiling are unsupported; metric-view
  string fields are always `STRING` (CHAR/VARCHAR padding is lost — equality comparisons
  can differ from the source table).

---

## 8. Gotchas

1. **Never use the DBFS API** (`/api/2.0/dbfs/...`) or `dbfs:/` mounts for new code — deprecated. Files API + volumes only.
2. **Upload/download hard limit: 5 GiB per file** over the REST Files API. Bigger data belongs in tables or must be chunked into multiple files.
3. **`overwrite` defaults to `false`** on upload → a second PUT of the same path returns `409`. Decide explicitly.
4. **Success responses for PUT/DELETE are `204` with an empty body** — don't call `res.json()` unconditionally; only error responses carry a JSON `{error_code, message}` body.
5. **HEAD responses carry metadata in headers only** — there is no body to parse, and `fetch` won't error on 404; check `res.status` yourself.
6. **`last_modified` in list results is epoch *milliseconds*** (int64); the `Last-Modified` header on file endpoints is an RFC 7231 date *string*. Two formats for the same concept.
7. **Directory listing caps at 1000 entries per page** — always implement the `page_token` loop or you'll silently miss files.
8. **No recursive directory delete** and no rename/move endpoint — implement both client-side (list → delete each; download → upload → delete for moves).
9. **No appends or random writes to volume files** — write-whole-file semantics.
10. **URL-encode path segments** individually; unencoded spaces or `%` in filenames will 400 or hit the wrong path.
11. **Streamed request bodies with Node `fetch` require `duplex: "half"`** — omitting it throws at runtime. Prefer sending `Content-Length` to avoid chunked encoding.
12. **Rate limiting:** expect `429` + `Retry-After` under bursty many-small-files workloads; retry with backoff. Exact per-endpoint numbers aren't published for the Files API.
13. **MVs are stale between refreshes** by design — surface refresh time in the UI if freshness matters; the app cannot make an MV recompute by querying it (and `REFRESH` needs its own privilege and pays serverless DBUs).
14. **Metric views: forgetting `MEASURE()` or using `SELECT *` fails** — always list dimensions explicitly, wrap every measure, and use `GROUP BY ALL`.
15. **Metric views can't be joined directly** — CTE-wrap the metric query first.
16. **Backtick column names**: metric view fields often contain spaces (`` `Order Month` ``); remember backticks in SQL sent via Statement Execution, and escape them in TS template literals.
17. **MV storage may leak upstream data**: an MV's underlying files can contain source values not visible in the view result (kept for incremental refresh) — don't grant untrusted principals access to the underlying storage location.

### Primary sources

- Files API reference: `https://docs.databricks.com/api/azure/workspace/files` (endpoint semantics cross-checked via the official Python/Go/Java SDK docs, which embed the REST descriptions)
- Work with files in UC volumes (curl examples, limits): `https://learn.microsoft.com/en-us/azure/databricks/volumes/volume-files`
- Files overview / DBFS deprecation: `https://learn.microsoft.com/en-us/azure/databricks/files/`
- Materialized views (standalone): `https://learn.microsoft.com/en-us/azure/databricks/views/materialized` and `https://learn.microsoft.com/en-us/azure/databricks/ldp/dbsql/materialized`
- Metric views — overview / create / query / manage / YAML: `https://learn.microsoft.com/en-us/azure/databricks/uc-semantics/metric-views/`, `.../business-semantics/metric-views/create-edit`, `.../business-semantics/metric-views/query`, `.../business-semantics/metric-views/manage`, `.../metric-views/yaml-ref`
- `information_schema.tables`: `https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/information-schema/tables`
