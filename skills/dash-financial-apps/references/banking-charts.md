# Banking Chart Recipes (Pinnacle, open-source)

Recipes for the visuals a bank finance team builds most, styled to the Pinnacle standard
and the IBCS conventions. Assumes `import plotly.graph_objects as go`, `import
plotly.express as px`, and `from finance_theme import (apply_finance_theme, NAVY, TEAL,
LIGHT_BLUE, MEDIUM_GRAY, GREEN, CORAL, GOLD, variance_color)`. Always finish with
`apply_finance_theme(fig, yformat=...)`.

A note on metric direction (favorability): for **expense, efficiency ratio, delinquency,
NCO, cost of funds**, *lower is better* — so a decrease is favorable (green). For revenue,
NII, NIM, deposits, *higher is better*. Pass `favorable_when_positive` accordingly anywhere
you color a variance.

## Table of contents
1. NII / P&L waterfall bridge
2. Rate / Volume / Mix decomposition (the NII bridge math)
3. NIM trend with target reference line
4. NIM / metric by business line (sorted bar)
5. Clustered or stacked columns + line (combo) — and the dual-axis caveat
6. Top & bottom movers (diverging variance bar)
7. Bullet chart (actual vs target vs prior)
8. Composition over time (100% stacked) — deposit/loan mix
9. Banking KPI quick-reference (formulas)

---

## 1. NII / P&L waterfall bridge

The signature "what drove the change" chart. Green increases, coral decreases, navy totals
— matching IBCS. Use `go.Waterfall` (px has none).

```python
fig = go.Figure(go.Waterfall(
    orientation="v",
    measure=["absolute", "relative", "relative", "relative", "total"],
    x=["FY24 NII", "Volume", "Rate", "Mix", "FY25 NII"],
    y=[420.0, 38.5, -22.1, 9.3, None],          # $M; None auto-sums the total
    text=["$420.0M", "+$38.5M", "-$22.1M", "+$9.3M", "$445.7M"],
    textposition="outside",
    connector={"line": {"color": "#D9D9D9"}},
    increasing={"marker": {"color": GREEN}},
    decreasing={"marker": {"color": CORAL}},
    totals={"marker": {"color": NAVY}},
))
fig = apply_finance_theme(fig, yformat="$,.0f", title="Net interest income grew $25.7M as volume gains outpaced rate pressure")
```

`measure`: `"absolute"` sets a starting level, `"relative"` is a step, `"total"` is a
summed checkpoint. The title is an **action title** (the insight), per the layout standard.

---

## 2. Rate / Volume / Mix decomposition (the bridge math)

The bars in a NII bridge come from decomposing the change in interest income/expense into
volume and rate effects. Standard formulas (per portfolio, then sum):

```
volume_effect = (avg_balance_cur - avg_balance_pri) * rate_pri
rate_effect   = (rate_cur - rate_pri) * avg_balance_pri
mix_residual  = total_change - volume_effect - rate_effect   # cross term / mix
```

```python
def rate_volume_bridge(df):  # df has bal_pri, bal_cur, rate_pri, rate_cur per portfolio
    vol = ((df.bal_cur - df.bal_pri) * df.rate_pri).sum()
    rate = ((df.rate_cur - df.rate_pri) * df.bal_pri).sum()
    total = (df.bal_cur * df.rate_cur - df.bal_pri * df.rate_pri).sum()
    return {"Volume": vol, "Rate": rate, "Mix": total - vol - rate}
```

Feed the three effects into the waterfall in §1. Do the heavy aggregation in SQL on
Databricks where possible (see `databricks-data.md`) and decompose on the small result.

---

## 3. NIM trend with target reference line

NIM over time as a line, with the target as a dashed reference and direct end-label (no
legend). Operational dashboards REQUIRE a threshold/target line on every chart.

