---
name: databricks-bank-statement-auditor
description: Audit internal bank financial statement packages in Databricks Genie or Agent mode after a user uploads a PDF or Excel package and Databricks AI functions parse/extract the tables. Use this whenever the user asks to audit, foot, tie out, reconcile, validate, QA, or review bank financial statements, management financial packets, P&L/expense detail, FTP schedules, branch/LOB/cost-center rollups, balance sheets, income statements, NIM/NIR/NIE schedules, headcount tables, or supporting detail pages. Pair with databricks-pdf-genie-report for ingestion/extraction and databricks-bank-financial-analysis for narrative variance commentary after the audit passes.
---

# Databricks Bank Statement Auditor

Use this skill to turn a parsed PDF or Excel financial statement package into an audit workpaper inside Databricks Genie or a Databricks agent. The user is assumed to have uploaded an internal bank financial statement package. Databricks AI functions, Genie file upload, or an upstream Lakeflow/AI Functions workflow have already parsed or extracted the package into queryable tables.

This skill is adapted from the Anthropic `statement-auditor` pattern: the statement package is the thing under test. Your job is to recompute, foot, cross-foot, tie supporting detail to summaries, and produce a pass/hold recommendation with exact exceptions.

## Operating Assumptions

- The package may be a PDF management packet, an Excel workbook, or both.
- Source extraction may come from `ai_parse_document`, `ai_extract`, Genie file upload, Excel tables, or curated Delta tables produced by `databricks-pdf-genie-report`.
- Preserve page, sheet, table, row, column, citation, and confidence metadata whenever it exists.
- Treat extracted values as untrusted until they are footed and tied. Low OCR/extraction confidence is an audit issue, not a fact.
- If a trusted ledger, IBM Planning Analytics Finance ERP Genie Space, GL fact table, or GL transaction table is available, use it as a source-of-truth tie-out layer. If it is not available, perform an internal consistency audit and say that external GL tie-out was not performed.

## First Decision

Classify the requested audit:

1. **Internal consistency audit**: Foot every table, cross-foot row/column totals, and tie related package tables to each other.
2. **Ledger-supported audit**: Do the internal audit, then tie material values to GL Fact, GL Transactions, IBM Planning Analytics, or another trusted finance source.
3. **Extraction quality audit**: Focus on whether Databricks AI Functions correctly extracted table structure, labels, units, periods, signs, and citations from the uploaded package.

If the user does not specify, default to **internal consistency audit** plus ledger-supported checks where a trusted finance source is available.

## Required Inputs

Proceed with placeholders when possible, but identify missing blockers:

- Package period and scenario: month, quarter, YTD, Actuals, Budget, Forecast, Goal.
- Organization scope: consolidated bank, holding company, legal entity, region, market, branch, line of business, cost center, product, or officer.
- Parsed table source: uploaded Genie file, extracted Delta table, or Excel sheet/table names.
- Available source-of-truth tables or Genie Spaces, especially GL Fact and GL Transactions.
- Display units: dollars, thousands, millions, percentages, basis points, FTEs.

## Audit Workflow

### 1. Inventory the Package

Build a source coverage table before doing math:

| Field | Capture |
|---|---|
| Source | PDF path, Excel file, Genie upload, Delta table, or workbook sheet |
| Period | Month/quarter/YTD and comparison period |
| Scenario | Actuals/Budget/Forecast/Goal |
| Org level | Consolidated/entity/branch/LOB/cost center/product |
| Table name | Statement, schedule, detail page, or extracted table id |
| Units | Dollars/thousands/millions/percent/bps/FTE |
| Confidence | Extraction confidence, if available |
| Citation | Page, sheet, row/column, element id, or citation id |

Do not start with variance commentary. Start with whether the package is internally reliable.

### 2. Normalize Values

Normalize each extracted table before testing:

- Convert parentheses and trailing minus signs to negative values.
- Standardize scale: actual dollars, thousands, millions, percent, and bps.
- Preserve the displayed value and the normalized numeric value.
- Identify subtotal, total, memo, and calculated rows.
- Preserve row labels exactly enough to trace source citations, but map them to standard bank categories when useful.
- Separate period columns from scenario columns and organization columns.
- Treat blank, dash, `n/m`, and `NA` differently from zero.

Read `references/audit-checks.md` for the detailed bank-specific check library.

### 3. Foot and Cross-Foot Every Table

For each table:

- Recompute row totals across periods, organizations, products, or scenarios where shown.
- Recompute column totals from detail rows.
- Recompute subtotals and grand totals.
- Check calculated ratios and percentages from underlying numerator/denominator.
- Check YTD totals from monthly values when both are present.
- Check prior-period beginning balances against current rollforwards.
- Flag missing labels, duplicate rows, duplicated table names, stale period headers, mixed units, and low-confidence cells.

Use tolerance rules from `references/audit-checks.md`. Show both displayed and recomputed values for every exception.

