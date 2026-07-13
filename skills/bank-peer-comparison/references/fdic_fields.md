# FDIC BankFind Field Reference

Authoritative field map for the FDIC BankFind Suite APIs used by this skill. All
dollar amounts from `/financials` are in **thousands of dollars**. Ratios with
`R`-style names (e.g. `NIMY`, `ROA`, `ROE`, `LNLSDEPR`) are FDIC-computed
percentages — prefer them over hand-rolled math when they exist.

Base URLs:
- Institutions: `https://api.fdic.gov/banks/institutions`
- Financials: `https://api.fdic.gov/banks/financials`
- Docs / data dictionary: `https://api.fdic.gov/banks/docs`

## Table of contents
1. Institution / screening fields
2. Balance-sheet & summary financials
3. FDIC-computed performance ratios
4. Loan product-mix fields
5. Deposit-mix fields
6. Noninterest-income (NIR) fields
7. Derived metrics this skill computes
8. Charter / specialization / region code values

---

## 1. Institution / screening fields (`/institutions`)

| Field | Meaning | Use in screening |
| --- | --- | --- |
| `NAME` | Legal bank name | Display / matching |
| `CERT` | FDIC certificate number | Primary key across both APIs |
| `STALP` | State (2-letter) | Region proximity |
| `COUNTY` | County | Region proximity (fine grain) |
| `FED` | Federal Reserve district code (01-12) | Fed peer-group / region tie-break |
| `FEDDESC` | Fed district name | Display |
| `ASSET` | Total assets ($000) | Asset-band screen |
| `DEP` | Total deposits ($000) | Secondary size check |
| `BKCLASS` | Charter/regulator class (see §8) | Business-model screen |
| `CALLFORM` | Call Report form (31/41/51) | Comparability note |
| `SPECGRP` | Asset-concentration specialization code (see §8) | Business-model screen |
| `SPECGRPN` | Specialization name | Display |
| `QBPRCOML` | Quarterly Banking Profile commercial peer code | Business-model tie-break |
| `CB` | Community-bank flag (1/0) | Optional business-model filter |
| `OFFDOM` | Domestic offices (branches) | Comparative metric + sanity |
| `RSSDHCR` | Top-holder RSSD | Holdco mapping (FR Y-9C) |
| `NAMEHCR` | Top-holder name | Holdco mapping |
| `MUTUAL` | Mutual vs stock (1/0) | Optional exclusion (mutuals rarely peers) |
| `ESTYMD` | Establishment date | Context only |
| `ACTIVE` | Active flag — always filter `ACTIVE:1` | Exclude failed/merged |

## 2. Balance-sheet & summary financials (`/financials`)

| Field | Meaning ($000 unless noted) |
| --- | --- |
| `REPDTE` | Report date `YYYYMMDD` |
| `ASSET` | Total assets |
| `LNLSNET` | Net loans & leases |
| `LNLSGR` | Gross loans & leases (mix denominator) |
| `SC` | Total securities |
| `DEP` | Total deposits |
| `DEPUNINS` | Estimated uninsured deposits |
| `DEPINS` | Estimated insured deposits |
| `COREDEP` | Core deposits |
| `EQ` | Total equity capital |
| `EQPP` | Perpetual preferred equity (subtract for common equity) |
| `INTAN` | Total intangible assets incl. goodwill (subtract for tangible) |
| `NETINC` | Net income (YTD at each report date) |
| `NIM` | **Net interest income $ (YTD)** — NB: dollar amount, not the margin |
| `NONII` | Total noninterest income (YTD) |
| `NONIX` | Total noninterest expense (YTD) |
| `NUMEMP` | Employees (FTE) |
| `OFFDOM` | Domestic offices |
| `INTEXP` | Total interest expense (YTD) — deposit-cost numerator source |
| `EINTEXP` | Interest expense on deposits (YTD), where available |
| `INTINC` | Total interest income (YTD) — earning-asset yield |
| `ILNDOM` / `ILND` | Interest income on loans (YTD) — loan-yield numerator |

