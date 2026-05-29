---
name: dash-financial-apps
description: Build professional, Pinnacle-branded financial charts, tables, and dashboards using open-source Plotly Dash in Python, especially when sourcing data from Databricks. Use whenever the user wants to visualize financial, accounting, or banking data in Dash — NII/P&L waterfalls and variance bridges, rate/volume/mix, NIM and efficiency-ratio trends, actual-vs-budget combos, top/bottom movers, KPI cards, deposit/loan mix, or formatted financial tables (currency, %, bps, IBCS variance coloring, totals rows). Trigger for any Dash app, dashboard, dash-ag-grid/DataTable, dcc.Graph, or plotly figure in a finance/banking context, for laying a finance dashboard to the Pinnacle five-zone or report-type standard, and for connecting a Dash app to a Databricks SQL Warehouse or Jobs. Assume open-source only — no Dash Enterprise, Plotly Cloud, Design Kit, or AG Grid Enterprise license. Use even when the user says "chart," "graph," "table," or "dashboard" without naming Dash, as long as the stack is Plotly/Dash/Databricks.
---

# Dash Financial Apps (Pinnacle, Open-Source + Databricks)

Build executive-grade financial visualizations in Plotly Dash using only open-source
components, branded to the **Pinnacle Financial Partners** standard, with data typically
coming from a Databricks SQL Warehouse or Databricks Jobs. The goal is output a Pinnacle
finance leader would put in front of a CFO: correct numbers, restrained brand styling,
currency/percent/bps formatting that reads cleanly, IBCS-correct variance signals, and
tables and pages that follow the Pinnacle layout standard — not a generic web demo.

## The hard constraint: open-source only

This skill assumes there is **no Dash Enterprise, no Plotly Cloud account, and no AG Grid
Enterprise license.** That rules out a few things the official docs casually suggest, so
do not reach for them:

- **Do NOT use Dash Design Kit (DDK)** — `import dash_design_kit` / `ddk.App`, `ddk.Card`,
  `ddk.Graph`. It is Enterprise-licensed and will fail to import. Use plain `html`/`dcc`
  plus the `pinnacle_layout.py` helpers (or Dash Bootstrap / Mantine) for layout instead.
- **Do NOT use the Plotly Cloud / Dash Enterprise publish flow** (`plotly app publish`,
  `dash[cloud]`, `de deploy`). Deploy with plain `gunicorn`, or on Databricks Apps.
- **Do NOT use AG Grid Enterprise features**: row grouping, pivoting, built-in value
  aggregation, the tool-panel sidebar, master/detail, sparklines, tree data. These need
  `enableEnterpriseModules=True` + a license. When a request implies one of these (e.g.
  "group by region and subtotal"), do the grouping/aggregation in **pandas or SQL** and
  feed the grid pre-shaped rows. See `references/financial-tables.md`.

Everything else — `dash`, `plotly`, `dash-ag-grid` (Community), `dash-bootstrap-components`,
`dash-mantine-components`, `pandas`, the `databricks-sql-connector`, and `databricks-sdk` —
is open-source and fair game.

## Pinnacle brand + IBCS (non-negotiable)

- **Palette (exact hex):** Navy `#002855` (headers/primary), Deep Blue `#004976`, Teal
  `#00A3AD` (accents/secondary series), Light Blue `#5B9BD5` (tertiary), Darker Blue
  `#264478`. **Arial throughout.** All in `finance_theme.py`.
- **IBCS variance colors are reserved:** Green `#70AD47` = favorable, Coral `#ED7D31` =
  unfavorable, Gold `#FFC000` = at-risk. **Never** use green/coral for ordinary category
  coloring or to color a value by its sign — that destroys the variance signal. Color
  *variance* columns/series by **favorability** (which is not the same as sign: expense
  under budget is a negative variance but favorable) via `variance_col` / `variance_color`,
  and leave level columns neutral.
