---
name: bank-fpa-forecaster
description: |
  Driver-based and time-series forecasting for regional bank internal FP&A — balance sheet and income statement modeling at a detailed GL / TM1 roll-up level. Use when the user asks to forecast, project, or stress-test bank financials: net interest income, non-interest revenue (NIR), non-interest expense (NIE), balance sheet (loans, deposits, securities, borrowings), or any GL-level segment. Triggers include "forecast", "budget", "stress test", "scenario", "driver-based model", "ARIMA", "baseline vs severely adverse", "NIE/NIR forecast", "balance sheet projection", "GL forecast", and "TM1".
---

# Bank FP&A Forecaster

Forecast a regional bank's income statement and balance sheet at a detailed GL level using a segment → methodology → driver/model → aggregate → validate workflow. Adapted from a general time-series skill and optimized for internal FP&A and stress-test work where TM1 (or an equivalent EPM cube) is the source of record for history.

## Core Workflow

1. **Segment.** Decompose the statement into forecastable segments aligned to TM1 roll-ups one level below the statement caption (e.g., NIE → Employment, Occupancy, Other; Other → sub-level carveouts). Forecast at the sub-level; report at the roll-up. See `references/segmentation-map.md`.
2. **Classify methodology.** Assign every segment to one of four methodology buckets (see `references/methodology-guide.md`):
   - **Primary Driver** — determined by external, scenario-specific factors (e.g., salaries = headcount × average wage growth).
   - **Scenario-driven Management Assumption** — a management call heavily dictated by the scenario (e.g., cut bonuses in Severely Adverse).
   - **Driver + Management Assumption** — scenario driver × managed rate (e.g., headcount × insurance cost per employee).
   - **Management Assumption** — flat with prior year / prior quarter / trailing average. Reserve for immaterial or scenario-insensitive lines (e.g., BOLI, amortization of intangibles).
3. **Select model or driver.** For quantitative segments, default to ARIMAX with 1–2 macro covariates from the scenario set (unemployment, GDP, S&P 500, HH net worth, corporate profits, 2Y UST, BAA spread). For driver-based segments, build explicit driver math (volume × rate). See `references/model-selection.md`.
4. **Forecast and aggregate.** Run quarterly forecasts over the horizon (typically 9 quarters for stress tests, 4–8 for budget/plan), then aggregate sub-levels back to reporting captions. Balance the balance sheet with a funding plug (typically wholesale borrowings or cash).
5. **Validate.** Back-test (holdout MAPE/RMSE), sanity-check against history and scenario narrative, document assumptions and overlays. See `references/validation-governance.md`.

## Statement Coverage

**Income statement:**
- **NII**: average earning asset balances × yields, deposits/borrowings × cost; tie to balance sheet forecast. Rate paths come from the scenario.
- **NIR** (8 segments): Deposit Service Charges, NSF Fees, Card Fees, Mortgage Revenue, Wealth Management, Capital Markets, Other Fee Income, BOLI.
- **NIE** (3 segments + sub-levels): Employment Expense (driver-based; 14 GL sub-segments), Occupancy, Other Expense (with carveouts: Amortization of Intangibles, Operational Risk Losses, Fixed Asset G/L, Lawsuits; remainder split Fixed vs. Discretionary misc.).
- **Provision**: link to credit-loss model output or scenario loss rates by portfolio; do not freelance CECL math — take rates as inputs.
- **Taxes**: effective rate on pre-tax income, adjusted for permanent items (BOLI, tax credits).

**Balance sheet:**
- Loans by portfolio: roll-forward (beginning + originations/draws − payoffs/charge-offs).
- Deposits by product: driver- or model-based; mix shift matters more than total in rate scenarios.
- Securities, borrowings, equity (net income − dividends ± AOCI), then plug to balance.

## Scenario Discipline

- Forecast **Baseline** first; scenario forecasts (Adverse / Severely Adverse / rate shocks) are expressed relative to Baseline wherever possible.
- Internal Baseline (e.g., GOALS) includes initiatives that time-series models will not pick up. Decide explicitly whether to overlay them; default is to exclude from model-driven segments and document the resulting conservatism/upside.
- When a model output contradicts the scenario narrative (e.g., fee income rising in a deep recession), override with a documented qualitative assumption rather than forcing the model.

## Working With the User's Data

- Expect history as GL-level quarterly (or monthly) extracts: `period, segment_code, segment_name, amount`. Driver inputs as `period, driver_code, value`. Templates in `assets/`.
- Scripts in `scripts/` run on pandas + statsmodels (`pip install pandas statsmodels --break-system-packages` if needed): `preprocess.py` (clean/pivot/stationarity checks), `forecast.py` (ARIMAX, ETS, and driver-based engines), `evaluate.py` (holdout backtest, MAPE/RMSE/bias).
- Output a forecast table per segment per scenario plus a methodology summary table (Segment | Methodology | Variables | Key Assumptions) in the format used in stress-test documentation.
- The user works in Power BI/DAX and reads Python. Keep script outputs as tidy CSVs that load cleanly into Power BI; explain Python only when asked.

