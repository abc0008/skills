#!/usr/bin/env python3
"""Render a narrative markdown peer-comparison report from the comparison CSVs.

Produces a CFO-readable report: executive readout, peer set table, headline
comparison, where-the-target-stands callouts, and sources. Numbers come from the
already-built CSVs; this script only formats and narrates.

Usage:
    python build_report.py --in-dir . --out peer_comparison_report.md
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HEADLINE_METRICS = [
    ("assets_$000", "Assets", "bn"), ("net_loans_$000", "Net loans", "bn"),
    ("deposits_$000", "Deposits", "bn"), ("branches", "Branches", "int"),
    ("employees", "Headcount", "int"),
    ("asset_growth_yoy_pct", "Asset growth YoY", "pct"),
    ("deposit_growth_yoy_pct", "Deposit growth YoY", "pct"),
    ("roa_pct", "ROA", "pct"), ("roe_pct", "ROE", "pct"), ("nim_pct", "NIM", "pct"),
    ("earning_asset_yield_pct", "Earning-asset yield", "pct"),
    ("cost_of_funds_pct", "Cost of funds", "pct"),
    ("efficiency_pct", "Efficiency", "pct"),
    ("ppnr_to_assets_pct", "PPNR/assets", "pct"),
    ("nir_to_total_revenue_pct", "NIR/Revenue", "pct"),
    ("loans_to_deposits_pct", "Loans/Deposits", "pct"),
    ("commercial_loan_pct", "C&I %", "pct"), ("cre_loan_pct", "CRE %", "pct"),
    ("mortgage_loan_pct", "Mortgage %", "pct"), ("cet1_pct", "CET1", "pct"),
    ("rotce_pct", "ROTCE", "pct"), ("tce_to_ta_pct", "TCE/TA", "pct"),
]


def ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def fnum(v: str) -> float | None:
    if v in ("", None):
        return None
    try:
        return float(v)
    except ValueError:
        return None


def fmt(v: float | None, kind: str) -> str:
    if v is None:
        return "n/a"
    if kind == "bn":
        return f"${v/1_000_000:,.1f}B"
    if kind == "pct":
        return f"{v:,.2f}%"
    if kind == "int":
        return f"{int(v):,}"
    return f"{v:,.0f}"


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |",
           "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", default=".")
    ap.add_argument("--out", default="peer_comparison_report.md")
    args = ap.parse_args()

    in_dir = Path(args.in_dir)
    wide = read_csv(in_dir / "peer_comparison_wide.csv")
    stats = read_csv(in_dir / "peer_comparison_stats.csv")
    meta = json.loads((in_dir / "comparison_metadata.json").read_text())
    peer_set = json.loads((in_dir / "peer_set.json").read_text()) if (in_dir / "peer_set.json").exists() else None

    target = next((r for r in wide if r.get("is_target") == "True"), None)
    peers = [r for r in wide if r.get("is_target") != "True"]
    tgt_name = (target or {}).get("name", "Target bank")
    as_of = meta.get("as_of")

    stat_by_key = {s["metric_key"]: s for s in stats}

    def callout(key: str, kind: str = "pct") -> str:
        s = stat_by_key.get(key)
        if not s:
            return "n/a"
        tv = fnum(s["target_value"])
        med = fnum(s["peer_median"])
        if tv is None or med is None:
            return "n/a"
        unit = "%" if kind == "pct" else ""
        pctl = s["target_percentile_vs_peers"]
        pctl_str = ordinal(int(pctl)) if pctl not in ("", None) else "n/a"
        return f"{tv:,.2f}{unit} vs peer median {med:,.2f}{unit} ({pctl_str} pctile)"

    # Peer set table.
    peer_rows = []
    if peer_set:
        for p in peer_set.get("peers", []):
            peer_rows.append([
                p["name"], p["cert"], p["state"],
                fmt(p["assets_$000"], "bn"), p["specialization"],
                f"{p['proximity_score']:.2f}", p["selection_reason"],
            ])

    # Headline comparison table: metric | target | peer median | percentile.
    headline_rows = []
    for key, label, kind in HEADLINE_METRICS:
        s = stat_by_key.get(key)
        if not s:
            continue
        headline_rows.append([
            label, fmt(fnum(s["target_value"]), kind),
            fmt(fnum(s["peer_median"]), kind), fmt(fnum(s["peer_min"]), kind),
            fmt(fnum(s["peer_max"]), kind), f"{s['target_percentile_vs_peers']}",
        ])

    built = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    dropped = (peer_set or {}).get("dropped_outliers", []) if peer_set else []
    if dropped:
        items = "; ".join(f"{o['name']} ({o['dropped_reason']})" for o in dropped)
        outlier_note = ("\n_Atypical banks screened out of the default set "
                        f"(sweep/trust/custody profile): {items}. "
                        "Force any back with `--include-cert` if you want them in._\n")
    else:
        outlier_note = ""
    lines = f"""# {tgt_name} — Peer Comparison

