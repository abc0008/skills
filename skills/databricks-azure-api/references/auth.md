# Authentication to Azure Databricks from Server-Side Node.js / Next.js (Azure Web Apps)

Reference for coding agents building Next.js API routes / server actions or plain Node services on
Azure Web Apps that call the Azure Databricks workspace REST API with plain `fetch()` (no SDK).

All Databricks REST calls use a workspace base URL of the form:

```
https://adb-1234567890123456.7.azuredatabricks.net
```

and a header `Authorization: Bearer <token>`. This document covers every supported way to obtain
that token from server-side Node, how to cache/refresh it, what must be configured on the
Databricks side, and security rules.

> **Legacy note:** Do NOT use the old Azure Databricks "two-token" flow with
> `X-Databricks-Azure-SP-Management-Token` / `X-Databricks-Azure-Workspace-Resource-Id` headers
> unless you deliberately need first-call auto-provisioning of a workspace admin (see §7.4) — for
> app authentication it is a legacy pattern; provision the service principal in the workspace and
> use a single Bearer token. Also do not use the deprecated `/api/2.0/preview/scim/...` username /
> password basic auth; it does not exist for Azure Databricks.

---

## Table of Contents

1. [Decision guide: which auth method to use](#1-decision-guide-which-auth-method-to-use)
2. [Databricks-native OAuth M2M (`/oidc/v1/token`)](#2-databricks-native-oauth-m2m-oidcv1token)
3. [Microsoft Entra ID client_credentials (`login.microsoftonline.com`)](#3-microsoft-entra-id-client_credentials-loginmicrosoftonlinecom)
4. [Cached `getToken()` helper for Node (both OAuth flavors)](#4-cached-gettoken-helper-for-node-both-oauth-flavors)
5. [Azure Managed Identity from Azure Web Apps](#5-azure-managed-identity-from-azure-web-apps)
6. [Personal Access Tokens (PAT) and the Token API](#6-personal-access-tokens-pat-and-the-token-api)
7. [Provisioning the service principal and granting permissions](#7-provisioning-the-service-principal-and-granting-permissions)
8. [Required environment variables](#8-required-environment-variables)
9. [Security notes](#9-security-notes)
10. [Gotchas](#10-gotchas)

---

## 1. Decision guide: which auth method to use

| Scenario | Use |
|---|---|
| Production app on Azure Web Apps, wants zero stored secrets | **Managed Identity** (§5) — best option on Azure |
| Production app, secret storage acceptable (Key Vault / app settings), Databricks-only automation | **Databricks-native OAuth M2M** (§2) — Databricks' recommended M2M method |
| App must call Databricks **and** other Azure resources (Storage, Key Vault, ARM) with one identity | **Entra ID client_credentials** (§3) with an Entra service principal (one app registration, two token audiences), or Managed Identity |
| Local development / quick prototype only | **PAT** (§6) — never in production |

Key facts that drive the choice:

- **Databricks-native OAuth M2M** uses a *Databricks-managed* service principal (or an Entra SP
  that has been added to the workspace and given a Databricks OAuth secret). The secret is
  generated inside Databricks, tokens come from the workspace's own `/oidc/v1/token` endpoint,
  and the token is only good for Databricks. Access tokens live **1 hour** (`expires_in: 3600`).
- **Entra ID client_credentials** uses a Microsoft Entra app registration
  (client ID + client secret in Entra). Tokens come from `login.microsoftonline.com` with the
  fixed Azure Databricks resource scope `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default`. The same
  app registration can also mint tokens for Storage, Graph, etc. Entra access tokens live
  **60–90 minutes** (variable; read `expires_in`). Microsoft/Databricks docs say: prefer
  Databricks OAuth M2M when you only talk to Databricks; use Entra SP auth when you must
  authenticate to both Databricks and other Azure resources.
- **Managed Identity** is the Entra flow with no secret at all — Azure Web Apps injects a local
  token endpoint (`IDENTITY_ENDPOINT`) into the app's environment. Same
  `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d` resource, same Bearer usage. Nothing to rotate.

In **all** cases the resulting token is sent identically:

```ts
const res = await fetch(`${process.env.DATABRICKS_HOST}/api/2.0/clusters/list`, {
  headers: { Authorization: `Bearer ${await getToken()}` },
});
```

---

## 2. Databricks-native OAuth M2M (`/oidc/v1/token`)

### 2.1 One-time setup (Databricks side)

1. Workspace admin: **Settings → Identity and access → Service principals → Manage → Add
   service principal**. Either create a *Databricks managed* SP or add a *Microsoft Entra ID
   managed* one (paste its application/client ID).
2. Open the SP → **Secrets** tab → **Generate secret**. Choose a lifetime (**max 730 days**).
   Copy the secret immediately — **it is shown only once**. The *client ID* equals the SP's
   application ID. A service principal can have **at most 5 OAuth secrets** concurrently
   (rotate by creating the new one before deleting the old).
3. Grant the SP the workspace entitlements/permissions it needs (§7).

### 2.2 Token endpoint

**`POST https://<workspace-host>/oidc/v1/token`** (workspace-level; there is also an
account-level endpoint `https://accounts.azuredatabricks.net/oidc/accounts/<account-id>/v1/token`
for account APIs — a token from that endpoint works on both account-level and workspace-level
APIs; the workspace-level token works only on that workspace's APIs).

Content type: `application/x-www-form-urlencoded`. Credentials go either in an HTTP Basic
`Authorization` header (`client_id:client_secret`) or as form fields.

Request fields:

| Field | Type | Required | Value |
|---|---|---|---|
| `grant_type` | string | yes | `client_credentials` |
| `scope` | string | yes | `all-apis` (token valid for every REST API the SP is entitled to) |
| `client_id` | string | yes (if not using Basic auth) | SP application ID (a UUID) |
| `client_secret` | string | yes (if not using Basic auth) | Databricks-generated OAuth secret (`dose...`) |
| `assume_group` | string | no | Group ID to assume (Preview; workspace-level endpoint only; SP needs the *Assume* permission on the group; the group's permissions **replace** the SP's own) |

Response (JSON):

| Field | Type | Notes |
|---|---|---|
| `access_token` | string | JWT; put in `Authorization: Bearer ...` |
| `token_type` | string | `Bearer` |
| `expires_in` | number | Seconds; **3600** (1 hour) |

There is no refresh token in the M2M flow — just request a new token when the old one is near
expiry (see §4 for the caching pattern).

Errors / edge cases:

- `400` with `invalid_client` / `invalid_request`: wrong client ID, expired or deleted OAuth
  secret, or you posted JSON instead of form-encoded data.
- `401` on subsequent API calls: token expired (1 h) or secret revoked — re-fetch a token.
- `403` on API calls: token is fine, the SP lacks permission on the object (§7).
- Sending `assume_group` to the **account-level** endpoint fails — workspace endpoint only.
- Use the bare workspace host — no `/api` suffix on `DATABRICKS_HOST`.

### 2.3 TypeScript example (fetch a token + call an API)

```ts
// databricks-oauth.ts  (server-side only)
const host = process.env.DATABRICKS_HOST!;            // https://adb-xxxx.azuredatabricks.net

export async function fetchDatabricksOAuthToken(): Promise<{ accessToken: string; expiresIn: number }> {
  const body = new URLSearchParams({
    grant_type: "client_credentials",
    scope: "all-apis",
  });
  const basic = Buffer.from(
    `${process.env.DATABRICKS_CLIENT_ID}:${process.env.DATABRICKS_CLIENT_SECRET}`
  ).toString("base64");

  const res = await fetch(`${host}/oidc/v1/token`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${basic}`,
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  });
  if (!res.ok) {
    throw new Error(`Databricks token request failed: ${res.status} ${await res.text()}`);
  }
  const json = (await res.json()) as { access_token: string; token_type: string; expires_in: number };
  return { accessToken: json.access_token, expiresIn: json.expires_in };
}
```

---

## 3. Microsoft Entra ID client_credentials (`login.microsoftonline.com`)

Use an Entra **app registration** (a.k.a. Entra-managed service principal): note its
*Directory (tenant) ID*, *Application (client) ID*, and create a *client secret* in
**Certificates & secrets**. The SP must also be added to the Databricks workspace (§7) — an Entra
token for an unknown principal yields `403` (unless you use the legacy two-token bootstrap, §7.4).

### 3.1 Token endpoint (v2.0)

**`POST https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token`**

Content type: `application/x-www-form-urlencoded`.

| Field | Type | Required | Value |
|---|---|---|---|
| `grant_type` | string | yes | `client_credentials` |
| `client_id` | string | yes | Entra application (client) ID |
| `client_secret` | string | yes | Entra client secret value |
| `scope` | string | yes | `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default` |

`2ff814a6-3304-4ab8-85cb-cd0e6f879c1d` is the **fixed, global application ID of the
AzureDatabricks first-party resource** — identical in every Azure tenant; never changes per
workspace. (The legacy v1.0 endpoint `/oauth2/token` uses `resource=2ff814a6-...` instead of
`scope`; prefer v2.0.)

Response: standard Entra shape — `token_type: "Bearer"`, `expires_in` (seconds, typically
**3599** but Entra varies lifetimes 60–90 min; always read the field), `access_token` (JWT with
`aud: 2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`).

Errors / edge cases:

- `AADSTS7000215` invalid client secret — you pasted the secret *ID* instead of the *value*, or it expired (Entra secrets max 24 months).
- `AADSTS700016` app not found in tenant — wrong tenant ID.
- URL-encode the scope if building the body by hand (`%2F.default`); `URLSearchParams` handles it.
- A valid Entra token still gets Databricks `403` if the SP isn't in the workspace or lacks object permissions.
- Databricks accepts the Entra token exactly like a native one: `Authorization: Bearer <access_token>`.

### 3.2 TypeScript example

```ts
export async function fetchEntraToken(): Promise<{ accessToken: string; expiresIn: number }> {
  const body = new URLSearchParams({
    grant_type: "client_credentials",
    client_id: process.env.AZURE_CLIENT_ID!,
    client_secret: process.env.AZURE_CLIENT_SECRET!,
    scope: "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default",
  });

  const res = await fetch(
    `https://login.microsoftonline.com/${process.env.AZURE_TENANT_ID}/oauth2/v2.0/token`,
    { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body }
  );
  if (!res.ok) throw new Error(`Entra token request failed: ${res.status} ${await res.text()}`);
  const json = (await res.json()) as { access_token: string; expires_in: number };
  return { accessToken: json.access_token, expiresIn: json.expires_in };
}
```

---

## 4. Cached `getToken()` helper for Node (both OAuth flavors)

Never fetch a fresh token per request — cache in module scope with an expiry slack (refresh ~5
minutes early) and de-duplicate concurrent refreshes. Module-level state survives across requests
in a warm Next.js server process; it resets on cold start, which is fine.

```ts
// lib/getToken.ts — server-side only. Works for §2, §3 or §5: swap `fetchFn`.
type TokenResult = { accessToken: string; expiresIn: number };

const EXPIRY_SLACK_MS = 5 * 60 * 1000; // refresh 5 min before expiry

let cached: { token: string; expiresAt: number } | null = null;
let inflight: Promise<string> | null = null;

async function refresh(fetchFn: () => Promise<TokenResult>): Promise<string> {
  const { accessToken, expiresIn } = await fetchFn();
  cached = { token: accessToken, expiresAt: Date.now() + expiresIn * 1000 - EXPIRY_SLACK_MS };
  return accessToken;
}

export async function getToken(
  fetchFn: () => Promise<TokenResult> = fetchDatabricksOAuthToken
): Promise<string> {
  if (cached && Date.now() < cached.expiresAt) return cached.token;
  // collapse concurrent callers into one token request
  inflight ??= refresh(fetchFn).finally(() => { inflight = null; });
  return inflight;
}
```

Usage in a Next.js route handler:

```ts
// app/api/warehouses/route.ts
import { getToken } from "@/lib/getToken";

export async function GET() {
  const res = await fetch(`${process.env.DATABRICKS_HOST}/api/2.0/sql/warehouses`, {
    headers: { Authorization: `Bearer ${await getToken()}` },
    cache: "no-store",
  });
  if (res.status === 401) {
    // token was revoked/expired between cache check and call — treat as retryable once
  }
  if (!res.ok) return Response.json({ error: await res.text() }, { status: res.status });
  return Response.json(await res.json());
}
```

Retry guidance: on `401`, invalidate the cache (`cached = null`) and retry once. On `429`, honor
the `Retry-After` header (Databricks rate limits are per-workspace and per-endpoint-group;
exact numbers are not published — implement exponential backoff).

---

## 5. Azure Managed Identity from Azure Web Apps

The best production option on Azure: no client secret anywhere. Azure Web Apps (App Service)
injects two env vars into your process when a managed identity is enabled:
`IDENTITY_ENDPOINT` (a local http URL) and `IDENTITY_HEADER` (a per-boot secret). You exchange
those for an Entra token with audience `2ff814a6-3304-4ab8-85cb-cd0e6f879c1d`.

### 5.1 Azure-side setup

1. Web App → **Identity** → enable **System assigned** (or create/attach a **User assigned**
   managed identity — copy its *Client ID*).
2. No Azure RBAC role on the Databricks workspace resource is needed for plain REST calls — the
   authorization happens inside Databricks (§5.2).

### 5.2 Databricks-side setup (required)

A managed identity is just an Entra service principal. It must be registered in Databricks:

1. Account console (`accounts.azuredatabricks.net`) → **User management → Service principals →
   Add service principal → Microsoft Entra ID managed** → paste the managed identity's
   **Client ID** (application ID) → name → **Add**. (Workspace admins can equivalently add it in
   the workspace: **Settings → Identity and access → Service principals**.)
2. Assign it to the target **workspace** (account console → workspace → Permissions, or the
   workspace assignment API `PUT /api/2.0/accounts/{account_id}/workspaces/{workspace_id}/permissionassignments/principals/{principal_id}`).
3. Grant entitlements and object permissions (§7). Without this you get `403` on every call.

### 5.3 Option A — `@azure/identity` (recommended)

`DefaultAzureCredential` uses the App Service identity endpoint in production and falls back to
`az login` / env-var credentials locally, so the same code runs everywhere.

```bash
npm i @azure/identity
```

```ts
// lib/getTokenMI.ts — server-side only
import { DefaultAzureCredential } from "@azure/identity";

const DATABRICKS_SCOPE = "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default";

// For a user-assigned identity pass its client ID; omit for system-assigned.
const credential = new DefaultAzureCredential({
  managedIdentityClientId: process.env.AZURE_CLIENT_ID, // undefined => system-assigned
});

export async function fetchMIToken(): Promise<{ accessToken: string; expiresIn: number }> {
  const t = await credential.getToken(DATABRICKS_SCOPE); // SDK caches internally too
  return {
    accessToken: t.token,
    expiresIn: Math.max(60, Math.floor((t.expiresOnTimestamp - Date.now()) / 1000)),
  };
}
```

Plug `fetchMIToken` into the `getToken()` helper from §4 (the SDK already caches and
proactively refreshes, so double-caching is harmless).

### 5.4 Option B — raw fetch against `IDENTITY_ENDPOINT` (no dependency)

```ts
export async function fetchMITokenRaw(): Promise<{ accessToken: string; expiresIn: number }> {
  const endpoint = process.env.IDENTITY_ENDPOINT; // set by App Service automatically
  const header = process.env.IDENTITY_HEADER;
  if (!endpoint || !header) throw new Error("Managed identity endpoint not available (not on App Service?)");

  const url = new URL(endpoint);
  url.searchParams.set("resource", "2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"); // no /.default here
  url.searchParams.set("api-version", "2019-08-01");
  if (process.env.AZURE_CLIENT_ID) url.searchParams.set("client_id", process.env.AZURE_CLIENT_ID); // user-assigned

  const res = await fetch(url, { headers: { "X-IDENTITY-HEADER": header } });
  if (!res.ok) throw new Error(`MI token request failed: ${res.status} ${await res.text()}`);
  const json = (await res.json()) as { access_token: string; expires_on: string | number };
  const expiresOnSec = Number(json.expires_on); // epoch seconds
  return { accessToken: json.access_token, expiresIn: Math.max(60, expiresOnSec - Math.floor(Date.now() / 1000)) };
}
```

Notes:

- The App Service endpoint takes a `resource` (bare app ID URI), **not** a `scope` — no `/.default` suffix.
- Managed-identity tokens are cached by the platform and typically valid up to 24 h; still treat
  `expires_on` as authoritative.
- `IDENTITY_ENDPOINT`/`IDENTITY_HEADER` do not exist on your laptop — that's why Option A's
  `DefaultAzureCredential` (which falls back to Azure CLI login or
  `AZURE_TENANT_ID`/`AZURE_CLIENT_ID`/`AZURE_CLIENT_SECRET` env vars) is preferred.
- The Databricks CLI/Terraform equivalents use `ARM_CLIENT_ID` + `ARM_USE_MSI=true`; those env
  vars are only for Databricks tooling, not needed for your own fetch code.

---

## 6. Personal Access Tokens (PAT) and the Token API

PATs are static workspace-scoped bearer strings (`dapi...`). They are a **dev-only shortcut**:
long-lived static secrets, valid for exactly one workspace, no automatic rotation, and cannot
call account-level APIs. Databricks explicitly recommends OAuth instead. Fine for local
prototyping (`DATABRICKS_TOKEN` in `.env.local`); do not ship to production.

### 6.1 Creating a PAT

- **UI:** username menu → **Settings → Developer → Access tokens → Manage → Generate new
  token** → name, lifetime (days), optional scopes → **Generate**. Copy immediately; it is not
  retrievable later.
- **For a service principal:** authenticate the CLI as the SP (via OAuth) and run
  `databricks tokens create --lifetime-seconds 86400`, or call the Token API below with an
  OAuth token.

### 6.2 Token API (workspace-level, current)

**`POST /api/2.0/token/create`** — create a PAT for the calling identity.

| Request field | Type | Required | Notes |
|---|---|---|---|
| `lifetime_seconds` | number | no | Omit ⇒ no expiry (unless workspace enforces a max lifetime — admins commonly do) |
| `comment` | string | no | Display name |
| `scopes` | string[] | no | Scoped PATs, e.g. `["sql", "unity-catalog", "scim", "authentication"]`. Omit ⇒ all-APIs token. A token with `authentication` scope can mint further tokens of any scope — avoid. |
| `autoscope_enabled` | boolean | no | Let Databricks narrow scopes to observed usage after ~30 days |

Response: `token_value` (the secret — shown once) and `token_info`
(`token_id`, `creation_time`, `expiry_time` (epoch ms; `-1` = never), `comment`, `scopes`,
`last_accessed_time`).

**`GET /api/2.0/token/list`** — list the caller's tokens → `{ "token_infos": [ ... ] }` (metadata
only, never secrets; no pagination — bounded by the 600-token cap).

**`POST /api/2.0/token/delete`** — body `{ "token_id": "<id>" }` → revoke.

**`PATCH /api/2.0/token/{token_id}`** — update scopes:
`{ "token": { "scopes": ["sql"] }, "update_mask": "scopes" }`. Scope changes take up to
**10 minutes** to propagate; manually setting scopes permanently disables auto-scoping for that
token.

**`GET /api/2.0/token-scopes`** — list available scope names.

(There is also an admin-only Token Management API under `/api/2.0/token-management/...` to list
and revoke *other users'* tokens — use it for hygiene jobs, not app auth.)

Limits and lifecycle:

- **Max 600 PATs per user per workspace** (`QUOTA_EXCEEDED` beyond that).
- Tokens **unused for 90 days are automatically revoked**.
- Workspace admins can set a maximum lifetime for new tokens; requests exceeding it fail.
- A lost PAT cannot be recovered — create a new one.

### 6.3 TypeScript example (dev-only usage)

```ts
// Dev-only: DATABRICKS_TOKEN is a PAT in .env.local — never committed, never in production.
const res = await fetch(`${process.env.DATABRICKS_HOST}/api/2.0/token/list`, {
  headers: { Authorization: `Bearer ${process.env.DATABRICKS_TOKEN}` },
});
const { token_infos } = (await res.json()) as {
  token_infos: { token_id: string; comment?: string; expiry_time: number }[];
};
```

---

## 7. Provisioning the service principal and granting permissions

An authenticated-but-unauthorized SP is the #1 source of `403`s. Checklist:

### 7.1 Add the SP to the workspace and set entitlements

UI: **Settings → Identity and access → Service principals → Manage → Add service principal**
(choose *Databricks managed* or *Microsoft Entra ID managed* + application ID). Then on the SP's
page enable entitlements as needed:

- **Workspace access** (`workspace-access`) — use the workspace / general APIs.
- **Databricks SQL access** (`databricks-sql-access`) — required to use SQL warehouses via the
  SQL Statement Execution API and Genie.
- **Allow cluster creation** / **Allow pool creation** — only if the app creates compute.

API (SCIM, workspace-level): `POST /api/2.0/preview/scim/v2/ServicePrincipals` with
`{ "applicationId": "<entra-app-id>", "displayName": "my-app", "entitlements": [{"value": "workspace-access"}, {"value": "databricks-sql-access"}] }`.
Account-level SCIM lives at `/api/2.1/accounts/{account_id}/scim/v2/ServicePrincipals`; assign to
a workspace with `PUT .../workspaces/{workspace_id}/permissionassignments/principals/{principal_id}`
body `{ "permissions": ["USER"] }`.

### 7.2 Object permissions (Permissions API)

`GET | PUT | PATCH /api/2.0/permissions/{request_object_type}/{request_object_id}` —
`PUT` replaces the full ACL, `PATCH` adds/updates entries (prefer `PATCH`).

- **SQL warehouse CAN_USE** (needed to run queries / power Genie):

```ts
await fetch(`${host}/api/2.0/permissions/warehouses/${warehouseId}`, {
  method: "PATCH",
  headers: { Authorization: `Bearer ${await getToken()}`, "Content-Type": "application/json" },
  body: JSON.stringify({
    access_control_list: [
      { service_principal_name: process.env.DATABRICKS_CLIENT_ID, permission_level: "CAN_USE" },
    ],
  }),
});
```

  `service_principal_name` is the SP's **application ID (UUID)**, not its display name.
  Warehouse levels: `CAN_VIEW`, `CAN_MONITOR`, `CAN_USE`, `CAN_MANAGE`, `IS_OWNER`.

- **Genie space access:** the SP needs **CAN_RUN** on the Genie space (levels: `CAN_VIEW`,
  `CAN_RUN`, `CAN_EDIT`, `CAN_MANAGE`), granted via the space's **Share** dialog or the
  Permissions API with object type `genie` (path `/api/2.0/permissions/genie/{space_id}`).
  Additionally the SP needs `CAN_USE` on the space's default warehouse and Unity Catalog access
  to the underlying tables. Permission changes can take **5–15 minutes** to propagate to Genie.

- **Catalog grants (Unity Catalog):** minimum for querying:

```sql
GRANT USE CATALOG ON CATALOG my_catalog TO `<application-id>`;
GRANT USE SCHEMA  ON SCHEMA  my_catalog.my_schema TO `<application-id>`;
GRANT SELECT      ON TABLE   my_catalog.my_schema.my_table TO `<application-id>`;
```

  or via REST: `PATCH /api/2.1/unity-catalog/permissions/{securable_type}/{full_name}` with
  `{ "changes": [{ "principal": "<application-id>", "add": ["SELECT"] }] }`
  (securable_type: `catalog`, `schema`, `table`).

### 7.3 Verify identity

`GET /api/2.0/preview/scim/v2/Me` with the SP's token returns the SP record — a fast smoke test
that auth + workspace membership are correct.

### 7.4 Legacy bootstrap (avoid)

If an Entra SP has `Contributor`/`Owner` on the workspace's Azure resource, it can call APIs
without prior provisioning by sending a Databricks-audience token **plus**
`X-Databricks-Azure-SP-Management-Token` (an ARM token for `https://management.core.windows.net/`)
and `X-Databricks-Azure-Workspace-Resource-Id`. First use auto-provisions the SP **as a workspace
admin**. Over-privileged and awkward — provision explicitly instead. One line: exists, don't use.

---

## 8. Required environment variables

App Settings on the Web App (or Key Vault references); `.env.local` for dev. Suggested set:

```bash
# Always
DATABRICKS_HOST=https://adb-1234567890123456.7.azuredatabricks.net   # no trailing slash, no /api

# §2 Databricks-native OAuth M2M
DATABRICKS_CLIENT_ID=<sp-application-id>
DATABRICKS_CLIENT_SECRET=<databricks-oauth-secret>          # 'dose...' — Key Vault reference in prod

# §3 Entra client_credentials
AZURE_TENANT_ID=<tenant-id>
AZURE_CLIENT_ID=<entra-app-client-id>
AZURE_CLIENT_SECRET=<entra-client-secret>                   # Key Vault reference in prod

# §5 Managed identity — nothing secret needed.
# IDENTITY_ENDPOINT / IDENTITY_HEADER are injected by App Service automatically.
AZURE_CLIENT_ID=<user-assigned-mi-client-id>                # only for user-assigned MI

# §6 Dev only
DATABRICKS_TOKEN=<pat>                                      # never in production

# App resources
DATABRICKS_WAREHOUSE_ID=<sql-warehouse-id>
DATABRICKS_GENIE_SPACE_ID=<genie-space-id>
```

Don't set `DATABRICKS_TOKEN` *and* client-credential vars simultaneously if you ever use
Databricks tooling — unified auth treats it as a configuration conflict.

---

## 9. Security notes

- **Never expose any token to the browser.** No Databricks token — PAT, OAuth, Entra, or MI —
  may appear in client components, `NEXT_PUBLIC_*` vars, cookies readable by JS, or API
  responses. All Databricks calls go through Next.js route handlers / server actions; the
  browser only ever talks to *your* API.
- Databricks tokens grant everything the SP can do (`scope=all-apis`); treat them like passwords
  even though they expire in an hour.
- Store secrets in **Azure Key Vault** with App Service Key Vault references; prefer Managed
  Identity to eliminate secrets entirely.
- Principle of least privilege: dedicated SP per app; only the entitlements and object grants
  the app needs; no workspace admin.
- Log token *acquisition events*, never token values. Strip `Authorization` headers from any
  request logging.
- Rotate: Databricks OAuth secrets ≤ 730 days (5 allowed → zero-downtime rotation), Entra
  secrets ≤ 24 months. Put rotation dates in your ops calendar.

---

## 10. Gotchas

1. **`403` with a valid token** — SP authenticated but not provisioned in the workspace, missing
   an entitlement (`databricks-sql-access`), or missing object permission (warehouse `CAN_USE`,
   Genie `CAN_RUN`, UC `SELECT`). Work through §7 in order.
2. **`scope=all-apis` vs Entra `/.default`** — the Databricks-native endpoint wants
   `scope=all-apis`; the Entra endpoint wants `scope=2ff814a6-3304-4ab8-85cb-cd0e6f879c1d/.default`;
   the App Service MI endpoint wants `resource=2ff814a6-3304-4ab8-85cb-cd0e6f879c1d` (no
   `/.default`). Mixing these up is the most common 400.
3. **Form-encoded, not JSON** — both OAuth token endpoints require
   `application/x-www-form-urlencoded`. Posting JSON returns `invalid_request`.
4. **Databricks OAuth secret shown once**, max 5 per SP, max 730-day lifetime. Entra secret:
   copy the *value* column, not the secret ID.
5. **Token lifetimes**: Databricks OAuth = 3600 s fixed; Entra = 60–90 min variable; MI tokens
   can be much longer. Always drive cache expiry from `expires_in` / `expires_on`, never a
   hard-coded constant; keep ≥5 min slack (§4).
6. **Serverless/multi-instance caching** — the §4 module cache is per-process. On a scaled-out
   Web App each instance fetches its own token; that's fine (token endpoints tolerate this), but
   don't put tokens in a shared cache like Redis unless encrypted — and it's rarely worth it.
7. **PAT auto-revocation** — dev PATs die after 90 days of inactivity and count toward a
   600-token cap; workspace admins may cap lifetimes. Mysterious dev 401s are usually this.
8. **Account vs workspace endpoints** — `accounts.azuredatabricks.net` OIDC tokens work
   everywhere; workspace `/oidc/v1/token` tokens work only on that workspace. PATs can never
   call account-level APIs (use Entra tokens or account-level OAuth there).
9. **`DATABRICKS_HOST` hygiene** — https, no trailing slash, no `/api` suffix; it's the
   *workspace* URL, not `portal.azure.com` or the ARM resource ID.
10. **Rate limiting** — Databricks enforces per-workspace, per-endpoint-group rate limits
    (numbers not published). Handle `429` + `Retry-After` with backoff; a shared token cache
    (§4) also keeps you off the token endpoint.
11. **Genie propagation lag** — permission grants for Genie spaces can take 5–15 minutes to take
    effect; don't debug-loop faster than that.
12. **MI locally** — `IDENTITY_ENDPOINT` doesn't exist outside Azure; use
    `DefaultAzureCredential` so local dev falls back to `az login` or env-var credentials.
