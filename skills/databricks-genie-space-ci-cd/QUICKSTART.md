# QUICKSTART — stand this up in order

A checklist for the human (and the agent assisting them). Do these in sequence;
each step assumes the previous one is done.

## 0. Prereqs (human confirms)
- [ ] Genie Spaces Management API is enabled on the workspace (GA).
- [ ] A **service principal** exists with: CAN EDIT on the target Genie spaces,
      SELECT on the metric views, CAN USE on a SQL warehouse.
- [ ] An SP **token** is generated. You will store it as a secret, not in code.
- [ ] Azure Repos holds this repo; Databricks Git folders are linked to it.

## 1. Drop the files in
- [ ] Copy `ci/`, `tests/`, the two `azure-pipelines-*.yml`, `.gitignore`,
      `pytest.ini`, `requirements-dev.txt`, and `config.example.yaml` into the
      repo root.
- [ ] `cp config.example.yaml config.yaml`
- [ ] Confirm the suite runs: `pip install -r requirements-dev.txt &&
      PYTHONPATH=ci python -m pytest` (expect ~72 passing, no workspace needed).

## 2. Fill in config.yaml (the only hand-written file)
- [ ] Replace every `# >>> ADAPT` value: host, warehouse_id, catalog, schema.
- [ ] List each metric view and the model files it depends on.
- [ ] List each Genie space, its dev+prod space_ids, and the views it depends on.
- [ ] If you'd rather not hand-maintain dependencies, generate a first draft from
      Unity Catalog lineage (`databricks_helpers.lineage_downstream_of`) and have
      a human confirm it. Do NOT ship a guessed map.

## 3. Seed the blueprints (workspace -> repo)
- [ ] `export DATABRICKS_HOST=... DATABRICKS_TOKEN=...` (dev SP token)
- [ ] `python ci/deploy_spaces.py --export --env dev`
- [ ] Inspect the generated `genie_spaces/*.genie.json`. Confirm no `space_id`,
      timestamps, or warehouse_id leaked through (the normalizer strips them; if
      something slipped, add it to `config.normalize.strip_space_fields`).
- [ ] Commit them on a branch and open a PR (this exercises L1 for the first time).

## 4. Wire L1 (the gate)
- [ ] Create Variable Group `databricks-genie` (Pipelines → Library) with
      DATABRICKS_HOST, DATABRICKS_TOKEN (secret).
- [ ] New pipeline → this repo → `azure-pipelines-pr.yml`.
- [ ] Repos → Branches → main → Branch policies → Build validation →
      add the pipeline as a **required** check. *(This is the part that actually
      blocks merges. The pipeline alone only reports.)*
- [ ] Test: open a PR that edits a model but not its view. It must fail. Add a
      `drift-ack:` line to the PR description and confirm it passes.

## 5. Wire CD (deploy on merge)
- [ ] Add a release/CD pipeline (or extend an existing one) that runs
      `python ci/deploy_spaces.py --deploy --env prod` on merge to main,
      authenticated as the **prod** SP. Gate it behind your normal approval.
- [ ] First prod deploy will CREATE spaces and print their new ids — record
      those under `space_id_by_env.prod` in config.yaml and commit.

## 6. Wire L2 (the nightly audit)
- [ ] Add AZDO_ORG_URL, AZDO_PROJECT, AZDO_PAT (secret) and the prod
      DATABRICKS_* to the Variable Group (or a prod-specific group).
- [ ] New pipeline → `azure-pipelines-nightly.yml`.
- [ ] Test: make a harmless edit to a space in the prod UI, run the pipeline
      manually, confirm it reports drift and opens a work item. Then revert via
      `deploy_spaces.py --deploy --env prod`.

## 7. Wire L2b (behavioral benchmark regression)
- [ ] For each space, create `benchmarks/<space>.bench.yaml` (see the example
      `benchmarks/treasury.bench.yaml`). Author 5–15 questions with the space
      owner. **Pin `as_of_date`** and verify each golden value against the
      blessed dashboard. Do not invent golden numbers.
- [ ] Prefer `match: sql` for governed KPIs (assert the space routes through the
      certified metric view) and `match: scalar` for headline numbers. Reserve
      `match: rowset` for small stable lookups.
- [ ] The step is already wired in `azure-pipelines-nightly.yml` (runs after the
      structural audit, with `condition: always()`).
- [ ] Mind the rate limit: the Genie conversation API free tier is ~5 questions/
      min/workspace, so the script throttles ~13s between questions. Size the job
      timeout for your total question count.
- [ ] Test: run `python ci/run_benchmarks.py --env prod --only treasury` and
      confirm passes/regressions report correctly. (Set `PYTHONPATH=ci`.)
- [ ] Alternative backend: if you register benchmark questions *inside* the
      Genie space, use `--native` to let Databricks run + grade them
      (`genie_create_eval_run`). The custom YAML backend is best when you want
      SQL-fragment assertions or goldens stored in the repo.

> Note: the "framing guard" benchmark (asking for a metric that doesn't exist)
> is aspirational — both Anthropic and nao report confident-wrong-answers are
> not yet reliably solvable. Track it as a soft signal, not a hard gate.

---

## Mental model to keep straight
- **L1** = "you can't merge a model change that forgets its definition." (git, pre-merge)
- **CD** = "merging republishes the definition to the workspace." (repo→ws)
- **L2** = "if someone edited the workspace behind our back, we find out by
  morning." (ws vs repo, structural)
- **L2b** = "if a space still looks right but now answers wrong, we find out by
  morning." (behavioral, grades answers vs date-pinned goldens)
- A human always owns the definition. An agent may draft fixes; it never merges
  or writes to a live space directly.
