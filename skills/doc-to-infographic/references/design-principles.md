# Design Principles

Distilled from infographic-design and cognitive-science research (Nielsen Norman
Group on effective infographics, mental models, and cognitive/mind/concept maps;
plus Marq, Canva, and Figma design guides). These are the *why* behind the
choices the skill makes. Read this when building a page and check against the
list at the end before delivering.

## 1. Match the form to the content

The single highest-leverage decision. The shape of the information should dictate
the shape of the visual:

- A **process** is a sequence → flow or numbered steps.
- A **timeline** is events against time → a track, often with swimlanes per owner.
- A **hierarchy** is a whole and its parts → a tree.
- A **concept map** is several ideas joined by *named* relationships (the edges are
  labeled with verbs/prepositions). Use it when the relationships matter as much
  as the nodes — e.g. "workstream → answers → decision question".
- A **mind map** is one central topic expanded into sub-topics (a tree with one
  root, unlabeled edges). Use it to break a single subject into its components.
- A **comparison** is options measured on shared attributes → aligned columns.
- A **weighting / scoring** is criteria with relative importance → ranked bars
  sized by weight.

NN/G's taxonomy is useful: *cognitive maps* are the umbrella (free-form, no rules);
*mind maps* are the simple one-root tree; *concept maps* add labeled relationships
and multiple parents. Don't force an enumeration of steps into a map — that's a
flow's job.

## 2. Anchor to a familiar mental model

People build understanding of something new by mapping it onto something they
already know ("Jakob's Law": users spend most of their time elsewhere, so they
arrive with expectations). Reach for the metaphor the reader already holds:

- Stages with go/no-go decisions → **gates on a track** (people know checkpoints).
- Value realized over time → **a pipeline filling up** or **phasing bars**.
- A screening that narrows → **a funnel**.
- Money/headcount built up from parts → **a waterfall / bridge**.
- Quality across dimensions → **a radar profile** (a shape you can compare at a
  glance).

The closer the visual sits to an existing mental model, the less the reader has to
decode and the faster the concept lands. When you invent a brand-new visual
convention, you owe the reader a clear legend.

## 3. Establish one clear visual hierarchy

The reader's eye needs an obvious entry point and an obvious path. Give each level
of information a distinct, consistent treatment:

- Page title (largest) → section takeaway heading → diagram label → caption / fine
  print (smallest).
- Size, weight, and color all reinforce the same hierarchy; don't let a decorative
  element outweigh the data.
- Within a diagram, the most important node/number should be the most visually
  prominent. Arbitrary sizing or random sequencing destroys the hierarchy and
  makes the message hard to find (a common, fatal mistake).

## 4. Lead with the takeaway (especially for executives)

Each section's heading should state the conclusion, not just name the topic.
"Diligence runs through six phase gates, each with a go/no-go decision" beats
"Phase Gates". The visual then supports that claim; the caption adds the one piece
of context the reader needs. Put the overall answer in an executive band at the
top, before any detail.

## 5. Keep a high data-ink ratio (Tufte)

Every visual element should carry meaning. Strip anything that doesn't:

- No drop shadows, gradients, glows, or textures used as decoration.
- No clip-art or illustrations that don't interpret the data. (NN/G's recurring
  failure case is a big decorative image stealing attention from the chart.)
- No gridlines, borders, or backgrounds that aren't doing a job.

Minimalism here is not austerity — it's removing noise so the signal is obvious.

## 6. Discipline with color

- **≤3 meaningful colors** over a neutral base (the template gives you an accent, a
  secondary, and semantic status colors). Three is a well-worn rule of thumb across
  every guide.
- Use color to **encode** — category, status, emphasis, sequence — not to
  decorate. If two colors don't mean two different things, use one.
- Anything color encodes needs a **one-line legend**.
- **Never rely on color alone.** Pair it with a label, icon, shape, or position so
  colorblind and low-vision readers (and anyone printing in grayscale) still get
  the message.
- Prefer shades/tints of your existing palette over adding new hues.

## 7. Typography and whitespace

- Choose **readable over decorative**. One clean sans for the body; reserve any
  display weight for the title only.
- Sentence case. Avoid all-caps blocks and never put a paragraph inside a diagram
  node — labels are a few words, detail goes in the caption or an expandable.
- Let it breathe. Whitespace between sections and around headings reduces the sense
  of overload and makes the page feel approachable. Crowding is the fastest way to
  make an infographic look amateur and feel unreadable.

## 8. Copy is not an afterthought

The text is half the infographic. Write captions deliberately:

- One takeaway sentence + at most two of support. Concise, scannable, objective.
- Say what to *notice* and why it matters — don't just restate the labels.
- Carry the source's caveats and hedges into the caption rather than dropping them.

## 9. Informational honesty

- Proportional encodings: bar lengths, areas, and timeline spans must be true to
  their values. Don't truncate or stretch an axis to exaggerate a difference.
- **Never invent data.** If the source has placeholders (`TBD`, `0`,
  `user-needed`), show the structure with empty slots — do not fill them with
  guesses. This matters acutely for financial, regulatory, and diligence content.
- Cite the source where the reader would want it (a small note, not clutter).

## 10. Accessibility

- Contrast: body text and meaningful marks must meet WCAG AA against their
  background.
- Semantics: real `<h1>…<h3>` headings, `alt` on images, `<title>` and `<desc>`
  on SVG, `aria-label` on icon-only controls.
- Don't encode meaning in color alone (see #6).
- Keep interactivity optional: the page must make full sense with nothing expanded
  and nothing hovered (progressive enhancement).

## 11. Find the relationship first, then encode it

**Before you render any set of items, ask what relates them — and draw *that*, not an
arbitrary row of cards.** A list of items almost always has a structure waiting to be
shown; finding it is the difference between an infographic and a glorified bullet
list.

The discipline comes from concept-map theory (Novak/Cañas; NN/g): the atomic unit
of an explanatory visual is the **proposition** — `node —linking verb→ node` — not
the node. Three consequences:

- **Every meaningful edge carries a verb** ("feeds", "gates", "owns", "requires",
  "escalates to"). An unlabeled arrow is barely better than no arrow: NN/g's line
  between a mind map (unlabeled, one parent, decorative) and a concept map
  (labeled, multiple parents, explanatory) is exactly the line between a card
  grid and an infographic. If you can't name the verb, you haven't earned the
  arrow — the "string map" of boxes joined by bare lines is a named anti-pattern.
- **Edges are typed, and types look different.** Sequence, causal dependency,
  ownership handoff, and feedback are different relationships; render them with
  distinct arrow classes (the template's `.e-seq` / `.e-dep` / `.e-handoff` /
  `.e-feedback`), not one uniform connector. In a swimlane, the lane-*crossing*
  arrows are the payload (each is an accountability transfer and a potential
  bottleneck) — make them visually distinct from within-lane steps.
- **Nodes are typed too.** Activity, output, outcome, decision, event, and actor
  are different things; don't render them as identical boxes. Carry causal
  chains through to the *outcome* an output serves (the logic-model /
  strategy-map rule) — a diagram that stops at "report produced" has dropped the
  relationship the executive actually cares about.

Look for these relationships in any list:

- **Category / type** — group or cluster by kind (revenue types vs risk types; cost
  vs revenue synergies). Don't interleave different kinds at random.
- **Sequence / timing** — order them on a track or timeline (integration comes
  *after* close; diligence precedes the bid). Position then encodes "what comes
  before what".
- **People / groups** — map items to the departments or owners that hold them, and
  show overlap and hubs (the *theme ↔ owner matrix*), not a flat list.
- **Dependency / causation** — connect what feeds what (*converging inputs*, a flow,
  a concept map).
- **Magnitude / weight** — rank or size by it (weighted scorecard, phasing bars).

