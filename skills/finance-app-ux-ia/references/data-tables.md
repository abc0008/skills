# Data tables & dense financial grids

The highest-traffic pattern in finance software. Read this for anything with a table, grid,
ledger, register, statement, variance view, or comps sheet. Source: NN/g "Data Tables: Four
Major User Tasks" plus the density/consistency guidance, applied to financial data.

## Why a table (not cards/tiles) for financial data

Tables beat card layouts for finance for two concrete reasons:

- **Scalability** — you can add rows and columns as the dataset grows without redesigning.
- **Comparison** — adjacent values are directly comparable; the eye barely moves and nothing has
  to be held in working memory. Card UIs force users to spatially reorient for every comparison,
  which is exactly the task finance users do constantly (period vs. period, actual vs. budget,
  this entity vs. peer).

Reach for a table by default for financial data. Use cards/visualizations to *summarize* or
*narrate* on top of the table, not to replace it.

## Design around the four user tasks

Every table serves some mix of these four. Name the ones your table must support, then apply the
matching requirements.

### 1. Find record(s) that fit criteria

- **First column = a human-readable identifier**, not a system ID. Account name before account
  code; entity/business-unit name before its key. The reader scans the anchor column to locate a
  row; a "mystery-meat" ID column defeats that. (Keep the code — put it second, or in the detail
  view. Lineage needs it; scanning doesn't.)
- **Column order follows importance; related columns are adjacent.** Don't strand the two numbers
  a user compares at column 1 and column 20. In finance: put the measure the screen is *about*
  and its comparator (e.g. FY1 NI Δ vs. baseline, right next to the baseline) side by side.
- **Filtering must be discoverable, quick, and powerful, with a visible active-filter state.**
  The single most important provenance cue in a table: the user must know instantly whether they
  are looking at filtered/sorted or complete data before they trust a total. Show which filters
  are active and offer one-click clear. (This is half of the lineage pillar — see
  `disclosure-lineage-confirmation.md`.)

### 2. Compare data

Two failure modes in big financial tables: users lose track of *what a cell means / which row it
belongs to*, and the columns/rows they want to compare are far apart. Counter both:

- **Freeze header rows and the identifier column** once the table exceeds the viewport, so the
  user never loses the row label or the column meaning while scrolled deep or wide.
- **Zebra striping, hairline borders, and hover row-highlight** to hold place as the eye tracks
  across a wide row. A subtle shadow on the frozen elements (so they read as floating above the
  data) reinforces orientation.
- **Right-align numbers**; align to the decimal so magnitudes line up and a wrong order of
  magnitude is visible at a glance. Left-align text labels. Use tabular/monospaced figures so
  digits sit in columns. Format consistently (thousands separators, consistent decimal places,
  parentheses or a consistent convention for negatives).
- **Make hiding and reordering columns low-friction** (not drag-only), discoverable, and
  **state-indicated** — e.g. show "15 columns hidden" so the user knows the view is customized.
  Let users bring the two columns they care about next to each other.
- **Let users hide/reorder individual rows and sort by any variable**, distinct from filtering.
  Bringing non-adjacent rows together is as important as columns.

### 3. View, edit, or add a single row

A wide financial row is painful to read/edit inline. Four patterns, with the finance default
called out:

- **Edit in place** — only for narrow tables; the editable row must look visually distinct so the
  user sees what's editable and can't fat-finger a change.
- **Modal popup — avoid for editing.** It covers the other rows, and users routinely reference
  neighboring records while editing (to recognize a reasonable value range rather than recall
  it). Blocking that reference is the exact wrong move for finance, where "is this number
  plausible vs. the line above" is how errors get caught.
- **Nonmodal side panel — the finance default.** It covers part of the table but leaves other
  rows visible for cross-reference while the user edits or inspects one. Use it for line-item
  drill-down, edit, and "view detail."
- **Accordion / expand-in-place row** — doesn't obscure the rest, good for a quick expand, but
  users don't re-collapse them (clutter builds) and it's poor for referencing non-adjacent rows.
  Fine for a lightweight peek; not for sustained editing.

### 4. Take action(s) on records

- **1–2 row actions:** show them inline, with labels (or icon+label). More than that inline gets
  crowded, tiny, and hard to hit (Fitts's Law), or forces a hover-gated menu that's undiscoverable
  and inaccessible.
- **Several row actions:** a per-row contextual (kebab) menu is acceptable **for secondary
  actions only** — never bury the primary or completion action (approve, post, "view source")
  there. Place the menu icon inside the row, adjacent to what it affects (see `ia-navigation.md`
  for the full menu rules).
- **Batch actions:** row-selection checkboxes + an action bar above/below the table, with a
  "Select All". This is the scalable pattern for operating on many records (bulk approve, bulk
  reclassify, bulk export) and keeps single rows uncluttered. For consequential bulk operations,
  show the affected count/selection before commit — error prevention scales with the batch size.

## Finance-specific table guidance

- **Totals and subtotals** are anchors — make them visually distinct (weight, a top hairline,
  slight ground shift) and keep them sticky/visible when scrolling a long statement so the reader
  always sees the number the rows roll up to.
- **Density is a feature for experts.** Offer a comfortable/compact toggle; default per role.
  Don't force whitespace-heavy "consumer" spacing on a controller reconciling 400 lines.
- **Expandable hierarchy rows** (statement → section → account → line) are common; **persist
  expand/collapse state** — auto-collapsing what a user deliberately opened is a regression (see
  `ia-navigation.md`, accordions). Consider an expand-all for experts who want the flat view.
- **The expand-to-detail control is a content reveal, not an action** — give it a distinct
  affordance (a caret, "View detail"), never a generic kebab icon.
- **Audit/status columns are not noise.** A status flag, an as-of date, a "tie-out" indicator may
  look like clutter to a minimalist but serve a real compliance/trust purpose. Keep them; the
  test is "does it serve this user's task or a legitimate control," not "is it the fewest pixels."
- **Comparison framing** — for actual-vs-budget / period-over-period, put the delta and the %
  change adjacent to the base, use the data-viz semantics from `DESIGN.md` sparingly (green
  positive, red breach; ghosted old value, accent for the new), and never let color be the *only*
  signal (accessibility + print).
- **Export / interop is a baseline, not a bonus.** Native Excel and PowerPoint export — plus
  copy-as-values and copy-visual — are near-universal expectations in FP&A workflows: users will
  pull the table into a model or a board deck regardless, so make export first-class and faithful
  (respect formatting, hidden/reordered columns, and the active filter state) rather than an
  afterthought. Coordinating cleanly with Excel/PowerPoint is part of the job, not a nice-to-have.

## Quick review pass for any table

- First column human-readable? Codes demoted?
- Numbers right-aligned, consistently formatted, tabular figures?
- Headers + identifier column frozen; zebra/hover to hold place?
- Active filter/sort state visible?
- Column hide/reorder low-friction and state-indicated?
- Row edit via side panel (not modal)? Cross-reference preserved?
- Primary/completion actions visible; only secondary ones in a kebab?
- Batch actions via checkboxes + action bar for multi-record ops?
- Totals distinct and sticky; expand state persisted?
- Excel/PowerPoint export first-class and faithful to formatting + filter state?
