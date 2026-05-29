# Pinnacle Layout Standards (for Dash)

The Pinnacle Finance Analytics Power BI Layout Standards, translated for open-source Dash.
Follow these for any financial dashboard — they make output read as a Pinnacle deliverable
and pass the CFO's 1-3-10 test. The `pinnacle_layout.py` module implements most of this;
this file explains the rules and when to apply each report type.

## Table of contents
1. Universal principles (apply to every report)
2. The five-zone skeleton
3. KPI card specification
4. The four report types (canvas, zones, rules)
5. Reading patterns (Z vs F)
6. Chart selection matrix + BAN LIST
7. Building a zoned page with pinnacle_layout.py

---

## 1. Universal principles

- **Inverted pyramid.** Answer first, evidence below, detail last. The **most important KPI
  goes top-left** — that's where the eye lands. **Never put a logo in the top-left corner.**
- **Action titles, not labels.** Every chart's title states the *insight*: "Premium drove
  67% of Q4 growth", not "Revenue by Segment". Max ~15 words. Use `chart_title(...)`.
- **Three text levels only**, one font (Arial), **left-align always**:
  L1 page/action title 20-24px semibold · L2 chart title 14-16px · L3 footnote 10-12px.
  More than 3 font sizes in a report is a defect.
- **8px spacing grid.** 16-20px between visuals · 24-32px between zones · 32-48px outer
  margins. Every position a multiple of 8. (`GAP_VISUAL`, `GAP_ZONE`, `MARGIN_OUTER`.)
- **Every KPI carries context** — value + comparison + trend + period. A bare number with
  no comparison is not allowed.
