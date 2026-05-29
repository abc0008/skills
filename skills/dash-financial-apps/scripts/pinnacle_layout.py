"""
pinnacle_layout.py — Pinnacle Finance Analytics layout primitives for open-source Dash.

Encodes the Power BI Layout Standards (five-zone skeleton, KPI card spec, action titles,
8px spacing system, report-type canvas sizes) as reusable Dash html/dcc helpers. Pair
with finance_theme.py for colors/formatters. Pure open-source.

Core ideas from the standard:
- Inverted pyramid: answer first; the most important KPI goes top-left; never a logo there.
- Action titles: every chart's title states the insight, not the metric ("Premium drove
  67% of Q4 growth", not "Revenue by Segment"). Max ~15 words.
- Three text levels only: L1 page title 20-24px semibold, L2 chart title 14-16px,
  L3 footnote 10-12px. One font (Arial). Left-align always.
- 8px grid: 16-20px between visuals, 24-32px between zones, 32-48px outer margins.
- Five zones: Header 5-8% / KPI 12-18% / Primary 40-50% (left ~60% width) /
  Secondary (remaining) / Detail 20-25% / Footer 3-5%.
- KPI cards must show Value + Label + Comparison(Δ vs target) + Trend + Period.
"""
from __future__ import annotations
from dash import html
from finance_theme import (
    FONT, NAVY, TEAL, TEXT_GRAY, MEDIUM_GRAY, BORDER_GRAY, WHITE,
    LIGHT_GREEN, LIGHT_CORAL, LIGHT_GOLD, GREEN, CORAL, GOLD,
    variance_color, variance_arrow,
)

# 8px spacing system -------------------------------------------------------- #
GAP_VISUAL = 16     # between visuals
GAP_ZONE = 24       # between zones
MARGIN_OUTER = 40   # outer page margin (multiple of 8, within 32-48)

# Report-type canvas sizes (px) from the standard --------------------------- #
CANVAS = {
    "ad_hoc":      (1600, 900),   # Type 1 — F-pattern, max 6-8 visuals, export-safe
    "drillthrough":(1600, 900),   # Type 2 — max 7 pages, back button top-left
    "executive":   (1600, 900),   # Type 3 — Z-pattern, max 5-7 visuals, zero scroll
    "operational": (1920, 1080),  # Type 4 — 6-8 compact KPIs, thresholds, refresh stamp
}

# Zone height fractions per report type (header, kpi, body, detail, footer) -- #
ZONES = {
    "ad_hoc":      dict(header=0.06, kpi=0.14, body=0.50, detail=0.25, footer=0.05),
    "executive":   dict(header=0.07, kpi=0.18, body=0.50, detail=0.20, footer=0.05),
    "operational": dict(header=0.05, kpi=0.15, body=0.55, detail=0.25, footer=0.00),
    "drillthrough":dict(header=0.10, kpi=0.15, body=0.45, detail=0.25, footer=0.05),
}


# Text levels --------------------------------------------------------------- #
def page_title(text, sub=None):
    """L1 page/action title (20-24px semibold, navy). Optional sub-line in gray."""
    children = [html.Div(text, style={"fontSize": 22, "fontWeight": 600, "color": NAVY,
                                       "fontFamily": FONT, "lineHeight": 1.2})]
    if sub:
        children.append(html.Div(sub, style={"fontSize": 12, "color": MEDIUM_GRAY,
                                              "fontFamily": FONT, "marginTop": 2}))
    return html.Div(children)


def chart_title(insight):
    """L2 action title for a chart — state the INSIGHT, not the metric. Max ~15 words."""
    return html.Div(insight, style={"fontSize": 15, "fontWeight": 600, "color": NAVY,
                                     "fontFamily": FONT, "marginBottom": 6,
                                     "lineHeight": 1.25})


def footnote(text):
    """L3 footnote (10-12px light gray) — source, methodology, refresh stamp."""
    return html.Div(text, style={"fontSize": 11, "color": MEDIUM_GRAY,
                                  "fontFamily": FONT})


