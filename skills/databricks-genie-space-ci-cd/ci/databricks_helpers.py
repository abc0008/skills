"""
databricks_helpers.py — the ONLY module that touches Databricks or the filesystem
layout. Every script imports from here. Verified against the Databricks SDK for
Python `w.genie` reference and the Statement Execution API (June 2026).

================================================================================
AI AGENT ORIENTATION
================================================================================
Verified SDK surface (databricks.sdk.service.dashboards.GenieAPI), reached via
`WorkspaceClient().genie`:
  - get_space(space_id, include_serialized_space=True)  -> GenieSpace
        NOTE: serialized_space is OMITTED unless include_serialized_space=True,
        and that flag requires CAN EDIT on the space. We always pass it.
  - create_space(warehouse_id, serialized_space, *, description, parent_path,
        title) -> GenieSpace
  - update_space(space_id, *, serialized_space, warehouse_id, etag, title,
        description, parent_path) -> GenieSpace
        NOTE: etag gives optimistic concurrency — if the live space changed
        since we read it, the update FAILS instead of clobbering. We use it.
  - start_conversation_and_wait(space_id, content) -> GenieMessage
  - get_message_attachment_query_result(space_id, conversation_id, message_id,
        attachment_id) -> GenieGetMessageQueryResultResponse
  - genie_create_eval_run / genie_get_eval_run / genie_list_eval_results
        -> NATIVE benchmark evaluation (see run_benchmarks.py --native).

Statement Execution (WorkspaceClient().statement_execution):
  - execute_statement(warehouse_id, statement, wait_timeout="50s",
        disposition=INLINE, format=JSON_ARRAY) -> StatementResponse
        result rows live at .result.data_array; status at .status.state
        ("SUCCEEDED" | "FAILED" | ...). INLINE caps ~16-25 MiB — fine for
        DESCRIBE; for big result sets you'd switch to EXTERNAL_LINKS.

If a method is missing on the installed SDK (older version), we fall back to a
typed REST call. All network calls are wrapped so transient failures (429/5xx)
become TransientError and are retried; hard failures become PermanentError.
================================================================================
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml

from _core import (ConfigError, PermanentError, TransientError,
                   classify_http_error, get_logger, retry)

log = get_logger("drift.helpers")

# ------------------------------------------------------------------------------
# Filesystem layout (relative to repo root, one level above ci/).
# >>> ADAPT: change if the repo puts models/views/spaces elsewhere.
# ------------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = REPO_ROOT / "models"
METRIC_VIEWS_DIR = REPO_ROOT / "metric_views"
GENIE_SPACES_DIR = REPO_ROOT / "genie_spaces"
BENCHMARKS_DIR = REPO_ROOT / "benchmarks"
CONFIG_PATH = REPO_ROOT / "config.yaml"

VIEW_SUFFIX = ".metricview.yaml"
SPACE_SUFFIX = ".genie.json"
BENCH_SUFFIX = ".bench.yaml"


# ==============================================================================
# CONFIG — load + VALIDATE. A bad config should fail loudly and early with a
# precise message, never with a confusing AttributeError 20 lines later.
# ==============================================================================
_REQUIRED_WORKSPACE_KEYS = ("host", "warehouse_id", "catalog", "schema")


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Read and validate config.yaml. Raises ConfigError (exit 2) with an
    actionable message on any structural problem."""
    cfg_path = path or CONFIG_PATH
    if not cfg_path.exists():
        raise ConfigError(
            f"{cfg_path} not found. Copy config.example.yaml to config.yaml and "
            f"fill in the '# >>> ADAPT' values.")
    try:
        cfg = yaml.safe_load(cfg_path.read_text()) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"{cfg_path} is not valid YAML: {e}") from e
    validate_config(cfg)
    return cfg


