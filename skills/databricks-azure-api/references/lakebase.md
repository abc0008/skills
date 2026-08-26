# Lakebase (Databricks Managed Postgres) — App Writeback Reference

Reference for building Next.js / Node.js apps (on Azure Web Apps) that **write user input back to Databricks-managed Postgres (Lakebase)**, optionally synced with Unity Catalog. Covers the current `/api/2.0/database/*` REST API surface (Lakebase **Provisioned** database instances), credential generation, connecting with `pg`, synced tables (UC → Postgres), and registering Postgres databases back into Unity Catalog (Postgres → UC).

All REST examples assume:

```ts
const HOST = process.env.DATABRICKS_HOST!; // e.g. https://adb-1234567890123456.7.azuredatabricks.net
declare function getToken(): Promise<string>; // returns a workspace OAuth/PAT Bearer token
```

## Table of Contents

1. [What Lakebase is](#what-lakebase-is)
2. [API map (quick reference)](#api-map-quick-reference)
3. [Database Instances API](#database-instances-api)
4. [Generating database credentials (Postgres passwords)](#generating-database-credentials-postgres-passwords)
5. [Database Instance Roles API](#database-instance-roles-api)
6. [Connecting from Node.js with `pg`](#connecting-from-nodejs-with-pg)
7. [Synced Tables API (Unity Catalog → Postgres)](#synced-tables-api-unity-catalog--postgres)
8. [Database Catalogs API (Postgres → Unity Catalog)](#database-catalogs-api-postgres--unity-catalog)
9. [Writeback schema patterns](#writeback-schema-patterns)
10. [Gotchas](#gotchas)

---

## What Lakebase is

- **Fully managed PostgreSQL** (standard Postgres wire protocol + SQL, current major versions; standard drivers like `pg` work unchanged) integrated into the Databricks platform, designed for OLTP / low-latency transactional workloads next to the lakehouse.
- **Separated compute and storage**: compute nodes (one primary for read/write, optional secondaries for HA / read scaling) are stateless and sit on top of durable shared storage. Stopping an instance halts compute billing but retains data; capacity changes and failovers don't lose data.
- **Capacity units (CU)**: instance size is expressed as `CU_1`, `CU_2`, `CU_4`, `CU_8` — each CU ≈ 16 GB RAM plus corresponding CPU and local SSD cache.
- **Auth is Databricks-native**: you log into Postgres with your Databricks identity (user or service principal) using a **short-lived OAuth token (~1 hour) as the Postgres password** over TLS. Native Postgres passwords are possible but opt-in.
- **Two-way Unity Catalog integration**:
  - **Synced tables**: UC/Delta tables replicated *into* Postgres for low-latency reads.
  - **Database catalogs**: a Postgres database registered *into* UC as a (read-only, federated) catalog so SQL warehouses / analytics can query your writeback data.

### Provisioned vs. Autoscaling — important product note

The `/api/2.0/database/*` API documented here is **Lakebase Provisioned** (fixed-size CU compute, up to 10 instances/workspace). Databricks has introduced **Lakebase Autoscaling** (project/branch-based, scale-to-zero, its own newer API under the `postgres` API group, e.g. `POST /api/2.0/postgres` credential endpoints). Per Microsoft Learn: **new instances created after March 12, 2026 are created as Lakebase Autoscaling**, and existing Provisioned instances are being automatically upgraded starting June 2026. The Provisioned API below is current and not marked deprecated, but for greenfield apps check whether your workspace creates Autoscaling instances — the connection model (Postgres + OAuth token password) is the same, while management endpoints differ.

**Legacy note**: the old **"Online Tables"** feature (legacy Feature Serving online tables) is deprecated — do **not** use it; use **synced database tables** (below) instead.

### Provisioned limits (worth knowing up front)

| Limit | Value |
|---|---|
| Instances per workspace | 10 |
| Concurrent connections per instance | 1,000 (synced-table pipelines consume up to 16 each) |
| Max logical database size | 2 TB (≤1 TB recommended if you rely on full refreshes) |
| Credential (Postgres password) TTL | ~1 hour |
| Point-in-time restore window | 2–35 days (`retention_window_in_days`, default 7–14) |
| Scope | Single workspace; no cross-workspace connections |

---

## API map (quick reference)

All under the workspace host; JSON in/out; `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/2.0/database/instances` | Create instance |
| GET | `/api/2.0/database/instances` | List instances (paginated) |
| GET | `/api/2.0/database/instances/{name}` | Get instance |
| GET | `/api/2.0/database/instances:findByUid?uid=...` | Find instance by UID |
| PATCH | `/api/2.0/database/instances/{name}` | Update (capacity, stop/start, HA, retention) |
| DELETE | `/api/2.0/database/instances/{name}?purge=true` | Delete instance |
| POST | `/api/2.0/database/credentials` | **Generate short-lived Postgres credential (OAuth token)** |
| POST | `/api/2.0/database/instances/{instance_name}/roles` | Create Postgres role for a Databricks identity |
| GET | `/api/2.0/database/instances/{instance_name}/roles` | List roles (paginated) |
| GET | `/api/2.0/database/instances/{instance_name}/roles/{name}` | Get role |
| DELETE | `/api/2.0/database/instances/{instance_name}/roles/{name}` | Delete role |
| POST | `/api/2.0/database/synced_tables` | Create synced table (UC → Postgres) |
| GET | `/api/2.0/database/synced_tables/{name}` | Get synced table + sync status |
| PATCH | `/api/2.0/database/synced_tables/{name}` | Update synced table |
| DELETE | `/api/2.0/database/synced_tables/{name}` | Delete synced table |
| GET | `/api/2.0/database/instances/{instance_name}/synced_tables` | List synced tables (paginated) |
| POST | `/api/2.0/database/catalogs` | Register Postgres DB as UC catalog |
| GET | `/api/2.0/database/catalogs/{name}` | Get database catalog |
| PATCH | `/api/2.0/database/catalogs/{name}` | Update database catalog |
| DELETE | `/api/2.0/database/catalogs/{name}` | Unregister database catalog |
| GET | `/api/2.0/database/instances/{instance_name}/catalogs` | List catalogs on an instance |

List endpoints paginate with `page_size` / `page_token` query params and return `next_page_token` in the body (empty/absent = last page).

---

## Database Instances API

### Create — `POST /api/2.0/database/instances`

Key request fields (body is a `DatabaseInstance` object):

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | **yes** | 1–63 chars, letters/digits/hyphens, must start with a letter, no consecutive hyphens. This is the instance's stable identifier used in all other paths. |
| `capacity` | string | recommended | `"CU_1" \| "CU_2" \| "CU_4" \| "CU_8"` (default `CU_2`). Each CU ≈ 16 GB RAM. |
| `retention_window_in_days` | int | no | 2–35, PITR window (default 7). |
| `node_count` | int | no | Total compute nodes. `1` = no HA; `2–4` = primary + up to 3 HA secondaries. |
| `enable_readable_secondaries` | bool | no | Serve read-only traffic from secondaries via a separate `read_only_dns` endpoint. Use ≥3 nodes with this. |
| `parent_instance_ref` | object | no | `{ name, effective_point_in_time? }` — create a child instance from a PITR point (time travel / restore). |
| `usage_policy_id` / serverless usage policy | string | no | Billing attribution. |
| `stopped` | bool | no | Create in stopped state. |

Key response fields: `name`, `uid`, `capacity`, `state`, `read_write_dns`, `read_only_dns` (only when readable secondaries enabled), `pg_version`, `retention_window_in_days`, `node_count`, `creator`, `creation_time`, plus `effective_*` mirrors of settings.

`state` values: `STARTING`, `AVAILABLE`, `STOPPED`, `UPDATING`, `FAILING_OVER`, `DELETING`.

**Creation is asynchronous** — the response returns immediately with `state: "STARTING"`. Poll GET until `AVAILABLE` (typically a few minutes):

```ts
async function createInstanceAndWait(name: string) {
  const token = await getToken();
  const res = await fetch(`${HOST}/api/2.0/database/instances`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ name, capacity: "CU_1", retention_window_in_days: 7 }),
  });
  if (!res.ok) throw new Error(`create failed: ${res.status} ${await res.text()}`);

  // Poll until AVAILABLE
  for (let i = 0; i < 120; i++) {
    const g = await fetch(`${HOST}/api/2.0/database/instances/${name}`, {
      headers: { Authorization: `Bearer ${await getToken()}` },
    });
    const inst = (await g.json()) as { state: string; read_write_dns: string };
    if (inst.state === "AVAILABLE") return inst; // inst.read_write_dns is your PGHOST
    if (inst.state === "DELETING") throw new Error("instance is deleting");
    await new Promise((r) => setTimeout(r, 10_000));
  }
  throw new Error("timed out waiting for instance");
}
```

### Get / List / FindByUid

- `GET /api/2.0/database/instances/{name}` → full `DatabaseInstance`. 404 if missing.
- `GET /api/2.0/database/instances?page_size=100&page_token=...` → `{ database_instances: [...], next_page_token? }`.
- `GET /api/2.0/database/instances:findByUid?uid=<uuid>` → instance by immutable UID (names can be reused after delete; UID can't).

```ts
async function listInstances() {
  const out: any[] = [];
  let pageToken: string | undefined;
  do {
    const qs = new URLSearchParams({ page_size: "100" });
    if (pageToken) qs.set("page_token", pageToken);
    const res = await fetch(`${HOST}/api/2.0/database/instances?${qs}`, {
      headers: { Authorization: `Bearer ${await getToken()}` },
    });
    const body = await res.json();
    out.push(...(body.database_instances ?? []));
    pageToken = body.next_page_token;
  } while (pageToken);
  return out;
}
```

### Update — `PATCH /api/2.0/database/instances/{name}`

Send only the fields to change (SDKs also send an `update_mask`; with raw REST include the fields you're changing). Common operations:

- **Stop**: `{ "stopped": true }` — compute halts (no billing for compute), data retained, synced tables stop serving. Connections are refused while stopped.
- **Start**: `{ "stopped": false }` — instance goes `STARTING` → `AVAILABLE`.
- **Resize**: `{ "capacity": "CU_4" }` — capacity changes **take effect on restart**; resizing takes minutes.
- **HA / read replicas**: `{ "node_count": 3, "enable_readable_secondaries": true }` — adds secondaries; readable secondaries expose a separate `read_only_dns` host (`instance-ro-<uuid>....database.azuredatabricks.net`). Point read-heavy app queries at the RO host, writes at `read_write_dns`.

Requires `CAN MANAGE` permission on the instance.

### Delete — `DELETE /api/2.0/database/instances/{name}?purge=true`

- `purge=true` is **mandatory** (guard against accidental deletion); `force=true` additionally deletes child (PITR) instances.
- Deletes all data. Delete dependent UC database catalogs and synced tables first (synced-table cleanup after catalog deletion can take up to ~3 days).

### Failover behavior (HA)

If the primary node fails with `node_count >= 2`, a secondary is promoted in seconds-to-minutes. **DNS/connection strings do not change**, but active connections drop — your app must reconnect (a `pg` Pool does this naturally as new clients are created). Expect temporarily degraded performance while caches warm.

---

## Generating database credentials (Postgres passwords)

### `POST /api/2.0/database/credentials`

This is the current endpoint (SDK method `generateDatabaseCredential`; CLI `databricks database generate-database-credential`). It mints a **short-lived OAuth token scoped to one or more database instances** that you use as the **Postgres password** for your Databricks identity.

Request body:

| Field | Type | Required | Notes |
|---|---|---|---|
| `instance_names` | string[] | **yes** | Names of instances the credential should be valid for. |
| `request_id` | string | **yes** (per docs examples) | Client-supplied idempotency key — use a UUID per call. |
| `claims` | object[] | no | Optional requested claims/permission narrowing (beta; not needed for normal app auth). |

Response:

```json
{
  "token": "eyJ...long-opaque-string...",
  "expiration_time": "2026-08-11T14:15:22Z"
}
```

- **TTL ≈ 1 hour.** Expiry is enforced **only at login** — connections already open keep working after the token expires; only *new* logins fail.
- The identity of the Bearer token calling this endpoint (user or service principal) is the identity you must log into Postgres as (`user` = that identity's name / service principal application ID), and that identity must have a Postgres role on the instance (see Roles below).
- Cross-workspace use is not supported — the credential only works against instances in the same workspace.

```ts
import { randomUUID } from "node:crypto";

interface DbCredential { token: string; expiration_time: string }

export async function generatePgPassword(instanceName: string): Promise<DbCredential> {
  const res = await fetch(`${HOST}/api/2.0/database/credentials`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ request_id: randomUUID(), instance_names: [instanceName] }),
  });
  if (!res.ok) throw new Error(`credential failed: ${res.status} ${await res.text()}`);
  return (await res.json()) as DbCredential;
}
```

> For **Lakebase Autoscaling** projects the equivalent (beta) endpoint lives in the `postgres` API group (`docs.databricks.com/api/workspace/postgres/generatedatabasecredential`); same token-as-password model.

### Service principal (M2M) pattern for server apps

An Azure Web App backend should authenticate as a **service principal**: obtain the workspace Bearer token via OAuth client-credentials (`client_id`/`client_secret` against `https://<workspace>/oidc/v1/token`, scope `all-apis` — this is your `getToken()`), then call `/api/2.0/database/credentials`. The Postgres `user` is then the **service principal's client ID (application ID / UUID)**.

---

## Database Instance Roles API

Databricks identities are **not** auto-provisioned inside Postgres. Each identity that logs in needs a matching Postgres role. Two ways:

1. **SQL** (as an instance admin/owner): `CREATE ROLE "<identity-name-or-sp-client-id>" LOGIN;` then `GRANT` privileges.
2. **REST**: `POST /api/2.0/database/instances/{instance_name}/roles`

Create-role body (a `DatabaseInstanceRole`):

| Field | Type | Notes |
|---|---|---|
| `name` | string | Identity name — user email, group name, or **service principal client ID**. |
| `identity_type` | enum | `USER` \| `SERVICE_PRINCIPAL` \| `GROUP` |
| `membership_role` | enum | Postgres membership, e.g. `DATABRICKS_SUPERUSER` for admin-ish roles (optional). |
| `attributes` | object | Postgres role attributes, e.g. `{ "login": true, "createdb": false, "createrole": false }`. |

`GET .../roles` lists (with `page_size`/`page_token`), `GET .../roles/{name}` fetches one, `DELETE .../roles/{name}?reassign_owned_to=<role>&allow_missing=true` removes one (reassigning owned objects avoids orphaned tables).

After creating the role, grant it schema/table privileges with plain SQL (`GRANT USAGE ON SCHEMA app TO "..."; GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA app TO "...";`). Group roles: any member of the Databricks group can log in *as the group role name* using their own OAuth token; membership is checked only at login.

Native Postgres password roles exist for tools that can't rotate tokens (enable "Postgres Native Role Login" on the instance, then `CREATE ROLE x LOGIN PASSWORD '...'`), but prefer OAuth for apps.

---

## Connecting from Node.js with `pg`

Connection parameters:

| Param | Value |
|---|---|
| `host` | instance `read_write_dns` (writes) or `read_only_dns` (reads, if enabled) — e.g. `instance-<uuid>.database.azuredatabricks.net` |
| `port` | `5432` |
| `database` | `databricks_postgres` (default DB) or your own database name |
| `user` | Databricks identity — user email or **service principal client ID** (must have a Postgres role) |
| `password` | token from `POST /api/2.0/database/credentials` |
| `ssl` | **required** (`sslmode=require`); the token travels as a plaintext password so TLS is mandatory and enforced |

### Pool that refreshes the password on connect

`pg` accepts a **function** for `password` — it's invoked each time the Pool opens a *new* physical connection. Cache the credential and re-mint when close to expiry; existing connections keep working past expiry, only new connects need a fresh token.

```ts
// lib/db.ts — reusable module for Next.js API routes / server actions
import { Pool } from "pg";
import { randomUUID } from "node:crypto";

const HOST = process.env.DATABRICKS_HOST!;
const INSTANCE = process.env.LAKEBASE_INSTANCE!;   // e.g. "app-writeback"
const PGHOST = process.env.LAKEBASE_HOST!;         // read_write_dns of the instance
const PGUSER = process.env.LAKEBASE_USER!;         // service principal client ID

let cached: { token: string; exp: number } | null = null;

async function pgPassword(): Promise<string> {
  // refresh 5 minutes before expiry
  if (cached && Date.now() < cached.exp - 5 * 60_000) return cached.token;
  const res = await fetch(`${HOST}/api/2.0/database/credentials`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ request_id: randomUUID(), instance_names: [INSTANCE] }),
  });
  if (!res.ok) throw new Error(`credential failed: ${res.status} ${await res.text()}`);
  const { token, expiration_time } = await res.json();
  cached = { token, exp: Date.parse(expiration_time) };
  return token;
}

export const pool = new Pool({
  host: PGHOST,
  port: 5432,
  database: "databricks_postgres",
  user: PGUSER,
  password: pgPassword,            // <-- called on every new physical connection
  ssl: { rejectUnauthorized: true }, // sslmode=require; server presents a public CA cert
  max: 10,                          // stay well under the 1000-connection instance cap
  idleTimeoutMillis: 60_000,
  connectionTimeoutMillis: 10_000,
});

// usage in a Next.js route handler / server action
export async function saveAdjustment(userId: string, itemId: string, value: number) {
  const { rows } = await pool.query(
    `INSERT INTO app.adjustments (item_id, adjusted_value, updated_by)
     VALUES ($1, $2, $3)
     ON CONFLICT (item_id)
     DO UPDATE SET adjusted_value = EXCLUDED.adjusted_value,
                   updated_by     = EXCLUDED.updated_by,
                   updated_at     = now()
     RETURNING *`,
    [itemId, value, userId],
  );
  return rows[0];
}
```

Notes:

- If auth fails with Postgres error `28P01` (password authentication failed), the usual causes are: expired token (mint a new one — clear the cache and retry once), **no Postgres role for the identity**, or a token minted by a *different* identity than `user` (error text: *"token's identity ... did not match the security label configured for role ..."*).
- On Azure Web Apps, keep the Pool at module scope so it survives across requests within a warm instance. In serverless/edge contexts, keep `max` small.
- During instance **stop** or **failover**, connections drop/refuse — wrap queries with one retry-on-connection-error.
- A second Pool pointed at `read_only_dns` lets you send dashboards/read traffic to readable secondaries.

---

## Synced Tables API (Unity Catalog → Postgres)

Synced database tables continuously or periodically replicate a UC (Delta) table into Postgres so the app can read lakehouse data at millisecond latency — e.g. a forecast table the user then adjusts via writeback. (Replaces deprecated legacy Online Tables — do not use those.)

### Create — `POST /api/2.0/database/synced_tables`

```json
{
  "name": "my_uc_catalog.app.forecast_synced",
  "database_instance_name": "app-writeback",
  "logical_database_name": "databricks_postgres",
  "spec": {
    "source_table_full_name": "main.gold.forecast",
    "primary_key_columns": ["item_id"],
    "timeseries_key": "as_of_ts",
    "scheduling_policy": "TRIGGERED",
    "create_database_objects_if_missing": true,
    "new_pipeline_spec": {
      "storage_catalog": "main",
      "storage_schema": "sync_staging"
    }
  }
}
```

| Field | Required | Notes |
|---|---|---|
| `name` | yes | Three-part UC name for the synced table (in a **standard** UC catalog, or in the instance's registered database catalog). |
| `database_instance_name` | conditional | Target instance (required when `name` is in a standard catalog). |
| `logical_database_name` | conditional | Target Postgres database; the Postgres table lands at `<database>.<schema>.<table>` mirroring `name`. |
| `spec.source_table_full_name` | yes | UC source table. |
| `spec.primary_key_columns` | yes | Non-nullable PK columns; rows with NULL PKs are **silently excluded**. |
| `spec.timeseries_key` | no | Dedup column — keeps latest row per PK. |
| `spec.scheduling_policy` | yes | `SNAPSHOT` \| `TRIGGERED` \| `CONTINUOUS`. |
| `spec.create_database_objects_if_missing` | no | Auto-create Postgres DB/schema. |
| `spec.new_pipeline_spec` | no | Staging storage for the underlying Lakeflow pipeline (required when the synced table lives in a managed catalog); or `existing_pipeline_id` to share a pipeline. |

**Modes:**

| Mode | Behavior | CDF needed on source | Use when |
|---|---|---|---|
| `SNAPSHOT` | Full copy each run, atomically swapped | No (works for views, Iceberg) | >10% of rows change per cycle; cheapest for high churn (~15k rows/s/CU) |
| `TRIGGERED` | Initial snapshot, then incremental on demand/schedule | Yes (Delta Change Data Feed) | Known cadence, cost/lag balance (~1.2k rows/s/CU) |
| `CONTINUOUS` | Initial snapshot, then streaming updates | Yes | Near-real-time freshness; highest cost (pipeline always on) |

### Status / polling — `GET /api/2.0/database/synced_tables/{name}`

Response includes `data_synchronization_status` with `detailed_state` (`PROVISIONING` → `ONLINE`, or e.g. `ONLINE_TRIGGERED_UPDATE`, `FAILED`), `message`, and `pipeline_id`. Poll until `ONLINE`-ish before serving reads:

```ts
async function waitForSyncedTable(name: string) {
  for (;;) {
    const res = await fetch(
      `${HOST}/api/2.0/database/synced_tables/${encodeURIComponent(name)}`,
      { headers: { Authorization: `Bearer ${await getToken()}` } },
    );
    const t = await res.json();
    const state: string = t.data_synchronization_status?.detailed_state ?? "";
    if (state.startsWith("ONLINE")) return t;
    if (state === "FAILED")
      throw new Error(t.data_synchronization_status?.message ?? "sync failed");
    await new Promise((r) => setTimeout(r, 15_000));
  }
}
```

To **trigger a refresh** of a `TRIGGERED`/`SNAPSHOT` table, start the underlying pipeline: `POST /api/2.0/pipelines/{pipeline_id}/updates` (pipeline_id from the status), or wire a Lakeflow Job with a table-update or schedule trigger.

Other endpoints: `PATCH /api/2.0/database/synced_tables/{name}` (update spec), `DELETE /api/2.0/database/synced_tables/{name}` (stops refreshes; then `DROP TABLE` in Postgres to reclaim space), `GET /api/2.0/database/instances/{instance}/synced_tables?page_size&page_token` (list).

**Limits/edge cases**: max 20 synced tables per source table; each sync uses up to 16 Postgres connections (counts against the 1,000 cap); Postgres-side identifiers must match `[A-Za-z0-9_]+` (lowercase — no hyphens); complex types (ARRAY/MAP/STRUCT) become `JSONB`; GEOGRAPHY/GEOMETRY unsupported; null bytes (0x00) in strings fail the sync; only additive schema changes propagate in TRIGGERED/CONTINUOUS. The synced Postgres table is **read-only from the app's perspective** — write user edits to your own writeback tables, not into the synced table.

---

## Database Catalogs API (Postgres → Unity Catalog)

Registers a Postgres database from your instance as a **Unity Catalog catalog** (Lakebase-flavored foreign catalog, backed by query federation), so SQL warehouses, notebooks, and jobs can read your app's **writeback tables** with UC governance.

### Create — `POST /api/2.0/database/catalogs`

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string | yes | New UC catalog name. |
| `database_instance_name` | string | yes | Lakebase instance. |
| `database_name` | string | yes | Postgres database to register (alphanumeric/underscore only). |
| `create_database_if_not_exists` | bool | no | Create the Postgres DB if missing. |

```ts
await fetch(`${HOST}/api/2.0/database/catalogs`, {
  method: "POST",
  headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    name: "app_writeback",                       // UC catalog
    database_instance_name: "app-writeback",     // Lakebase instance
    database_name: "databricks_postgres",
    create_database_if_not_exists: false,
  }),
});
```

Then analytics can run `SELECT * FROM app_writeback.app.adjustments` from any SQL warehouse. The catalog is **read-only** from the UC side (writes always go through Postgres). Manage with `GET/PATCH/DELETE /api/2.0/database/catalogs/{name}` and `GET /api/2.0/database/instances/{instance}/catalogs`. Delete the catalog before deleting the instance.

For durable analytics copies / audit history of writeback data, also consider the **Lakebase change data feed → Delta** capture (public preview) rather than live federation.

---

## Writeback schema patterns

Recommended shape for user-adjustment writeback tables (created once via `psql`/migration script using an admin credential):

```sql
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE app.adjustments (
  item_id        text PRIMARY KEY,            -- matches PK of the synced source table
  adjusted_value numeric NOT NULL,
  comment        text,
  -- audit columns
  created_at     timestamptz NOT NULL DEFAULT now(),
  created_by     text        NOT NULL,
  updated_at     timestamptz NOT NULL DEFAULT now(),
  updated_by     text        NOT NULL
);

-- append-only audit trail for every change
CREATE TABLE app.adjustments_history (
  id             bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  item_id        text NOT NULL,
  adjusted_value numeric NOT NULL,
  changed_at     timestamptz NOT NULL DEFAULT now(),
  changed_by     text NOT NULL
);

GRANT USAGE ON SCHEMA app TO "<sp-client-id>";
GRANT SELECT, INSERT, UPDATE ON app.adjustments, app.adjustments_history TO "<sp-client-id>";
```

- **Upserts**: use `INSERT ... ON CONFLICT (pk) DO UPDATE` (shown in the Pool example) so the API route is idempotent.
- **Join pattern**: the app reads baseline data from the *synced* table (`databricks_postgres.gold.forecast_synced`) and LEFT JOINs `app.adjustments` — one low-latency query, all in Postgres.
- **Analytics readback**: register the database as a UC catalog (above); pipelines can then blend `app_writeback.app.adjustments` with lakehouse tables.
- Keep Postgres identifiers lowercase snake_case to avoid quoting pain across Postgres and UC.

---

### Retryable connection errors

Treat these as retry-once-with-a-fresh-connection (and, for `28P01`, mint a fresh OAuth token first — the cached one has expired):

| Code | Meaning | Action |
|---|---|---|
| `28P01` | invalid_password (expired OAuth token) | Refresh token, reconnect, retry once |
| `57P01` | admin_shutdown (instance restarted/failed over) | Reconnect, retry once |
| `08001` / `08004` / `08006` | connection exception / rejected / failure | Reconnect, retry once |
| `ECONNRESET`, `ETIMEDOUT`, `EPIPE` (socket) | transient network failure | Reconnect, retry once |

Do **not** blindly retry `40001` (serialization_failure) or `40P01` (deadlock) inside an open transaction: a failed connection aborts the whole transaction, so the retry must re-run the transaction from `BEGIN`, never resume mid-way. Wrap multi-statement writebacks in a function that owns the full transaction and is safe to invoke twice (idempotent upserts, `ON CONFLICT` keys).

## Gotchas

1. **Two different tokens.** The workspace Bearer token (REST auth) and the database credential (Postgres password) are different things with different lifetimes. Never use a PAT as a Postgres password.
2. **Credential endpoint path**: it's `POST /api/2.0/database/credentials` (not `.../instances/{name}/credentials`). Pass `instance_names` in the body plus a UUID `request_id`.
3. **Token TTL ~1h, enforced at login only.** Open connections outlive expiry; new connections need a fresh token — hence `password: async fn` on the `pg` Pool, refreshed ~5 min early. Don't create a new Pool per request.
4. **Missing Postgres role = auth failure even with a valid token.** Create a role per identity (SQL `CREATE ROLE ... LOGIN` or the instance roles REST API) and grant privileges. For service principals the role name is the **client ID UUID**, not the display name.
5. **SSL is mandatory** (`sslmode=require`). In `pg`, set `ssl: { rejectUnauthorized: true }`.
6. **Instance names vs UIDs**: names are the API key but can be recreated; store `uid` if you need a stable reference (`instances:findByUid`).
7. **Delete requires `purge=true`**; capacity changes apply on restart; a stopped instance refuses connections and its synced tables stop serving.
8. **Provisioned → Autoscaling transition** (new instances after 2026-03-12 are Autoscaling; auto-upgrades from June 2026). The Postgres connection + OAuth-password model is unchanged; management API for Autoscaling lives under the newer `postgres` API group. Verify which flavor your workspace gives you before hardcoding instance-management calls.
9. **Legacy Online Tables are deprecated** — use synced database tables only.
10. **Synced tables silently drop rows with NULL primary keys** and are read-only targets; don't write app data into them.
11. **Connection budget**: 1,000 per instance, minus up to 16 per synced-table pipeline; keep app Pool `max` modest (Azure Web Apps can scale out to many instances × pool size).
12. **Workspace-scoped everything**: instances, credentials, and catalogs don't cross workspaces.
13. **Rate limits**: Databricks workspace APIs enforce per-endpoint rate limits (HTTP 429 with `Retry-After`) — mint credentials at most ~once per hour per process, not per request.

### Sources

- Azure docs: `learn.microsoft.com/en-us/azure/databricks/oltp/` (Lakebase overview), `.../oltp/instances/` (Provisioned), `.../oltp/instances/create/`, `.../oltp/instances/authentication`, `.../oltp/instances/create/high-availability`, `.../oltp/instances/sync-data/sync-table`, `.../oltp/instances/register-uc`
- REST paths cross-checked against the Databricks SDK `database` service (`databricks-sdk-py`) and `docs.databricks.com/api/azure/workspace/database`.
