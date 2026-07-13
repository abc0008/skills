# Brand integration — composing with FRAME.md / DESIGN.md

Read this when producing anything visual (a screen, a component, a mockup, a coded UI) in a
project that carries `FRAME.md` and/or `DESIGN.md`. It defines how this skill's behavior/IA layer
composes with those files' visual-token layer, and it lists the real Bank Analysis product
vocabulary so examples and mockups are concrete instead of generic.

## Two layers, one system

- **`FRAME.md` / `DESIGN.md` = the visual + brand layer.** Color, typography, spacing, radius,
  elevation, motion, and brand composition rules (gold is a pinpoint never a fill; hairlines do
  the structural work; exactly one shadow, on the product window; the `headline-tri`; the
  frame/treatment recipes). They are the AceAnalytics.dev / **Bank Analysis** system.
- **This skill = the behavior + IA layer.** How flows work, how data is structured and disclosed,
  where actions go, how state/errors/confirmation/lineage are handled.

**Precedence:** on anything visual, the brand files win — read them first and conform. On anything
behavioral (disclosure, drill-down, action placement, states), this skill governs. When both are
silent, use the load-bearing rules in `SKILL.md`. Conformance to the brand files is a success
criterion for any rendered UI; so is conformance to the three pillars.

Practically: this skill decides *that* a row's detail opens in a nonmodal side panel and *that*
the number shows its lineage; `DESIGN.md` decides what that panel's hairlines, type ramp, and
accent usage look like. Don't restate the tokens here — read them from the files (canonically in
the project's setup folder). If the files are absent, apply the behavior rules and note that
visual tokens are unspecified rather than inventing a brand.

## A caution on register

`FRAME.md`/`DESIGN.md` are written for the **video / frame / marketing** layer (monumental
wordmarks, one-idea-per-frame, 55–75% empty, cinematic dwell). The *product UI* is denser and
more utilitarian than a hero frame — a controller reconciling 400 rows is not a keynote slide.
So: inherit the **tokens** (color, type, spacing, radius, the one-shadow rule, gold restraint,
hairlines-as-structure) and the **brand voice**, but do **not** import the frame layer's
emptiness targets or one-element-per-screen rule into a working data screen. The density
exception the brand already names — the Tool Index ledger — signals that data surfaces are
allowed to be tight. Dense financial tables are the product-side equivalent: bring brand tokens,
drop the frame silence budget.

## Real Bank Analysis vocabulary (use in examples & mockups)

Pulled from `DESIGN.md`'s "Real product vocabulary" — use these verbatim so work reads as the
actual product, not a generic finance demo:

- **Surface / wordmark:** Bank Analysis · `aceanalytics.dev / parallax` · tabs: **Forecasting ·
  RM Pro Forma · Mortgage LOS · ACE Home**.
- **Console:** **FY2027 Budget** · "Acting as" roles — **Finance Liaison / FP&A Manager /
  Corporate Planning / Executive Viewer** (role-based views: the personalization-as-reduction
  pattern in `ia-navigation.md`, and the analyst/controller/CFO signal-vs-noise split).
- **Lifecycle states:** **NOT STARTED → IN PROGRESS → SUBMITTED → APPROVED → FP&A LIVE → LOADED.**
  This is the confirmation pillar's backbone — a record's state is the proof an action landed;
  show it prominently with actor + timestamp.
- **Columns:** Business unit · Status · Assigned · **FY1 NI Δ vs baseline** · Last saved. (Note
  "Last saved" = the preserve-work / confirmation cue; "Status" = the lifecycle state in a list.)
- **Surfaces / consoles:** Forecast Console · FP&A Review Console · Executive Review Console ·
  Forecast cube.
- **Baseline / basis:** `Actual vs FCST_2026Q1_PRIOR` — the as-of/basis string that belongs next
  to a number for lineage.
- **Engine / formulas:** deterministic monthly engine; formulas shown in mono, e.g.
  `max(0, pre-tax income) × tax rate` — expose these for the calculation half of lineage.
- **Driver-linkage matrix:** drivers × line items with gold dots at the linkages — the drill map
  from a line item to the drivers that move it.

## How the pillars land in this product specifically

- **Disclosure/drill-down:** Forecast Console summary → business-unit line → driver-linkage matrix
  → the driver × line-item detail, in a nonmodal side panel so the console stays visible.
- **Lineage:** every forecast figure shows its basis (`Actual vs FCST_2026Q1_PRIOR`), its formula
  (mono), and the drivers linked to it; filter/scenario state is visible on the surface.
- **Confirmation:** submitting a budget transitions NOT STARTED → … → SUBMITTED with actor +
  timestamp and a "Last saved" cue; a long engine run shows step progress beyond 10s and a
  persistent completion notice; approval moves the state again, visibly, in the review console.
