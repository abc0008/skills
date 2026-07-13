---
name: doc-to-infographic
description: >-
  Turn a markdown or Word document explaining a business concept, process,
  framework, or strategy into a polished, self-contained, animated HTML infographic /
  visual explainer — diagrams paired with concise text so dense structure lands
  fast. Trigger on "visualize this", "make a diagram / flowchart", "turn
  this into an infographic", "explain this visually", "make a one-pager / explainer",
  "make this doc board-ready", or any heavy process, framework, or workflow doc
  someone wants made clear. Also for turning structured business content — phase
  gates, workstreams, scorecards, timelines, swimlanes, decision flows, org maps,
  risk registers — into HTML diagrams (process flows with inline decisions,
  swimlanes, phase × function matrices, decision trees, hierarchies, scorecards,
  decision bands, converging and backbone diagrams). Output is one self-contained,
  reduced-motion-safe .html file. Prefer over generic HTML, chart, or slide help when
  the goal is to EXPLAIN visually, not plot a dataset or build a deck.
---

# Doc to Infographic

Convert a document that *explains* something into a self-contained HTML page that
*shows* it: a sequence of diagrams and visuals, each paired with a short
explanatory passage, that a reader understands faster than the prose.

## What "good" means here

An infographic is not a chart. It is **visual structure + explanatory text that
reinforce each other** (Nielsen Norman Group). A bare diagram leaves the reader
guessing; a wall of prose buries the point. The job is to carry the same meaning
in less time by doing three things well:

1. **Match the visual form to the shape of the content.** A process wants a flow;
   a comparison wants columns; a weighted assessment wants ranked bars; a web of
   related ideas wants a concept map. Picking the right form is 80% of the value.
2. **Anchor abstract ideas to a familiar mental model.** Readers understand new
   concepts by mapping them onto things they already know (a pipeline, a funnel, a
   scorecard, gates on a track). Reaching for the right metaphor is what makes a
   concept *click* rather than merely display.
3. **Lead with the takeaway, support with the visual, finish with one line of
   context.** Especially for an executive reader: say the "so what" first.

Quality comes from clarity and the right form — never from decoration. A clean
two-color diagram that's instantly legible beats a busy, colorful one every time.

## Workflow

### 1. Ingest the source

- Markdown / text / pasted content: read it directly.
- Word (`.docx`): run `scripts/extract_doc.py <path>` to get clean markdown
  (preserves headings and tables). Read its output.
- If the user pasted content into the chat, use that — don't ask for a file.

### 2. Find the spine, then select what's worth visualizing

Read the whole document first. Identify the **one decision or story it serves**
(e.g. "should we acquire this target, at this price?"). That spine determines the
order and what earns a visual.

Then segment the content into **4–8 high-value visual sections**. Resist the urge
to visualize everything — a page with twenty diagrams is as unreadable as the
original wall of text. A section earns a visual when it has *structure worth
seeing*: a sequence, a hierarchy, a set of relationships, a comparison, a
weighting, a set of stages with timing. Pure narrative or caveats stay as prose.

For a very long source (e.g. a 1,000-line framework), do not transcribe it. Pull
the spine and the handful of structures that carry the most meaning, and let the
rest live as brief connective text or an "what's inside" list.

### 3. Extract the relationship inventory — BEFORE choosing any visual

This step is mandatory and it produces a **written artifact** (a scratch block in
your working notes — never "in your head"). It is what separates an infographic
from a wall of cards: the atomic unit of an explanatory diagram is the
**proposition** — `Entity —VERB→ Entity` — not the entity (Novak's concept-map
rule). For each candidate section, write:

1. **Focus question** — one line: what question does this page answer, for whom?
2. **Entities** — the concepts / actors / deliverables in play (a parking lot).
3. **Propositions** — every relationship the source states or implies, as a
   labeled sentence: `credit review —feeds→ risk rating`, `Legal —owns→ VDR
   requests`, `Phase 2 gate —requires→ scorecard ≥ threshold`. Common verbs:
   feeds, produces, gates, requires, precedes, owns, hands off to, escalates to,
   drives, offsets, groups with. **If you can't name the verb, you haven't earned
   an arrow.**
4. **Node types** — tag each entity: *activity / output / outcome / decision /
   event / actor*. Different types must not render as identical boxes, and causal
   chains carry through to the **outcome** the doc says an output serves — never
   stop at "report produced" (logic-model rule).
