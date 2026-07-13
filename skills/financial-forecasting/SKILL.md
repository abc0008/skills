---
name: financial-forecasting
description: "Financial statement forecasting and projection modeling for commercial banking analysis. Use for: (1) Revenue and expense forecasting, (2) Balance sheet projections, (3) Cash flow forecasting, (4) Scenario modeling (base/upside/downside), (5) Driver-based forecasting, (6) Working capital projections, (7) Debt schedule modeling. Triggers: forecast, projection, pro forma, financial model, budget, revenue forecast, expense forecast, balance sheet projection, cash flow projection, scenario analysis, what-if analysis."
---

# Financial Statement Forecasting

Build driver-based financial forecasts for income statement, balance sheet, and cash flow projections.

## Forecasting Workflow

1. **Analyze historicals** - Review 3-5 years of trends, identify drivers
2. **Establish assumptions** - Document key drivers and growth rates
3. **Build revenue forecast** - Top-down or bottom-up approach
4. **Project expenses** - Fixed vs. variable cost modeling
5. **Forecast balance sheet** - Working capital, CapEx, debt
6. **Generate cash flow** - Derive from I/S and B/S changes
7. **Run scenarios** - Base, upside, downside cases
8. **Validate and sensitize** - Reasonableness checks

## Revenue Forecasting

### Top-Down Approach
```
Market Size × Market Share × Pricing = Revenue

Example:
  Total Addressable Market (TAM):     $500MM
  × Serviceable Market %:              40%
  = Serviceable Addressable Market:   $200MM
  × Target Market Share:               5%
  = Revenue Forecast:                 $10MM
```

### Bottom-Up Approach
```
Units × Price = Revenue

Example (by product line):
  Product A: 10,000 units × $500 = $5.0MM
  Product B: 25,000 units × $150 = $3.75MM
  Services:  500 contracts × $2,000 = $1.0MM
  Total Revenue: $9.75MM
```

### Growth Rate Methods
| Method | When to Use | Formula |
|--------|-------------|---------|
| Historical CAGR | Stable, mature business | (End/Start)^(1/n) - 1 |
| YoY Growth | Volatile or trending | (Current - Prior) / Prior |
| Regression | Clear correlation exists | Y = mX + b |
| Management Guidance | Available and credible | As provided |
| Industry Growth | Market-driven business | Industry rate ± adjustment |

### Revenue Build Template
```
REVENUE FORECAST ($000s)
                        Hist    Hist    Proj    Proj    Proj
                        FY23    FY24    FY25    FY26    FY27
─────────────────────────────────────────────────────────────
Product Revenue
  Units Sold            100     110     121     133     146
  Growth %                      10%     10%     10%     10%
  Avg Price            $50     $52     $53     $55     $56
  Price Growth %                4%      2%      3%      2%
  Product Revenue    $5,000  $5,720  $6,413  $7,315  $8,176

Service Revenue
  Contracts             50      55      61      67      74
  Growth %                      10%     10%     10%     10%
  Avg Contract        $20     $21     $21     $22     $22
  Service Revenue   $1,000  $1,155  $1,281  $1,474  $1,628

TOTAL REVENUE       $6,000  $6,875  $7,694  $8,789  $9,804
  YoY Growth %               14.6%   11.9%   14.2%   11.5%
```

## Expense Forecasting

### Cost Behavior Analysis
| Cost Type | Behavior | Forecasting Method |
|-----------|----------|-------------------|
| Variable | Changes with volume | % of Revenue |
| Semi-variable | Fixed + variable component | Fixed $ + % Rev |
| Fixed | Constant regardless of volume | Flat or inflation adj |
| Step | Fixed within ranges | Step function |

### Expense Drivers
```
COST DRIVER MAPPING

Cost of Goods Sold
  └─ Materials: % of revenue (historical avg or trending)
  └─ Direct Labor: Headcount × avg wage
  └─ Manufacturing OH: % of direct costs

Operating Expenses
  └─ Salaries: Headcount × avg salary × (1 + merit increase)
  └─ Benefits: % of salaries (typically 25-35%)
  └─ Rent: Lease terms (fixed or escalating)
  └─ Utilities: Sq footage × rate/sq ft
  └─ Insurance: Prior year × inflation
  └─ Professional Fees: Budget or % revenue
  └─ Marketing: % of revenue or budget
  └─ D&A: Depreciation schedule (see below)
  └─ Travel: Headcount × avg/employee or % revenue
```

