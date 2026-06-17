# Getting Started, CLI, Project Setup & Deployment

Everything for creating, configuring, running, and deploying an AppKit app.

## Table of contents
- [Prerequisites](#prerequisites)
- [Two ways to start](#two-ways-to-start)
- [Project structure](#project-structure)
- [The server entry point](#the-server-entry-point)
- [Configuration: app.yaml & env vars](#configuration-appyaml--env-vars)
- [Local development & auth](#local-development--auth)
- [The appkit CLI](#the-appkit-cli)
- [App lifecycle management](#app-lifecycle-management)
- [The databricks-builder-app (related, separate project)](#the-databricks-builder-app)

## Prerequisites
- **Node.js v22+** with `npm`.
- **Databricks CLI** (v0.295.0+, v1.0.0+ for Lakebase). Install & configure per the official CLI
  tutorial.

## Two ways to start

**AI-assisted (recommended).** Install the Databricks Agent Skills, then prompt your assistant:
```bash
databricks aitools install            # newer docs: `databricks experimental aitools install`
```
Then e.g. *"Create a new Databricks app that displays a dashboard of the nyc taxi trips dataset."*
The skills let the assistant explore catalogs/schemas/tables, run SQL, run CLI commands, and
scaffold/iterate.

**Manual.**
```bash
databricks apps init      # interactive: creates app, scaffolds code, installs deps, optional deploy
databricks apps deploy    # build + deploy + run
```

## Project structure

```
my-app/
├── app.yaml                 # Databricks Apps runtime config (command + env)
├── databricks.yml           # Asset bundle deployment config
├── package.json             # "type": "module"
├── tsconfig.server.json / tsconfig.client.json
├── server/
│   └── server.ts            # createApp({ plugins: [...] })
├── config/
│   ├── queries/             # *.sql / *.obo.sql
│   └── agents/<id>/agent.md
└── client/
    ├── index.html           # <div id="root"></div> + script -> src/main.tsx
    └── src/                 # React 19 app
```

Notable `package.json` facts (from the current published template, pinned ~`0.41.x`):
- `"type": "module"`, deps `@databricks/appkit` + `@databricks/appkit-ui` (same version, released
  together), `@databricks/sdk-experimental`, `react@19`, `zod`, `react-router` (the published
  template uses **react-router**, not TanStack Router — older docs reference TanStack; follow what
  the actual scaffold gives you).
- Scripts: `dev` = `NODE_ENV=development tsx watch ... server/server.ts`; `build` = build server
  (tsdown) + client (vite, a `rolldown-vite` fork); `sync` = `appkit plugin sync`; `typegen` =
  `appkit generate-types`.
- `predev`/`prebuild` run `sync` + `typegen` automatically — query/serving types regenerate before
  you run.

## The server entry point

Minimal valid app:
```ts
// server/server.ts
import { createApp, server } from "@databricks/appkit";

await createApp({ plugins: [server()] });
```

Realistic app with custom routes via `onPluginsReady` (runs after plugin setup, before the server
starts — the place for async init and `server.extend`):
```ts
import { createApp, server, analytics } from "@databricks/appkit";

await createApp({
  plugins: [server(), analytics({})],
  async onPluginsReady(appkit) {
    appkit.server.extend((app) => {
      app.get("/custom", (_req, res) => res.json({ ok: true }));
    });
  },
});
```

`createApp` full config: `{ plugins, onPluginsReady, cache?, client?, telemetry?,
disableInternalTelemetry? }`. Returns a `Promise<PluginMap>` keyed by plugin name, each with its
`exports()` API plus an `asUser(req)` method for user-scoped execution.

`server()` options: `{ port?, host?, staticPath? }` (defaults: port `DATABRICKS_APP_PORT` || 8000,
host `0.0.0.0`). It adds `/health` → `{ status: "ok" }`, mounts plugin routes under
`/api/<plugin>/...`, runs Vite in dev and serves static (`dist`/`client/dist`/`build`/`public`/`out`)
in prod.

## Configuration: app.yaml & env vars

`app.yaml` defines the runtime command and binds Databricks resources to env vars:
```yaml
command:
  - node
  - build/index.mjs
env:
  - name: DATABRICKS_WAREHOUSE_ID
    valueFrom: sql-warehouse        # analytics plugin
  - name: DATABRICKS_VOLUME_UPLOADS
    valueFrom: volume               # files plugin (one per volume)
```

Key env vars:
| Variable | Used by | Notes |
| --- | --- | --- |
| `DATABRICKS_HOST` | all | Workspace URL (provided by Apps runtime) |
| `DATABRICKS_APP_PORT` | server | Bind port (default 8000) |
| `DATABRICKS_WAREHOUSE_ID` | analytics | Bind via `valueFrom: sql-warehouse` |
| `DATABRICKS_VOLUME_<KEY>` | files | Auto-discovered; suffix becomes volume key (lowercased) |
| `DATABRICKS_GENIE_SPACE_ID` | genie | Default space when `spaces` omitted |
| `DATABRICKS_JOB_ID` / `DATABRICKS_JOB_<NAME>` | jobs | Single vs multi-job |
| `DATABRICKS_SERVING_ENDPOINT_NAME` | serving / agents | Default endpoint; agents default model |
| `DATABRICKS_AGENT_ENDPOINT` | agents | Fallback agent model endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_SERVICE_NAME` | telemetry | Optional OpenTelemetry export |
| `NODE_ENV` | all | `development` enables Vite + OBO dev fallbacks |

## Local development & auth

Authenticate once with the CLI (recommended):
```bash
databricks auth login --host <host> --profile <profile-name>
```
If the profile is `DEFAULT`, `npm run dev` just works. Otherwise set
`DATABRICKS_CONFIG_PROFILE=<profile>`. In dev, OBO (on-behalf-of-user) calls fall back to the
configured credentials with a warning when user tokens aren't present (no reverse proxy locally).

## The appkit CLI

```bash
npx appkit plugin sync --write     # aggregate plugin manifests into appkit.plugins.json
npx appkit plugin create           # scaffold a new custom plugin (interactive)
npx appkit plugin validate         # validate manifest(s) against JSON schema
npx appkit plugin list             # list configured plugins
npx appkit plugin add-resource     # add a resource requirement to a plugin
npx appkit generate-types          # regenerate types from SQL/serving schemas
npx @databricks/appkit docs        # view docs (see SKILL.md "Verifying APIs")
```

## App lifecycle management

```bash
databricks apps deploy                 # build frontend + deploy bundle + run
databricks apps deploy --target prod
databricks apps deploy --var="warehouse_id=abc123"
databricks apps deploy --skip-validation   # faster iteration
databricks apps deploy --force             # override git branch validation
databricks apps start  <name>
databricks apps stop   <name>
databricks apps list
```

## The databricks-builder-app

The second source the user referenced (`databricks-solutions/ai-dev-kit/databricks-builder-app`) is
a **different artifact from the AppKit SDK** — clarify this if it comes up. It is a Python/FastAPI +
React web app that wraps **Claude Code** (`claude-agent-sdk`) behind a chat UI and exposes **75+
Databricks tools** (execute_sql, create_or_update_pipeline, upload_folder, execute_code, …) to the
agent in-process via MCP. It can also run as a standalone **MCP server at `/mcp`** for Genie Code
and other MCP clients.

Relevant patterns it demonstrates (transferable to AppKit thinking, though the stack differs):
- **Per-request auth via contextvars**: extract `X-Forwarded-User` / `X-Forwarded-Access-Token` in
  prod (env `DATABRICKS_HOST`/`DATABRICKS_TOKEN` in dev), set auth context before invoking the
  agent, clear it after — every tool resolves the workspace client from that context. This mirrors
  AppKit's OBO/`asUser(req)` execution-context model.
- **Claude Code sessions** per message with session resumption, SSE streaming of
  text/thinking/tool_use/tool_result, and per-project working-directory isolation.
- **Skills loaded from `.claude/skills`** (e.g. `sdp`, `dabs`, `sdk`).

Use it as a reference for "an AI agent that operates a Databricks workspace," not as a substitute
for AppKit when the goal is shipping a Databricks App.
