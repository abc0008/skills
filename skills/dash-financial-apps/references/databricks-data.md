# Connecting a Dash App to Databricks (open-source)

Patterns for sourcing data from Databricks in an open-source Dash app: the SQL Warehouse
connector for queries, the Databricks SDK for triggering Jobs, plus the performance and
state-management rules that keep an interactive app correct. None of this requires Dash
Enterprise.

## Table of contents
1. Credentials & environment variables (never hard-code)
2. SQL Warehouse connector — the core pattern
3. Querying inside callbacks (and why, not globals)
4. SQLAlchemy variant
5. Pushing compute down + caching
6. Triggering Databricks Jobs from a callback
7. Deployment notes (gunicorn / Databricks Apps)

---

## 1. Credentials & environment variables

Authenticate with environment variables or Databricks secrets — **never** commit a token.
The SQL connector uses three values:

```
SERVER_HOSTNAME   e.g. dbc-xxxx.cloud.databricks.com   (no https://)
HTTP_PATH         e.g. /sql/1.0/warehouses/abc123
ACCESS_TOKEN      a Databricks personal access token (dapi...)
```

Find these in Databricks under your SQL Warehouse's **Connection details** tab. Read them
in Python with `os.getenv` and fail loudly if missing:

```python
import os
SERVER_HOSTNAME = os.getenv("SERVER_HOSTNAME")
HTTP_PATH = os.getenv("HTTP_PATH")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
assert all([SERVER_HOSTNAME, HTTP_PATH, ACCESS_TOKEN]), "Set Databricks env vars"
```

Locally, pass them on the launch line or use a `.env` (git-ignored). On a server, set them
as the platform's environment variables / secrets.

---

## 2. SQL Warehouse connector — the core pattern

`pip install databricks-sql-connector`. Open a connection, run a query, pull results into
pandas. Use `fetchall_arrow().to_pandas()` — Arrow transfer is much faster than row-by-row
for analytical result sets.

```python
from databricks import sql
import pandas as pd

def query_df(query: str, params: tuple | None = None) -> pd.DataFrame:
    with sql.connect(server_hostname=SERVER_HOSTNAME,
                     http_path=HTTP_PATH,
                     access_token=ACCESS_TOKEN) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall_arrow().to_pandas()
```

The context managers (`with`) guarantee the connection and cursor close even on error —
important in a long-running web server where leaked connections accumulate.

**Parameterize** queries instead of f-string-ing user input into SQL, to avoid injection
and quoting bugs:

```python
df = query_df(
    "SELECT month, revenue FROM finance.fct_pl WHERE entity = ? AND year = ?",
    ("Commercial Bank", 2025),
)
```

---

## 3. Query inside callbacks — not module globals

