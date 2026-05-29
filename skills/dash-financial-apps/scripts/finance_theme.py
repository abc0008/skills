"""
finance_theme.py — Pinnacle Financial Partners brand theming + formatting for
open-source Plotly Dash financial apps.

Drop this beside your app.py (or into assets/ and adjust the import). It encodes the
Pinnacle brand palette, Arial typography, the IBCS variance-color convention, a Plotly
template, number formatters, and AG Grid (Community) column/styling builders. Pure
open-source: plotly + dash-ag-grid Community. No Dash Enterprise / AG Grid license.

Pair with pinnacle_layout.py for KPI cards, action titles, and the five-zone page shell.

Key brand rule baked in: GREEN and CORAL are reserved for variance favorability ONLY.
Do not color plain value columns by sign — that destroys the variance signal. Use
variance_col / variance_color on variance (Δ) columns, and leave level columns neutral.
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.io as pio

# --------------------------------------------------------------------------- #
# Pinnacle brand palette (exact hex — do not substitute)
# --------------------------------------------------------------------------- #
NAVY = "#002855"          # headers, table headers, primary/actual series
DEEP_BLUE = "#004976"     # secondary headers, section dividers
TEAL = "#00A3AD"          # KPI accents, secondary/plan series
LIGHT_BLUE = "#5B9BD5"    # tertiary / prior-year series
DARKER_BLUE = "#264478"   # detail borders, series 4
GREEN = "#70AD47"         # FAVORABLE variance ONLY (IBCS)
LIGHT_GREEN = "#C5E0B4"   # positive cell fill / on-track background
CORAL = "#ED7D31"         # UNFAVORABLE variance ONLY (IBCS)
LIGHT_CORAL = "#FDEBD7"   # negative cell fill / off-track background
GOLD = "#FFC000"          # neutral / at-risk indicator
LIGHT_GOLD = "#FFF8E1"    # at-risk cell fill / callout background
LIGHT_TINT = "#E6F2F5"    # alternating rows, zone backgrounds
ALT_ROW_GRAY = "#F2F2F2"  # alternating rows, section backgrounds
BORDER_GRAY = "#D9D9D9"   # borders, gridlines
TEXT_GRAY = "#595959"     # body text
MEDIUM_GRAY = "#A5A5A5"   # inactive labels, baseline/comparison series
WHITE = "#FFFFFF"

FONT = "Arial, Helvetica, sans-serif"   # Pinnacle standard: Arial throughout

# General-purpose series order (max 3 emphasized per chart). Green/Coral are intentionally
# EXCLUDED here because they are reserved for variance favorability.
SEQUENCE = [NAVY, TEAL, LIGHT_BLUE, DARKER_BLUE, GOLD, MEDIUM_GRAY]

# --------------------------------------------------------------------------- #
# Plotly template
# --------------------------------------------------------------------------- #
FINANCE_TEMPLATE = go.layout.Template(
    layout=go.Layout(
        font=dict(family=FONT, size=13, color=TEXT_GRAY),
        title=dict(font=dict(family=FONT, size=16, color=NAVY), x=0.0, xanchor="left"),
        colorway=SEQUENCE,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        xaxis=dict(showgrid=False, linecolor=BORDER_GRAY, ticks="outside",
                   tickcolor=BORDER_GRAY, title=dict(font=dict(color=TEXT_GRAY))),
        yaxis=dict(showgrid=True, gridcolor=BORDER_GRAY, zerolinecolor=MEDIUM_GRAY,
                   title=dict(font=dict(color=TEXT_GRAY))),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    title_text="", font=dict(color=TEXT_GRAY)),
        margin=dict(l=64, r=24, t=48, b=44),
        hoverlabel=dict(font=dict(family=FONT), bgcolor=WHITE, bordercolor=BORDER_GRAY),
        colorscale=dict(sequential=[[0, LIGHT_TINT], [1, NAVY]]),
    )
)
pio.templates["pinnacle"] = FINANCE_TEMPLATE


def apply_finance_theme(fig, *, yformat=None, xformat=None, title=None):
    """Apply the Pinnacle template and optional d3 axis tick formats. Returns fig.
    yformat / xformat examples: '$,.0f', ',.1%', '$,.2s'."""
    fig.update_layout(template=FINANCE_TEMPLATE)
    if yformat:
        fig.update_yaxes(tickformat=yformat)
    if xformat:
        fig.update_xaxes(tickformat=xformat)
    if title is not None:
        fig.update_layout(title=title)
    return fig


# --------------------------------------------------------------------------- #
# IBCS variance favorability — green = favorable, coral = unfavorable, gold = at-risk.
# Favorability is NOT the same as sign: expense under budget is a negative variance but
# favorable. Always pass favorable_when_positive to say which direction is good.
# --------------------------------------------------------------------------- #
def variance_color(value, *, favorable_when_positive=True, at_risk_band=None):
    """Return the IBCS color for a variance value.
    favorable_when_positive=False for cost/expense/delinquency/NCO style metrics where
    coming in below is good. at_risk_band: optional (low, high) on the favorable side that
    should read gold/at-risk instead of green."""
    if value is None:
        return TEXT_GRAY
    favorable = value >= 0 if favorable_when_positive else value <= 0
    if at_risk_band is not None:
        lo, hi = at_risk_band
        if lo <= abs(value) <= hi:
            return GOLD
    return GREEN if favorable else CORAL


def variance_arrow(value, *, favorable_when_positive=True):
    """Directional arrow for a variance (▲ up / ▼ down), independent of favorability."""
    if value is None:
        return ""
    return "▲" if value >= 0 else "▼"


# --------------------------------------------------------------------------- #
# Python-side formatters (KPI tiles, annotations, titles)
# --------------------------------------------------------------------------- #
def fmt_currency(value, decimals=0, symbol="$"):
    return "—" if value is None else f"{symbol}{value:,.{decimals}f}"


def fmt_thousands(value, decimals=0, symbol="$"):
    return "—" if value is None else f"{symbol}{value/1_000:,.{decimals}f}K"


def fmt_millions(value, decimals=1, symbol="$"):
    return "—" if value is None else f"{symbol}{value/1_000_000:,.{decimals}f}M"


def fmt_billions(value, decimals=2, symbol="$"):
    return "—" if value is None else f"{symbol}{value/1_000_000_000:,.{decimals}f}B"


def fmt_pct(value, decimals=1, already_percent=False):
    """value=0.123 -> '12.3%'. already_percent=True if value is 12.3 not 0.123."""
    if value is None:
        return "—"
    v = value if already_percent else value * 100
    return f"{v:,.{decimals}f}%"


def fmt_bps(value, decimals=0, already_bps=False):
    """value=0.0125 -> '125 bps'. already_bps=True if value is already in bps."""
    if value is None:
        return "—"
    v = value if already_bps else value * 10_000
    return f"{v:,.{decimals}f} bps"


# --------------------------------------------------------------------------- #
# AG Grid (Community) column-definition builders
# A dict {"function": "<js>"} is evaluated grid-side; params.value is the cell, d3 is
# available. type 'rightAligned' right-aligns numerics; labels stay left-aligned.
# --------------------------------------------------------------------------- #
def _vf(d3_format):
    return {"function": f"d3.format('{d3_format}')(params.value)"}


def currency_col(field, header=None, *, decimals=0, width=None):
    """Right-aligned currency column, neutral color (IBCS: don't sign-color levels)."""
    col = {"field": field, "headerName": header or field.replace("_", " ").title(),
           "type": "rightAligned", "valueFormatter": _vf(f"$,.{decimals}f")}
    if width:
        col["width"] = width
    return col


def number_col(field, header=None, *, decimals=0, width=None):
    col = {"field": field, "headerName": header or field.replace("_", " ").title(),
           "type": "rightAligned", "valueFormatter": _vf(f",.{decimals}f")}
    if width:
        col["width"] = width
    return col


def percent_col(field, header=None, *, decimals=1, width=None, already_percent=False):
    """Right-aligned percent. Default expects a fraction (0.123 -> 12.3%).
    already_percent=True if stored value is 12.3 rather than 0.123."""
    if already_percent:
        vf = {"function": f"d3.format(',.{decimals}f')(params.value) + '%'"}
    else:
        vf = _vf(f",.{decimals}%")
    col = {"field": field, "headerName": header or field.replace("_", " ").title(),
           "type": "rightAligned", "valueFormatter": vf}
    if width:
        col["width"] = width
    return col


def variance_col(field, header=None, *, kind="currency", decimals=0, width=None,
                 favorable_when_positive=True):
    """A variance (Δ) column colored by IBCS favorability: favorable green, unfavorable
    coral. Set favorable_when_positive=False for expense/cost/risk metrics where a
    negative variance is good. kind: 'currency' | 'percent' | 'bps' | 'number'."""
    if kind == "currency":
        vf = _vf(f"$,.{decimals}f")
    elif kind == "percent":
        vf = _vf(f",.{max(decimals,1)}%")
    elif kind == "bps":
        # stored as a fraction (0.0012) -> '12 bps'; multiply by 10,000 grid-side
        vf = {"function": "d3.format(',.0f')(params.value * 10000) + ' bps'"}
    else:
        vf = _vf(f",.{decimals}f")
    good, bad = (">= 0", "< 0") if favorable_when_positive else ("<= 0", "> 0")
    col = {"field": field, "headerName": header or field.replace("_", " ").title(),
           "type": "rightAligned", "valueFormatter": vf,
           "cellStyle": {"styleConditions": [
               {"condition": f"params.value {good}",
                "style": {"color": GREEN, "fontWeight": "600"}},
               {"condition": f"params.value {bad}",
                "style": {"color": CORAL, "fontWeight": "600"}},
           ]}}
    if width:
        col["width"] = width
    return col


# --------------------------------------------------------------------------- #
# AG Grid (Community) styling: Pinnacle look + conditional cell styles
# --------------------------------------------------------------------------- #
def pinnacle_grid_style():
    """Return (defaultColDef, dashGridOptions-fragment, getRowStyle, className-css-vars)
    for a Pinnacle-branded grid: navy header, alt-row tint, gray borders, Arial.
    Apply via dag.AgGrid(defaultColDef=..., dashGridOptions={..., **frag})."""
    default_col_def = {"sortable": True, "filter": True, "resizable": True,
                       "cellStyle": {"fontFamily": FONT}}
    # Header + row striping are set through CSS class rules; see references for the
    # assets/pinnacle_grid.css snippet. Alt rows can also be done with getRowStyle:
    get_row_style = {"styleConditions": [
        {"condition": "params.rowIndex % 2 === 1",
         "style": {"backgroundColor": ALT_ROW_GRAY}}]}
    return default_col_def, get_row_style


def rag_style_conditions(amber_below, green_at_or_above, *, higher_is_better=True):
    """Red/Amber/Green cellStyle. higher_is_better=False flips it (cost/risk ratios).
    Thresholds compare the raw stored value (pass fractions if data is fractional)."""
    if higher_is_better:
        conds = [
            {"condition": f"params.value >= {green_at_or_above}",
             "style": {"color": GREEN, "fontWeight": "600"}},
            {"condition": f"params.value < {amber_below}",
             "style": {"color": CORAL, "fontWeight": "600"}},
            {"condition": "true", "style": {"color": GOLD, "fontWeight": "600"}}]
    else:
        conds = [
            {"condition": f"params.value <= {green_at_or_above}",
             "style": {"color": GREEN, "fontWeight": "600"}},
            {"condition": f"params.value > {amber_below}",
             "style": {"color": CORAL, "fontWeight": "600"}},
            {"condition": "true", "style": {"color": GOLD, "fontWeight": "600"}}]
    return {"styleConditions": conds}


def status_fill_conditions(favorable_when_positive=True):
    """Background-fill version (light green / light coral) for a variance/status column."""
    good, bad = (">= 0", "< 0") if favorable_when_positive else ("<= 0", "> 0")
    return {"styleConditions": [
        {"condition": f"params.value {good}", "style": {"backgroundColor": LIGHT_GREEN}},
        {"condition": f"params.value {bad}", "style": {"backgroundColor": LIGHT_CORAL}}]}


def totals_row(df, label_field, sum_fields, *, label="Total"):
    """One-row list for AG Grid pinnedBottomRowData (Community-safe totals)."""
    row = {label_field: label}
    for f in sum_fields:
        row[f] = float(df[f].sum())
    return [row]
