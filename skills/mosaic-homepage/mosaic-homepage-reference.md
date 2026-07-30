# Mosaic homepage prototype

This package contains the standalone interactive reference for the Mosaic
Agentic Finance Platform homepage.

## Paired files

- `mosaic-homepage.html` — self-contained interactive prototype
- `mosaic-homepage-reference.md` — this implementation and design reference

The HTML has the Mosaic 3C.4N on-dark wordmark embedded as a data URI. It does
not require the original Downloads directory, a build step, or network access.

## Opening the prototype

Open `mosaic-homepage.html` directly in a browser. For a local HTTP URL:

```bash
cd /path/to/the/downloaded/files
python3 -m http.server 8765
```

Then visit:

```text
http://127.0.0.1:8765/mosaic-homepage.html
```

## Experience structure

1. Persistent Mosaic application sidebar with the existing item groupings.
2. Full-viewport strategic-finance thesis.
3. One `400vh` narrative runway containing a single sticky viewport.
4. Four scroll-driven motif states rendered inside that stationary viewport.
5. Grouped Mosaic workspace directory after the pinned sequence.

The viewer remains spatially anchored while the active motif changes. The
outgoing chapter exits upward and the next chapter rises from below.

## The four motifs

### 01 — Input / Output

A micro-tessera pipeline moves independent inputs through a controlled compute
matrix into a structured governed output.

Right-side sequence:

```text
Assumption + decision → compute → plan-of-record output
```

### 02 — Ambient Agents

A tessellated perimeter, distributed sensor nodes, scanning rail, and central
analytic core represent continuous control infrastructure without using a
character-like robot.

Right-side sequence:

```text
Observe ledger activity → classify rows → surface anomalies → draw activity
```

### 03 — Commentary Captured

Ragged narrative tiles become citation lineage, a structured institutional
record, and a retrieved prior judgment.

Right-side sequence:

```text
Analyst disposition → citations lock → commentary becomes retrievable context
```

### 04 — Agentic Analysis

Deterministic analytical components resolve into an agent-created synthesis,
then pass to a spatially separate human review and approval checkpoint.

Right-side sequence:

```text
Decompose variance → synthesize draft → review → edit → approve
```

## Brand construction

The motif symbols are derived from the Mosaic 3C.4N production wordmark:

- Tessera size: `5.6px`
- Grid pitch: `6.4px`
- Transparent gap: `0.8px`
- Structural navy: `#14385C`
- Active/action blue: `#0074C4`
- Secondary sky: `#8EC6E6`
- Canvas: `#EBEBEB`

On the navy pinned viewport, frost tiles establish structure, blue tiles carry
active signals, and sky tiles indicate resolved or retrieved output.

## Sticky-scroll mechanics

The sequence follows the supplied ToolMorpher pattern without an animation
library:

```js
runway = sequenceHeight - viewportHeight
progress = clamp(-sequenceTop / runway, 0, 1)
raw = progress * motifCount
active = min(motifCount - 1, floor(raw))
localProgress = clamp(raw - active, 0, 1)
```

The outer sequence is `400vh`. Its inner frame is `position: sticky`, `top: 0`,
and `height: 100vh`. Every motif remains mounted in the same frame; active state
changes opacity, vertical offset, scale, and pointer events.

## Internal animation gate

Symbol and right-side animations begin only when both conditions are satisfied:

```text
local segment progress ≥ 35%
and
chapter transition has been settled for 440ms
```

This separates the chapter transition from the internal visual choreography.
Animations replay if the user leaves a motif and later returns.

## Motion behavior

- Chapter changes: crossfade with upward/downward `40px` offsets and subtle
  `0.975 → 1` scale.
- Input/output: input cards resolve before compute and governed output.
- Ambient agents: rows stagger in, bars grow from the baseline, and monitoring
  continues with a restrained scan.
- Commentary: narrative reveals, citations lock, then prior context returns.
- Agentic analysis: deterministic bridge cells resolve before the draft; human
  review, edit, and approval follow sequentially.
- `prefers-reduced-motion: reduce` disables animation and presents final,
  legible states immediately.
- Below the desktop breakpoint, motifs become ordinary stacked sections.

## Application integration reference

The corresponding React/Next implementation is maintained in:

```text
/Users/alexcardell/Downloads/MosaicHomePage.jsx
/Users/alexcardell/Downloads/mosaichomepage.tsx
```

Important integration behavior:

- Authentication remains owned by `useAccount` and `SignInGate`.
- Sidebar and homepage groupings continue to derive from `navGroups`.
- The homepage does not replace or independently recreate the application
  sidebar.
- `MotifSequence` reads the application's internal scroll container rather than
  `window`.
- `MotifSymbol` renders deterministic inline SVG; no icon library or remote
  image dependency is required.
- `MotifVisual` receives `active` and `shouldAnimate` from the pinned sequence.

## Supplied source references

Brand masters:

```text
mosaic-3c4n-primary.svg
mosaic-3c4n-on-dark.svg
mosaic-3c4n-monochrome.svg
mosaic-3c4n-footer.svg
```

Motion reference:

```text
ToolMorpher — Sticky Scroll Animation Spec
```

## Validation completed

- Four motif symbols present.
- Four pinned motif states present.
- Sticky panel remains fixed while document scroll advances.
- Scroll-driven active index and progress indicator verified.
- Internal animation gate exercised for all four motifs.
- Persistent sidebar retained.
- Product directory remains available after the narrative sequence.
- Standalone HTML contains the embedded Mosaic wordmark.
- React JSX source parses successfully with Babel.