A flat grid of cards in arbitrary order is the **default to avoid** — it discards the
most useful thing the visual could carry: how the items relate. When you catch
yourself about to list cards, pick the relationship above that fits and draw it. (In
the M&A material, for example: revenue-vs-risk by *type*, integration by *timing*,
themes by the *departments* that own them.) And after the first pass, make one
deliberate **cross-link sweep**: relations *between* sections/branches (a register
risk that gates a playbook decision, one workstream consuming another's output)
are the most-skipped, highest-value edges — a page with zero cross-links usually
means under-extraction, not a simple document.

Once you've chosen a relationship to show, three cheap moves turn it into a polished
infographic rather than a flat card-list:

- **Colour with meaning.** Assign one hue per *category* (the template's `--cat-*`
  palette: finance, risk, legal, tech, people, revenue) and use it consistently on
  that category's lanes / nodes / chips. Colour should let the reader group and
  distinguish at a glance — not decorate. Recurring category colours get a one-line
  legend. (This is still "≤ a controlled set + neutrals", not a rainbow — each
  colour earns its place by encoding a category.) The decision-bands pattern
  (green→amber→red by severity) is the model to imitate.
- **Icons for actors and objects.** People, teams, documents, money, systems,
  risk, time — give them an icon (the template's sprite + `.ichip`) so a node is
  recognisable before it's read. An icon chip + a two-word label beats a sentence in
  a box. Pick the icon that matches the *thing*, and keep the icon style consistent.
- **Arrows show order; don't assume it.** Adjacency (left-to-right, top-to-bottom)
  implies sequence but doesn't *show* it. Put an actual arrow between steps and let
  it draw on (the `.draw` motion class, or the marching-ant connector) so the eye is
  led through the flow. This is what makes the decision-diamond flow land.

Default away from "a grid of cards". If you find yourself listing items as plain
cards, ask whether colour-coding, an icon per item, an arrow between items, or a
different form entirely (flow, matrix, bands) would carry the meaning better.

## Common mistakes to avoid

- Decorative visuals that outshine the data.
- Distorted or truncated scales.
- Text bolted on at the end, in long unstructured paragraphs.
- Unclear hierarchy / arbitrary sizing.
- **Flat grids of plain text cards with no colour, icons, or connectors** — the most
  common "it's a bit boring" failure. Encode (colour/icon/arrow) or change the form.
- Colour as decoration, or color as the only signal (always pair with label/icon).
- Trying to visualize everything instead of the few structures that matter.
- Inventing numbers to make a framework "look finished".

## Pre-delivery checklist

Run through this before presenting the file:

- [ ] **Spine**: there's a clear overall takeaway up top; sections follow a logical
      order that serves one decision/story.
- [ ] **Form fit**: each visual is the right form for its content (no process
      crammed into a table, no comparison hidden in prose).
- [ ] **Selectivity**: 4–8 visuals, each earning its place; nothing visualized just
      because it could be.
- [ ] **Takeaway-first**: every section heading states a conclusion; captions say
      what to notice.
- [ ] **Hierarchy**: obvious entry point; consistent title/section/label/caption
      sizing.
- [ ] **Color**: meaningful colors + neutrals; legends where color encodes;
      never color-only.
- [ ] **RELATIONSHIP GATE (hard fail, not a vibe check)** — do all four, with
      evidence, before delivery:
      1. *Per-section table.* List every visual section and the named relationship
         it encodes (feeds / gates / owns / precedes / groups / ranks / drives). A
         section whose answer is "none — it's items in a grid" FAILS unless it is
         the headline-KPI band or deliberate prose.
      2. *Zero unconnected elements.* Count elements that participate in no
         encoded relationship (no arrow, labeled edge, lane, matrix cell, rank, or
         band ties them to anything). The count must be 0 outside the KPI band.
         Colour-coding alone is NOT an encoded relationship.
      3. *Verbs on directional edges.* Every causal/dependency edge carries a verb
         label (`.edge-lbl` or `.redge` `data-verb`); branch edges are labeled with
         their outcomes. Bare lines between boxes FAIL.
      4. *Edge types differentiated.* Sequence vs dependency vs handoff vs feedback
         use visually distinct arrow classes; swimlane crossings are distinct from
         within-lane arrows.
      Categories carry colour + icons; processes have explicit (animated) arrows
      showing order.
- [ ] **Honesty**: no invented numbers; placeholders shown as empty; scales
      proportional; source labels preserved; caveats carried into captions.
- [ ] **Self-contained**: one `.html` file, renders with no external dependency.
- [ ] **Interactivity is additive**: page is complete with nothing expanded/hovered;
      hover and expand enhance rather than hide essentials.
- [ ] **Accessible**: AA contrast, real headings, SVG `<title>`/`<desc>`, alt text.
- [ ] **Renders**: opened and visually verified; no overflow, overlap, or broken
      layout.
