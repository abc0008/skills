# Worked examples

Two gold-standard outputs with the exact source documents that produced them. Open
the `output.html` files in any browser — they are fully self-contained and animate
on load/scroll. Read them alongside the `input.md` to see how dense prose/tables
become relationship-first diagrams. These are reference targets for the quality bar;
reuse their patterns, don't copy their content.

## board-explainer/  (the flagship)

- `input.md` — a ~1,000-line commercial-bank M&A due-diligence framework (dense,
  table-heavy, full of `TBD` placeholders).
- `output.html` — a board walkthrough that distills it into one page. Demonstrates
  the components users liked most:
  - **gated process flow** — all six phases in sequence with the two *real* go/no-go
    decisions branching inline (diamond markers + outcome chips), not carved out.
  - **phase × function swimlane matrix** — "who does what, when"; FP&A fills every
    column (the spine).
  - **spine / backbone** — the five FP&A workstreams laid across phases (timing),
    with specialist functions feeding in (dependency).
  - **theme ↔ owner matrix** — overlap and the Finance hub, instead of a flat list.
  - **converging inputs → decision** — five dimensions all pointing at one call.
  - **grouped convergence** — deliverables grouped by category, each with its owner,
    funnelling into the final memo.
  - **2×2 likelihood/impact risk matrix**, colour-coded **stat cards**, and a
    **phase timeline** with sub-steps.

## swimlane-matrix/  (the favourite diagram)

- `input.md` — the FP&A-led M&A diligence playbook (roles, phase gates, workstreams).
- `output.html` — leads with the phase × function swimlane matrix users called the
  best diagram: rows are functions (icon + colour), columns are phase gates, the
  deal flows left→right, empty cells mean no distinct deliverable that phase.

## How the motion works (important)

**The animation is plain in-page CSS + a few lines of vanilla JS — there is no
HyperFrames, no Remotion, no build step, and no external dependency.** Everything
lives inside the single `.html` file. The motion layer is defined in
`assets/template.html` and documented in `references/motion.md`. You opt a component
in with a class or attribute:

| Effect | How | Implementation |
| --- | --- | --- |
| reveal on scroll | `class="reveal"` | IntersectionObserver adds `.in`; CSS fades/rises it |
| staggered children | `data-stagger` | children get incremental `transition-delay` |
| draw-on connector | `class="draw"` on an SVG `<path>` | JS sets `--len` to `getTotalLength()`; CSS animates `stroke-dashoffset` |
| marching-ant arrow | repeating-linear-gradient + `@keyframes` | pure CSS, on the connector pseudo-element |
| count-up number | `data-count="42"` | `requestAnimationFrame` counts to the real value |

All of it is **reduced-motion-safe and print-safe**: a `@media (prefers-reduced-motion: reduce)`
block (and `@media print`) disables transforms/animation and snaps to the final
state, so the page is fully legible with motion off. To see the static state, open
the file with OS "reduce motion" on, or print to PDF.

### If you specifically want a video (MP4), then use HyperFrames

Only reach for HyperFrames when the deliverable is a **standalone video clip** of a
diagram (for a slide, a Teams message, a lobby screen) — not for the page itself.
That optional path is described in `references/motion.md` ("Exported MP4 via
HyperFrames"): build the diagram as a HyperFrames composition (HTML on a single
paused timeline), then `hyperframes render` to MP4. The self-contained HTML page
stays the primary deliverable; the MP4 is an add-on.