### 4. Tie Summary Tables to Supporting Detail

Tie related tables before drawing conclusions:

- Summary income statement expense category line items to supporting detail page totals.
- Non-interest expense summary to compensation, occupancy, data processing, professional fees, marketing, FDIC/insurance, and other expense schedules.
- Non-interest revenue summary to service charges, interchange/card, mortgage, wealth, treasury management, gain/loss, and other fee schedules.
- Net interest income and NIM tables to interest income, interest expense, average earning assets, average interest-bearing liabilities, and FTP schedules.
- Balance sheet totals to loan, deposit, securities, borrowing, allowance, and equity schedules.
- Credit and asset quality summary to provision, allowance, net charge-off, NPA, delinquency, criticized/classified asset, and reserve schedules.
- Headcount and compensation schedules to salary, benefits, incentives, and FTE totals.

For each tie-out, record `summary_value`, `detail_value`, `difference`, `tolerance`, `status`, and `source_citations`.

### 5. Audit Bank Organization Rollups

Internal bank packets often show multiple organization levels. Validate hierarchy math:

- Branches roll to markets.
- Markets roll to regions.
- Regions roll to bank or holding-company totals.
- Cost centers roll to departments.
- Products roll to line of business.
- Legal entities consolidate with eliminations where applicable.

If eliminations or allocations exist, do not force child rows to equal parent rows without an explicit elimination/adjustment row. Instead, show:

```text
Parent total
  - Sum of visible children
  - Explicit eliminations/allocations
  = unexplained difference
```

### 6. Audit Funds Transfer Pricing

Treat FTP as a first-class bank audit area:

- FTP credits and charges should tie to the FTP schedule by entity, branch, LOB, product, and period.
- Consolidated FTP credits and charges should net to zero or to the documented treasury/balancing unit.
- Deposit FTP credit, loan FTP charge/credit, liquidity premium, basis adjustments, and duration/maturity adjustments should use consistent signs across schedules.
- Net interest income by organization should tie after FTP allocation.
- FTP detail should reconcile to summary profitability tables.
- If FTP methodology, curve, duration, beta, or spread assumptions are not in the package, flag methodology support as missing rather than inventing it.

### 7. Ledger-Supported Tie-Outs

If GL Fact or IBM Planning Analytics Finance ERP Genie is available:

- Default Scenario to **Actuals** unless the user names Budget, Forecast, Goal, or another scenario.
- Use GL account, GL category, line item, account family, organization, period, and scenario filters.
- Tie summary statement values to GL Fact by period, entity, branch/LOB/cost center/product, scenario, and account family.
- Use GL Transactions only for exception investigation, unusual journal activity, manual postings, reversals, or unexplained category differences.
- Do not silently override the packet. Show packet value, GL value, and difference.

### 8. Output the Audit Report

Use this exact structure:

1. **Audit scope and source coverage**
2. **Overall recommendation**: Pass, Pass with immaterial exceptions, Hold pending correction, or Hold pending source clarification
3. **Executive exception summary**
4. **Table footing results**
5. **Cross-table tie-out results**
6. **Organization rollup results**
7. **FTP audit results**
8. **Ledger tie-out results** if a source-of-truth table was available
9. **Extraction quality issues**
10. **Open questions and controller follow-up**

Every exception must include:

| Field | Requirement |
|---|---|
| Severity | Critical, Warning, or Info |
| Location | Page/sheet/table/row/column and citation if available |
| Test | Footing, cross-footing, summary-to-detail, org rollup, FTP, GL tie-out, extraction quality |
| Reported value | Value from the statement package |
| Recomputed/source value | Recomputed total, detail total, or source-of-truth value |
| Difference | Dollar, percent, bps, or FTE difference |
| Tolerance | Applied threshold |
| Likely cause | Extraction error, missing row, stale schedule, sign issue, unit mismatch, allocation/elimination, timing, or unclear |
| Recommendation | Correct package, rerun extraction, map line item, request support, or controller review |

## Templates

- Use `templates/genie_statement_auditor_instructions.md` when the user needs paste-ready Databricks Genie or Agent instructions.
- Use `templates/audit_report.md` as the output skeleton.
- Use `references/audit-checks.md` for tolerance and check definitions.

## Pairing With Existing Skills

- Use `databricks-pdf-genie-report` first when PDFs or Excel files still need durable ingestion, parsing, extraction, citations, or Delta table creation.
- Use this skill next to validate whether the extracted financial statement package is internally reliable.
- Use `databricks-bank-financial-analysis` only after the audit passes or after clearly separating known audit exceptions from management commentary.

## Source Anchors

Refresh Databricks-specific details from these official docs when implementing the pipeline:

- Genie file upload: https://docs.databricks.com/aws/en/genie/file-upload
- `ai_parse_document`: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_parse_document
- `ai_extract`: https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract
