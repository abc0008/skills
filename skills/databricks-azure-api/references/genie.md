# Azure Databricks REST API Reference — Genie Conversation APIs (`/api/2.0/genie/...`)

Reference for building a natural-language "ask your data" chat feature in a Next.js / Node.js app
(server-side TypeScript, plain `fetch()`, no SDK). All endpoints are workspace-level and live under
`https://<workspace>.azuredatabricks.net/api/2.0/genie/...`.

Verified against: the Databricks REST API reference (`docs.databricks.com/api/azure/workspace/genie`),
the Genie Conversation API guide (`docs.databricks.com/aws/en/genie/conversation-api`), and the
official Databricks SDK definitions (Python `databricks-sdk-py` and Go `databricks-sdk-go`
`service/dashboards`), which are generated from the same OpenAPI spec as the REST docs.

---

## Table of contents

1. [Conventions, auth, and prerequisites](#conventions-auth-and-prerequisites)
2. [Spaces](#spaces)
   - `GET /api/2.0/genie/spaces` (list spaces)
   - `GET /api/2.0/genie/spaces/{space_id}` (get space)
   - Space management (create / update / trash) — brief
3. [Conversations and messages](#conversations-and-messages)
   - `POST .../start-conversation`
   - `POST .../conversations/{conversation_id}/messages` (follow-up message)
   - `GET .../messages/{message_id}` (get message / poll status)
   - Message status enum (full)
   - `GET .../conversations/{conversation_id}/messages` (list messages)
   - `GET .../conversations` (list conversations)
   - `DELETE .../conversations/{conversation_id}` (delete conversation)
   - `DELETE .../messages/{message_id}` (delete message)
   - `POST .../messages/{message_id}/feedback` (send feedback)
4. [The attachments model](#the-attachments-model)
5. [Query results](#query-results)
   - `GET .../attachments/{attachment_id}/query-result`
   - `POST .../attachments/{attachment_id}/execute-query` (re-run expired)
6. [Full query result download flow](#full-query-result-download-flow)
   - `POST .../attachments/{attachment_id}/downloads` (generate)
   - `GET .../attachments/{attachment_id}/downloads/{download_id}` (retrieve)
7. [Deprecated endpoints — do not use](#deprecated-endpoints--do-not-use)
8. [The polling loop pattern](#the-polling-loop-pattern)
9. [Complete TypeScript `askGenie()` helper](#complete-typescript-askgenie-helper)
10. [TypeScript: full-result download snippet](#typescript-full-result-download-snippet)
11. [Rate limits, size limits, timeouts](#rate-limits-size-limits-timeouts)
12. [UI considerations for a chat interface](#ui-considerations-for-a-chat-interface)
13. [Gotchas](#gotchas)

---

## Conventions, auth, and prerequisites

```ts
// Shared helpers assumed throughout this document.
const HOST = process.env.DATABRICKS_HOST!; // e.g. "https://adb-1234567890123456.7.azuredatabricks.net"
declare function getToken(): Promise<string>; // PAT or Microsoft Entra / OAuth access token

async function dbxFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${HOST}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${await getToken()}`,
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store", // important in Next.js — never cache Genie polling calls
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`Databricks ${init.method ?? "GET"} ${path} -> ${res.status}: ${body}`);
  }
  return (await res.json()) as T;
}
```

- **Auth**: `Authorization: Bearer <token>`. Databricks recommends OAuth U2M (on-behalf-of user)
  or OAuth M2M (service principal) for production; workspace PATs also work. On Azure, a
  Microsoft Entra ID token for the AzureDatabricks resource works as the bearer token.
- **Identity matters**: Genie enforces Unity Catalog permissions **as the calling identity**. A
  service principal must have access to the space, the warehouse (at least CAN USE on a **pro or
  serverless** SQL warehouse), and SELECT on the underlying tables. Two different callers can get
  different answers/rows from the same space.
- **Permissions on the space**: at least **CAN RUN** to ask questions (CAN VIEW only allows
  viewing the space, not interacting with Genie — a caller with only CAN VIEW gets 403 on
  start-conversation). This matches auth.md §7.2 (grant the service principal CAN_RUN);
  CAN MANAGE for
  `include_all=true` on list-conversations; CAN EDIT for `include_serialized_space=true` on
  get-space.
- **Timestamps** are epoch **milliseconds** (int64) in API responses.
- All IDs (`space_id`, `conversation_id`, `message_id`, `attachment_id`) are opaque 32-char hex
  strings — treat them as opaque strings.

---

## Spaces

### GET /api/2.0/genie/spaces — list spaces

Lists Genie spaces the caller can access.

Query parameters:

| Param | Type | Required | Notes |
|---|---|---|---|
| `page_size` | int | no | Max results per page. |
| `page_token` | string | no | Token from previous response. |

Response:

```json
{
  "spaces": [
    { "space_id": "3c409c00b54a44c79f79da06b82460e2", "title": "Sales Space", "description": "..." }
  ],
  "next_page_token": "..."
}
```

- `spaces[]` items: `space_id` (string), `title` (string), `description` (string, optional).
  The list response **excludes** `serialized_space` and may omit `warehouse_id`.
- Pagination: keep calling with `page_token = next_page_token` until `next_page_token` is
  absent/empty. `spaces` may be missing entirely on an empty page — default to `[]`.

```ts
async function listAllSpaces() {
  const spaces: { space_id: string; title: string; description?: string }[] = [];
  let pageToken: string | undefined;
  do {
    const qs = new URLSearchParams({ page_size: "100" });
    if (pageToken) qs.set("page_token", pageToken);
    const page = await dbxFetch<{ spaces?: typeof spaces; next_page_token?: string }>(
      `/api/2.0/genie/spaces?${qs}`
    );
    spaces.push(...(page.spaces ?? []));
    pageToken = page.next_page_token || undefined;
  } while (pageToken);
  return spaces;
}
```

### GET /api/2.0/genie/spaces/{space_id} — get space

Returns details of a single Genie space.

Query parameters:

| Param | Type | Required | Notes |
|---|---|---|---|
| `include_serialized_space` | bool | no | Returns the space definition JSON; requires at least CAN EDIT on the space. |

Response fields (`GenieSpace`): `space_id` (string), `title` (string), `description` (string),
`warehouse_id` (string), `parent_path` (string, workspace folder), `etag` (string, for optimistic
concurrency on update), `serialized_space` (string, only when requested).

Errors: `403` if no access to the space, `404` for unknown/trashed `space_id`.

### Space management (brief)

Current, non-deprecated management endpoints exist but are usually not needed for a chat app:

- `POST /api/2.0/genie/spaces` — create a space from a `serialized_space` payload
  (required: `warehouse_id`, `serialized_space`; optional: `title`, `description`, `parent_path`).
- `PATCH /api/2.0/genie/spaces/{space_id}` — update (any of `title`, `description`,
  `warehouse_id`, `serialized_space`, `parent_path`, with `etag` for concurrency).
- `DELETE /api/2.0/genie/spaces/{space_id}` — trash the space (recoverable via workspace trash).

---

## Conversations and messages

### POST /api/2.0/genie/spaces/{space_id}/start-conversation

Starts a **new** conversation with a first question. Returns immediately — processing is
asynchronous; you must poll the message afterwards.

Request body:

| Field | Type | Required | Notes |
|---|---|---|---|
| `content` | string | **yes** | The user's natural-language question. |

Response (note: contains **both** the conversation and the first message, plus convenience IDs):

```json
{
  "conversation_id": "6a64adad2e664ee58de08488f986af3e",
  "message_id": "e1ef34712a29169db030324fd0e1df5f",
  "conversation": {
    "id": "6a64adad2e664ee58de08488f986af3e",
    "space_id": "3c409c00b54a44c79f79da06b82460e2",
    "title": "Give me top sales for last month",
    "created_timestamp": 1719769718,
    "last_updated_timestamp": 1719769718,
    "user_id": 12345
  },
  "message": {
    "id": "e1ef34712a29169db030324fd0e1df5f",
    "conversation_id": "6a64adad2e664ee58de08488f986af3e",
    "space_id": "3c409c00b54a44c79f79da06b82460e2",
    "content": "Give me top sales for last month",
    "status": "IN_PROGRESS",
    "attachments": null,
    "error": null,
    "query_result": null,
    "created_timestamp": 1719769718,
    "user_id": 12345
  }
}
```

- The conversation `title` is auto-derived from the first question.
- The returned message `status` starts as `IN_PROGRESS`/`SUBMITTED` — never final. Poll get-message.
- Errors: `403` (no space access), `404` (bad space id), `429` (rate limited — see
  [Rate limits](#rate-limits-size-limits-timeouts)).

### POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages — follow-up

Creates a new message (follow-up question) in an existing conversation. **The AI response uses all
previously created messages in the conversation as context**, so pronouns and refinements
("only for Q2", "which of these customers...") work.

Request body:

| Field | Type | Required | Notes |
|---|---|---|---|
| `content` | string | **yes** | Follow-up question. |

Response: a single `GenieMessage` object (same shape as `message` above, includes `message_id`).
Again asynchronous — poll get-message.

### GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id} — get message (poll)

Returns the current state of a message. This is the endpoint you poll.

Response — `GenieMessage`:

| Field | Type | Notes |
|---|---|---|
| `id` / `message_id` | string | Message ID. |
| `space_id`, `conversation_id` | string | |
| `content` | string | The user's question text. |
| `status` | enum | See table below. |
| `attachments` | array | Populated as processing progresses; final on `COMPLETED`. See [attachments model](#the-attachments-model). |
| `error` | object | `{ "type": "<MessageErrorType>", "error": "<human message>" }` when `status = FAILED`. |
| `query_result` | object | **Deprecated** (legacy inline result with `statement_id`, `row_count`). Ignore; use the attachment query-result endpoint. |
| `created_timestamp`, `last_updated_timestamp` | int64 | Epoch ms. |
| `user_id` | int64 | Author. |

#### Message status enum (complete, from the API spec)

| Status | Meaning |
|---|---|
| `SUBMITTED` | Message has been submitted. |
| `FILTERING_CONTEXT` | Running the smart-context step to determine relevant context. |
| `FETCHING_METADATA` | Fetching metadata from the data sources. |
| `ASKING_AI` | Waiting for the LLM to respond to the user's question. |
| `PENDING_WAREHOUSE` | Waiting for a SQL warehouse before the generated query can start executing (warehouse cold start shows up here). |
| `EXECUTING_QUERY` | Executing the generated SQL query. The result can already be fetched via the attachment query-result endpoint at this stage. |
| `COMPLETED` | Processing finished. Responses are in the `attachments` field — terminal (success). |
| `FAILED` | Response generation or query execution failed — terminal. See the `error` field. |
| `QUERY_RESULT_EXPIRED` | The SQL result is no longer available; re-run via `execute-query` — terminal-ish (message is done, result is stale). |
| `CANCELLED` | Message was cancelled — terminal. |

Notes:
- Some responses have shown a transitional `IN_PROGRESS` value in older payloads; treat any
  status that is not `COMPLETED` / `FAILED` / `CANCELLED` / `QUERY_RESULT_EXPIRED` as "still working".
- The `attachments` array is populated **progressively** (query first, then description, etc.).
  You may show partial content during `PENDING_WAREHOUSE` / `EXECUTING_QUERY` instead of waiting
  for `COMPLETED`.
- Sample `MessageErrorType` values worth handling: `NO_TABLES_TO_QUERY_EXCEPTION` (question not
  answerable from the space's tables), `SQL_EXECUTION_EXCEPTION`, `WAREHOUSE_NOT_FOUND_EXCEPTION`,
  `RATE_LIMIT_EXCEEDED_GENERIC_EXCEPTION`, `CONTEXT_EXCEEDED_EXCEPTION`,
  `GENERATED_SQL_QUERY_TOO_LONG_EXCEPTION`, `DESCRIBE_QUERY_TIMEOUT`,
  `INVALID_SQL_UNKNOWN_TABLE_EXCEPTION`, `TABLES_MISSING_EXCEPTION` (there are ~60 values —
  show `error.error` text to the user, switch on `error.type` only for special handling).

### GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages — list messages

Lists messages in a conversation (for rehydrating chat history in the UI).

Query params: `page_size` (int, optional), `page_token` (string, optional).

Response: `{ "messages": [GenieMessage, ...], "next_page_token": "..." }` — each item is a full
`GenieMessage` including `status` and `attachments`, so you can rebuild the transcript (user turns
come from `content`, assistant turns from `attachments`).

### GET /api/2.0/genie/spaces/{space_id}/conversations — list conversations

Query params:

| Param | Type | Required | Notes |
|---|---|---|---|
| `include_all` | bool | no | Include all users' conversations in the space; requires at least CAN MANAGE on the space. Default: only the caller's conversations. |
| `page_size` | int | no | |
| `page_token` | string | no | |

Response: `{ "conversations": [ { "conversation_id", "space_id", "title", "user_id",
"created_timestamp", "last_updated_timestamp" } ], "next_page_token": "..." }`.

### DELETE /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id} — delete conversation

Deletes a conversation and its messages. Empty response body on success (200/204). Use this for a
"clear chat" feature and for hygiene — spaces have an upper bound on stored conversations
(on the order of 10,000 per space per the guide), so long-running bots should delete old threads.

### DELETE .../conversations/{conversation_id}/messages/{message_id} — delete message

Deletes a single message from a conversation. Empty response on success.

### POST .../messages/{message_id}/feedback — send feedback

Body: `{ "rating": "POSITIVE" | "NEGATIVE" | "NONE", "comment": "optional text" }`. Useful for
thumbs-up/down buttons in your chat UI; feedback shows up in the space's monitoring for curators.
(Related but optional: message comments endpoints exist at `POST/GET .../messages/{id}/comments`
and `GET .../conversations/{id}/list-comments`.)

---

## The attachments model

The assistant's answer to a message lives in `message.attachments: GenieAttachment[]`. Each
attachment has an `attachment_id` plus **exactly one** payload key set:

```jsonc
{
  "attachment_id": "0195...c9e",
  // EITHER a text attachment (pure natural-language answer / summary):
  "text": {
    "id": "...",
    "content": "Sales were highest in December...",
    "purpose": "FOLLOW_UP_QUESTION" // optional; usually absent for the main answer
  },
  // OR a query attachment (Genie wrote SQL):
  "query": {
    "id": "...",
    "title": "Top sales last month",            // short name for the query
    "description": "This query returns ...",     // NL description of what the SQL does
    "query": "SELECT customer, SUM(amount) ...", // the generated SQL text
    "statement_id": "01f0...",                   // Statement Execution API statement ID
    "query_result_metadata": { "row_count": 42, "is_truncated": false },
    "parameters": [ { "keyword": "start_date", "sql_type": "DATE", "value": "2026-07-01" } ],
    "thoughts": [ { "content": "...", "thought_type": "..." } ], // reasoning trace, may be absent
    "last_updated_timestamp": 1719769750
  },
  // OR suggested follow-up questions:
  "suggested_questions": { "questions": ["..."] }
}
```

Key points:

- **Text attachment** (`text.content`): the conversational answer. Present for pure-knowledge
  answers ("what does churn mean in this space?") and often alongside a query as a summary.
- **Query attachment** (`query`): the generated SQL is in `attachment.query.query`; a
  human-readable `description` explains it. The **rows are NOT in the message** — fetch them with
  the [query-result endpoint](#query-results) using this attachment's `attachment_id`.
- `query.parameters` being present indicates the answer used a **trusted asset**
  (parameterized example query defined by the space curator) rather than free-form SQL.
- `query_result_metadata.is_truncated === true` means the inline result was capped; offer the
  [full download flow](#full-query-result-download-flow).
- A message can contain multiple attachments (e.g. one `text` + one `query`, or a
  `suggested_questions` attachment). Iterate the array; don't assume `attachments[0]`.
- A newer beta adds visualization attachments (rendered chart PNG via
  `GET /api/2.0/genie/spaces/.../download-visualization`); it is beta and not supported on
  Private Link workspaces — treat as optional.

---

## Query results

### GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/query-result

Gets the SQL query result for a **query attachment**. Only valid when the message has a query
attachment and message status is `EXECUTING_QUERY` or `COMPLETED`.

Response:

```jsonc
{
  "statement_response": {           // same schema as SQL Statement Execution API
    "statement_id": "01f0...",
    "status": { "state": "SUCCEEDED" }, // PENDING | RUNNING | SUCCEEDED | FAILED | CANCELED | CLOSED
    "manifest": {
      "format": "JSON_ARRAY",
      "schema": {
        "column_count": 2,
        "columns": [
          { "name": "customer", "type_name": "STRING", "type_text": "STRING", "position": 0 },
          { "name": "total",    "type_name": "DECIMAL", "type_text": "DECIMAL(18,2)", "position": 1 }
        ]
      },
      "total_row_count": 42,
      "truncated": false
    },
    "result": {
      "row_count": 42,
      "data_array": [ ["Acme", "1023.50"], ["Globex", "998.10"] ]  // rows as arrays of strings
    }
  }
}
```

- `statement_response` follows the **SQL Statement Execution API** (`/api/2.0/sql/statements`)
  response schema: `data_array` is an array of rows, each row an array of **string** values
  (numbers/dates come back as strings; convert using `manifest.schema.columns[i].type_name`).
  `NULL` is `null`.
- If `status.state` is `PENDING`/`RUNNING` (possible while message is `EXECUTING_QUERY`), poll this
  endpoint again; when in doubt, just keep polling get-message until `COMPLETED` and then fetch.
- If the underlying result has expired you'll get a failure here / `QUERY_RESULT_EXPIRED` on the
  message — call `execute-query` (below) and then fetch the result again.
- Large results may be chunked/truncated (`manifest.truncated`, `chunks` in the manifest); the
  inline JSON response only carries the first chunk. For everything, use the
  [download flow](#full-query-result-download-flow).

### POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/execute-query

Re-executes the SQL for a message query attachment. **Use when the query attachment's result has
expired** (`QUERY_RESULT_EXPIRED`) — e.g. when a user re-opens an old conversation and clicks a
stale result. Empty request body. Response: same `{ statement_response }` shape as above (may be
in `RUNNING` state initially; poll the query-result endpoint until `SUCCEEDED`).

```ts
async function rerunExpired(spaceId: string, conversationId: string, messageId: string, attachmentId: string) {
  const base = `/api/2.0/genie/spaces/${spaceId}/conversations/${conversationId}/messages/${messageId}/attachments/${attachmentId}`;
  await dbxFetch(`${base}/execute-query`, { method: "POST" });
  // then poll:
  for (;;) {
    const r = await dbxFetch<{ statement_response?: any }>(`${base}/query-result`);
    const state = r.statement_response?.status?.state;
    if (state === "SUCCEEDED") return r.statement_response;
    if (state === "FAILED" || state === "CANCELED" || state === "CLOSED")
      throw new Error(`Query re-execution ${state}`);
    await new Promise((res) => setTimeout(res, 1000));
  }
}
```

---

## Full query result download flow

Two-step flow to get the **complete** result set (beyond the inline/truncated first chunk).
This initiates a **new SQL execution** — it re-runs the query and is billed as such.

### Step 1 — POST .../attachments/{attachment_id}/downloads (generate)

`POST /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/downloads`

Empty body. Response:

```json
{
  "download_id": "abc123...",
  "download_id_signature": "eyJhbGciOi..." 
}
```

- `download_id`: use to track/poll the download.
- `download_id_signature`: a JWT signing the `download_id` for secure access — you must send it
  back verbatim in step 2.

### Step 2 — GET .../attachments/{attachment_id}/downloads/{download_id}?download_id_signature=... (retrieve/poll)

`GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/attachments/{attachment_id}/downloads/{download_id}?download_id_signature=<jwt>`

`download_id_signature` goes in the **query string** (URL-encode it). Poll this endpoint until the
execution completes. Response: `{ "statement_response": { ... } }` — Statement Execution schema.
While the new execution is running, `statement_response.status.state` is `PENDING`/`RUNNING`;
keep polling (~1s). On `SUCCEEDED`, the full result is delivered via the manifest — for large
results this uses `EXTERNAL_LINKS` disposition: `result.external_links[]` entries contain
presigned `external_link` URLs (plus `chunk_index`, `row_count`, `byte_count`,
`next_chunk_index`, and an `expiration` timestamp). Download each link with a **plain** fetch
(no Authorization header — they're presigned cloud-storage URLs).

Expiry and caveats:

- Presigned external links are **short-lived** (Statement Execution external links expire on the
  order of 15 minutes; each entry carries an `expiration` field — honor it and re-generate if it
  lapses). Don't store the links; stream them to the user immediately.
- The `download_id`/signature pair is single-flow state; if it goes stale, just call step 1 again.
- Because step 1 re-executes SQL, results can differ from what the user saw inline if data changed.

---

## Deprecated endpoints — do not use

These appear in older blog posts and must NOT be used in new code:

- `GET .../messages/{message_id}/query-result` (**getMessageQueryResult**) — replaced by the
  per-attachment `GET .../attachments/{attachment_id}/query-result`.
- `GET .../messages/{message_id}/query-result/{attachment_id}` (**getMessageQueryResultByAttachment**)
  — same replacement.
- `POST .../messages/{message_id}/execute-query` (**executeMessageQuery**) — replaced by
  `POST .../attachments/{attachment_id}/execute-query`.
- `message.query_result` field on `GenieMessage` — legacy inline result; ignore it.

---

## The polling loop pattern

There is **no streaming/webhook/SSE support** — the Conversation API is poll-based:

1. `POST start-conversation` (or `POST .../messages` for a follow-up) with the question.
2. Poll `GET .../messages/{message_id}` every ~1 second, backing off toward ~5s (docs recommend
   1–5s, backing off up to 60s max; cap total polling at ~10 minutes and surface a timeout).
3. Stop when `status` is `COMPLETED` (or `FAILED` / `CANCELLED` / `QUERY_RESULT_EXPIRED`).
4. Read `attachments`: collect `text.content`, and for each `query` attachment fetch
   `GET .../attachments/{attachment_id}/query-result` for the rows.
5. Optionally: show intermediate progress by mapping status → label ("Understanding your
   question…", "Waiting for warehouse…", "Running SQL…"). The SQL text is often available in
   `attachments` before `COMPLETED` (during `EXECUTING_QUERY`), so you can render it early.

First questions after idle are slow if the SQL warehouse is cold — expect tens of seconds stuck in
`PENDING_WAREHOUSE` on a pro warehouse (serverless is much faster to start).

---

## Complete TypeScript `askGenie()` helper

```ts
// ---- types (minimal, matching the REST payloads) ----
interface GenieAttachment {
  attachment_id: string;
  text?: { id?: string; content: string; purpose?: string };
  query?: {
    id?: string;
    title?: string;
    description?: string;
    query: string;
    statement_id?: string;
    query_result_metadata?: { row_count?: number; is_truncated?: boolean };
    parameters?: { keyword: string; sql_type?: string; value?: string }[];
  };
  suggested_questions?: { questions?: string[] };
}

interface GenieMessage {
  id?: string;
  message_id?: string;
  conversation_id: string;
  space_id: string;
  content: string;
  status: string;
  attachments?: GenieAttachment[] | null;
  error?: { type?: string; error?: string } | null;
}

interface StatementResponse {
  statement_id?: string;
  status?: { state: string; error?: { message?: string } };
  manifest?: {
    schema?: { columns?: { name: string; type_name: string; position: number }[] };
    total_row_count?: number;
    truncated?: boolean;
  };
  result?: { data_array?: (string | null)[][]; row_count?: number };
}

export interface GenieAnswer {
  text: string | null;                       // NL answer/summary (concatenated text attachments)
  sql: string | null;                        // generated SQL (first query attachment)
  sqlDescription: string | null;
  columns: { name: string; type: string }[]; // schema of the result
  rows: (string | null)[][];                 // first-chunk rows (strings; convert per column type)
  truncated: boolean;
  suggestedQuestions: string[];
  conversationId: string;
  messageId: string;
  attachmentId: string | null;               // query attachment id (for re-run / full download)
}

const TERMINAL = new Set(["COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"]);

export async function askGenie(
  spaceId: string,
  question: string,
  conversationId?: string,
  opts: { timeoutMs?: number } = {}
): Promise<GenieAnswer> {
  const timeoutMs = opts.timeoutMs ?? 10 * 60_000; // docs: cap polling at ~10 minutes

  // 1) start conversation or send follow-up
  let convId: string, msgId: string;
  if (!conversationId) {
    const started = await dbxFetch<{
      conversation_id?: string; message_id?: string;
      conversation: { id: string }; message: { id: string };
    }>(`/api/2.0/genie/spaces/${spaceId}/start-conversation`, {
      method: "POST",
      body: JSON.stringify({ content: question }),
    });
    convId = started.conversation_id ?? started.conversation.id;
    msgId = started.message_id ?? started.message.id;
  } else {
    convId = conversationId;
    const msg = await dbxFetch<GenieMessage>(
      `/api/2.0/genie/spaces/${spaceId}/conversations/${convId}/messages`,
      { method: "POST", body: JSON.stringify({ content: question }) }
    );
    msgId = msg.message_id ?? msg.id!;
  }

  const msgPath = `/api/2.0/genie/spaces/${spaceId}/conversations/${convId}/messages/${msgId}`;

  // 2) poll get-message: 1s -> 5s backoff, hard timeout
  const start = Date.now();
  let delay = 1000;
  let message: GenieMessage;
  for (;;) {
    message = await dbxFetch<GenieMessage>(msgPath);
    if (TERMINAL.has(message.status)) break;
    if (Date.now() - start > timeoutMs) throw new Error("Genie timed out (still " + message.status + ")");
    await new Promise((r) => setTimeout(r, delay));
    delay = Math.min(Math.round(delay * 1.4), 5000);
  }

  if (message.status === "FAILED")
    throw new Error(`Genie failed: ${message.error?.type ?? ""} ${message.error?.error ?? "unknown error"}`);
  if (message.status === "CANCELLED") throw new Error("Genie message was cancelled");
  // QUERY_RESULT_EXPIRED: SQL exists but result is stale — we re-run below.

  // 3) read attachments
  const attachments = message.attachments ?? [];
  const text =
    attachments.filter((a) => a.text?.content).map((a) => a.text!.content).join("\n\n") || null;
  const suggestedQuestions = attachments.flatMap((a) => a.suggested_questions?.questions ?? []);
  const queryAtt = attachments.find((a) => a.query);

  let sql: string | null = null, sqlDescription: string | null = null, attachmentId: string | null = null;
  let columns: { name: string; type: string }[] = [];
  let rows: (string | null)[][] = [];
  let truncated = false;

  if (queryAtt?.query) {
    sql = queryAtt.query.query;
    sqlDescription = queryAtt.query.description ?? null;
    attachmentId = queryAtt.attachment_id;
    const attBase = `${msgPath}/attachments/${attachmentId}`;

    // 4) fetch rows (re-running first if the result expired)
    if (message.status === "QUERY_RESULT_EXPIRED") {
      await dbxFetch(`${attBase}/execute-query`, { method: "POST" });
    }
    let sr: StatementResponse | undefined;
    for (let d = 1000; ; d = Math.min(d * 1.4, 5000)) {
      const res = await dbxFetch<{ statement_response?: StatementResponse }>(`${attBase}/query-result`);
      sr = res.statement_response;
      const state = sr?.status?.state;
      if (state === "SUCCEEDED") break;
      if (state === "FAILED" || state === "CANCELED" || state === "CLOSED")
        throw new Error(`SQL ${state}: ${sr?.status?.error?.message ?? ""}`);
      if (Date.now() - start > timeoutMs) throw new Error("Timed out waiting for query result");
      await new Promise((r) => setTimeout(r, d));
    }
    columns = (sr!.manifest?.schema?.columns ?? [])
      .sort((a, b) => a.position - b.position)
      .map((c) => ({ name: c.name, type: c.type_name }));
    rows = sr!.result?.data_array ?? [];
    truncated = Boolean(sr!.manifest?.truncated || queryAtt.query.query_result_metadata?.is_truncated);
  }

  return { text, sql, sqlDescription, columns, rows, truncated, suggestedQuestions,
           conversationId: convId, messageId: msgId, attachmentId };
}
```

Usage in a Next.js route handler:

```ts
// app/api/genie/route.ts
export async function POST(req: Request) {
  const { question, conversationId } = await req.json();
  try {
    const answer = await askGenie(process.env.GENIE_SPACE_ID!, question, conversationId);
    return Response.json(answer);
  } catch (e) {
    return Response.json({ error: (e as Error).message }, { status: 502 });
  }
}
```

Note: this whole loop can take minutes on cold warehouses. On Azure Web Apps behind a ~4-minute
(230s default) idle HTTP timeout, do NOT hold one HTTP request open for the entire loop — instead
have the browser call a "start" route (returns `conversationId`/`messageId`) and then a "status"
route repeatedly, mirroring the Databricks polling on your own API.

---

## TypeScript: full-result download snippet

```ts
export async function downloadFullResult(
  spaceId: string, conversationId: string, messageId: string, attachmentId: string
): Promise<{ columns: string[]; chunks: ArrayBuffer[] }> {
  const base = `/api/2.0/genie/spaces/${spaceId}/conversations/${conversationId}` +
               `/messages/${messageId}/attachments/${attachmentId}`;

  // Step 1: initiate (re-executes the SQL)
  const gen = await dbxFetch<{ download_id: string; download_id_signature: string }>(
    `${base}/downloads`, { method: "POST" }
  );

  // Step 2: poll the download until the execution succeeds
  const dlPath = `${base}/downloads/${gen.download_id}` +
    `?download_id_signature=${encodeURIComponent(gen.download_id_signature)}`;
  let sr: any;
  for (let d = 1000; ; d = Math.min(d * 1.5, 5000)) {
    const res = await dbxFetch<{ statement_response?: any }>(dlPath);
    sr = res.statement_response;
    const state = sr?.status?.state;
    if (state === "SUCCEEDED") break;
    if (state === "FAILED" || state === "CANCELED") throw new Error(`Download query ${state}`);
    await new Promise((r) => setTimeout(r, d));
  }

  const columns = (sr.manifest?.schema?.columns ?? []).map((c: any) => c.name);

  // Small results: inline data_array. Large results: presigned external links.
  const chunks: ArrayBuffer[] = [];
  const links: any[] = sr.result?.external_links ?? [];
  if (links.length) {
    for (const link of links) {
      // presigned URL: fetch WITHOUT Authorization header; expires quickly (~15 min, see link.expiration)
      const r = await fetch(link.external_link);
      if (!r.ok) throw new Error(`external link fetch failed: ${r.status}`);
      chunks.push(await r.arrayBuffer());
    }
  } else if (sr.result?.data_array) {
    chunks.push(new TextEncoder().encode(JSON.stringify(sr.result.data_array)).buffer);
  }
  return { columns, chunks };
}
```

Stream the bytes straight through to the browser (e.g. as CSV/JSON download) — do not cache the
presigned URLs server-side.

---

## Rate limits, size limits, timeouts

- **Questions**: Genie is limited to about **20 questions per minute per workspace** (fixed limit,
  confirmed by Databricks; applies across spaces/users in the workspace, UI + API combined). Expect
  `429` responses or `RATE_LIMIT_EXCEEDED_GENERIC_EXCEPTION` message errors when exceeded — queue
  questions in your app and retry with backoff. Standard workspace-wide REST API rate limits also
  apply to the polling `GET` calls, which is one reason not to poll faster than ~1s.
- **Polling guidance (from docs)**: poll every 1–5 s, back off up to 60 s, give up after ~10 min.
- **Result size**: the inline `query-result` response carries only the first chunk of the
  statement result and may be truncated (`manifest.truncated`, `query_result_metadata.is_truncated`;
  Genie caps what it materializes inline the same way the Statement Execution API caps inline JSON
  results). Use the downloads flow for complete data; it delivers via presigned external links with
  per-link `expiration` (~15 min).
- **Result expiry**: statement results age out; old conversations surface `QUERY_RESULT_EXPIRED`
  and need `execute-query` to refresh. Do not persist `statement_id`s expecting them to stay fetchable.
- **Conversation storage**: on the order of 10,000 conversations retained per space — delete old
  ones programmatically for kiosk/bot use.
- **Warehouse**: questions run on the space's SQL warehouse (pro or serverless). Cold-start time
  shows as long `PENDING_WAREHOUSE`; serverless minimizes this. Warehouse auto-stop adds latency
  for sporadic traffic.

---

## UI considerations for a chat interface

- **No streaming.** There is no SSE/WebSocket; responses arrive only via polling. Poll your own
  backend ~1s (with backoff) and show a status-driven progress indicator
  (`FILTERING_CONTEXT`/`ASKING_AI` → "Thinking…", `PENDING_WAREHOUSE` → "Starting compute…",
  `EXECUTING_QUERY` → "Running SQL…"). Render the generated SQL as soon as it appears in
  `attachments` (often during `EXECUTING_QUERY`) for perceived responsiveness.
- **Conversation continuity**: persist `conversationId` client-side per chat session and pass it
  to follow-ups so Genie keeps context. Start a **new** conversation per user session — reusing
  old threads degrades accuracy through unintended context reuse.
- **Rehydrate history** with `listConversations` + `listConversationMessages`; re-run expired
  results on demand rather than eagerly.
- **Render answers** as: NL text (text attachments) + collapsible "View SQL" (query.query +
  description) + result table (typed via `manifest.schema`) + "Download full results" button when
  `truncated`. Offer `suggested_questions` as tappable chips. Wire thumbs up/down to the feedback
  endpoint.
- **Per-user auth**: prefer OAuth on-behalf-of the signed-in user so Unity Catalog row/column
  security applies per user; a shared service principal shows everyone the same data.

---

### One blocking endpoint vs. the ~230 s platform timeout

If the product wants a single `POST /api/genie/ask` that returns the full answer, cap the server-side polling loop well below Azure App Service's ~230 s response limit (3 min is a safe ceiling) and return a `{ pending: true, conversationId, messageId }` payload when the cap is hit, letting the client resume via a status endpoint. For anything user-facing, prefer the split pattern from the start: one endpoint to create the message (returns IDs immediately), one to poll status/result. Genie has no streaming API, so the split pattern is also what enables progress UI ("Generating SQL…", "Running query…") from the message status enum.

## Gotchas

1. **Two shapes for "message id"**: `start-conversation` returns top-level `conversation_id` /
   `message_id` *and* nested `conversation.id` / `message.id`; `GenieMessage` objects may carry
   `id`, `message_id`, or both. Read defensively (`msg.message_id ?? msg.id`).
2. **`COMPLETED` ≠ rows in hand.** The message never contains rows; you must make the extra
   attachment `query-result` call. Conversely a message with only a `text` attachment has no rows
   at all — handle "no query" answers gracefully.
3. **Don't use `message.query_result` or the message-level `query-result`/`execute-query`
   endpoints** — all deprecated; only the per-attachment variants are current.
4. **`data_array` values are all strings** (or null). Convert numerics/dates yourself using
   `manifest.schema.columns[].type_name` before charting/sorting.
5. **`attachments` can be `null`**, and fields appear progressively during processing — never
   assume presence, and re-read the whole message on each poll rather than merging.
6. **`QUERY_RESULT_EXPIRED` is per-viewing, not an error** — the answer/SQL are still valid; call
   `execute-query` then re-fetch. Data may have changed since the original run.
7. **The downloads flow re-runs the SQL** (cost + possibly different data) and its presigned links
   expire in minutes — generate on user click, stream immediately, never cache the URLs. The
   `download_id_signature` must be passed back as a query parameter, URL-encoded (it's a JWT with
   dots and possible special chars).
8. **429s / 20 QPM workspace-wide** — shared across all users and the Genie UI. Serialize
   questions per user and queue globally; retry `429` with `Retry-After`/exponential backoff.
9. **Cold warehouses** make the first question take 30s+; keep the UI honest with
   status text, and consider serverless warehouses for chat-grade latency.
10. **Next.js caching**: route handlers and `fetch` may cache GETs; use `cache: "no-store"` (or
    `export const dynamic = "force-dynamic"`) on all polling calls or you'll poll a stale status
    forever.
11. **Long-running loops vs Azure Web Apps timeouts**: don't hold a single HTTP request open for
    the whole ask→poll→result cycle; expose start/status endpoints and let the browser poll.
12. **Permissions asymmetry**: `include_all=true` (list conversations) needs CAN MANAGE;
    `include_serialized_space=true` (get space) needs CAN EDIT; plain asking needs space access +
    warehouse CAN USE + UC table grants for the **caller's** identity.
13. **Genie answers are probabilistic** — same question can produce different SQL. Show the SQL
    and description so users can verify, and provide the feedback buttons so curators can improve
    the space with instructions/trusted assets.
