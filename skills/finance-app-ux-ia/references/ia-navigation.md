# Information architecture, navigation & menus

Read for structural decisions: where things live, how users move, how menus and actions are
placed, and how to validate a taxonomy. Sources: NN/g's IA Study Guide, "Reduce Redundancy",
"Accordions for Complex Content", and "Designing Effective Contextual Menus (10 Guidelines)".

## IA fundamentals

- **IA ≠ navigation.** IA is the underlying structure (how content is organized and labeled);
  navigation is its visible manifestation. Get the structure right first, then express it.
- **Information scent is the core mechanic.** Users "follow their noses" — they judge each link
  by how likely it seems to lead to their goal. Every label, tab, and drill affordance either has
  scent or doesn't. Weak scent is the root cause of most "I can't find it."
- **Depth is not the enemy; ambiguity is.** The "no more than 3 clicks" rule is false — click
  depth doesn't predict abandonment when each step has strong scent. This is the structural
  license for deep drill-down to line-item detail: go as deep as the data, keep every step legible.
- **Findability vs. discoverability.** Findability = the user seeking a known thing (a specific
  report). Discoverability = stumbling onto the unexpected (a feature they didn't know existed).
  Finance tools skew heavily to findability — optimize labels and search for "I know what I want,
  help me get there."
- **Labels earn clicks.** Specific, user-language labels (the finance term, not the internal
  system name); avoid vague CTAs ("Learn more", "Options"), unnecessary parallel phrasing, and
  over-conversational tone.

### Navigation patterns that fit finance apps

- **Left-side vertical navigation** scales well for broad IAs and is easy to scan — a good fit for
  a multi-module finance suite (e.g. Forecasting · RM Pro Forma · Mortgage LOS · ACE Home).
- **Keep global navigation persistent**; don't rely on search alone. Sticky but unobtrusive
  headers; breadcrumbs for "you are here" on deep drill paths; local navigation to expose sibling
  items within a section.
- **Hamburger/hidden nav hurts discoverability** on desktop — don't hide primary navigation behind
  it when there's room to show it.
- **Avoid audience-based top-level splits** ("For Analysts" / "For Executives") as the primary
  scheme — it often degrades usability because users don't self-classify reliably. Prefer
  task/subject organization, and handle roles via view/permission filtering instead.

## Polyhierarchy & cross-references (dimensional finance data)

Financial data is inherently multi-dimensional: one transaction legitimately belongs under
account, cost center, vendor, period, and entity. Don't force a single "true" taxonomy, and don't
duplicate whole nav paths.

- **Polyhierarchy / cross-listing** is the sanctioned way to let one item appear in multiple
  categories. Let a GL line be reachable by account *and* by cost center.
- **Limited cross-reference links** at the right points prevent "garden-pathing" (following a
  plausible-but-wrong path until giving up). But cap them: too many cross-references make it
  unclear where you are and what your options are. Link only the alternatives most useful at that
  location.

## Consistency & the anti-redundancy discipline

- **Duplicating a feature/link/decision multiplies complexity without proportional benefit.**
  Users can't tell a duplicate from a new thing, so they waste effort re-deciding. Don't expose
  "export" (or "drill to detail", or "add") from three places "in case users miss it."
- **Fix visibility at the source, not with a second copy.** When usability testing shows users
  miss a control, the fix is to reposition it, strengthen its label, or reduce competing clutter —
  not to add a duplicate. Carry this discipline into review: when the proposed fix is "add another
  button/link/menu entry," push back and ask whether repositioning or clarifying is the real fix.
- **One interaction pattern = one meaning, everywhere.** Same icon, same behavior, same place.
  Inconsistency (same action with different words; the same control in different locations;
  elements that move between screens) confuses even multi-year expert users and erodes trust.
- **Personalization = reduction, not addition** in expert/dense contexts. Role- or task-based view
  filtering (show a controller what a controller needs now) beats exposing every path to everyone.

## Menus & action placement — the three-tier vocabulary

Use this vocabulary explicitly when placing actions:

- **Hamburger (☰) → global/main navigation only.** Never for item-level actions.
- **Kebab (⋮) / meatball (⋯) → secondary, contextual, item-specific actions only.** Never for
  global actions, never for a single action, never to expand content.
- **Primary / frequent / completion actions → their own visible control**, not hidden in any menu.

The 10 contextual-menu guidelines, condensed to what bites in finance:

1. **Secondary, noncritical actions only.** Never bury a frequent or completion-critical action
   (approve, post, submit, "view source") behind an overflow icon.
2. **Place the menu next to what it affects** (proximity = predictability) — inside the row, by
   the relevant cell.
3. **Make the trigger visible** — sufficient size/contrast, not hover-only (hover-gated actions
   are undiscoverable and inaccessible).
4. **Group only truly related actions**; keep global and element-specific actions out of the same
   menu; optionally surface a key action outside the overflow to raise scent.
5. **Consistent representation and behavior** — the same icon does the same thing everywhere;
   never "expand here, popup there, side-panel elsewhere."
6. **Label or tooltip ambiguous triggers** ("Row actions", "Message options") — overflow icons
   carry low scent; give them words.
7. **Icons for actions, not content expansion.** A "show detail / show lineage" reveal gets its
   own affordance (caret, "View detail") — never a kebab. (Load-bearing for drill-down UI.)
8. **Don't hide a single action behind a menu** — show it directly (and if a standard icon exists
   — trash, flag — use it).
9. **Don't use the hamburger for contextual actions**, or the kebab for global ones — their
   meanings are established; swapping breaks mental models.
10. **Keyboard + screen-reader accessible.** For regulated finance software this is a hard
    requirement (WCAG / Section 508), not polish — and it doubles as power-user efficiency.

## Accordions & progressive disclosure of content

Accordions cut scrolling but add interaction cost (every heading is a decision) and hide content,
diminishing awareness of it. Apply deliberately:

- **Use accordions only when users need a *few* key sections, not most/all content.** If they
  need most of it, show it all — "relevance trumps page length," and users scroll fine when
  content is relevant and well-formatted (eyetracking debunks "users don't scroll").
- Don't fragment content users intend to consume in one sitting (e.g. a full statement's line
  items). If a page is genuinely too long, consider splitting into a few digestible pages rather
  than over-fragmenting into tiny accordion slices.
- **If you do use accordions:** allow multiple sections open at once, and **persist open/closed
  state** — never auto-collapse what the user opened.
- **Mini-IA use** — collapsed section headers (Assets / Liabilities / Equity) can serve as a
  scannable local table of contents for first-time orientation, *while* experts get an expand-all
  or flat-table alternative rather than clicking through every time.

## Validate the taxonomy before you ship it

Don't eyeball a new report/menu structure — test it:

- **Card sorting (discovery)** — learn how analysts/controllers naturally group financial
  concepts. Open sort (they name categories) to build a new IA; closed sort (sort into your
  categories) to validate one.
- **Tree testing (validation)** — test a *proposed* structure for findability without visual
  design as a confound: can users locate key items (a specific report, a specific setting) from
  the labels alone? Fast and iterative; do it before build, not after complaints.