- **Show state.** Last-refresh timestamp visible in the header; active filter context
  always visible (don't hide filter state — it destroys stakeholder trust).
- **No-scroll.** Each page/view is designed to fit one screen; don't make the reader scroll.

---

## 2. The five-zone skeleton

Every report type is a variation on these zones (top to bottom), with the body split so the
**primary chart earns the left ~60%**:

| Zone | Contains | Height |
|------|----------|--------|
| 1 Header | Action title · last-refresh · active filters | 5-8% |
| 2 KPI summary | 3-5 cards (exec) / 6-8 (ops), identical size | 12-18% |
| 3 Primary chart | Main trend/driver, largest visual, left ~60% | 40-50% |
| 4 Secondary | 1-2 supporting charts, right of primary | remaining |
| 5 Detail | Tables/matrices, sorted by variance/severity | 20-25% |
| Footer | Source · methodology · navigation | 3-5% |

Detail tables are sorted by **variance or severity, never alphabetically** — the reader
needs the largest unfavorable items first.

---

## 3. KPI card specification

A KPI card MUST show all five: **Value + Label + Comparison (Δ vs target/prior) + Trend
(arrow) + Period.** Use `kpi_card(...)`, which colors the comparison by IBCS favorability
(green favorable / coral unfavorable / gold at-risk) and draws the trend arrow.

```python
kpi_card("Net Interest Margin", fmt_pct(0.0287, already_percent=False),
         delta=-0.0008, delta_str="8bps vs Q4", period="Q1 2026",
         favorable_when_positive=True, status="at_risk")
```

Executive cards are larger (`emphasis=True`, 20-25% canvas width). Operational dashboards
use 6-8 compact cards with alert fills (`status="on_track"|"off_track"|"at_risk"`).

---

## 4. The four report types

Choose the type from the audience and use, then use the matching canvas + zone split. The
`CANVAS` and `ZONES` dicts and `five_zone_page(report_type=...)` encode these.

**Type 1 — Ad Hoc Single-Page.** 1600×900, **F-pattern**, max 6-8 visuals, export-safe
(must work as a static PDF/PPTX — no hover-only content), one answer per page. Zones:
header 6% · KPI 14% · primary 50% · supporting 25% · footer 5%. 1-2 slicers inline near
the chart they affect. Action title frames the specific question answered.

**Type 2 — Multi-Page Drillthrough.** 1600×900, **F-pattern**, **max 7 pages**. Overview →
category → drillthrough. Drillthrough pages: **back button always top-left** (`back_button()`),
entity identifiers in the KPI card row, one entity type per page, hidden from the tab bar,
carry filter context. In Dash, implement with Dash Pages (`use_pages=True`) + query params
or `dcc.Store` to carry context; see `app-structure.md` §5.

**Type 3 — Executive Summary.** 1600×900, **Z-pattern**, max 5-7 visuals, **zero scroll**,
no interactivity dependency (design for tablet/print/projection). Larger KPI cards
(18% / `emphasis=True`). Max 2 slicers (period + business unit). Conditional formatting
on-track/off-track/at-risk. Apply the **1-3-10 test**: org health readable in 1s (fix KPI
zone if not), key driver obvious in 3s (fix action titles/placement), next action clear in
10s (add a recommended-action call-out).

**Type 4 — Operational / Monitoring.** **1920×1080** (wall/monitor), **Z-pattern**, 6-8
compact KPI/alert cards, **refresh timestamp prominent** (+ a "data age" indicator if stale),
**every chart has a threshold/target line**, shorter time windows (daily/hourly, never
monthly), exception table sorted by severity, collapsible filter sidebar + a clear "reset
filters" control.

---

## 5. Reading patterns

- **Z-pattern** (Executive & Operational): few visuals, quick status scan. Place the main
  story top-left, secondary top-right, detail along the bottom.
- **F-pattern** (Ad Hoc & Drillthrough): content-heavy, multi-row. Reader scans across the
  top then down the left; stack rows of charts with the key one first.

---

## 6. Chart selection matrix + BAN LIST

Pick the chart from the analytical question:

| Question | Use | Avoid |
|----------|-----|-------|
| Trend over time | Line chart | Area chart for volatile data |
| What drove the change? (P&L/NII bridge) | **Waterfall / variance bridge** | Stacked bar (hides drivers) |
| Compare categories | Horizontal bar, **sorted by value** | Pie chart |
| Composition breakdown | 100% stacked bar · treemap | Pie with >5 segments |
| Is this metric on target? | Bullet chart · KPI card + cond. format | Gauge chart |
| Two-variable relationship | Scatter plot | Dual-axis line chart |
| Exceptions / outliers | Table + conditional formatting | Radar / spider |

**BAN LIST — never use in a Pinnacle report:** 3D charts of any kind · pie charts with >5
segments · **dual-axis charts** (misleading scales) · gauge charts (use a KPI card or
bullet instead). See `banking-charts.md` for the bar+line combo nuance: a *level + rate*
combo with honest, clearly-labeled axes is acceptable; a dual-axis comparison of two
*trends* is not — use a scatter or index both to a base.

**Color discipline:** max 3 colors per chart, 5-7 across the whole report; direct labels
replace legends wherever possible; IBCS fills — solid = actual, outline/hollow = plan/budget,
hatched = forecast; green/coral reserved for variance favorability only.

---

## 7. Building a zoned page with pinnacle_layout.py

```python
from pinnacle_layout import (five_zone_page, header_bar, page_title, chart_title,
                             footnote, kpi_card, kpi_row)
from finance_theme import fmt_billions, fmt_pct, apply_finance_theme

header = header_bar(page_title("Expense growth tracking below revenue — positive operating leverage"),
                    refresh="Mar 1, 2026", period="Q1 2026", filters="All Business Units")

kpis = kpi_row([
    kpi_card("Net Revenue", fmt_billions(1.24e9), delta=0.042, delta_str="4.2% vs Plan",
             period="Q1 2026", emphasis=True, status="on_track"),
    kpi_card("NIM", fmt_pct(0.0287, already_percent=False), delta=-0.0008,
             delta_str="8bps vs Q4", period="Q1 2026", emphasis=True, status="at_risk"),
    kpi_card("NCO Rate", fmt_pct(0.0042, already_percent=False), delta=-0.0003,
             delta_str="improving", period="Q1 2026", favorable_when_positive=False,
             emphasis=True, status="on_track"),
])

layout = five_zone_page(
    report_type="executive",
    header=header, kpis=kpis,
    primary=html.Div([chart_title("Revenue beat plan by 4.2% through Q1"),
                      dcc.Graph(figure=apply_finance_theme(primary_fig))]),
    secondary=html.Div([chart_title("Expense up 3.1% vs revenue up 4.2%"),
                        dcc.Graph(figure=apply_finance_theme(secondary_fig))]),
    detail=detail_grid,                       # AG Grid sorted by variance
    footer=footnote("Source: Finance Analytics / Hyperion · Confidential — Board Use Only"),
)
```

This produces a 1600-wide, Z-pattern executive page with the most-important KPI top-left,
action titles on every chart, the 8px spacing system, and Pinnacle brand throughout — no
logo in the top-left, no banned chart types.
