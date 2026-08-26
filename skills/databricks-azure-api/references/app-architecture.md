# Azure Databricks REST API — Integration Patterns for Next.js / Node.js on Azure Web Apps

Cross-cutting reference for building TypeScript server-side code (Next.js API routes, server actions, plain Node services) that calls the Azure Databricks workspace REST API. Endpoint-level detail for individual API families (Statement Execution, Genie, Files, Lakebase, etc.) lives in sibling documents; this file covers architecture, a shared client, auth, retries, rate limits, errors, pagination, caching, long-running work, configuration, and security.

All examples use plain `fetch()` (Node 18+ / Next.js runtime), a `DATABRICKS_HOST` env var (full URL **with** `https://`, e.g. `https://adb-1234567890123456.7.azuredatabricks.net`, no trailing slash — same convention as auth.md and SKILL.md), and a `getToken()` helper that returns a valid Bearer token.

## Table of Contents

1. [Overall Architecture](#1-overall-architecture)
2. [Authentication: OAuth M2M for Service Principals](#2-authentication-oauth-m2m-for-service-principals)
3. [A Thin `DatabricksClient` Wrapper](#3-a-thin-databricksclient-wrapper)
4. [Rate Limits of the Workspace APIs](#4-rate-limits-of-the-workspace-apis)
5. [Error Taxonomy and User-Safe Error Mapping](#5-error-taxonomy-and-user-safe-error-mapping)
6. [Pagination Conventions](#6-pagination-conventions)
7. [Long-Running Queries in a Serverless-ish Web Tier](#7-long-running-queries-in-a-serverless-ish-web-tier)
8. [Caching Strategies for Query Results](#8-caching-strategies-for-query-results)
9. [Decision Matrix: Statement Execution vs Genie vs Saved Queries vs Lakebase vs Files API](#9-decision-matrix)
10. [Env Var / Config Checklist for Azure Web Apps](#10-env-var--config-checklist-for-azure-web-apps)
11. [Security Checklist](#11-security-checklist)
12. [Gotchas](#12-gotchas)

---

## 1. Overall Architecture

**Rule zero: the browser never talks to Databricks.** All Databricks calls happen server-side:

```
Browser ──HTTP──> Next.js API route / server action / Node service ──HTTPS──> $DATABRICKS_HOST/api/...
                       (holds SP credentials, caches tokens,                (Bearer token auth)
                        enforces authz, shapes/limits responses)
```

Why:

- **Credentials.** The service principal client secret and the OAuth tokens minted from it must never reach the client. There is no safe way to scope a Databricks workspace token to a browser session.
- **Authorization.** Databricks permissions are per-principal (the SP), not per end user. Your app layer is where you map *your* users to *what data they may see* — by choosing which queries/parameters to run, or by running per-user on-behalf-of tokens if you implement that (advanced; default is one SP identity for the app).
- **Response shaping.** Databricks responses (result manifests, chunk links, external SAS URLs) are not browser-friendly and can leak infrastructure detail. Return only the rows/fields the UI needs.
- **Rate limits.** Limits are per workspace (shared by every caller). A server-side chokepoint lets you queue, coalesce, and cache; a fleet of browsers hitting the API directly cannot be throttled.

Practical layering in a Next.js app:

- `lib/databricks/client.ts` — the fetch wrapper below (auth, retry, errors).
- `lib/databricks/sql.ts` — Statement Execution helpers (execute, poll, fetch chunks).
- `app/api/*/route.ts` or server actions — thin handlers: validate input, call lib, map errors, return DTOs.
- Never import `lib/databricks/*` from a Client Component. Mark modules with `import 'server-only'` to make the build fail if someone does.

```ts
// lib/databricks/client.ts (top of file)
import 'server-only';
```

---

## 2. Authentication: OAuth M2M for Service Principals

**Do not use personal access tokens (PATs) for a production app** — they are tied to a human/SP but long-lived and unrotated. The current, recommended pattern for app-to-Databricks auth is **OAuth machine-to-machine (client credentials)** with a Databricks service principal. (Entra ID tokens for the SP also work against Azure Databricks, but Databricks-native OAuth M2M is the documented, cloud-portable default.)

- Token endpoint (workspace-level): `POST https://<DATABRICKS_HOST>/oidc/v1/token`
- Grant: `grant_type=client_credentials&scope=all-apis`, HTTP Basic auth with `client_id:client_secret`
- Access token lifetime: **1 hour** (`expires_in: 3600`)
- SP OAuth secrets: max **5 active** per SP, lifetime up to **2 years** — plan rotation.

`getToken()` with in-process caching and early refresh:

```ts
// lib/databricks/token.ts
import 'server-only';

let cached: { token: string; expiresAt: number } | null = null;
let inflight: Promise<string> | null = null;

export async function getToken(): Promise<string> {
  const now = Date.now();
  if (cached && now < cached.expiresAt - 5 * 60_000) return cached.token; // refresh 5 min early
  if (inflight) return inflight; // dedupe concurrent refreshes

  inflight = (async () => {
    const basic = Buffer.from(
      `${process.env.DATABRICKS_CLIENT_ID}:${process.env.DATABRICKS_CLIENT_SECRET}`
    ).toString('base64');

    const res = await fetch(`${process.env.DATABRICKS_HOST}/oidc/v1/token`, {
      method: 'POST',
      headers: {
        Authorization: `Basic ${basic}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: 'grant_type=client_credentials&scope=all-apis',
    });
    if (!res.ok) throw new Error(`Token request failed: ${res.status} ${await res.text()}`);
    const json = (await res.json()) as { access_token: string; expires_in: number };
    cached = { token: json.access_token, expiresAt: Date.now() + json.expires_in * 1000 };
    inflight = null;
    return cached.token;
  })();
  return inflight;
}
```

Notes:

- On Azure Web Apps each instance/process keeps its own token cache — that's fine; tokens are cheap to mint and the cache just avoids a token round-trip per request.
- Grant the SP only what it needs in the workspace: `CAN USE` on the SQL warehouse, `SELECT` on the specific Unity Catalog tables/schemas, `CAN RUN` on the Genie space, etc. (see [Security Checklist](#11-security-checklist)).

---

## 3. A Thin `DatabricksClient` Wrapper

One wrapper handles: base URL, auth header, JSON encoding, the standard error envelope, and retry with backoff on `429`/`503` honoring `Retry-After`.

The Databricks error envelope (consistent across current workspace APIs):

```json
{ "error_code": "RESOURCE_DOES_NOT_EXIST", "message": "Statement abc123 does not exist.", "details": [ ... ] }
```

```ts
// lib/databricks/client.ts
import 'server-only';
import { getToken } from './token';

export class DatabricksError extends Error {
  constructor(
    public status: number,
    public errorCode: string | undefined,
    message: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'DatabricksError';
  }
  get isRetryable() {
    return this.status === 429 || this.status === 503;
  }
}

export interface DbxRequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  maxRetries?: number;       // default 4
  signal?: AbortSignal;      // wire to request abort / route timeout
}

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

export class DatabricksClient {
  constructor(host = process.env.DATABRICKS_HOST!) {
    if (!host) throw new Error('DATABRICKS_HOST is not set');
    // Accept both "https://adb-....azuredatabricks.net" and a bare hostname.
    this.host = host.startsWith('https://') ? host.replace(/\/$/, '') : `https://${host}`;
  }
  private host: string;

  /** path is e.g. "/api/2.0/sql/statements". Returns parsed JSON (or undefined for 204/empty). */
  async request<T = unknown>(path: string, opts: DbxRequestOptions = {}): Promise<T> {
    const { method = 'GET', query, body, maxRetries = 4, signal } = opts;
    const url = new URL(`${this.host}${path}`);
    for (const [k, v] of Object.entries(query ?? {})) {
      if (v !== undefined) url.searchParams.set(k, String(v));
    }

    let attempt = 0;
    // Retry loop: only 429/503 (and transient network errors) are retried.
    // 5xx other than 503 is retried once for idempotent GETs only.
    for (;;) {
      let res: Response;
      try {
        res = await fetch(url, {
          method,
          signal,
          headers: {
            Authorization: `Bearer ${await getToken()}`,
            ...(body !== undefined ? { 'Content-Type': 'application/json' } : {}),
          },
          body: body !== undefined ? JSON.stringify(body) : undefined,
        });
      } catch (e) {
        // Network error (DNS, reset, abort). Abort is not retryable.
        if (signal?.aborted || attempt >= maxRetries) throw e;
        await sleep(backoffMs(attempt++));
        continue;
      }

      if (res.ok) {
        const text = await res.text();
        return (text ? JSON.parse(text) : undefined) as T;
      }

      // Parse the JSON error envelope defensively (proxies can return HTML).
      let errorCode: string | undefined, message = res.statusText, details: unknown;
      const raw = await res.text();
      try {
        const j = JSON.parse(raw);
        errorCode = j.error_code;
        message = j.message ?? message;
        details = j.details;
      } catch {
        message = raw.slice(0, 500) || message;
      }

      const retryable =
        res.status === 429 ||
        res.status === 503 ||
        (res.status >= 500 && method === 'GET');

      if (retryable && attempt < maxRetries) {
        const retryAfter = Number(res.headers.get('retry-after')); // seconds, may be absent
        const delay = Number.isFinite(retryAfter) && retryAfter > 0
          ? retryAfter * 1000
          : backoffMs(attempt);
        attempt++;
        await sleep(delay);
        continue;
      }

      throw new DatabricksError(res.status, errorCode, message, details);
    }
  }
}

/** Exponential backoff with full jitter: ~1s, 2s, 4s, 8s (capped 10s). */
function backoffMs(attempt: number): number {
  const cap = Math.min(10_000, 1000 * 2 ** attempt);
  return Math.random() * cap;
}

export const dbx = new DatabricksClient();
```

Usage:

```ts
import { dbx, DatabricksError } from '@/lib/databricks/client';

const res = await dbx.request<{ statement_id: string; status: { state: string } }>(
  '/api/2.0/sql/statements',
  {
    method: 'POST',
    body: {
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      statement: 'SELECT * FROM sales.orders WHERE region = :region LIMIT 100',
      parameters: [{ name: 'region', value: 'EMEA', type: 'STRING' }],
      wait_timeout: '10s',
    },
  }
);
```

Wrapper design notes:

- **Retry only what's safe.** `429` and `503` are always safe to retry (the request was throttled/rejected). Blind retry of `500` on a `POST` can double-execute (e.g., submit a statement twice); restrict 5xx retries to `GET`.
- **Honor `Retry-After`** when present; otherwise exponential backoff with full jitter. Cap total attempts (4–5) — a web request shouldn't hang for a minute retrying.
- **One client instance per process** (module singleton) so token caching and any future concurrency limiting are shared.
- If you add many concurrent background calls, add a small semaphore (e.g., limit 5–10 concurrent Databricks requests) to avoid tripping per-endpoint limits under load.

---

## 4. Rate Limits of the Workspace APIs

Databricks enforces **per-workspace** (sometimes per-endpoint) rate limits. Exceeding them returns **HTTP 429** with error codes like `REQUEST_LIMIT_EXCEEDED` / `RESOURCE_EXHAUSTED`; a `Retry-After` header may be present. Limits are fixed (not raisable) unless noted. Selected published limits relevant to app builders (per workspace):

| API | Limit |
|---|---|
| Jobs `runs/get` | 100 req/s |
| Jobs `run-now` | 20 req/s (submit: 35 req/s) |
| Jobs `runs/list` | 30 req/s |
| Workspace `list` / `export` | 50 / 60 req/s |
| Permissions GET / mutate | 100 / 30 req/s |
| Pipelines GET / mutate | 150 / 50 req/s |
| Secrets API | 1,100 req/min |
| Repos / Git credentials | 10 req/s |
| DBFS (legacy — don't build on it) | 30 req/s |

Notes:

- The **Statement Execution API** does not publish a numeric limit; treat it as throttled and always handle 429. Real throughput is bounded by warehouse concurrency anyway (a SQL warehouse queues statements; more clusters = more concurrency).
- Limits are shared by **everything** in the workspace — your app, scheduled jobs, other tools. Design for 429 as a normal event, not an error.
- App-side mitigations, in order of value: cache (Section 8), coalesce duplicate in-flight requests, poll at modest intervals with backoff, queue background work.

---

## 5. Error Taxonomy and User-Safe Error Mapping

Standard envelope: `{ "error_code": string, "message": string, "details"?: [...] }` with the HTTP status carrying the class of failure. Common cases:

| HTTP | Typical `error_code` | Meaning | App action |
|---|---|---|---|
| 400 | `BAD_REQUEST`, `INVALID_PARAMETER_VALUE`, `MALFORMED_REQUEST` | Bad input (bad SQL param type, invalid field) | Fix caller; surface validation message if user-driven |
| 401 | `UNAUTHENTICATED` | Missing/expired/invalid token | Force token refresh once, then retry once; else alert (secret expired?) |
| 403 | `PERMISSION_DENIED` | SP lacks grant on warehouse/table/space | Do **not** retry; log; user-safe "not available" |
| 404 | `RESOURCE_DOES_NOT_EXIST`, `NOT_FOUND` | Wrong ID, or expired statement/statement results | For statement polling: treat as "expired — re-run query" |
| 409 | `RESOURCE_ALREADY_EXISTS`, `RESOURCE_CONFLICT`, `ABORTED` | Create collision / concurrent modification | Idempotency handling; maybe retry with new name |
| 429 | `REQUEST_LIMIT_EXCEEDED`, `RESOURCE_EXHAUSTED` | Throttled | Retry with `Retry-After`/backoff (the client does this) |
| 500 | `INTERNAL_ERROR` | Server-side failure | Retry GETs; otherwise fail with generic message |
| 503 | `TEMPORARILY_UNAVAILABLE` | Transient unavailability (e.g., warehouse starting) | Retry with backoff |

Also handle **domain-level failure inside a 200**: Statement Execution returns HTTP 200 with `status.state = "FAILED"` and `status.error = { error_code, message }` when the SQL itself fails. Check the state, not just the HTTP code.

User-safe mapping — never forward raw Databricks messages to the browser (they leak table names, warehouse IDs, internal hostnames):

```ts
// lib/databricks/errors.ts
import { DatabricksError } from './client';

export type ApiFailure = { status: number; code: string; userMessage: string };

export function toUserError(e: unknown): ApiFailure {
  if (e instanceof DatabricksError) {
    switch (e.status) {
      case 400: return { status: 400, code: 'bad_request', userMessage: 'Invalid request.' };
      case 401:
      case 403: return { status: 403, code: 'forbidden', userMessage: 'You do not have access to this data.' };
      case 404: return { status: 404, code: 'not_found', userMessage: 'The requested data is no longer available.' };
      case 429:
      case 503: return { status: 503, code: 'busy', userMessage: 'The data service is busy. Please try again shortly.' };
      default:  return { status: 502, code: 'upstream_error', userMessage: 'Something went wrong fetching data.' };
    }
  }
  return { status: 500, code: 'internal', userMessage: 'Something went wrong.' };
}
```

Log the full `DatabricksError` (status, `error_code`, message) server-side (App Insights) with a correlation ID you also return to the client, so support can trace without exposing internals.

---

## 6. Pagination Conventions

Current Databricks APIs use **token pagination**: pass `page_size` (or `max_results`) and `page_token`; the response carries `next_page_token` (absent/empty on the last page). Examples: Jobs 2.2 (`/api/2.2/jobs/list`), Unity Catalog tables (`/api/2.1/unity-catalog/tables`), Files directory listing (`/api/2.0/fs/directories/...`), SQL queries list, Warehouses list. A few older endpoints still use `offset`/`limit` — prefer token pagination whenever the endpoint offers both, and note the **legacy cluster events offset pagination is deprecated in favor of tokens**.

Generic helper:

```ts
// Collects all pages. Use responsibly — prefer passing page_size and stopping early in a UI.
export async function listAll<TItem>(
  path: string,
  itemsKey: string, // e.g. 'jobs', 'tables', 'contents'
  query: Record<string, string | number | undefined> = {}
): Promise<TItem[]> {
  const out: TItem[] = [];
  let pageToken: string | undefined;
  do {
    const page = await dbx.request<Record<string, unknown> & { next_page_token?: string }>(
      path,
      { query: { ...query, page_token: pageToken } }
    );
    out.push(...((page[itemsKey] as TItem[]) ?? []));
    pageToken = page.next_page_token || undefined;
  } while (pageToken);
  return out;
}

// const tables = await listAll<{ full_name: string }>(
//   '/api/2.1/unity-catalog/tables', 'tables',
//   { catalog_name: 'main', schema_name: 'sales', max_results: 50 });
```

Rules of thumb:

- Treat `next_page_token` as **opaque and short-lived**; don't store it across user sessions.
- The items array key varies per endpoint (`jobs`, `runs`, `tables`, `contents`, `results`) — check each API.
- A page can legitimately be empty while `next_page_token` is still set; loop on the token, not on item count.
- Statement Execution results paginate differently — by **chunks** (`manifest.total_chunk_count`, `result.next_chunk_internal_link`, `GET .../result/chunks/{index}`), not page tokens.

---

## 7. Long-Running Queries in a Serverless-ish Web Tier

Azure Web Apps requests shouldn't block for minutes (front-end/load-balancer idle timeouts ~4 min default, plus poor UX). The Statement Execution API is designed for this: it is a **stateless-client async protocol** where `statement_id` is the resume handle.

Key facts (verified against the API docs):

- `wait_timeout`: `"0s"` or `"5s"`–`"50s"` (default `10s`). With `0s` the call returns immediately with `statement_id` and state `PENDING`. With 5–50s it behaves as *hybrid*: returns results if ready within the window, otherwise returns the `statement_id`.
- `on_wait_timeout`: `CONTINUE` (default — statement keeps running) or `CANCEL`.
- States: `PENDING → RUNNING → SUCCEEDED | FAILED | CANCELED | CLOSED`.
- **Results are available for 1 hour after success; polling does not extend this.** To keep a long-running statement alive you must poll (`GET /api/2.0/sql/statements/{id}`) **at least every 15 minutes**. Statements are removed ≥12 hours after reaching a terminal state; after that, GETs return 404.
- Status polling can lag up to ~5 s behind reality; don't poll faster than ~1 s.
- Result chunks are **re-fetchable**: within the 1-hour result window, chunks "can be resolved and fetched multiple times and in parallel" (per the API docs). Re-requesting a chunk in `EXTERNAL_LINKS` mode mints fresh presigned URLs — useful because each link expires in ≤15 min.

Pattern: split across HTTP requests, storing `statement_id` (in the client, or in Redis/DB keyed by a job token you hand to the client):

```ts
// app/api/query/start/route.ts — kick off, return a handle
export async function POST(req: Request) {
  const { region } = await req.json(); // validate!
  const r = await dbx.request<{ statement_id: string; status: { state: string } }>(
    '/api/2.0/sql/statements',
    {
      method: 'POST',
      body: {
        warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
        statement: 'SELECT day, revenue FROM sales.daily WHERE region = :region',
        parameters: [{ name: 'region', value: region, type: 'STRING' }],
        wait_timeout: '10s',          // hybrid: fast queries return inline in one round-trip
        on_wait_timeout: 'CONTINUE',
        format: 'JSON_ARRAY',
        disposition: 'INLINE',
      },
    }
  );
  return Response.json(r); // if state is SUCCEEDED, result is already included
}

// app/api/query/[statementId]/route.ts — client polls this every 1–2 s
export async function GET(_: Request, { params }: { params: { statementId: string } }) {
  try {
    const r = await dbx.request<{
      status: { state: string; error?: { error_code: string; message: string } };
      manifest?: { schema: { columns: { name: string }[] }; total_row_count: number };
      result?: { data_array?: string[][] };
    }>(`/api/2.0/sql/statements/${encodeURIComponent(params.statementId)}`);

    if (r.status.state === 'FAILED')
      return Response.json({ state: 'FAILED', message: 'Query failed.' }, { status: 422 });
    if (r.status.state !== 'SUCCEEDED')
      return Response.json({ state: r.status.state }); // client keeps polling
    return Response.json({
      state: 'SUCCEEDED',
      columns: r.manifest!.schema.columns.map((c) => c.name),
      rows: r.result?.data_array ?? [],
    });
  } catch (e) {
    const f = toUserError(e); // 404 here => statement expired: tell client to re-run
    return Response.json({ error: f.userMessage }, { status: f.status });
  }
}
```

Guidance:

- **Let the browser drive polling** (poll your route every 1–2 s with backoff). This survives instance restarts/scale-out because the only state is the `statement_id` string.
- Databricks does **not** validate that the poller is the submitter's session — anyone with your app route + a statement ID reaches your SP's statement. Bind statement IDs to your app's user session (store `statementId → userId` in Redis/cookie-signed token) before proxying polls.
- Use `disposition: "EXTERNAL_LINKS"` for big results (up to 100 GiB; INLINE caps at 25 MiB, `JSON_ARRAY` only). External links are presigned Azure storage SAS URLs valid **≤15 minutes** — download server-side (send **no** Authorization header to the SAS URL) and stream/transform to the client; don't hand SAS URLs to browsers unless you accept the exposure.
- For genuinely long analytics (minutes+), consider precomputing with a Databricks Job + materialized view instead of making users wait (Section 8).
- Cancel with `POST /api/2.0/sql/statements/{id}/cancel` when a user abandons the page; cancellation is best-effort (may silently no-op if already finished) — confirm via a final GET.
- Max statement text size: 16 MiB (you should never approach this — if you are, you're inlining data that belongs in parameters or tables).

---

## 8. Caching Strategies for Query Results

A SQL warehouse round trip costs 100s of ms (warm) to minutes (cold start / queued). Layer caches:

**1. In-memory LRU with TTL (per instance)** — first line of defense for repeated dashboard queries. Key = normalized SQL + parameters + warehouse.

```ts
// lib/cache.ts — tiny TTL LRU (or use the 'lru-cache' package)
const MAX = 500;
const store = new Map<string, { value: unknown; expiresAt: number }>();

export function cacheGet<T>(key: string): T | undefined {
  const e = store.get(key);
  if (!e || Date.now() > e.expiresAt) { store.delete(key); return undefined; }
  store.delete(key); store.set(key, e); // bump LRU order
  return e.value as T;
}
export function cacheSet(key: string, value: unknown, ttlMs: number) {
  if (store.size >= MAX) store.delete(store.keys().next().value!); // evict oldest
  store.set(key, { value, expiresAt: Date.now() + ttlMs });
}
```

Caveats on Azure Web Apps: memory cache is per instance (scale-out = N caches) and dies on restart. Fine for read-mostly dashboards with 30–300 s TTLs; use Azure Cache for Redis if you need shared caching or larger TTLs.

**2. Next.js data cache / ISR** — for pages/routes whose data changes on a schedule, use `export const revalidate = 300` on the route/page, or `unstable_cache`/`"use cache"` around the query function. This caches the *rendered* result and coalesces all users onto one Databricks call per revalidation window. Note: Next's automatic `fetch()` caching does not apply to your Databricks POSTs — POST + Authorization headers are not cached — so cache at the function/route level, not the fetch level.

**3. Databricks-side result cache** — warehouses cache query results; identical SQL from the same warehouse can return in milliseconds with `SUCCEEDED` immediately. Parameterized statements with identical parameter values benefit too. This is free — prefer stable, canonical SQL text to maximize hits.

**4. Precompute with materialized views / scheduled jobs** — when a dashboard query aggregates large tables, don't run the aggregation per page view. Create a **materialized view** (or a Lakeflow job writing a summary table) refreshed on a schedule, and have the app run cheap `SELECT`s against it. Rule of thumb: if the query takes >5–10 s warm, or is hit by many users with the same shape, precompute. For point-lookup/serving latency (<100 ms, high QPS), sync the table to **Lakebase** (managed Postgres synced tables) and read via Postgres instead of a warehouse (see matrix below).

Invalidation: prefer TTLs sized to the data's refresh cadence (e.g., hourly pipeline → 5–15 min TTL is plenty). Expose an admin "refresh" that busts keys (`revalidateTag` / delete from Redis) after pipelines complete if freshness matters.

---

## 9. Decision Matrix

Statement Execution vs Genie vs saved Queries vs Lakebase vs Files API — when each is the right tool:

| Need | Use | Why / notes |
|---|---|---|
| App-defined SQL over lakehouse data (dashboards, reports, exports) | **Statement Execution API** (`/api/2.0/sql/statements`) | The default. Parameterized, async, chunked/external results up to 100 GiB. Latency = warehouse latency (use serverless warehouse; seconds warm). |
| Natural-language Q&A over curated data ("ask your data" chat UI) | **Genie Conversation API** (`/api/2.0/genie/spaces/{space_id}/...`) | Start conversation → poll message status → fetch generated SQL result. You provide the Genie *space ID*; Genie authors the SQL. Slower, conversational; not for fixed dashboards. |
| Analyst-curated SQL managed in Databricks UI, app just runs it | **Queries API** (`/api/2.0/sql/queries`) + run via Statement Execution | Store/version SQL in Databricks (Queries API is CRUD only — it does not execute). Fetch query text by ID, execute through Statement Execution with parameters. Legacy Queries/Dashboards API (`/api/2.0/preview/sql/queries`) is deprecated — don't use it. |
| Low-latency (<100 ms), high-QPS operational reads; OLTP-style lookups | **Lakebase** (managed Postgres) with **synced tables** from UC | App connects over the Postgres wire protocol (`pg` npm client) using the SP's OAuth token as the password; UC tables sync into Postgres. Right tool when a warehouse round trip per page view is too slow/expensive. Also the right place for app-owned writable state. |
| Upload/download files, images, exports ≤5 GiB in UC volumes | **Files API** (`/api/2.0/fs/files/{volume_path}`) | PUT/GET raw bytes against Unity Catalog volumes. Use for report artifacts, ingest drops. Don't use legacy DBFS API (deprecated pattern, 30 req/s, no UC governance). |
| Batch/ETL orchestration triggered by the app | **Jobs API 2.2** (`/api/2.2/jobs/run-now`) | Fire-and-poll (`runs/get`, 100 req/s). Not for interactive latency. Jobs API 2.0/2.1 are superseded — use 2.2. |

---

## 10. Env Var / Config Checklist for Azure Web Apps

Set these as **App Service → Configuration → Application settings** (they become `process.env.*`), with secrets sourced from Key Vault via references.

| Variable | Example | Notes |
|---|---|---|
| `DATABRICKS_HOST` | `https://adb-1234567890123456.7.azuredatabricks.net` | Full workspace URL **with** `https://`, no trailing slash. |
| `DATABRICKS_CLIENT_ID` | `a1b2c3d4-...` | Service principal application (client) ID. |
| `DATABRICKS_CLIENT_SECRET` | `@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/dbx-sp-secret/)` | SP OAuth secret via **Key Vault reference** — never a literal in config exports. |
| `DATABRICKS_WAREHOUSE_ID` | `abcdef1234567890` | SQL warehouse for Statement Execution (from warehouse Connection details). |
| `DATABRICKS_GENIE_SPACE_ID` | `01ef1234...` | Only if using Genie; from the space URL. |
| `LAKEBASE_HOST` / `LAKEBASE_DB` / `LAKEBASE_PORT` | `instance-name.database.azuredatabricks.net` / `databricks_postgres` / `5432` | Only if using Lakebase; SP OAuth token is the Postgres password (refresh — it expires hourly). |
| `NODE_ENV` | `production` | |

Checklist:

- [ ] Key Vault created; SP secret + any other secrets stored there; App Service **managed identity** granted `get` on secrets; app settings use Key Vault references.
- [ ] Separate SPs (and ideally separate workspaces/warehouses) for dev/staging/prod; never share prod credentials with lower environments.
- [ ] Secret rotation reminder before the SP OAuth secret's expiry (max 2 years; you can hold 2 secrets and roll without downtime — 5 active max).
- [ ] App Service **Always On** enabled (keeps token cache warm, avoids cold starts mid-poll).
- [ ] Outbound: Databricks is public HTTPS by default; if the workspace uses Private Link / IP access lists, ensure the Web App's outbound (VNet integration/NAT) IPs are allowed.
- [ ] Health check endpoint that verifies token minting (but **not** on every probe — probe result should be cached; probes at 30 s × instances can waste token calls).
- [ ] Fail fast at boot: validate all required env vars on startup and log which are missing (without printing values).

---

## 11. Security Checklist

- [ ] **No Databricks calls from the browser.** All credentials and tokens stay server-side; `import 'server-only'` in every Databricks lib module.
- [ ] **Secrets in Key Vault**, surfaced via App Service Key Vault references; nothing in source control, `local.settings`, or build args. Enable Defender/secret scanning on the repo.
- [ ] **Least-privilege service principal.** Workspace-level grants only for what the app does: `CAN USE` on the one warehouse; UC `USE CATALOG`/`USE SCHEMA`/`SELECT` on exactly the tables/views the app reads (grant on **views**, not base tables, where possible); `READ VOLUME`/`WRITE VOLUME` only on needed volumes; `CAN RUN` on the Genie space. No workspace admin, no `ALL PRIVILEGES`.
- [ ] **SQL injection: always use `parameters`, never string interpolation.** The Statement Execution API's named parameter markers (`:name` + `parameters: [{name, value, type}]`) are server-side typed binding — user input never becomes SQL text. Also allow-list anything that *cannot* be parameterized (table names, ORDER BY columns) against a fixed set in app code.
- [ ] **Row-level security via Unity Catalog**, not app-side filtering alone: use UC row filters and column masks (or secured views) so even a bug in your app's WHERE clause can't over-expose data to the SP. If different user groups must see different rows through one SP, either use per-group views/filters keyed by an app-supplied parameter validated server-side, or separate SPs per tenant/tier.
- [ ] **Don't leak Databricks internals to clients**: map errors (Section 5), never return raw manifests, external SAS links, statement IDs unbound from sessions, or hostnames.
- [ ] **Bind async handles to sessions**: statement IDs / conversation IDs returned to a browser must be tied to that user's session server-side before honoring poll requests.
- [ ] **TLS 1.2+ only** (Node default is fine); never disable certificate verification.
- [ ] **Audit & observability**: log SP activity via Databricks audit logs / `system.access.audit` and `system.query.history` (use `query_tags` on statements — e.g. `[{key:"app",value:"webapp"},{key:"route",value:"/api/query"}]` — for cost attribution and tracing).
- [ ] **Rotate** SP OAuth secrets on a calendar; revoke unused secrets (5 active max is also a limit you can hit during sloppy rotations).

---

## 12. Gotchas

1. **Statement results expire after 1 hour** (success time, not last fetch), statements need a poll **every ≤15 min** to stay alive, and everything about a statement 404s ≥12 h after terminal state. A "resume yesterday's result" feature must persist rows yourself.
2. **Results are re-fetchable for 1 hour after success.** Chunks can be resolved and fetched multiple times and in parallel — two readers pulling the same statement's chunks is fine, and re-requesting a chunk mints fresh ≤15-min presigned links in `EXTERNAL_LINKS` mode. Caching server-side is still worthwhile (saves API calls and survives the 1-hour window), but it's an optimization, not a correctness requirement.
3. **HTTP 200 ≠ query success.** Check `status.state`; `FAILED` comes back as a 200 with `status.error.{error_code,message}`.
4. **`wait_timeout` must be `0s` or between `5s` and `50s`** — `1s`–`4s` values are rejected (`INVALID_PARAMETER_VALUE`). Timeouts are approximate and server-side.
5. **INLINE disposition caps at 25 MiB and only supports `JSON_ARRAY`**; `CSV`/`ARROW_STREAM` require `EXTERNAL_LINKS`. External links are SAS URLs valid ≤15 min, fetched **without** the Authorization header (sending it to Azure storage causes an auth error).
6. **All inline values arrive as strings** in `JSON_ARRAY` `data_array` (numbers, booleans, dates included — `null` stays `null`). Coerce using `manifest.schema.columns[].type_name`.
7. **429s are shared fate**: workspace rate limits are consumed by all clients in the workspace, so your app can get throttled because a batch job elsewhere is hammering the API. Always retry with `Retry-After`.
8. **Serverless warehouse ≠ zero cold start.** A stopped warehouse auto-starts on first statement — first query after idle can take a while and may surface as long `PENDING`. Consider keeping a small serverless warehouse with short auto-stop, and a warm-up ping for business hours.
9. **Next.js won't cache your Databricks fetches automatically** (POST + auth header). Cache deliberately at route/function level; conversely, remember `revalidate` caching means users share results — never cache per-user-authorized data in a shared cache key without including the authorization context in the key.
10. **Token endpoint failures look like app bugs**: an expired SP OAuth secret yields `invalid_client` from `/oidc/v1/token` and every route 500s at once. Alert specifically on token-mint failures; rotate before expiry.
11. **Azure front-end idle timeout (~4 min)** kills long-held HTTP requests — never hold a request open polling Databricks server-side for minutes; return the `statement_id` handle and let the client poll.
12. **Legacy APIs to avoid**: SQL Analytics preview endpoints (`/api/2.0/preview/sql/...` Queries/Dashboards legacy), Jobs 2.0/2.1 (use 2.2), DBFS API for file storage (use UC volumes + Files API), cluster-events offset pagination (use token pagination). If a docs page says "legacy" or "deprecated", the replacement exists in the current reference — build only on the current one.
13. **Scale-out multiplies pollers and caches.** N instances each hold their own token and LRU cache (fine) but browser polling load on Databricks scales with users, not instances — poll your own route (which reads a shared cache) and coalesce upstream GETs when many users watch the same statement.
14. **Encode path parameters** (`encodeURIComponent`) for statement IDs, volume paths in Files API, and UC three-part names in URLs — volume file paths with spaces are a classic 404-that-looks-like-a-permissions-issue.

---

### Sources

- Azure Databricks REST API reference: `https://docs.databricks.com/api/azure/workspace/introduction`
- Resource & API rate limits: `https://learn.microsoft.com/en-us/azure/databricks/resources/limits`
- Statement Execution tutorial: `https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial`
- Statement Execution behavior (retention, chunking, dispositions): Databricks SDK StatementExecution service docs
- OAuth M2M auth: `https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-m2m`
- Cluster events pagination migration: `https://learn.microsoft.com/en-us/azure/databricks/compute/events-api-updates`
