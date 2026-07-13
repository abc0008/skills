#!/usr/bin/env python3
"""Build comparative financials across a peer set from the FDIC Financials API.

Reads peer_set.json (from build_peer_set.py), pulls the latest available period
(and optional prior periods) for the target + every peer, computes a consistent
metric set, and writes a wide comparison table (CSV) plus a long tidy CSV for
Power BI and a metadata file. See references/fdic_fields.md for field meanings.

Usage:
    python build_comparison.py --peer-set peer_set.json [--out-dir .]
    python build_comparison.py --peer-set peer_set.json --as-of 20251231
"""

from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FDIC_FINANCIALS = "https://api.fdic.gov/banks/financials"
USER_AGENT = "bank-peer-comparison/1.0"

FIN_FIELDS = [
    "CERT", "REPDTE", "NAME", "ASSET", "LNLSNET", "LNLSGR", "SC", "DEP",
    "DEPUNINS", "DEPINS", "COREDEP", "EQ", "NETINC", "NIM", "NONII", "NONIX",
    "ROA", "ROE", "NIMY", "LNLSDEPR", "NPERFV", "NCLNLSR", "LNATRESR",
    "RBC1AAJ", "IDT1CER", "IDT1RWAJR", "RBCRWAJ", "NUMEMP", "OFFDOM",
    "INTINC", "INTEXP", "ILNDOM", "EINTEXP", "DEPIDOM", "EEFFR",
    # FDIC-computed analytical ratios + bases
    "INTINCY", "INTEXPY", "ERNAST", "ROAPTX", "NONIIAY", "NONIXAY", "ELNATR",
    # tangible-equity components (ROTCE, TCE/TA)
    "EQPP", "INTAN",
    # loan mix
    "LNRE", "LNCI", "LNCON", "LNRERES", "LNRENRES", "LNRECONS", "LNREMULT",
]

# Output metric order for the wide comparison table.
METRICS = [
    # --- Scale ---
    ("assets_$000", "Total assets ($000)"),
    ("net_loans_$000", "Net loans ($000)"),
    ("deposits_$000", "Deposits ($000)"),
    ("equity_$000", "Equity ($000)"),
    ("branches", "Branches"),
    ("employees", "Headcount (FTE)"),
    # --- Growth (YoY) ---
    ("asset_growth_yoy_pct", "Asset growth YoY %"),
    ("loan_growth_yoy_pct", "Loan growth YoY %"),
    ("deposit_growth_yoy_pct", "Deposit growth YoY %"),
    # --- Profitability ---
    ("net_income_ytd_$000", "Net income YTD ($000)"),
    ("roa_pct", "ROA %"),
    ("roa_pretax_pct", "Pre-tax ROA %"),
    ("roe_pct", "ROE %"),
    ("nim_pct", "NIM %"),
    ("earning_asset_yield_pct", "Earning-asset yield %"),
    ("cost_of_funds_pct", "Cost of funding earning assets %"),
    ("loan_yield_pct_approx", "Loan yield % (approx)"),
    ("deposit_cost_pct_approx", "Deposit cost % (approx)"),
    ("efficiency_pct", "Efficiency ratio %"),
    ("ppnr_to_assets_pct", "PPNR / avg assets %"),
    ("nie_to_assets_pct", "Noninterest expense / avg assets %"),
    # --- Revenue mix ---
    ("nir_$000", "Noninterest income YTD ($000)"),
    ("nir_to_total_revenue_pct", "NIR / total revenue %"),
    ("nir_to_assets_pct", "NIR / avg assets %"),
    # --- Balance-sheet mix ---
    ("loans_to_deposits_pct", "Loans / deposits %"),
    ("loans_to_assets_pct", "Loans / assets %"),
    ("securities_to_assets_pct", "Securities / assets %"),
    ("uninsured_deposits_pct", "Uninsured deposits / deposits %"),
    ("commercial_loan_pct", "C&I loans % of gross"),
    ("cre_loan_pct", "CRE loans % of gross (supervisory)"),
    ("cre_to_capital_pct", "CRE loans / total RBC capital %"),
    ("mortgage_loan_pct", "1-4 family mortgage % of gross"),
    # --- Productivity ---
    ("deposits_per_branch_$000", "Deposits per branch ($000)"),
    ("assets_per_employee_$000", "Assets per employee ($000)"),
    # --- Asset quality ---
    ("npa_to_assets_pct", "NPA / assets %"),
    ("nco_to_loans_pct", "Net charge-offs / loans %"),
    ("allowance_to_loans_pct", "Allowance / gross loans %"),
    # --- Capital ---
    ("cet1_pct", "CET1 %"),
    ("tier1_rbc_pct", "Tier 1 RBC %"),
    ("total_rbc_pct", "Total RBC %"),
    ("leverage_pct", "Leverage %"),
    ("equity_to_assets_pct", "Equity / assets %"),
    ("tce_to_ta_pct", "Tangible common equity / tangible assets %"),
    ("rotce_pct", "Return on tangible common equity %"),
]


