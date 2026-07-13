# Diagram Catalog

Ready-to-paste visual forms for the `doc-to-infographic` skill. Every snippet uses
the CSS variables defined in `assets/template.html` (`--accent`, `--ink`, `--line`,
etc.), so it inherits the theme automatically. Paste a component into a section,
then replace the placeholder content. Merge any component `<style>` rules into the
page's single `<style>` block.

These are starting points, not a cage. Adapt structure, counts, and labels to the
source. The goal is always the right form for the content (see
`design-principles.md`), legible and honest.

**Route by the dominant relationship, not by the item type.** Ask what *connects*
the items, then pick the form that draws that connection: sequence → process flow;
cause/effect across layers → causal cascade or concept map; shared attributes →
comparison; one thing feeds many → converging inputs; pure decomposition →
hierarchy; ownership hand-off across roles → swimlane. A grid of cards encodes *no*
relationship — reach for it only when the items are genuinely a flat unordered set
(a legend, a glossary). If any relationship holds between the items, draw it.

> **Process flow / flowcharts live in `flowcharts.md`.** That file covers the
> flowchart family in depth — symbol flowcharts with decision diamonds, swimlanes,
> decision trees, event storming, logic models, plus standard symbols and the five
> characteristics. The basic linear process flow below (#1) is the simplest case;
> reach for `flowcharts.md` whenever the process branches, crosses roles, or needs
> proper symbols. Components in both files share the template's motion classes
> (`.reveal`, `data-stagger`, `.draw`) — see `motion.md`.

## Contents

0. [Proposition rail](#0--proposition-rail-the-cheapest-relational-form) — 2–4 nodes joined by verbs
1. [Process flow](#1-process-flow) — steps in a sequence
2. [Phase / gate track](#2-phase--gate-track) — stages with go/no-go decisions
3. [Timeline with swimlanes](#3-timeline-with-swimlanes) — activity over time
4. [Hierarchy / synoptic tree](#4-hierarchy--synoptic-tree) — a whole and its parts
5. [Concept map](#5-concept-map) — ideas joined by named relationships
6. [Comparison columns](#6-comparison-columns) — options on shared attributes
7. [Weighted scorecard](#7-weighted-scorecard) — criteria ranked by weight
8. [Radar profile](#8-radar-profile) — a profile across dimensions
9. [Decision bands](#9-decision-bands) — value ranges mapped to actions
10. [Phasing bars](#10-phasing-bars) — benefit/cost realized across periods
11. [2×2 matrix](#11-2x2-matrix) — items placed on two axes
12. [Funnel / waterfall](#12-funnel--waterfall) — narrowing or building quantities
13. [Cycle](#13-cycle) — a repeating loop
14. [Causal cascade / strategy map](#14--causal-cascade--strategy-map) — cause in one layer drives effect in the next

General rules for every component: keep node labels to a few words; put detail in
the caption or an expandable; give any color that encodes meaning a legend; add
`<title>`/`<desc>` to SVGs; never invent numbers.

---

## #0 — Proposition rail (the cheapest relational form)

**Use when** one or two links carry the whole point and a full diagram is overkill
— a two-to-four-node chain where the *verbs* are the content ("credit review →
**feeds** → risk rating → **gates** → pricing"). Also use it as a **relationship
strip** placed directly above or below another component, to state the causal spine
in one line before the detail. It's as cheap to paste as a card row, but unlike a
card row it encodes direction and relation. Each link gets a `data-verb`; use
`.redge.seq` for a neutral "then" step, `.redge.handoff` (dashed) when ownership
transfers between the two nodes.

```html
<div class="rel reveal">
  <span class="rnode"><span class="ichip risk"><svg class="ic"><use href="#ic-file"/></svg></span>Credit review</span>
  <span class="redge" data-verb="feeds"><i class="shaft"></i></span>
  <span class="rnode"><span class="ichip fin"><svg class="ic"><use href="#ic-target"/></svg></span>Risk rating</span>
  <span class="redge" data-verb="gates"><i class="shaft"></i></span>
  <span class="rnode"><span class="ichip rev"><svg class="ic"><use href="#ic-coins"/></svg></span>Loan pricing</span>
</div>
<!-- handoff variant: ownership transfers between the two nodes -->
<div class="rel reveal" style="margin-top:12px">
  <span class="rnode">Deal team</span>
  <span class="redge handoff" data-verb="hands off"><i class="shaft"></i></span>
  <span class="rnode">Integration office</span>
</div>
```

<p class="note">The verb is the payload. If you can't name the relation between two
nodes, they don't belong on a rail — use a card or a list instead.</p>

---

## 1. Process flow

**Use when** content is an ordered sequence of steps with no branching (e.g. a
seven-step diligence spine, an onboarding flow). Horizontal for ≤5 steps; switch
to vertical (stack the items, arrows pointing down) for more.

```html
<style>
  .flow{display:flex;gap:0;align-items:stretch;overflow-x:auto;padding:4px 0}
  .flow .step{flex:1 1 0;min-width:150px;background:var(--bg);border:1px solid var(--line);
    border-top:3px solid var(--accent);border-radius:var(--radius-sm);padding:14px 16px;
    margin-right:26px;position:relative;box-shadow:var(--shadow)}
  .flow .step:last-child{margin-right:0}
  .flow .step::after{content:"";position:absolute;right:-22px;top:50%;width:18px;height:2px;
    background:var(--line)}
  .flow .step:last-child::after{display:none}
  .flow .n{font-size:12px;font-weight:700;color:var(--accent)}
  .flow .t{font-weight:600;margin:4px 0 4px;font-size:15px}
  .flow .d{font-size:13px;color:var(--muted)}
</style>
<div class="scroller"><div class="flow" role="list">
  <div class="step" role="listitem"><div class="n">01</div><div class="t">Regulatory path</div><div class="d">Map filings & public-interest factors</div></div>
  <div class="step" role="listitem"><div class="n">02</div><div class="t">Credit & portfolio</div><div class="d">Marks, CECL, concentrations</div></div>
  <div class="step" role="listitem"><div class="n">03</div><div class="t">Deposits & funding</div><div class="d">Runoff, beta, CDI</div></div>
  <div class="step" role="listitem"><div class="n">04</div><div class="t">Compliance</div><div class="d">Exams, BSA/AML, CRA</div></div>
</div></div>
```

---

## 2. Phase / gate timeline

**Use when** stages run over time and each ends in a decision (the classic "phase
gate"). Render it as a horizontal timeline — each phase a node with an icon,
category colour, week label, and objective, joined by animated arrows, with a gate
pill on each. **Pair the final gate with the *decision gate* component (see
`flowcharts.md`)** so the go/no-go branch is shown graphically, not just labelled.
This has the depth, flow, icons, and colour a plain card track lacks. (For a
function × phase view, prefer the *phase swimlane matrix* in `flowcharts.md`.)

```html
<style>
  .ptl{display:flex;align-items:stretch;overflow-x:auto;padding:6px 0}
  .ptl .ph{flex:0 0 auto;width:158px;background:var(--bg);border:1px solid var(--line);border-top:3px solid var(--c);
    border-radius:var(--radius-sm);padding:13px;margin-right:36px;position:relative;box-shadow:var(--shadow)}
  .ptl .ph:last-child{margin-right:0}
  .ptl .ph .wk{font-size:11px;font-weight:700;color:var(--c);text-transform:uppercase;letter-spacing:.03em}
  .ptl .ph .ichip{width:34px;height:34px;font-size:19px;border-radius:9px;margin:8px 0}
  .ptl .ph .t{font-weight:600;font-size:14px} .ptl .ph .d{font-size:11.5px;color:var(--muted);margin-top:2px}
  .ptl .ph .gate{display:inline-block;margin-top:9px;font-size:10.5px;font-weight:600;color:var(--warn);background:var(--warn-soft);padding:2px 8px;border-radius:99px}
  .ptl .ph .subs{display:flex;flex-direction:column;gap:4px;margin:8px 0 2px}
  .ptl .ph .sub{font-size:11px;color:var(--ink);background:var(--panel);border-radius:6px;padding:4px 8px;display:flex;gap:6px;align-items:center}
  .ptl .ph .sub::before{content:"";width:5px;height:5px;border-radius:50%;background:var(--c);flex:none}
  .ptl .axis{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--muted);margin-bottom:6px}
  .ptl .ph::after{content:"";position:absolute;right:-32px;top:50%;width:24px;height:2px;transform:translateY(-50%);
    background:repeating-linear-gradient(90deg,#9aa7b6 0 6px,transparent 6px 11px);background-size:22px 2px;animation:ptlm 1.1s linear infinite}
  .ptl .ph::before{content:"";position:absolute;right:-10px;top:50%;transform:translateY(-50%);border-left:7px solid #9aa7b6;border-top:5px solid transparent;border-bottom:5px solid transparent}
  .ptl .ph:last-child::after,.ptl .ph:last-child::before{display:none}
  @keyframes ptlm{to{background-position:22px 0}}
  @media (prefers-reduced-motion:reduce){.ptl .ph::after{animation:none}}
</style>
<div class="axis"><span class="ichip ink" style="width:24px;height:24px;font-size:14px;border-radius:6px"><svg class="ic"><use href="#ic-clock"/></svg></span><span>Weekly cadence — each phase ends in a gate before the next begins</span></div>
<div class="scroller"><div class="ptl reveal" data-stagger>
  <div class="ph" style="--c:var(--cat-fin)"><div class="wk">Phase 0 · wk 0</div><span class="ichip fin"><svg class="ic"><use href="#ic-flag"/></svg></span><div class="t">Setup</div>
    <div class="subs"><span class="sub">VDR access</span><span class="sub">Kick-off meeting</span><span class="sub">Begin procedures</span></div><span class="gate">gate → VDR review</span></div>
  <div class="ph" style="--c:var(--cat-fin)"><div class="wk">Phase 1 · wk 1</div><span class="ichip fin"><svg class="ic"><use href="#ic-target"/></svg></span><div class="t">Requests out</div>
    <div class="subs"><span class="sub">Doc &amp; question lists</span><span class="sub">Memo template</span></div><span class="gate">gate → lists issued</span></div>
  <div class="ph" style="--c:var(--cat-risk)"><div class="wk">Phase 2 · wk 2–3</div><span class="ichip risk"><svg class="ic"><use href="#ic-file"/></svg></span><div class="t">Review &amp; meet</div>
    <div class="subs"><span class="sub">VDR review</span><span class="sub">Targeted meetings</span><span class="sub">Issue log</span></div><span class="gate">gate → follow-ups</span></div>
  <div class="ph" style="--c:var(--cat-rev)"><div class="wk">Phase 3 · wk 4</div><span class="ichip rev"><svg class="ic"><use href="#ic-trend"/></svg></span><div class="t">Draft memo</div>
    <div class="subs"><span class="sub">Finalize findings</span><span class="sub">Quantify synergies</span></div><span class="gate">gate → risk / opportunity</span></div>
  <div class="ph" style="--c:var(--ink)"><div class="wk">Phase 4 · wk 5</div><span class="ichip ink"><svg class="ic"><use href="#ic-check"/></svg></span><div class="t">Decide</div>
    <div class="subs"><span class="sub">Resolve final-round</span><span class="sub">LOI / bid support</span></div><span class="gate">gate → bid / no-bid</span></div>
</div></div>
```

---

## 3. Timeline with swimlanes

**Use when** activities play out over time, optionally by owner. Columns are time
periods; the header row is the timeline; rows can group deliverables vs activities.

```html
<style>
  .tl{display:grid;gap:10px}
  .tl .row{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}
  .tl .hd{font-size:12px;font-weight:700;color:var(--accent);text-align:center;
    padding-bottom:6px;border-bottom:2px solid var(--accent-soft)}
  .tl .cell{background:var(--panel);border-radius:var(--radius-sm);padding:10px 11px;font-size:12.5px;color:var(--ink)}
  .tl .cell .k{display:block;font-weight:600;margin-bottom:3px}
</style>
<div class="scroller"><div class="tl">
  <div class="row">
    <div class="hd">Week 0</div><div class="hd">Week 1</div><div class="hd">Week 2</div>
    <div class="hd">Week 3</div><div class="hd">Week 4</div><div class="hd">Week 5</div>
  </div>
  <div class="row">
    <div class="cell"><span class="k">Kick-off</span>VDR access, instructions</div>
    <div class="cell"><span class="k">Requests</span>Doc & question lists, memo template</div>
    <div class="cell"><span class="k">Review</span>Workstreams submit requests</div>
    <div class="cell"><span class="k">Meetings</span>Targeted follow-ups, issue log</div>
    <div class="cell"><span class="k">Draft memo</span>Quantify synergies & costs</div>
    <div class="cell"><span class="k">Decision</span>Final memo, LOI/bid support</div>
  </div>
</div></div>
```

---

## 4. Hierarchy / synoptic tree

**Use when** showing a whole broken into parts, or reporting/ownership lines (e.g.
working groups under a diligence office) — and **the relation is pure
decomposition**: no cross-links between children, no sequence among them, no shared
children. The parent→child line must be *drawn*, not implied by proximity. **Gate:**
if a child reports to two parents, or children depend on each other, this is the
wrong form — use the concept map (#5) instead; if the children are a flat unordered
set with no parent, they're just cards.

Draw the connectors with a CSS tree (each node emits a stub down; a horizontal rule
joins the row to the root), so the parent→child relation is literally on the page.
Color-code by category, icon each node, reveal in sequence.

```html
<style>
  .htree{display:grid;gap:0;justify-items:center}
  .htree .root{display:inline-flex;align-items:center;gap:10px;background:var(--accent);color:#fff;
    border-radius:var(--radius-sm);padding:11px 18px;font-weight:600;box-shadow:var(--shadow)}
  .htree .trunk{width:2px;height:18px;background:var(--line)}
  .htree .kids{display:flex;gap:18px;flex-wrap:wrap;justify-content:center;align-items:flex-start}
  /* each child draws its own connector stub + the joining rule via ::before/::after */
  .htree .kid{position:relative;padding-top:20px;display:flex;flex-direction:column;align-items:center}
  .htree .kid::before{content:"";position:absolute;top:0;left:50%;width:2px;height:20px;background:var(--line)}   /* down-stub */
  .htree .kid::after{content:"";position:absolute;top:0;left:-9px;right:-9px;height:2px;background:var(--line)}    /* joining rule */
  .htree .kid:first-child::after{left:50%} .htree .kid:last-child::after{right:50%}                                /* trim rule at ends */
  .htree .node{background:var(--bg);border:1px solid var(--line);border-top:3px solid var(--c);width:170px;
    border-radius:var(--radius-sm);padding:13px 14px;box-shadow:var(--shadow);display:flex;gap:11px;align-items:flex-start}
  .htree .node .t{font-weight:600;font-size:14px} .htree .node .d{font-size:12px;color:var(--muted);margin-top:2px}
</style>
<div class="htree reveal">
  <div class="root"><span class="ichip" style="width:26px;height:26px;font-size:15px;background:rgba(255,255,255,.18);color:#fff"><svg class="ic"><use href="#ic-sitemap"/></svg></span>Diligence working groups</div>
  <div class="trunk"></div>
  <div class="kids" data-stagger>
    <div class="kid"><div class="node" style="--c:var(--cat-fin)"><span class="ichip fin"><svg class="ic"><use href="#ic-coins"/></svg></span><div><div class="t">Finance / FP&amp;A</div><div class="d">Model, valuation, synergies</div></div></div></div>
    <div class="kid"><div class="node" style="--c:var(--cat-risk)"><span class="ichip risk"><svg class="ic"><use href="#ic-shield"/></svg></span><div><div class="t">Risk &amp; Credit</div><div class="d">Portfolio, marks, allowance</div></div></div></div>
    <div class="kid"><div class="node" style="--c:var(--cat-legal)"><span class="ichip legal"><svg class="ic"><use href="#ic-scale"/></svg></span><div><div class="t">Legal</div><div class="d">Structure, contracts, governance</div></div></div></div>
    <div class="kid"><div class="node" style="--c:var(--cat-tech)"><span class="ichip tech"><svg class="ic"><use href="#ic-server"/></svg></span><div><div class="t">Tech &amp; Ops</div><div class="d">Conversion, cyber, vendors</div></div></div></div>
    <div class="kid"><div class="node" style="--c:var(--cat-people)"><span class="ichip people"><svg class="ic"><use href="#ic-users"/></svg></span><div><div class="t">Human Resources</div><div class="d">Retention, comp, culture</div></div></div></div>
    <div class="kid"><div class="node" style="--c:var(--cat-rev)"><span class="ichip rev"><svg class="ic"><use href="#ic-trend"/></svg></span><div><div class="t">Commercial / LOB</div><div class="d">Revenue, segments, cross-sell</div></div></div></div>
  </div>
</div>
<p class="note">Real connector lines show the parent→child relation; color + icon encode the function. If the same category colors recur elsewhere, add a one-line legend. (Many children on a narrow page will wrap — for a deeper tree, nest a second <code>.kids</code> under a child.)</p>
```

---

## 5. Concept map

**Use when** several ideas are joined by *named* relationships and the relationships
carry meaning. **Every edge must carry a verb** (`<text class="edge-lbl">`) — an
unlabeled line is just adjacency, which is what separates a concept map from a
mind map. Per NN/g, a concept map allows **multiple parents** (a node fed by two
others) — that's precisely the case the hierarchy tree (#4) can't handle, so reach
here whenever a child has two parents. Use SVG.

Wire **hover-to-trace** (`data-trace` on the `<svg>`, `data-node="id"` on each node
group, `data-link="a b"` on each edge): hovering a node lights its edges and
neighbors and dims the rest. Because trace lets the reader isolate one node's
connections on demand, a *denser* map stays readable — you no longer have to keep it
to a bare handful, though past ~8–10 nodes it still pays to split into two maps.

```html
<svg viewBox="0 0 640 300" role="img" aria-labelledby="cm-t cm-d" style="width:100%;height:auto" data-trace>
  <title id="cm-t">Workstream to decision concept map</title>
  <desc id="cm-d">Workstreams answer decision questions that feed the bid decision.</desc>
  <defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M0 0L10 5L0 10z" fill="#8a98a8"/></marker></defs>
  <style>
    .cm-node rect{fill:var(--bg);stroke:var(--line);stroke-width:1.5}
    .cm-node.key rect{fill:var(--accent-soft);stroke:#d4e2f0}
    .cm-t{font:600 13px var(--font);fill:var(--ink)}
    .cm-e{stroke:#c4cedb;stroke-width:1.5;fill:none}
  </style>
  <!-- edges: each carries a verb (.edge-lbl) and data-link joining two node ids -->
  <g data-link="assess priorities"><line class="cm-e" x1="150" y1="70" x2="150" y2="120" marker-end="url(#arr)"/><text class="edge-lbl" x="158" y="100">scores</text></g>
  <g data-link="priorities decision"><line class="cm-e" x1="150" y1="172" x2="320" y2="210" marker-end="url(#arr)"/><text class="edge-lbl" x="196" y="186">answers</text></g>
  <g data-link="synergy decision"><line class="cm-e" x1="490" y1="172" x2="360" y2="210" marker-end="url(#arr)"/><text class="edge-lbl dep" x="430" y="186">feeds</text></g>
  <g data-link="assess synergy"><line class="cm-e" x1="230" y1="50" x2="410" y2="140" marker-end="url(#arr)"/><text class="edge-lbl" x="300" y="86">sizes</text></g>
  <!-- nodes: each group carries data-node="id" -->
  <g class="cm-node" data-node="assess"><rect x="70" y="30" width="160" height="40" rx="8"/><text class="cm-t" x="150" y="55" text-anchor="middle">Target assessment</text></g>
  <g class="cm-node" data-node="priorities"><rect x="70" y="130" width="160" height="42" rx="8"/><text class="cm-t" x="150" y="156" text-anchor="middle">Diligence priorities</text></g>
  <g class="cm-node" data-node="synergy"><rect x="410" y="130" width="160" height="42" rx="8"/><text class="cm-t" x="490" y="156" text-anchor="middle">Synergy &amp; model</text></g>
  <g class="cm-node key" data-node="decision"><rect x="250" y="210" width="180" height="46" rx="8"/><text class="cm-t" x="340" y="238" text-anchor="middle">Bid / no-bid decision</text></g>
</svg>
```

<p class="note">"Synergy &amp; model" and "Bid decision" each have two parents — the
case that forces a concept map over a tree. Hover any node to trace its links.</p>

---

## 5b. Converging inputs → decision

**Use when** several factors *together* drive one outcome and you want to show the
relationship, not list them (e.g. the five decision dimensions feeding the acquire
call). Each input is a colour-coded chip with an animated arrow converging on a
central decision node — so the reader sees that all of them feed the same decision.
Far better than five isolated stat cards. Give the feeder edges a verb (`.edge-lbl`)
so "feeds / gates / caps" is stated, not just implied, and put an optional
`.flow-dot` on the straight middle edge (give that path an `id`, point
`data-follow` at it) so a dot visibly travels *into* the decision — direction of
dependency, encoded in motion.

```html
<svg width="100%" viewBox="0 0 640 270" role="img" aria-labelledby="cv-t cv-d">
  <title id="cv-t">Five decision dimensions converge on the recommendation</title>
  <desc id="cv-d">Strategic fit, financial return, revenue durability, workforce durability, and integration executability all feed the acquire decision.</desc>
  <defs><marker id="cvA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs>
  <style>
    .cvb{fill:var(--bg);stroke-width:2} .cvt{font:600 12.5px var(--font);fill:var(--ink)}
    .cvtw{font:600 14px var(--font);fill:#fff}
  </style>
  <path id="cv-mid" class="e-dep draw" d="M212 138H424" marker-end="url(#cvA)"/>
  <path class="e-dep draw" d="M212 34C322 34 332 118 424 130" marker-end="url(#cvA)"/>
  <path class="e-dep draw" d="M212 86C322 86 342 126 424 136" marker-end="url(#cvA)"/>
  <path class="e-dep draw" d="M212 190C322 190 342 150 424 142" marker-end="url(#cvA)"/>
  <path class="e-dep draw" d="M212 242C322 242 332 158 424 148" marker-end="url(#cvA)"/>
  <text class="edge-lbl dep" x="300" y="130" text-anchor="middle">feeds</text>
  <circle class="flow-dot" data-follow="#cv-mid" r="4"/>
  <g><rect class="cvb" x="8" y="16" width="204" height="36" rx="8" style="stroke:var(--accent)"/><text class="cvt" x="22" y="38">Strategic fit</text></g>
  <g><rect class="cvb" x="8" y="68" width="204" height="36" rx="8" style="stroke:var(--cat-rev)"/><text class="cvt" x="22" y="90">Financial return</text></g>
  <g><rect class="cvb" x="8" y="120" width="204" height="36" rx="8" style="stroke:var(--cat-fund)"/><text class="cvt" x="22" y="142">Revenue durability</text></g>
  <g><rect class="cvb" x="8" y="172" width="204" height="36" rx="8" style="stroke:var(--cat-people)"/><text class="cvt" x="22" y="194">Workforce durability</text></g>
  <g><rect class="cvb" x="8" y="224" width="204" height="36" rx="8" style="stroke:var(--cat-tech)"/><text class="cvt" x="22" y="246">Integration executability</text></g>
  <g><rect x="424" y="104" width="208" height="70" rx="12" fill="var(--accent)"/><text class="cvtw" x="528" y="134" text-anchor="middle">Acquire at this</text><text class="cvtw" x="528" y="154" text-anchor="middle">price &amp; terms?</text></g>
</svg>
```

## 5c. Grouped convergence (category + owner → outcome)

**Use when** a set of deliverables/outputs should show three relationships at once:
**category** (group by kind), **owner** (who produces each), and **convergence**
(they all feed one outcome). Far richer than an owner-tagged list — the grouping
carries the categorical relationship, the labels carry ownership, and the funnel
carries the dependency.

```html
<style>
  .conv{display:grid;gap:12px}
  .conv .groups{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:12px;align-items:start}
  .conv .g{border:1px solid var(--line);border-top:3px solid var(--c);border-radius:var(--radius-sm);overflow:hidden;background:var(--bg)}
  .conv .g h5{margin:0;padding:9px 12px;font-size:12px;font-weight:700;color:var(--c);background:var(--cs);display:flex;align-items:center;gap:7px}
  .conv .g h5 .ic{font-size:15px}
  .conv .g .it{padding:9px 12px;border-top:1px solid var(--line);font-size:12px}
  .conv .g .it .o{font-size:10.5px;color:var(--muted);margin-top:1px}
  .conv .cvr{display:flex;justify-content:center;color:#9aa7b6}
  .conv .decision{background:var(--accent);color:#fff;border-radius:var(--radius-sm);padding:13px 16px;display:flex;align-items:center;justify-content:center;gap:11px;font-weight:600;font-size:14px}
  .conv .decision small{display:block;font-weight:400;opacity:.85;font-size:11.5px}
  .conv .decision .ic{font-size:20px}
</style>
<div class="conv reveal">
  <div class="groups" data-stagger>
    <div class="g" style="--c:var(--accent);--cs:var(--accent-soft)"><h5><svg class="ic"><use href="#ic-target"/></svg>Strategy</h5><div class="it">Thesis, fit &amp; scorecard<div class="o">Corp Dev / FP&amp;A</div></div></div>
    <div class="g" style="--c:var(--cat-fin);--cs:var(--cat-fin-soft)"><h5><svg class="ic"><use href="#ic-coins"/></svg>Earnings &amp; valuation</h5><div class="it">Normalized earnings &amp; QoE<div class="o">Finance / FP&amp;A</div></div><div class="it">Pro forma model (base/down/up)<div class="o">Finance / FP&amp;A</div></div><div class="it">EPS, TBV earnback &amp; capital<div class="o">Finance / FP&amp;A</div></div></div>
    <div class="g" style="--c:var(--cat-fund);--cs:var(--cat-fund-soft)"><h5><svg class="ic"><use href="#ic-bank"/></svg>Marks</h5><div class="it">Credit mark &amp; purchase accounting<div class="o">Credit / FP&amp;A</div></div><div class="it">Deposit mark, CDI &amp; goodwill<div class="o">Treasury / FP&amp;A</div></div></div>
    <div class="g" style="--c:var(--cat-rev);--cs:var(--cat-rev-soft)"><h5><svg class="ic"><use href="#ic-trend"/></svg>Value capture</h5><div class="it">Synergy, dis-synergy &amp; retention<div class="o">Commercial / FP&amp;A</div></div><div class="it">Integration budget &amp; value-capture map<div class="o">Integration Office</div></div></div>
    <div class="g" style="--c:var(--cat-risk);--cs:var(--cat-risk-soft)"><h5><svg class="ic"><use href="#ic-alert"/></svg>Risk</h5><div class="it">Cross-function risk register<div class="o">All / Legal &amp; Reg</div></div></div>
  </div>
  <div class="cvr"><svg width="60%" height="26" viewBox="0 0 240 26" preserveAspectRatio="none"><path class="draw" d="M14 2H226 M40 2V13 M120 2V13 M200 2V13 M120 13V22" fill="none" stroke="#9aa7b6" stroke-width="2" marker-end="url(#cv5c)"/><defs><marker id="cv5c" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs></svg></div>
  <div class="decision"><svg class="ic"><use href="#ic-flag"/></svg><div>Final memo — bid / no-bid / reprice / defer<small>FP&amp;A, for IC / board</small></div></div>
</div>
<p class="note">Deliverables grouped by category (strategy, earnings &amp; valuation, marks, value capture, risk); each names its owner; all converge into the FP&amp;A decision memo. FP&amp;A co-owns most — the spine again.</p>
```

> **Gate (what licenses the grid of group boxes here):** the columns are a *grouping*
> relationship (category) plus a *convergence* relationship (the funnel into the
> decision) — that's what earns the layout. If your items are **not** grouped by a
> shared kind and **don't** feed a common outcome, an auto-fit grid encodes nothing;
> use a `.rel` proposition row (#0), converging inputs (#5b), or a flow instead.

---

## 6. Comparison columns

**Use when** two or more options are **measured on the same shared attributes**, so
the reader can compare *across* each row and see which option wins on it. Lay it out
as a grid with the attribute name in the leftmost column and one column per option,
**row-aligned** — every option answers the same attribute on the same line. Mark the
winner per row (`.win`) and close with a **verdict row** that states the
differentiator or the pick. **Gate:** if the options aren't scored/described on the
*same* attributes, this is the wrong form — a shared-attribute comparison is the
whole point; use separate cards or a scorecard instead.

```html
<style>
  .cmp{display:grid;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
  .cmp .row{display:grid;grid-template-columns:150px repeat(3,1fr);border-top:1px solid var(--line)}
  .cmp .row:first-child{border-top:0}
  .cmp .hd{background:var(--accent-soft);color:var(--accent);font-weight:600;font-size:14px;padding:12px 14px;border-left:1px solid var(--line)}
  .cmp .hd.corner{background:var(--ink);color:#fff;font-size:12px;border-left:0}
  .cmp .attr{font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.03em;color:var(--faint);
    background:var(--panel);padding:11px 14px;display:flex;align-items:center}
  .cmp .cell{padding:11px 14px;border-left:1px solid var(--line);font-size:13px;color:var(--ink);position:relative}
  .cmp .cell.win{background:var(--good-soft,rgba(46,160,90,.10))}
  .cmp .cell.win::after{content:"✓";position:absolute;top:8px;right:10px;font-size:11px;font-weight:800;color:var(--good)}
  .cmp .row.verdict .attr{color:var(--accent)} .cmp .row.verdict .cell{font-weight:600}
</style>
<div class="cmp reveal" data-stagger>
  <div class="row"><div class="hd corner">Attribute ▸ option</div><div class="hd">Option A</div><div class="hd">Option B</div><div class="hd">Option C</div></div>
  <div class="row"><div class="attr">Upfront cost</div><div class="cell win">Lowest — $1.2m</div><div class="cell">$2.0m</div><div class="cell">$3.4m</div></div>
  <div class="row"><div class="attr">Time to value</div><div class="cell">9 mo</div><div class="cell win">4 mo</div><div class="cell">12 mo</div></div>
  <div class="row"><div class="attr">Scalability</div><div class="cell">Limited</div><div class="cell">Moderate</div><div class="cell win">High</div></div>
  <div class="row verdict"><div class="attr">Verdict</div><div class="cell">Cheapest, capped</div><div class="cell win">Best balance</div><div class="cell">Scales, slow &amp; dear</div></div>
</div>
<p class="note">Each row is one shared attribute; the ✓ marks the winner on that attribute; the verdict row names the differentiator. Only mark a winner where the source actually establishes one.</p>
```

---

## 7. Weighted scorecard

**Use when** criteria carry different weights (the target assessment scorecard:
strategic fit 14%, financial profile 16%, …). Bars sized by weight, ranked
high-to-low so importance is visible at a glance. Show the score only if present in
the source; otherwise show the weight and an empty score slot — do not invent a
score.

```html
<style>
  .sc{display:grid;gap:9px}
  .sc .row{display:grid;grid-template-columns:160px 1fr 48px;align-items:center;gap:12px}
  .sc .lab{font-size:13.5px;color:var(--ink)}
  .sc .bar{height:18px;background:var(--panel);border-radius:99px;overflow:hidden}
  .sc .fill{height:100%;background:var(--accent);border-radius:99px}
  .sc .wt{font-size:12.5px;color:var(--muted);text-align:right}
</style>
<div class="sc">
  <div class="row"><div class="lab">Financial profile</div><div class="bar"><div class="fill" style="width:100%"></div></div><div class="wt">16%</div></div>
  <div class="row"><div class="lab">Strategic fit</div><div class="bar"><div class="fill" style="width:87.5%"></div></div><div class="wt">14%</div></div>
  <div class="row"><div class="lab">Credit quality</div><div class="bar"><div class="fill" style="width:87.5%"></div></div><div class="wt">14%</div></div>
  <div class="row"><div class="lab">Deposit quality</div><div class="bar"><div class="fill" style="width:81%"></div></div><div class="wt">13%</div></div>
  <div class="row"><div class="lab">Revenue durability</div><div class="bar"><div class="fill" style="width:62.5%"></div></div><div class="wt">10%</div></div>
</div>
<p class="note">Bar length = criterion weight. Scores are unscored in the source (shown as weights only).</p>
```

---

## 8. Radar profile

**Use when** an entity is profiled across several dimensions and the overall
*shape* is the message. Only use with real values; for an unscored framework,
prefer the weighted scorecard instead.

```html
<svg viewBox="0 0 360 320" role="img" aria-labelledby="rd-t rd-d" style="max-width:380px;margin:auto">
  <title id="rd-t">Target profile radar</title>
  <desc id="rd-d">Profile across five diligence dimensions.</desc>
  <style>
    .rd-grid{fill:none;stroke:var(--line)}
    .rd-area{fill:var(--accent);fill-opacity:.16;stroke:var(--accent);stroke-width:2}
    .rd-ax{stroke:var(--line)} .rd-l{font:500 11px var(--font);fill:var(--muted)}
  </style>
  <g transform="translate(180,160)">
    <polygon class="rd-grid" points="0,-110 105,-34 65,89 -65,89 -105,-34"/>
    <polygon class="rd-grid" points="0,-73 70,-23 43,59 -43,59 -70,-23"/>
    <line class="rd-ax" x1="0" y1="0" x2="0" y2="-110"/><line class="rd-ax" x1="0" y1="0" x2="105" y2="-34"/>
    <line class="rd-ax" x1="0" y1="0" x2="65" y2="89"/><line class="rd-ax" x1="0" y1="0" x2="-65" y2="89"/>
    <line class="rd-ax" x1="0" y1="0" x2="-105" y2="-34"/>
    <polygon class="rd-area" points="0,-88 84,-27 39,53 -52,71 -84,-27"/>
    <text class="rd-l" x="0" y="-120" text-anchor="middle">Strategic</text>
    <text class="rd-l" x="112" y="-34">Financial</text>
    <text class="rd-l" x="70" y="104">Credit</text>
    <text class="rd-l" x="-70" y="104" text-anchor="end">Deposits</text>
    <text class="rd-l" x="-112" y="-34" text-anchor="end">Revenue</text>
  </g>
</svg>
```

---

## 9. Decision bands

**Use when** a score or value falls into ranges that map to recommended actions
(the scorecard's 4.0–5.0 → continue, 3.0–3.9 → prioritize, etc.). Color encodes
severity — always pair with a label.

```html
<style>
  .bands{display:grid;gap:8px}
  .bands .b{display:grid;grid-template-columns:96px 1fr;gap:14px;align-items:center;
    border-left:4px solid var(--line);background:var(--panel);border-radius:0 var(--radius-sm) var(--radius-sm) 0;padding:11px 14px}
  .bands .b.good{border-color:var(--good)} .bands .b.ok{border-color:var(--accent)}
  .bands .b.warn{border-color:var(--warn)} .bands .b.bad{border-color:var(--bad)}
  .bands .rng{font-weight:700;font-size:15px;color:var(--ink)}
  .bands .ac{font-size:13.5px;color:var(--muted)}
  .bands .ac strong{color:var(--ink)}
</style>
<div class="bands">
  <div class="b good"><div class="rng">4.0–5.0</div><div class="ac"><strong>Strong profile.</strong> Continue diligence; focus on valuation discipline.</div></div>
  <div class="b ok"><div class="rng">3.0–3.9</div><div class="ac"><strong>Mixed but workable.</strong> Prioritize weak categories and downside cases.</div></div>
  <div class="b warn"><div class="rng">2.0–2.9</div><div class="ac"><strong>Material gaps.</strong> Reprice, narrow scope, or escalate.</div></div>
  <div class="b bad"><div class="rng">&lt; 2.0</div><div class="ac"><strong>Not supportable.</strong> Pause / no-bid unless new evidence changes the score.</div></div>
</div>
```

---

## 10. Phasing bars

**Use when** a benefit or cost is realized in tranches over periods (synergy
realization Y1/Y2/Y3, integration spend). Use the *actual* percentages from the
source. A simple stacked/segmented bar per lever reads cleanly.

```html
<style>
  .ph{display:grid;gap:10px}
  .ph .row{display:grid;grid-template-columns:180px 1fr;gap:12px;align-items:center}
  .ph .lab{font-size:13px;color:var(--ink)}
  .ph .track{display:flex;height:22px;border-radius:6px;overflow:hidden;background:var(--panel)}
  .ph .seg{display:flex;align-items:center;justify-content:center;font-size:11px;color:#fff;font-weight:600}
  .ph .y1{background:var(--accent)} .ph .y2{background:var(--accent-2)} .ph .y3{background:#9bb4cc}
</style>
<div class="legend"><span><i class="dot" style="background:var(--accent)"></i>Year 1</span>
  <span><i class="dot" style="background:var(--accent-2)"></i>Year 2</span>
  <span><i class="dot" style="background:#9bb4cc"></i>Year 3</span></div>
<div class="ph" style="margin-top:10px">
  <div class="row"><div class="lab">Corporate overhead</div>
    <div class="track"><div class="seg y1" style="width:50%">50%</div><div class="seg y2" style="width:25%">75%</div><div class="seg y3" style="width:25%">100%</div></div></div>
  <div class="row"><div class="lab">Technology / vendor</div>
    <div class="track"><div class="seg y1" style="width:25%">25%</div><div class="seg y2" style="width:35%">60%</div><div class="seg y3" style="width:40%">100%</div></div></div>
  <div class="row"><div class="lab">Cross-sell (revenue)</div>
    <div class="track"><div class="seg y1" style="width:25%">25%</div><div class="seg y2" style="width:25%">50%</div><div class="seg y3" style="width:25%">75%</div></div></div>
</div>
<p class="note">Segments are cumulative realization % by year, from the value-capture tracker.</p>
```

---

## 11. 2×2 matrix

**Use when** items are positioned on two axes (risk vs impact, effort vs value,
concentration vs durability). Classic strategy mental model.

```html
<style>
  .mx{position:relative;aspect-ratio:1/.7;border-left:2px solid var(--line);border-bottom:2px solid var(--line);margin:8px 0 0}
  .mx .q{position:absolute;width:50%;height:50%;display:flex;align-items:center;justify-content:center;
    font-size:12px;color:var(--faint);text-transform:uppercase;letter-spacing:.04em}
  .mx .q.tl{top:0;left:0} .mx .q.tr{top:0;right:0} .mx .q.bl{bottom:0;left:0} .mx .q.br{bottom:0;right:0}
  .mx .pt{position:absolute;transform:translate(-50%,50%);background:var(--accent);color:#fff;font-size:12px;
    font-weight:600;padding:5px 10px;border-radius:99px;white-space:nowrap;box-shadow:var(--shadow)}
  .mx .ax{position:absolute;font-size:12px;color:var(--muted)}
</style>
<div class="mx">
  <div class="q tl">Monitor</div><div class="q tr">Mitigate now</div>
  <div class="q bl">Accept</div><div class="q br">Plan for</div>
  <div class="pt" style="left:72%;top:22%">Key-producer attrition</div>
  <div class="pt" style="left:38%;top:64%" >Brand transition</div>
  <div class="ax" style="left:50%;bottom:-22px;transform:translateX(-50%)">Likelihood →</div>
  <div class="ax" style="left:-10px;top:50%;transform:rotate(-90deg) translateX(50%);transform-origin:left">Impact →</div>
</div>
```

---

## 12. Funnel / waterfall

**Use when** a quantity narrows through stages (pipeline, screening) or builds/
reduces step by step (EPS bridge, headcount build). Funnel shown; for a waterfall,
use floating bars. Only use with real magnitudes.

```html
<style>
  .fn{display:grid;gap:6px;max-width:520px;margin:auto}
  .fn .lv{margin:auto;background:var(--accent);color:#fff;border-radius:6px;padding:10px 14px;
    text-align:center;font-size:13.5px;font-weight:600}
  .fn .lv small{display:block;font-weight:400;opacity:.85;font-size:11.5px}
</style>
<div class="fn">
  <div class="lv" style="width:100%">Targets screened<small>full pipeline</small></div>
  <div class="lv" style="width:74%;background:#356293">Pass strategic fit</div>
  <div class="lv" style="width:48%;background:#4a76a8">Clear preliminary diligence</div>
  <div class="lv" style="width:26%;background:var(--accent-2)">Advance to bid<small>decision package</small></div>
</div>
```

---

## 13. Cycle

**Use when** stages repeat in a loop (post-close track → measure → correct →
track). Arrange as a ring of steps.

```html
<style>
  .cyc{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}
  .cyc .s{flex:0 0 150px;background:var(--bg);border:1px solid var(--line);border-radius:var(--radius);
    padding:14px;text-align:center;box-shadow:var(--shadow);position:relative}
  .cyc .s .i{width:30px;height:30px;border-radius:50%;background:var(--accent-soft);color:var(--accent);
    font-weight:700;display:flex;align-items:center;justify-content:center;margin:0 auto 8px}
  .cyc .s .t{font-size:13.5px;font-weight:600}
  .cyc .s .d{font-size:12px;color:var(--muted);margin-top:3px}
</style>
<div class="cyc">
  <div class="s"><div class="i">1</div><div class="t">Track run-rate</div><div class="d">Actuals vs deal model</div></div>
  <div class="s"><div class="i">2</div><div class="t">Compare variances</div><div class="d">Benefits, spend, retention</div></div>
  <div class="s"><div class="i">3</div><div class="t">Act</div><div class="d">Corrective actions</div></div>
  <div class="s"><div class="i">4</div><div class="t">Report</div><div class="d">Management reporting</div></div>
</div>
```

---

## #14 — Causal cascade / strategy map

**Use when** the doc says one thing *drives / enables / supports / reduces* another
in a **different layer** — capability → process → customer → financial, or control →
risk metric → outcome. Stack the layers as horizontal bands and draw labeled
`.e-dep` arrows that **cross the band boundaries** (the crossing *is* the point:
cause lives in one layer, effect in the next). This is the Kaplan/Norton strategy-map
idea — a chain of "if we improve X, then Y" hypotheses made visible. Use an HTML +
SVG overlay: bands and nodes in HTML, the cross-layer arrows as an absolutely-
positioned SVG on top.

```html
<style>
  .cscd{position:relative}
  .cscd .band{display:grid;grid-template-columns:120px 1fr;gap:12px;align-items:center;
    border-radius:var(--radius-sm);padding:12px 14px;margin-bottom:34px;background:var(--panel)}
  .cscd .band:last-child{margin-bottom:0}
  .cscd .band .ly{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:var(--c)}
  .cscd .band .nodes{display:flex;gap:12px;flex-wrap:wrap}
  .cscd .band .nd{background:var(--bg);border:1px solid var(--line);border-left:3px solid var(--c);
    border-radius:8px;padding:9px 13px;font-size:13px;font-weight:600;box-shadow:var(--shadow)}
  .cscd .arrows{position:absolute;inset:0;pointer-events:none;width:100%;height:100%}
  .cscd .arrows text{pointer-events:none}
</style>
<div class="cscd reveal" data-stagger>
  <div class="band" style="--c:var(--cat-people)"><div class="ly">Capability</div>
    <div class="nodes"><div class="nd">Banker training</div><div class="nd">Data platform</div></div></div>
  <div class="band" style="--c:var(--cat-tech)"><div class="ly">Process</div>
    <div class="nodes"><div class="nd">Faster underwriting</div><div class="nd">Targeted outreach</div></div></div>
  <div class="band" style="--c:var(--cat-rev)"><div class="ly">Customer</div>
    <div class="nodes"><div class="nd">Higher satisfaction</div><div class="nd">More cross-sell</div></div></div>
  <div class="band" style="--c:var(--cat-fin)"><div class="ly">Financial</div>
    <div class="nodes"><div class="nd">Fee &amp; NII growth</div></div></div>
  <!-- cross-layer arrows: viewBox matches the box; each .e-dep crosses a band boundary.
       Tune coordinates to your node positions; give each edge a verb via .edge-lbl. -->
  <svg class="arrows" viewBox="0 0 600 340" preserveAspectRatio="none" aria-hidden="true">
    <defs><marker id="csA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
    <path class="e-dep draw" d="M210 46 V96"  marker-end="url(#csA)"/>
    <path class="e-dep draw" d="M340 46 V96"  marker-end="url(#csA)"/>
    <path class="e-dep draw" d="M210 142 V192" marker-end="url(#csA)"/>
    <path class="e-dep draw" d="M340 142 V192" marker-end="url(#csA)"/>
    <path class="e-dep draw" d="M275 238 V288" marker-end="url(#csA)"/>
    <text class="edge-lbl dep" x="216" y="74">enables</text>
    <text class="edge-lbl dep" x="216" y="170">drives</text>
    <text class="edge-lbl dep" x="281" y="266">grows</text>
  </svg>
</div>
<p class="note">Arrows cross the layer boundaries — capability <em>enables</em> process, process <em>drives</em> customer outcomes, which <em>grow</em> the financials. Every arrow is a stated hypothesis, not a decoration.</p>
```

---

## Combining components

A strong page is a short narrative of 4–8 of these, in the order the source's spine
implies — e.g. phase-gate track (the overall process) → weighted scorecard (how a
target is judged) → decision bands (what scores trigger) → concept map (how
workstreams feed the decision) → phasing bars (how value is captured over time).
Connect them with one-line takeaway headings and concise captions so the reader is
led, not dropped into a gallery.

**Hybrids are encouraged when two relations co-exist.** One form per section is a
floor, not a ceiling: if the content carries two relationships at once, draw both in
one visual rather than splitting them. The worked example below fuses the weighted
scorecard (#7) and decision bands (#9) — the scorecard's **total** *feeds* a band,
and the band *selects* an action — joined by a labeled `.e-dep` arrow, rendered as
one picture. The reader sees the whole causal chain "score → band → action" without
hopping between two components.

```html
<style>
  .sccard{display:grid;gap:14px}
  .sccard .sc{display:grid;gap:8px}
  .sccard .sc .r{display:grid;grid-template-columns:150px 1fr 42px;align-items:center;gap:10px}
  .sccard .sc .lab{font-size:13px;color:var(--ink)}
  .sccard .sc .bar{height:16px;background:var(--panel);border-radius:99px;overflow:hidden}
  .sccard .sc .fill{height:100%;background:var(--accent);border-radius:99px}
  .sccard .sc .wt{font-size:12px;color:var(--muted);text-align:right}
  .sccard .total{display:flex;align-items:center;gap:10px;font-weight:700;font-size:14px;color:var(--ink);
    border-top:1px dashed var(--line);padding-top:10px}
  .sccard .total .score{background:var(--accent);color:#fff;border-radius:99px;padding:3px 12px;font-size:14px}
  .sccard .bridge{display:flex;justify-content:center;align-items:center;height:34px}
  .sccard .bands .b{display:grid;grid-template-columns:96px 1fr;gap:14px;align-items:center;
    border-left:4px solid var(--line);background:var(--panel);border-radius:0 var(--radius-sm) var(--radius-sm) 0;padding:10px 14px;margin-bottom:6px}
  .sccard .bands .b.sel{border-color:var(--good);background:var(--good-soft,rgba(46,160,90,.10))}
  .sccard .bands .b:not(.sel){opacity:.55}
  .sccard .bands .rng{font-weight:700;font-size:14px;color:var(--ink)}
  .sccard .bands .ac{font-size:13px;color:var(--muted)} .sccard .bands .ac strong{color:var(--ink)}
</style>
<div class="sccard reveal">
  <div class="sc" data-stagger>
    <div class="r"><div class="lab">Financial profile</div><div class="bar"><div class="fill" style="width:92%"></div></div><div class="wt">4.6</div></div>
    <div class="r"><div class="lab">Strategic fit</div><div class="bar"><div class="fill" style="width:84%"></div></div><div class="wt">4.2</div></div>
    <div class="r"><div class="lab">Credit quality</div><div class="bar"><div class="fill" style="width:76%"></div></div><div class="wt">3.8</div></div>
  </div>
  <div class="total">Weighted total <span class="score">4.2 / 5</span></div>
  <!-- the bridge: total FEEDS the band it falls in -->
  <div class="bridge">
    <svg width="150" height="30" viewBox="0 0 150 30" aria-hidden="true">
      <defs><marker id="scb" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
      <path class="e-dep draw" d="M75 4 V22" marker-end="url(#scb)"/>
      <text class="edge-lbl dep" x="83" y="16">falls in band</text>
    </svg>
  </div>
  <div class="bands">
    <div class="b sel"><div class="rng">4.0–5.0</div><div class="ac"><strong>Continue.</strong> Score lands here → proceed on valuation discipline.</div></div>
    <div class="b"><div class="rng">3.0–3.9</div><div class="ac"><strong>Prioritize gaps.</strong> Reweight the weak categories.</div></div>
    <div class="b"><div class="rng">&lt; 3.0</div><div class="ac"><strong>Reprice / pause.</strong> Material gaps.</div></div>
  </div>
</div>
<p class="note">One visual, two relations: the scorecard's weighted total (4.2) <em>feeds</em> the decision band it lands in (4.0–5.0), which <em>selects</em> the action (Continue). The unselected bands dim so the chosen path reads at a glance.</p>
```