5. **Ownership changes** — mark every step whose owner differs from the previous
   step. Handoffs are the highest-value relationship in a cross-functional
   process (they're where bottlenecks live) and get visually distinct treatment.
6. **Cross-link pass** — deliberately hunt for relations *between* sections or
   branches (a risk in the register that gates a decision in the playbook; a
   workstream output another workstream consumes). Cross-links are the most
   skipped, highest-value relationships; a diagram set with zero cross-links is
   usually an under-extraction, not a simple document.

Hard rules that fall out of the inventory:

- An entity with **no proposition** does not get its own box — fold it into a
  caption or cut it.
- A section whose inventory is genuinely relationship-free is either prose or a
  headline-KPI band. It **never** becomes a grid of cards.
- Every arrow drawn later must trace to a proposition here; every proposition
  must surface somewhere (edge, lane crossing, matrix cell, rank, band).

### 4. Choose the visual form — keyed by the dominant relationship

Route on the **relationship the inventory surfaced**, not on what the items look
like. **Process flow is the most common request** — for the full flowchart family
and standard symbols, go to `references/flowcharts.md`. For everything else,
`references/diagram-catalog.md` has ready-to-paste code.

| The dominant relationship is… | Use this form | Where |
| --- | --- | --- |
| A precedes B (sequence, with real go/no-go branches) | Process flow / gated process flow | flowcharts.md |
| A precedes B **and** owners change along the way | Swimlane (handoff arrows distinct) | flowcharts.md |
| A decision splits into outcome paths | Decision tree (with pros/cons) | flowcharts.md |
| Events trigger events (causality chain) | Event-storming flow | flowcharts.md |
| Inputs → activities → outputs → **outcomes** | Logic model (carry to outcome) | flowcharts.md |
| Stages gated by criteria | Phase / gate track | catalog #2 |
| Things positioned against time | Timeline (often with owner lanes) | catalog #3 |
| Whole decomposes into parts (no cross-links, no sequence) | Hierarchy / synoptic tree | catalog #4 |
| Many-to-many named relations, multiple parents | Concept map (labeled edges) | catalog #5 |
| Several inputs feed one output / decision | Converging inputs | catalog #5b |
| X drives Y across layers (capability→process→customer→financial) | Causal cascade / strategy map | catalog #14 |
| One or two links carry the point; a full diagram is overkill | Proposition rail (`.rel` row) | template |
| Options measured on shared attributes | Comparison columns (+ verdict row) | catalog #6 |
| Criteria weighted → a score → a call | Weighted scorecard **feeding** decision bands | catalog #7 + #9 |
| Profile across dimensions | Radar / spider | catalog #8 |
| Value falls into ranges → prescribed actions | Decision bands | catalog #9 |
| Amounts realized across periods | Phasing bars (Gantt-lite) | catalog #10 |
| Items positioned on two independent axes | 2×2 matrix / quadrant | catalog #11 |
| Quantity narrows or accumulates | Funnel / waterfall | catalog #12 |
| Output loops back to input | Cycle | catalog #13 |
| **No relationship at all** (verified headline KPIs only) | Stat cards — the only card grid allowed | template |

Rules of engagement:

- **Stat cards are the exception, not a peer.** They're licensed only by a
  section whose inventory is empty of relations. Related numbers get a relational
  form.
- **Hybrids are encouraged when two relations co-exist.** One form per section is
  a floor, not a ceiling: swimlane × time axis (owner + sequence), scorecard →
  decision bands (weight + consequence), matrix with a flow overlay, timeline
  with converging feeders. The phase × function matrix in flowcharts.md is the
  house example.
- When two forms could work, pick the simpler one. When the source has no real
  numbers (frameworks, templates, placeholders), visualize the **structure** —
  never invent figures (see Guardrails).

For a **bespoke or complex diagram**, or when the user already has an asset in a
design tool (or asks to "build it in Figma / Mermaid / Lucid / etc."), you can
author or fetch it in a connected diagram MCP and inline it as SVG. The HTML page
is always the final surface — see `references/external-diagrams.md`. Default to the
native components above; reach for an external tool only when it clearly pays off.

### 5. Build the page

Start from `assets/template.html` — copy it to your output file. It carries the
modern-corporate design system, the light interactivity (hover elevation,
expand/collapse, sticky section nav, scrollspy), print/PDF styles, and accessible
defaults already wired up. You fill in content; you do not re-derive CSS.

Populate it as a short visual narrative:

- **Header**: title, a one-sentence dek that states the document's purpose, and
  light meta (source, date) if useful.
- **Executive summary / takeaway band** up top: 2–4 sentences or a few stat cards
  giving the answer before the detail.
- **Each visual section**: a one-line takeaway heading → the diagram (from the
  catalog) → a 1–3 sentence explainer that says what to notice and why it matters.
  Keep the diagram itself sparse; push secondary detail into an expandable block.
- **Section nav** so a reader can jump around.
- **Encode every proposition from the step-3 inventory.** The relationships are
  already written down — now they must all surface visually: as a labeled edge
  (SVG `.e-dep`/`.e-seq`/`.e-handoff` + `.edge-lbl` verb, or the HTML `.rel`
  proposition row), a lane crossing, a matrix cell, a rank, or a band. Give each
  category a meaningful colour (the `--cat-*` palette) and an icon (the sprite +
  `.ichip`). **Differentiate arrow classes by relation type** — sequence, causal
  dependency, ownership handoff, and feedback must not all look like the same
  line, and directional/causal edges carry a verb label. An arrow with no
  nameable verb goes back to the inventory. See
  `references/design-principles.md` §11. In particular:
  - **When the content has phases AND functions, use the phase swimlane matrix**
    (`flowcharts.md`) — "who does what, when", deal flowing left→right through gates.
    It almost always beats a flat parallel grid (which hides the timing).
  - **Keep decisions inside the flow.** For a multi-phase gated process, use the
    *gated process flow* component — show every phase in sequence and let the real
    go/no-go decisions branch *inline* (diamond marker + outcome chips). Don't carve
    the decisions into a separate section away from the steps they belong to. Reserve
    diamonds for genuine branch points (one or two); ordinal phases stay as nodes.
    This is an infographic, not an engineering flowchart — don't symbol-ize every box.
  - **Show relationships, not isolated cards.** When several factors drive one
    outcome (e.g. decision dimensions → the call), use the *converging inputs →
    decision* component. When one entity runs through the whole process and others
    feed it (a through-line), use the *spine / backbone* component (timing + the band
    + feeder arrows). When deliverables/outputs should show category + owner +
    convergence at once, use the *grouped convergence* component — not an owner-tagged
    list.
  - Map list items that belong to people/functions to their owner (icon + colour)
    with the *owner-mapped items* component, not plain bullets. When ownership
    **overlaps** (co-owned items, one function is a hub), use the *theme ↔ owner
    matrix* so the relationships and the hub are visible — not a flat list.
  - Give headline **stat cards** a category colour + icon (the template example shows
    this), and give a weekly/phase **timeline** its sub-deliverables and a time axis —
    don't leave it a lazy one-line-per-step row.
  - The animated decision-diamond flow, the likelihood/impact risk matrix, and the
    colour-coded decision bands are the bar — imitate them.
- **Motion encodes the relationship it sits on.** Wrap each diagram in
  `class="reveal"` (or `data-stagger` in flow order); add `class="draw"` to SVG
  connectors so the path builds in reading order; `data-count` on KPI numbers.
  Then reach for the meaning-carrying effects where the relationship warrants:
  a `.flow-dot` traveling a dependency edge (shows direction), `[data-branch]`
  with `.br-on`/`.br-off` on a decision (chosen path stays lit, rejected dims),
  `.handoff-mark` on swimlane crossings (flags ownership transfer), and
  `[data-trace]`/`data-node`/`data-link` on dense maps (hover a node → its
  connections light up, the rest dims). All are built into the template and
  disabled under reduced-motion and print. One or two effects per section — see
  `references/motion.md`. If the user wants a shareable **video clip** of a
  diagram (for a deck), motion.md covers the optional MP4 export via HyperFrames;
  the self-contained HTML page stays the primary deliverable.

Components in the catalog use the template's CSS variables (`--accent`, `--ink`,
etc.), so they inherit the theme automatically. Merge any component-specific CSS
into the page's single `<style>` block — the output must remain one self-contained
`.html` file with no external dependencies.

