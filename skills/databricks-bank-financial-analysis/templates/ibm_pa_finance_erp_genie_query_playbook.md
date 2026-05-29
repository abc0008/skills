# IBM Planning Analytics Finance ERP Genie Query Playbook

Use these prompts inside the IBM Planning Analytics Finance ERP Genie Space when the extracted PDF financials do not contain enough detail.

The target Genie Space should expose:

- `General Ledger Fact`
- `General Ledger Transactions`

## General Rules

- Default scenario to `Actuals` unless Budget, Forecast, Goal, or another scenario is explicitly named.
- Include GL account, GL category, or line-item filters whenever the financial statement category implies one.
- Query `General Ledger Fact` before `General Ledger Transactions` for rollups.
- Query `General Ledger Transactions` after a material movement is identified and needs an activity-level explanation.
- Ask for source period, comparison period, entity, branch, cost center, product, GL category, account, scenario, and amount when available.
- Tie every transaction anomaly back to a MoM, QoQ, or YTD category movement.

## GL Fact Prompt Patterns

### MoM category movement

```text
Using General Ledger Fact, show monthly Actuals for {entity_scope} for {current_month} and {prior_month}
filtered to GL category or account family "{gl_category}".
Return current amount, prior month amount, dollar change, percent change, entity, branch, cost center, product if available, GL account, and account description.
```

### QoQ category movement

```text
Using General Ledger Fact, compare Actuals for {current_quarter} vs {prior_quarter}
for {entity_scope}, filtered to "{gl_category}".
Return quarter totals, dollar change, percent change, and the top contributing GL accounts or cost centers.
```

### YTD actual vs budget or goal

```text
Using General Ledger Fact, compare YTD Actuals to YTD {Budget_or_Goal}
through {current_month} for {entity_scope}, filtered to "{gl_category}".
Return YTD Actual, YTD {Budget_or_Goal}, dollar variance, percent variance, and top contributing GL accounts or cost centers.
```

### NIM rate/volume/mix support

```text
Using General Ledger Fact, return interest income, interest expense, average earning assets,
average interest-bearing liabilities, loan yield, deposit cost, earning asset mix, and funding mix for
{current_month}, {prior_month}, {current_quarter}, and YTD where available.
Use Actuals and filter to {entity_scope}.
```

### Headcount and compensation support

```text
Using General Ledger Fact, return salary, incentive compensation, benefits, payroll tax, contractor,
and recruiting expense for {current_month} and {prior_month}, Actuals, filtered to {entity_scope}.
Break out by cost center and GL account. Include headcount metrics if available.
```

### Credit and asset quality support

```text
Using General Ledger Fact, return provision, charge-offs, recoveries, allowance, nonperforming loans,
delinquencies, criticized/classified assets, and credit-related expense metrics for {current_month},
{prior_month}, {current_quarter}, and YTD where available. Use Actuals and filter to {entity_scope}.
```

## GL Transaction Prompt Patterns

### Anomaly scan for a category

```text
Using General Ledger Transactions, list the largest and most unusual transactions in {current_month}
for {entity_scope}, filtered to "{gl_category}".
Return transaction date, posting date, journal id, source system, GL account, account description,
description, debit amount, credit amount, net amount, cost center, branch, preparer, approver,
reversal indicator, and whether the entry is manual or system-generated if available.
```

### Explain a material movement

```text
Using General Ledger Transactions, explain the drivers behind the {current_month} vs {prior_month}
movement in "{gl_category}" for {entity_scope}.
Identify the top transactions, journals, vendors, sources, or cost centers that explain the movement.
```

### Manual journal and reversal review

```text
Using General Ledger Transactions, show manual journals, reversals, backdated entries, and late-posted
transactions for {current_month} in "{gl_category}" for {entity_scope}.
Return transaction identifiers, amounts, descriptions, preparer/approver, and related reversal links if available.
```

## Category Mapping Hints

Use the local chart of accounts when available. Otherwise start with these account-family filters:

| Analysis area | GL filter concept |
|---|---|
| Loan balances | Loans, commercial loans, consumer loans, mortgage loans, lease financing, loan contra accounts |
| Deposit balances | Demand deposits, interest-bearing deposits, savings, money market, CDs, brokered deposits |
| NIM | Interest income, loan interest income, securities interest income, interest expense, deposit interest expense, borrowing cost |
| NIR | Service charges, interchange, wealth/trust fees, mortgage banking, gain/loss, other non-interest income |
| NIE | Salaries, benefits, occupancy, equipment, data processing, marketing, professional fees, FDIC, OREO, other expense |
| Headcount | Salary, benefits, bonus, incentive compensation, payroll tax, recruiting, contractor |
| Credit quality | Provision, allowance, charge-offs, recoveries, NPA/NPL, delinquency, criticized/classified |

