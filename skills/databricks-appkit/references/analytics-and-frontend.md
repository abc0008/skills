# Analytics Plugin + Frontend (SQL, hooks, charts)

The analytics plugin is AppKit's core for querying Lakehouse data. SQL lives in files; the frontend
consumes results over SSE with typed hooks. This is the bread-and-butter for dashboards.

## Table of contents
- [Setup](#setup)
- [Query files & execution context](#query-files--execution-context)
- [SQL parameters & the sql.* helpers](#sql-parameters--the-sql-helpers)
- [Server-injected parameters](#server-injected-parameters)
- [HTTP endpoints & formats](#http-endpoints--formats)
- [Frontend: useAnalyticsQuery](#frontend-useanalyticsquery)
- [Warehouse cold-start handling](#warehouse-cold-start-handling)
- [Type-safe queries & type generation](#type-safe-queries--type-generation)
- [Charts (ECharts, not Recharts)](#charts)
- [Frontend checklist](#frontend-checklist)

## Setup
```ts
import { analytics, createApp, server } from "@databricks/appkit";
await createApp({ plugins: [server(), analytics({})] });
```
Requires `DATABRICKS_WAREHOUSE_ID` (bind via `valueFrom: sql-warehouse` in `app.yaml`).
Config options: `warehouseStartupTimeoutMs` (default 300000), `autoStartWarehouse` (default true —
set `false` for cost-controlled deployments so user requests never trigger billable warehouse
starts; a stopped warehouse then surfaces a `ConfigurationError`).

## Query files & execution context
- Put `.sql` files in `config/queries/`. The **query key is the filename without `.sql`**
  (`spend_summary.sql` → `"spend_summary"`).
- **Execution context is decided by the filename, not the call site:**
  - `queryKey.sql` → runs as the **service principal** (shared cache).
  - `queryKey.obo.sql` → runs as the **end user** (OBO, per-user cache). Use this when row-level
    access / UC grants must be enforced per user — important for regulated finance data.

## SQL parameters & the sql.* helpers
Use `:paramName` placeholders. **Never concatenate SQL strings.** Optionally annotate types with
`-- @param` comments:
```sql
-- @param startDate DATE
-- @param endDate DATE
-- @param limit INT
SELECT region, SUM(cost_usd) AS cost
FROM main.fin.spend
WHERE usage_date BETWEEN :startDate AND :endDate
GROUP BY region
LIMIT :limit
```

`-- @param` types (case-insensitive): `STRING`, `BOOLEAN`, `DATE`, `TIMESTAMP`, `BINARY`, `INT`,
`BIGINT`, `TINYINT`, `SMALLINT`, `FLOAT`, `DOUBLE`, `NUMERIC`, `DECIMAL`.

Bind from the UI with the matching `sql.*` helper (import from `@databricks/appkit-ui/js`):
`sql.string()`, `sql.date()`, `sql.boolean()`, `sql.timestamp()`, `sql.int()`, `sql.bigint()`,
`sql.float()`, `sql.double()`, `sql.numeric()` (pass strings to preserve precision), and
`sql.number()` (auto-infers INT vs BIGINT).

**Gotcha:** `LIMIT`/`OFFSET` require Spark `IntegerType`. `BIGINT` is rejected with
`INVALID_LIMIT_LIKE_EXPRESSION.DATA_TYPE`. Annotate the param `INT` or use `sql.int()` /
`sql.number()` for in-range values.

## Server-injected parameters
`:workspaceId` is injected by the server — use it in SQL but **do not** annotate it with `@param`:
```sql
WHERE workspace_id = :workspaceId
```

## HTTP endpoints & formats
Mounted under `/api/analytics`:
- `POST /api/analytics/query/:query_key` — execute with parameters.
- `GET  /api/analytics/arrow-result/:jobId` — fetch binary Arrow payload.

Formats: `JSON` (default) returns JSON rows; `ARROW` streams a `statement_id` over SSE then the
client fetches binary Arrow from the arrow-result endpoint (use for large result sets).

## Frontend: useAnalyticsQuery
```tsx
import { useAnalyticsQuery } from "@databricks/appkit-ui/react";
import { sql } from "@databricks/appkit-ui/js";
import { Skeleton } from "@databricks/appkit-ui";
import { useMemo } from "react";

function SpendTable() {
  // ALWAYS memoize params — a new object every render causes infinite refetches.
  const params = useMemo(() => ({
    startDate: sql.date("2025-01-01"),
    endDate: sql.date("2025-12-31"),
    limit: sql.int(100),
  }), []);

  const { data, loading, error, warehouseStatus } =
    useAnalyticsQuery("spend_summary", params);

  if (warehouseStatus && warehouseStatus.state !== "RUNNING")
    return <div>Warehouse is {warehouseStatus.state.toLowerCase()}…</div>;
  if (loading) return <Skeleton className="h-32 w-full" />;
  if (error) return <div className="text-destructive">{error}</div>;
  if (!data?.length) return <div className="text-muted-foreground">No results</div>;

  return <ul>{data.map((r) => <li key={r.region}>{r.region}: ${r.cost}</li>)}</ul>;
}
```
Signature: `useAnalyticsQuery(queryKey, parameters, options?)` →
`{ data, loading, error, warehouseStatus }`.
Options: `format` (`"JSON"|"ARROW"`, default JSON), `maxParametersSize` (default 102400),
`autoStart` (default true).

## Warehouse cold-start handling
If the warehouse is `STOPPED`/`STARTING`, the plugin auto-starts it (when stopped), streams
`warehouse_status` SSE events until `RUNNING`, then runs the query — so the UI never hangs on a dead
spinner. Render `warehouseStatus` for feedback. After one observed `RUNNING`, requests within ~30s
skip the readiness check (`warehouseStatus` stays `null`).

For multi-chart dashboards, use the shared status surface instead of per-chart spinners:
```tsx
import { ResourceStatusProvider, ResourceStatusIndicator } from "@databricks/appkit-ui/react";

export function AppShell({ children }) {
  return (
    <ResourceStatusProvider>
      <ResourceStatusIndicator />   {/* sonner toast for worst pending resource */}
      {children}
    </ResourceStatusProvider>
  );
}
```
`useAnalyticsQuery` auto-registers with the nearest provider. Alternatives: `useResourceStatusToaster()`
(reuse your own `<Toaster>`), `useResourceStatus({ kind })` (build custom UI), and
`useResourceStatusPublisher()` (publish status for non-analytics resources like Lakebase warmup).

## Type-safe queries & type generation
Augment `QueryRegistry` for full inference on params and results:
```ts
// shared/appkit-types/analytics.d.ts
declare module "@databricks/appkit-ui/react" {
  interface QueryRegistry {
    spend_summary: {
      name: "spend_summary";
      parameters: { startDate: string; endDate: string; limit: number };
      result: Array<{ region: string; cost: number }>;
    };
  }
}
```
Or let AppKit generate these from your `.sql` files: `npx appkit generate-types` (runs
automatically via `predev`/`prebuild`).

## Charts
AppKit chart components are **ECharts-based**. Configure with **props** (`xKey`, `yKey`, `colors`,
`format`) — **never** pass Recharts children (`<Bar>`, `<XAxis>`, `<Line>`). Default `format="auto"`
unless you have a reason to force `"json"`/`"arrow"`. If using tooltips, wrap the root in
`<TooltipProvider>`. (See `@databricks/appkit-ui` `ui/ChartContainer` and the data components for
the current chart surface; verify exact prop names via `npx @databricks/appkit docs`.)

## Frontend checklist
- `useMemo` wraps every parameters object.
- Loading / error / empty states are explicit (`Skeleton`, error text, empty message).
- Charts use props, not Recharts children; `format="auto"` by default.
- Tooltip users wrap the root in `<TooltipProvider>`.
- Only documented `@databricks/appkit-ui` components/hooks — don't invent components.
- Use `import type` for type-only imports when `verbatimModuleSyntax` is on.