### 6. Apply the design principles

Read `references/design-principles.md` and hold the output to it. The essentials:

- **One clear visual hierarchy**: distinct sizes for title, section takeaway,
  diagram label, and caption. The eye should always know where to start.
- **≤3 meaningful colors** over a neutral base. Use color to *encode* (status,
  category, emphasis) — never as decoration. Every color that carries meaning gets
  a one-line legend.
- **High data-ink ratio**: remove anything that doesn't carry meaning. No drop
  shadows-as-decoration, no gradients-for-flair, no clip-art.
- **Generous whitespace** and consistent alignment; let sections breathe.
- **Readable type**, sentence case, never walls of text inside a diagram.
- **Explanatory text is not an afterthought** — write the captions deliberately,
  concise and takeaway-first.

### 7. Self-check, then deliver

Before handing it over, open the file and verify it renders (use the sandbox: load
the HTML, take a screenshot, or at minimum validate the structure). Then run the
checklist at the bottom of `references/design-principles.md` — including the
**relationship gate**: build the per-section table (section → relationship encoded
→ how) and count elements that participate in no encoded relationship; the count
must be zero outside the KPI band. Fix anything that fails. Save the final `.html`
to the outputs folder and present it.

## Guardrails (the ones that matter most for business / finance docs)

- **Never fabricate numbers.** These documents are often frameworks with `TBD`,
  `0%`, or `user-needed` placeholders. Show the *structure*, the weights, and the
  phasing percentages that are actually given. If a figure isn't in the source,
  it does not appear in the visual — represent it as an unfilled slot or omit it.
  Inventing a plausible-looking number in a bank diligence diagram is a serious
  failure, not a helpful flourish.
