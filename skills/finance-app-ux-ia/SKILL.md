---
name: finance-app-ux-ia
description: >-
  Use this skill when designing, building, structuring, or reviewing any UI for a complex B2B
  financial-services web app — the FP&A, banking, and fintech tools used by analysts,
  controllers, and CFOs. Reach for it for dashboards, data tables and grids, reports,
  reconciliations, variance and forecasting tools, approval and close flows, forms,
  navigation/IA, drill-down, and loading/empty/error/success states — where the hard problems
  are dense tables, drilling from a summary number to its underlying line item, showing where a
  number came from (lineage), and confirming an action actually happened. Trigger even when the
  user doesn't say "UX" — e.g. "design this screen", "build this dashboard", "lay out this
  variance table", "is this flow any good", or when they share a React/Next.js finance component
  or screenshot. Also for cognitive walkthroughs, heuristic reviews, and IA/taxonomy decisions.
  Grounded in Nielsen Norman Group and Laws of UX research.
metadata:
  author: alex-cardell
  version: "1.0"
  source: "Synthesized from 20 Nielsen Norman Group + Laws of UX articles"
---

# Finance-app UX & information architecture

Design and review UIs for complex financial-services apps whose users are finance professionals
(FP&A analysts, controllers, CFOs) doing high-stakes, repeat, expert work — not consumers.
Consumer-app instincts are the main failure mode here. Optimize every screen for three pillars:

1. **Simple flow, deep on demand** — a calm default path, but the expert can always drill from a
   summary number to the underlying line item without losing their place.
2. **Confirmation it happened** — after any consequential action (save, submit, post, approve,
   run, close), give unambiguous proof of what changed and when. Silent or vague completion is a
   trust failure in finance.
3. **Lineage / provenance** — for any number, the user can see its source, filter state, and
   as-of basis. These users audit numbers; hiding the trail fails them.

Detailed, sourced guidance lives in `references/`. Load files on demand per the routing below —
don't read them all up front.

## First: defer to the brand layer

If `FRAME.md` and `DESIGN.md` exist in the project, read them before rendering anything. They own
visual tokens (color, type, spacing, radius, the one-shadow rule, gold-as-a-pinpoint) and win on
anything visual; this skill owns behavior and IA. Read `references/brand-integration.md` when you
render visuals in a project that has those files — it covers how the layers compose and the real
product vocabulary to use in examples.

## Route the task → load the reference

Read only the file(s) the task actually touches:

- Table, grid, ledger, register, statement, comps sheet, or variance view →
  `references/data-tables.md`.
- Drill-down, "where did this number come from," or any save/submit/run/close flow →
  `references/disclosure-lineage-confirmation.md`.
- Navigation, menus, taxonomy, where things live, accordions, or action placement →
  `references/ia-navigation.md`.
- Data entry, validation, error messages, or empty/loading/error/success states →
  `references/forms-errors-states.md`.
- Reviewing/critiquing an existing screen, or evaluating a flow's learnability →
  `references/review-and-evaluation.md`.
- Framing a new or unfamiliar problem, or when you need the underlying model (the five
  complexity types, the three user types, CASTLE metrics) → `references/framework.md`.
- Rendering visuals in a project that has `FRAME.md`/`DESIGN.md` → `references/brand-integration.md`.

## Gotchas — finance-specific, non-obvious, wrong-by-default

These are the corrections that separate finance UX from consumer UX. Apply them without being
asked; each reference file expands the reasoning.

- **Hide actions, not content.** Hiding a *secondary action* in a kebab menu is fine; hiding
  *content the user came to read* (statement line items collapsed "to reduce clutter") is not. A
  "show lineage / expand to detail" control is a **content reveal, not an action** — give it its
  own affordance (a caret, "View detail"), never a generic overflow icon.
- **Modal for confirming, side panel for editing.** Don't edit a table row in a modal — it blocks
  cross-referencing the other rows, which is how finance users sanity-check a value. Use a
  nonmodal side panel. Do use a non-auto-dismissing modal for a post-wait success confirmation.
- **Never bury a primary or completion action** (approve, post, submit, export, "view source") in
  an overflow menu — overflow is for secondary actions only. Keep destructive actions (Delete)
  spaced apart from confirming ones (Save); a slip on a financial record is expensive.
- **Human-readable label leads; demote codes, don't delete them.** The GL/account/transaction
  code is needed for lineage — keep it, but let a readable name anchor the first column.
- **Show real progress past 10 seconds.** A spinner is fine for 2–10s; beyond 10s show
  percent-done or a step list, never a bare spinner — model runs, consolidations, and closes
  routinely exceed this.
- **Don't over-abstract (Tesler's caveat).** Minimalism that hides the calculation or source from
  an expert is a failure, not a win — provenance is deferred detail, never deleted detail.
- **Depth is fine; ambiguity is the enemy.** Deep drill-down is good when every step has strong
  information scent (the "3-click rule" is a myth). Preserve scroll, selection, and expand state
  on the way back — no pogo-sticking between list and detail.
- **Reuse prior input as defaults** (last period, cost center, org hierarchy) instead of making
  users re-enter what the system already knows.
- **Icons need text labels**, and **audit/status columns are not noise** — they serve a real
  control/compliance purpose even when a minimalist read calls them clutter.
- **Excel/PowerPoint export is a baseline**, not a bonus — users pull the table into a model or a
  board deck regardless; make export faithful to formatting and the active filter state.

## Definition of done (and the fast review pass)

Check every finance screen against this. State each item pass/fail with the specific on-screen
evidence, not "looks good." The full checklist is in `references/review-and-evaluation.md`.

- [ ] Every summary number drills to its detail, with strong scent at each step and place preserved.
- [ ] Every consequential action gives unambiguous confirmation — what changed, when.
- [ ] Every number shows its source, filter state, and as-of basis.
- [ ] Primary/completion actions are visible (not in overflow); destructive actions are separated.
- [ ] Icons carry labels; codes sit behind human-readable anchors.
- [ ] Menus and hidden interactions are keyboard- and screen-reader-operable (a WCAG/508 hard
  requirement in regulated finance); color is never the only signal.
- [ ] Long operations (>10s) show real progress, not a bare spinner.
- [ ] Loading, empty, error, and success states are all designed — not just the happy path.
- [ ] Conforms to `FRAME.md`/`DESIGN.md` visual tokens when present.

## Deliver to the mode

- **Build** — the design or code, plus a one-line note on which patterns you applied and why.
- **Review** — a defect list ordered by severity; each defect names the rule it breaks and a
  concrete fix, not just "this is bad."
- **Structure IA** — the proposed structure plus how you'd validate it (card sort to discover how
  users group concepts, tree test to validate findability before build).
- **Evaluate** — the cognitive-walkthrough output: the four questions answered per step, any "No"
  flagged as a failure.

Be specific and cite the principle, so each recommendation is defensible rather than taste.
