# Data & Service Plugins: Genie, Files, Lakebase, Jobs, Model Serving, Vector Search

Reference for the non-analytics built-in plugins. All mount routes under `/api/<plugin>/...` and
share the caching/retry/timeout/telemetry interceptor chain. Most support OBO (`asUser(req)`).

## Table of contents
- [Genie](#genie)
- [Files (Unity Catalog Volumes)](#files-unity-catalog-volumes)
- [Lakebase (Postgres)](#lakebase-postgres)
- [Jobs (Lakeflow)](#jobs-lakeflow)
- [Model Serving](#model-serving)
- [Vector Search](#vector-search)

---

## Genie
Natural-language data Q&A backed by Databricks AI/BI Genie spaces. Great for self-serve analytics.

```ts
import { createApp, genie, server } from "@databricks/appkit";
await createApp({ plugins: [server(), genie()] });
```
Config: `spaces` (`Record<alias, spaceId>`; default reads `DATABRICKS_GENIE_SPACE_ID` as `default`),
`timeout` (default 120000ms; `0` = indefinite). Find the Space ID on the Genie space's **About** tab.
```ts
genie({ spaces: { sales: "01ABCDEF12345678", support: "01GHIJKL87654321" } });
```

Endpoints (`/api/genie`): `POST /:alias/messages` (send a message, SSE) and
`GET /:alias/conversations/:conversationId` (replay history, SSE). SSE event types: `message_start`,
`status` (e.g. `ASKING_AI`, `EXECUTING_QUERY`), `message_result`, `query_result`, `error`.

Programmatic: `app.genie.sendMessage(alias, text)` (async iterable of events),
`app.genie.getConversation(alias, conversationId)`.

Frontend — drop-in chat or custom hook:
```tsx
import { GenieChat, useGenieChat } from "@databricks/appkit-ui/react";

<GenieChat alias="demo" />   // full UI: streaming, history, reconnection. alias must match config.

const { messages, status, sendMessage, reset } = useGenieChat({ alias: "demo" });
```

---

## Files (Unity Catalog Volumes)
CRUD on UC Volume files with caching, policies, and per-volume auth. **Security-critical** — read
the permission model.

```ts
import { createApp, files, server } from "@databricks/appkit";
await createApp({ plugins: [server(), files()] });
```
**Auto-discovery:** the plugin scans env for `DATABRICKS_VOLUME_*`; the suffix (lowercased) becomes
the volume key (`DATABRICKS_VOLUME_UPLOADS` → `uploads`). Explicit `volumes` config merges with
discovered ones (explicit wins for overrides).

```ts
files({
  maxUploadSize: 5_000_000_000,                 // 5 GB default (per-volume override available)
  customContentTypes: { ".avro": "application/avro" },
  volumes: { uploads: { maxUploadSize: 100_000_000 } },
});
```

### Three layers of access control (understand all three)
1. **UC grants** — `WRITE_VOLUME` (or read-equivalent). On the **SP** for service-principal volumes;
   on the **end user** for OBO volumes.
2. **Execution identity** — per-volume `auth`: `"service-principal"` (default) or
   `"on-behalf-of-user"`. Resolution: `VolumeConfig.auth ?? IFilesConfig.auth ?? "service-principal"`.
   `asUser(req)` is a hard override at the SDK level for the programmatic API.
3. **File policies** — `(action, resource, user) => boolean | Promise<boolean>`, evaluated before
   every op. **This is the only gate that distinguishes users on HTTP routes for SP volumes.**

> **Default since v0.21.0:** a volume with no policy defaults to `publicRead()` — **all writes
> (`upload`, `mkdir`, `delete`) are denied.** Set an explicit policy (e.g. `files.policy.allowAll()`)
> on volumes that need writes.

Built-in policies: `files.policy.publicRead()` (reads only), `files.policy.allowAll()`,
`files.policy.denyAll()`. Combinators: `files.policy.all(a,b)` (AND), `files.policy.any(a,b)` (OR),
`files.policy.not(p)`. Custom:
```ts
import { type FilePolicy, WRITE_ACTIONS } from "@databricks/appkit";
const adminOnly: FilePolicy = (action, _res, user) =>
  WRITE_ACTIONS.has(action) ? ["admin-id"].includes(user.id) : true;
files({ volumes: { reports: { policy: adminOnly } } });
```
OBO pattern (deny SP traffic so header-less calls can't reach the volume):
```ts
files({ volumes: { "user-uploads": {
  auth: "on-behalf-of-user",
  policy: (_a, _r, user) => user.isServicePrincipal !== true,
}}});
```

Actions: reads = `list, read, download, raw, exists, metadata, preview`; writes = `upload, mkdir,
delete`. Routes (`/api/files`): `GET /volumes`, `GET /:vol/list|read|download|raw|exists|metadata|preview`,
`POST /:vol/upload|mkdir`, `DELETE /:vol`. Errors: 400 bad path, 403 policy denied, 404 unknown
volume, 413 too large, 500 op failed.

Programmatic API — `app.files("uploads")` returns a `VolumeHandle` with methods `list, read,
download, exists, metadata, upload, createDirectory, delete, preview`, plus `.asUser(req)` for
per-user execution. Without `asUser`, programmatic calls run as the SP regardless of the volume's
`auth` (no request to derive the user from). `read()` caps at 10 MB by default — use `download()` for
larger files. Paths may be absolute (must start `/Volumes/`) or relative (resolved from the volume
env var); `../` traversal is rejected.

Execution tiers: Read (60s cache, 3x retry, 30s timeout); Download (no cache, 3x, 30s);
Write (no cache, no retry, 600s). Inline `/raw` serving forces unsafe types (HTML/JS/SVG) to
download and sets `nosniff` + `sandbox` CSP.

Frontend components: `DirectoryList`, `FileBreadcrumb`, `FilePreviewPanel` (compose a file browser).

---

## Lakebase (Postgres)
OLTP access to Databricks Lakebase Autoscaling. Returns a standard `pg.Pool` with automatic OAuth
token refresh (1-hour tokens, 2-min refresh buffer) — works with Prisma, Drizzle, TypeORM,
Sequelize, raw `pg`.

Two layers: the standalone `@databricks/lakebase` package (full connector) and the AppKit-integrated
wrapper re-exported from `@databricks/appkit`.
```ts
import { createLakebasePool } from "@databricks/appkit";
const pool = createLakebasePool();                  // reads PGHOST, PGDATABASE, LAKEBASE_ENDPOINT
const result = await pool.query("SELECT * FROM users");
```
Setup: create a Lakebase Postgres Autoscaling project, then `databricks apps init` and select the
**Lakebase** plugin (CLI walks you through project/branch/database). Built-in OTel instrumentation
(query duration, pool connections, token refresh).

**OBO note:** Lakebase OBO uses a **separate `pg.Pool` per user** (connections authenticate at
connect time — the pool is the auth boundary), unlike the AsyncLocalStorage `WorkspaceClient` swap
the other plugins use.

---

## Jobs (Lakeflow)
Trigger and monitor Lakeflow Jobs.
```ts
import { createApp, jobs, server } from "@databricks/appkit";
await createApp({ plugins: [server(), jobs()] });
```
Env: `DATABRICKS_JOB_ID` (→ `default`) or `DATABRICKS_JOB_<NAME>` (multi-job). Config: `timeout`
(60000), `pollIntervalMs` (5000), `jobs` (`Record<key, JobConfig>`). Per-job `JobConfig`:
`waitTimeout` (600000), `taskType`, `params` (Zod schema validated → 400 on failure).

`taskType` auto-maps validated params to SDK fields: `notebook`→`notebook_params`,
`python_wheel`→`python_named_params`, `python_script`→`python_params` (`{args}`),
`spark_jar`→`jar_params` (`{args}`), `sql`→`sql_params`, `dbt`→none. Omitted → passthrough.

Routes (`/api/jobs`): `POST /:jobKey/run` (add `?stream=true` for SSE status), `GET /:jobKey/runs`,
`GET /:jobKey/runs/:runId`, `GET /:jobKey/status`, `DELETE /:jobKey/runs/:runId`.

Programmatic: `const etl = app.jobs("etl")` then `etl.runNow(params)`, `etl.runAndWait(params)`
(async iterable of statuses), `etl.lastRun()`, `etl.listRuns({limit})`, `etl.getRun(id)`,
`etl.getRunOutput(id)`, `etl.getJob()`, `etl.cancelRun(id)`. All return `ExecutionResult<T>` —
check `result.ok` before `result.data`.

**Execution context:** runs as the **app SP** by default (jobs are shared infra; the app's resource
binding grants `CAN_MANAGE_RUN` to the SP, so users don't need individual grants). Per-run UI
attribution shows the SP. For user attribution / user-grant enforcement, opt into OBO with
`app.jobs("etl").asUser(req).runNow(...)` (requires `jobs.jobs` in `databricks.yml`
`user_api_scopes` + the user's own `CAN_MANAGE_RUN`).

---

## Model Serving
Authenticated proxy to Databricks Model Serving endpoints (invoke + streaming).
```ts
import { createApp, serving, server } from "@databricks/appkit";
await createApp({ plugins: [server(), serving()] });
```
Env: `DATABRICKS_SERVING_ENDPOINT_NAME` (→ `default`). Config: `endpoints` (`Record<alias,
EndpointConfig>` where each maps to an env var; optional `servedModel` to target a specific model),
`timeout` (120000).
```ts
serving({ endpoints: {
  llm: { env: "DATABRICKS_SERVING_ENDPOINT_NAME" },
  classifier: { env: "DATABRICKS_SERVING_ENDPOINT_CLASSIFIER" },
}});
```
Routes: named mode `POST /api/serving/:alias/invoke` and `/:alias/stream`; default mode
`POST /api/serving/invoke` and `/stream`.

**Execution context:** serving routes run **OBO by default** (enforces per-user `CAN_QUERY`).
Programmatic: `app.serving("llm").invoke({messages})` (SP) or
`app.serving("llm").asUser(req).invoke({messages})` (user).

Type generation: `appKitServingTypesPlugin()` Vite plugin auto-generates TS types from endpoints'
OpenAPI schemas (included automatically by the AppKit dev server) — alias autocomplete + typed
request/response/chunk per endpoint. Endpoints without a streaming response schema get
`chunk: unknown`; use `useServingInvoke` (not `useServingStream`) for those. Frontend hooks:
`useServingInvoke`, `useServingStream`.

---

## Vector Search
A vector-search plugin exists in the docs surface but is the **least documented** of the built-ins.
Treat it as experimental: confirm the exact import, config, and routes with
`npx @databricks/appkit docs` before relying on it, and tell the user it's less battle-tested than
analytics/genie/files.