### Expense Forecast Template
```
EXPENSE FORECAST ($000s)
                        Hist    Hist    Proj    Proj    Proj
                        FY23    FY24    FY25    FY26    FY27    Driver
───────────────────────────────────────────────────────────────────────
Revenue               $6,000  $6,875  $7,694  $8,789  $9,804

COGS
  Materials           $1,800  $2,063  $2,308  $2,637  $2,941  30% Rev
  Direct Labor          $600    $650    $700    $750    $800  HC × wage
  Mfg Overhead          $300    $325    $350    $375    $400  Fixed+3%
Total COGS           $2,700  $3,038  $3,358  $3,762  $4,141
  % of Revenue        45.0%   44.2%   43.6%   42.8%   42.2%

GROSS PROFIT         $3,300  $3,837  $4,336  $5,027  $5,663
  Gross Margin        55.0%   55.8%   56.4%   57.2%   57.8%

OpEx
  Salaries           $1,200  $1,260  $1,386  $1,525  $1,677  HC growth
  Benefits             $360    $378    $416    $457    $503  30% sal
  Rent                 $180    $185    $191    $196    $202  3% escal
  D&A                  $200    $220    $250    $280    $300  Schedule
  Other                $300    $344    $385    $439    $490  5% Rev
Total OpEx           $2,240  $2,387  $2,628  $2,897  $3,172

EBIT                 $1,060  $1,450  $1,708  $2,130  $2,491
  EBIT Margin         17.7%   21.1%   22.2%   24.2%   25.4%
```

## Balance Sheet Forecasting

### Working Capital Drivers
```
WORKING CAPITAL ASSUMPTIONS

Accounts Receivable
  A/R Days = (A/R / Revenue) × 365
  Projected A/R = (Revenue / 365) × A/R Days Target

Inventory
  Inventory Days = (Inventory / COGS) × 365
  Projected Inventory = (COGS / 365) × Inventory Days Target

Accounts Payable
  A/P Days = (A/P / COGS) × 365
  Projected A/P = (COGS / 365) × A/P Days Target

Prepaid Expenses
  Usually % of Operating Expenses

Accrued Liabilities
  Usually % of Operating Expenses
```

### Fixed Asset Schedule
```
FIXED ASSET ROLL-FORWARD ($000s)

                        FY24    FY25    FY26    FY27
─────────────────────────────────────────────────────
Beginning Gross PP&E   $2,000  $2,300  $2,650  $3,050
  + Capital Expenditures  $300    $350    $400    $450
  - Disposals              $0      $0      $0      $0
Ending Gross PP&E      $2,300  $2,650  $3,050  $3,500

Beginning Accum Depr   ($800)  ($1,020) ($1,270) ($1,550)
  + Depreciation Exp    ($220)   ($250)   ($280)   ($300)
  - Disposals              $0       $0       $0       $0
Ending Accum Depr     ($1,020) ($1,270) ($1,550) ($1,850)

Net PP&E              $1,280  $1,380  $1,500  $1,650

CapEx as % Revenue      4.4%    4.5%    4.5%    4.6%
Depreciation Method: Straight-line, 10-year avg life
```

### Debt Schedule
```
DEBT SCHEDULE ($000s)

Term Loan A
  Beginning Balance    $1,500  $1,300  $1,100    $900
  - Principal Payments  ($200)  ($200)  ($200)  ($200)
  Ending Balance       $1,300  $1,100    $900    $700
  Interest Rate         6.5%    6.5%    6.5%    6.5%
  Interest Expense       $91     $78     $65     $52

Revolver
  Beginning Balance      $200    $150    $100     $50
  +/- Net Draws/Paydowns ($50)   ($50)   ($50)   ($50)
  Ending Balance         $150    $100     $50      $0
  Interest Rate         7.0%    7.0%    7.0%    7.0%
  Interest Expense       $12      $9      $5      $2

Total Debt            $1,450  $1,200    $950    $700
Total Interest Exp      $103     $87     $70     $54
```

