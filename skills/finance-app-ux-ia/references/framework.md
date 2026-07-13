# Framework — the mental model behind every finance-UX decision

This is the *why* layer. Read it when framing a new problem or when you need to justify a
recommendation past "it looks better." Sources are Nielsen Norman Group's "Designing Complex
Applications" series and Laws of UX; the finance framing is applied.

## 1. Is this actually a complex application?

NN/g defines a complex application by six traits. A finance/FP&A/banking tool hits all six —
which is why consumer-app instincts mislead here:

- Broad, unstructured, or open-ended goals ("understand why NII moved", not "buy this item").
- Nonlinear workflows (analysts jump between console, cube, review, export — not a funnel).
- Specialized, highly trained users (they know accounting; they don't know *your system* yet).
- Large data sets (GL detail, driver × line-item matrices, multi-period actuals + forecast).
- High-stakes / high-value tasks (a mis-posted number flows into a board deck).
- Multi-role handoff (Finance Liaison → FP&A Manager → Corporate Planning → Executive).

Naming which of these dominate a given screen tells you where the design effort goes. A
high-stakes multi-role handoff screen needs airtight confirmation and audit trail; a large-data
exploration screen needs table craft and drill-down.

### The five kinds of complexity (diagnostic lens)

"Context" is too vague. NN/g's complex-application-design *framework* separates five layers so
you can name what's actually hard:

- **Integrative** — the tool must stitch together other systems/data (legacy GL, source
  systems, Excel). Maps directly onto lineage problems.
- **Information** — sheer volume, density, and interconnection of the data.
- **Intention** — the user's goal is fuzzy or evolves mid-task.
- **Environmental** — where/how the work happens (interruptions, long batch waits, dual monitors).
- **Institutional** — org politics, regulation, audit, "that's how it's always been done."

Institutional complexity is a real hazard: legacy patterns persist because practitioners feel
they can't fight them. When "that's how it's always been done" — not a user need — is driving a
UI decision, flag it.

## 2. Tesler's Law — the backbone principle

*Law of conservation of complexity:* for any process there is a core of complexity that cannot
be designed away; it can only be **shifted** between the user and the system. Good design makes
the system absorb as much as possible.

- Absorb on the system side: smart defaults, reused prior input, deterministic engines, derived
  values — so the user doesn't carry the complexity.
- The explicit caveat, verbatim: **"Take care not to simplify interfaces to the point of
  abstraction."** In finance this is load-bearing: an expert must be able to audit a number.
  Over-hiding the calculation or source is a failure, not minimalism. This is exactly why the
  **lineage pillar** exists — provenance is deferred detail, not deleted detail.
- **Complexity bias** (self-check): people over-value complex solutions because complexity reads
  as expertise. If a screen defaults to an unconditional complex control (e.g. a 12-field
  advanced filter always visible), treat that as a sign the user's real need isn't understood
  yet — spend more time on the problem, not more UI.

Progressive disclosure is Tesler's Law made concrete: show the important thing by default, keep
the rest one clearly-labeled step away. The top-level number is the simple default; its
calculation/source chain is the deferred detail.

## 3. Design for three user types at once

Any finance product serves all three simultaneously. Designing only for the loud power user
(the Legend) is the classic enterprise mistake.

- **Legacy** — long-tenured; efficient in the *old* way; fears losing productivity more than
  fears change. Protect them with spatial stability, migration paths, and not moving their chrome.
- **Legend** — power user; gives the most (and loudest) feedback, which can over-steer the
  roadmap toward niche depth. Serve them with accelerators — keyboard shortcuts, saved/custom
  views, bulk actions, dense modes — *without* letting their asks fork the whole UI.
- **Learner** — a domain expert (real accountant/analyst) who is new to *this system*. Often
  misdiagnosed as a "training problem." Serve them with primary labeled paths, recognition cues
  (names not codes), and in-context help — not dense upfront documentation.

The reconciliation: primary labeled methods for Learners, accelerators layered on top for
Legends, stable geometry for Legacy. Same UI, not three UIs.

## 4. Reducing cognitive load (the mechanisms)

Working memory is finite; every element and decision spends it. The three root causes are **too
many choices, too much thought required, and lack of clarity.** Levers:

- **Progressive / staged disclosure** — defer rarely-used or advanced settings to a secondary
  level revealed on demand (e.g. an advanced field appears only after a related checkbox).
- **Eliminate unnecessary tasks** — editable defaults and reuse of prior input. Finance form:
  default to last period's inputs, the user's cost center, the org hierarchy — don't make them
  re-enter what the system already knows.
- **Recognition over recall** — show a readable name/label, a hover preview, the human meaning of
  a code — so users recognize rather than decode.
- **Minimize choices, but display them as a group** — cut decision paralysis, but never fragment
  or partially hide the primary choice set (users take the visible subset for the whole).
- **Icons with caution** — icons need inferential decode; pair with text labels. (Three sources
  converge here — treat it as a default.)
- **Don't over-cut** — "avoid unnecessary elements" carries its own caveat: don't overvalue
  simplicity at the cost of clarity.

## 5. The classic heuristics, in finance terms

Nielsen's ten heuristics apply fully to complex apps. The ones that bite hardest in finance:

- **Visibility of system status** — long waits are normal (model runs, consolidations); show real
  progress, not a generic spinner — percent-done or a step list once a wait passes ~10 seconds.
- **Match the real world** — use the user's finance vocabulary and real-world conventions, not
  internal system jargon or inverted metaphors.
- **User control and freedom** — heavy cognitive investment means undo / version history /
  restore-to-previous matter more, and make "learning by doing" safe.
- **Consistency** — internal (same icon/action = same meaning everywhere) and external (Jakob's
  Law: even daily power users spend most of their time in *other* apps, so outside conventions
  still apply).
- **Error prevention** — real-time preview before commit (show the effect of a formula/allocation
  change before it's applied).
- **Recognition over recall**, **flexibility** (accelerators for experts alongside labeled paths
  for novices), **aesthetic/minimalist** (staged disclosure; strip gratuitous graphics),
  **help users recover from errors** (plain-language, actionable), and **in-context help** over
  forced tutorials.

## 6. Measuring whether it worked — use CASTLE, not HEART

For compulsory workplace software, engagement/adoption/retention metrics are near-meaningless
(people use it because they must). The fitting frame is **CASTLE**: Cognitive load, Advanced-
feature usage, Satisfaction, Task efficiency, Learnability, Errors. When someone asks "how do we
know the redesign helped," point at these — especially task efficiency, errors, and whether
learners reached competence — not at time-on-page or logins. Watch errors beyond raw counts:
repeated frustration loops (the same correction over and over) are invisible to simple error
instrumentation but are real usability failures.

## The six domains this model spans

1. Frame the complexity (§1–2).
2. Design for the three users (§3).
3. Reduce cognitive load without hiding what experts need (§4–5).
4. Structure the information.
5. Display dense data and confirm long operations.
6. Handle errors, evaluation, and maturity.

Domains 4–6 have their own pattern files; `SKILL.md` routes to them. This file is the "why"
behind all six — read it when framing a new problem, not as a router.
