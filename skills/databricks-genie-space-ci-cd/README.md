# Genie Metric-Drift Defense — L1 + L2

> **READ THIS FIRST IF YOU ARE AN AI AGENT.**
> You have been handed a working *reference implementation*, not a finished
> product. Your job is to adapt it to a specific Databricks workspace + Azure
> DevOps project. Every place you must change something is marked with
> `# >>> ADAPT:` in the code. Search for that token across all files before you
> claim the system is wired up. Do not invent table names, catalog names, space
> IDs, or warehouse IDs — ask the human for them, or read them from existing
> repo config. Inventing them is the single most common way this breaks.

---

## What problem this solves (the one-paragraph version)

A Databricks **Genie space** stores its definition — table list, instructions,
example SQL, and the **metric views** it points at — in the Databricks *control
plane* (the service), NOT in the git repo that holds the dbt/SQL models those
definitions describe. So when a model changes (a column is renamed, a grain
changes, a metric is redefined), the Genie space can keep pointing at the old
shape and quietly return wrong answers. Nobody gets an error. Trust erodes
silently. This is called **metric drift**. The fix is to make the space
definition live *as a file in the same repo as the models*, and to enforce —
in CI — that the two never get out of sync.

This mirrors how Anthropic keeps its internal analytics agent accurate: the
pull request that changes a model is the same PR that updates the doc
describing it, and a CI hook blocks any model change that forgets to update its
doc. We are rebuilding that control on Databricks + Azure DevOps.

---

## The two layers

| Layer | Type | When it runs | What it catches | File |
|------|------|--------------|-----------------|------|
| **L1** | Preventive | On every PR | A model changed but its dependent metric-view / Genie-space file did NOT change in the same PR | `ci/check_colocation.py` + `azure-pipelines-pr.yml` |
| **L2** | Detective (structural) | Nightly (cron) | Someone edited a space/metric-view in the **UI**, so the live object no longer matches the repo | `ci/audit_drift.py` + `azure-pipelines-nightly.yml` |
| **L2b** | Detective (behavioral) | Nightly (cron) | A space passes L1+L2 but now returns the **wrong answer** (upstream data changed, or a metric is subtly mis-specified) | `ci/run_benchmarks.py` + `benchmarks/*.bench.yaml` |

**The golden rule both layers enforce:** the definition of a metric is owned by
a human and lives in the repo. An agent may *draft* a fix; a human *approves*
the PR; the pipeline *deploys from the repo* — never straight to a live space.

**Why all three?** L1 cannot see UI edits (they never touch the repo, so there
is no PR to gate). L2 catches those UI edits but only checks *structure* — it
can't tell that a structurally-correct space now returns a wrong number. L2b
catches that by actually asking questions and grading answers. Each covers the
others' blind spots. None replaces another.

---

## File-by-file

```
genie-drift-defense/
├── README.md                    ← you are here
├── QUICKSTART.md                ← ordered setup runbook
├── repo-layout.md               ← directory assumptions
├── config.example.yaml          ← copy to config.yaml and fill in; maps models→views→spaces
├── requirements-dev.txt         ← runtime + test deps
├── pytest.ini
├── .gitignore
├── ci/
│   ├── _core.py                 ← foundation: typed exceptions, logging, retry (no deps)
│   ├── databricks_helpers.py    ← config validation + DatabricksAdapter (retries, REST fallback,
│   │                                etag-safe update, SQL-injection-guarded DESCRIBE)
│   ├── check_colocation.py      ← L1 gate (PR pipeline; exits non-zero to block merge)
│   ├── audit_drift.py           ← L2 structural audit (nightly; live workspace vs repo)
│   ├── run_benchmarks.py        ← L2b behavioral regression (native OR custom backend)
│   └── deploy_spaces.py         ← CD: export blueprints + idempotent etag-safe upsert
├── tests/                       ← pytest suite; runs offline with a fake Databricks client
│   ├── conftest.py              ← fakes + fixtures
│   ├── test_core.py             ← retry / error classification
│   ├── test_helpers.py          ← config validation, normalize, identifier safety
│   ├── test_adapter.py          ← adapter vs fake SDK (export/update/ask/sql)
│   ├── test_logic.py            ← L1 violations + L2b grading + determinism guard
│   └── test_audit_integration.py← L2 drift detection end-to-end
├── benchmarks/
│   └── <space>.bench.yaml       ← date-pinned eval questions + golden answers per space
├── models/        .gitkeep      ← your dbt/SQL transforms live here
├── metric_views/  .gitkeep      ← UC metric views as code live here
├── genie_spaces/  .gitkeep      ← exported space blueprints live here
├── azure-pipelines-pr.yml       ← L1 + unit tests (pr trigger)
└── azure-pipelines-nightly.yml  ← L2 + L2b wiring (schedule trigger)
```

