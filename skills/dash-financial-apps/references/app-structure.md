# Dash App Structure (open-source)

Layout, callbacks, multi-page, and styling for open-source financial Dash apps. This is the
scaffolding around the charts (`financial-charts.md`), banking recipes (`banking-charts.md`),
and tables (`financial-tables.md`). For the **Pinnacle zone layout, KPI card spec, action
titles, and the four report types**, follow `layout-standards.md` — use the `pinnacle_layout.py`
helpers (`five_zone_page`, `kpi_card`, `header_bar`, `page_title`, `chart_title`) for page
structure rather than hand-rolling divs. Pinnacle font is **Arial** throughout.

## Table of contents
1. App skeleton & modern idioms
2. Layout: html + dcc building blocks
3. Callbacks (and patterns finance dashboards need)
4. Styling without Enterprise (CSS, Bootstrap, Mantine)
5. Multi-page apps (Dash Pages)
6. Loading states, errors, and empty data
7. Project layout & deployment

---

## 1. App skeleton & modern idioms

```python
from dash import Dash, html, dcc, callback, Input, Output, State

app = Dash(__name__)
server = app.server          # WSGI entrypoint (gunicorn / Databricks Apps)

app.layout = [               # a list is valid in Dash 2.17+
    html.H3("Title"),
    # components...
]

if __name__ == "__main__":
    app.run(debug=True)      # NOT app.run_server() — removed in Dash 3.0
```

Idioms that distinguish current Dash from older generated code:
- `from dash import callback` and decorate with `@callback` (not `@app.callback`).
- `app.run(debug=True)`; `run_server` is gone in 3.x.
- Prefer `dash_ag_grid` over `dash_table` for tables.
- `Dash(__name__)` so `assets/` (CSS, favicon) is discovered automatically.

---

## 2. Layout: html + dcc building blocks

- **`dash.html`** mirrors HTML tags: `html.Div`, `html.H1`–`H6`, `html.Span`, `html.Table`,
  `html.Button`, etc. Attributes differ from raw HTML: `className` (not `class`), `style` is
  a **dict** with camelCased keys (`textAlign`, `backgroundColor`), and `children` is the
  first positional arg.
- **`dash.dcc`** holds interactive components: `dcc.Graph`, `dcc.Dropdown`, `dcc.DatePickerRange`,
  `dcc.RadioItems`, `dcc.Checklist`, `dcc.Slider`/`RangeSlider`, `dcc.Input`, `dcc.Tabs`,
  `dcc.Store` (client-side state), `dcc.Loading` (spinner wrapper), `dcc.Download`.

A typical finance dashboard header: KPI tiles in a flex row, a filter bar of dropdowns/date
pickers, then a content grid of charts and tables.

```python
app.layout = html.Div([
    html.Div([kpi_tile("NII", 46.7e6, 42.0e6), kpi_tile("Fees", 12.1e6, 11.4e6)],
             style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),
    html.Div([
        dcc.Dropdown(entities, entities[0], id="entity", style={"width": 260}),
        dcc.DatePickerRange(id="dates"),
    ], style={"display": "flex", "gap": "12px", "marginBottom": "16px"}),
    dcc.Loading(dcc.Graph(id="trend")),
    dag.AgGrid(id="detail", ...),
], style={"maxWidth": 1200, "margin": "0 auto", "padding": "24px"})
```

---

## 3. Callbacks

A callback wires component properties together: when an `Input` property changes, the
function runs and its return value sets the `Output` property.

```python
@callback(
    Output("trend", "figure"),
    Output("detail", "rowData"),
    Input("entity", "value"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
)
def refresh(entity, start, end):
    df = query_df(...)                       # see databricks-data.md
    return apply_finance_theme(px.line(df, x="month", y="value")), df.to_dict("records")
```

Patterns finance dashboards lean on:
- **`State`** for "don't fire until the button" inputs — pair with a `html.Button` `Input`
  and `prevent_initial_call=True` (e.g. running a heavy query/job on demand).
- **Multiple outputs** from one callback (return a tuple) to update a chart + table + KPI
  together from the same filter change.
- **`dcc.Store`** to compute a filtered dataset once and fan it out to several charts
  without re-querying: one callback writes the Store, others read it as `Input`.