```python
fig = go.Figure()
fig.add_trace(go.Scatter(x=d.month, y=d.nim, mode="lines+markers", name="NIM",
                         line=dict(color=NAVY, width=2.5)))
fig = apply_finance_theme(fig, yformat=",.2%",
        title="NIM compressed 8bps in Q1 on deposit repricing")
fig.add_hline(y=0.0275, line_dash="dash", line_color=MEDIUM_GRAY,
              annotation_text="Target 2.75%", annotation_position="top left")
fig.add_annotation(x=d.month.iloc[-1], y=d.nim.iloc[-1], text="2.87%",
                   showarrow=False, xshift=24, font=dict(color=NAVY))
```

For basis-point change series, format the axis `",.2%"` or convert to bps and label "bps".

---

## 4. NIM / metric by business line (sorted bar)

"Compare categories" → horizontal bar **sorted by value**, single color (navy), direct
value labels. Never a pie.

```python
d = df.sort_values("nim")                      # ascending so largest sits on top
fig = px.bar(d, x="nim", y="business_line", orientation="h", text="nim")
fig.update_traces(marker_color=NAVY, texttemplate="%{x:.2%}", textposition="outside")
fig = apply_finance_theme(fig, xformat=",.1%",
        title="Commercial leads NIM at 3.4%; Treasury drags at 1.9%")
fig.update_layout(yaxis_title="", showlegend=False)
```

---

## 5. Clustered/stacked columns + line (combo) — and the dual-axis caveat

Banking constantly pairs a **level** (balances, $) with a **rate** (yield/cost/NIM, %), or
clustered actual-vs-budget columns with a cumulative line. These combos are useful, but the
Pinnacle BAN LIST prohibits **dual-axis charts with misleading scales**. Reconcile like
this:

- **Acceptable:** a *level + rate* combo (e.g., deposit balances as columns + cost-of-funds
  as a line) where the two answer different questions, **both axes are labeled with units**,
  the secondary axis is anchored sensibly (not zoomed to exaggerate), and the line uses a
  reserved/neutral color (teal or gray).
- **Not acceptable:** a dual-axis chart comparing *two trends* to imply correlation — use a
  scatter, or index both series to a common base on one axis.

```python
from plotly.subplots import make_subplots
fig = make_subplots(specs=[[{"secondary_y": True}]])
# Clustered actual vs budget (same $ unit, primary axis)
fig.add_trace(go.Bar(x=d.month, y=d.actual, name="Actual", marker_color=NAVY),
              secondary_y=False)
fig.add_trace(go.Bar(x=d.month, y=d.budget, name="Budget", marker_color=LIGHT_BLUE),
              secondary_y=False)
# Rate line on an honest secondary axis (%), neutral color, clearly labeled
fig.add_trace(go.Scatter(x=d.month, y=d.cof, name="Cost of funds", mode="lines+markers",
                         line=dict(color=TEAL, width=2)), secondary_y=True)
fig = apply_finance_theme(fig, title="Deposit growth held while cost of funds plateaued")
fig.update_layout(barmode="group")
fig.update_yaxes(title_text="Balances ($)", tickformat="$,.2s", secondary_y=False)
fig.update_yaxes(title_text="Cost of funds (%)", tickformat=",.2%", secondary_y=True,
                 showgrid=False)   # gridlines on primary only, to reduce noise
```

For a **stacked** columns + line (e.g., deposit mix stacked + total NIM line), use
`barmode="stack"` and keep stack segments to ≤3 colors.

---

## 6. Top & bottom movers (diverging variance bar)

"What moved the most" — a horizontal bar of variances sorted by magnitude, colored by IBCS
favorability. Great for the detail/secondary zone. This replaces eyeballing a big table.