def validate_config(cfg: dict[str, Any]) -> None:
    """Structural validation, separated so tests can call it on dicts directly.
    Checks required keys, type sanity, and referential integrity (every space's
    depends_on_metric_views names a real metric_views entry)."""
    if not isinstance(cfg, dict):
        raise ConfigError("config root must be a mapping/object.")

    ws = cfg.get("workspace")
    if not isinstance(ws, dict):
        raise ConfigError("config.workspace section is missing or not a mapping.")
    missing = [k for k in _REQUIRED_WORKSPACE_KEYS if not ws.get(k)]
    if missing:
        raise ConfigError(f"config.workspace missing required keys: {missing}")
    if "REPLACE" in str(ws.get("warehouse_id", "")) or "your-workspace" in str(ws.get("host", "")):
        raise ConfigError("config.workspace still contains placeholder values "
                          "(warehouse_id/host). Fill in the '# >>> ADAPT' fields.")

    mvs = cfg.get("metric_views") or {}
    spaces = cfg.get("genie_spaces") or {}
    if not isinstance(mvs, dict) or not isinstance(spaces, dict):
        raise ConfigError("metric_views and genie_spaces must be mappings.")

    # Referential integrity: a space cannot depend on a metric view that the
    # config doesn't define — that's almost always a typo and would silently
    # make the L1 gate under-enforce.
    known_views = set(mvs.keys())
    for sname, spec in spaces.items():
        spec = spec or {}
        for v in (spec.get("depends_on_metric_views") or []):
            if v not in known_views:
                raise ConfigError(
                    f"genie_spaces.{sname}.depends_on_metric_views references "
                    f"'{v}', which is not defined under metric_views. Fix the "
                    f"name or add the metric view.")
        # space_id_by_env should be a mapping if present.
        sib = spec.get("space_id_by_env")
        if sib is not None and not isinstance(sib, dict):
            raise ConfigError(f"genie_spaces.{sname}.space_id_by_env must be a "
                              f"mapping of env -> id.")


def get_space_id(cfg: dict, space_name: str, env: str) -> str:
    """Resolve a space_id for (name, env) or raise ConfigError. Centralized so
    every script reports the same precise error."""
    spec = (cfg.get("genie_spaces") or {}).get(space_name)
    if spec is None:
        raise ConfigError(f"genie_spaces.{space_name} not found in config.")
    sid = (spec.get("space_id_by_env") or {}).get(env)
    if not sid:
        raise ConfigError(
            f"genie_spaces.{space_name}.space_id_by_env.{env} is not set. Add the "
            f"space_id for env '{env}'.")
    return sid


def logical_name(path: str | Path) -> str:
    """'metric_views/nim.metricview.yaml' -> 'nim'."""
    name = Path(path).name
    for suffix in (VIEW_SUFFIX, SPACE_SUFFIX, BENCH_SUFFIX):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return Path(path).stem


