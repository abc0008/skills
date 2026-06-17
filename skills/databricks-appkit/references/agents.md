# Agents Plugin (beta) — AI agents on Databricks Apps

The `agents` plugin turns an AppKit app into an AI-agent host: load agents from markdown or
TypeScript, give them tools (including plugin tools and MCP), and serve them over HTTP with
streaming, human-in-the-loop approval, threads, and sub-agents.

> **Beta:** import from `@databricks/appkit/beta` (`agents`, `createAgent`, `tool`, `runAgent`).
> APIs may shift between minor releases.

> **Requires streaming serving endpoints.** Foundation Model APIs (Claude, Llama, GPT) and
> chat-style endpoints stream and work out of the box. Custom single-JSON endpoints (typical
> sklearn/MLflow pyfunc) do **not** stream and fail with "Response body is null — streaming not
> supported." For those, use the `serving` plugin's `/invoke` + `useServingInvoke` instead.

## Table of contents
- [Install](#install)
- [Five ways to define an agent](#five-ways-to-define-an-agent)
- [Tools: plugin tools, ambient tools, scoping](#tools)
- [Built-in SQL agent tools & safety](#built-in-sql-agent-tools--safety)
- [Human-in-the-loop approval](#human-in-the-loop-approval)
- [Auto-inherit posture](#auto-inherit-posture)
- [MCP host policy](#mcp-host-policy)
- [Config reference, limits, runtime API](#config-reference)
- [Frontmatter schema](#frontmatter-schema)

## Install
```ts
import { agents, analytics, files, server } from "@databricks/appkit";
import { agents as agentsPlugin } from "@databricks/appkit/beta";
await createApp({ plugins: [server(), analytics(), files(), agentsPlugin()] });
```
Endpoints: `POST /chat` (streaming, HITL-capable — preferred for user-facing agents),
`POST /invocations` + alias `POST /responses` (non-streaming, OpenAI Responses-compatible, single
JSON; **no HITL** — see warning below), plus thread/cancel/approval routes. Every tool call runs
through `asUser(req)` so SQL runs as the requesting user, file access respects UC ACLs, and
telemetry spans are automatic.

## Five ways to define an agent

**Level 1 — markdown package.** Each agent is `config/agents/<id>/agent.md` (frontmatter + prompt):
```md
---
endpoint: databricks-claude-sonnet-4-5
default: true
---
You are a helpful data assistant running on Databricks.
Use the available tools to query data, browse files, and help users.
```
Agent id = folder name. The agent starts with **no tools** (opt-in). `endpoint`/`model` resolves the
adapter (falls back to `DATABRICKS_AGENT_ENDPOINT`).

**Level 2 — scope tools in frontmatter:**
```md
---
endpoint: databricks-claude-sonnet-4-5
tools:
  - plugin:analytics                            # all analytics.* tools
  - plugin:files: [uploads.read, uploads.list]  # only these
  - plugin:genie: { except: [getConversation] } # everything but this
  - get_weather                                 # ambient tool declared in code
default: true
---
You are a read-only data analyst.
```
Declaring any `tools:` turns off auto-inherit — the agent sees exactly what's listed.

**Level 3 — code-defined (`createAgent`):**
```ts
import { agents, createAgent, tool } from "@databricks/appkit/beta";
import { z } from "zod";

const support = createAgent({
  instructions: "You help customers with data and files.",
  model: "databricks-claude-sonnet-4-5",
  tools(plugins) {
    return {
      ...plugins.analytics.toolkit(),                       // all analytics tools
      ...plugins.files.toolkit({ only: ["uploads.read"] }),  // filtered
      get_weather: tool({
        description: "Weather",
        schema: z.object({ city: z.string() }),
        execute: async ({ city }) => `Sunny in ${city}`,
      }),
    };
  },
});
await createApp({ plugins: [server(), analytics(), files(), agents({ agents: { support } })] });
```
Code agents start with no tools by default (engineers want no surprises; markdown authors get
auto-inherit). The `tools(plugins)` function runs once at setup and is cached. Inline `tool()`
`name` is optional — the record key wins.

**Level 4 — sub-agents.** Each key in `agents: {...}` on an `AgentDefinition` becomes an
`agent-<key>` tool on the parent; child runs with a fresh message list. Cycles rejected at load.
```ts
const supervisor = createAgent({
  instructions: "Coordinate researcher and writer.",
  model: "databricks-claude-sonnet-4-5",
  agents: { researcher, writer },   // exposed as agent-researcher, agent-writer
});
```

**Level 5 — standalone (`runAgent`, no `createApp`/HTTP).** For CI, batch eval, internal scripts:
```ts
import { createAgent, runAgent, tool } from "@databricks/appkit/beta";
const classifier = createAgent({ instructions: "Classify tickets.", model: "databricks-claude-sonnet-4-5",
  tools(plugins) { return { ...plugins.analytics.toolkit() }; } });
const result = await runAgent(classifier, { messages: "is ticket 42 a duplicate?", plugins: [analytics()] });
```
Standalone runs as the **service principal** (no OBO) and **bypasses the approval gate** — treat it
as trusted-prompt only. Hosted MCP tools are `agents()`-only (need the live MCP client). Plugins
whose `setup()` needs `createApp` runtime throw a clear "use createApp instead" at init.

## Tools
Tool sources mix freely:
- `plugin:<name>` — all tools from a plugin. `plugin:<name>: [t1,t2]` — only those.
  `plugin:<name>: { only, except, rename, prefix }` — full `ToolkitOptions`.
- bare `<key>` — ambient tool resolved against `agents({ tools: {...} })`.
- In code: `plugins.<name>.toolkit(opts?)` with the same options
  (`only` allowlist, `except` denylist, `prefix` to drop the `name.` prefix, `rename` map).
- `tool(config)` factory: `{ description, schema (Zod), execute, annotations?, autoInheritable? }`.
  Generates JSON Schema via `z.toJSONSchema()`, validates args at runtime, returns a formatted error
  string to the LLM on validation failure (model self-corrects).
- `mcpServer(name, url)` — declares a custom MCP server tool (positional sugar for the verbose
  `custom_mcp_server` wrapper).

Plugins without a `toolkit()` method (third-party `toPlugin` plugins) fall back to walking
`getAgentTools()` with synthesized `${plugin}.${local}` keys, still honoring only/except/rename/prefix.
Referencing an unregistered plugin throws at setup with an `Available: …` listing.

## Built-in SQL agent tools & safety
- **`analytics.query`** — runs under the caller's **OBO** token. `readOnly: true` is enforced at
  execution: statements are tokenized and only `SELECT/WITH/SHOW/EXPLAIN/DESCRIBE/DESC` are
  accepted; writes, DDL, and stacked statements are rejected before reaching the warehouse.
- **`lakebase.query`** — **not registered by default.** The Lakebase pool is bound to the app SP, so
  this tool runs as the SP regardless of end user. Opt in explicitly:
  ```ts
  lakebase({ exposeAsAgentTool: { iUnderstandRunsAsServicePrincipal: true, readOnly: true } });
  ```
  With `readOnly: true` (default) the SQL classifier applies AND the statement is wrapped in
  `BEGIN READ ONLY; … ROLLBACK;`. With `readOnly: false` it accepts arbitrary SQL, is annotated
  `effect: "destructive"`, and triggers HITL approval on every call.

This read-only-by-default SQL posture is exactly what regulated-finance agents want: let an LLM
answer data questions without any path to mutate.

## Human-in-the-loop approval
Any tool annotated with a mutating effect (`effect: "write" | "update" | "destructive"`, or legacy
`destructive: true`) requires explicit user approval before executing. Secure by default.

Flow: plugin emits `appkit.approval_pending` SSE (carrying `approval_id`, `stream_id`, `tool_name`,
`args`, `annotations`) → client renders an approval prompt → the **same user** posts
`POST /api/agent/approve` `{ streamId, approvalId, decision: "approve"|"deny" }` (with the user's
`x-forwarded-user` / `x-forwarded-access-token`). An approve from a different user → 403. No decision
within `approval.timeoutMs` (default 60s) → auto-deny. Denied → the LLM gets a denial string and can
replan. `POST /api/agent/cancel` denies all pending approvals on the stream.

> **No HITL on `/invocations` and `/responses`.** The non-streaming surface can't surface a mid-call
> approval. When `approval.requireForDestructive` is on (default) and the agent has any mutating
> tool, those endpoints reject with HTTP 400 before running. Move HITL agents to `POST /chat`, or set
> `agents({ approval: { requireForDestructive: false } })` for autonomous back-office agents.

## Auto-inherit posture
Two-key: the developer opts in (`autoInheritTools`) AND the plugin author marks each tool
`autoInheritable: true`. Both required. Mutating tools are never auto-inherited even when opted in.
```ts
agents({ autoInheritTools: true });             // both origins
agents({ autoInheritTools: { file: true } });   // markdown agents only
```
Core plugin markings: `analytics.query` ✓ (OBO read-only); `files.list/read/exists/metadata` ✓;
`files.upload/delete` ✗; `genie.getConversation` ✓; `genie.sendMessage` ✗; `lakebase.query` ✗.
Setup logs what each agent inherited vs skipped.

## MCP host policy
Zero-trust on every MCP URL. By default only **same-origin Databricks workspace URLs** (matching
`DATABRICKS_HOST`) are reachable; everything else must be in `mcp.trustedHosts`, and workspace
credentials are never forwarded to those hosts.
```ts
agents({
  agents: { support: createAgent({ instructions: "…",
    tools: { "mcp.internal": mcpServer("internal", "https://mcp.corp.internal/mcp") } }) },
  mcp: { trustedHosts: ["mcp.corp.internal"], allowLocalhost: false },
});
```
Rules at connect time: only http/https; plaintext http only for localhost when allowed (default dev
on, prod off); hostname must match workspace / localhost / trustedHosts; resolved DNS must not be
loopback/RFC1918/CGNAT/link-local(169.254 — blocks cloud metadata)/ULA/multicast.

## Config reference
```ts
agents({
  dir?: string | false,            // "./config/agents" default; false disables
  agents?: Record<string, AgentDefinition>,
  defaultAgent?: string,
  defaultModel?: AgentAdapter | Promise<AgentAdapter> | string,
  tools?: Record<string, AgentTool>,             // ambient tools
  autoInheritTools?: boolean | { file?: boolean, code?: boolean },
  threadStore?: ThreadStore,                      // default in-memory
  baseSystemPrompt?: false | string | ((ctx: PromptContext) => string),
  mcp?: { trustedHosts?: string[], allowLocalhost?: boolean },
  approval?: { requireForDestructive?: boolean /*true*/, timeoutMs?: number /*60000*/ },
  limits?: {
    maxConcurrentStreamsPerUser?: number,  // 5 (429 + Retry-After when exceeded)
    maxToolCalls?: number,                 // 50 (shared across sub-agents; aborts run when exhausted)
    maxSubAgentDepth?: number,             // 3
  },
})
```
Static request caps: chat message / invocation input string 64000 chars; input array 100 items;
per-seeded-message content 64000 chars / 100 items.

Runtime API: `app.agents.list()`, `.get(name)`, `.getDefault()`, `.register(name, def)`,
`.reload()`, `.getThreads(userId)`.

## Frontmatter schema
| Key | Type | Notes |
| --- | --- | --- |
| `endpoint` / `model` | string | Serving endpoint name (either works) |
| `tools` | array | Unified tool list (see [Tools](#tools)) |
| `default` | boolean | First (sorted) `default: true` agent becomes default |
| `maxSteps` / `maxTokens` | number | Adapter hints |
| `baseSystemPrompt` | false \| string | Per-agent override; `false` disables AppKit base prompt |
| `ephemeral` | boolean | Delete the thread after the stream finishes (stateless one-shots) |

Unknown keys are logged and ignored; invalid YAML or missing plugin/tool refs throw at boot.