```python
from finance_theme import fmt_millions, fmt_thousands
d = mov.reindex(mov.variance.abs().sort_values().index)       # smallest..largest magnitude
colors = [variance_color(v, favorable_when_positive=True) for v in d.variance]

def signed_label(v):                                          # "+$8.4M" / "−$1.5M"
    mag = fmt_millions(abs(v)) if abs(v) >= 1e6 else fmt_thousands(abs(v))
    return ("\u2212" + mag) if v < 0 else ("+" + mag)
labels = [signed_label(v) for v in d.variance]

fig = go.Figure(go.Bar(x=d.variance, y=d.entity, orientation="h",
                       marker_color=colors, text=labels, textposition="outside",
                       cliponaxis=False))                    # let labels extend past axis
fig.add_vline(x=0, line_color=MEDIUM_GRAY)
fig = apply_finance_theme(fig, xformat="$,.2s",
        title="Commercial RE drove the largest unfavorable swing (-$4.1M)")
fig.update_layout(yaxis_title="", showlegend=False, margin=dict(l=110, r=60))
fig.update_yaxes(automargin=True)                            # don't clip long category names
```

Two robustness notes that matter for any horizontal bar with labels and long category names:
**format the data labels in Python** (build the signed string from the value's sign, not by
inspecting a formatted string — `fmt_millions(-1.5e6)` is `"$-1.5M"`, so prefixing by string
prefix double-signs it) — Python labels render identically everywhere and survive static
PDF/PPTX export; and set `cliponaxis=False` + `yaxes(automargin=True)` with a generous left
margin so outside labels and long entity names are never clipped.

For a true "top 5 / bottom 5", slice the sorted frame: `pd.concat([d.head(5), d.tail(5)])`.
For a cost metric (expense, NCO), pass `favorable_when_positive=False` so reductions read
green.

---

## 7. Bullet chart (actual vs target vs prior)

"Is this metric on target?" → bullet, not gauge (gauges are banned). Build with
`go.Indicator(mode="number+gauge+delta")` in bullet form, or a compact horizontal bar with
a target tick.

```python
fig = go.Figure(go.Indicator(
    mode="number+gauge+delta", value=4.2e6,
    delta={"reference": 3.9e6, "increasing": {"color": GREEN},
           "decreasing": {"color": CORAL}},
    gauge={"shape": "bullet", "axis": {"tickformat": "$,.1s"},
           "threshold": {"line": {"color": NAVY, "width": 2}, "value": 3.9e6},
           "bar": {"color": NAVY}},
    title={"text": "Revenue vs target"},
))
fig.update_layout(height=140, margin=dict(l=120, r=24, t=24, b=24), template=None)
apply_finance_theme(fig)
```

---

## 8. Composition over time (100% stacked) — deposit/loan mix

"Composition breakdown" → 100% stacked columns (or treemap), not pie. Useful for funding
mix (DDA / savings / CDs / borrowings) or loan mix over quarters.

```python
fig = px.bar(d, x="quarter", y="share", color="category",
             color_discrete_sequence=[NAVY, TEAL, LIGHT_BLUE, MEDIUM_GRAY])
fig = apply_finance_theme(fig, yformat=",.0%",
        title="Noninterest-bearing mix slipped 4pts as CDs repriced up")
fig.update_layout(barmode="stack", yaxis_title="% of deposits")
```

Keep stack segments to ≤4 and order them consistently across periods.

---

## 9. Banking KPI quick-reference (formulas)

Get the math right — these feed both KPI cards and chart series:

| Metric | Formula | Favorable |
|--------|---------|-----------|
| Net interest margin (NIM) | Net interest income / avg earning assets (annualized) | higher |
| Efficiency ratio | Noninterest expense / (NII + noninterest income) | **lower** |
| Net charge-off (NCO) rate | Net charge-offs / avg loans (annualized) | **lower** |
| Cost of funds | Interest expense / avg interest-bearing liabilities | **lower** |
| Loan-to-deposit | Total loans / total deposits | context |
| Deposit beta | Δ deposit cost / Δ market rate | context |
| Operating leverage | Revenue growth % − expense growth % | higher |
| ROA / ROE | Net income / avg assets (or avg equity) | higher |
| Coverage ratio (ALLL) | Allowance / total loans | context |

Express NIM/NCO/cost-of-funds in **bps** when showing small changes (use `fmt_bps` /
axis `",.2%"`). For the "lower is better" metrics, always set
`favorable_when_positive=False` so the variance colors and arrows read correctly.