## Best Practices

- Forecast at the level where a stable driver relationship exists — not necessarily the lowest GL level. Aggregate noisy small accounts into Fixed/Discretionary buckets.
- Prefer fewer covariates with an economic story over best-fit covariate mining. Document why each macro variable plausibly drives the segment.
- Every quantitative model needs a qualitative review step; every management assumption needs a one-line rationale. Assume the output will be challenged by model risk management or examiners.
- Refresh vs. redevelop: refresh (re-estimate coefficients on updated history) annually; redevelop when residuals deteriorate, the business changes (acquisition, fee structure change), or backtest misses exceed tolerance.

## Application Embedding (Regional Forecasting Module)

These sections govern the skill when embedded as the AI Auto Forecast engine in
the BankAnalysis Regional Forecasting Module (`/api/regional-forecast/auto-forecast`).

### Short-History Protocol

When fewer than 36 monthly observations exist, do not claim ARIMAX. Use a
seasonal-naive + trend reference: monthly seasonal indices from available full
years, trailing-12 level, capped YoY trend. Always report a holdout backtest
(fit excluding the last 6 months, predict them, report MAPE) so the user can
judge model quality. With 36+ months, seasonal indices are mandatory and the
trend must be estimated on at least two full-year pairs.

### Forecast Window Alignment

The forecast starts at the first month after the last closed actual — never at
a generic fiscal-year boundary. If the forecast window opens mid-year, first
complete the stub year (actual YTD + forecast remainder = full-year total),
then forecast whole fiscal years. State the stub-year composition explicitly.

### Reasonability Review Loop (mandatory)

Every model-generated forecast is reviewed before presentation:

1. **Continuity** — the implied first forecast month must sit within ±20% of
   the last actual month unless a documented driver explains the break.
2. **Growth plausibility** — annual growth beyond ±15% requires an explicit
   driver; trend extrapolation alone never justifies it.
3. **Stub-year math** — stub-year total must equal actual YTD plus a remainder
   consistent with the recent run-rate.
4. **Driver coherence** — every driver must reference a scenario variable or an
   observed regime change in the history; no unexplained rates.

The reviewer returns approve or revise-with-critique; one revision round is
allowed, after which the forecast is presented with the review verdict and any
open warnings attached. The end user always sees the review status.

### Driver Linkage Map (mandatory)

Every forecasted GL segment carries a pre-mapped set of driver candidates with
an economic story, injected into the forecaster as `driverLinkageCandidates`.
Each driver the forecaster emits must set `linkedTo` to one of those candidate
names (or its scenario variable); off-map drivers require a justified deviation
in the rationale, and the reasonability reviewer fails the driver-coherence
check for any unlinked driver.

| Segment family | Linked drivers |
| --- | --- |
| Loan balances | Producer hiring & production ramp; paydowns/payoffs (SOFR); regional GDP |
| Deposit balances | Household/business liquidity (GDP); rate competition / beta (SOFR); producer deposit production |
| Interest income | Average loan balances (loan forecast); SOFR + portfolio spread |
| Interest expense | Average deposit balances (deposit forecast); deposit beta × SOFR |
| Personnel / comp | Headcount FTE (hiring plan); wage inflation |
| Occupancy / equipment | Lease escalators / CPI (expense inflation) |
| Technology / data processing | Key vendor inflation; project portfolio (management assumption) |
| Marketing / BD / T&E / community | Discretionary spend plan (management assumption) |
| Service charges / NSF | Transaction deposit accounts (deposit forecast) |
| Card fees | Consumer spend volume (GDP) |
| Mortgage revenue | Mortgage rates, inverse (SOFR) |
| Wealth / trust / brokerage | Market levels / AUM (GDP) |
| Capital markets / swaps | Deal activity (GDP) |
| Provision | Scenario loss rate × loan balances (creditLoss) |
| BOLI / intangibles | Management assumption (flat) |
| Unmapped | Trailing run-rate trend; expense inflation |

### Output Contract

Respond with only JSON: `methodologyBucket`, `method`, `narrative`, `drivers`
(name/value/rationale/linkedTo), `annual` ([{year, valueMM}] starting at the
stub year), `confidence`. Balances are EOP $MM; flows are full-year $MM. The
host computes deltas vs the prior-cycle plan and maps them into planning
levers — never emit lever values directly.
