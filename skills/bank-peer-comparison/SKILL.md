---
name: bank-peer-comparison
description: >-
  Build a defensible peer set (~10-12 banks) for a target U.S. bank from
  authoritative regulatory data, then produce a comparative financial analysis
  across the group. Use this whenever the user wants to benchmark a bank against
  peers, build a peer group, compare a bank to "similar banks", or analyze
  competitive position on metrics like assets, loans, deposits, branches,
  headcount, NIM, loan yield, deposit cost, efficiency, ROA/ROE, NIR, NIR/revenue,
  C&I %, CRE %, mortgage %, capital ratios, or asset quality. Trigger on phrases
  like "peer group", "peer comparison", "peer set", "benchmark this bank",
  "comparable banks", "how does [bank] stack up", "competitive analysis of a
  bank", or any request to compare a bank to others using Call Report / FDIC /
  FR Y-9C / FFIEC data — even if the user only names one bank. Prefer regulatory
  (FDIC/Call Report) sources over SEC filings because the rules are stricter and
  the data is consistent across all banks.
---

# Bank Peer Comparison

Build a comparable peer set for a target U.S. bank, then assemble a
regulatory-sourced comparative financial analysis across the group. The output
is the kind of benchmark a bank CFO, board, or examiner would accept: same
ruler for every bank, defensible peer selection, sourced metrics.

## When to use

Use this whenever the goal is to benchmark a bank against similar banks — even
when the user names only the target. Typical asks: "build a peer group for
[bank]", "how does [bank] compare to peers on efficiency and NIM", "who are
[bank]'s comparable banks and how do their loan mixes differ", "benchmark our
capital and asset quality against peers".

## Source priority (regulatory first)

Lead with regulatory data because the reporting rules are stricter and uniform
across banks, which is what makes a comparison fair:

1. **FDIC BankFind Suite APIs** (default, bank-level) — institutions endpoint for
   screening attributes, financials endpoint for the metric pull. This is the
   primary engine and needs no key.
2. **Public Call Report fields** — exposed through the FDIC financials API; the
   field meanings are in `references/fdic_fields.md`.
