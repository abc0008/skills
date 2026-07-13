# Flowcharts & Process Diagrams

Process flow is the most common request, so this file goes deep on it. It covers
the flowchart taxonomy (which type for which content), the standard symbols, the
five characteristics every flowchart needs, and animated, paste-ready components
for the workhorse types. Components use the template's CSS variables and motion
classes (`.reveal`, `.ants`, `.draw`, `[data-stagger]`) — see `motion.md`.

Taxonomy and "best for" notes are grounded in Figma's *17 types of flowcharts*;
symbols follow the standard flowchart symbol set.

## Contents

- [Pick the flowchart type](#pick-the-flowchart-type)
- [The five characteristics](#the-five-characteristics)
- [Standard symbols](#standard-symbols)
- [Component: symbol flowchart with a decision](#component-symbol-flowchart-with-a-decision)
- [Component: swimlane flowchart](#component-swimlane-flowchart)
- [Component: decision tree (with pros / cons)](#component-decision-tree-with-pros--cons)
- [Component: event-storming flow](#component-event-storming-flow)
- [Component: logic model](#component-logic-model)
- [Design rules](#design-rules)

> **Don't over-anchor on formal flowchart symbols.** This skill makes *infographics*,
> not engineering flowcharts. Reach for a decision **diamond** only at the genuine
> go/no-go (one, maybe two per page); use terminators sparingly. For everything else,
> prefer the richer treatments — colour-coded icon step flows, the phase swimlane
> matrix, decision bands, converging inputs, the risk matrix. The symbols and rules
> below are tools available when they help, not a checklist to satisfy on every box.

## Pick the flowchart type

Route by the **dominant relationship** between the items — what *connects* them, not
what they are. Every row below names that relationship; pick the form that draws it.

| The dominant relationship is… | Flowchart type | Best for |
| --- | --- | --- |
| Sequence — one step *then* the next | **Process flow** (see catalog #1) | Outlining steps and decisions in a process |
| Sequence owned by one team/role | **Workflow diagram** | Refining team workflows, onboarding |
| Data moving/changing through a system | **Data flow diagram** | Explaining where data goes and changes |
| Ownership hand-off — the same process crossing roles/depts | **Swimlane** | Who does what, cross-functional hand-offs |
| Branch on a condition to different outcomes | **Decision tree** | Analyzing options and where a decision lands |
| Trigger/produce — actors and events that set a process off | **Event storming** | High-level brainstorm of players & events |
| Causal chain: inputs → activities → outputs → outcomes | **Logic model** | Tying work to long-term outcomes |
| Sequence gated by decisions between phases | **Phase / gate track** (catalog #2) | Stage-gated processes (e.g. M&A diligence) |
| A repeating loop | **Cycle** (catalog #13) | Track → measure → correct → repeat |

For business/finance docs the five that earn their keep most often are: process
flow, swimlane, decision tree, phase-gate track, and logic model.

## The five characteristics

Every basic flowchart should have all five — checking for them is a fast quality
gate (a flowchart, unlike a mind map, shows *progression and change*, not loose
association):

1. **Start and end points** — one or more, tied to the core process. Use the
   terminator (stadium) shape.
2. **Substeps / processes** — the actions that move the reader from start to end.
3. **Directional arrows** — show the sequence; the flow goes one clear direction
   (left→right or top→bottom), never ambiguous.
4. **Decision points** — a diamond that splits the flow into labeled branches
   (Yes/No, pass/fail) with different outcomes.
5. **Standard symbols** — consistent shapes so readers don't have to decode.

## Standard symbols

Use shape to encode *kind of step* — this is the flowchart's built-in legend, so
keep it consistent. Drop this key in when a diagram uses more than process boxes.

```html
<svg viewBox="0 0 640 90" role="img" aria-labelledby="sym-t" style="width:100%;max-width:640px">
  <title id="sym-t">Flowchart symbol key</title>
  <style>
    .sym{fill:var(--bg);stroke:var(--accent);stroke-width:1.6}
    .syl{font:500 12px var(--font);fill:var(--muted)}
  </style>
  <g><rect class="sym" x="14" y="20" width="86" height="34" rx="17"/><text class="syl" x="57" y="72" text-anchor="middle">Start / end</text></g>
  <g><rect class="sym" x="140" y="20" width="86" height="34" rx="5"/><text class="syl" x="183" y="72" text-anchor="middle">Process</text></g>
  <g><polygon class="sym" points="312,20 346,37 312,54 278,37"/><text class="syl" x="312" y="72" text-anchor="middle">Decision</text></g>
  <g><polygon class="sym" points="408,20 470,20 456,54 394,54"/><text class="syl" x="432" y="72" text-anchor="middle">Input / output</text></g>
  <g><line x1="520" y1="37" x2="600" y2="37" stroke="var(--accent)" stroke-width="2" marker-end="url(#sa)"/>
     <defs><marker id="sa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
     <text class="syl" x="560" y="72" text-anchor="middle">Flow</text></g>
</svg>
```

## Animated arrows (show order, don't assume it)

Don't rely on left-to-right adjacency to imply flow — make the direction explicit
with an arrow, and let it draw on so the eye follows the sequence. Drop these
between steps; they use the motion layer's `.draw` (see `motion.md`). Give each
`<marker>` a unique id if several appear on one page.

```html
<!-- horizontal animated arrow -->
<svg viewBox="0 0 60 24" style="width:48px;height:20px;overflow:visible">
  <path class="draw" d="M2 12H46" fill="none" stroke="var(--accent)" stroke-width="2.4" marker-end="url(#arh)"/>
  <defs><marker id="arh" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
</svg>
<!-- vertical animated arrow -->
<svg viewBox="0 0 24 50" style="width:20px;height:40px;overflow:visible">
  <path class="draw" d="M12 2V40" fill="none" stroke="var(--accent)" stroke-width="2.4" marker-end="url(#arv)"/>
  <defs><marker id="arv" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
</svg>
```

## Component: icon + colour step flow

**Use when** a process should feel vivid and scannable: each step is a coloured icon
chip + a short label, joined by animated arrows. Reach for this over plain boxes
whenever the steps map to recognisable actors/objects (people, documents, money,
systems) — the icon and colour carry meaning so the words don't have to.

```html
<style>
  .iflow{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
  .iflow .st{display:flex;flex-direction:column;align-items:center;gap:8px;text-align:center;min-width:104px}
  .iflow .st .lab{font-size:12.5px;font-weight:600;color:var(--ink)}
  .iflow .st .sub{font-size:11px;color:var(--muted)}
  .iflow .ichip{width:46px;height:46px;font-size:24px;border-radius:13px}
  .iflow .ar{flex:0 0 auto;width:46px;height:20px}
</style>
<div class="iflow reveal" data-stagger>
  <div class="st"><span class="ichip fin"><svg class="ic"><use href="#ic-target"/></svg></span><div><div class="lab">Score target</div><div class="sub">assessment</div></div></div>
  <svg class="ar" width="46" height="20" viewBox="0 0 60 24"><path class="draw" d="M4 12H50" fill="none" stroke="var(--cat-fin)" stroke-width="2.4" marker-end="url(#f1)"/><defs><marker id="f1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--cat-fin)"/></marker></defs></svg>
  <div class="st"><span class="ichip risk"><svg class="ic"><use href="#ic-file"/></svg></span><div><div class="lab">Validate evidence</div><div class="sub">VDR &amp; diligence</div></div></div>
  <svg class="ar" width="46" height="20" viewBox="0 0 60 24"><path class="draw" d="M4 12H50" fill="none" stroke="var(--cat-risk)" stroke-width="2.4" marker-end="url(#f2)"/><defs><marker id="f2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--cat-risk)"/></marker></defs></svg>
  <div class="st"><span class="ichip rev"><svg class="ic"><use href="#ic-coins"/></svg></span><div><div class="lab">Quantify value</div><div class="sub">synergies</div></div></div>
  <svg class="ar" width="46" height="20" viewBox="0 0 60 24"><path class="draw" d="M4 12H50" fill="none" stroke="var(--cat-rev)" stroke-width="2.4" marker-end="url(#f3)"/><defs><marker id="f3" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--cat-rev)"/></marker></defs></svg>
  <div class="st"><span class="ichip ink"><svg class="ic"><use href="#ic-flag"/></svg></span><div><div class="lab">Decision</div><div class="sub">bid / no-bid</div></div></div>
</div>
```

## Component: symbol flowchart with a decision

**Use when** a process has a real branch (a Yes/No that changes what happens).
This is the canonical flowchart: terminators, process boxes, a decision diamond,
labeled branches, animated draw-on connectors. SVG keeps shapes crisp.

```html
<svg viewBox="0 0 760 300" role="img" aria-labelledby="fc-t fc-d" style="width:100%">
  <title id="fc-t">Diligence go / no-go flow</title>
  <desc id="fc-d">Score the target, decide whether evidence supports the bid, branch to proceed or reprice.</desc>
  <defs><marker id="fa" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto">
    <path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs>
  <style>
    .nb{fill:var(--bg);stroke:var(--accent);stroke-width:1.8}
    .nd{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.8}
    .term{fill:var(--accent);stroke:none}
    .ft{font:600 13px var(--font);fill:var(--ink)} .ftw{font:600 13px var(--font);fill:#fff}
    .fl{font:600 11px var(--font);fill:var(--muted)}
    .edge{stroke:#9aa7b6;stroke-width:2;fill:none}
  </style>
  <!-- edges (draw on). Optional: give one edge an id + a .flow-dot so a dot travels
       source→target along it, encoding direction of flow (see note below). -->
  <path id="fc-e1" class="edge draw" d="M120 47 L120 78" marker-end="url(#fa)"/>
  <path class="edge draw" d="M120 124 L120 150" marker-end="url(#fa)"/>
  <path class="edge draw" d="M196 174 L320 174" marker-end="url(#fa)"/>
  <path class="edge draw" d="M120 198 L120 244" marker-end="url(#fa)"/>
  <circle class="flow-dot" data-follow="#fc-e1" r="3.5"/>
  <text class="fl" x="150" y="166">No</text>
  <text class="fl" x="128" y="226">Yes</text>
  <!-- nodes -->
  <g><rect class="term" x="64" y="16" width="112" height="32" rx="16"/><text class="ftw" x="120" y="37" text-anchor="middle">Score target</text></g>
  <g><rect class="nb" x="48" y="80" width="144" height="44" rx="6"/><text class="ft" x="120" y="107" text-anchor="middle">Validate evidence</text></g>
  <g><polygon class="nd" points="120,150 200,174 120,198 40,174"/><text class="ft" x="120" y="178" text-anchor="middle">Supports bid?</text></g>
  <g><rect class="nb" x="320" y="152" width="150" height="44" rx="6"/><text class="ft" x="395" y="179" text-anchor="middle">Reprice / narrow</text></g>
  <g><rect class="term" x="64" y="246" width="112" height="32" rx="16"/><text class="ftw" x="120" y="267" text-anchor="middle">Proceed to bid</text></g>
</svg>
```

<p class="note"><strong>Optional flow-dot.</strong> The <code>.flow-dot</code> above rides
<code>#fc-e1</code> source→target, encoding <em>direction</em> of flow — useful on a
long or ambiguous edge. It needs a path with an <code>id</code> and
<code>data-follow="#thatId"</code>; it's hidden under reduced motion and in print
(the arrowhead still carries direction), so never rely on it alone. Add one dot per
key edge at most — a dot on every arrow reads as noise.</p>

## Component: swimlane flowchart

**Use when** one process crosses several roles/departments and *who owns each
step* matters.

**Doctrine: the hand-offs are the payload — the lanes are just grouping.** Every
time work crosses a lane it's an **accountability transfer** and a candidate
**bottleneck**; those crossings are what a swimlane exists to expose. So make them
visually distinct: within-lane sequence steps get a neutral `.e-seq` connector;
lane-*crossing* steps get an `.e-handoff` (dashed, `--cat-imo`) connector and a
`.handoff-mark` ripple at the crossing. If nothing ever crosses lanes, you don't
need a swimlane — a plain flow will do.

**Lane discipline:** one owner per lane; every step sits in exactly one lane
(no step straddles two); progression is monotonic left→right (or top→bottom) — the
eye never backtracks.

```html
<style>
  .lanes{display:grid;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden}
  .lane{display:grid;grid-template-columns:152px 1fr;border-top:1px solid var(--line)}
  .lane:first-child{border-top:0}
  .lane .who{background:var(--panel);font-weight:600;font-size:13px;color:var(--c);
    padding:14px;display:flex;align-items:center;gap:9px;border-left:4px solid var(--c)}
  .lane .who .ichip{width:30px;height:30px;font-size:17px;border-radius:8px}
  .lane .track{display:flex;align-items:center;padding:14px 16px;overflow-x:auto}
  .lane .stepf{flex:0 0 auto;background:var(--bg);border:1px solid var(--line);border-top:3px solid var(--c);
    border-radius:var(--radius-sm);padding:9px 13px;font-size:13px;box-shadow:var(--shadow);position:relative;margin-right:46px}
  .lane .stepf:last-child{margin-right:0}
  /* within-lane sequence connector: thin, neutral (.e-seq feel) */
  .lane .stepf::after{content:"";position:absolute;right:-40px;top:50%;width:32px;height:2px;transform:translateY(-50%);
    background:var(--faint)}
  .lane .stepf::before{content:"";position:absolute;right:-11px;top:50%;transform:translateY(-50%);
    border-left:7px solid var(--faint);border-top:5px solid transparent;border-bottom:5px solid transparent}
  .lane .stepf:last-child::after,.lane .stepf:last-child::before{display:none}
  /* lane-CROSSING connector: the hand-off — dashed, --cat-imo, with a ripple mark
     (the .handoff-mark ripple carries the motion cue; the dash + colour mark the transfer) */
  .lane .stepf.handoff::after{width:32px;height:0;border-top:2px dashed var(--cat-imo);background:none}
  .lane .stepf.handoff::before{border-left-color:var(--cat-imo)}
</style>
<div class="lanes reveal" data-stagger>
  <div class="lane" style="--c:var(--cat-fin)"><div class="who"><span class="ichip fin"><svg class="ic"><use href="#ic-coins"/></svg></span>Finance / FP&amp;A</div>
    <div class="track"><div class="stepf">Score target</div><div class="stepf">Build model</div><div class="stepf handoff handoff-mark">Quantify synergies</div></div></div>
  <div class="lane" style="--c:var(--cat-risk)"><div class="who"><span class="ichip risk"><svg class="ic"><use href="#ic-shield"/></svg></span>Risk &amp; Credit</div>
    <div class="track"><div class="stepf">Review portfolio</div><div class="stepf handoff handoff-mark">Set credit marks</div></div></div>
  <div class="lane" style="--c:var(--cat-legal)"><div class="who"><span class="ichip legal"><svg class="ic"><use href="#ic-scale"/></svg></span>Legal / Reg</div>
    <div class="track"><div class="stepf">Map approval path</div><div class="stepf">Draft LOI support</div></div></div>
  <div class="lane" style="--c:var(--cat-tech)"><div class="who"><span class="ichip tech"><svg class="ic"><use href="#ic-sitemap"/></svg></span>IMO / Tech</div>
    <div class="track"><div class="stepf">Integration plan</div><div class="stepf">Day-1 budget</div></div></div>
</div>
<p class="note">Neutral connectors = within-lane sequence; dashed <span style="color:var(--cat-imo)">imo-coloured</span> connectors with a ripple = a hand-off to another lane (an accountability transfer, and where work stalls). Mark <code>.handoff</code> on the step that hands work across lanes; add <code>.handoff-mark</code> for the ripple.</p>
```

## Component: phase swimlane (matrix) — who does what, when ★

**Use when** a process crosses several functions AND moves through phases over time.
This is usually the strongest "who does what, when" view — function lanes (rows) ×
phase columns, with the deal flowing left→right through the gates. Prefer it over a
flat parallel grid (which hides the timing) whenever the content has phases. Colour
lanes by category, icon per lane, empty cells as a neutral dash.

```html
<style>
  .pm{display:grid;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;min-width:740px}
  .pm .row{display:grid;grid-template-columns:154px repeat(4,1fr);border-top:1px solid var(--line)}
  .pm .row:first-child{border-top:0}
  .pm .corner{background:var(--ink);color:#fff;font-size:12px;font-weight:600;padding:12px 13px;display:flex;align-items:center}
  .pm .ph{background:var(--panel);padding:10px 12px;border-left:1px solid var(--line)}
  .pm .ph .pn{font-weight:700;color:var(--accent);font-size:12.5px}
  .pm .ph .pg{font-size:10.5px;color:var(--warn);font-weight:600;margin-top:2px}
  .pm .who{display:flex;align-items:center;gap:8px;padding:12px 13px;font-size:12.5px;font-weight:600;color:var(--c);background:var(--panel);border-left:4px solid var(--c)}
  .pm .who .ichip{width:28px;height:28px;font-size:16px;border-radius:7px}
  .pm .cell{border-left:1px solid var(--line);border-top:2px solid var(--c);padding:11px 12px;font-size:12px;color:var(--ink);background:var(--bg)}
  .pm .cell.e{display:flex;align-items:center;justify-content:center}
  .pm .cell.e::before{content:"";width:16px;height:2px;background:var(--line);border-radius:2px}
  .pm-flow{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);margin:0 0 8px}
</style>
<div class="pm-flow"><span>Deal flows through the gates</span>
  <svg width="150" height="14" viewBox="0 0 160 14"><path class="draw" d="M2 7H150" fill="none" stroke="var(--accent)" stroke-width="2.2" marker-end="url(#pmf)"/><defs><marker id="pmf" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs></svg></div>
<div class="scroller"><div class="pm reveal" data-stagger>
  <div class="row"><div class="corner">Function ▸ phase</div>
    <div class="ph"><div class="pn">1 · Assess</div><div class="pg">gate: continue / narrow</div></div>
    <div class="ph"><div class="pn">2 · Diligence</div><div class="pg">gate: final-round focus</div></div>
    <div class="ph"><div class="pn">3 · Decide</div><div class="pg">gate: bid / no-bid</div></div>
    <div class="ph"><div class="pn">4 · Close</div><div class="pg">gate: readiness</div></div></div>
  <div class="row" style="--c:var(--cat-fin)"><div class="who"><span class="ichip fin"><svg class="ic"><use href="#ic-coins"/></svg></span>Finance / FP&amp;A</div>
    <div class="cell">Score &amp; prioritize</div><div class="cell">Model, PPA, EPS</div><div class="cell">Final memo &amp; outputs</div><div class="cell">Run-rate baseline</div></div>
  <div class="row" style="--c:var(--cat-risk)"><div class="who"><span class="ichip risk"><svg class="ic"><use href="#ic-shield"/></svg></span>Risk &amp; Credit</div>
    <div class="cell e"></div><div class="cell">Marks, CECL, concentr.</div><div class="cell">Downside cases</div><div class="cell e"></div></div>
  <div class="row" style="--c:var(--cat-legal)"><div class="who"><span class="ichip legal"><svg class="ic"><use href="#ic-scale"/></svg></span>Legal / Reg</div>
    <div class="cell e"></div><div class="cell">Approval path</div><div class="cell">LOI support</div><div class="cell">Reg package</div></div>
  <div class="row" style="--c:var(--cat-imo)"><div class="who"><span class="ichip imo"><svg class="ic"><use href="#ic-sitemap"/></svg></span>IMO / Tech</div>
    <div class="cell e"></div><div class="cell">Conversion risk</div><div class="cell">Integration cost</div><div class="cell">Day-1 &amp; plan</div></div>
</div></div>
<p class="note">Rows = functions (icon + colour); columns = phase gates; the deal flows left→right. An empty cell means that function owns no distinct deliverable that phase.</p>
```

## Component: spine / backbone (a through-line others feed into)

**Use when** one entity runs through the whole process while others feed into it
(e.g. FP&A is present in every phase; specialist findings plug into it). Don't list
the through-line's workstreams as cards — show the *relationships*: **timing** (the
workstreams laid left→right across phases), the **spine** (a coloured band), and
**dependency** (feeder chips arrowing into the band). One picture carries all three.

```html
<style>
  .spine{display:grid;gap:12px}
  .spine .feeders{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center}
  .spine .fl{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
  .spine .fchip{display:inline-flex;align-items:center;gap:6px;font-size:12px;font-weight:600;padding:5px 11px;border-radius:99px;border:1px solid var(--line);background:var(--bg)}
  .spine .fchip .ic{font-size:14px}
  .spine .fa{display:flex;justify-content:center;color:#9aa7b6}
  .spine .track{background:var(--cat-fin-soft);border:1px solid #d4e2f0;border-radius:14px;padding:14px 16px}
  .spine .lab{font-size:11px;font-weight:700;color:var(--cat-fin);text-transform:uppercase;letter-spacing:.04em;display:flex;align-items:center;gap:8px;margin-bottom:10px}
  .spine .flow{display:flex;align-items:stretch;overflow-x:auto}
  .spine .ws{flex:1 0 0;min-width:140px;background:var(--bg);border:1px solid #d4e2f0;border-top:3px solid var(--cat-fin);border-radius:8px;padding:10px 12px;margin-right:30px;position:relative;box-shadow:var(--shadow)}
  .spine .ws:last-child{margin-right:0}
  .spine .ws .ph{font-size:10px;font-weight:700;color:var(--cat-fin);text-transform:uppercase}
  .spine .ws .t{font-size:13px;font-weight:600;margin:2px 0} .spine .ws .d{font-size:11px;color:var(--muted)}
  .spine .ws::after{content:"";position:absolute;right:-26px;top:50%;width:18px;height:2px;transform:translateY(-50%);background:repeating-linear-gradient(90deg,var(--cat-fin) 0 6px,transparent 6px 11px);background-size:22px 2px;animation:spm 1.1s linear infinite}
  .spine .ws::before{content:"";position:absolute;right:-8px;top:50%;transform:translateY(-50%);border-left:6px solid var(--cat-fin);border-top:4px solid transparent;border-bottom:4px solid transparent}
  .spine .ws:last-child::after,.spine .ws:last-child::before{display:none}
  @keyframes spm{to{background-position:22px 0}}
  @media (prefers-reduced-motion:reduce){.spine .ws::after{animation:none}}
</style>
<div class="spine reveal">
  <div class="feeders"><span class="fl">Findings feed in</span>
    <span class="fchip" style="color:var(--cat-risk)"><svg class="ic"><use href="#ic-shield"/></svg>Credit</span>
    <span class="fchip" style="color:var(--cat-fund)"><svg class="ic"><use href="#ic-bank"/></svg>Deposits</span>
    <span class="fchip" style="color:var(--cat-legal)"><svg class="ic"><use href="#ic-scale"/></svg>Regulatory</span>
    <span class="fchip" style="color:var(--cat-people)"><svg class="ic"><use href="#ic-users"/></svg>Workforce</span>
    <span class="fchip" style="color:var(--cat-tech)"><svg class="ic"><use href="#ic-server"/></svg>Technology</span>
  </div>
  <div class="fa"><svg width="20" height="22" viewBox="0 0 20 22"><path class="draw" d="M10 2V18" fill="none" stroke="#9aa7b6" stroke-width="2" marker-end="url(#spf)"/><defs><marker id="spf" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs></svg></div>
  <div class="track">
    <div class="lab"><span class="ichip fin" style="width:24px;height:24px;font-size:14px;border-radius:6px"><svg class="ic"><use href="#ic-sitemap"/></svg></span>FP&amp;A economic spine — others' findings convert here into the decision</div>
    <div class="flow" data-stagger>
      <div class="ws"><div class="ph">Phase 1</div><div class="t">Target assessment</div><div class="d">Score &amp; set priorities</div></div>
      <div class="ws"><div class="ph">Phase 2</div><div class="t">Financial modeling</div><div class="d">Earnings, PPA, EPS, TBV</div></div>
      <div class="ws"><div class="ph">Phase 2–3</div><div class="t">Synergy analysis</div><div class="d">Baseline, timing, leakage</div></div>
      <div class="ws"><div class="ph">Phase 4</div><div class="t">Integration planning</div><div class="d">Budget, run-rate baseline</div></div>
      <div class="ws"><div class="ph">Phase 5</div><div class="t">Post-close tracking</div><div class="d">Benefits, spend, variances</div></div>
    </div>
  </div>
</div>
<p class="note">Left→right is time (phase); the band is the through-line; the feeder chips are the specialist findings that plug into modeling &amp; synergy and convert into the decision. Assumption governance wraps all of it (one risk register, one assumption log).</p>
```

## Component: gated process flow (ordinal steps + inline decisions) ★

**Use when** a process runs through several phases AND a couple of them are genuine
branch points. **Don't carve the decisions into a separate section** — show the
*whole* flow: every phase in sequence, with the real go/no-go decisions branching
inline (a diamond marker whose outcomes sit right beside it). Ordinal phases get a
round marker and a "gate → focuses next round" pill; decision phases get a diamond
marker and their branch outcomes as coloured chips. One diagram, decisions in context.

**Light the taken branch.** Wrap a decision's outcome chips in `[data-branch]`, tag
the chosen outcome `.br-on` and the rejected ones `.br-off`: on reveal the rejected
paths dim and the taken path stays lit, so the *decision* — not just the options —
is what the reader sees. Only do this when the source states which branch was taken;
if it's a live/open decision, leave all chips equal (no `data-branch`).

```html
<style>
  .pgf{display:grid;gap:0}
  .pgf .ph{display:grid;grid-template-columns:40px minmax(210px,290px) 1fr;gap:14px;align-items:stretch}
  .pgf .rail{display:flex;flex-direction:column;align-items:center}
  .pgf .mark{width:34px;height:34px;border-radius:50%;background:var(--c);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;flex:none}
  .pgf .mark.dec{border-radius:6px;transform:rotate(45deg)} .pgf .mark.dec span{transform:rotate(-45deg)}
  .pgf .line{width:2px;flex:1;background:var(--line);min-height:30px}
  .pgf .ph:last-child .line{display:none}
  .pgf .node{border:1px solid var(--line);border-left:4px solid var(--c);border-radius:var(--radius-sm);padding:11px 13px;box-shadow:var(--shadow);margin-bottom:16px;display:flex;gap:10px;align-items:flex-start}
  .pgf .node .t{font-weight:600;font-size:14px} .pgf .node .d{font-size:11.5px;color:var(--muted);margin-top:2px}
  .pgf .side{display:flex;align-items:center;margin-bottom:16px}
  .pgf .gate{font-size:11px;font-weight:600;color:var(--warn);background:var(--warn-soft);padding:3px 10px;border-radius:99px}
  .pgf .dec-out{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
  .pgf .dec-out .lead{font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:.03em}
  .pgf .oc{font-size:11.5px;font-weight:600;color:#fff;padding:4px 11px;border-radius:99px}
  .pgf .oc.go{background:var(--good)} .pgf .oc.warn{background:var(--warn)} .pgf .oc.bad{background:var(--bad)} .pgf .oc.alt{background:var(--accent)}
  .pgf .ai{width:24px;height:13px;flex:none}
</style>
<div class="pgf reveal" data-stagger>
  <div class="ph" style="--c:var(--cat-fin)"><div class="rail"><div class="mark"><span>0</span></div><div class="line"></div></div>
    <div class="node"><span class="ichip fin"><svg class="ic"><use href="#ic-flag"/></svg></span><div><div class="t">Setup</div><div class="d">Thesis, team, VDR protocol, model shell</div></div></div>
    <div class="side"><span class="gate">gate → proceed to VDR review</span></div></div>
  <div class="ph" style="--c:var(--cat-fin)"><div class="rail"><div class="mark dec"><span>1</span></div><div class="line"></div></div>
    <div class="node"><span class="ichip fin"><svg class="ic"><use href="#ic-target"/></svg></span><div><div class="t">Target assessment</div><div class="d">Score fit; find value-driving questions</div></div></div>
    <div class="side"><div class="dec-out" data-branch><span class="lead">decision</span>
      <svg class="ai" viewBox="0 0 28 13"><path class="draw" d="M2 6.5H22" fill="none" stroke="#9aa7b6" stroke-width="2" marker-end="url(#pgf1)"/><defs><marker id="pgf1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs></svg>
      <span class="oc go br-on">Continue</span><span class="oc warn br-off">Narrow</span><span class="oc bad br-off">Pause</span></div></div></div>
  <div class="ph" style="--c:var(--cat-risk)"><div class="rail"><div class="mark"><span>2</span></div><div class="line"></div></div>
    <div class="node"><span class="ichip risk"><svg class="ic"><use href="#ic-file"/></svg></span><div><div class="t">Deep diligence</div><div class="d">Validate earnings, credit, deposits, synergies</div></div></div>
    <div class="side"><span class="gate">gate → final-round focus</span></div></div>
  <div class="ph" style="--c:var(--accent)"><div class="rail"><div class="mark dec"><span>3</span></div><div class="line"></div></div>
    <div class="node"><span class="ichip ink"><svg class="ic"><use href="#ic-check"/></svg></span><div><div class="t">Decision package</div><div class="d">Convert findings to bid / LOI support</div></div></div>
    <div class="side"><div class="dec-out"><span class="lead">decision</span>
      <svg class="ai" viewBox="0 0 28 13"><path class="draw" d="M2 6.5H22" fill="none" stroke="#9aa7b6" stroke-width="2" marker-end="url(#pgf2)"/><defs><marker id="pgf2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs></svg>
      <span class="oc go">Bid</span><span class="oc bad">No-bid</span><span class="oc warn">Reprice</span><span class="oc alt">Defer</span></div></div></div>
  <div class="ph" style="--c:var(--cat-imo)"><div class="rail"><div class="mark"><span>4</span></div><div class="line"></div></div>
    <div class="node"><span class="ichip imo"><svg class="ic"><use href="#ic-sitemap"/></svg></span><div><div class="t">Signing → close</div><div class="d">Regulatory package, integration &amp; Day-1 plan</div></div></div>
    <div class="side"><span class="gate">gate → close readiness</span></div></div>
  <div class="ph" style="--c:var(--cat-rev)"><div class="rail"><div class="mark"><span>5</span></div></div>
    <div class="node"><span class="ichip rev"><svg class="ic"><use href="#ic-trend"/></svg></span><div><div class="t">Post-close tracking</div><div class="d">Actuals vs deal model; corrective actions</div></div></div>
    <div class="side"><span class="gate">gate → realize value or intervene</span></div></div>
</div>
<p class="note">All phases in sequence; the diamond markers (1 &amp; 3) are the real branch points, outcomes shown inline. Phase 1's chips use <code>[data-branch]</code> — the taken outcome (Continue) stays lit while the rejected ones dim on reveal. Ordinal gates focus the next round; decision gates can change the deal's direction.</p>
```

## Component: decision gate with branches

**Use when** you need to zoom in on *one* decision in detail (and it isn't already
shown inline by the gated-process-flow above). A diamond with labelled, animated
branches to outcome terminators. Don't use this as a substitute for showing the
decision inside the overall flow — prefer the gated process flow when the doc has a
multi-phase process.

```html
<svg width="100%" viewBox="0 0 520 170" role="img" aria-labelledby="dg-t dg-d">
  <title id="dg-t">Phase-1 gate</title>
  <desc id="dg-d">The target score branches the deal to continue, narrow, or pause.</desc>
  <defs><marker id="dgA" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10z" fill="#9aa7b6"/></marker></defs>
  <style>
    .dgd{fill:var(--accent-soft);stroke:var(--accent);stroke-width:1.8}
    .dgt{font:600 13px var(--font);fill:var(--ink)} .dgtw{font:600 12.5px var(--font);fill:#fff}
    .dgl{font:600 11px var(--font);fill:var(--muted)} .dge{stroke:#9aa7b6;stroke-width:2;fill:none}
  </style>
  <polygon class="dgd" points="95,35 175,85 95,135 15,85"/>
  <text class="dgt" x="95" y="81" text-anchor="middle">Target</text>
  <text class="dgt" x="95" y="97" text-anchor="middle">score?</text>
  <path class="dge draw" d="M175 85 L300 52" marker-end="url(#dgA)"/>
  <path class="dge draw" d="M175 85 L300 85" marker-end="url(#dgA)"/>
  <path class="dge draw" d="M175 85 L300 118" marker-end="url(#dgA)"/>
  <text class="dgl" x="208" y="58">high</text><text class="dgl" x="208" y="132">low</text>
  <g><rect fill="var(--good)" x="302" y="35" width="170" height="34" rx="17"/><text class="dgtw" x="387" y="57" text-anchor="middle">Continue diligence</text></g>
  <g><rect fill="var(--warn)" x="302" y="68" width="170" height="34" rx="17"/><text class="dgtw" x="387" y="90" text-anchor="middle">Narrow scope</text></g>
  <g><rect fill="var(--bad)" x="302" y="101" width="170" height="34" rx="17"/><text class="dgtw" x="387" y="123" text-anchor="middle">Pause / no-bid</text></g>
</svg>
```

## Component: owner-mapped items

> **Gate — try the theme ↔ owner matrix first.** Use this flat form *only* when there
> is genuinely **no ownership overlap and no hub function**: each item has exactly one
> owner, and no one function touches many items. If any item is co-owned, or one
> function is a hub that owns several themes, this layout hides that — use the
> **theme ↔ owner matrix** (below) instead, which shows the overlap and the hub.

**Use when** (after the gate) a list of items each belongs to *one* function and you
just need to show that mapping. Encode ownership visibly — **group the items by owner**
(one block per function, its icon + colour heading), not as an interleaved auto-fit
grid where the reader has to re-scan to find who owns what. The grouping carries the
ownership relation; the icon chip repeats it per item.

```html
<style>
  .owg{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:12px;align-items:start}
  .owg .grp{border:1px solid var(--line);border-top:3px solid var(--c);border-radius:var(--radius-sm);overflow:hidden;background:var(--bg)}
  .owg .grp h5{margin:0;padding:9px 12px;font-size:12.5px;font-weight:700;color:var(--c);background:var(--cs);
    display:flex;align-items:center;gap:8px}
  .owg .grp h5 .ichip{width:26px;height:26px;font-size:15px;border-radius:7px}
  .owg .grp .it{display:flex;align-items:center;gap:9px;padding:9px 12px;border-top:1px solid var(--line);font-size:13px;font-weight:600}
  .owg .grp .it .ichip{width:22px;height:22px;font-size:13px;border-radius:6px}
</style>
<div class="owg reveal" data-stagger>
  <div class="grp" style="--c:var(--cat-fin);--cs:var(--cat-fin-soft)"><h5><span class="ichip fin"><svg class="ic"><use href="#ic-coins"/></svg></span>Finance / FP&amp;A</h5>
    <div class="it"><span class="ichip fin"><svg class="ic"><use href="#ic-coins"/></svg></span>Earnings</div></div>
  <div class="grp" style="--c:var(--cat-risk);--cs:var(--cat-risk-soft)"><h5><span class="ichip risk"><svg class="ic"><use href="#ic-shield"/></svg></span>Risk &amp; Credit</h5>
    <div class="it"><span class="ichip risk"><svg class="ic"><use href="#ic-shield"/></svg></span>Credit</div></div>
  <div class="grp" style="--c:var(--cat-fund);--cs:var(--cat-fund-soft)"><h5><span class="ichip fund"><svg class="ic"><use href="#ic-bank"/></svg></span>Treasury</h5>
    <div class="it"><span class="ichip fund"><svg class="ic"><use href="#ic-bank"/></svg></span>Deposits</div></div>
  <div class="grp" style="--c:var(--cat-legal);--cs:var(--cat-legal-soft)"><h5><span class="ichip legal"><svg class="ic"><use href="#ic-scale"/></svg></span>Legal / Reg</h5>
    <div class="it"><span class="ichip legal"><svg class="ic"><use href="#ic-scale"/></svg></span>Compliance</div></div>
  <div class="grp" style="--c:var(--cat-tech);--cs:var(--cat-tech-soft)"><h5><span class="ichip tech"><svg class="ic"><use href="#ic-server"/></svg></span>Tech &amp; Ops</h5>
    <div class="it"><span class="ichip tech"><svg class="ic"><use href="#ic-server"/></svg></span>Technology</div></div>
</div>
<p class="note">Items grouped under their owner — the block itself carries the ownership relation, so the reader never re-scans to find who owns what. If two blocks would share an item, that's your signal to switch to the matrix.</p>
```

## Component: theme ↔ owner matrix (shows overlap)

**Use when** items map to owners but the ownership *overlaps* — some themes are
co-owned, one function is a hub. A flat owner-mapped list hides that; a small
responsibility matrix shows it. A dot marks an owner (a second dot a co-owner);
read down a column to spot the hub, across a row to spot shared ownership.

```html
<style>
  .rmx{display:grid;border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;min-width:660px}
  .rmx .row{display:grid;grid-template-columns:230px repeat(6,1fr);border-top:1px solid var(--line)}
  .rmx .row:first-child{border-top:0}
  .rmx .hc{padding:9px 6px;text-align:center;font-size:10.5px;font-weight:700;background:var(--panel);border-left:1px solid var(--line);color:var(--hc)}
  .rmx .corner{background:var(--ink);color:#fff;font-size:11.5px;font-weight:600;padding:10px 12px;display:flex;align-items:center}
  .rmx .th{padding:10px 12px;font-size:12.5px;font-weight:500;background:var(--bg);display:flex;align-items:center}
  .rmx .c{border-left:1px solid var(--line);display:flex;align-items:center;justify-content:center;background:var(--bg)}
  .rmx .d{width:14px;height:14px;border-radius:50%}
  .rmx .d.lead{box-shadow:0 0 0 3px rgba(0,0,0,.06)}
</style>
<div class="scroller"><div class="rmx reveal" data-stagger>
  <div class="row"><div class="corner">Theme ▸ owner</div>
    <div class="hc" style="--hc:var(--cat-fin)">Finance</div><div class="hc" style="--hc:var(--cat-risk)">Risk</div><div class="hc" style="--hc:var(--cat-legal)">Legal</div><div class="hc" style="--hc:var(--cat-tech)">Tech</div><div class="hc" style="--hc:var(--cat-people)">HR</div><div class="hc" style="--hc:var(--cat-rev)">Comm.</div></div>
  <div class="row"><div class="th">Normalized earnings power</div><div class="c"><span class="d lead" style="background:var(--cat-fin)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div></div>
  <div class="row"><div class="th">Revenue durability</div><div class="c"><span class="d lead" style="background:var(--cat-fin)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"><span class="d" style="background:var(--cat-rev)"></span></div></div>
  <div class="row"><div class="th">Workforce durability</div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"><span class="d lead" style="background:var(--cat-people)"></span></div><div class="c"></div></div>
  <div class="row"><div class="th">Credit &amp; risk profile</div><div class="c"></div><div class="c"><span class="d lead" style="background:var(--cat-risk)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div></div>
  <div class="row"><div class="th">Deposit &amp; funding quality</div><div class="c"><span class="d lead" style="background:var(--cat-fin)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div></div>
  <div class="row"><div class="th">Regulatory &amp; compliance</div><div class="c"></div><div class="c"></div><div class="c"><span class="d lead" style="background:var(--cat-legal)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div></div>
  <div class="row"><div class="th">Integration complexity &amp; cost</div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"><span class="d lead" style="background:var(--cat-tech)"></span></div><div class="c"></div><div class="c"></div></div>
  <div class="row"><div class="th">Cost &amp; revenue synergies</div><div class="c"><span class="d lead" style="background:var(--cat-fin)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"><span class="d" style="background:var(--cat-rev)"></span></div></div>
  <div class="row"><div class="th">Valuation support</div><div class="c"><span class="d lead" style="background:var(--cat-fin)"></span></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div><div class="c"></div></div>
</div></div>
<p class="note">Read down the Finance column to see it anchors most themes (the spine); read across a row to see shared ownership (revenue durability and synergies are Finance + Commercial). Use this over the flat owner-mapped list whenever ownership overlaps.</p>
```

## Component: decision tree (with pros / cons)

**Use when** a decision branches on a condition and each branch has trade-offs
that lead to a Yes/No outcome. Mirrors the classic "should I…?" tree: a root
question, condition branches, pro/con cards, and a verdict. Reveals top-down.

```html
<style>
  .dt{display:grid;gap:14px}
  .dt .root{justify-self:center;background:var(--ink);color:#fff;border-radius:var(--radius-sm);
    padding:14px 22px;font-weight:600;font-size:16px;box-shadow:var(--shadow)}
  .dt .branches{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px}
  .dt .br{border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
  .dt .cond{padding:11px 14px;font-weight:600;font-size:14px;color:#fff;background:var(--accent)}
  .dt .pc{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--line)}
  .dt .pc div{background:var(--bg);padding:11px 13px;font-size:12.5px}
  .dt .pc .h{font-weight:700;font-size:10.5px;text-transform:uppercase;letter-spacing:.03em;margin-bottom:4px}
  .dt .pc .pro .h{color:var(--good)} .dt .pc .con .h{color:var(--bad)}
  .dt .verdict{padding:11px;text-align:center;font-weight:700;color:#fff;letter-spacing:.03em}
  .dt .verdict.yes{background:var(--good)} .dt .verdict.no{background:var(--bad)}
</style>
<div class="dt reveal" data-stagger>
  <div class="root">Acquire this target at this price?</div>
  <div class="branches">
    <div class="br"><div class="cond">Score 4.0–5.0</div>
      <div class="pc"><div class="pro"><div class="h">Pro</div>Strong, evidence-backed profile</div>
        <div class="con"><div class="h">Con</div>Price discipline still required</div></div>
      <div class="verdict yes">Proceed</div></div>
    <div class="br"><div class="cond">Score 2.0–2.9</div>
      <div class="pc"><div class="pro"><div class="h">Pro</div>Strategic fit may hold</div>
        <div class="con"><div class="h">Con</div>Material gaps / value leakage</div></div>
      <div class="verdict no">Reprice or pass</div></div>
    <div class="br"><div class="cond">Score &lt; 2.0</div>
      <div class="pc"><div class="pro"><div class="h">Pro</div>—</div>
        <div class="con"><div class="h">Con</div>Economics not supportable</div></div>
      <div class="verdict no">No-bid</div></div>
  </div>
</div>
<p class="note">Branches and verdicts come straight from the source's decision bands — no scores invented.</p>
```

## Component: event-storming flow

**Use when** you want a high-level, left-to-right sequence of *what happens* and
*who/what sets it off*. **Type the nodes** and **label the edges** — that's the
grammar: an **actor** or **command** *triggers* an **event** (write events in the
**past tense** — "Diligence started", "Bid submitted"); a system or event *produces*
the next. Colour encodes type (keep the legend); the small `triggers` / `produces`
label on each connector states the relation rather than leaving it to adjacency.

```html
<style>
  .es-legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12.5px;color:var(--muted);margin-bottom:12px}
  .es-legend span{display:inline-flex;align-items:center;gap:6px}
  .es-row{display:flex;align-items:center;gap:0;overflow-x:auto;padding:16px 0 4px}
  .es .e{flex:0 0 auto;border-radius:6px;padding:11px 13px;font-size:12.5px;font-weight:600;color:#243;
    margin-right:64px;position:relative;min-width:120px;box-shadow:var(--shadow)}
  .es .e::after{content:"";position:absolute;right:-54px;top:50%;width:44px;height:2px;background:#c4cedb}
  .es .e::before{content:attr(data-verb);position:absolute;right:-56px;top:calc(50% - 16px);width:52px;text-align:center;
    font-size:9.5px;font-weight:700;letter-spacing:.03em;text-transform:uppercase;color:var(--muted)}
  .es .e:last-child::after,.es .e:last-child::before{display:none}
  .es .actor{background:#fde9b8} .es .cmd{background:#bfe0ff} .es .event{background:#ffc9a3}
  .es .system{background:#cdeacb} .es .policy{background:#e3c9f2}
</style>
<div class="es reveal">
  <div class="es-legend">
    <span><i class="dot" style="background:#fde9b8"></i>Actor</span>
    <span><i class="dot" style="background:#bfe0ff"></i>Command</span>
    <span><i class="dot" style="background:#ffc9a3"></i>Event (past tense)</span>
    <span><i class="dot" style="background:#cdeacb"></i>System</span>
    <span><i class="dot" style="background:#e3c9f2"></i>Policy</span>
  </div>
  <div class="es-row" data-stagger>
    <div class="e actor" data-verb="issues">Deal team</div>
    <div class="e cmd" data-verb="triggers">Open VDR</div>
    <div class="e event" data-verb="runs on">Diligence started</div>
    <div class="e system" data-verb="produces">Model + risk register</div>
    <div class="e policy" data-verb="produces">Gate criteria met</div>
    <div class="e event">Bid submitted</div>
  </div>
</div>
```

## Component: logic model

**Use when** you need to tie work to outcomes. Chain all four links — Inputs →
Activities → **Outputs → Outcomes** (short/long) — and draw the **output→outcome**
step as an `.e-dep` arrow with a verb, because that's the leap the model exists to
make (a memo is not a decision; a report is not a realized result). **Rule: never
stop the chain at "report produced."** Style the node types distinctly so the reader
reads *kind*: activities are solid accent, outputs are outlined, outcomes are
warn-toned — the change in treatment marks the change from *what we do* to *what
changes as a result*.

```html
<style>
  .lm{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;align-items:start;position:relative}
  .lm .col h4{margin:0 0 8px;font-size:13px;font-weight:700;color:#fff;border-radius:var(--radius-sm);
    padding:9px 12px;text-align:center}
  .lm .c1 h4{background:#7a5af0} .lm .c2 h4{background:var(--accent)}
  .lm .c3 h4{background:var(--accent-2)} .lm .c4 h4{background:var(--warn)}
  .lm .col ul{list-style:none;margin:0;padding:0;display:grid;gap:8px}
  .lm .col li{border-radius:var(--radius-sm);padding:9px 11px;font-size:12.5px;box-shadow:var(--shadow)}
  /* node types read distinctly: activity = solid, output = outlined, outcome = warn-toned */
  .lm .c2 li{background:var(--accent);color:#fff;border:1px solid var(--accent)}
  .lm .c3 li{background:var(--bg);color:var(--ink);border:1.5px dashed var(--accent-2)}
  .lm .c4 li{background:var(--warn-soft);color:var(--ink);border:1px solid var(--warn)}
  .lm .c1 li{background:var(--bg);color:var(--ink);border:1px solid var(--line)}
  .lm .outc{display:grid;gap:6px}
  .lm .outc .sub{font-size:10.5px;text-transform:uppercase;letter-spacing:.03em;color:var(--faint);font-weight:600}
  /* the load-bearing output→outcome dependency edge, drawn across the c3|c4 gap */
  .lm .dep{position:absolute;top:52px;left:calc(75% - 20px);width:40px;height:22px;z-index:2}
</style>
<div class="lm reveal" data-stagger>
  <div class="col c1"><h4>Inputs</h4><ul><li>FP&amp;A team &amp; model</li><li>VDR data, advisors</li></ul></div>
  <div class="col c2"><h4>Activities</h4><ul><li>Score &amp; validate</li><li>Quantify synergies</li></ul></div>
  <div class="col c3"><h4>Outputs</h4><ul><li>Diligence memo</li><li>Pro forma model</li></ul></div>
  <div class="col c4"><h4>Outcomes</h4>
    <div class="outc">
      <div><div class="sub">Short</div><ul><li>Bid / no-bid decision</li></ul></div>
      <div><div class="sub">Long</div><ul><li>Realized value vs model</li></ul></div>
    </div></div>
  <svg class="lm dep" viewBox="0 0 40 22" aria-hidden="true">
    <defs><marker id="lmA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)"/></marker></defs>
    <path class="e-dep draw" d="M2 15 H34" marker-end="url(#lmA)"/>
    <text class="edge-lbl dep" x="4" y="9">drives</text>
  </svg>
</div>
<p class="note">Left→right: what goes in, what we do, what it produces, and — the link that matters — what those outputs <em>drive</em>. The output→outcome edge is <code>.e-dep</code> because a diligence memo only earns its keep if it changes the decision and the realized result.</p>
```

## Design rules

General guidance (per Figma's flowchart rules). Treat these as defaults that give a
diagram a sense of *growth and change* — not a rigid checklist. This is an
infographic, not an engineering flowchart, so apply them where they help:

- **Generally start and end clearly.** Most process diagrams read better with a
  defined start and an explicit end / output. A terminator (stadium) shape is fine
  but optional.
- **Connect steps with arrows.** Show direction explicitly — prefer animated draw-on
  / marching-ant arrows so the order is visible, not assumed.
- **One direction, logical order.** Reads left→right or top→bottom, consistently;
  don't make the eye backtrack.
- **Show the *real* decision graphically.** At a genuine go/no-go, a diamond with
  labelled branches (the *decision gate* component) earns its place and looks great.
  Don't add diamonds or terminators to ordinary steps.
- **Terse text.** A few words per box; detail goes in the caption or an expandable.
- **Symbols are optional.** Standard flowchart symbols (diamonds, parallelograms,
  stadiums) are available when they aid clarity, but the infographic treatments —
  colour-coded icon flows, the phase swimlane matrix, decision bands, converging
  inputs — are usually the better default. Don't over-anchor on "the correct symbol".
- **Animate the path, not the meaning.** Draw-on connectors and staggered reveals
  help the eye follow the sequence, but the chart must be fully readable with motion
  off (see `motion.md`).

**Robust SVG sizing (avoid the "huge lines" bug).** Always give an inline `<svg>`
an explicit `width` and `height` attribute (or a CSS `width`+`height`). An SVG with
a `viewBox` but no height — sized only by a flex-basis — balloons to the ~150px
replaced-element default and the stroke stretches into giant distorted lines. Keep
arrow paths *inside* the `viewBox` so you don't need `overflow:visible`; give each
`<marker>` a unique id when several appear on one page.
