---
name: databricks-genie-space-ci-cd
description: Implement Genie metric-drift defense for Databricks Genie spaces with Azure DevOps CI/CD — L1 colocation gates on PRs, L2 structural drift audits, L2b behavioral benchmarks, and repo-driven deploy. Use when wiring Genie space definitions as code, preventing metric drift between models and Genie spaces, exporting space blueprints, setting up azure-pipelines for Genie, or adapting the reference ci/ scripts to a Databricks workspace + Azure Repos project. Search for # >>> ADAPT markers before claiming setup is complete.
---

# Databricks Genie Space CI/CD

Use this skill to stand up **metric-drift defense** for Databricks Genie spaces: keep space definitions versioned in git alongside the models and metric views they depend on, and enforce sync in CI.

## When to use

- A Genie space definition lives in the Databricks control plane but the SQL/dbt models it references live in git — and they can drift silently.
- You need PR gates that block model changes unless dependent metric-view / Genie-space files change in the same PR (L1).
- You need nightly checks that catch UI edits to live spaces (L2) or wrong answers despite structurally-correct definitions (L2b).
- You are wiring Azure DevOps pipelines for export, deploy, audit, and benchmark runs.

## The three layers

| Layer | Type | When | What it catches |
|-------|------|------|-----------------|
| **L1** | Preventive | Every PR | Model changed but dependent metric-view / Genie-space file did not |
| **L2** | Detective (structural) | Nightly | Live workspace object no longer matches repo blueprint |
| **L2b** | Detective (behavioral) | Nightly | Space returns wrong answers (upstream data or subtle metric mis-spec) |

**Golden rule:** definitions are human-owned in the repo. Agents may draft fixes; humans approve PRs; pipelines deploy from the repo — never straight to a live space.

## Reference implementation layout

This skill ships a working reference under:

- `ci/` — `check_colocation.py`, `audit_drift.py`, `run_benchmarks.py`, `deploy_spaces.py`, `databricks_helpers.py`
- `tests/` — offline pytest suite (no live workspace required)
- `benchmarks/` — example `treasury.bench.yaml` for L2b
- `azure-pipelines-pr.yml` / `azure-pipelines-nightly.yml` — Azure DevOps wiring
- `config.example.yaml` — dependency map (models → metric views → Genie spaces)

Read `QUICKSTART.md` for the ordered setup checklist, `repo-layout.md` for directory assumptions, and `README.md` for architecture and data flow.

## Adaptation workflow

1. Search all files for `# >>> ADAPT:` — every marker must be resolved before claiming the system is wired up.
2. Do **not** invent table names, catalog names, space IDs, or warehouse IDs. Ask the human or read existing repo config.
3. Copy `ci/`, `tests/`, pipeline YAML, and config into the target Azure Repos repo (see `QUICKSTART.md`).
4. `cp config.example.yaml config.yaml` and fill in host, warehouse, catalog, schema, and the model→view→space dependency map.
5. Export blueprints: `python ci/deploy_spaces.py --export --env dev`, normalize, commit `genie_spaces/*.genie.json`.
6. Wire L1 PR pipeline and L2/L2b nightly pipeline with a service-principal token in an Azure DevOps variable group.

## Verification

Run offline tests before touching a workspace:

```bash
pip install -r requirements-dev.txt
PYTHONPATH=ci python -m pytest
```

Expect ~72 passing tests with no Databricks connection.

## Prerequisites (confirm with human first)

- Genie Spaces Management API enabled on the workspace
- Service principal with CAN EDIT on target spaces, SELECT on metric views, CAN USE on a SQL warehouse
- Azure Repos + Databricks Git folders linked
- Python 3.10+ on the pipeline agent with `databricks-sdk` and `pyyaml`

## Key gotcha

Exported space JSON contains environment-specific metadata (`space_id`, timestamps, warehouse IDs, FQ table names). Always normalize before commit and diff (`normalize_space()` / `normalize_metric_view()` in `databricks_helpers.py`).
