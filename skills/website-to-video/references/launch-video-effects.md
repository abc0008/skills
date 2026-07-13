# Launch-Video Effects — Proven Patterns from Shipped HyperFrames Videos

A pattern library mined from HeyGen's `hyperframes-launches` repo (16 launch videos, 146 compositions).
This file is the **WHERE-IT'S-PROVEN** layer: `capabilities.md` is the WHAT, `techniques.md` is the
HOW, and this is the WHO-SHIPPED-IT — real effects with exact source line numbers you can copy.

> **How to read this file.** Scan the **Lookup table** below; jump to the technique you need.
> **Do NOT read linearly.** Canonical runnable examples for the starred effects are bundled in
> `assets/effect-examples/` (open the file, copy the cited line range). Full originals + every other
> effect are in the companion `hyperframes-launches/` repo dump.

## The contract these examples assume (same as capabilities.md)

All examples are seek-safe: one paused GSAP timeline on `window.__timelines["id"]`; no
`Math.random` / `Date.now` / `requestAnimationFrame` / `repeat:-1`; `gsap.set()` rest states first;
constants measured once at init; text reveals animate `width`/`clipPath`, not live DOM text; Lottie
frames and shader `u_time` are driven by tweened proxies. Lift the habits with the code.

## Lookup table — effect → bundled example → original `:line`

| Effect | Bundled example (`assets/effect-examples/`) | Original in repo dump `:line` |
| --- | --- | --- |
| **Typewriter — cleanest** ★ | `typewriter_cleanest_textcontent-slice.html` | `sfx-music-launch/compositions/terminal-sfx.html:183-189` |
| Typewriter — all 6 variants | `typewriter_terminal_all-variants.html` | `HF-heygen-stripe/compositions/terminal.html:128-153` |
| Blinking cursor (seek-safe) ★ | `typewriter_cleanest_textcontent-slice.html` | `sfx-music-launch/compositions/terminal-sfx.html:179-181` |
| **Domain-warp generative background** ★ | `shader_domain-warp_generative-bg.html` | `hyperframes-launch/compositions/flex-shader.html:78-148` |
| Domain-warp dissolve transition | `shader_domain-warp_dissolve-transition.html` | `texture-launch-video/compositions/domain-warp-dissolve.html:326-377` |
| Ray-march cursor god-rays | `shader_raymarch_cursor-godrays.html` | `vfx-heygen-combined/compositions/vfx-text-cursor.html:448-545` |
| **Canvas2D procedural engine (ASCII lightning)** | `canvas2d_ascii-lightning-engine.html` | `hyperframes-launch/compositions/canvas-close.html:381-509` |
| **Halftone / dot-matrix background system** ★ | `background_halftone_motion-lab.html` | `inspector-launch/background-studies/halftone-motion-examples.html:425-899` |
| **Liquid-glass panel** ★ | `glass_liquid-glass-player.html` | `hyperframes-launch/compositions/glass-intro.html:79-103` |
| **Lottie seek-safe driver** ★ | `lottie_seek-safe-driver.html` | `cloud-render-launch/compositions/checks.html:24-37` |
| **3D-CSS rotary word drum** | `css3d_rotary-word-drum.html` | `HF-heygen-stripe/compositions/rotary.html:21-78` |
| **Scroll-synced line reveal** ★ | `uimotion_scroll-synced-reveal.html` | `claude-paper-launch/compositions/response-scroll.html:326-362` |
| **Number / money count-up ticker** ★ | `uimotion_money-count-up-ticker.html` | `spacex-launch/compositions/apple-money-count.html:170-306` |
| Container morph (resize + crossfade) | `morph_container-resize-crossfade.html` | `claude-paper-launch/compositions/connector-morph.html:503-573` |
| Aurora end-card + DOM particles | `particles_aurora-end-card.html` | `website-to-hyperframes/compositions/act-4-end-card.html:65-280` |
| SVG handwriting + panel morph | `svg_handwriting-and-panel-morph.html` | `frame-md-launch-storyboard/compositions/scene-02-diagnosis.html:194-327` |
| Micro-FX grab-bag (spinners, pulses, bars, flip) | `microfx_css-gsap-grabbag.html` | `hyperframes-launch/compositions/flex-css.html:129-323` |

## Why this is useful inside website-to-video

Step 5 (build) already lets the agent invent any browser-renderable effect. This library shortcuts
the most common website-video beats to a known-good, render-deterministic source:

- **Opener / cold-open** → typewriter terminal, or a scene melt via domain-warp dissolve.
- **Background bed for any beat** → domain-warp "living gradient" or the halftone field (re-theme via one `colors[]`/palette swap).
- **Showcase a captured screenshot** → liquid-glass player frame; or RGB-split / portal reveal for a hero.
- **Stat / proof beat** → money count-up ticker, parallel progress dashboard, digit-stack odometer.
- **Scrolling content from the site** → scroll-synced line reveal (each line lands at a fixed read-line).
- **End card / CTA** → aurora + DOM particles, converging motion-blur lockup, zoom-through logo handoff.
- **Scene seams** → the house "cut-the-curve" (accelerate+blur out → decelerate+blur in, mirrored direction).

## Effect notes (condensed; see the bundled file for full code)

### Typewriter & cursor
6 implementations exist. **Default to the `textContent.slice` counter tween** — wrap-safe, font-safe,
~6 lines: `tl.to({n:0},{n:str.length,ease:"none",onUpdate(){el.textContent=str.slice(0,Math.round(n))}})`.
Pair with the `steps(1)` yoyo caret blink (finite, timeline-tied). Use `clipPath:inset()`+`steps(N)`
when you want zero per-frame callbacks; use measured-`width` when the caret must hug the exact text edge.

### Backgrounds
`flex-shader.html` is the smallest copy-paste living gradient (cascaded `fbm(p+fbm(p+fbm(p)))` + cosine
palette, one `u_time`, Canvas2D fallback). The halftone field samples that warped noise per dot so it
reads as a video texture; `setBgTransition` makes the field bloom ~0.1s ahead of each cut.

### Glassmorphism
Recipe: 4-stop low-alpha white `linear-gradient` + `backdrop-filter:blur(14px) saturate(1.12)` + 1px rim
border + two box-shadows (outer depth + `inset` top highlight). Keep media children at higher `z-index`
so they stay sharp through the panel's backdrop blur.

### Lottie
Always: `loop:false, autoplay:false` → capture `goToAndStop` → no-op the native method → drive a
`{frame}` proxy via `tl.to(...,{onUpdate})`. This is the only render-deterministic way to scrub Lottie.

### Count-up
`tl.to({v:0},{v:TARGET,onUpdate:()=>el.textContent='$'+Math.round(v).toLocaleString()})`. For the money
showpiece, add a golden-angle (`i*2.399963`) particle fan-out on complete.

### Scene transitions
"Cut-the-curve" is the dominant grammar: outgoing `{y:-150…-280, blur(10–30px), power3.in}`, incoming
starts mirrored and decelerates `expo.out`. Encode implied camera direction in the offsets and mirror it
across the file boundary so a hard cut reads as one continuous move.

---

*Source: github.com/heygen-com/hyperframes-launches — mined across all 146 compositions. The companion
`HYPERFRAMES-EFFECTS-GUIDE.md` (and `effects-signal-index.csv`) hold the full catalog for every file.*