# KPI card ------------------------------------------------------------------ #
def kpi_card(label, value_str, *, delta=None, delta_str=None, period=None,
             favorable_when_positive=True, status=None, emphasis=False):
    """A standard KPI card: Value + Label + Comparison + Trend + Period.

    value_str: pre-formatted value (use finance_theme formatters).
    delta: numeric variance used to pick favorability color + arrow (optional).
    delta_str: pre-formatted comparison text, e.g. '7.3% vs target' or '4bps vs prior'.
    period: e.g. 'Q4 2025' or 'MoM'.
    status: override fill — 'on_track' | 'off_track' | 'at_risk' (else neutral white).
    emphasis: larger card for executive viewing.
    """
    fills = {"on_track": LIGHT_GREEN, "off_track": LIGHT_CORAL, "at_risk": LIGHT_GOLD}
    bg = fills.get(status, WHITE)
    val_size = 30 if emphasis else 24
    delta_children = []
    if delta_str is not None:
        color = (variance_color(delta, favorable_when_positive=favorable_when_positive)
                 if delta is not None else TEXT_GRAY)
        arrow = (variance_arrow(delta, favorable_when_positive=favorable_when_positive)
                 if delta is not None else "")
        delta_children.append(
            html.Div(f"{arrow} {delta_str}".strip(),
                     style={"fontSize": 12.5, "fontWeight": 600, "color": color,
                            "fontFamily": FONT, "marginTop": 4}))
    if period:
        delta_children.append(html.Div(period, style={"fontSize": 10.5,
                              "color": MEDIUM_GRAY, "fontFamily": FONT, "marginTop": 2}))
    return html.Div([
        html.Div(value_str, style={"fontSize": val_size, "fontWeight": 700,
                                   "color": NAVY, "fontFamily": FONT, "lineHeight": 1.1}),
        html.Div(label, style={"fontSize": 12, "color": TEXT_GRAY, "fontFamily": FONT,
                               "marginTop": 2}),
        *delta_children,
    ], style={"flex": 1, "minWidth": 150, "padding": "14px 18px", "background": bg,
              "border": f"1px solid {BORDER_GRAY}", "borderRadius": 6})


def kpi_row(cards):
    """Lay KPI cards in an equal-width row with standard gap. Pass 3-5 (exec) or 6-8 (ops)."""
    return html.Div(cards, style={"display": "flex", "gap": GAP_VISUAL})


# Zone shell ---------------------------------------------------------------- #
def _zone(children, *, grow=False):
    style = {"marginBottom": GAP_ZONE}
    if grow:
        style["flex"] = 1
    return html.Div(children, style=style)


def five_zone_page(*, header, kpis, primary, secondary=None, detail=None, footer=None,
                   report_type="executive", primary_width_pct=60):
    """Assemble the five-zone skeleton.

    header: a page_title(...) (and optional refresh/filter line).
    kpis: a kpi_row(...) of cards.
    primary: the main chart component (largest visual; earns left position).
    secondary: optional list/component of supporting charts (right of primary).
    detail: optional table/matrix component (sorted by variance/severity).
    footer: optional footnote(...) (source · methodology · refresh).
    report_type drives canvas width; primary_width_pct splits primary vs secondary.
    """
    w, _h = CANVAS.get(report_type, CANVAS["executive"])
    body_children = [html.Div(primary, style={"flex": primary_width_pct, "minWidth": 0})]
    if secondary is not None:
        sec = secondary if isinstance(secondary, list) else [secondary]
        body_children.append(html.Div(sec, style={"flex": 100 - primary_width_pct,
                              "minWidth": 0, "display": "flex", "flexDirection": "column",
                              "gap": GAP_VISUAL}))
    body = html.Div(body_children, style={"display": "flex", "gap": GAP_VISUAL})

    blocks = [_zone(header), _zone(kpis), _zone(body, grow=True)]
    if detail is not None:
        blocks.append(_zone(detail))
    if footer is not None:
        blocks.append(html.Div(footer, style={"borderTop": f"1px solid {BORDER_GRAY}",
                                               "paddingTop": 8}))
    return html.Div(blocks, style={
        "maxWidth": w, "margin": "0 auto", "padding": MARGIN_OUTER,
        "fontFamily": FONT, "background": WHITE, "color": TEXT_GRAY,
        "display": "flex", "flexDirection": "column", "minHeight": "100vh"})


def header_bar(title, *, refresh=None, period=None, filters=None):
    """Zone 1 header: action title left; refresh date / period / active filters right.
    The standard requires last-refresh visible and active filter context shown."""
    right_bits = []
    if period:
        right_bits.append(f"Period: {period}")
    if refresh:
        right_bits.append(f"As of: {refresh}")
    if filters:
        right_bits.append(f"Filters: {filters}")
    right = html.Div("  |  ".join(right_bits), style={"fontSize": 12, "color": MEDIUM_GRAY,
                     "fontFamily": FONT, "textAlign": "right"}) if right_bits else None
    return html.Div([title, right] if right else [title],
                    style={"display": "flex", "justifyContent": "space-between",
                           "alignItems": "flex-end"})


def back_button(href="/", label="← Back"):
    """Drillthrough requirement (Type 2): back button always top-left, always visible."""
    from dash import dcc
    return dcc.Link(label, href=href, style={
        "display": "inline-block", "padding": "6px 14px", "border": f"1px solid {NAVY}",
        "borderRadius": 6, "color": NAVY, "fontFamily": FONT, "fontWeight": 600,
        "textDecoration": "none", "fontSize": 13})