3. **FR Y-9C / FFIEC-NIC / BHCPR** (holding-company layer) — use only as a
   labeled overlay when the user wants the holdco view; never mix it into the
   bank-level comparison table. Note the `RSSDHCR`/`NAMEHCR` and point to
   FFIEC/NIC for FR Y-9C. The **BHCPR** (Bank Holding Company Performance Report,
   https://www.ffiec.gov/npw/FinancialReport/BHCPRReports) is the Fed's holdco
   analog of the UBPR — it publishes regulator-defined peer groups and peer
   averages and is a useful methodology cross-check, but it is PDF/peer-group
   output, not an API.

Avoid SEC filings as the comparison basis. They are fine for narrative color but
are not uniform across the peer set.

## Workflow

The four scripts in `scripts/` are the engine. Run them in order; each writes
files the next one reads. Default working dir is the output folder.

### Step 1 — Resolve the target and confirm scope

Identify the target by name or FDIC CERT. If the user gave a name, the script
resolves the CERT. Before the heavy pull, confirm with the user: peer count
(default 11), whether they want to supply or veto any peers, and the as-of
period (default = latest available). If the user already gave enough detail,
proceed without re-asking.

### Step 2 — Build the peer set

```bash
python scripts/build_peer_set.py --target-cert <CERT> --count 11 --out-dir <dir>
# or by name:
python scripts/build_peer_set.py --target-name "Arvest Bank" --count 11 --out-dir <dir>
# honor user-supplied or vetoed peers:
python scripts/build_peer_set.py --target-cert <CERT> \
    --include-cert 110 5510 --exclude-cert 33497 --out-dir <dir>
```

Selection blends **asset band + business model** (a hard gate on FDIC
specialization and charter class) with **Fed district / region** as grouping and
tie-break, ranking the survivors by a proximity score. It then applies an
**automatic outlier screen** that drops deposit-sweep / trust / custody banks
(which carry a commercial code but distort the comparison) while keeping genuine
lean commercial banks. The methodology is in `references/peer_selection.md`.
This writes `peer_set.csv` and `peer_set.json` (the latter includes
`dropped_outliers`).

**Always show the peer set to the user and let them adjust before Step 3.** The
auto-screen catches the obvious sweep/trust outliers, but borderline cases (a
brokerage-affiliated bank that does real lending, a holdco-entity name collision)
still warrant a human glance. Print the selected list AND the dropped-outlier
list, flag anything that looks off, and re-run with `--include-cert` /
`--exclude-cert` if they want changes. Forced peers bypass the outlier screen, so
a user can always pull a flagged bank back in.

### Step 3 — Build the comparative financials

```bash
python scripts/build_comparison.py --peer-set <dir>/peer_set.json --out-dir <dir>
# pin a specific period:
python scripts/build_comparison.py --peer-set <dir>/peer_set.json --as-of 20251231 --out-dir <dir>
```

Pulls the target + every peer from the FDIC financials API and computes a
consistent ~42-metric set across six families: **scale** (assets, loans,
deposits, equity, branches, headcount), **growth** (YoY assets/loans/deposits),
**profitability** (ROA, pre-tax ROA, ROE, NIM, earning-asset yield, cost of
funds, loan yield, deposit cost, efficiency ratio, PPNR/assets, NIE/assets),
**revenue mix** (NIR, NIR/total revenue, NIR/assets), **balance-sheet mix**
(loans/deposits, loans/assets, securities/assets, uninsured %, C&I %, CRE %,
CRE/capital, mortgage %, deposits/branch, assets/employee), **asset quality**
(NPA, NCO, allowance), and **capital** (CET1, Tier 1 RBC, total RBC, leverage,
equity/assets). FDIC-computed annualized ratios are preferred over hand math.
Writes:
- `peer_comparison_wide.csv` — banks × metrics (the main table)
- `peer_comparison_long.csv` — tidy long form for Power BI / DAX
- `peer_comparison_stats.csv` — target vs peer min/median/max + percentile
- `comparison_metadata.json` — as-of, source, caveats

### Step 4 — Render deliverables

Default to producing all three; skip any the user doesn't want.

```bash
# Formatted Excel workbook (Summary, Comparison, Stats, Sources; target highlighted)
python scripts/build_workbook.py --in-dir <dir> --out <dir>/peer_comparison.xlsx
# MANDATORY after building: recalc to guarantee zero formula errors
python <xlsx-skill>/scripts/recalc.py <dir>/peer_comparison.xlsx

# Narrative markdown report (executive readout, peer table, headline comparison)
python scripts/build_report.py --in-dir <dir> --out <dir>/peer_comparison_report.md
```

The flat `peer_comparison_long.csv` is already Power BI-ready (one row per
bank-metric with `is_target` flag) — point the user to it for their own
dashboards. The `xlsx` public skill's `recalc.py` is the recalculation tool;
locate it under `/mnt/skills/public/xlsx/scripts/recalc.py`.

### Step 5 — Present and interpret

Share the files and give a short, honest read of where the target stands.
Percentiles describe position, not virtue — call out that some metrics (efficiency
ratio, charge-offs, deposit cost) are better when lower. Tie the story together:
is a profitability gap operating-leverage-driven (high efficiency ratio) or
spread-driven (low NIM)? Is the balance-sheet mix retail/mortgage-heavy or
CRE-concentrated versus peers?

## Metric definitions and field map

The exact FDIC field for every metric, the dollar-unit convention ($000), the
ratio fields to prefer over hand math, and the loan/deposit/NIR mix fields are in
`references/fdic_fields.md`. Read it before modifying the metric set or
explaining a number's basis. Key gotchas: `NIM` is net-interest-income **dollars**
(margin % is `NIMY`); CRE uses the supervisory definition
(construction + multifamily + nonfarm nonresidential); loan yield and deposit
cost are **approximate** (YTD interest annualized by quarter) and must be
labeled as such.

## Customization

- **Different peer count**: `--count 10` through `--count 12` (or beyond).
- **Tighter/looser size band**: `--band-low` / `--band-high` (defaults 0.5 / 2.0
  of target assets).
- **User-driven peer set**: `--include-cert` forces members; the screen fills
  remaining slots. `--exclude-cert` drops members.
- **Trend, not just snapshot**: `build_comparison.py` pulls history; extend it to
  emit multiple periods if the user wants peer trends over time.
- **Add a metric**: add the FDIC field to `FIN_FIELDS` and a `METRICS` entry in
  `build_comparison.py` (and mirror in `build_workbook.py` / `build_report.py`).

## Output structure

```
<output-dir>/
├── peer_set.csv / peer_set.json                  # the selected group + why
├── peer_comparison_wide.csv                      # banks × metrics
├── peer_comparison_long.csv                      # tidy, Power BI-ready
├── peer_comparison_stats.csv                     # target vs peer distribution
├── comparison_metadata.json                      # as-of, source, caveats
├── peer_comparison.xlsx                          # formatted workbook
└── peer_comparison_report.md                     # narrative report
```
