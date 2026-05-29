# Financial Tables in Dash (open-source: AG Grid Community + DataTable)

How to build Pinnacle-standard, management-report-quality tables with **only** open-source
components. Default to **Dash AG Grid Community** (`pip install dash-ag-grid`, `import
dash_ag_grid as dag`). DataTable still works but is deprecated (removal targeted for Dash
5.0); use it only if the user asks. Examples assume `from finance_theme import currency_col,
percent_col, number_col, variance_col, rag_style_conditions, status_fill_conditions,
totals_row, pinnacle_grid_style`.

**Pinnacle table look:** navy `#002855` header with white Arial text, alternating-row tint
(`#F2F2F2`), gray `#D9D9D9` borders, numerics right-aligned, labels left-aligned. The
`pinnacle_grid_style()` helper returns the `defaultColDef` and an alt-row `getRowStyle`; the
navy header is applied with a tiny CSS class (see §3). **IBCS rule:** color cells green/coral
by *variance favorability*, not by sign — so plain level columns (revenue, balances) stay
neutral, and only Δ/variance columns get colored via `variance_col`.

## Table of contents
1. The Community-vs-Enterprise line (what you cannot use, and the workaround)
2. Basic grid + finance column types
3. Pinnacle styling (navy header, alt rows) + number formatting
4. IBCS variance coloring, RAG, status fills
5. Totals / subtotals without Enterprise aggregation
6. Sorting, filtering, pagination, sizing
7. Handling large data: don't ship millions of rows
8. Editable grids & reading edits in a callback
9. Exporting to CSV
10. DataTable fallback

---

## 1. The Community-vs-Enterprise line

AG Grid Community is free and covers most financial tables. These features are
**Enterprise-only** (need `enableEnterpriseModules=True` + a paid license) and must be
avoided:

| Enterprise feature | Open-source workaround |
|---|---|
| Row grouping / tree data | Group in **pandas/SQL**; render one grid per group or a pre-grouped flat grid with an indented label column |
| Built-in value aggregation (group subtotals) | Compute subtotals with `df.groupby(...).sum()`; insert subtotal rows into `rowData`, or use multiple grids |
| Pivoting | Pivot in pandas (`df.pivot_table`) and feed the wide frame as ordinary columns |
| Tool-panel sidebar | Provide your own `dcc.Dropdown`/`dcc.Checklist` filter controls |
| Master / detail | Use a second grid (or a `dcc.Graph`) driven by `selectedRows` via callback |
| Sparklines in cells | Put a small `dcc.Graph` beside the grid, or a column of unicode bars |

Pinned rows, conditional styling, value formatters, sorting, filtering, pagination,
editing, and CSV export are all **Community** — that covers the vast majority of finance
reporting needs.

---

## 2. Basic grid + finance column types

```python
import dash_ag_grid as dag
from finance_theme import (currency_col, percent_col, number_col, variance_col,
                           totals_row, pinnacle_grid_style)

default_col_def, get_row_style = pinnacle_grid_style()

columnDefs = [
    {"field": "segment", "headerName": "Segment", "pinned": "left", "minWidth": 180},
    currency_col("actual", "Actual"),                 # level → neutral (IBCS)
    currency_col("budget", "Budget"),                 # level → neutral
    variance_col("variance", "Var vs Budget"),        # Δ → green favorable / coral unfav.
    percent_col("attainment", "Attainment"),          # expects fraction (0.123)
]

grid = dag.AgGrid(
    id="pl-grid",
    rowData=df.to_dict("records"),
    columnDefs=columnDefs,
    defaultColDef=default_col_def,
    className="ag-theme-quartz pinnacle-grid",        # navy header via CSS (see §3)
    dashGridOptions={"getRowStyle": get_row_style, "pagination": True,
                     "paginationPageSize": 20},
    columnSize="sizeToFit",
    style={"height": 520},
)
```

The builders right-align numerics and attach the correct d3 formatter. **Level columns stay
neutral; only the variance column is colored** (favorability, not sign). Left-pin the label
column so it stays visible on horizontal scroll. For an expense/cost variance where coming
in under is good, use `variance_col("variance", favorable_when_positive=False)`.

---

## 3. Pinnacle styling (navy header, alt rows) + number formatting

`pinnacle_grid_style()` gives Arial defaults + an alternating-row tint. The **navy header
with white text** is one small CSS rule — put this in `assets/pinnacle_grid.css` (Dash
auto-loads `assets/`):

```css
.pinnacle-grid .ag-header { background-color: #002855; }
.pinnacle-grid .ag-header-cell-text { color: #FFFFFF; font-family: Arial; font-weight: 600; }
.pinnacle-grid { --ag-border-color: #D9D9D9; --ag-font-family: Arial; }
```

Cells format via JS-side **valueFormatter** — a dict `{"function": "<js>"}` evaluated
grid-side where `params.value` is the cell and `d3` is available. The builders wrap this;
to hand-roll: `{"valueFormatter": {"function": "d3.format('$,.0f')(params.value)"}}`. Keep
stored values numeric so sorting/filtering use the real number.

---

## 4. IBCS variance coloring, RAG, status fills

`cellStyle` accepts a Dash-friendly `styleConditions` list (Community). First match wins; a
trailing `"condition": "true"` is the default.

```python
# Variance column, colored by favorability (built in to variance_col):
variance_col("variance", "Var vs Plan", favorable_when_positive=True)

# Red/Amber/Green on a coverage ratio where higher is better (thresholds on a fraction):
{**percent_col("dscr", "DSCR", already_percent=True),
 "cellStyle": rag_style_conditions(amber_below=1.20, green_at_or_above=1.50)}

# For a cost/risk ratio where lower is better, flip it:
{**percent_col("efficiency", "Efficiency"),
 "cellStyle": rag_style_conditions(0.60, 0.55, higher_is_better=False)}

# Light green/coral background fill for an on-track/off-track status column:
{**currency_col("variance", "Status"),
 "cellStyle": status_fill_conditions(favorable_when_positive=True)}

# Background highlight on a whole row condition (e.g., flag watch-list accounts):
{"field": "risk_rating",
 "cellStyle": {"styleConditions": [
     {"condition": "params.value >= 6", "style": {"backgroundColor": "#FBEAE8"}},
 ]}}
```

For a simple in-cell "data bar," a background gradient via `styleConditions` keyed on value
buckets works without Enterprise. For anything fancier, prefer a small chart beside the
grid.

---

## 5. Totals / subtotals without Enterprise aggregation

Use a **pinned bottom row** for grand totals — it's Community and always visible:

```python
from finance_theme import totals_row
grid = dag.AgGrid(
    rowData=df.to_dict("records"),
    columnDefs=columnDefs,
    dashGridOptions={
        "pinnedBottomRowData": totals_row(df, "segment",
                                          ["revenue", "expense", "net_income"]),
    },
)
```

For **subtotals by group**, compute them in pandas and interleave subtotal rows into the
data (style them via a flag column + `styleConditions`):

```python
parts = []
for seg, g in df.groupby("region"):
    parts.append(g)
    sub = g[["revenue", "expense"]].sum()
    parts.append(pd.DataFrame([{"region": f"{seg} subtotal", "is_subtotal": True,
                                "revenue": sub.revenue, "expense": sub.expense}]))
shaped = pd.concat(parts, ignore_index=True)
# then bold subtotal rows: cellStyle condition on params.data.is_subtotal === true
```

This reproduces grouped-subtotal reports without the Enterprise row-grouping module.

---

## 6. Sorting, filtering, pagination, sizing

- **Defaults once** via `defaultColDef={"sortable": True, "filter": True, "resizable":
  True}` instead of repeating per column.
- **Filter types**: `"filter": "agNumberColumnFilter"` for amounts, `"agDateColumnFilter"`
  for dates, `"agTextColumnFilter"` for labels. Bare `True` picks a sensible default.
- **Sizing**: `columnSize="sizeToFit"` fills the width; `"autoSize"` fits content. Pin key
  columns with `"pinned": "left"`.
- **Pagination**: `dashGridOptions={"pagination": True, "paginationPageSize": 25}`.
- **Theme**: default is `themeQuartz`; switch via `dashGridOptions={"theme":
  "themeBalham"}` (Balham is compact and reads well for dense financial tables).

---

## 7. Don't ship millions of rows

AG Grid Community has **no server-side row model** (that's Enterprise). So:

- Aggregate/filter in **SQL or pandas** before populating `rowData`. A management report
  rarely needs more than a few thousand rows in the browser.
- For drill-down, keep the summary grid small and query detail **on demand** in a callback
  triggered by `cellClicked`/`selectedRows`.
- If you genuinely must browse a very large detail set, paginate at the **query** level
  (LIMIT/OFFSET against Databricks) and drive the page from a callback, rather than loading
  everything and paginating client-side.

---

## 8. Editable grids & reading edits

Useful for forecast/assumption input. Mark columns `"editable": True`, then read the
edited `rowData` (or `cellValueChanged`) in a callback.

```python
columnDefs = [{"field": "account"},
              {**currency_col("forecast", "Forecast"), "editable": True}]

@callback(Output("total", "children"),
          Input("grid", "cellValueChanged"),
          State("grid", "rowData"))
def recompute(_, rows):
    return fmt_currency(sum(r["forecast"] for r in rows))
```

---

## 9. Exporting to CSV

CSV export is Community. Enable a button by setting `csvExportParams` and calling
`exportDataAsCsv` via the `exportDataAsCsv` grid property triggered from a callback:

```python
dag.AgGrid(id="grid", ..., csvExportParams={"fileName": "pl_detail.csv"})

@callback(Output("grid", "exportDataAsCsv"), Input("export-btn", "n_clicks"))
def export(n):
    return bool(n)
```

---

## 10. DataTable fallback

If the user specifically wants `dash_table.DataTable` (e.g. matching an existing
Databricks doc example), it still works. Finance essentials map as:

```python
from dash import dash_table
dash_table.DataTable(
    data=df.to_dict("records"),
    columns=[{"name": "Revenue", "id": "revenue", "type": "numeric",
              "format": {"specifier": "$,.0f"}}],   # d3 specifier
    sort_action="native", filter_action="native", page_size=20,
    style_data_conditional=[
        {"if": {"filter_query": "{net_income} < 0", "column_id": "net_income"},
         "color": "#C0392B"}],
    style_cell={"textAlign": "right", "fontFamily": "Arial"},
    style_cell_conditional=[{"if": {"column_id": "segment"}, "textAlign": "left"}],
)
```

Note the different APIs: DataTable uses `format={"specifier": ...}` and
`style_data_conditional` with `filter_query`, whereas AG Grid uses `valueFormatter` and
`cellStyle`/`styleConditions`. Don't mix them up. For new work, prefer AG Grid.
