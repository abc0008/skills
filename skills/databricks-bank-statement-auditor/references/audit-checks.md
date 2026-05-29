# Bank Statement Audit Checks

Use this checklist when auditing parsed bank financial statement packages.

## Tolerance Rules

Set tolerance from the displayed unit unless the user gives a stricter rule:

| Unit | Default tolerance |
|---|---|
| Actual dollars | `max($1.00, 0.01% of absolute reported value)` |
| Dollars in thousands | `max($1K, 0.01% of absolute reported value)` |
| Dollars in millions | `max($0.1MM, 0.01% of absolute reported value)` |
| Percentages | `0.1 percentage point` unless used in a ratio reported to more precision |
| Basis points | `1 bp` |
| FTE/headcount | `0.5 FTE` or `1 person` depending on source precision |

Rounding differences inside tolerance are Info only. Differences outside tolerance are Warning unless they affect totals, executive summaries, source-of-truth values, or a sign, in which case they are Critical.

## Required Normalization

Normalize values before testing:

- Parentheses: `(123)` means `-123`.
- Trailing minus: `123-` means `-123`.
- Dash or blank: missing, not zero, unless the table legend says otherwise.
- `n/m`, `NM`, or `N/A`: not meaningful, not zero.
- Percent signs and bps labels: store as separate units.
- Mixed units: flag as Warning unless every affected value can be clearly normalized.
- Page or table captions may define units for the whole table; row labels can override units.

## Footing Tests

For every table:

1. Sum visible detail rows to each subtotal.
2. Sum subtotals to grand totals.
3. Sum columns across organizations, products, or periods where a row total is shown.
4. Recompute percentages and ratios from numerators and denominators.
5. Recompute period change, percent change, and bps change.
6. Check beginning balance plus activity equals ending balance for rollforwards.
7. Check YTD equals the sum of completed months when monthly detail is shown.

## Core Bank Statement Tie-Outs

### Income Statement

- Net income equals pre-tax income less tax expense.
- Pre-tax income equals revenue less non-interest expense plus/minus provision and other items according to bank convention.
- Net interest income equals interest income less interest expense.
- Total revenue equals net interest income plus non-interest income when the package uses that definition.
- Total non-interest expense equals the sum of compensation, occupancy, data processing, professional fees, marketing, FDIC/insurance, amortization, other operating expense, and other disclosed categories.

### Balance Sheet

- Total assets equals total liabilities plus equity.
- Total loans ties to commercial, CRE, consumer, mortgage, and other loan schedules.
- Total deposits ties to DDA, interest-bearing checking, savings, money market, CD, brokered, public funds, and other deposit schedules.
- Allowance for credit losses rollforward ties beginning allowance, provision, charge-offs, recoveries, and ending allowance.
- Securities totals tie amortized cost, fair value, unrealized gain/loss, and AFS/HTM schedules where shown.

### Net Interest Margin and FTP

- Net interest income ties to NIM schedule numerator.
- Average earning assets tie to balance sheet or average-balance schedule.
- NIM equals annualized net interest income divided by average earning assets.
- Yield and cost rates tie interest dollars to average balances.
- FTP charges/credits tie detail rows to organization profitability totals.
- Consolidated FTP credits and charges net to zero or to documented treasury/balancing unit.
- FTP adjustment signs are consistent across summary, LOB, branch, and product views.

### Non-Interest Revenue

- Service charges, interchange/card, mortgage, wealth, treasury management, gain/loss, and other fee income detail ties to non-interest revenue summary.
- One-time gains/losses tie to supporting schedules or GL transaction support when available.

### Non-Interest Expense

- Compensation and benefits tie to headcount/FTE and salary/benefits/incentive schedules when shown.
- Occupancy, equipment, data processing, professional fees, marketing, FDIC/insurance, and other operating expenses tie to supporting detail pages.
- Expense allocations and shared-service charges tie to organization-level profitability tables.

### Credit and Asset Quality

- Provision expense ties to allowance rollforward and income statement.
- Net charge-offs equal charge-offs less recoveries.
- NPA, delinquency, criticized/classified assets, and reserve ratios recalculate from disclosed numerators and denominators.

## Organization Rollup Checks

Check each visible hierarchy:

- Branch to market.
- Market to region.
- Region to bank.
- Cost center to department.
- Product to line of business.
- Legal entity to consolidated bank or holding company.

If the parent does not equal children plus explicit eliminations/allocations, flag the unexplained difference. Do not assume missing branches or hidden cost centers explain the difference unless the package says so.

## Extraction Quality Checks

Flag these separately from accounting exceptions:

- Low confidence values in totals, subtotals, or executive summary tables.
- Split tables where rows continue across pages but extraction treated them as separate unrelated tables.
- Misread signs, parentheses, decimal places, or percent/bps units.
- Header rows attached to the wrong period or organization.
- Duplicate table extraction.
- Missing table captions or page citations.
- Merged Excel cells that create ambiguous row/column labels.

## Severity

| Severity | Use when |
|---|---|
| Critical | A total does not foot, source-of-truth tie-out fails, balance sheet does not balance, FTP does not net as expected, or a summary-to-detail difference affects management conclusions. |
| Warning | A supporting schedule mismatch, unit issue, low-confidence extraction, missing mapping, or unexplained rollup difference needs review but does not clearly alter the headline result. |
| Info | Rounding, display, labeling, or documentation items that do not affect values. |