- **Preserve the source's labels and meaning.** Don't relabel "revenue
  dis-synergy" as "revenue loss" or smooth over hedged language. Caveats in the
  source ("do not infer regulatory conclusions") belong in the visual's caption.
- **Don't distort scale.** Bars, areas, and timelines must be proportional to the
  values they represent. A truncated or stretched axis that exaggerates a
  difference is dishonest.
- **Self-contained and portable.** One `.html` file, no external scripts or fonts
  required to render. (A web font via `<link>` is acceptable only as a progressive
  enhancement with a system-font fallback.)
- **Accessible.** Sufficient color contrast, never color as the *only* signal,
  meaningful `alt`/`aria` text and `<title>`/`<desc>` on SVG, real headings.

## Files in this skill

- `assets/template.html` — the self-contained scaffold (design system + light
  interactivity + motion layer + print styles). Copy this first; build into it.
  Ships the **relationship primitives**: the `.rel` proposition row, typed SVG
  edge classes (`.e-seq`/`.e-dep`/`.e-handoff`/`.e-feedback` + `.edge-lbl`), and
  the meaning-carrying motion utilities (`.flow-dot`, `[data-branch]`,
  `.handoff-mark`, `[data-trace]`).
- `references/flowcharts.md` — **the flowchart/process-diagram deep dive**: the
  type taxonomy, the five characteristics, standard symbols, and animated paste-
  ready components (symbol flowchart, swimlane, decision tree, event storming,
  logic model). Start here for any process/flow request.
- `references/diagram-catalog.md` — the catalog of the other visual forms: when to
  use each, its structure, and ready-to-paste HTML/SVG/CSS that matches the
  template. Includes the proposition rail (#0), the causal cascade / strategy map
  (#14), and the scorecard→decision-bands composite.
- `references/design-principles.md` — the principles distilled from infographic and
  cognitive-mapping research, plus the pre-delivery checklist.
- `references/motion.md` — the in-page animation layer (classes/attributes,
  reduced-motion) and the optional HyperFrames MP4 export path.
- `references/external-diagrams.md` — bringing a diagram authored in Figma, Mermaid,
  tldraw, Canva, Lucid, etc. into the page as inline SVG (or base64 PNG), and
  reconciling it with the theme, accessibility, and motion.
- `references/sources.md` — the infographic / flowchart / cognition research the
  guidance is distilled from (links + what each contributed).
- `assets/examples/` — **two worked examples** (`input.md` + the finished
  `output.html`) that set the quality bar and show the favourite components (gated
  flow, phase × function matrix, spine, theme↔owner matrix, convergence, risk
  matrix). Its `README.md` also explains exactly **how the in-page motion works**
  (pure CSS/JS — no HyperFrames/build step). Open the `output.html` files to study
  the patterns before building.
- `scripts/extract_doc.py` — convert `.docx` (and other formats) to clean markdown
  for ingestion.
