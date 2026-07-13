# Forms, inputs, errors & system states

Read for any data entry, validation, or when a screen has to represent loading / empty / error /
success / partial states. Sources: NN/g "Hostile Error Messages", the error/feedback/default
items from "Top 10 Application-Design Mistakes", heuristics #5/#9, and the waits guidance.

## Inputs & defaults

- **Give fields sensible defaults; reuse prior input.** Defaults speed entry, demonstrate a valid
  answer, and steer novices to a safe choice. In finance, default to the obvious prior state:
  last period's inputs, the user's cost center, the org hierarchy, the current scenario. Don't
  make an analyst re-enter what the system already knows.
- **Avoid "Select one" as a dropdown default** when a most-common value exists — pre-select it.
- **Use steppers for numeric fields near a common value** (increment/decrement while still
  allowing a typed override) to cut interaction cost.
- **Recognition over recall** — show the human-readable name next to any code the user must pick;
  offer type-ahead against readable labels, not raw IDs.
- **Match the real world** — field labels and units in the user's finance vocabulary, in a
  natural order; don't surface internal system field names.

## Validation timing — don't accuse before there's an error

The most common way validation turns hostile is firing too early:

- **Validate on field-exit (blur) or on submit — not on every keystroke, and not on focus.**
  Turning a field red before the user has finished (or before they've typed anything) is the
  hostile pattern; it accuses them of an error they haven't made.
- **One required-field indicator, not three.** An asterisk (or one clear cue) is enough. Stacking
  asterisk + red border + inline message simultaneously is visual noise — especially costly in a
  dense finance form/grid where every extra cue competes with real data.
- **Prevent errors up front** where you can: constrain inputs to valid ranges/formats, offer a
  preview of the effect before commit, and confirm before destructive/irreversible steps.

## Error messages — helpful, not hostile

The rule the sources converge on: an error message must say **what went wrong, why, and how to
fix it, in plain language, without losing the user's work.**

- **Plain language, no bare codes.** "Something went wrong. Contact your administrator" is the
  named dead-end anti-pattern — no diagnosis, no path forward. If a code must appear (for support),
  pair it with a human explanation.
- **Be specific and constructive** — name the exact problem and the next action ("The period is
  locked for FY2027 Q1; reopen it or post to the current period"). When the fix can't be stated
  in the message, **link directly to the relevant help/doc** from the error itself.
- **Preserve user input.** Never clear a form or lose entered data because of a validation or
  submission error — re-render what they typed, mark only what needs fixing.
- **Errors are a teachable moment** — users are unusually motivated to read an explanation exactly
  when something breaks; spend a clear sentence, don't waste it.
- **Don't style non-errors like errors.** Reserve red + warning iconography for genuine critical
  problems. A neutral/informational status ("No exceptions found", "Saved") gets neutral styling
  and an info icon — otherwise experts stop trusting the color-coding on financial screens, which
  is where red actually needs to mean something.

## System states — design all of them, not just the happy path

A finance screen lives in several states. Each needs an explicit, honest design:

- **Loading** — scaled to duration (see the response-time thresholds): instant under ~1s; spinner
  2–10s; **percent-done or a step list beyond 10s**, highly salient. For known layouts, a skeleton
  of the coming table reads faster than a blank spinner. Never leave the user unsure whether the
  app is working or hung.
- **Empty** — say why it's empty and what to do next ("No variances above threshold this period"
  is a *result*, not an error — style it neutrally; "No data loaded yet — run the forecast to
  populate" is an onboarding cue with an action). Distinguish "empty because zero results" from
  "empty because nothing's happened yet."
- **Partial / stale** — when data is filtered, as-of an older sync, or mid-recalc, say so on the
  surface (ties to the lineage pillar). A number the user can't tell is stale is worse than a
  visible "as of 09:14, recalculating…".
- **Error** — per the message rules above; also show whether work was preserved and how to retry.
- **Success** — per the confirmation pillar in `disclosure-lineage-confirmation.md`: what happened,
  when, what changed, link to results; modal/persistent after a long wait; reflected in any
  lifecycle state (SUBMITTED / APPROVED / …).

## Two placement rules worth repeating here

- **Separate destructive from confirming actions.** Save/Finish must not sit adjacent to
  Delete/Discard/Cancel — a slip on the last step of a long financial workflow can wipe the work.
  Space them, and make the destructive one require a beat (a confirm, an undo window).
- **Make the editable scope obvious.** In an editable grid, show what's currently editable (cell
  vs. row vs. table) via background/contextual cues, so the user never edits the wrong scope.
