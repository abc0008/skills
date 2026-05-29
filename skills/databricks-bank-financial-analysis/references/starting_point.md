# Starting Point

This skill was shaped from locally cached Anthropic financial-services patterns, especially:

- `month-end-closer/local/skills/variance-commentary/SKILL.md`
- `fund-admin/local/skills/variance-commentary/SKILL.md`
- `earnings-reviewer/local/skills/earnings-analysis/SKILL.md`
- `financial-analysis/local/skills/3-statement-model/SKILL.md`

Useful inherited principles:

- Explain the movement from underlying activity.
- Use period-over-period and budget-vs-actual framing.
- Treat source attribution as mandatory.
- Prefer structured tables plus a concise management narrative.
- Avoid inventing drivers when the source data is not sufficient.

Bank-specific changes:

- Baseline source is extracted monthly bank financial PDFs.
- Secondary source is IBM Planning Analytics Finance ERP Genie Space.
- Required analysis order is time first, then GL category.
- Required category set covers loan balances, deposit balances, NIM, NIR, NIE, headcount, GL transaction anomalies, and credit/asset quality.
- The intended runtime audience is a Databricks Genie Agent or Supervisor Agent.

