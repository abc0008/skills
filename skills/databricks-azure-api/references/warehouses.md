# Azure Databricks SQL Warehouses API Reference

Reference for `/api/2.0/sql/warehouses` (and related config/permissions endpoints) for building
Next.js / Node.js server-side code that runs SQL against Databricks. All examples use plain
`fetch()`, a `DATABRICKS_HOST` env var (e.g. `https://adb-1234567890123456.7.azuredatabricks.net`,
no trailing slash) and an assumed `getToken(): Promise<string>` helper that returns an AAD /
Databricks PAT bearer token.

> **Legacy note:** The old SQL Endpoints API (`/api/2.0/sql/endpoints/*`) is the legacy
> predecessor of this API and must **not** be used. Use `/api/2.0/sql/warehouses` only.

## Table of Contents

- [Concepts: warehouse types, states, sizing](#concepts-warehouse-types-states-sizing)
- [Common request plumbing (TypeScript)](#common-request-plumbing-typescript)
- [List warehouses](#list-warehouses)
- [Get a warehouse](#get-a-warehouse)
- [Create a warehouse](#create-a-warehouse)
- [Edit a warehouse](#edit-a-warehouse)
- [Delete a warehouse](#delete-a-warehouse)
- [Start a warehouse](#start-a-warehouse)
- [Stop a warehouse](#stop-a-warehouse)
- [Workspace warehouse config (get/set)](#workspace-warehouse-config-getset)
- [Warehouse permissions (CAN_USE / CAN_MANAGE)](#warehouse-permissions-can_use--can_manage)
- [Handling STOPPED / STARTING warehouses in a web app](#handling-stopped--starting-warehouses-in-a-web-app)
- [Health-check pattern](#health-check-pattern)
- [Gotchas](#gotchas)

---

## Concepts: warehouse types, states, sizing

### Serverless vs PRO vs CLASSIC

| Capability | Serverless | Pro | Classic |
|---|---|---|---|
| Photon engine | Yes | Yes | Yes |
| Predictive IO | Yes | Yes | No |
| Intelligent Workload Management (IWM) | Yes | No | No |
| Typical startup time | **2–6 seconds** | ~4 minutes | ~4 minutes |
| Compute lives in | Databricks' Azure account | Your Azure subscription | Your Azure subscription |
| Autoscaling responsiveness | Fast up/down | Slower | Slower |

- **Serverless** is what you want for app-serving workloads (Next.js API routes hitting the
  Statement Execution API): cold start is seconds, not minutes, autoscaling reacts to query
  queuing quickly, and IWM handles high-concurrency bursts. In the API model there is **no
  `warehouse_type: SERVERLESS`** — serverless is expressed as `warehouse_type: "PRO"` **plus**
  `enable_serverless_compute: true`.
- **Pro** (`warehouse_type: "PRO"`, `enable_serverless_compute: false`): use only when serverless
  is unavailable in your region or you need the compute plane inside your own VNet (e.g. to reach
  on-prem/private databases for federation). ~4 minute cold start makes it painful for
  interactive web apps unless you keep it always-on.
- **Classic** (`warehouse_type: "CLASSIC"`): entry-level, Photon only, lowest performance tier.
  It exists mostly for backwards compatibility; avoid for new work.

**API default trap:** the UI defaults to serverless (where available), but the **API defaults to
CLASSIC**. When creating warehouses via the API you must explicitly set
`warehouse_type: "PRO"` and `enable_serverless_compute: true` to get serverless.

### Warehouse states

`state` in get/list responses is one of:
`STARTING`, `RUNNING`, `STOPPING`, `STOPPED`, `DELETING`, `DELETED`.

Health (separate from state) is in `health.status`: `HEALTHY`, `DEGRADED`, `FAILED`
(with `health.summary`, `health.details`, and `health.failure_reason` — a `TerminationReason`
object with `code`, `type`, `parameters` — populated on failure). If `health` is absent, assume
healthy.

### Cluster sizes

`cluster_size` accepts: `2X-Small`, `X-Small`, `Small`, `Medium`, `Large`, `X-Large`,
`2X-Large`, `3X-Large`, `4X-Large`, `5X-Large`. Size controls per-cluster power (driver size /
worker count — e.g. on Azure a `Small` is 4 × Standard_E8ds_v4 workers, an `X-Large` is 32);
concurrency is controlled by `min_num_clusters`/`max_num_clusters` instead (rule of thumb:
1 cluster per ~10 concurrent queries; max queue is 1,000 queries).

### Auto-stop

`auto_stop_mins`: idle minutes before automatic stop. `0` disables auto-stop.

- API validation (pro/classic): must be `0` or `>= 10`. API default: `120`.
- UI defaults: 45 min (pro/classic), 10 min (serverless). UI minimum: 10 (pro/classic), 5 (serverless).
- Serverless via API can go lower than the UI allows (down to ~1–5 min) because restart cost is
  seconds.

**Trade-off for an always-on web app:**
- Serverless: keep a short auto-stop (5–10 min). Cold start is 2–6 s, so the first query after an
  idle period only pays a few seconds; you save money whenever traffic is quiet.
- Pro/Classic: an auto-stopped warehouse costs a ~4 min cold start on the next request — usually
  unacceptable for a web UI. Either set `auto_stop_mins: 0` (always on, pay continuously) or
  accept the latency. This is the main reason serverless is the right answer for app serving.

Auto-stopped warehouses **auto-restart** when a new query arrives (JDBC/ODBC/Statement Execution
API); you don't have to call `start` yourself — see
[Handling STOPPED / STARTING](#handling-stopped--starting-warehouses-in-a-web-app).

---

## Common request plumbing (TypeScript)

```ts
// lib/databricks.ts
const HOST = process.env.DATABRICKS_HOST!; // e.g. https://adb-123.4.azuredatabricks.net

declare function getToken(): Promise<string>; // your auth helper (AAD or PAT)

export async function dbxFetch<T>(
  path: string,
  init: { method?: string; body?: unknown; query?: Record<string, string> } = {},
): Promise<T> {
  const url = new URL(path, HOST);
  for (const [k, v] of Object.entries(init.query ?? {})) url.searchParams.set(k, v);

  const res = await fetch(url, {
    method: init.method ?? "GET",
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/json",
    },
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
  });

  if (res.status === 429) {
    // Respect Retry-After, then retry (left to caller or a wrapper).
    const retryAfter = Number(res.headers.get("Retry-After") ?? "1");
    throw Object.assign(new Error("Rate limited"), { retryAfter, status: 429 });
  }
  if (!res.ok) {
    // Databricks errors: { "error_code": "RESOURCE_DOES_NOT_EXIST", "message": "..." }
    const err = await res.json().catch(() => ({}));
    throw Object.assign(
      new Error(`Databricks ${res.status}: ${err.error_code ?? ""} ${err.message ?? ""}`),
      { status: res.status, error_code: err.error_code },
    );
  }
  // Some endpoints (start/stop/edit/delete) return an empty JSON body.
  const text = await res.text();
  return (text ? JSON.parse(text) : {}) as T;
}
```

---

## List warehouses

`GET /api/2.0/sql/warehouses`

Lists all SQL warehouses the caller can see in the workspace.

**Query parameters**

| Param | Type | Required | Notes |
|---|---|---|---|
| `page_size` | int | no | Max warehouses per page. |
| `page_token` | string | no | Token from a previous call's `next_page_token`. All other params must match the original call. |
| `run_as_user_id` | int | no | **Deprecated / ignored by the server** — do not use. |

**Response**

```json
{
  "warehouses": [ { /* EndpointInfo — same shape as Get response, see below */ } ],
  "next_page_token": "opaque-token-or-absent"
}
```

Pagination: keep calling with `page_token = next_page_token` until `next_page_token` is absent.
In practice most workspaces have few warehouses and one unpaginated call returns everything, but
handle the token to be safe.

```ts
export interface WarehouseInfo {
  id: string;
  name: string;
  cluster_size: string;
  min_num_clusters: number;
  max_num_clusters: number;
  auto_stop_mins: number;
  num_clusters: number;
  num_active_sessions?: number;         // deprecated
  state: "STARTING" | "RUNNING" | "STOPPING" | "STOPPED" | "DELETING" | "DELETED";
  creator_name?: string;
  enable_photon?: boolean;
  enable_serverless_compute?: boolean;
  warehouse_type?: "PRO" | "CLASSIC" | "TYPE_UNSPECIFIED";
  spot_instance_policy?: "COST_OPTIMIZED" | "RELIABILITY_OPTIMIZED" | "POLICY_UNSPECIFIED";
  channel?: { name?: string; dbsql_version?: string };
  tags?: { custom_tags?: { key: string; value: string }[] };
  jdbc_url?: string;
  odbc_params?: { hostname: string; path: string; port: number; protocol: string };
  health?: {
    status: "HEALTHY" | "DEGRADED" | "FAILED";
    summary?: string;
    details?: string;
    failure_reason?: { code?: string; type?: string; parameters?: Record<string, string> };
  };
}

export async function listWarehouses(): Promise<WarehouseInfo[]> {
  const all: WarehouseInfo[] = [];
  let pageToken: string | undefined;
  do {
    const resp = await dbxFetch<{ warehouses?: WarehouseInfo[]; next_page_token?: string }>(
      "/api/2.0/sql/warehouses",
      { query: pageToken ? { page_token: pageToken } : {} },
    );
    all.push(...(resp.warehouses ?? []));
    pageToken = resp.next_page_token;
  } while (pageToken);
  return all;
}
```

---

## Get a warehouse

`GET /api/2.0/sql/warehouses/{id}`

Returns full info for one warehouse (the `WarehouseInfo` shape above). Key response fields:

- `id`, `name`, `state`, `health`
- Config: `cluster_size`, `min_num_clusters`, `max_num_clusters`, `auto_stop_mins`,
  `warehouse_type`, `enable_serverless_compute`, `enable_photon`, `spot_instance_policy`,
  `channel`, `tags`
- Runtime: `num_clusters` (currently running clusters), `jdbc_url`, `odbc_params`
  (`odbc_params.path` is the `http_path` you need for SQL drivers / connectors)

Errors: `404` / `RESOURCE_DOES_NOT_EXIST` for unknown id; `403` / `PERMISSION_DENIED` if the
caller lacks at least CAN_VIEW-level access.

```ts
export async function getWarehouse(id: string): Promise<WarehouseInfo> {
  return dbxFetch<WarehouseInfo>(`/api/2.0/sql/warehouses/${encodeURIComponent(id)}`);
}
```

---

## Create a warehouse

`POST /api/2.0/sql/warehouses`

Creates a warehouse. Requires appropriate workspace entitlement (typically admin or a user with
cluster-creation rights for SQL).

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | effectively yes | Unique within org, < 100 chars. |
| `cluster_size` | string | effectively yes | One of the T-shirt sizes listed above. |
| `warehouse_type` | string | recommended | `"PRO"` or `"CLASSIC"`. **Defaults to CLASSIC via API.** Set `"PRO"` + `enable_serverless_compute: true` for serverless. |
| `enable_serverless_compute` | boolean | recommended | `true` for serverless (needs `warehouse_type: "PRO"` and serverless enabled in region/account). |
| `auto_stop_mins` | int | no | `0` = never stop; else `>= 10` (serverless can be lower). Default `120`. |
| `min_num_clusters` | int | no | Default 1. Must be `> 0` and `<= min(max_num_clusters, 30)`. |
| `max_num_clusters` | int | no | `>= min_num_clusters`, `<= 40`. Defaults to `min_num_clusters`. |
| `enable_photon` | boolean | no | Default `true`. Leave on. |
| `spot_instance_policy` | string | no | `COST_OPTIMIZED` \| `RELIABILITY_OPTIMIZED`. **On Azure this is a no-op** — both map to on-demand driver and executors (it only changes behavior on AWS). |
| `tags` | object | no | `{ "custom_tags": [{ "key": "...", "value": "..." }] }`. < 45 tags. Propagated to underlying Azure resources for cost tracking. |
| `channel` | object | no | `{ "name": "CHANNEL_NAME_CURRENT" }` (default) or `CHANNEL_NAME_PREVIEW` (not for production; also `CHANNEL_NAME_PREVIOUS`, `CHANNEL_NAME_CUSTOM` with `dbsql_version`). |
| `creator_name` | string | no | Informational. |
| `instance_profile_arn` | string | no | **Deprecated**, AWS-only — ignore on Azure. |

**Response:** `{ "id": "<warehouse-id>" }`. The warehouse starts creating/starting
asynchronously — poll `GET` until `state` is `RUNNING` if you need it ready.

```ts
export async function createServerlessWarehouse(name: string): Promise<string> {
  const resp = await dbxFetch<{ id: string }>("/api/2.0/sql/warehouses", {
    method: "POST",
    body: {
      name,
      cluster_size: "2X-Small",
      warehouse_type: "PRO",
      enable_serverless_compute: true,
      auto_stop_mins: 10,
      min_num_clusters: 1,
      max_num_clusters: 1,
      tags: { custom_tags: [{ key: "app", value: "my-nextjs-app" }] },
    },
  });
  return resp.id;
}
```

Edge cases: creating with `enable_serverless_compute: true` fails if serverless isn't enabled
for the workspace/region; duplicate `name` fails validation; `cluster_size` strings are
case/format sensitive (use exactly e.g. `"2X-Small"`, `"X-Large"`).

---

## Edit a warehouse

`POST /api/2.0/sql/warehouses/{id}/edit`

Updates a warehouse's configuration. Body takes the **same fields as create** (all optional at
the wire level). **Treat this as a full replace**: fields you omit can revert to their defaults,
so the safe pattern is read–modify–write (GET the warehouse, mutate the config fields, POST the
whole config back). Editing a running warehouse restarts/recreates its clusters, which can
briefly disrupt running queries.

Response: empty `{}` on success (HTTP 200).

```ts
export async function setAutoStop(id: string, autoStopMins: number): Promise<void> {
  const w = await getWarehouse(id);
  await dbxFetch(`/api/2.0/sql/warehouses/${encodeURIComponent(id)}/edit`, {
    method: "POST",
    body: {
      name: w.name,
      cluster_size: w.cluster_size,
      min_num_clusters: w.min_num_clusters,
      max_num_clusters: w.max_num_clusters,
      auto_stop_mins: autoStopMins,
      warehouse_type: w.warehouse_type,
      enable_serverless_compute: w.enable_serverless_compute,
      enable_photon: w.enable_photon,
      spot_instance_policy: w.spot_instance_policy,
      channel: w.channel,
      tags: w.tags,
    },
  });
}
```

---

## Delete a warehouse

`DELETE /api/2.0/sql/warehouses/{id}`

Deletes the warehouse (state transitions through `DELETING` to `DELETED`). Running queries are
terminated. Response: empty on success. `404` for unknown id. There is no undo — in app code,
gate this behind confirmation and require CAN_MANAGE.

---

## Start a warehouse

`POST /api/2.0/sql/warehouses/{id}/start`

Starts a stopped warehouse. **Idempotent** — starting a RUNNING/STARTING warehouse is not an
error. Returns an empty body immediately; the start is asynchronous. Poll `GET` until
`state === "RUNNING"`.

```ts
export async function startWarehouse(id: string): Promise<void> {
  await dbxFetch(`/api/2.0/sql/warehouses/${encodeURIComponent(id)}/start`, { method: "POST" });
}

/** Start and wait until RUNNING. Serverless: ready in seconds. Pro/Classic: minutes. */
export async function ensureRunning(id: string, timeoutMs = 10 * 60_000): Promise<WarehouseInfo> {
  await startWarehouse(id);
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const w = await getWarehouse(id);
    if (w.state === "RUNNING") return w;
    if (w.state === "STOPPED" || w.state === "DELETED" || w.health?.status === "FAILED") {
      throw new Error(
        `Warehouse ${id} failed to start: state=${w.state} health=${w.health?.summary ?? "n/a"}`,
      );
    }
    if (Date.now() > deadline) throw new Error(`Timed out waiting for warehouse ${id} to start`);
    await new Promise((r) => setTimeout(r, 2_000)); // 2s poll; use 10-15s for pro/classic
  }
}
```

---

## Stop a warehouse

`POST /api/2.0/sql/warehouses/{id}/stop`

Stops the warehouse (running queries are terminated). Idempotent. Empty response; state moves
`STOPPING` → `STOPPED`. Rarely needed from an app — auto-stop usually handles this.

---

## Workspace warehouse config (get/set)

`GET /api/2.0/sql/config/warehouses` — read workspace-level warehouse configuration.
`PUT /api/2.0/sql/config/warehouses` — set it (workspace admin only). PUT **replaces** the whole
config object — do a GET, merge, PUT.

Fields (same shape on GET response and PUT request):

| Field | Type | Notes |
|---|---|---|
| `sql_configuration_parameters` | `{ configuration_pairs: [{key, value}] }` | Global SQL config parameters applied to all warehouses (e.g. `ANSI_MODE`). |
| `data_access_config` | `[{key, value}]` | Spark confs for external Hive metastore access. Serialized size ≤ 512 KB. |
| `enabled_warehouse_types` | `[{ warehouse_type: "PRO"\|"CLASSIC"\|"TYPE_UNSPECIFIED", enabled: bool }]` | Restricts which `warehouse_type` values create/edit will accept. Disabling a type may convert existing warehouses. |
| `security_policy` | `"DATA_ACCESS_CONTROL" \| "NONE" \| "PASSTHROUGH"` | Warehouse security policy. |
| `channel` | `{ name, dbsql_version }` | Optional channel selection. |
| `instance_profile_arn` | string | AWS only — ignore on Azure. |
| `google_service_account` | string | GCP only — ignore on Azure. |
| `config_param`, `global_param` | — | **Deprecated** — use `sql_configuration_parameters`. |
| `enable_serverless_compute` | boolean | **Deprecated** at workspace-config level (only `true` allowed); control serverless per-warehouse instead. |

Most app code never touches these; they matter for platform/IaC setup (e.g. forcing ANSI mode
workspace-wide).

---

## Warehouse permissions (CAN_USE / CAN_MANAGE)

Warehouse ACLs live under the generic Permissions API, object type `warehouses`:

| Endpoint | Purpose |
|---|---|
| `GET /api/2.0/permissions/warehouses/{warehouse_id}` | Read current ACL. |
| `PUT /api/2.0/permissions/warehouses/{warehouse_id}` | **Replace** the ACL (removes grants not listed; direct grants only — inherited ones remain). |
| `PATCH /api/2.0/permissions/warehouses/{warehouse_id}` | **Add/update** grants without touching others. Prefer this. |
| `GET /api/2.0/permissions/warehouses/{warehouse_id}/permissionLevels` | List permission levels valid for this object with descriptions. |

**Permission levels** (ascending): `CAN_VIEW` (see warehouse + queries), `CAN_MONITOR` (view +
monitoring), `CAN_USE` (run queries against it — what your app's service principal needs),
`CAN_MANAGE` (edit/start/stop/delete/permissions), `IS_OWNER` (single owner).

**Request body** (PUT/PATCH):

```json
{
  "access_control_list": [
    { "user_name": "alice@example.com", "permission_level": "CAN_MANAGE" },
    { "group_name": "analysts", "permission_level": "CAN_USE" },
    { "service_principal_name": "<application-id-guid>", "permission_level": "CAN_USE" }
  ]
}
```

Exactly one of `user_name` / `group_name` / `service_principal_name` per entry;
`service_principal_name` is the SP's **application ID (GUID)**, not its display name.

**Response** (PUT/PATCH/GET): `{ object_id: "/sql/warehouses/<id>", object_type: "warehouses",
access_control_list: [{ user_name?, group_name?, service_principal_name?, display_name?,
all_permissions: [{ permission_level, inherited, inherited_from_object }] }] }`.

Caller must have CAN_MANAGE (or be admin) to set permissions. Admins implicitly have CAN_MANAGE
on everything; those show up as `inherited: true` and cannot be removed via PUT.

```ts
export async function grantCanUse(warehouseId: string, servicePrincipalAppId: string) {
  return dbxFetch(`/api/2.0/permissions/warehouses/${encodeURIComponent(warehouseId)}`, {
    method: "PATCH",
    body: {
      access_control_list: [
        { service_principal_name: servicePrincipalAppId, permission_level: "CAN_USE" },
      ],
    },
  });
}
```

---

## Handling STOPPED / STARTING warehouses in a web app

Key facts:

1. **You usually don't need to call `/start` at all.** Submitting a query to a stopped warehouse
   (via the Statement Execution API `POST /api/2.0/sql/statements`, JDBC/ODBC, or the SQL
   connectors) **auto-starts** it. The statement just takes longer while the warehouse spins up.
2. First-query latency after idle = warehouse cold start + query time. Serverless: +2–6 s.
   Pro/Classic: +~4 min — for pro/classic, a synchronous Statement Execution call with
   `wait_timeout` will come back `state: "PENDING"` and you must poll the statement, or your
   HTTP route will time out.
3. Therefore, for a Next.js app:
   - Use a **serverless** warehouse; just fire the statement and let auto-start happen. Show a
     "warming up" spinner if the first response is slow.
   - If you must use pro/classic, either set `auto_stop_mins: 0` (always on) or proactively call
     `/start` from a warm-up hook (e.g. on deployment, or a scheduled ping before business hours)
     and poll to RUNNING before routing user traffic.
4. Don't gate every query on a `GET state == RUNNING` check — that's a race (it can stop between
   check and query) and wastes a round trip. Check state only for health/status pages and
   warm-up flows.

---

## Health-check pattern

A cheap readiness endpoint for your app (e.g. `/api/health/databricks`):

```ts
// app/api/health/databricks/route.ts (Next.js App Router)
import { NextResponse } from "next/server";
import { getWarehouse } from "@/lib/databricks";

export async function GET() {
  const id = process.env.DATABRICKS_WAREHOUSE_ID!;
  try {
    const w = await getWarehouse(id);
    const healthy =
      (w.state === "RUNNING" || w.state === "STARTING" || w.state === "STOPPED") &&
      w.health?.status !== "FAILED";
    return NextResponse.json(
      {
        warehouseId: id,
        state: w.state,                       // STOPPED is OK: it will auto-start on query
        health: w.health?.status ?? "HEALTHY",
        detail: w.health?.summary,
        runningClusters: w.num_clusters,
        ready: w.state === "RUNNING",         // "ready now" vs "will warm up on first query"
      },
      { status: healthy ? 200 : 503 },
    );
  } catch (e: any) {
    return NextResponse.json({ warehouseId: id, error: e.message }, { status: 503 });
  }
}
```

Interpretation: `STOPPED` + serverless = fine (seconds to warm). `STOPPED` + pro/classic = warn
(first query pays minutes). `DEGRADED`/`FAILED` = alert; surface `health.summary` /
`health.failure_reason.code` for diagnostics. For deeper checks, run `SELECT 1` through the
Statement Execution API on a schedule — but note that this resets the idle timer and defeats
auto-stop, so don't do it more often than your `auto_stop_mins`.

---

## Gotchas

- **Legacy API:** never use `/api/2.0/sql/endpoints/*`; it's the deprecated predecessor with the
  same shapes. Everything here is `/api/2.0/sql/warehouses`.
- **Serverless is not a `warehouse_type`:** it's `warehouse_type: "PRO"` +
  `enable_serverless_compute: true`. `GET` on a serverless warehouse reports type `PRO`.
- **API defaults differ from UI defaults:** API create defaults to `CLASSIC` type and
  `auto_stop_mins: 120`; the UI defaults to serverless and 10–45 min. Always set these fields
  explicitly.
- **Edit is effectively full-replace:** read–modify–write; don't PATCH-style send only the
  changed field or other settings may reset. Editing restarts clusters.
- **Permissions PUT replaces, PATCH merges.** Use PATCH to add a grant. `service_principal_name`
  = application ID GUID.
- **`spot_instance_policy` does nothing on Azure** — both values map to on-demand VMs. It's an
  AWS-relevant knob kept for API symmetry.
- **`instance_profile_arn`, `google_service_account`:** AWS/GCP-only fields — ignore on Azure.
  `instance_profile_arn` on the warehouse object is deprecated anyway.
- **`num_active_sessions` and `health.message` are deprecated** response fields; use
  `num_clusters` / `health.summary` + `health.details`.
- **Start/stop/create are asynchronous** — they return before the state transition completes.
  Poll `GET` (2 s interval for serverless, 10–15 s for pro/classic; cap with a deadline).
- **Statement API auto-start resets nothing you configured** — but any query (including health
  probes) resets the idle timer, so aggressive `SELECT 1` monitoring keeps the warehouse alive
  and billing.
- **Cluster recycling:** clusters running > 24 h get recycled; queries still running on the old
  cluster are force-terminated after 4 h. Long-running statements should be designed accordingly.
- **Scaling limits:** `min_num_clusters` ≤ 30, `max_num_clusters` ≤ 40, ~10 concurrent queries
  per cluster, 1,000-query queue cap per warehouse.
- **Tags limit:** fewer than 45 custom tags per warehouse; tags flow to Azure resources for cost
  attribution — tag your app's warehouse (`app`, `env`) from day one.
- **Channel `CHANNEL_NAME_PREVIEW`** runs pre-release DBSQL versions — never for production
  warehouses.
- **Rate limiting:** workspace REST APIs are rate-limited; on `429`, back off honoring the
  `Retry-After` header (see `dbxFetch` above). Databricks does not publish specific per-endpoint
  limits for the Warehouses API; keep list/get polling modest (no tighter than ~2 s).
- **Auth:** service principal needs `CAN_USE` on the warehouse to run queries, `CAN_MANAGE` to
  start/stop/edit. A `403 PERMISSION_DENIED` on `/start` but success on `GET` usually means the
  SP has only CAN_USE/CAN_VIEW.