def fetch(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def num(row: dict[str, Any], key: str) -> float | None:
    raw = row.get(key)
    if raw in (None, ""):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def pct(n: float | None, d: float | None) -> float | None:
    if n is None or d in (None, 0):
        return None
    return round(n / d * 100, 2)


def rnd(v: float | None, digits: int = 2) -> float | None:
    return None if v is None else round(v, digits)


def pull_history(cert: str, limit: int = 24) -> list[dict[str, Any]]:
    params = urllib.parse.urlencode({
        "filters": f"CERT:{cert}",
        "fields": ",".join(FIN_FIELDS),
        "sort_by": "REPDTE", "sort_order": "DESC",
        "limit": str(limit), "format": "json",
    })
    data = fetch(f"{FDIC_FINANCIALS}?{params}").get("data", [])
    return [d["data"] for d in data]


def pick_period(rows: list[dict[str, Any]], as_of: str | None) -> dict[str, Any] | None:
    if not rows:
        return None
    if as_of:
        match = [r for r in rows if r["REPDTE"] == as_of]
        return match[0] if match else None
    return max(rows, key=lambda r: r["REPDTE"])


def prior_year_row(rows: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any] | None:
    """Return the same-quarter prior-year row, for growth and averaging."""
    cur = current["REPDTE"]
    py = f"{int(cur[:4]) - 1}{cur[4:]}"
    for r in rows:
        if r["REPDTE"] == py:
            return r
    return None


def prior_year_loans(rows: list[dict[str, Any]], current: dict[str, Any]) -> float | None:
    """Find the same-quarter prior-year gross loans for averaging."""
    cur = current["REPDTE"]
    py = f"{int(cur[:4]) - 1}{cur[4:]}"
    for r in rows:
        if r["REPDTE"] == py:
            return num(r, "LNLSGR")
    return None


def compute_metrics(rows: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any]:
    assets = num(current, "ASSET")
    gross_loans = num(current, "LNLSGR")
    net_loans = num(current, "LNLSNET")
    deposits = num(current, "DEP")
    nii = num(current, "NIM")        # net interest income $ (YTD)
    nir = num(current, "NONII")
    nonix = num(current, "NONIX")
    total_rev = (nii or 0) + (nir or 0) if (nii is not None or nir is not None) else None

    # Approximate yields/costs. YTD numerators are annualized by quarter so a
    # Q1 figure is comparable to a full-year figure. Still labelled approximate.
    month = current["REPDTE"][4:6]
    annualizer = {"03": 4.0, "06": 2.0, "09": 4.0 / 3.0, "12": 1.0}.get(month, 1.0)

    loan_int = num(current, "ILNDOM")
    py_loans = prior_year_loans(rows, current)
    avg_loans = None
    if gross_loans is not None and py_loans is not None:
        avg_loans = (gross_loans + py_loans) / 2
    elif gross_loans is not None:
        avg_loans = gross_loans
    loan_yield = pct((loan_int * annualizer) if loan_int is not None else None, avg_loans)

    dep_int = num(current, "EINTEXP")
    ib_dep = num(current, "DEPIDOM")
    deposit_cost = pct((dep_int * annualizer) if dep_int is not None else None, ib_dep) \
        if (dep_int is not None and ib_dep) else None

    cre = sum(v for v in (num(current, "LNRECONS"), num(current, "LNREMULT"),
                          num(current, "LNRENRES")) if v is not None) or None

    eff = num(current, "EEFFR")
    if eff is None:
        eff = pct(nonix, total_rev)

    # FDIC-computed analytical ratios (annualized by FDIC; prefer over hand math).
    earning_yield = rnd(num(current, "INTINCY"))
    cost_of_funds = rnd(num(current, "INTEXPY"))
    roa_pretax = rnd(num(current, "ROAPTX"))
    nir_to_assets = rnd(num(current, "NONIIAY"))
    nie_to_assets = rnd(num(current, "NONIXAY"))
    avg_earning = num(current, "ERNAST")

    # Pre-provision net revenue / avg assets. PPNR = NII + NIR - NIE (annualized).
    ppnr_ytd = None
    if nii is not None or nir is not None or nonix is not None:
        ppnr_ytd = (nii or 0) + (nir or 0) - (nonix or 0)
    py_row = prior_year_row(rows, current)
    avg_assets = None
    if assets is not None and py_row is not None and num(py_row, "ASSET") is not None:
        avg_assets = (assets + num(py_row, "ASSET")) / 2
    elif assets is not None:
        avg_assets = assets
    ppnr_to_assets = pct((ppnr_ytd * annualizer) if ppnr_ytd is not None else None, avg_assets)

    # Year-over-year growth from the same quarter prior year (level fields).
    def growth(field: str) -> float | None:
        cur_v = num(current, field)
        prv_v = num(py_row, field) if py_row else None
        if cur_v is None or prv_v in (None, 0):
            return None
        return round((cur_v / prv_v - 1) * 100, 2)

    # CRE concentration vs total risk-based capital (supervisory 300% guideline lens).
    total_rbc_capital = None
    rbc_ratio = num(current, "RBCRWAJ")
    # back into capital $ only if we have risk-weighted assets proxy; otherwise use equity
    cre_to_capital = pct(cre, num(current, "EQ")) if cre is not None else None

    # Tangible common equity = total equity - perpetual preferred - intangibles.
    equity = num(current, "EQ")
    preferred = num(current, "EQPP") or 0
    intangibles = num(current, "INTAN") or 0
    tce = (equity - preferred - intangibles) if equity is not None else None
    tangible_assets = (assets - intangibles) if assets is not None else None
    tce_to_ta = pct(tce, tangible_assets)

    # Return on tangible common equity: annualized net income over average TCE.
    net_income = num(current, "NETINC")
    py_tce = None
    if py_row is not None:
        py_eq = num(py_row, "EQ")
        if py_eq is not None:
            py_tce = py_eq - (num(py_row, "EQPP") or 0) - (num(py_row, "INTAN") or 0)
    avg_tce = None
    if tce is not None and py_tce is not None:
        avg_tce = (tce + py_tce) / 2
    elif tce is not None:
        avg_tce = tce
    rotce = pct((net_income * annualizer) if net_income is not None else None, avg_tce)

    return {
        "cert": str(current.get("CERT")),
        "name": current.get("NAME"),
        "period": current.get("REPDTE"),
        "assets_$000": assets,
        "net_loans_$000": net_loans,
        "deposits_$000": deposits,
        "equity_$000": num(current, "EQ"),
        "branches": int(num(current, "OFFDOM") or 0),
        "employees": int(num(current, "NUMEMP") or 0),
        "asset_growth_yoy_pct": growth("ASSET"),
        "loan_growth_yoy_pct": growth("LNLSGR"),
        "deposit_growth_yoy_pct": growth("DEP"),
        "net_income_ytd_$000": num(current, "NETINC"),
        "roa_pct": rnd(num(current, "ROA")),
        "roa_pretax_pct": roa_pretax,
        "roe_pct": rnd(num(current, "ROE")),
        "nim_pct": rnd(num(current, "NIMY")),
        "earning_asset_yield_pct": earning_yield,
        "cost_of_funds_pct": cost_of_funds,
        "loan_yield_pct_approx": loan_yield,
        "deposit_cost_pct_approx": deposit_cost,
        "efficiency_pct": rnd(eff),
        "ppnr_to_assets_pct": ppnr_to_assets,
        "nie_to_assets_pct": nie_to_assets,
        "nir_$000": nir,
        "nir_to_total_revenue_pct": pct(nir, total_rev),
        "nir_to_assets_pct": nir_to_assets,
        "loans_to_deposits_pct": rnd(num(current, "LNLSDEPR")) or pct(net_loans, deposits),
        "loans_to_assets_pct": pct(net_loans, assets),
        "securities_to_assets_pct": pct(num(current, "SC"), assets),
        "uninsured_deposits_pct": pct(num(current, "DEPUNINS"), deposits),
        "commercial_loan_pct": pct(num(current, "LNCI"), gross_loans),
        "cre_loan_pct": pct(cre, gross_loans),
        "cre_to_capital_pct": cre_to_capital,
        "mortgage_loan_pct": pct(num(current, "LNRERES"), gross_loans),
        "deposits_per_branch_$000": rnd(deposits / num(current, "OFFDOM"))
            if (deposits is not None and num(current, "OFFDOM")) else None,
        "assets_per_employee_$000": rnd(assets / num(current, "NUMEMP"))
            if (assets is not None and num(current, "NUMEMP")) else None,
        "npa_to_assets_pct": rnd(num(current, "NPERFV")),
        "nco_to_loans_pct": rnd(num(current, "NCLNLSR")),
        "allowance_to_loans_pct": rnd(num(current, "LNATRESR")),
        "cet1_pct": rnd(num(current, "IDT1CER")),
        "tier1_rbc_pct": rnd(num(current, "IDT1RWAJR")),
        "total_rbc_pct": rnd(num(current, "RBCRWAJ")),
        "leverage_pct": rnd(num(current, "RBC1AAJ")),
        "equity_to_assets_pct": pct(num(current, "EQ"), assets),
        "tce_to_ta_pct": tce_to_ta,
        "rotce_pct": rotce,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--peer-set", required=True)
    ap.add_argument("--as-of", default=None, help="REPDTE YYYYMMDD; default latest common")
    ap.add_argument("--out-dir", default=".")
    args = ap.parse_args()

    peer_data = json.loads(Path(args.peer_set).read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target = peer_data["target"]
    members = [{"cert": target["cert"], "name": target["name"], "is_target": True}]
    members += [{"cert": p["cert"], "name": p["name"], "is_target": False}
                for p in peer_data["peers"]]

    records: list[dict[str, Any]] = []
    histories: dict[str, list[dict[str, Any]]] = {}
    for m in members:
        rows = pull_history(m["cert"])
        histories[m["cert"]] = rows
        cur = pick_period(rows, args.as_of)
        if cur is None:
            print(f"  WARN: no period for {m['name']} (CERT {m['cert']})")
            continue
        rec = compute_metrics(rows, cur)
        rec["is_target"] = m["is_target"]
        records.append(rec)

    # Wide table: rows = banks, columns = metrics.
    wide_cols = ["cert", "name", "is_target", "period"] + [k for k, _ in METRICS]
    with (out_dir / "peer_comparison_wide.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=wide_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(records)

    # Long/tidy table for Power BI: one row per bank-metric.
    long_rows = []
    for rec in records:
        for key, label in METRICS:
            long_rows.append({
                "cert": rec["cert"], "name": rec["name"],
                "is_target": rec["is_target"], "period": rec["period"],
                "metric_key": key, "metric_label": label, "value": rec.get(key),
            })
    with (out_dir / "peer_comparison_long.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["cert", "name", "is_target", "period",
                                           "metric_key", "metric_label", "value"])
        w.writeheader()
        w.writerows(long_rows)

    # Percentile/rank stats for the target vs peers, per metric.
    stats = []
    target_rec = next((r for r in records if r["is_target"]), None)
    peer_recs = [r for r in records if not r["is_target"]]
    for key, label in METRICS:
        vals = sorted(v for v in (r.get(key) for r in peer_recs) if v is not None)
        if not vals:
            continue
        median = vals[len(vals) // 2]
        tv = target_rec.get(key) if target_rec else None
        rank = None
        if tv is not None:
            below = sum(1 for v in vals if v < tv)
            rank = round(below / len(vals) * 100)
        stats.append({
            "metric_key": key, "metric_label": label,
            "target_value": tv,
            "peer_min": vals[0], "peer_median": median, "peer_max": vals[-1],
            "target_percentile_vs_peers": rank,
        })
    with (out_dir / "peer_comparison_stats.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["metric_key", "metric_label", "target_value",
                                           "peer_min", "peer_median", "peer_max",
                                           "target_percentile_vs_peers"])
        w.writeheader()
        w.writerows(stats)

    meta = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "target": target,
        "as_of": args.as_of or (target_rec["period"] if target_rec else None),
        "n_banks": len(records),
        "source": "FDIC BankFind Financials API (https://api.fdic.gov/banks/financials)",
        "field_reference": "references/fdic_fields.md",
        "caveats": [
            "Loan yield and deposit cost are approximate: YTD interest is annualized by quarter over period-end or 2-point average balances.",
            "CRE % uses the supervisory definition: construction + multifamily + nonfarm nonresidential.",
            "All figures are bank-level FDIC CERT data for cross-bank comparability.",
        ],
    }
    (out_dir / "comparison_metadata.json").write_text(json.dumps(meta, indent=2) + "\n")

    print(f"Built comparison for {len(records)} banks as of "
          f"{meta['as_of']}. Wrote wide, long, stats CSVs and metadata to {out_dir}.")


if __name__ == "__main__":
    main()
