# Motion & Animation

Motion should help the reader *follow* a diagram — trace a sequence, watch a value
build, draw a path — never decorate or distract. The page must be completely
legible with motion off; every effect here degrades gracefully and is disabled
under `prefers-reduced-motion`.

There are two ways to deliver motion. Default to the first.

## 1. Animated in-page HTML (default)

The template (`assets/template.html`) ships a small, dependency-free motion layer.
It keeps the deliverable a single self-contained `.html` file that animates live in
any browser. You opt a component in with a class or attribute — no JS to write.

| Effect | How to use | Good for |
| --- | --- | --- |
| **Reveal on scroll** | add `class="reveal"` to a block | bringing each section/diagram in as the reader arrives |
| **Staggered children** | add `data-stagger` to a container | steps/cards appearing in sequence (flow order) |
| **Draw-on connector** | add `class="draw"` to an SVG `<path>`/`<line>` | tracing arrows along a flowchart in order |
| **Marching ants** | add `class="ants"` to an SVG stroke | showing an active/continuous flow on an edge |
| **Sheen sweep** | add `class="flow-ants"` to an HTML bar/track | a subtle "in motion" cue on a connector bar |
| **Count-up** | wrap a number in `<span data-count="42">42</span>` | KPI / stat cards animating up on view |

And four effects whose job is to **encode a specific relationship** — reach for
the one that matches the relation the diagram carries:

| Effect | How to use | Relationship it encodes |
| --- | --- | --- |
| **Traveling dot** | `<circle class="flow-dot" data-follow="#pathId" r="3.5"/>` after an SVG path with an `id` | *direction* of a dependency/flow — the dot runs source→target on loop while in view |
| **Decision lights up** | container gets `data-branch`; chosen path elements `.br-on`, rejected `.br-off` | *decision* — after reveal, the rejected branch dims (opacity + grayscale), the chosen path stays lit |
| **Handoff flash** | `class="handoff-mark"` on the marker where an arrow crosses a lane (gets `.in` on reveal) | *ownership transfer* — one ripple flags each swimlane crossing |
| **Hover-to-trace** | container `data-trace`; nodes `data-node="id"`; edges `data-link="a b"` | *connectedness* — hover/focus a node: its edges + neighbors stay lit, everything else dims. For dense maps (concept maps, theme↔owner matrices) |

Reduced-motion behavior: the dot hides (the arrowhead still shows direction), the
branch dim applies instantly (final state, no transition), the handoff ripple is
suppressed (the distinct `.e-handoff` dash still marks the crossing), and trace
transitions are instant. The final, motion-off state always carries the full
meaning.

Guidance:

- **Sequence matters.** On a flowchart, put `data-stagger` on the step container
  and `class="draw"` on the connectors so the path appears to build in reading
  order. That's the payoff — the reader's eye is led through the process.
- **One or two effects per section.** Reveal + draw is plenty. Stacking every
  effect everywhere is noise, which violates the data-ink principle as much as
  clutter does.
- **Keep the final state correct.** Always include the real values/text in the
  markup (e.g. `<span data-count="42">42</span>` shows `42` with JS off). Motion
  animates *to* the true state; it never invents or hides it.
- **Reduced motion is automatic.** The template disables transforms, ants, and
  draw-on, and snaps numbers to final, when the OS requests reduced motion or when
  printing. Don't add motion that can't be turned off this way.
- **Don't animate essentials behind a delay the reader might miss.** Reveal is a
  gentle rise from ~85% opacity, not a long fade from invisible; nothing critical
  should be unreadable mid-animation.

The flowchart components in `flowcharts.md` already use these classes — paste them
and the motion works.

## 2. Exported MP4 via HyperFrames (optional)

When the user wants a **shareable video clip** of a diagram — for a slide, a Teams
message, a screen with no browser — render it to MP4 instead of (or in addition
to) the in-page version. Use the HyperFrames workflow rather than reinventing a
renderer.

When to reach for this:

- The ask is explicitly a "video", "clip", "animation file", "for the deck", or
  "for the screen in the lobby".
- A single hero diagram (a phase-gate track, a build-up, a flow) carries the
  message and benefits from controlled, timed motion.

How to do it (high level — defer to the HyperFrames skills for specifics):

1. Build the diagram as a HyperFrames composition (HTML, timed with the framework's
   `data-*` attributes and a single paused timeline). The in-page component is a
   good starting point, but HyperFrames owns the timing — read the `hyperframes`
   entry skill first; it routes to `hyperframes-core` (composition contract) and
   `hyperframes-animation` (motion).
2. Render to MP4 with the HyperFrames CLI (`hyperframes render`), or the HeyGen
   HyperFrames MCP if working in a hosted chat with no local filesystem.
3. Deliver the `.mp4` alongside the self-contained `.html` page.

Keep this path scoped to one or two key diagrams — the whole page does not become a
video. The HTML page with the in-page motion layer remains the primary deliverable;
the MP4 is an add-on for a specific distribution channel.

## Honesty still applies

Animation is subject to every guardrail in `design-principles.md`. A count-up must
count to a real figure from the source (never a placeholder dressed up as data); a
build-up bar must reach a true value; a drawn path must trace the real process.
Motion that makes an empty framework *look* like it has data is a failure.
