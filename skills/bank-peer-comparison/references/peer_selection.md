# Peer Selection Methodology

This skill builds a defensible peer set of ~10-12 banks for a target institution.
The goal is comparability: peers a CFO, board, or regulator would accept as a fair
benchmark group. Selection blends **size**, **business model**, and **region**, with
**proximity breaking near ties**.

## Selection signal stack (in priority order)

1. **Business model — hard gate.** Peers must share the target's broad model.
   Screen on `SPECGRP` (specialization, usually `4` commercial lending or `9`
   large diversified) and `BKCLASS` (keep commercial charters `N, SM, NM, SB`;
   drop trust/custody, industrial, and pure thrifts unless the target is one).
   A same-size bank with a different specialization is a bad peer — this gate
   prevents the "Deutsche Bank Trust shows up next to a regional commercial bank"
   failure.

2. **Asset band — primary size screen.** Default band is roughly **0.5x to 2.0x**
   the target's assets (e.g. a $28B target → ~$14B-$56B). Tighten to 0.66x-1.5x
   if the band returns far more than 12 candidates; widen if it returns fewer
   than ~15.

3. **Fed / FDIC peer group + region — grouping and tie-break.** Prefer banks in
   the target's `FED` district and nearby states. Region is a *preference and
   tie-breaker*, not a hard gate — a structurally identical bank one district
   over is a better peer than a poorly matched in-region bank. When two
   candidates are otherwise close, the one closer in region and in asset size
   wins.

4. **Proximity score — final ranking.** Rank surviving candidates by a combined
   proximity score so the top ~10-12 are the closest overall matches.

## Proximity scoring

For each candidate compute a distance from the target, lower = closer:

```
size_distance   = |ln(candidate_assets) - ln(target_assets)|        # log so 2x up/down symmetric
region_distance = 0.0 if same FED district
                  0.5 if adjacent/same-region district
                  1.0 otherwise
model_distance  = 0.0 if same SPECGRP and compatible BKCLASS
                  0.5 if compatible SPECGRP (e.g. 4 vs 9)
                  1.0 otherwise
proximity_score = 1.00*size_distance + 0.50*region_distance + 0.35*model_distance
```

Rank ascending, take the top N (default 11, configurable 10-12). Always exclude
the target itself, inactive institutions, mutuals (unless target is mutual), and
obvious non-operating shells.

## When the user supplies their own peers

If the user names specific banks or CERTs, honor them exactly — skip screening
for those and only auto-fill any remaining slots up to the requested count. Always
echo the final peer list (name, CERT, state, assets, specialization) and let the
user swap members before the heavy financial pull.

## Output of this phase

A `peer_set.csv` / in-memory list with, per bank: `CERT`, `NAME`, `STALP`,
`FED`, `ASSET`, `SPECGRP`, `SPECGRPN`, `BKCLASS`, `proximity_score`, and a
`selection_reason` string ("in-region commercial peer, 0.8x assets"). This list
feeds the comparative financial pull.

## Atypical-bank outlier screen

Asset band + specialization screening lets in banks that carry a commercial
specialization code but are not operating commercial banks — deposit-sweep
vehicles, trust/custody banks, brokerage-affiliated banks. These distort peer
medians and percentile rankings (e.g. a sweep bank with 14% loans-to-deposits
and a 15% efficiency ratio). After ranking, the builder pulls a one-shot
financials fingerprint for the closest candidates and drops banks showing the
structural sweep signature, while deliberately keeping merely lean/efficient
commercial banks (low efficiency ratio but normal loan deployment and real
lending — e.g. ServisFirst — are GOOD peers, not outliers).

Detection (conservative, multi-signal):
- **Hard signals** (each alone marks a non-operating bank): loans-to-deposits
  `< 25`, or uninsured-deposit share `< 5`.
- **Soft signal** (only with corroboration): efficiency ratio `< 30`, which drops
  a bank only when paired with loans-to-deposits `< 50`.

Dropped banks are reported to the user (name + reason) and recorded in
`peer_set.json` under `dropped_outliers`. A user can always force one back with
`--include-cert`; forced peers bypass the screen entirely.

## Holding-company overlay (FR Y-9C / BHCPR)

The default basis is bank-level FDIC data. When the user wants the
holding-company view, two authoritative Fed sources apply, both as a labeled
overlay — never mixed into the bank-level comparison table:

- **FR Y-9C** (Consolidated Financial Statements for Holding Companies) via
  FFIEC/NIC — the consolidated holdco financials.
- **BHCPR** (Bank Holding Company Performance Report,
  https://www.ffiec.gov/npw/FinancialReport/BHCPRReports) — the Fed's
  holdco analog of the UBPR. It already publishes regulator-defined peer groups
  and peer-group average ratios, and its sections (loan mix & concentration
  analysis, relative income statement and margin analysis) mirror the metric
  categories this skill computes. Use it two ways: (1) as a **methodology
  cross-check** for peer grouping and ratio definitions, and (2) as a **holdco
  overlay** when the user benchmarks at the BHC level. Note it is PDF/peer-group
  output, not a JSON API, so it is a reference and overlay, not a drop-in feed.
