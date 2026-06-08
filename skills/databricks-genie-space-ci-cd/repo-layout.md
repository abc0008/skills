# Repo layout assumptions

Every script in `ci/` assumes this structure. If your repo differs, you have
two choices: (a) move files to match this, or (b) edit the path constants at the
top of `databricks_helpers.py` (marked `# >>> ADAPT:`). Option (b) is usually
right for an existing repo — don't reorganize someone's repo to fit a script.

```
<repo root>/
├── models/                       # Your transforms. dbt .sql, or plain Databricks SQL.
│   ├── instrument_dim.sql        #   The thing that, when it changes, can break a space.
│   └── deposits_fact.sql
│
├── metric_views/                 # Unity Catalog metric views, as code.
│   ├── nim.metricview.yaml        #   The GOVERNED definition of a metric. Human-owned.
│   └── deposits.metricview.yaml   #   Genie spaces should point at THESE, not raw tables.
│
├── genie_spaces/                 # Exported Genie space blueprints (the "docs").
│   ├── treasury.genie.json
│   └── retail_deposits.genie.json
│
├── benchmarks/                   # Date-pinned eval questions per space (L2b).
│   ├── treasury.bench.yaml        #   Behavioral regression: grade answers vs golden.
│   └── retail_deposits.bench.yaml
│
├── config.yaml                   # The dependency map. THE ONE FILE A HUMAN FILLS IN.
│
└── ci/                           # These scripts.
    ├── databricks_helpers.py
    ├── check_colocation.py
    ├── audit_drift.py
    ├── run_benchmarks.py
    └── deploy_spaces.py
```

## Why metric views sit between models and spaces

This is the architecture the source guidance pushes, and it matters for drift:

- **Models** (`models/`) are raw-ish transforms. They change often.
- **Metric views** (`metric_views/`) are the *one governed answer* for a
  business concept ("NIM", "total deposits"). They are defined in YAML,
  registered in Unity Catalog, and are what a Genie space should reference
  first. They change rarely and only with human sign-off.
- **Genie spaces** (`genie_spaces/`) are the natural-language interface. They
  point at metric views (preferred) and/or tables, and carry instructions and
  example SQL.

Drift can happen at *either* seam:
1. model → metric view  (a column the metric view's `expr` uses gets renamed)
2. metric view / table → genie space  (the space references a view/column that changed)

`config.yaml` declares both seams so the L1 gate knows what depends on what.

## Naming convention (the scripts rely on it)

- Metric view files end in `.metricview.yaml`
- Genie space files end in `.genie.json`
- The "logical name" of an object is its filename without that suffix
  (`nim.metricview.yaml` → logical name `nim`).

If you change these suffixes, update `SPACE_SUFFIX` and `VIEW_SUFFIX` in
`databricks_helpers.py`.
