# Review, evaluation & maturity

Read in **review mode** (auditing an existing screen) and **evaluate mode** (testing a flow's
learnability before shipping). Sources: NN/g "Cognitive Walkthroughs", "Hostile Error Messages",
the heuristics and mistakes lists, and "Informal UX Maturity".

## Review mode — the audit checklist

Work the screen against this list. For each item, return **pass / fail with the specific evidence
on the screen** and, for fails, the rule and a concrete fix — the way the research does ("this is
X mistake; the fix is Y"), not "this feels off." Order the final defect list by severity.

**The three pillars (finance-critical — check first):**
- Drill path: can the user reach every summary number's underlying detail, with strong scent at
  each step, without losing place (no pogo-sticking, state preserved)?
- Confirmation: after each consequential action, is there unambiguous proof — what happened, when,
  what changed — and does a lifecycle state reflect it?
- Lineage: for each displayed number, can the user see source, filter/sort state, and as-of basis?

**Cognitive load & clarity:**
- Icons carry text labels? Codes sit behind human-readable anchors?
- Choices minimized but not fragmented (primary set fully visible; only rare/advanced deferred)?
- Sensible defaults; prior input reused rather than re-entered?
- Any element that's pure decoration adding load without serving a task or a real business/
  compliance purpose?

**Data display (if a table/grid is present — cross-check `data-tables.md`):**
- Human-readable first column; numbers right-aligned and consistently formatted?
- Headers/identifier frozen; zebra/hover to hold place; active filter state visible?
- Row edit via side panel (not modal); batch actions via checkboxes; expand state persisted?

**IA & actions:**
- Primary/completion actions visible (not in an overflow menu); destructive actions separated?
- Kebab menus only for secondary actions, placed by what they affect, labeled?
- Content-reveal (drill) uses a distinct affordance, not an action icon?
- Consistent patterns/placement across screens; no redundant entry points to the same thing?
- Menus and hidden interactions keyboard- and screen-reader-operable (WCAG/508)?

**States, errors & feedback:**
- Loading scaled to duration (percent/steps beyond 10s, not a bare spinner)?
- Empty / partial / stale / error / success states all designed and honest?
- Error messages plain-language, specific, actionable, input-preserving; non-errors not styled red?
- Undo / version history / restore available where the user invests heavy work?

**Brand (when `FRAME.md`/`DESIGN.md` present):**
- Conforms to the visual tokens — color, type, spacing, radius, one-shadow, gold-as-pinpoint?

## Evaluate mode — the cognitive walkthrough

Use this to test a **novel, high-stakes, or unfamiliar** flow's learnability without users —
exactly the finance screens this skill targets (a new drill-down, a first-time forecast
submission). Skip it for standard, convention-following flows (login, generic settings) where
it's overkill; those get a heuristic pass instead.

**Setup:** define the specific task, the exact correct action sequence, and the target user
(usually a Learner — a finance expert new to *this* system). For finance flows, frame the task as
a real scenario (investigate a threshold-breaching variance, respond to a rate move, close a
locked period) rather than a bare click-path — scenario-based reasoning surfaces the high-stakes
decision points that plain task-completion testing misses. Then walk the sequence one action at
a time. At each step, answer the four questions:

1. **Will the user try to achieve the right goal?** Do they know this is the step to take, given
   what they're trying to accomplish?
2. **Will the user notice the correct control is available?** Is the affordance visible and
   present when needed?
3. **Will the user associate the control with the goal?** Does its label/appearance make clear it
   produces the outcome they want (information scent)?
4. **After acting, will the user see that progress was made toward the goal?** Is there feedback
   confirming the step worked?

**Any "No" fails that step** — record it as a defect with the question it failed. Note that Q4 is
the confirmation pillar formalized: "will the user see that progress was made" is literally the
"did it happen?" test. A flow that leaves the user unsure whether their action registered fails
Q4, no matter how good the rest looks.

Cognitive walkthroughs ≠ heuristic evaluations: walkthroughs assess **learnability** of a
targeted task from a new user's view; heuristic evals assess **general usability** against
guidelines comprehensively. They're complementary — use the walkthrough for the hard novel path,
the heuristic checklist above for overall coverage.

## Informal UX maturity — keeping the practice alive

For building UX quality inside a finance/FP&A org with no dedicated UX budget, work informally
rather than waiting for headcount:

- **Treat UX quality as a living system, not a one-time grade.** It can silently regress between
  sessions/releases — build periodic light checkpoints, not a single assessment.
- **Low-cost tactics that need no executive buy-in:** log usability signals as you notice them;
  run a short four-factor retrospective after a release; keep a quarterly traffic-light snapshot;
  pilot changes with a single team before rolling out.
- **Don't over-assess.** Reassessing too often creates box-checking and superficial fixes; only
  reassess after you've acted on the last round's findings.
- **When to go formal:** leadership wants objective proof; a merger/reorg/major pivot is underway;
  or you need hard numbers to justify UX headcount or budget. Otherwise, informal is enough.

## A note on measurement

When asked whether a change worked, reach for CASTLE (see `framework.md`), not engagement
metrics: task efficiency, error rate (including repeated-frustration loops, which raw counts
miss), learnability (did Learners reach competence), cognitive load, advanced-feature usage,
satisfaction. Usage counts are meaningless when the software is mandatory.