It's tempting to load a DataFrame once at the top of the module and let callbacks filter
it. For **static reference data** (a small, read-only dimension that never changes during
the app's life), that's fine. For **anything that varies by user input or should reflect
fresh data**, query inside the callback instead.

Why: a Dash server process is shared across all users and requests. A module-level
DataFrame that callbacks re-filter or mutate creates cross-request bugs — one user's filter
can bleed into another's view, and "current" data goes stale. Per-interaction data belongs
in the callback (or in a per-session `dcc.Store`).

```python
@callback(Output("chart", "figure"),
          Input("entity", "value"), Input("year", "value"))
def update(entity, year):
    df = query_df(
        "SELECT month, revenue FROM finance.fct_pl WHERE entity = ? AND year = ?",
        (entity, year))
    fig = px.bar(df, x="month", y="revenue")
    return apply_finance_theme(fig, yformat="$,.0f")
```

If a query is expensive and shared across users (e.g. a daily-refreshed summary), cache it
rather than globaling it — see §5.

---

## 4. SQLAlchemy variant

If the codebase standardizes on SQLAlchemy, register the Databricks dialect (`pip install
databricks-sql-connector` ships the dialect as `databricks+connector`; older guides used
`sqlalchemy-databricks`). Build an engine and use `pd.read_sql`:

```python
from sqlalchemy import create_engine
import pandas as pd

engine = create_engine(
    f"databricks://token:{ACCESS_TOKEN}@{SERVER_HOSTNAME}?http_path={HTTP_PATH}"
)
df = pd.read_sql("SELECT * FROM finance.dim_account", engine)
```

The raw connector (§2) is simpler and has fewer moving parts; reach for SQLAlchemy only if
the rest of the app already uses it.

---

## 5. Push compute down + caching

- **Aggregate and filter in SQL**, not in the browser. Send `GROUP BY` results and small
  filtered frames, not whole fact tables. The connector docs are explicit: filter/aggregate
  before bringing data into the app.
- **Limit detail rows.** AG Grid Community renders client-side; keep result sets to
  thousands, not millions (see `financial-tables.md` §7).
- **Cache expensive shared queries** with `flask_caching` so every callback firing doesn't
  re-hit the warehouse:

```python
from flask_caching import Cache
cache = Cache(app.server, config={"CACHE_TYPE": "SimpleCache",
                                  "CACHE_DEFAULT_TIMEOUT": 300})

@cache.memoize()
def monthly_pl(entity, year):
    return query_df("SELECT month, revenue, expense FROM finance.fct_pl "
                    "WHERE entity = ? AND year = ?", (entity, year))
```

- **Warehouse startup**: a cold SQL Warehouse adds latency on first query. Serverless or a
  short auto-stop reduces the cold-start penalty for interactive apps.

---

## 6. Triggering Databricks Jobs from a callback

For heavy computation (forecasts, model scoring, large transforms) that shouldn't run in a
web request, hand the work to a Databricks Job via the SDK (`pip install databricks-sdk`)
and read its output. Authenticate with `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, and a target
cluster (`DATABRICKS_CLUSTER_ID`).

The pattern: a notebook defines input widgets (`dbutils.widgets.text(...)`) and writes its
result somewhere readable (e.g. a Plotly figure as JSON to DBFS). The Dash callback passes
parameters matching those widget names, runs the job, and loads the output.

```python
from databricks.sdk import WorkspaceClient
from databricks.sdk.service import jobs
import os, json, base64, plotly.graph_objects as go

@callback(Output("forecast", "children"),
          State("state", "value"), State("days", "value"),
          Input("run", "n_clicks"), prevent_initial_call=True)
def run_job(state, days, _):
    w = WorkspaceClient(host=os.environ["DATABRICKS_HOST"],
                        token=os.environ["DATABRICKS_TOKEN"])
    params = {"us-state": state, "forecast-forward-days": days}  # match widget names
    nb = f"/Users/{w.current_user.me().user_name}/my_notebook"
    w.clusters.ensure_cluster_is_running(os.environ["DATABRICKS_CLUSTER_ID"])
    job = w.jobs.create(name=f"dash-{__import__('time').time_ns()}",
        tasks=[jobs.Task(task_key="t",
            existing_cluster_id=os.environ["DATABRICKS_CLUSTER_ID"],
            notebook_task=jobs.NotebookTask(notebook_path=nb, base_parameters=params))])
    w.jobs.run_now(job_id=job.job_id).result()           # blocks until done
    raw = w.dbfs.read("/tmp/forecast_plot.json").data
    w.jobs.delete(job_id=job.job_id)
    fig = go.Figure(json.loads(base64.b64decode(raw).decode()))
    return dcc.Graph(figure=apply_finance_theme(fig))
```

Notes: wrap the long-running call in `dcc.Loading` so the user sees a spinner; use
`prevent_initial_call=True` so it only runs on the button click; pass the cluster spin-up
in a `try/except` to surface clear config errors. For genuinely long jobs, consider polling
the run status instead of blocking the callback.

---

## 7. Deployment notes

- Expose the WSGI server: `server = app.server`, run under **gunicorn** (e.g. `gunicorn
  app:server --workers 4`). This is the open-source path — the Plotly Cloud / Dash
  Enterprise publish commands do not apply.
- **Databricks Apps** can host an open-source Dash app; provide the entrypoint and a
  `requirements.txt`, and set the Databricks connection values as the app's environment
  variables / secrets rather than baking them into code.
- Keep `requirements.txt` to open-source packages: `dash`, `dash-ag-grid`, `plotly`,
  `pandas`, `databricks-sql-connector`, `databricks-sdk`, `gunicorn`, and any of
  `dash-bootstrap-components` / `dash-mantine-components` / `flask-caching` you used.
