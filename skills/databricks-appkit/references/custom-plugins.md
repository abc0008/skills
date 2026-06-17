# Custom Plugins, Manifests, Interceptors & Execution Context

How to extend AppKit beyond the built-in plugins: custom routes/logic, the manifest contract, the
execution interceptor chain, and the OBO/service-principal execution model.

## Table of contents
- [When to write a custom plugin](#when-to-write-a-custom-plugin)
- [Scaffold via CLI](#scaffold-via-cli)
- [Anatomy of a plugin](#anatomy-of-a-plugin)
- [The manifest (resources)](#the-manifest-resources)
- [Config-dependent resources](#config-dependent-resources)
- [Extension points](#extension-points)
- [Execution interceptor chain](#execution-interceptor-chain)
- [Execution context & OBO](#execution-context--obo)
- [SSE streaming](#sse-streaming)
- [Telemetry](#telemetry)

## When to write a custom plugin
Reach for a custom plugin when you need custom API routes, background logic, or to package a reusable
capability with its own resource requirements. For one-off routes you don't need a plugin — use
`onPluginsReady(appkit) { appkit.server.extend((app) => { ... }); }`.

## Scaffold via CLI
```bash
npx @databricks/appkit plugin create        # interactive
npx @databricks/appkit plugin create --placement in-repo --path plugins/my-plugin \
  --name my-plugin --description "My plugin" --force
```
Then `npx appkit plugin sync --write` to register it into `appkit.plugins.json`, and
`npx appkit plugin validate` to check the manifest against the schema.

## Anatomy of a plugin
Author the manifest as JSON (the canonical surface that `appkit plugin sync` reads), attach it via
`static manifest`, subclass `Plugin`, export with `toPlugin()`:

```json
// my-plugin/manifest.json
{
  "$schema": "https://databricks.github.io/appkit/schemas/plugin-manifest.schema.json",
  "name": "my-plugin",
  "displayName": "My Plugin",
  "description": "A custom plugin",
  "resources": {
    "required": [{
      "type": "secret", "alias": "apiKey", "resourceKey": "api-key",
      "description": "API key for external service", "permission": "READ",
      "fields": {
        "scope": { "env": "MY_SECRET_SCOPE", "description": "Secret scope" },
        "key":   { "env": "MY_API_KEY", "description": "Secret key name" }
      }
    }],
    "optional": []
  }
}
```
```ts
// my-plugin/index.ts
import { Plugin, toPlugin, type PluginManifest } from "@databricks/appkit";
import manifest from "./manifest.json";

class MyPlugin extends Plugin {
  static manifest = manifest as PluginManifest<"my-plugin">;

  async setup() { /* init */ }
  myCustomMethod() { /* ... */ }
  async shutdown() { /* cleanup */ }

  exports() { return { myCustomMethod: this.myCustomMethod }; }
}

export const myPlugin = toPlugin(MyPlugin);
```
Consume programmatically once registered:
```ts
const app = await createApp({ plugins: [server(), analytics(), myPlugin()] });
app.myPlugin.myCustomMethod();
```

## The manifest (resources)
Resources are `required` (always) or `optional` (maybe). Each resource declares a `type`
(`sql_warehouse`, `secret`, `database`, `volume`, …), `alias`, `resourceKey`, `permission`
(e.g. `READ`, `CAN_USE`, `CAN_CONNECT_AND_CREATE`, `WRITE_VOLUME`), and `fields` mapping config to
env vars. Static tooling (CLI/docs) reads all possible resources; runtime validation enforces the
ones actually needed. For the full v2.0 contract see `npx @databricks/appkit docs` → plugin manifest.

## Config-dependent resources
When a resource becomes required based on config, list it as `optional` in the manifest and promote
it at runtime via a static `getResourceRequirements(config)`:
```ts
static getResourceRequirements(config: MyPluginConfig) {
  const resources = [];
  if (config.enableCaching) {
    resources.push({
      type: "database", alias: "cache", resourceKey: "cache",
      description: "Query result caching", permission: "CAN_CONNECT_AND_CREATE",
      fields: { instance_name: { env: "DATABRICKS_CACHE_INSTANCE" }, database_name: { env: "DATABRICKS_CACHE_DB" } },
      required: true,
    });
  }
  return resources;
}
```
The built-in `files` plugin uses this pattern to generate one required volume resource per discovered
`DATABRICKS_VOLUME_*`.

## Extension points
- **Routes:** implement `injectRoutes()` using `IAppRouter` to add `/api/<plugin>/...` endpoints.
- **Lifecycle:** override `setup()` and `shutdown()`.
- **Shared services:** `this.cache` (see `CacheConfig`), `this.telemetry` (see `ITelemetry`).
- **Interceptors:** call `this.execute()` / `this.executeStream()` so your op gets caching, retry,
  timeout, and telemetry automatically.
- **`exports()`:** return the object exposed on the `AppKit` handle.
- **Plugin phases:** `core` (framework), `normal` (default), `deferred` (initializes last with
  access to other plugin instances via `config.plugins`; the server plugin is deferred).

## Execution interceptor chain
`execute(fn, settings)` / `executeStream(...)` wrap your operation in this order (outermost →
innermost): **Telemetry** (span) → **Timeout** (AbortSignal) → **Retry** (exponential backoff) →
**Cache** (TTL). Example:
```ts
await this.execute(() => expensiveOperation(), {
  cache: { ttl: 60000 },
  retry: { maxRetries: 3 },
  timeout: 5000,
  telemetry: { traces: true },
});
```

## Execution context & OBO
Two contexts: **ServiceContext** (singleton, SP credentials at startup) and **ExecutionContext**
(per-request: SP or user).

User context comes from headers Databricks Apps injects: `x-forwarded-user` (required in prod) and
`x-forwarded-access-token` (for token passthrough). In a route handler:
```ts
// run as the requesting user (their Databricks permissions / UC ACLs)
const result = await this.asUser(req).query("SELECT ...");
// run as the service principal (default)
const result2 = await this.query("SELECT ...");
```
Context helpers (from `@databricks/appkit`): `getCurrentUserId()`, `getWorkspaceClient()`,
`getWarehouseId()`, `getWorkspaceId()`.

Dev behavior: if `asUser(req)` is called without a user token in `NODE_ENV=development`, it logs a
warning and runs with default credentials (span shows `execution.context: "service"`,
`execution.obo_dev_fallback: true`). In prod, missing required headers fail (e.g. 401/AuthenticationError).

Telemetry span attributes auto-added by the interceptor chain: `execution.context` (`"user"`|`"service"`),
`caller.id`, `execution.obo_dev_fallback`. Use `execute()`/`executeStream()` to get them for free.

Lakebase OBO is special: a separate `pg.Pool` per user (the pool is the auth boundary), not an
AsyncLocalStorage `WorkspaceClient` swap.

## SSE streaming
Built-in SSE with automatic reconnection: connection-ID stream tracking, a ring buffer for missed
events (reconnect via `Last-Event-ID`), per-stream abort signals, heartbeats. `StreamManager` creates
streams from an `AsyncGenerator` handler and handles reconnection + cleanup. Use `executeStream()` so
streamed ops still get telemetry/timeout/etc.

## Telemetry
OpenTelemetry is first-class. `TelemetryManager` (singleton) sets up tracer/meter/logger providers
with auto-instrumentation (Node, Express, HTTP) and exports to `OTEL_EXPORTER_OTLP_ENDPOINT` when
set. `TelemetryProvider` is per-plugin (plugin name as default scope; traces/metrics/logs
configurable). Instrument custom plugins via `this.telemetry`.

## Design philosophy (why the API looks the way it does)
Plugin-first modularity; heavy TypeScript + Zod runtime validation; streaming-first (SSE w/
reconnection); observability first-class; strong DX (HMR, hot reload, source maps); production-ready
and zero-trust from day one; layered extensibility (high-level plugins → low-level primitives →
custom plugins). Graceful shutdown handles SIGTERM/SIGINT with a 15s timeout, aborting in-flight ops.