> Caution: `NIM` in `/financials` is the **net-interest-income dollar figure**.
> The **margin percentage** is `NIMY`. Do not confuse them.

## 3. FDIC-computed performance ratios (`/financials`) — percentages

| Field | Meaning |
| --- | --- |
| `ROA` | Return on assets |
| `ROE` | Return on equity |
| `NIMY` | Net interest margin (%) |
| `LNLSDEPR` | Net loans & leases to deposits |
| `NPERFV` | Nonperforming assets to assets |
| `NCLNLSR` | Net charge-offs to loans |
| `LNATRESR` | Allowance to gross loans |
| `RBC1AAJ` | Leverage ratio (Tier 1 to avg assets) |
| `IDT1CER` | Common equity tier 1 (CET1) ratio |
| `IDT1RWAJR` | Tier 1 risk-based capital ratio |
| `RBCRWAJ` | Total risk-based capital ratio |
| `INTEXPYQ`/`INTEXPY` | Cost of funding earning assets (%) where present |
| `ROAQ`/`ROEQ` | Quarterly annualized variants (if needed) |
| `EEFFR` | Efficiency ratio (FDIC-computed) — prefer if present, else derive |

## 4. Loan product-mix fields (`/financials`, denominator `LNLSGR`)

Top-level, non-overlapping:
`LNRE` real estate · `LNCI` C&I · `LNCON` consumer · `LNAG` farm/ag production ·
`LNMUNI` municipal · `LS` leases · `LNSOTHER` other · `LNDEP` depository-institution loans.

Real-estate submix (sum ties to `LNRE` ex-HELOC memo):
`LNRERES` 1-4 family · `LNRENRES` nonfarm nonresidential CRE ·
`LNRECONS` construction & land development · `LNREMULT` multifamily ·
`LNREAG` farmland/ag RE · `LNRELOC` 1-4 family revolving/HELOC (**memo line, not additive**).

Consumer submix: `LNAUTO` auto · `LNCRCD` credit card ·
`LNCONOTH` other consumer · `LNCONOT1` home improvement.

CRE definition note: the supervisory "CRE concentration" view is usually
`LNRECONS + LNREMULT + LNRENRES` (construction + multifamily + nonfarm
nonresidential). State which definition is used in output.

## 5. Deposit-mix fields (`/financials`, denominator `DEP`)

Funding split: `DEPNIDOM` noninterest-bearing dom · `DEPIDOM` interest-bearing dom.
Transaction split: `TRN` transaction · `NTR` nontransaction.
Memos: `TS` time & savings · `NTRTIME` time deposits · `NTRTMLGJ` time > $250k.
Quality: `COREDEP` core · `BRO` brokered · `DEPLSNB` listing-service (non-brokered).
Insurance estimates: `DEPINS` insured · `DEPUNINS` uninsured.

## 6. Noninterest-income (NIR) fields (`/financials`, denominator `NONII`)

Primary tie-out (`ISERCHG + IFIDUC + IGLTRAD + ADDNONII = NONII`):
`ISERCHG` service charges on deposits · `IFIDUC` fiduciary ·
`IGLTRAD` trading revenue · `ADDNONII` additional NIR (residual).

Supplemental detail (may sit inside `ADDNONII`, so do not double-count):
`IINVFEE` investment banking/advisory/brokerage/underwriting · `ISERFEE` servicing ·
`IINSCOM`/`IINSOTH` insurance commissions · `IINSUND` insurance underwriting ·
`NETGNSLN` net gains on loan sales · `NETGNAST` net gains on fixed-asset sales ·
`IOTNII` other NIR · `IVENCAP` venture capital · `IGLSEC` securities gains/losses.

## 7. Derived metrics this skill computes

