---
name: databricks-bank-financial-analysis
description: Produce structured monthly internal bank financial analysis inside a Databricks Genie Agent using extracted PDF financials as the baseline and the IBM Planning Analytics Finance ERP Genie Space for additional GL Fact and GL Transaction research. Use this whenever the user asks for bank monthly financials, MoM, QoQ, YTD vs Budget, YTD vs Goal, GL variance commentary, NIM/NIR/NIE drivers, loan/deposit trends, headcount story, anomalous GL transactions, asset quality, or internal bank management reporting. Pair with databricks-pdf-genie-report when PDFs need to be ingested or cited, and use databricks-bank-statement-auditor first when the user asks to audit, foot, tie out, reconcile, or validate the statement package before writing commentary.
---

# Databricks Bank Financial Analysis

Use this skill to produce internal bank financial analysis in a Databricks Genie Agent. The analysis starts with extracted PDF financials, then queries the IBM Planning Analytics Finance ERP Genie Space when source PDFs do not contain enough detail to explain a movement.

This skill is bent from the Anthropic financial-services variance-commentary pattern: explain the movement from underlying activity, not by restating the variance.

## Data Source Priority

Use this hierarchy:

1. **Extracted PDF financials** from the paired `databricks-pdf-genie-report` workflow. Treat these as the baseline for reported period values, management packet figures, citations, and report context.
2. **IBM Planning Analytics Finance ERP Genie Space** for missing drivers, additional dimensions, budget/goal comparisons, account-level detail, and transaction-level evidence.
3. **Manual assumptions from the user** only when neither source contains the needed data. Label these clearly.

The IBM Planning Analytics Finance ERP Genie Space should expose:

- `General Ledger Fact`
- `General Ledger Transactions`

When asking the Finance ERP Genie Space for GL data:

- Default Scenario to `Actuals` unless the user names Budget, Forecast, Goal, or another scenario.
- Include a GL account, GL category, line-item, or account-family filter whenever the question implies a specific category.
- Use `General Ledger Fact` for balances, totals, rollups, time comparisons, scenario comparisons, business-unit comparisons, and line-item trending.
- Use `General Ledger Transactions` for anomaly review, unusual entries, large journal activity, vendor/payee/source details, posting descriptions, and explanations of GL movements.
- Do not invent drivers. If the data does not explain the movement, say "driver unclear - requires controller follow-up."

## Analysis Order

Always structure the report by **time analysis first**, then by **GL category**.

Required order:

1. Data scope and source coverage.
2. Executive summary.
3. MoM analysis by GL category.
4. QoQ analysis by GL category when quarter context is available.
5. YTD vs Budget or YTD vs Goal analysis by GL category.
6. Cross-period themes and management implications.
7. GL transaction anomalies tied to the category analyses.
8. Open questions, missing data, and follow-up requests.

Within each period section, use this GL category sequence unless the user specifies another:

1. Loan balances.
2. Deposit balances.
3. Net interest margin, including attribution and rate/volume/mix changes when available.
4. Non-interest revenue changes and key drivers.
5. Non-interest expense changes and key drivers.
6. Headcount and hiring story.
7. Anomalous GL transactions related to the above items.
8. Credit and asset quality trends.

## Variance Commentary Standard

For every material movement, write commentary in this structure:

| Field | Requirement |
|---|---|
| Line / Category | GL category, account family, or KPI |
| Current / Comparison | Current period actual and comparison value |
| Change | Dollar change, percent change, and bps where relevant |
| Driver | One sentence explaining why the movement happened |
| Evidence | PDF citation or Finance ERP Genie Space query evidence |
| Confidence | High, medium, low, or follow-up required |

A good driver explains the underlying activity:

- Good: "Deposit balances fell $42.3MM as commercial non-interest DDA runoff offset retail CD growth."
- Weak: "Deposits decreased $42.3MM month over month."

## Materiality

Use user-provided thresholds when available. Otherwise use these defaults:

- Balance sheet categories: explain changes above 2.5% or above $1.0MM.
- Revenue and expense categories: explain changes above 5.0% or above $250K.
- Margin or ratio metrics: explain changes above 10 bps.
- Credit/asset quality: always comment on NPA, NCO, allowance, delinquency, criticized/classified assets, and provision changes.
- Headcount: always comment if headcount changes by 2 or more FTEs or if compensation/benefit expense moves materially.
- GL transaction anomalies: flag any transaction, journal, vendor, source, or account movement that is large, unusual, manually posted, backdated, reversed, or inconsistent with the period story.

## Required Financial Lenses

### MoM Analysis

Include, at minimum:

- MoM Analysis: Loan balances.
- MoM Analysis: Deposit balances.
- MoM Analysis: Net interest margin attribution and changes.
- MoM Analysis: Non-interest revenue changes and key drivers.
- MoM Analysis: Non-interest expense changes and key drivers.
- MoM Analysis: Headcount and hiring story.
- MoM Analysis: Anomalous GL transactions related to the above items.
- MoM Analysis: Credit and asset quality trends.

### QoQ Analysis

Use the same GL category sequence. Distinguish seasonality, quarter-end balance-sheet behavior, rate reset effects, credit migration, incentive accruals, one-time expenses, and reserve/provision timing.

### YTD vs Budget or Goal

Use the same GL category sequence. If the user says "budget," "forecast," or "goal," query the Finance ERP Genie Space for that scenario. Show:

- YTD Actual.
- YTD Budget or Goal.
- Dollar variance.
- Percent variance.
- Driver and outlook.
- Whether the variance is timing, permanent, mix, rate, volume, credit, or one-time.

## Query Playbook

Use `templates/ibm_pa_finance_erp_genie_query_playbook.md` for query patterns to send to the IBM Planning Analytics Finance ERP Genie Space.

When querying:

- Ask for period, entity, branch, cost center, product, GL category, account, scenario, and amount if available.
- For GL Fact queries, request both current and comparison periods in the same result when possible.
- For GL Transaction queries, request transaction date, posting date, source, journal id, account, description, debit/credit, amount, entity, cost center, preparer/approver if available, and reversal markers.
- After retrieving transaction detail, roll it back up to the GL category movement. Do not leave transaction lists unconnected from the main story.

## Output Structure

Use `templates/monthly_bank_financial_analysis_report.md` as the report skeleton.

Every report should include:

- Period, entity, and scope.
- Source coverage table: PDFs used, Finance ERP Genie Space queries used, missing data.
- Time-first analysis sections.
- Category-level variance tables.
- Driver commentary with evidence.
- Anomaly table for GL transactions.
- Management implications and follow-up questions.

Do not bury the time comparison. The reader should know what changed MoM, QoQ, and YTD before reading category detail.

## Pairing with PDF Ingestion Skill

When PDFs are not already parsed or table-loaded, invoke or follow `databricks-pdf-genie-report` first:

1. Ingest the monthly financial PDF package.
2. Extract balance sheet, income statement, KPI, credit, headcount, and footnote fields.
3. Preserve citations and page references.
4. Load the extracted fields to a curated table.
5. Use this skill for the financial analysis layer.

If the PDF and Finance ERP Genie Space disagree, show both values, identify source and period differences, and do not silently pick one.

## Pairing with Statement Audit Skill

When the user asks to audit, foot, tie out, reconcile, validate, QA, or review the integrity of a financial statement package, use `databricks-bank-statement-auditor` before producing variance commentary. Treat unresolved footing, summary-to-detail, organization rollup, FTP, or GL tie-out exceptions as audit exceptions, not business drivers.

## References

- Starting pattern: Anthropic financial-services `variance-commentary` skill.
- Related repo areas supplied by user:
  - https://github.com/anthropics/financial-services/tree/main/plugins/agent-plugins/earnings-reviewer/skills
  - https://github.com/anthropics/financial-services/tree/main/plugins/vertical-plugins/financial-analysis
- Paired local skill: `/Users/alexcardell/AlexCoding_Local/.agents/skills/databricks-pdf-genie-report/SKILL.md`
