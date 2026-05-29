"""
starter_app.py — a complete, runnable Pinnacle-branded executive finance dashboard.

A Type 3 (Executive Summary) layout: five-zone skeleton, Z-pattern, larger KPI cards,
an NII waterfall as the primary chart, a top/bottom movers bar as secondary, and an AG Grid
P&L detail (sorted by variance, IBCS-colored). Uses generated sample data so it runs with
no Databricks connection — replace load_sample() with query_df(...) (see
references/databricks-data.md) to wire it to a SQL Warehouse.

Run:
    pip install dash dash-ag-grid plotly pandas
    python starter_app.py          # http://127.0.0.1:8050

Keep finance_theme.py, pinnacle_layout.py, and assets/pinnacle_grid.css alongside this file
(here assets/pinnacle_grid.css applies the navy grid header automatically).
"""
from dash import Dash, html, dcc, callback, Input, Output
import dash_ag_grid as dag
import plotly.graph_objects as go
import pandas as pd
import numpy as np

from finance_theme import (
    apply_finance_theme, NAVY, GREEN, CORAL, MEDIUM_GRAY,
    fmt_billions, fmt_millions, fmt_thousands, fmt_pct, variance_color,
    currency_col, variance_col, percent_col, pinnacle_grid_style, totals_row,
)
from pinnacle_layout import (
    five_zone_page, header_bar, page_title, chart_title, footnote, kpi_card, kpi_row,
)


# --------------------------------------------------------------------------- #
# Sample data (swap for Databricks queries in real use)
# --------------------------------------------------------------------------- #
def load_sample():
    rng = np.random.default_rng(11)
    segments = ["Commercial", "Consumer", "Wealth", "Treasury", "Cards"]
    actual = np.array([128.4, 86.2, 41.9, 22.5, 18.7]) * 1e6
    budget = np.array([120.0, 88.0, 39.0, 24.0, 17.0]) * 1e6
    detail = pd.DataFrame({"segment": segments, "actual": actual, "budget": budget})
    detail["variance"] = detail["actual"] - detail["budget"]
    detail["attainment"] = detail["actual"] / detail["budget"]
    return detail


detail = load_sample()


# --------------------------------------------------------------------------- #
# Primary chart: NII waterfall bridge (action title states the insight)
# --------------------------------------------------------------------------- #
def nii_bridge():
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["FY24 NII", "Volume", "Rate", "Mix", "FY25 NII"],
        y=[420.0, 38.5, -22.1, 9.3, None],
        text=["$420.0M", "+$38.5M", "-$22.1M", "+$9.3M", "$445.7M"],
        textposition="outside",
        connector={"line": {"color": "#D9D9D9"}},
        increasing={"marker": {"color": GREEN}},
        decreasing={"marker": {"color": CORAL}},
        totals={"marker": {"color": NAVY}},
    ))
    fig = apply_finance_theme(fig, yformat="$,.0f")
    fig.update_layout(height=360, margin=dict(l=64, r=24, t=12, b=40))
    return fig


# --------------------------------------------------------------------------- #
# Secondary chart: top/bottom movers (variance by segment, IBCS-colored)
# --------------------------------------------------------------------------- #
def movers_chart(df):
    d = df.reindex(df["variance"].abs().sort_values().index)
    colors = [variance_color(v, favorable_when_positive=True) for v in d["variance"]]
    def _signed(v):
        mag = fmt_millions(abs(v)) if abs(v) >= 1e6 else fmt_thousands(abs(v))
        return ("−" + mag) if v < 0 else ("+" + mag)
    labels = [_signed(v) for v in d["variance"]]
    fig = go.Figure(go.Bar(x=d["variance"], y=d["segment"], orientation="h",
                           marker_color=colors, text=labels, textposition="outside",
                           cliponaxis=False))
    fig.add_vline(x=0, line_color=MEDIUM_GRAY)
    fig = apply_finance_theme(fig, xformat="$,.2s")
    fig.update_layout(height=360, yaxis_title="", showlegend=False,
                      margin=dict(l=110, r=60, t=12, b=40))
    fig.update_yaxes(automargin=True)
    return fig


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
app = Dash(__name__)
server = app.server

default_col_def, get_row_style = pinnacle_grid_style()

columnDefs = [
    {"field": "segment", "headerName": "Segment", "pinned": "left", "minWidth": 160},
    currency_col("actual", "Actual"),
    currency_col("budget", "Budget"),
    variance_col("variance", "Var vs Budget", favorable_when_positive=True),
    percent_col("attainment", "Attainment"),
]

detail_grid = html.Div([
    chart_title("Segment P&L — sorted by variance, largest unfavorable first"),
    dag.AgGrid(
        id="pl-grid",
        rowData=detail.sort_values("variance").to_dict("records"),
        columnDefs=columnDefs,
        defaultColDef=default_col_def,
        className="ag-theme-quartz pinnacle-grid",
        columnSize="sizeToFit",
        dashGridOptions={"getRowStyle": get_row_style,
                         "pinnedBottomRowData": totals_row(
                             detail, "segment", ["actual", "budget", "variance"])},
        style={"height": 240},
    ),
])

kpis = kpi_row([
    kpi_card("Net Revenue", fmt_billions(1.24e9), delta=0.042, delta_str="4.2% vs Plan",
             period="Q1 2026", emphasis=True, status="on_track"),
    kpi_card("NIM", fmt_pct(0.0287, already_percent=False), delta=-0.0008,
             delta_str="8bps vs Q4", period="Q1 2026", emphasis=True, status="at_risk"),
    kpi_card("NCO Rate", fmt_pct(0.0042, already_percent=False), delta=-0.0003,
             delta_str="improving", period="Q1 2026", favorable_when_positive=False,
             emphasis=True, status="on_track"),
    kpi_card("Avg Deposits", fmt_billions(18.4e9), delta=0.011, delta_str="1.1% MoM",
             period="Q1 2026", emphasis=True),
])

app.layout = five_zone_page(
    report_type="executive",
    header=header_bar(
        page_title("Expense growth tracking below revenue — positive operating leverage"),
        refresh="March 1, 2026", period="Q1 2026", filters="All Business Units"),
    kpis=kpis,
    primary=html.Div([
        chart_title("Net interest income grew $25.7M as volume gains outpaced rate pressure"),
        dcc.Graph(figure=nii_bridge(), config={"displayModeBar": False}),
    ]),
    secondary=html.Div([
        chart_title("Commercial led the favorable swing; Treasury lagged plan"),
        dcc.Graph(id="movers", config={"displayModeBar": False}),
    ]),
    detail=detail_grid,
    footer=footnote("Source: Finance Analytics / Hyperion  ·  Confidential — Board Use Only  "
                    "·  Pinnacle Finance Analytics"),
)


@callback(Output("movers", "figure"), Input("pl-grid", "rowData"))
def update_movers(_rows):
    return movers_chart(detail)


if __name__ == "__main__":
    app.run(debug=True)
