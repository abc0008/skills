# External Diagram Tools (Figma, Mermaid, tldraw, Canva, …)

Most diagrams should be built with the native components in `flowcharts.md` and
`diagram-catalog.md` — they're fast, themeable, animatable, and self-contained. But
for a **bespoke or complex diagram**, or when the user already has an asset in a
design tool, you can author/fetch it in an external MCP and bring it into the page.

**The contract: the deliverable is always the self-contained HTML page.** Whatever
the external tool produces must end up *inside* the one `.html` file — as inline SVG
(strongly preferred) or a base64-embedded PNG (fallback). The page must still open
with no network dependency.

## Decision: native component vs external tool

Reach for an external tool only when it clearly pays off:

- **Use a native component** when the diagram is one of the known forms (flow,
  swimlane, decision tree, scorecard, phasing, etc.). Faster, on-theme, animated.
- **Use an external tool** when: the diagram is genuinely bespoke (a custom system
  map, an unusual layout), the user points you at an existing Figma/Lucid/Miro file,
  or they explicitly ask to "build it in Figma / Mermaid / etc."

When unsure, build native first; escalate to an external tool only if it falls short.

## Which tools are available

Check what's connected with the connector registry (`search_mcp_registry`,
keywords like `figma`, `diagram`, `mermaid`). Commonly available:

| Tool | Good for | What you get back | Bring-in format |
| --- | --- | --- | --- |
| **Figma** | bespoke design, existing Figma frames, FigJam | design context, node screenshot, generated diagram, variables | export node as **SVG** → inline; or screenshot → PNG |
| **Mermaid Chart** | flowcharts/sequence/graphs from a text spec | validated diagram rendered to **SVG** | inline the SVG |
| **tldraw** | hand-style sketches, freeform canvas | shapes on a canvas; export | export canvas → **SVG** → inline |
| **Canva** | branded, polished layouts | a Canva design; `export-design` | export **PNG/SVG** → embed |
| **Lucid / Miro / Whimsical** | org charts, mind maps, board diagrams | a diagram doc; export/share | export **SVG/PNG** → inline/embed |

If a needed tool isn't connected, call `suggest_connectors` so the user can connect
it — don't silently fall back to a worse approach.

## The workflow

1. **Decide** native vs external (above). If external, pick the connected tool that
   fits.
2. **Author / fetch** the diagram in that tool. For Figma, that may be
   `generate_diagram` (create), `get_design_context` / `get_metadata` (read an
   existing frame), `get_variable_defs` (pull brand variables), or `get_screenshot`
   (raster preview). Discover the exact tool I/O at call time — schemas vary.
3. **Get it as SVG if at all possible.** SVG inlines cleanly, scales crisply, can be
   recolored to the page theme, can carry `<title>`/`<desc>`, and can be animated.
   Only fall back to PNG when SVG isn't available.
4. **Bring it into the page and reconcile it** (next section).
5. **Verify** it renders in context (open the HTML, screenshot it) — external SVGs
   often carry surprises (huge viewBoxes, clipped text, hardcoded colors).

## Reconciling an external SVG with the page

A raw export rarely matches the page out of the box. Fix these before shipping:

- **Theme the colors.** External SVGs hardcode hex fills. Map the main fills/strokes
  to the page palette (`var(--accent)`, `var(--ink)`, `var(--line)`, etc.) so the
  diagram doesn't clash. At minimum, neutralize off-brand colors.
- **Size it responsively.** Ensure a `viewBox` is present and drop fixed pixel
  `width`/`height` (or set `style="width:100%;height:auto"`) so it scales in the
  column.
- **Accessibility.** Add `role="img"` and `<title>`/`<desc>` describing what it
  shows; make sure text has enough contrast.
- **Strip cruft.** Remove editor metadata, unused `<defs>`, clip paths you don't
  need. Keep the file lean.
- **Optional motion.** Add `class="reveal"` to the wrapper, or `class="draw"` to key
  connector `<path>`s, to fold it into the page's motion layer (see `motion.md`).
- **Pair with text.** Like every visual, give it a takeaway heading and an
  explanatory caption. The external tool made the picture; you still write the "so
  what".

## Embedding a PNG (fallback)

If only a raster is available, embed it base64 so the page stays self-contained:

```html
<figure class="reveal" style="margin:0">
  <img src="data:image/png;base64,iVBORw0K…" alt="REPLACE — describe the diagram"
       style="width:100%;height:auto;border:1px solid var(--line);border-radius:var(--radius)">
  <figcaption class="caption"><strong>What to notice:</strong> REPLACE.</figcaption>
</figure>
```

Note the trade-offs: PNG can't be recolored to the theme, won't animate, and looks
soft when scaled. Prefer SVG whenever the tool can give it.

## Honesty still applies

An externally-built diagram is held to the same guardrails: real labels and figures
from the source, no invented numbers, scale not distorted, the source's caveats
carried into the caption. A polished Figma frame doesn't get a pass on accuracy.
