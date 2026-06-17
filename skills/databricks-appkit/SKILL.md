---
name: databricks-appkit
description: >-
  Build, scaffold, and extend Databricks Apps with the AppKit Node.js + React/TypeScript SDK
  (@databricks/appkit, @databricks/appkit-ui). Use this skill whenever the user mentions AppKit,
  "Databricks app", `databricks apps init`/`deploy`, building a data app/dashboard/agent on
  Databricks, or wiring up AppKit plugins (analytics SQL queries, Genie, files/Unity Catalog
  Volumes, Lakebase Postgres, jobs, model serving, vector search, agents). Also trigger when
  writing `config/queries/*.sql`, `config/agents/*/agent.md`, `server/server.ts`, custom AppKit
  plugins, or `useAnalyticsQuery`/`GenieChat`/`useServingStream` frontend code, even if the user
  doesn't say "AppKit" by name. This is the authoritative guardrail against inventing AppKit APIs.
---

# Databricks AppKit

AppKit is a **TypeScript SDK for building production-ready Databricks Apps** with a plugin-based
architecture. Backend is Node.js (`@databricks/appkit`, Express under the hood); frontend is React
(`@databricks/appkit-ui`). It ships opinionated defaults, built-in caching/retry/timeout/telemetry,
SSE streaming, and native integration with SQL Warehouses, Unity Catalog, Genie, Lakebase, and
model serving.

This skill keeps you from hallucinating APIs. **Only use documented exports.** When unsure, verify
against the live docs (see "Verifying APIs" below) rather than guessing.

## When you're doing one of these, read the matching reference first

The SKILL.md body is the map. Detailed, copy-pasteable patterns live in `references/`. Read the
relevant file(s) before writing code — they contain the exact config options, route shapes, and
gotchas that are easy to get wrong.

| Task | Read |
| --- | --- |
| Scaffolding/deploying an app, CLI commands, project structure, env/`app.yaml` | `references/getting-started.md` |
| SQL queries, `useAnalyticsQuery`, charts, `sql.*` params, type generation | `references/analytics-and-frontend.md` |
| Genie, model serving, files (UC Volumes), jobs, Lakebase, vector search | `references/data-plugins.md` |
| AI agents (`config/agents/*.md`, `createAgent`, tools, MCP, HITL approval) | `references/agents.md` |
| Writing a custom plugin, manifests, interceptors, execution context/OBO | `references/custom-plugins.md` |

## Non-negotiable guardrails (apply to ALL AppKit code)

These come straight from AppKit's own LLM guidance. Violating them produces code that fails to
build or behaves insecurely.

1. **Do not invent APIs.** Use only documented exports from `@databricks/appkit` and
   `@databricks/appkit-ui`. Beta features import from `@databricks/appkit/beta` (currently: the
   `agents` plugin, `createAgent`, `tool`, `runAgent`).
2. **`createApp()` is async.** Prefer top-level `await createApp({...})`. If you can't, use
   `createApp({...}).catch(console.error)` — never silently drop the promise.
3. **Never build SQL strings dynamically.** Use file-based queries in `config/queries/*.sql` with
   `:paramName` placeholders, and pass values from the UI via `sql.*` helpers.
4. **Always handle loading / error / empty states** in UI (e.g. `<Skeleton>`, error text, empty
   state). Wrap query parameter objects in `useMemo` or you get infinite refetch loops.
5. **ESM only.** Use `import`/`export`, never `require()`. `package.json` has `"type": "module"`.
   If `tsconfig` sets `verbatimModuleSyntax: true`, use `import type` for type-only imports.
6. **Charts are ECharts-based, not Recharts.** Pass props (`xKey`, `yKey`, `colors`), never
   Recharts children like `<Bar>`/`<XAxis>`.
7. **Security is zero-trust by default.** Mutating agent tools require human approval; file volumes
   default to read-only; MCP hosts are allowlisted. Don't disable these without a clear reason.

## The plugin model (mental model)

Everything is a plugin. You compose an app by passing plugins to `createApp`:

```ts
import { createApp, server, analytics, genie, files, jobs, serving } from "@databricks/appkit";

await createApp({
  plugins: [
    server(),        // always include — owns the Express/Vite HTTP layer
    analytics({}),   // SQL queries against a SQL Warehouse
    genie(),         // natural-language data Q&A
    files(),         // Unity Catalog Volume file ops
    jobs(),          // trigger/monitor Lakeflow Jobs
    serving(),       // proxy to model serving endpoints
  ],
});
```