Run the test suite any time with: `PYTHONPATH=ci python -m pytest`
(needs only `pytest` + `pyyaml`; no live workspace, no databricks-sdk).

Read `repo-layout.md` next, then `config.example.yaml` (the one file a human
fills in by hand).

---

## How the pieces talk to each other (data flow)

```
                    ┌─────────────────────────────────────────┐
   AUTHORING (dev)  │ Analyst builds a Genie space in the UI    │
                    │ pointing at certified metric views        │
                    └───────────────────┬───────────────────────┘
                                         │  export (one time + after intended edits)
                                         ▼
                    ┌─────────────────────────────────────────┐
   REPO (git)       │ /genie_spaces/<name>.genie.json           │  ← versioned blueprint
                    │ /metric_views/<name>.metricview.yaml      │  ← versioned definition
                    │ /models/<name>.sql                        │  ← the transforms
                    │ /config.yaml                              │  ← model→view→space map
                    └───────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        ▼ (on PR)                         ▼ (on merge)                      ▼ (nightly)
  check_colocation.py               deploy_spaces.py                 audit_drift.py
  "did you update the space         "upsert the blueprint            "does live workspace
   when you changed the model?"      into the workspace"              still match the repo?"
        │                                 │                                 │
        ▼                                 ▼                                 ▼
  PASS → merge allowed            space updated in prod            MATCH → silent success
  FAIL → merge blocked            from versioned source            DRIFT → open work item +
                                                                    fail the run
```

---

## Prerequisites (tell the human to confirm these BEFORE running anything)

1. **Genie Spaces Management API access.** GA as of early 2026. Needs a
   workspace with the Databricks SQL entitlement and at least CAN USE on a SQL
   warehouse. Confirm the workspace host + a service-principal token.
2. **A service principal** (not a human PAT) for the pipelines, stored in an
   Azure DevOps **variable group** or **service connection**. It needs:
   CAN EDIT on the Genie spaces it manages, and SELECT on the metric views.
3. **Databricks Git folders** already connected to the Azure Repos repo (the
   human says they have this). The CI scripts run on the Azure DevOps agent and
   talk to Databricks over the REST API — they do NOT need to run *inside*
   Databricks, though `deploy_spaces.py` may target a production Git folder.
4. **Python 3.10+** on the pipeline agent, with `databricks-sdk` and `pyyaml`.

---

## The #1 gotcha (do not skip)

When you export a space or metric view from one workspace, the JSON contains
**environment-specific metadata**: `space_id`, `created_at`, `created_by`, and
embedded **SQL warehouse IDs** and sometimes fully-qualified
`catalog.schema.table` names. If you commit those and replay them in another
workspace, the deploy will either collide with an existing object or be
rejected outright.

**Always normalize before committing and before diffing** (the helper does
this — `normalize_space()` / `normalize_metric_view()`). Keep table references
**unqualified** where possible and let environment config inject the catalog
and schema, so one blueprint works in dev, staging, and prod.

---

## What "done" looks like

- A PR that renames a column in `instrument_dim.sql` **fails** L1 until the
  same PR updates `treasury.genie.json` (or whichever space depends on it).
- A sneaky UI edit to a production space is caught by **tonight's** L2 run,
  which files an Azure DevOps work item with the exact diff.
- Merging to `main` redeploys the space from the committed blueprint, so prod
  always equals the repo.
- A human governance owner approves every definition change. No agent writes
  directly to a live space.