### Balance Sheet Projection Template
```
PROJECTED BALANCE SHEET ($000s)
                        FY24    FY25    FY26    FY27    Driver
───────────────────────────────────────────────────────────────
ASSETS
Cash                    $500    $650    $850  $1,100  Plug/Min
Accounts Receivable     $945  $1,057  $1,208  $1,348  45 days
Inventory               $500    $552    $618    $681  60 days
Prepaid Expenses        $120    $131    $145    $159  5% OpEx
Total Current Assets  $2,065  $2,390  $2,821  $3,288

Net PP&E              $1,280  $1,380  $1,500  $1,650  Schedule
Other Assets            $200    $200    $200    $200  Flat
TOTAL ASSETS          $3,545  $3,970  $4,521  $5,138

LIABILITIES
Accounts Payable        $416    $460    $515    $567  45 days
Accrued Liabilities     $239    $263    $290    $317  10% OpEx
Current Portion LTD     $200    $200    $200    $200  Schedule
Total Current Liab      $855    $923  $1,005  $1,084

Long-Term Debt        $1,250  $1,000    $750    $500  Schedule
TOTAL LIABILITIES     $2,105  $1,923  $1,755  $1,584

EQUITY
Retained Earnings     $1,440  $2,047  $2,766  $3,554  Cumulative
TOTAL EQUITY          $1,440  $2,047  $2,766  $3,554

TOTAL LIAB + EQUITY   $3,545  $3,970  $4,521  $5,138
Balance Check             $0      $0      $0      $0
```

## Cash Flow Projection

### Indirect Method Template
```
PROJECTED CASH FLOW ($000s)
                            FY25    FY26    FY27
────────────────────────────────────────────────────
OPERATING ACTIVITIES
Net Income                  $607    $719    $788

Adjustments:
  + Depreciation            $250    $280    $300
  - Increase in A/R        ($112)  ($151)  ($140)
  - Increase in Inventory   ($52)   ($66)   ($63)
  - Increase in Prepaid     ($11)   ($14)   ($14)
  + Increase in A/P          $44     $55     $52
  + Increase in Accrued      $24     $27     $27
Cash from Operations        $750    $850    $950

INVESTING ACTIVITIES
  - Capital Expenditures   ($350)  ($400)  ($450)
Cash from Investing        ($350)  ($400)  ($450)

FINANCING ACTIVITIES
  - Debt Principal Pmts    ($250)  ($250)  ($250)
  - Dividends                 $0      $0      $0
Cash from Financing        ($250)  ($250)  ($250)

NET CHANGE IN CASH          $150    $200    $250
Beginning Cash              $500    $650    $850
ENDING CASH                 $650    $850  $1,100
```

## Scenario Analysis

### Scenario Framework
| Scenario | Revenue | Margins | Assumptions |
|----------|---------|---------|-------------|
| Base | Historical growth | Stable | Management plan achieved |
| Upside | +20% vs base | +200 bps | Market share gains, pricing |
| Downside | -20% vs base | -200 bps | Recession, competitive pressure |

### Scenario Output Summary
```
SCENARIO COMPARISON - FY27 PROJECTED

                    Downside    Base    Upside
──────────────────────────────────────────────
Revenue              $7,843   $9,804  $11,765
  vs. Base            -20%       -      +20%

EBITDA               $1,569   $2,791   $4,013
  Margin              20.0%    28.5%    34.1%

Net Income             $471     $788   $1,105

Total Debt             $700     $700     $700
Debt/EBITDA           0.45x    0.25x    0.17x
DSCR                  1.05x    1.65x    2.25x

Cash Balance           $650   $1,100   $1,550
```

## Assumption Documentation

### Required Disclosures
For each forecast, document:
1. **Time horizon** - Number of projection years
2. **Key drivers** - Revenue growth, margins, CapEx
3. **Methodology** - Top-down vs. bottom-up
4. **Sources** - Management, industry data, historical
5. **Limitations** - Key uncertainties and sensitivities

### Assumption Table Format
```
KEY ASSUMPTIONS

Revenue Assumptions              FY25    FY26    FY27    Source
──────────────────────────────────────────────────────────────────
Revenue Growth Rate              12%     14%     12%    Mgmt guidance
Price Increase                    2%      3%      2%    Historical avg
Volume Growth                    10%     11%     10%    Market outlook

Margin Assumptions
──────────────────────────────────────────────────────────────────
Gross Margin                    56.4%   57.2%   57.8%  Mix improvement
EBITDA Margin                   26.2%   28.5%   28.5%  Operating leverage

Balance Sheet Assumptions
──────────────────────────────────────────────────────────────────
A/R Days                          45      45      45    Policy target
Inventory Days                    60      60      60    Historical avg
CapEx (% Revenue)               4.5%    4.5%    4.6%   Expansion plan
```

## Excel Output

Use the `xlsx` skill to build forecast models:
- Separate tabs: Assumptions, I/S, B/S, CF, Scenarios
- All projections linked to assumption cells
- Conditional formatting for validation checks
- Sensitivity tables using Data Tables
