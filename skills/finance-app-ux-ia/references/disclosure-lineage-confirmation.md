# The three pillars — progressive disclosure, lineage, and confirmation

The finance-specific heart of this skill. Read for any drill-down, "where did this number come
from," or save / submit / post / run flow. Sources: Tesler's Law and progressive-disclosure
guidance (Laws of UX), NN/g's "Designing for Long Waits and Interruptions", data-tables filter
guidance, and the accordions/contextual-menu distinction.

## Pillar 1 — Simple flow, deep on demand (progressive disclosure & drill-down)

The default view is calm; the expert can always go deeper. The discipline is deciding *what*
defers and *how* the descent works.

**What to defer vs. keep:**
- Keep by default: the numbers and columns the primary task needs; the primary and completion
  actions; audit/status context the role relies on.
- Defer behind a clear control: rarely-used advanced settings, secondary actions, the
  calculation/source chain behind a number, deep line-item detail *when most users don't need
  most of it*.
- The gate, from the accordions research: **if users need most of the content, show it all** —
  hide only when they need a few pieces. Don't accordion-hide statement line items a controller
  reviews every time; do collapse a rarely-opened "advanced assumptions" block.

**How the descent should work (drill-down):**
- **Depth is fine; ambiguity is the enemy.** The "3-click rule" is a myth — users go deep
  happily when each step has strong information scent. So every drill affordance must clearly
  predict what's below it (a labeled "View detail", the line's name, "3 source transactions"),
  not a bare chevron or a mystery icon.
- **Don't lose the user's place.** Avoid "pogo-sticking" — bouncing between a list and a detail
  view while holding state in working memory. Preserve scroll position, selection, and expand
  state on the way back. A **nonmodal side panel** for the detail (see `data-tables.md`) keeps the
  summary visible while the user inspects the line — the ideal drill pattern for dense tables.
- **The drill control is a content reveal, not an action** — give it its own affordance (an
  expand caret, "View detail", a row click into a side panel), never a kebab/overflow icon (which
  means "actions"). Conflating the two is a named failure mode.
- **Persist expand/collapse state** across refresh and navigation; auto-collapsing what an expert
  opened is a regression.

**Choosing the disclosure widget:**
- *Inline expand / accordion row* — a quick peek at a few items; persist state, allow multiple
  open, offer expand-all for experts.
- *Nonmodal side panel* — sustained inspection/edit of one item while referencing others. The
  finance default for line-item drill.
- *Dedicated detail page* — when the detail is itself a rich workspace (a full transaction, a
  full sub-schedule). Give it a breadcrumb back so the user keeps orientation.
- *Not a modal* — modals block cross-reference; reserve them for confirmations (Pillar 3).

## Pillar 2 — Lineage / provenance (where did this number come from?)

Finance professionals audit numbers. A UI that can't answer "where did this come from?" fails
them. Provenance is itself an application of progressive disclosure: the number is the simple
default; its trail is deferred detail, revealed on demand — never deleted (Tesler's "don't
abstract away needed complexity").

Build lineage from these concrete elements:

- **Visible data-state at all times.** The user must know, without asking, whether a figure
  reflects filtered / sorted / partial data or the complete set, and the **as-of / basis**
  (e.g. `Actual vs FCST_2026Q1_PRIOR`, the period, the scenario, the FX date). A total with an
  invisible filter behind it is a trust bomb. Surface active filters and the basis near the
  number, not buried in a settings panel.
- **Drill to source.** Every derived number should let the user step toward its inputs: summary →
  the formula/driver → the contributing line items → the source records/system. Show the
  calculation in mono when it clarifies (e.g. `max(0, pre-tax income) × tax rate`), and name the
  driver linkages (the driver × line-item matrix with dots at the linkages, per `DESIGN.md`).
- **Show the derivation, not just the result.** For a variance or an adjusted figure, expose
  base → adjustments → result, each attributable. Never present a moved number without a path to
  why it moved.
- **Cite the source system.** When a value comes from an upstream system/import, say which one
  and when it was last synced — that's integrative complexity made visible.
- **Let users annotate the trail.** Allow open-ended notes/comments attached to a figure, an
  adjustment, or a model element — why it was changed, who requested it, what assumption it rests
  on — shown in the context of the workflow, not a separate log. This is both external memory
  across interruptions and an audit-trail/provenance record; don't force analysts out to a side
  spreadsheet to track their own reasoning.
- **Credibility rule for generated commentary.** If the product auto-writes variance narratives
  or executive summaries, it must stick to the data even when the data undercuts the headline —
  never cherry-pick supporting numbers. Headline-first, each claim cited to its figure/source.

## Pillar 3 — Confirmation that it happened

After any consequential action, the user gets unambiguous proof. Silent or vague completion is a
trust failure in finance, where the user can't just "check later" without cost.

**Immediate feedback, scaled to duration (the classic 0.1s / 1s / 10s response-time limits):**
- Under ~0.1s: feels instant — no indicator needed; just reflect the new state.
- Up to ~1s: the user's train of thought stays unbroken; a simple state change suffices even
  though the delay is perceptible.
- ~2–10s: hold attention with a spinner / wait animation.
- **Over 10s: a spinner is not enough** — show an explicit percent-done bar, or, when a
  percentage can't be estimated, a **list of completed and remaining steps** ("Aggregating
  drivers… Running tax… Writing forecast cube…"). Keep the indicator highly salient and
  discoverable. This applies to every long finance operation: model runs, consolidations,
  recalcs, close steps, large exports.

**Post-action confirmation (the contract):**
- For anything consequential, confirm **what happened, when, and what changed** — not a bare
  "Success." A good completion dialog reports **start time, stop time, total elapsed**, what
  occurred (records created / updated / skipped, rows affected), and a **link to the results**
  (the new records, the log, the error detail).
- **After a long wait, the confirmation must be modal / require explicit dismissal** — the user
  likely stepped away or switched tasks; an auto-dismissing toast will be missed. (This is the
  one place modals are right — contrast with editing, where they're wrong.)
- **Let long processes run in the background** so the user keeps working, precisely *because* the
  salient completion notice will bring them back. Don't trap them in an idle wait.
- **State transitions are confirmation too.** Where the domain has a lifecycle, moving through it
  *is* the proof the action landed. Bank Analysis uses **NOT STARTED → IN PROGRESS → SUBMITTED →
  APPROVED → FP&A LIVE → LOADED**; show the current state prominently, show who acted and when,
  and make the transition visible on the record and in any list/console view. A "Submitted"
  badge with an actor and timestamp is stronger confirmation than a toast.
- **Preserve work across interruptions.** Autosave, "last saved" timestamps, and recoverable
  drafts mean an interruption or error never silently loses entered data. Surface the last-saved
  state so the user trusts it.
- **Speed re-entry after an interruption.** Surface a clearly labeled "recent" / "continue where
  you left off" list immediately (not buried behind an overview screen), with previews for
  slow-loading or ambiguously-named items. FP&A analysts juggle many models, entities, and
  periods and lose real time reopening the wrong one.

**Confirm before, as well as after:**
- **Preview before commit** for actions with downstream consequences (a formula/allocation change,
  a re-forecast) — show the effect before it's applied. This is error prevention, the cheapest
  kind of confirmation.
- **Make heavy work reversible.** Undo, version history, and restore-to-previous matter more when
  the user has invested hours in a model or workflow — and they make learning-by-doing safe for
  the Learner (see `framework.md` §3, §5).
- **Separate the confirming action from the destructive one** — Save must not sit next to
  Delete/Discard; a slip on a financial record is expensive.

## How the three pillars interlock

The same drill-down machinery serves all three: disclosure defers the detail, lineage *is* the
deferred detail (source/calc/filter), and confirmation reports what a drilled action did. Design
them together — a line-item side panel that shows the value, its derivation and source (lineage),
lets you edit with a preview (confirm-before), and on save shows what changed with a timestamp
and a state transition (confirm-after) is the finance UX ideal in a single surface.