- `server()` is effectively required — it mounts every other plugin's routes under
  `/api/<pluginName>/...` and serves the React app (Vite in dev, static in prod).
- Plugins initialize in three phases: **core** → **normal** → **deferred** (the server plugin runs
  deferred so it can see other plugins' routes).
- The returned object is typed per registered plugin: `const app = await createApp({...})` then
  `app.genie.sendMessage(...)`, `app.jobs("etl").runNow(...)`, etc.
- Every plugin gets caching/retry/timeout/telemetry "for free" through the execution interceptor
  chain (`execute()` / `executeStream()`).

### Built-in plugins at a glance

| Plugin | Import | Purpose | Reference |
| --- | --- | --- | --- |
| `server` | `@databricks/appkit` | HTTP server, routing, static/Vite serving, `/health` | `references/getting-started.md` |
| `analytics` | `@databricks/appkit` | File-based SQL on SQL Warehouses, typed results, SSE | `references/analytics-and-frontend.md` |
| `genie` | `@databricks/appkit` | AI/BI Genie conversational data Q&A | `references/data-plugins.md` |
| `files` | `@databricks/appkit` | Unity Catalog Volume CRUD, policies, OBO | `references/data-plugins.md` |
| `lakebase` | `@databricks/appkit` | Lakebase Postgres pool (`pg.Pool`, ORM-ready) | `references/data-plugins.md` |
| `jobs` | `@databricks/appkit` | Trigger/monitor Lakeflow Jobs | `references/data-plugins.md` |
| `serving` | `@databricks/appkit` | Model serving invoke/stream proxy | `references/data-plugins.md` |
| `agents` (beta) | `@databricks/appkit/beta` | Host AI agents w/ tools, MCP, HITL | `references/agents.md` |

> Vector search exists in the docs surface but is the least-documented plugin; treat it as
> experimental and verify before relying on it.

## Standard project layout

```
my-app/
├── app.yaml              # Databricks Apps runtime config (command + env bindings)
├── databricks.yml        # Asset bundle / deployment config
├── package.json          # "type": "module"; @databricks/appkit + appkit-ui pinned
├── server/
│   └── server.ts         # createApp({ plugins: [...] })
├── config/
│   ├── queries/          # *.sql (service principal) and *.obo.sql (per-user)
│   └── agents/<id>/agent.md   # markdown-defined agents (frontmatter + prompt)
└── client/
    └── src/              # React 19 app; consumes @databricks/appkit-ui hooks/components
```

## Verifying APIs (do this instead of guessing)

AppKit moves fast (the published template pins ~0.41.x; some docs show 0.2x). When you need exact
signatures or aren't sure something exists:

```bash
npx @databricks/appkit docs            # ALWAYS run with no query first — prints the index
npx @databricks/appkit docs "<query>"  # then view a specific section by its indexed path
npx @databricks/appkit docs --full     # full index incl. every API entry
```

Do **not** guess doc paths — read the index, then open the right entry. The hosted
`llms.txt` (`https://databricks.github.io/appkit/llms.txt`) is the complete LLM guidance if you
have web access. If neither is available, stick to the patterns in this skill's references and flag
any uncertainty to the user rather than inventing an export.

## AI-assisted scaffolding (the intended workflow)

AppKit is "built for humans and AI." The fastest path to a new app is to let the Databricks Agent
Skills + CLI scaffold it, then iterate:

```bash
databricks aitools install     # install Agent Skills for your assistant (one-time)
databricks apps init           # interactive scaffold (pick plugins, resources, deploy)
databricks apps deploy         # build + deploy + run
```

See `references/getting-started.md` for the full lifecycle, manual setup, env vars, and the
related **databricks-builder-app** (a separate Python/FastAPI reference app that hosts a Claude
Code agent exposing 75+ Databricks tools over MCP — useful context, but NOT the AppKit SDK itself).

## Tone for this user's context

This skill's owner builds finance/analytics MVPs on Databricks (Power BI/DAX/SQL background, reads
but doesn't write Python, prefers Next.js + FastAPI). When relevant, lean on AppKit's strengths for
that audience: file-based parameterized SQL (familiar territory), Genie for self-serve analytics,
OBO/service-principal execution for regulated-data access control, and read-only-by-default agent
SQL tools. Note where AppKit diverges from his defaults — it's React (not Next.js) on the frontend
and Node/Express (not FastAPI) on the backend.