Built: {built} · As-of period: {as_of} · Basis: bank-level FDIC Call Report data

## Executive Readout

This compares **{tgt_name}** against a {len(peers)}-bank peer set selected on
size, business model, and region. Where the target sits relative to peers on the
metrics that matter most:

- Profitability: ROA {callout('roa_pct')}; ROE {callout('roe_pct')}; ROTCE {callout('rotce_pct')}; PPNR/assets {callout('ppnr_to_assets_pct')}.
- Spread: NIM {callout('nim_pct')}; earning-asset yield {callout('earning_asset_yield_pct')}; cost of funds {callout('cost_of_funds_pct')}.
- Efficiency: {callout('efficiency_pct')}; NIE/assets {callout('nie_to_assets_pct')}.
- Fee mix: NIR / total revenue {callout('nir_to_total_revenue_pct')}.
- Growth (YoY): assets {callout('asset_growth_yoy_pct')}; loans {callout('loan_growth_yoy_pct')}; deposits {callout('deposit_growth_yoy_pct')}.
- Balance-sheet mix: C&I {callout('commercial_loan_pct')}; CRE {callout('cre_loan_pct')}; 1-4 family {callout('mortgage_loan_pct')}.
- Capital: CET1 {callout('cet1_pct')}; total RBC {callout('total_rbc_pct')}; TCE/TA {callout('tce_to_ta_pct')}.

(Percentile = share of peers the target exceeds; higher is not always "better" —
read each metric in context, e.g. efficiency ratio, cost of funds, NIE/assets,
and charge-offs are better when lower.)
{outlier_note}

## Peer Set

{md_table(["Bank", "CERT", "State", "Assets", "Specialization", "Proximity", "Why"], peer_rows) if peer_rows else "_Peer set detail unavailable (peer_set.json not found)._"}

Peers are ranked by a proximity score combining log-asset distance, Fed-district
region distance, and business-model distance (lower = closer).

## Headline Comparison

{md_table(["Metric", tgt_name, "Peer median", "Peer min", "Peer max", "Pctile"], headline_rows)}

## Reading The Comparison

**Profitability and efficiency.** The clearest signal in a peer comparison is
usually the profitability triad — ROA, ROE, and the efficiency ratio. A target
below peer-median ROA with an above-median efficiency ratio is carrying an
operating-leverage gap, not a revenue-rate problem. Pair this with NIM and the
fee-income share to see whether the gap is spread-driven or cost-driven.

**Balance-sheet mix.** C&I, CRE, and 1-4 family mortgage shares show how the
target's lending model differs from peers. A high mortgage share with low CRE
share is a different risk and revenue profile than a CRE-concentrated peer, even
at the same asset size.

**Funding and capital.** Loans/deposits, uninsured-deposit share, and the CET1 /
total-RBC stack show funding pressure and loss-absorption capacity relative to
peers. These are the lines a regulator or board benchmarks first.

## Methodology & Caveats

- Peer selection: asset band + business-model gate (FDIC `SPECGRP` / `BKCLASS`),
  Fed district and region as grouping and tie-break, proximity score for final rank.
- Reporting basis: bank-level FDIC BankFind Financials (Call Report-derived) for
  every member, so all banks tie to the same ruler.
"""
    for c in meta.get("caveats", []):
        lines += f"- {c}\n"

    lines += f"""
## Sources

- FDIC BankFind Institutions API: https://api.fdic.gov/banks/institutions
- FDIC BankFind Financials API: https://api.fdic.gov/banks/financials
- FDIC field dictionary: https://api.fdic.gov/banks/docs
- FFIEC/NIC (holdco FR Y-9C context): https://www.ffiec.gov/npw
- FR Y-9C reporting form: https://www.federalreserve.gov/apps/reportingforms/Report/Index/FR_Y-9C
"""

    Path(args.out).write_text(lines)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