- **`callback_context`** (or `dash.ctx`) to tell which input fired when several share a
  callback.
- **`no_update`** (`from dash import no_update`) to skip updating a particular output.

Avoid: a global mutable DataFrame shared across callbacks (cross-user bleakage — see
databricks-data.md §3); chaining many tiny callbacks where one multi-output callback is
clearer.

---

## 4. Styling without Enterprise

Dash Design Kit is Enterprise — do not use it. Open-source options, in rough order of
effort:

- **Inline `style` dicts** — fine for one-offs and KPI tiles. Quick, no dependencies.
- **`assets/` CSS file** — create `assets/style.css`; Dash auto-loads it. Reference with
  `className`. Best for app-wide rules (fonts, card styles, table headers).
- **Dash Bootstrap Components** (`pip install dash-bootstrap-components`) — `dbc.Container`,
  `dbc.Row`, `dbc.Col`, `dbc.Card`, themed via `external_stylesheets=[dbc.themes.FLATLY]`.
  The most common professional layout system; responsive 12-column grid.
- **Dash Mantine Components** (`pip install dash-mantine-components`) — modern component set
  (`dmc.Card`, `dmc.SimpleGrid`, `dmc.Grid`); wrap the app in `dmc.MantineProvider`.

Pick **one** layout system and stay consistent. Bootstrap is the safe default for a
finance dashboard; Mantine if a more contemporary look is wanted. A clean card-based grid
of charts/tables on a white background, with the `finance_theme` palette, reads as
executive-grade without any Enterprise tooling.

```python
import dash_bootstrap_components as dbc
app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.layout = dbc.Container([
    dbc.Row([dbc.Col(dbc.Card(dbc.CardBody(dcc.Graph(id="trend"))), md=8),
             dbc.Col(dbc.Card(dbc.CardBody(kpi_stack)), md=4)]),
    dbc.Row(dbc.Col(dbc.Card(dbc.CardBody(dag.AgGrid(id="detail"))))),
], fluid=True)
```

---

## 5. Multi-page apps (Dash Pages)

For a dashboard with several views (P&L, Balance Sheet, KPIs), use Dash Pages instead of
hand-rolled routing.

```python
# app.py
app = Dash(__name__, use_pages=True)
app.layout = html.Div([
    html.Nav([dcc.Link(p["name"], href=p["path"]) for p in dash.page_registry.values()]),
    dash.page_container,
])
```

```python
# pages/pnl.py
import dash
dash.register_page(__name__, path="/", name="P&L")
layout = html.Div([...])     # this page's layout
```

Each file in `pages/` calls `dash.register_page` and defines a `layout`. `dash.page_container`
renders the active page; build the nav from `dash.page_registry`.

---

## 6. Loading states, errors, empty data

- Wrap slow outputs in **`dcc.Loading`** so users see a spinner during queries/jobs.
- Handle **empty results** explicitly — return a small "No data for this selection"
  `html.Div` and an empty figure rather than letting `px` choke on an empty frame.
- Surface **query/connection errors** as a readable message in the layout, not a stack
  trace; log the detail server-side. Set `app.run(debug=True)` only in development.

```python
@callback(Output("trend", "figure"), Input("entity", "value"))
def update(entity):
    df = query_df(...)
    if df.empty:
        return apply_finance_theme(go.Figure()).update_layout(
            annotations=[dict(text="No data for this selection", showarrow=False)])
    return apply_finance_theme(px.line(df, x="month", y="value"))
```

---

## 7. Project layout & deployment

```
my-dash-app/
├── app.py              # Dash app + callbacks (or thin entry that imports pages/)
├── finance_theme.py    # bundled theme/format helpers (copied from this skill)
├── data.py             # query_df + cached query functions (databricks-data.md)
├── pages/              # optional, for multi-page
├── assets/             # CSS, favicon (auto-loaded)
├── requirements.txt    # open-source deps only
└── Procfile            # web: gunicorn app:server --workers 4   (for some hosts)
```

Run locally with `python app.py`; serve in production with `gunicorn app:server`. Deploy on
Databricks Apps or any container/VM — no Enterprise/Plotly-Cloud step. Set Databricks
credentials as environment variables, never in code.
