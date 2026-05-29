# Charting Fundamentals + Pinnacle Styling

How to format and style any Plotly chart to the Pinnacle standard. Banking-specific
recipes (NII bridge, rate/volume, NIM, movers, bullet, mix) live in `banking-charts.md` —
this file covers the conventions that apply to *every* chart plus the general types. All
examples assume `from finance_theme import (apply_finance_theme, NAVY, TEAL, LIGHT_BLUE,
MEDIUM_GRAY, GREEN, CORAL, GOLD, variance_color)` and standard `px`/`go` imports, and end
with `apply_finance_theme(fig, yformat=...)`.

## Table of contents
1. Number & axis formatting (d3)
2. Pinnacle color & fill discipline (IBCS)
3. Action titles (not labels)
4. Trend line / actual-vs-prior
5. Grouped & stacked bars
6. KPI indicators
7. Small multiples
8. Hover, labels, reference lines
9. The BAN LIST + common mistakes

---

## 1. Number & axis formatting

Axes and hovers use **d3 format strings** (not Python specs). Set via `tickformat` and
`hovertemplate`. Keep data numeric; format at display time so sorting/aggregation still work.

| Want | d3 string | Renders |
|------|-----------|---------|
| Whole dollars | `"$,.0f"` | `$1,234,568` |
| Abbreviated $ | `"$,.2s"` | `$1.2M` |
| Percent from fraction | `",.1%"` | `12.3%` (×100) |
| Plain thousands | `",.0f"` | `1,234,568` |

```python
fig = px.line(df, x="month", y="nii")
fig = apply_finance_theme(fig, yformat="$,.0f")
fig.update_traces(hovertemplate="%{x|%b %Y}<br>NII: %{y:$,.0f}<extra></extra>")
```

---

## 2. Pinnacle color & fill discipline (IBCS)

The template's `colorway` is Navy → Teal → Light Blue → Darker Blue → Gold → Gray.
**Green and Coral are excluded from the general sequence — they are reserved for variance
favorability only.** Rules:

- **Max 3 colors per chart**, 5-7 across a whole report.
- **IBCS fills:** solid = actual, outline/hollow = plan/budget, hatched = forecast.
- **Variance color:** favorable = Green `#70AD47`, unfavorable = Coral `#ED7D31`, at-risk =
  Gold `#FFC000`. Use `variance_color(value, favorable_when_positive=...)`. Never use
  green/coral for ordinary category coloring — it destroys the variance signal.
- **Direct labels replace legends** wherever possible (annotate the last/biggest point).

```python
# Outline a budget series (plan) vs solid actual (IBCS fills):
fig.add_trace(go.Bar(x=d.month, y=d.budget, name="Budget", marker=dict(
    color="rgba(0,0,0,0)", line=dict(color=NAVY, width=1.5))))   # hollow = plan
```

---

## 3. Action titles (not labels)

Every chart title states the **insight**, max ~15 words: "Premium drove 67% of Q4 growth",
not "Revenue by Segment". Pass it via `apply_finance_theme(fig, title=...)` or
`chart_title(...)` from `pinnacle_layout`. This is a hard Pinnacle rule and the single
biggest driver of an executive read.

---

## 4. Trend line / actual-vs-prior

Current solid navy, prior muted gray dashed; direct end-labels beat a legend.

```python
fig = go.Figure()
fig.add_trace(go.Scatter(x=cur.month, y=cur.value, name="2026", mode="lines+markers",
                         line=dict(color=NAVY, width=2.5)))
fig.add_trace(go.Scatter(x=pri.month, y=pri.value, name="2025", mode="lines",
                         line=dict(color=MEDIUM_GRAY, width=1.5, dash="dash")))
fig = apply_finance_theme(fig, yformat="$,.0f", title="Net interest income up 6% YoY")
```

---

## 5. Grouped & stacked bars

```python
# Actual vs Budget, grouped (navy actual, light-blue budget)
fig = px.bar(df, x="month", y="amount", color="scenario", barmode="group",
             color_discrete_map={"Actual": NAVY, "Budget": LIGHT_BLUE})
fig = apply_finance_theme(fig, yformat="$,.0f")

# Composition, stacked (≤3-4 segments, consistent order)
fig = px.bar(df, x="quarter", y="revenue", color="product_line", barmode="stack",
             color_discrete_sequence=[NAVY, TEAL, LIGHT_BLUE, MEDIUM_GRAY])
fig = apply_finance_theme(fig, yformat="$,.2s")
```

For category comparison use a **horizontal bar sorted by value** (never a pie). See
`banking-charts.md` §4.

---

## 6. KPI indicators

Prefer the styled `kpi_card(...)` from `pinnacle_layout` (Value + Label + Comparison + Trend
+ Period, IBCS coloring). When you want a self-contained figure instead:

```python
fig = go.Figure(go.Indicator(
    mode="number+delta", value=46.7e6,
    number={"prefix": "$", "valueformat": ",.0f"},
    delta={"reference": 42.0e6, "relative": True, "valueformat": ".1%",
           "increasing": {"color": GREEN}, "decreasing": {"color": CORAL}},
    title={"text": "Net interest income"}))
fig.update_layout(height=170, margin=dict(l=20, r=20, t=40, b=10), template="pinnacle")
```

For "on target?" use a **bullet chart** (`banking-charts.md` §7), never a gauge.

---

## 7. Small multiples

Compare a metric across many segments without a rainbow of colors.

```python
fig = px.line(df, x="month", y="value", facet_col="region", facet_col_wrap=3,
              color_discrete_sequence=[NAVY])
fig = apply_finance_theme(fig, yformat="$,.2s")
fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
```

---

## 8. Hover, labels, reference lines

- **Direct labels** over legends for few series: `fig.add_annotation(x=last_x, y=last_y,
  text="2026", showarrow=False, xshift=22, font=dict(color=NAVY))`.
- **Custom hover**: `hovertemplate="%{x}<br>%{y:$,.0f}<extra></extra>"`.
- **Targets/thresholds** (required on operational charts): `fig.add_hline(y=target,
  line_dash="dash", line_color=MEDIUM_GRAY, annotation_text="Target")`.

---

## 9. The BAN LIST + common mistakes

**Never use** (Pinnacle ban list): 3D charts · pie charts with >5 segments · dual-axis
charts with misleading scales · gauge charts. See `banking-charts.md` §5 for the
acceptable *level + rate* bar+line combo nuance.

Common mistakes:
- **Pre-formatting numbers into strings** — breaks sorting/axes. Keep numeric; format with
  `tickformat`.
- **Green/coral for categories** — reserved for variance favorability only.
- **Metric labels instead of action titles** — "Revenue by Segment" says nothing.
- **More than 3 colors** on one chart, or legends where direct labels would be clearer.
- **DDK / `ddk.Graph`** — Enterprise-only; use `dcc.Graph(figure=fig)`.
- **Percent confusion** — `",.1%"` multiplies by 100 (feed `0.123`). If data is already
  `12.3`, use `",.1f"` and add `%`.
