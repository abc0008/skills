# Effect Examples — manifest

Canonical, runnable HyperFrames compositions, one per major technique, lifted from
HeyGen's `hyperframes-launches` launch videos. Each is self-contained HTML; open it and copy the
cited line range. Renamed `technique_descriptor.html` for browsing; original path noted below.

| Bundled file | Technique | Key lines | Original path |
| --- | --- | --- | --- |
| `typewriter_cleanest_textcontent-slice.html` | Typewriter (textContent.slice) + seek-safe caret | 179-189 | `sfx-music-launch/compositions/terminal-sfx.html` |
| `typewriter_terminal_all-variants.html` | Measured-width typewriter, terminal + headline | 128-153 | `HF-heygen-stripe/compositions/terminal.html` |
| `shader_domain-warp_generative-bg.html` | Domain-warp "living gradient" background (GLSL) | 78-148 | `hyperframes-launch/compositions/flex-shader.html` |
| `shader_domain-warp_dissolve-transition.html` | Domain-warp scene-melt transition (GLSL) | 326-377 | `texture-launch-video/compositions/domain-warp-dissolve.html` |
| `shader_raymarch_cursor-godrays.html` | Volumetric ray-march cursor light (GLSL) | 448-545 | `vfx-heygen-combined/compositions/vfx-text-cursor.html` |
| `canvas2d_ascii-lightning-engine.html` | Canvas2D ASCII lightning + BFS charge crawl | 381-509 | `hyperframes-launch/compositions/canvas-close.html` |
| `background_halftone_motion-lab.html` | Halftone dot-matrix field + 8 transition recipes | 425-899 | `inspector-launch/background-studies/halftone-motion-examples.html` |
| `glass_liquid-glass-player.html` | Liquid-glass player panel (CSS) | 79-103 | `hyperframes-launch/compositions/glass-intro.html` |
| `lottie_seek-safe-driver.html` | Seek-safe Lottie driver (goToAndStop override) | 24-37 | `cloud-render-launch/compositions/checks.html` |
| `css3d_rotary-word-drum.html` | 3D-CSS rotary word cylinder | 21-78 | `HF-heygen-stripe/compositions/rotary.html` |
| `uimotion_scroll-synced-reveal.html` | Auto-scroll w/ inverse-ease line reveal | 326-362 | `claude-paper-launch/compositions/response-scroll.html` |
| `uimotion_money-count-up-ticker.html` | Money count-up + golden-angle particle burst | 170-306 | `spacex-launch/compositions/apple-money-count.html` |
| `morph_container-resize-crossfade.html` | Container "morph" (resize + layer crossfade) | 503-573 | `claude-paper-launch/compositions/connector-morph.html` |
| `microfx_css-gsap-grabbag.html` | Spinners, sonar pulses, bar chart, shape morph, 3D flip | 129-323 | `hyperframes-launch/compositions/flex-css.html` |
| `particles_aurora-end-card.html` | Aurora gradient + DOM twinkle particles end-card | 65-280 | `website-to-hyperframes/compositions/act-4-end-card.html` |
| `svg_handwriting-and-panel-morph.html` | SVG handwriting draw→fill + doc→browser→slide morph | 194-327 | `frame-md-launch-storyboard/compositions/scene-02-diagnosis.html` |

All examples obey the seek-safe contract (`window.__timelines`, no wall clock). Preview any with
`hyperframes preview` or open directly in a browser; append `?t=<seconds>` to seek.

License/source: github.com/heygen-com/hyperframes-launches.