# ==============================================================================
# DATABRICKS CLIENT ADAPTER
# Thin wrapper so (a) the rest of the code never imports the SDK directly,
# (b) tests can inject a fake, (c) we centralize the SDK-vs-REST fallback and
# the transient/permanent error classification + retry.
# ==============================================================================
class DatabricksAdapter:
    """Wraps the Databricks SDK WorkspaceClient with retries and a REST
    fallback. All Genie/SQL access goes through here.

    Inject a fake in tests: DatabricksAdapter(client=FakeClient()).
    """

    def __init__(self, host: str | None = None, client: Any = None):
        self._host = host
        self._client = client  # if provided (tests), skip real auth

    # ---- auth ----------------------------------------------------------------
    @property
    def client(self):
        if self._client is None:
            self._client = self._make_client()
        return self._client

    def _make_client(self):
        try:
            from databricks.sdk import WorkspaceClient
        except ImportError as e:
            raise ConfigError("databricks-sdk not installed. "
                              "pip install databricks-sdk") from e
        if self._host:
            os.environ.setdefault("DATABRICKS_HOST", self._host)
        # The SDK raises if it can't authenticate; surface as ConfigError.
        try:
            return WorkspaceClient()
        except Exception as e:
            raise ConfigError(
                f"Could not authenticate to Databricks. Ensure DATABRICKS_HOST "
                f"and DATABRICKS_TOKEN (service principal) are set. Underlying: {e}"
            ) from e

    # ---- low-level REST fallback --------------------------------------------
    def _rest(self, method: str, path: str, body: dict | None = None) -> dict:
        import requests
        host = os.environ.get("DATABRICKS_HOST", self._host or "").rstrip("/")
        token = os.environ.get("DATABRICKS_TOKEN")
        if not host or not token:
            raise ConfigError("REST fallback needs DATABRICKS_HOST and "
                              "DATABRICKS_TOKEN env vars.")
        try:
            resp = requests.request(
                method, f"{host}{path}",
                headers={"Authorization": f"Bearer {token}",
                         "Content-Type": "application/json"},
                data=json.dumps(body) if body is not None else None,
                timeout=60)
        except requests.RequestException as e:
            raise TransientError(f"network error calling {path}: {e}") from e
        if resp.status_code >= 400:
            raise classify_http_error(resp.status_code, resp.text[:300])
        return resp.json() if resp.text else {}

    @staticmethod
    def _wrap_sdk_call(fn, *args, **kwargs):
        """Call an SDK method, translating its errors into our typed ones so
        retry/exit-code logic works. SDK raises databricks.sdk.errors.* ; we
        classify by HTTP-ish attributes when present."""
        try:
            return fn(*args, **kwargs)
        except Exception as e:  # noqa: BLE001 — we re-raise as typed
            status = getattr(e, "status_code", None) or getattr(e, "error_code", None)
            msg = str(e)
            if isinstance(status, int):
                raise classify_http_error(status, msg) from e
            # Heuristic on common SDK error class names / messages.
            lowered = msg.lower()
            if any(s in lowered for s in ("rate limit", "429", "timeout",
                                          "temporarily", "503", "502", "504")):
                raise TransientError(msg) from e
            if any(s in lowered for s in ("not found", "permission", "denied",
                                          "403", "404", "invalid", "etag")):
                raise PermanentError(msg) from e
            # Unknown -> treat as transient once; retry budget bounds the risk.
            raise TransientError(msg) from e

    # ---- Genie: export a space ----------------------------------------------
    @retry()
    def export_space(self, space_id: str) -> tuple[dict[str, Any], str | None]:
        """Return (parsed_serialized_space, etag). etag is used later for a safe
        update. Uses include_serialized_space=True (requires CAN EDIT)."""
        genie = getattr(self.client, "genie", None)
        if genie is not None and hasattr(genie, "get_space"):
            obj = self._wrap_sdk_call(
                genie.get_space, space_id, include_serialized_space=True)
            d = obj.as_dict() if hasattr(obj, "as_dict") else dict(obj)
        else:
            d = self._rest(
                "GET", f"/api/2.0/genie/spaces/{space_id}?include_serialized_space=true")
        ser = d.get("serialized_space")
        if ser is None:
            raise PermanentError(
                f"space {space_id} returned no serialized_space. Confirm the SP "
                f"has CAN EDIT on the space (required for the export flag).")
        parsed = json.loads(ser) if isinstance(ser, str) else ser
        etag = d.get("etag")
        return parsed, etag

    # ---- Genie: create / update (idempotent upsert is in deploy_spaces) -----
    @retry()
    def create_space(self, warehouse_id: str, serialized_space: str,
                     title: str | None = None, parent_path: str | None = None) -> dict:
        genie = self.client.genie
        obj = self._wrap_sdk_call(
            genie.create_space, warehouse_id=warehouse_id,
            serialized_space=serialized_space, title=title, parent_path=parent_path)
        return obj.as_dict() if hasattr(obj, "as_dict") else dict(obj)

    @retry()
    def update_space(self, space_id: str, serialized_space: str,
                     warehouse_id: str, etag: str | None = None) -> dict:
        """Update with optimistic concurrency. If etag is provided and the live
        space changed since we read it, the SDK raises -> we surface as
        PermanentError so the caller re-reads instead of clobbering."""
        genie = self.client.genie
        kwargs = dict(serialized_space=serialized_space, warehouse_id=warehouse_id)
        if etag:
            kwargs["etag"] = etag
        obj = self._wrap_sdk_call(genie.update_space, space_id, **kwargs)
        return obj.as_dict() if hasattr(obj, "as_dict") else dict(obj)

    # ---- SQL: run a statement, return rows ----------------------------------
    @retry()
    def run_sql(self, warehouse_id: str, statement: str) -> list[list]:
        """Execute SQL (INLINE/JSON_ARRAY) and return data_array rows. Raises
        PermanentError if the statement itself FAILED (a bad query won't get
        better on retry)."""
        se = self.client.statement_execution
        res = self._wrap_sdk_call(
            se.execute_statement, warehouse_id=warehouse_id,
            statement=statement, wait_timeout="50s")
        state = _deep_get(res, "status", "state")
        state = getattr(state, "value", state)  # enum -> str
        if state and str(state).upper() not in ("SUCCEEDED", "FINISHED"):
            err = _deep_get(res, "status", "error")
            raise PermanentError(f"SQL did not succeed (state={state}): {err}")
        rows = _deep_get(res, "result", "data_array")
        return rows or []

    # ---- Genie conversation: ask one question -------------------------------
    @retry()
    def ask(self, space_id: str, question: str) -> tuple[str | None, list[list]]:
        """Ask a question via the conversation API; return (generated_sql, rows).
        rows == [] and sql is None if Genie produced no query attachment."""
        genie = self.client.genie
        msg = self._wrap_sdk_call(
            genie.start_conversation_and_wait, space_id=space_id, content=question)
        attachments = getattr(msg, "attachments", None) or []
        query_att = next((a for a in attachments if getattr(a, "query", None)), None)
        if query_att is None:
            return None, []
        # Extract generated SQL defensively across SDK shapes.
        q = getattr(query_att, "query", None)
        gen_sql = getattr(q, "query", None) if q is not None and hasattr(q, "query") else q
        message_id = getattr(msg, "id", None) or getattr(msg, "message_id", None)
        attachment_id = getattr(query_att, "attachment_id", None) or getattr(query_att, "id", None)
        rows: list[list] = []
        if message_id and attachment_id:
            res = self._wrap_sdk_call(
                genie.get_message_attachment_query_result,
                space_id=space_id, conversation_id=msg.conversation_id,
                message_id=message_id, attachment_id=attachment_id)
            rows = _result_rows(res)
        return (str(gen_sql) if gen_sql else None), rows


