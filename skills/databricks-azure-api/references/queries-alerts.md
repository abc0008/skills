# Azure Databricks REST API Reference: Queries API & Alerts V2 API

> Audience: TypeScript/Node.js server-side code (Next.js API routes, server actions, plain Node services) running on Azure Web Apps, calling an Azure Databricks workspace with plain `fetch()`.
>
> Base URL: `https://<workspace-instance>.azuredatabricks.net` — supplied via `process.env.DATABRICKS_HOST` (no trailing slash). Auth: `Authorization: Bearer <token>` (Microsoft Entra ID token for the Databricks resource, or a Databricks PAT / OAuth M2M token). All examples assume an existing `getToken(): Promise<string>` helper.
>
> Verified against the official Databricks OpenAPI spec that backs `https://docs.databricks.com/api/azure/workspace/queries` and `https://docs.databricks.com/api/azure/workspace/alertsv2` (fetched 2026-08-11) plus the Azure Databricks alerts guide on Microsoft Learn.

## Table of contents

- [Legacy APIs you must NOT use](#legacy-apis-you-must-not-use)
- [Common conventions (auth, errors, pagination, update_mask)](#common-conventions)
- [Queries API (`/api/2.0/sql/queries`)](#queries-api)
  - [The Query object](#the-query-object)
  - [POST /api/2.0/sql/queries — Create a query](#create-a-query)
  - [GET /api/2.0/sql/queries — List queries (paged)](#list-queries)
  - [GET /api/2.0/sql/queries/{id} — Get a query](#get-a-query)
  - [PATCH /api/2.0/sql/queries/{id} — Update a query (update_mask)](#update-a-query)
  - [DELETE /api/2.0/sql/queries/{id} — Trash a query](#trash-a-query)
  - [How saved queries relate to actually running SQL](#saved-queries-vs-running-sql)
  - [Pattern: exposing curated saved queries in an app](#pattern-curated-saved-queries)
- [Alerts V2 API (`/api/2.0/alerts`)](#alerts-v2-api)
  - [The AlertV2 object](#the-alertv2-object)
  - [POST /api/2.0/alerts — Create an alert](#create-an-alert)
  - [GET /api/2.0/alerts — List alerts (paged)](#list-alerts)
  - [GET /api/2.0/alerts/{id} — Get an alert](#get-an-alert)
  - [PATCH /api/2.0/alerts/{id} — Update an alert (update_mask)](#update-an-alert)
  - [DELETE /api/2.0/alerts/{id} — Trash an alert](#trash-an-alert)
  - [Alert lifecycle and evaluation states](#alert-lifecycle-and-evaluation-states)
  - [Pattern: creating alerts programmatically for users](#pattern-creating-alerts-for-users)
- [Rate limits, size limits, and operational notes](#rate-limits-size-limits-and-operational-notes)
- [Gotchas](#gotchas)

---

## Legacy APIs you must NOT use

| Legacy API (do not use) | Replaced by (use this) |
|---|---|
| `/api/2.0/preview/sql/queries` (a.k.a. "Queries / Legacy", Redash-style, `data_source_id`, `options.parameters`) | `/api/2.0/sql/queries` (Queries API, GA since mid-2024) |
| `/api/2.0/preview/sql/alerts` ("Alerts / Legacy") | `/api/2.0/alerts` (Alerts V2) |
| `/api/2.0/sql/alerts` ("Alerts V1", 2024-era, references a saved query via `query_id`) | `/api/2.0/alerts` (Alerts V2, self-contained `query_text`) |
| `/api/2.0/preview/sql/data_sources` (Data Sources, only needed by legacy queries) | Warehouses API `/api/2.0/sql/warehouses` for warehouse IDs |

The legacy preview endpoints are explicitly marked deprecated in Databricks docs ("This API is deprecated... Learn more: docs.databricks.com/en/sql/dbsql-api-latest.html"). The legacy objects have a completely different shape (`name` instead of `display_name`, `data_source_id` instead of `warehouse_id`, `options` blob, `rearm` instead of `retrigger_seconds`) — do not mix shapes. Alerts V1 (`/api/2.0/sql/alerts`) still exists but is superseded by Alerts V2; new code should target V2 only. Note the subtle path difference: current queries live under `/api/2.0/sql/queries`, while current alerts (V2) live under `/api/2.0/alerts` (no `/sql/` segment).

---

## Common conventions

- **Auth**: every request needs `Authorization: Bearer <token>`. A 401 returns `{"error_code":"UNAUTHENTICATED","message":...}`; 403 returns `PERMISSION_DENIED`.
- **Errors**: non-2xx responses are JSON: `{ "error_code": string, "message": string, "details": [...] }`. Common codes: `BAD_REQUEST` (400, e.g. malformed `update_mask` or invalid cron), `UNAUTHENTICATED` (401), `PERMISSION_DENIED` (403), `NOT_FOUND` (404 — wrong ID, or object was trashed/permanently deleted), `RESOURCE_EXHAUSTED`/HTTP 429 (throttled — honor `Retry-After`), 500/503 (retry with backoff).
- **Pagination**: both list endpoints use `page_size` (int, default 20, **max 100**) and `page_token` (opaque string). The response carries `next_page_token`; keep calling until it is absent/empty. Never fabricate tokens.
- **`update_mask`** (both PATCH endpoints): a single comma-separated string of field paths, **no spaces** (e.g. `display_name,query_text,tags`). Dots navigate sub-fields (e.g. `evaluation.threshold`, `schedule.pause_status`). You cannot address individual array elements — masking an array/collection field replaces the whole collection. `update_mask=*` means full replacement; Databricks recommends avoiding `*` and always listing explicit fields. Fields present in the body but not listed in the mask are ignored; fields listed in the mask but absent from the body are cleared/reset.
- **IDs** are UUID strings (e.g. `fe25e731-92f2-4838-9fb2-1ca364320a3d`). Timestamps are RFC-3339 strings (`create_time`, `update_time`).
- **Shared fetch helper** used in all examples below:

```ts
// lib/databricks.ts
const HOST = process.env.DATABRICKS_HOST!; // e.g. https://adb-1234567890123456.7.azuredatabricks.net

export async function dbxFetch<T>(
  path: string,
  init: { method?: string; body?: unknown; query?: Record<string, string | number | undefined> } = {},
): Promise<T> {
  const url = new URL(path, HOST);
  for (const [k, v] of Object.entries(init.query ?? {})) {
    if (v !== undefined) url.searchParams.set(k, String(v));
  }
  const res = await fetch(url, {
    method: init.method ?? "GET",
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/json",
    },
    body: init.body !== undefined ? JSON.stringify(init.body) : undefined,
    // Next.js: avoid caching authenticated API responses
    cache: "no-store",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(`Databricks ${res.status} ${err.error_code ?? ""}: ${err.message ?? res.statusText}`);
  }
  return (await res.json()) as T;
}
```

---

## Queries API

Manages **saved query definitions** (the objects you see in the SQL editor's "Queries" list). Endpoint family: `/api/2.0/sql/queries`. This is the current GA API; the legacy `/api/2.0/preview/sql/queries` must not be used.

### The Query object

```ts
type RunAsMode = "OWNER" | "VIEWER";
type LifecycleState = "ACTIVE" | "TRASHED";

interface QueryParameter {
  name: string;              // marker between {{ }} in query_text
  title?: string;            // label shown in UI widgets
  // exactly one *_value member:
  text_value?: { value?: string };
  numeric_value?: { value?: number };
  enum_value?: { enum_options?: string; values?: string[]; multi_values_options?: { prefix?: string; suffix?: string; separator?: string } };
  query_backed_value?: { query_id?: string; values?: string[]; multi_values_options?: {...} };
  date_value?: { date_value?: string; dynamic_date_value?: "NOW" | "YESTERDAY"; precision?: "DAY_PRECISION" | "MINUTE_PRECISION" | "SECOND_PRECISION" };
  date_range_value?: { date_range_value?: { start: string; end: string }; dynamic_date_range_value?: string; precision?: string; start_day_of_week?: number };
}

interface Query {
  id: string;                       // UUID (output only)
  display_name: string;             // name shown in list views / query page
  description?: string;             // free-text usage notes
  query_text: string;               // the SQL, e.g. "SELECT 1"
  warehouse_id?: string;            // SQL warehouse the query is attached to, e.g. "a7066a8ef796be84"
  catalog?: string;                 // default catalog for execution context
  schema?: string;                  // default schema for execution context
  parameters?: QueryParameter[];    // {{param}} definitions
  tags?: string[];                  // plain string tags
  parent_path?: string;             // workspace folder, e.g. "/Users/user@acme.com" (create-time only)
  run_as_mode?: RunAsMode;          // "Run as" role: OWNER (owner's credentials) or VIEWER
  apply_auto_limit?: boolean;       // apply LIMIT 1000 to results
  owner_user_name?: string;         // output; settable on update to transfer ownership
  last_modifier_user_name?: string; // output only
  lifecycle_state?: LifecycleState; // output only: ACTIVE | TRASHED
  create_time?: string;             // output only, RFC-3339
  update_time?: string;             // output only, RFC-3339
}
```

Notes:
- `parameters[].name` must match a `{{marker}}` in `query_text`.
- `tags` is a flat `string[]` (unlike some other Databricks APIs which use key/value tag objects).
- `parent_path` controls where the query appears in the workspace tree; it can only be set at create.
- `run_as_mode: "VIEWER"` makes shared runs use the viewer's credentials; `"OWNER"` uses the owner's.

### Create a query

**POST `/api/2.0/sql/queries`**

Request body (both fields top-level, the query itself nested under `query`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `query` | object | effectively yes | Writable Query fields: `display_name`, `description`, `query_text`, `warehouse_id`, `catalog`, `schema`, `parameters`, `tags`, `parent_path`, `run_as_mode`, `apply_auto_limit` |
| `auto_resolve_display_name` | boolean | no (default `true`) | If `true`, name conflicts are auto-resolved (suffix added); if `false`, a conflicting `display_name` fails the request |

Response `200`: the full `Query` object (including generated `id`, `lifecycle_state: "ACTIVE"`, timestamps).

```ts
const created = await dbxFetch<Query>("/api/2.0/sql/queries", {
  method: "POST",
  body: {
    auto_resolve_display_name: true,
    query: {
      display_name: "Daily revenue by region",
      description: "Curated query surfaced in the ops dashboard",
      query_text:
        "SELECT region, SUM(amount) AS revenue FROM main.sales.orders WHERE order_date = :run_date GROUP BY region",
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      catalog: "main",
      schema: "sales",
      tags: ["curated", "ops-dashboard"],
      parent_path: "/Workspace/Shared/curated-queries",
      apply_auto_limit: true,
    },
  },
});
console.log(created.id, created.lifecycle_state); // "…uuid…", "ACTIVE"
```

Edge cases: 400 if `query_text`/`display_name` are missing or `warehouse_id` is unknown; 403 if the caller cannot create in `parent_path`; 404 if `parent_path` does not exist.

### List queries

**GET `/api/2.0/sql/queries`** — "Gets a list of queries accessible to the user, ordered by creation time."

> Official warning from the spec: *"Calling this API concurrently 10 or more times could result in throttling, service degradation, or a temporary ban."* Serialize your pagination loop; do not fan out.

Query params:

| Param | Type | Required | Notes |
|---|---|---|---|
| `page_size` | int32 | no | default 20, max 100 |
| `page_token` | string | no | from previous response's `next_page_token` |

Response `200`:

```ts
interface ListQueryObjectsResponse {
  results?: Query[];        // same shape as Query above
  next_page_token?: string; // absent on last page
}
```

```ts
export async function listAllQueries(): Promise<Query[]> {
  const out: Query[] = [];
  let pageToken: string | undefined;
  do {
    const page = await dbxFetch<ListQueryObjectsResponse>("/api/2.0/sql/queries", {
      query: { page_size: 100, page_token: pageToken },
    });
    out.push(...(page.results ?? []));
    pageToken = page.next_page_token;
  } while (pageToken);
  return out;
}
```

There is **no server-side filter** (no name/tag filter params) — filter client-side after fetching, and cache the result (see pattern below).

### Get a query

**GET `/api/2.0/sql/queries/{id}`**

| Param | In | Required |
|---|---|---|
| `id` | path | yes (query UUID) |

Response `200`: full `Query`. 404 `NOT_FOUND` if the ID is wrong or the query was permanently deleted; a **trashed** query is still fetchable and shows `lifecycle_state: "TRASHED"`.

```ts
const q = await dbxFetch<Query>(`/api/2.0/sql/queries/${encodeURIComponent(id)}`);
if (q.lifecycle_state === "TRASHED") throw new Error("Query is in trash");
```

### Update a query

**PATCH `/api/2.0/sql/queries/{id}`**

| Field | In | Type | Required | Notes |
|---|---|---|---|---|
| `id` | path | string | yes | query UUID |
| `update_mask` | **body** | string | **yes** | comma-separated field paths relative to the query object, e.g. `query_text,tags` (note: for Queries the mask goes in the body; for Alerts V2 it is a query param) |
| `query` | body | object | no | Writable fields: `display_name`, `description`, `query_text`, `warehouse_id`, `catalog`, `schema`, `parameters`, `tags`, `run_as_mode`, `apply_auto_limit`, `owner_user_name` (ownership transfer). `parent_path` is NOT updatable. |
| `auto_resolve_display_name` | body | boolean | no (default `true`) | as in create |

Response `200`: the updated `Query`.

```ts
const updated = await dbxFetch<Query>(`/api/2.0/sql/queries/${id}`, {
  method: "PATCH",
  body: {
    update_mask: "query_text,warehouse_id,tags",
    query: {
      query_text: "SELECT region, SUM(amount) AS revenue FROM main.sales.orders GROUP BY region",
      warehouse_id: newWarehouseId,
      tags: ["curated", "ops-dashboard", "v2"],
    },
  },
});
```

Edge cases: 400 `BAD_REQUEST` on a malformed mask (spaces, unknown field names — names must exactly match the resource field names); masking `parameters` or `tags` replaces the entire array; omitting a masked field clears it.

### Trash a query

**DELETE `/api/2.0/sql/queries/{id}`** (operation name: `trashQuery`)

Moves the query to the **trash** — it immediately disappears from searches and list views and **cannot be used for (legacy) alerts**. It can be restored through the UI (no REST restore endpoint). **Permanently deleted after 30 days** in trash.

Response `200`: empty JSON object `{}`.

```ts
await dbxFetch<Record<string, never>>(`/api/2.0/sql/queries/${id}`, { method: "DELETE" });
```

### Saved queries vs running SQL

A saved Query is a **definition only** — the Queries API never executes SQL and never returns result rows. To run SQL from your app:

1. **Statement Execution API** (`POST /api/2.0/sql/statements`, then `GET /api/2.0/sql/statements/{statement_id}` polling) — the normal path. Fetch the saved query via `GET /api/2.0/sql/queries/{id}`, take its `query_text` (and `catalog`/`schema`/`warehouse_id`), and submit it as a statement. Saved-query `{{parameter}}` markers are a UI concept; for Statement Execution rewrite them as named `:param` markers and pass `parameters: [{name, value, type}]`.
2. **Alerts**: Alerts V2 embeds its own `query_text` (it does not reference a saved query — that was the V1 model), so "attach a query to an alert" means copying the SQL into the alert.
3. **UI / dashboards / jobs**: saved queries can be opened in the SQL editor, placed in legacy dashboards, or run by a Lakeflow Jobs SQL task referencing the query ID.

### Pattern: curated saved queries

Expose an allow-listed set of saved queries (e.g. tagged `curated`) for end users to browse and run:

```ts
// app/api/curated-queries/route.ts (Next.js App Router)
export async function GET() {
  const all = await listAllQueries(); // paged loop from above; cache this (e.g. 60s) server-side
  const curated = all
    .filter((q) => q.lifecycle_state === "ACTIVE" && q.tags?.includes("curated"))
    .map((q) => ({ id: q.id, name: q.display_name, description: q.description }));
  return Response.json(curated);
}
// POST /api/run-query { id } would then: get the query, take query_text + warehouse_id,
// and submit it via the Statement Execution API.
```

---

## Alerts V2 API

Endpoint family: `/api/2.0/alerts` (tag "Alerts V2", operations `AlertsV2.*`). An alert periodically runs its own SQL, evaluates a condition on the first row (or an aggregation) of one result column, and notifies subscribers when the condition is met. Replaces both legacy `/api/2.0/preview/sql/alerts` and V1 `/api/2.0/sql/alerts` — do not use those.

Key model change vs V1/legacy: **the alert owns its query**. There is no `query_id`; you put SQL directly in `query_text`. Alert queries **do not support parameters**. Status model is simplified to `OK` / `TRIGGERED` / `ERROR` (`UNKNOWN` = not yet evaluated, and is being phased out as an `empty_result_state` choice).

### The AlertV2 object

```ts
type ComparisonOperator =
  | "GREATER_THAN" | "GREATER_THAN_OR_EQUAL"
  | "LESS_THAN" | "LESS_THAN_OR_EQUAL"
  | "EQUAL" | "NOT_EQUAL"
  | "IS_NULL" | "IS_NOT_NULL";

type Aggregation = "SUM" | "COUNT" | "COUNT_DISTINCT" | "AVG" | "MEDIAN" | "MIN" | "MAX" | "STDDEV";
type AlertEvaluationState = "UNKNOWN" | "TRIGGERED" | "OK" | "ERROR";
type AlertLifecycleState = "ACTIVE" | "DELETED";

interface AlertV2 {
  // ---- required on create ----
  display_name: string;
  query_text: string;                 // SQL owned by the alert; no {{parameters}} allowed
  warehouse_id: string;               // SQL warehouse used to run the alert query
  evaluation: {
    source: {                         // required: column of the result to evaluate
      name: string;                   // column name in the query result
      aggregation?: Aggregation;      // omitted => "first row" semantics
      display?: string;               // display label
    };
    comparison_operator: ComparisonOperator; // required
    threshold?: {                     // omit for IS_NULL / IS_NOT_NULL
      value?: { double_value?: number; string_value?: string; bool_value?: boolean };
      column?: { name: string; aggregation?: Aggregation; display?: string }; // compare to another column
    };
    empty_result_state?: AlertEvaluationState; // state when query returns no rows; avoid "UNKNOWN" (being deprecated)
    notification?: {
      subscriptions?: Array<
        | { user_email: string }        // notify a workspace user by email
        | { destination_id: string }    // notification destination (Slack/Teams/webhook/email dest.)
      >;
      notify_on_ok?: boolean;           // also notify when alert returns to OK
      retrigger_seconds?: number;       // 0/omitted: notify once until back to OK; 1: notify on every
                                        // triggered evaluation; N: wait N seconds between notifications
    };
    // ---- output only ----
    state?: AlertEvaluationState;       // latest evaluation result
    last_evaluated_at?: string;         // RFC-3339
  };
  schedule: {
    quartz_cron_schedule: string;       // REQUIRED: Quartz cron (6-7 fields), e.g. "0 0/15 * * * ?"
    timezone_id: string;                // REQUIRED: Java timezone id, e.g. "Europe/London" or "UTC"
    pause_status?: "UNPAUSED" | "PAUSED"; // default UNPAUSED; PAUSED stops evaluations
  };
  // ---- optional ----
  custom_summary?: string;            // notification subject; supports mustache templates
  custom_description?: string;        // notification body; supports mustache templates
  parent_path?: string;               // workspace folder; create-only, cannot be updated
  run_as?: {                          // identity that executes the alert query
    user_name?: string;               // own email only (unless admin)
    service_principal_name?: string;  // SP application ID; requires servicePrincipal/user role
  };
  // ---- output only ----
  id?: string;                        // UUID
  owner_user_name?: string;           // "Unavailable" if owner was deleted
  effective_run_as?: { user_name?: string; service_principal_name?: string }; // resolved identity
  lifecycle_state?: AlertLifecycleState; // ACTIVE | DELETED (trashed)
  create_time?: string;
  update_time?: string;
  /** @deprecated use run_as */
  run_as_user_name?: string;
}
```

Evaluation semantics: with no `aggregation`, the **first row's** value of `source.name` is compared (order your query with `ORDER BY` and/or `LIMIT 1` deliberately). With an `aggregation`, it is computed across all rows of that column. Threshold is either a constant `value` (set exactly one of `double_value`/`string_value`/`bool_value`, matching the column type) or another `column`.

Custom template variables usable in `custom_summary`/`custom_description` (mustache): `{{ALERT_NAME}}`, `{{ALERT_STATUS}}`, `{{ALERT_CONDITION}}`, `{{ALERT_THRESHOLD}}`, `{{ALERT_COLUMN}}`, `{{ALERT_URL}}`, `{{QUERY_RESULT_VALUE}}`, `{{QUERY_RESULT_TABLE}}` (HTML table, first 100 rows, email only), `{{QUERY_RESULT_ROWS}}`, `{{QUERY_RESULT_COLS}}`.

### Create an alert

**POST `/api/2.0/alerts`**

Request body: an `AlertV2` object. Required: `display_name`, `query_text`, `warehouse_id`, `evaluation` (with required `source` and `comparison_operator`), `schedule` (with required `quartz_cron_schedule` and `timezone_id`).

Response `200`: the full `AlertV2` with `id`, `lifecycle_state: "ACTIVE"`, `effective_run_as`, timestamps. Errors: 400 `BAD_REQUEST` (invalid cron/timezone/operator-threshold combination), 401, 404 (e.g. bad `parent_path` or unknown `warehouse_id`).

```ts
const alert = await dbxFetch<AlertV2>("/api/2.0/alerts", {
  method: "POST",
  body: {
    display_name: "Orders backlog too high",
    query_text: "SELECT COUNT(*) AS backlog FROM main.ops.orders WHERE status = 'PENDING'",
    warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
    parent_path: "/Workspace/Shared/app-alerts",
    evaluation: {
      source: { name: "backlog" },                 // first-row value of column "backlog"
      comparison_operator: "GREATER_THAN",
      threshold: { value: { double_value: 500 } },
      empty_result_state: "OK",                    // no rows => treat as OK
      notification: {
        subscriptions: [
          { user_email: "oncall@acme.com" },
          { destination_id: "d5e04e5c-1234-5678-9abc-def012345678" }, // e.g. a Teams destination
        ],
        notify_on_ok: true,
        retrigger_seconds: 3600,                   // at most one notification per hour while triggered
      },
    },
    schedule: {
      quartz_cron_schedule: "0 0/15 * * * ?",      // every 15 minutes (Quartz: sec min hour dom mon dow)
      timezone_id: "UTC",
      pause_status: "UNPAUSED",
    },
    custom_summary: "{{ALERT_NAME}} is {{ALERT_STATUS}} (backlog={{QUERY_RESULT_VALUE}})",
  },
});
console.log(alert.id, alert.evaluation.state); // state starts as UNKNOWN until first evaluation
```

### List alerts

**GET `/api/2.0/alerts`** — alerts accessible to the user, ordered by creation time.

| Param | Type | Required | Notes |
|---|---|---|---|
| `page_size` | int32 | no | max 100 |
| `page_token` | string | no | opaque continuation token |

Response `200`:

```ts
interface ListAlertsV2Response {
  alerts?: AlertV2[];
  next_page_token?: string;
}
```

```ts
export async function listAllAlerts(): Promise<AlertV2[]> {
  const out: AlertV2[] = [];
  let pageToken: string | undefined;
  do {
    const page = await dbxFetch<ListAlertsV2Response>("/api/2.0/alerts", {
      query: { page_size: 100, page_token: pageToken },
    });
    out.push(...(page.alerts ?? []));
    pageToken = page.next_page_token;
  } while (pageToken);
  return out;
}
```

Errors: 400, 401. No server-side filtering — filter on `display_name` / `lifecycle_state` / `evaluation.state` client-side.

### Get an alert

**GET `/api/2.0/alerts/{id}`** — `id` (path, required, UUID).

Response `200`: full `AlertV2`, including current `evaluation.state` and `evaluation.last_evaluated_at` — this is how you **poll alert status** from an app (poll no more often than your alert's schedule; the state only changes when the schedule fires). Errors: 400, 401, 403 `PERMISSION_DENIED`, 404 `NOT_FOUND`.

```ts
const a = await dbxFetch<AlertV2>(`/api/2.0/alerts/${encodeURIComponent(alertId)}`);
console.log(a.evaluation.state, a.evaluation.last_evaluated_at, a.lifecycle_state);
```

### Update an alert

**PATCH `/api/2.0/alerts/{id}?update_mask=...`**

| Field | In | Type | Required | Notes |
|---|---|---|---|---|
| `id` | path | string | yes | alert UUID |
| `update_mask` | **query param** | string | **yes** | comma-separated, no spaces; dot-paths into sub-objects, e.g. `evaluation.threshold`, `schedule.pause_status`, `evaluation.notification.subscriptions`. `*` = full replace (avoid). |
| body | body | `AlertV2` | yes | fields being updated (only masked fields are applied) |

Response `200`: updated `AlertV2`. Errors: 400 (bad mask/field), 401, 403, 404.

```ts
// Pause an alert
await dbxFetch<AlertV2>(`/api/2.0/alerts/${alertId}`, {
  method: "PATCH",
  query: { update_mask: "schedule.pause_status" },
  body: { schedule: { quartz_cron_schedule: "0 0/15 * * * ?", timezone_id: "UTC", pause_status: "PAUSED" } },
});

// Change threshold and subscribers (arrays are replaced wholesale)
await dbxFetch<AlertV2>(`/api/2.0/alerts/${alertId}`, {
  method: "PATCH",
  query: { update_mask: "evaluation.threshold,evaluation.notification.subscriptions" },
  body: {
    evaluation: {
      source: { name: "backlog" },
      comparison_operator: "GREATER_THAN",
      threshold: { value: { double_value: 1000 } },
      notification: { subscriptions: [{ user_email: "oncall@acme.com" }] },
    },
  },
});
```

Note: `parent_path` cannot be updated (create-only). To transfer alert run identity, mask `run_as`; setting a service principal requires the `servicePrincipal/user` role. **Difference from Queries API**: here `update_mask` is a URL query parameter; in Queries PATCH it is a body field.

### Trash an alert

**DELETE `/api/2.0/alerts/{id}`** (operation `trashAlert`)

| Param | In | Type | Required | Notes |
|---|---|---|---|---|
| `id` | path | string | yes | alert UUID |
| `purge` | query | boolean | no | "Whether to permanently delete the alert. If not set, the alert will only be soft deleted." |

Default (no `purge`, or `purge=false`): soft delete — moves the alert to the trash. It disappears from list views immediately and **can no longer trigger**; restorable via UI only; **permanently deleted after 30 days** in trash. With `purge=true` the alert is **permanently deleted immediately** (skips the trash — irreversible, no restore). Response `200`: `{}`. Errors: 401, 403, 404 (already permanently deleted / wrong ID).

```ts
// Soft delete (trash, 30-day retention, UI-restorable)
await dbxFetch<Record<string, never>>(`/api/2.0/alerts/${alertId}`, { method: "DELETE" });

// Hard delete (permanent, immediate, irreversible)
await dbxFetch<Record<string, never>>(`/api/2.0/alerts/${alertId}`, {
  method: "DELETE",
  query: { purge: "true" },
});
```

Note: `purge` exists only on Alerts V2 — the Queries API DELETE (`/api/2.0/sql/queries/{id}`) has no such parameter and always soft-deletes to trash.

### Alert lifecycle and evaluation states

- `lifecycle_state`: `ACTIVE` → (DELETE) → `DELETED` (trashed, 30-day retention) → permanent deletion; or `ACTIVE` → (DELETE with `purge=true`) → permanently deleted immediately. Note the enum differs from queries (`TRASHED` there, `DELETED` here).
- `evaluation.state` per evaluation: `UNKNOWN` (never evaluated yet) → `OK` | `TRIGGERED` | `ERROR` (evaluation failed, e.g. SQL error, missing column, warehouse failure).
- Notification flow: on transition to `TRIGGERED`, subscribers are notified once; while still triggered, further notifications are governed by `retrigger_seconds` (0/absent = never again until it returns to OK; 1 = every evaluation; N = at most every N seconds). If `notify_on_ok`, a notification also fires on the `TRIGGERED → OK` transition.
- `empty_result_state` decides the state when the query returns zero rows (otherwise an empty result yields... set it explicitly to `OK`, `TRIGGERED`, or `ERROR`; avoid `UNKNOWN`, which is planned for deprecation).
- Scheduling is fully controlled by `schedule` (Quartz cron + Java `timezone_id` + `pause_status`). There is no "run now" REST endpoint on Alerts V2 itself; to force an immediate evaluation, run the alert as a Lakeflow Jobs alert task, or briefly tighten the cron.

### Pattern: creating alerts for users

A typical multi-tenant app flow (service principal owns plumbing, users get notified):

```ts
// server action: user asks for "notify me when metric X crosses T"
export async function createUserAlert(userEmail: string, metricSql: string, threshold: number) {
  return dbxFetch<AlertV2>("/api/2.0/alerts", {
    method: "POST",
    body: {
      display_name: `Metric watch for ${userEmail}`,
      query_text: metricSql,                       // must return a column named "value"; no parameters
      warehouse_id: process.env.DATABRICKS_WAREHOUSE_ID,
      parent_path: "/Workspace/Shared/app-alerts", // folder the app SP can write to
      run_as: { service_principal_name: process.env.DATABRICKS_SP_APP_ID }, // stable identity
      evaluation: {
        source: { name: "value" },
        comparison_operator: "GREATER_THAN",
        threshold: { value: { double_value: threshold } },
        empty_result_state: "ERROR",
        notification: { subscriptions: [{ user_email: userEmail }], notify_on_ok: true, retrigger_seconds: 0 },
      },
      schedule: { quartz_cron_schedule: "0 0 * * * ?", timezone_id: "UTC" }, // hourly, staggered per tenant ideally
    },
  });
}
```

Tips: run alerts as a **service principal** so they survive user offboarding; stagger `quartz_cron_schedule` minute/second offsets across tenants to avoid the concurrent-run cap; store the returned `id` in your DB keyed by user; use PATCH to pause instead of DELETE when a user "mutes" an alert.

---

## Rate limits, size limits, and operational notes

- **List queries concurrency**: the spec explicitly warns that ≥10 concurrent calls to `GET /api/2.0/sql/queries` "could result in throttling, service degradation, or a temporary ban." Treat listing as a low-QPS, cached operation.
- **General REST throttling**: Databricks workspace APIs are rate-limited per workspace/endpoint group; on HTTP 429 (`RESOURCE_EXHAUSTED`) back off exponentially and honor `Retry-After` if present.
- **`page_size` max 100** on both list endpoints.
- **Alert concurrency cap**: default **250 simultaneous active alert evaluations per workspace**; when the pool is full, scheduled evaluations are **skipped, not queued**. Stagger schedules; contact Databricks support to raise the cap.
- **Notification content**: `{{QUERY_RESULT_TABLE}}` includes only the **first 100 rows**, email destinations only. HTML in custom bodies is restricted to an allow-list of tags/attributes.
- **Trash retention**: 30 days for both queries and (soft-deleted) alerts, then permanent deletion; restore is UI-only. Alerts V2 additionally supports immediate hard delete via `DELETE /api/2.0/alerts/{id}?purge=true`; queries have no purge option over REST.
- **Polling**: neither API has long-running operations. The only thing to poll is `GET /api/2.0/alerts/{id}` for `evaluation.state` / `last_evaluated_at`; align the poll interval with the alert's cron. (Executing SQL — the Statement Execution API — has its own polling model, out of scope here.)
- **Timeouts**: alert evaluation runs on the attached SQL warehouse and inherits warehouse/statement timeouts; a failed or timed-out run surfaces as `evaluation.state: "ERROR"`.

## Gotchas

1. **Path asymmetry**: current queries = `/api/2.0/sql/queries`; current alerts (V2) = `/api/2.0/alerts` (no `/sql/`). `/api/2.0/sql/alerts` is the older V1 API — easy to hit by mistake and it has a different schema (`query_id`, `condition` with `op`/`operand`, no schedule object).
2. **`update_mask` location differs**: body field for Queries PATCH, **query parameter** for Alerts V2 PATCH. Both are required; both reject masks containing spaces or unknown field names with 400.
3. **Masked-but-omitted fields are cleared.** If you put `tags` in the mask but send no `tags`, tags are wiped. Arrays can only be replaced whole (no element-level masking).
4. **Legacy shapes must never leak into your types**: legacy queries use `name`, `data_source_id`, `options.parameters`; legacy alerts use `rearm`, `options.op/value/muted`. If you see those fields in an example, it is a deprecated API.
5. **Alerts V2 cannot reference a saved query.** V1 attached alerts to saved queries via `query_id`; V2 embeds `query_text`. If your app maintains curated saved queries and also creates alerts from them, copy the SQL and keep your own linkage table (and re-PATCH the alert's `query_text` when the saved query changes).
6. **Alert queries do not support parameters** (`{{param}}` markers). Bake values into `query_text` when creating/updating the alert.
7. **First-row semantics**: without `aggregation`, only the first result row is evaluated — always add `ORDER BY`/`LIMIT 1` to make it deterministic.
8. **Threshold typing matters**: choose the `AlertV2OperandValue` member matching the column type (`double_value` for numerics, `string_value` for strings, `bool_value` for booleans); mismatches produce 400 or `ERROR` evaluations. `IS_NULL`/`IS_NOT_NULL` need no threshold.
9. **Quartz, not Unix cron**: `quartz_cron_schedule` is 6-7 fields with seconds first (`0 0/15 * * * ?`), and `timezone_id` is a required Java TZ id. A 5-field Unix cron string is rejected.
10. **`empty_result_state: "UNKNOWN"` is being deprecated** — set `OK`, `TRIGGERED`, or `ERROR` explicitly.
11. **Trash ≠ delete**: DELETE on both APIs is a trash (soft-delete) operation by default; GET on a trashed object still succeeds (`lifecycle_state: "TRASHED"` / `"DELETED"`), so filter list results by lifecycle state before showing them to users. For alerts only, `?purge=true` on the DELETE makes it a permanent, immediate hard delete — use it for app-driven cleanup, but know there is no undo.
12. **`auto_resolve_display_name` defaults to `true`** — the object you get back may have a different `display_name` than requested (conflict suffix). Read the response, don't assume.
13. **`run_as` for alerts**: users can only set their own email; service principals require the `servicePrincipal/user` role; `run_as_user_name` is deprecated in favor of the `run_as` object; check `effective_run_as` in responses for what will actually execute.
14. **Timestamps are RFC-3339 strings** (`create_time`/`update_time`), not epoch millis — parse with `new Date(s)`.
15. **List responses may omit empty arrays** (`results`/`alerts` absent instead of `[]`) and `next_page_token` when there are no more pages — code defensively (`page.results ?? []`).