- **IBCS fills:** solid = actual, outline/hollow = plan/budget, hatched = forecast.
- **Action titles, not labels:** every chart title states the insight ("Premium drove 67%
  of Q4 growth"), max ~15 words.
- **BAN LIST — never use:** 3D charts, pie charts with >5 segments, dual-axis charts
  (misleading scales), gauge charts. Use the chart-selection matrix in `layout-standards.md`.

## Workflow

1. **Clarify the deliverable, briefly.** What financial view is this (variance bridge, NIM
   trend, KPI summary, detail table)? Which **report type** — Ad Hoc, Drillthrough,
   Executive, or Operational (see `layout-standards.md`)? Where does the data live (a
   Databricks table/query, an uploaded CSV, a sample)? If the user gave enough, proceed.
2. **Read the relevant reference file(s) before writing code.** They hold the correct,
   non-obvious patterns; pulling these from memory is where mistakes happen.
   - Page layout, zones, KPI cards, report types, chart-selection → `references/layout-standards.md`
   - App skeleton, callbacks, multi-page, styling, deployment → `references/app-structure.md`
   - Charting fundamentals + Pinnacle styling → `references/financial-charts.md`
   - Banking recipes (NII bridge, rate/volume, NIM, movers, mix, bullet) → `references/banking-charts.md`
   - Any table/grid → `references/financial-tables.md`
   - Any Databricks data access → `references/databricks-data.md`
3. **Reuse the bundled modules.** `scripts/finance_theme.py` (palette, Plotly template,
   formatters, IBCS variance helpers, AG Grid builders) and `scripts/pinnacle_layout.py`
   (KPI cards, action titles, the five-zone page shell, report-type canvas sizes). Copy
   both next to the app and import from them rather than re-deriving brand styling.
4. **Write a single, runnable `app.py`** (unless the user wants multi-page). Make it run as
   written: correct imports, real component IDs, `app.run(debug=True)` at the bottom.
5. **Sanity-check before handing off.** Confirm imports resolve to open-source packages,
   no Enterprise components slipped in, every `Output`/`Input` ID exists in the layout,
   and numbers are formatted (no raw `1234567.89` floats in a finance deliverable).

## Modern Dash idioms (get these right)

These trip up code generated from older training data. Dash 3.x is the current line.

- **Run with `app.run(debug=True)`** — `app.run_server()` was removed in Dash 3.0.
- **Import the callback decorator directly**: `from dash import Dash, html, dcc, callback,
  Input, Output, State`. Use `@callback` (not `@app.callback`) so callbacks don't depend on
  the `app` object's scope.
- **`app.layout` can be a list** (Dash 2.17+): `app.layout = [html.H1(...), dcc.Graph(...)]`.
- **Prefer `dash_ag_grid` over `dash_table.DataTable`** for new tables — DataTable is
  deprecated and slated for removal in Dash 5.0. (DataTable still works today, and some
  Databricks docs use it, so it's acceptable if the user explicitly wants it.)
- **Prefer `plotly.express` (`px`)** for standard charts; drop to `plotly.graph_objects`
  (`go`) only for things px can't express cleanly (waterfalls, fine-grained combo charts,
  custom KPI indicators).
- **Don't stuff interactive/filtered data into module-level globals.** A global DataFrame
  that callbacks mutate or re-filter causes cross-user bugs because the server is shared.
  Load *static reference* data once at module scope (read-only is fine); for anything that
  changes per user/interaction, query inside the callback or stash per-session state in a
  `dcc.Store`. This is the "global variables will break your app" rule.

## Using the bundled modules

Two modules are the highest-leverage assets here. Import from them; don't re-derive brand
styling or hand-write format strings.

**`scripts/finance_theme.py`** — Pinnacle palette + Plotly/AG Grid styling:
- `FINANCE_TEMPLATE` (registered as the `"pinnacle"` template) and `apply_finance_theme(fig,
  yformat=..., title=...)` — navy/teal/Arial template so charts look like a Pinnacle report.
- Brand color constants: `NAVY, DEEP_BLUE, TEAL, LIGHT_BLUE, DARKER_BLUE, GREEN, CORAL,
  GOLD, MEDIUM_GRAY, BORDER_GRAY, ...`.
- `variance_color(value, favorable_when_positive=...)` and `variance_arrow(...)` — IBCS
  favorability color/arrow (the right way to color variances; not by sign).
- `fmt_currency, fmt_thousands, fmt_millions, fmt_billions, fmt_pct, fmt_bps` — Python-side
  formatters for KPI text and labels.
- `currency_col, number_col, percent_col` (neutral level columns) and `variance_col(...,
  favorable_when_positive=...)` (IBCS-colored Δ column) — AG Grid column builders.
- `rag_style_conditions(...)`, `status_fill_conditions(...)`, `pinnacle_grid_style()`,
  `totals_row(...)` — conditional styling, the navy-header/alt-row grid look, totals row.

**`scripts/pinnacle_layout.py`** — Pinnacle layout primitives (Dash html/dcc):
- `page_title`, `chart_title` (action titles), `footnote` — the three text levels.
- `kpi_card(...)` (Value + Label + Comparison + Trend + Period, IBCS-colored) and `kpi_row`.
- `five_zone_page(report_type=..., header=, kpis=, primary=, secondary=, detail=, footer=)`
  — the five-zone skeleton with the correct canvas width and 8px spacing.
- `header_bar(...)` (refresh + filter context) and `back_button(...)` (drillthrough).
- `CANVAS` / `ZONES` dicts encode the four report-type sizes and zone splits.

Keep both files beside `app.py` (or in `assets/` and adjust imports). The reference files
show them in use.

## Financial presentation defaults

Apply these unless the user asks otherwise — they're what makes output read as a Pinnacle
deliverable rather than a tech demo:

- **Format every number.** Currency as `$1.2M` / `$1,234,567`, ratios as `12.3%`, small rate
  moves in **bps**. Never surface raw floats in a table or KPI tile.
- **Color carries variance meaning only.** Green favorable / coral unfavorable / gold
  at-risk, applied to *variance* via favorability — not to level columns and not by sign.
- **Action titles**, not metric labels, on every chart (max ~15 words).
- **Most important KPI top-left; never a logo there.** KPI cards carry value + comparison +
  trend + period.
- **Right-align numerics**, left-align labels; pin a **totals row** (`pinnedBottomRowData`);
  sort detail tables by **variance/severity, not alphabetically**.
- **Label axes with units** via d3 `tickformat` (`"$,.0f"`, `",.1%"`), not post-formatting.
- **8px spacing, ≤3 colors per chart, no-scroll pages.** No banned chart types (3D, pie >5,
  dual-axis, gauge).

## Quick reference: the smallest correct app

A minimal but correct Pinnacle shape to build on (swap the data source for Databricks per
`references/databricks-data.md`; for a full zoned dashboard use `five_zone_page`):

```python
from dash import Dash, html, dcc, callback, Input, Output
import dash_ag_grid as dag
import plotly.express as px
import pandas as pd
from finance_theme import (apply_finance_theme, NAVY, LIGHT_BLUE,
                           currency_col, variance_col, pinnacle_grid_style)
from pinnacle_layout import page_title, chart_title, footnote

df = pd.read_csv("data.csv")  # or query Databricks inside the callback
default_col_def, get_row_style = pinnacle_grid_style()

app = Dash(__name__)
server = app.server  # WSGI entrypoint for gunicorn / Databricks Apps

app.layout = html.Div([
    page_title("Commercial RE drove 62% of the variance from plan"),  # action title
    dcc.Dropdown(sorted(df["year"].unique()), df["year"].max(), id="year"),
    chart_title("Actual vs Budget by segment"),
    dcc.Graph(id="chart"),
    dag.AgGrid(
        id="grid",
        rowData=df.to_dict("records"),
        columnDefs=[{"field": "segment", "pinned": "left"},
                    currency_col("actual", "Actual"),
                    currency_col("budget", "Budget"),
                    variance_col("variance", "Var vs Budget")],  # IBCS-colored Δ
        defaultColDef=default_col_def,
        className="ag-theme-quartz pinnacle-grid",
        dashGridOptions={"getRowStyle": get_row_style, "pagination": True},
    ),
    footnote("Source: Finance Analytics / Hyperion · Refreshed daily"),
], style={"maxWidth": 1600, "margin": "0 auto", "padding": 40,
          "fontFamily": "Arial, sans-serif"})

@callback(Output("chart", "figure"), Input("year", "value"))
def update(year):
    d = df[df["year"] == year]
    fig = px.bar(d, x="segment", y=["actual", "budget"], barmode="group",
                 color_discrete_sequence=[NAVY, LIGHT_BLUE])
    return apply_finance_theme(fig, yformat="$,.0f")

if __name__ == "__main__":
    app.run(debug=True)
```

Add `assets/pinnacle_grid.css` for the navy header (see `references/financial-tables.md` §3).

## Dependencies

Open-source install line for a typical financial Dash app on Databricks:

```bash
pip install dash dash-ag-grid plotly pandas databricks-sql-connector
# add as needed: dash-bootstrap-components  dash-mantine-components  databricks-sdk  gunicorn
```

## When working inside Databricks specifically

The user is typically driving a Databricks AI agent. Keep these in mind (details in
`references/databricks-data.md`):

- Authenticate with **environment variables / secrets**, never hard-coded tokens:
  `SERVER_HOSTNAME`, `HTTP_PATH`, `ACCESS_TOKEN` for the SQL connector.
- **Push filtering and aggregation into SQL** so the browser receives small result sets;
  AG Grid Community has no server-side row model, so don't ship millions of rows to it.
- For long-running compute, trigger a **Databricks Job** via the SDK and read its output,
  rather than blocking a callback on heavy work.
- Deploy as a normal WSGI app (`server = app.server`, run under `gunicorn`); Databricks
  Apps can host it. The Enterprise/Plotly-Cloud publish commands do not apply here.