def _deep_get(obj: Any, *names: str) -> Any:
    """Walk attributes OR dict keys (SDK objects vs dicts) safely."""
    cur = obj
    for n in names:
        if cur is None:
            return None
        cur = getattr(cur, n, None) if not isinstance(cur, dict) else cur.get(n)
    return cur


def _result_rows(res: Any) -> list[list]:
    """Extract data_array from a GenieGetMessageQueryResultResponse across the
    few shapes the SDK has used (statement_response.result.data_array or
    result.data_array)."""
    for path in (("statement_response", "result", "data_array"),
                 ("result", "data_array")):
        rows = _deep_get(res, *path)
        if rows is not None:
            return rows
    return []


# ==============================================================================
# METRIC VIEW export (uses the adapter)
# ==============================================================================
def export_metric_view(adapter: DatabricksAdapter, name: str, cfg: dict) -> dict:
    """Return a metric view's canonical definition via DESCRIBE ... AS JSON.
    Uses parameter-free fully-qualified name (identifiers can't be bound as
    SQL params, so we validate the name to avoid injection)."""
    ws = cfg["workspace"]
    _assert_safe_identifier(name)
    _assert_safe_identifier(ws["catalog"])
    _assert_safe_identifier(ws["schema"])
    fq = f'{ws["catalog"]}.{ws["schema"]}.{name}'
    rows = adapter.run_sql(ws["warehouse_id"], f"DESCRIBE TABLE EXTENDED {fq} AS JSON")
    if not rows or not rows[0]:
        raise PermanentError(f"DESCRIBE for {fq} returned no rows. Does the "
                             f"metric view exist and is it readable?")
    cell = rows[0][0]
    return json.loads(cell) if isinstance(cell, str) else cell


_IDENT = __import__("re").compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _assert_safe_identifier(s: str) -> None:
    """Guard against SQL injection in the DESCRIBE statement, since identifiers
    can't be parameterized. Catalog/schema/view names must be simple identifiers.
    >>> ADAPT: if you legitimately use names needing backtick-quoting, extend
    this to validate-then-quote rather than reject."""
    if not isinstance(s, str) or not _IDENT.match(s):
        raise ConfigError(f"unsafe / invalid identifier: {s!r}. Catalog, schema, "
                          f"and metric-view names must match {_IDENT.pattern}.")


# ==============================================================================
# NORMALIZE — strip env-specific noise so diffs mean something
# ==============================================================================
def _strip(obj: Any, fields: set[str]) -> Any:
    if isinstance(obj, dict):
        return {k: _strip(v, fields) for k, v in obj.items() if k not in fields}
    if isinstance(obj, list):
        return [_strip(v, fields) for v in obj]
    return obj


def normalize_space(space: dict, cfg: dict) -> dict:
    fields = set((cfg.get("normalize") or {}).get("strip_space_fields", []))
    return _strip(space, fields)


def normalize_metric_view(view: dict, cfg: dict) -> dict:
    fields = set((cfg.get("normalize") or {}).get("strip_view_fields", []))
    return _strip(view, fields)


def canonical_json(obj: Any) -> str:
    """Deterministic string form for diffing. Sorted keys so key reordering is
    never seen as drift."""
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False)


# ==============================================================================
# GIT — what changed in this PR (used by L1)
# ==============================================================================
def changed_files(base_ref: str = "origin/main") -> list[str]:
    """Repo-relative paths changed vs base_ref. Tries the triple-dot
    (merge-base) form first, then a plain diff. Raises ConfigError if git isn't
    available or the ref can't be resolved (so CI fails clearly, not silently)."""
    for spec in (f"{base_ref}...HEAD", base_ref):
        try:
            out = subprocess.run(
                ["git", "diff", "--name-only", spec],
                cwd=REPO_ROOT, text=True, capture_output=True, check=True)
            return [l.strip() for l in out.stdout.splitlines() if l.strip()]
        except FileNotFoundError as e:
            raise ConfigError("git not found on PATH; the L1 gate needs git.") from e
        except subprocess.CalledProcessError:
            continue
    raise ConfigError(
        f"could not diff against '{base_ref}'. In CI, ensure the pipeline does a "
        f"full fetch (fetchDepth: 0) and the target branch ref exists locally.")