| Output metric | Formula |
| --- | --- |
| Efficiency ratio | `NONIX / (NIM + NONII)` (use `EEFFR` if present) |
| Loans / assets | `LNLSNET / ASSET` |
| Securities / assets | `SC / ASSET` |
| Loans / deposits | `LNLSDEPR` (FDIC) or `LNLSNET / DEP` |
| Uninsured / deposits | `DEPUNINS / DEP` |
| NIR / total revenue | `NONII / (NIM + NONII)` |
| Earning-asset yield | `INTINCY` (FDIC-computed, annualized) |
| Cost of funding earning assets | `INTEXPY` (FDIC-computed, annualized) |
| Pre-tax ROA | `ROAPTX` (FDIC-computed) |
| NIR / avg assets | `NONIIAY` (FDIC-computed) |
| NIE / avg assets | `NONIXAY` (FDIC-computed) |
| PPNR / avg assets | `(NIM + NONII - NONIX)` annualized / avg assets |
| Asset/loan/deposit growth YoY | current vs same-quarter-prior-year `ASSET` / `LNLSGR` / `DEP` |
| Loan yield (approx) | `ILNDOM` annualized / avg gross loans (label approximate) |
| Deposit cost % (approx) | `EINTEXP` annualized / `DEPIDOM` (label approximate) |
| Commercial loan % | `LNCI / LNLSGR` |
| CRE % (supervisory) | `(LNRECONS + LNREMULT + LNRENRES) / LNLSGR` |
| CRE / capital | supervisory CRE $ / `EQ` (concentration lens) |
| Mortgage (1-4 fam) % | `LNRERES / LNLSGR` |
| Deposits per branch | `DEP / OFFDOM` |
| Assets per employee | `ASSET / NUMEMP` |
| Equity / assets | `EQ / ASSET` |
| Tangible common equity (TCE) | `EQ - EQPP - INTAN` (total equity less perpetual preferred less intangibles incl. goodwill) |
| TCE / tangible assets | `TCE / (ASSET - INTAN)` |
| Return on tangible common equity (ROTCE) | annualized `NETINC` / average TCE — the metric regional-bank investors lead with; strips goodwill/intangibles that inflate the equity base after acquisitions |
| Branches | `OFFDOM` |
| Headcount | `NUMEMP` |

**AOCI note (Category III/IV regional banks):** under the revised capital
framework, most AOCI elements — notably unrealized gains/losses on
available-for-sale securities — flow directly into CET1 and Tier 1 capital for
larger regional banks, so their reported CET1 now moves with rate-driven AFS
marks. The FDIC-reported `IDT1CER` (CET1) already reflects each bank's applicable
treatment, so no separate adjustment is needed in the comparison; just be aware
that CET1 dispersion across a peer set can partly reflect differing AOCI
inclusion and AFS duration, not only credit/RWA differences. Flag this when CET1
gaps look large.

Prefer the FDIC-computed `*Y`/`*AY` ratios (`INTINCY`, `INTEXPY`, `NONIIAY`,
`NONIXAY`, `ROAPTX`) over hand-rolled math — they are properly annualized and
consistent across banks. Loan yield and deposit cost have no clean FDIC ratio at
the bank level, so they stay approximate (YTD interest annualized by quarter).

## 8. Charter / specialization / region code values

`BKCLASS`: `N` national bank (OCC) · `SM` state member (Fed) ·
`NM` state nonmember (FDIC) · `SB` savings bank · `SA`/`OI` thrift/other ·
`SI` insured industrial. Commercial-bank peer screens usually keep `N, SM, NM, SB`.

`SPECGRP` (asset-concentration specialization):
`1` international · `2` ag · `3` ag-other · `4` commercial lending ·
`5` mortgage lending · `6` consumer lending · `7` other specialized <$1B ·
`8` all other <$1B · `9` all other >$1B. Commercial/regional peers are usually `4`
(or `9` for large diversified). Mismatched specialization is the most common
reason a same-asset bank is a poor peer.

`FED` Federal Reserve districts: `01` Boston · `02` New York · `03` Philadelphia ·
`04` Cleveland · `05` Richmond · `06` Atlanta · `07` Chicago · `08` St. Louis ·
`09` Minneapolis · `10` Kansas City · `11` Dallas · `12` San Francisco.
