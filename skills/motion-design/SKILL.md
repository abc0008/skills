---
name: "motion-design"
description: "Builds editorial (Vox-style) motion graphics in HTML: explainer icons (/motion-design icons) and data animations that pull the eye to the key number (/motion-design data). Uses Lucide icons, pairs with doc-to-infographic, exports GIFs for PowerPoint."
---

# Motion Design: explainer icons and data animation

Two things, one style:

- **A. Explainer icons**: small looping motion graphics that act out the core
  concept of a slide or section.
- **B. Data animation**: charts, tables and figures that build, then pull the
  viewer's eye to the key number or the point of the data.

In both, **the motion must relate to the core concept on the slide and help
explain it.** Motion that only decorates is a failure.

## Operating rules (minimal input)

- **Ask nothing.** Given a slide, deck, infographic page, a table of numbers or a
  sentence, derive the concept and build. Ask only if there is no content at all.
- **Commands.** The first word after `/motion-design` picks the mode; anything
  after it is the source (a URL, a file, pasted text or numbers, or nothing to
  use the page just built):

  | Command | What it makes |
  | --- | --- |
  | `/motion-design icons <source>` | explainer icons only (category A), one per major point |
  | `/motion-design data <source>` | data animations only (category B), one per figure, table or key statistic in the source |
  | `/motion-design both <source>` or no mode word | both, chosen per slide from the content (the rule below) |
  | add `pptx` anywhere | also export GIFs, build a .pptx with one graphic per slide, and render-check it |
  | add `gifs` anywhere | export the GIFs and stills only |

  Plain language works too: "animated icons for...", "explainer icons",
  "concept icons" mean `icons`; "animate this chart / table / these numbers",
  "data animation", "make the key number pop" mean `data`.
  In `data` mode with a text source, first list every number the source states,
  then build one animation per number or comparison worth showing; if the source
  has no numbers, say so and build nothing.
- **Pick the category from the content** (when no mode word is given): a slide
  whose point is an idea or mechanism gets an explainer icon (A); a slide whose
  point is in numbers gets a data animation (B). One motion graphic per slide.
- **Bare invocation** on a deck or infographic: do every slide/section that makes
  a claim. Skip title and agenda slides.
- **Output**: the graphics written into the HTML, a short log (slide, concept or
  key number, what the motion does), and, if the deck is headed to PowerPoint,
  exported GIFs (see Verify and export).
- Inline SVG/HTML + CSS keyframes only. No libraries, no JS needed to play.

## House style: editorial explainer (Vox-inspired)

Flat, bold, confident. Looks like a news explainer, not a dashboard.

- **Palette**: warm paper background, near-black ink, grey for everything that is
  not the point, one yellow highlighter, one red marker pen. Nothing else.
- **Type**: heavy sans, tight tracking, short labels. Numbers are big and bold.
- **Annotation language**: highlighter sweep behind the key number or phrase;
  hand-drawn marker circle, underline, bracket or arrow pointing at it. Marker
  paths are slightly imperfect curves (overshoot the join), never geometric.
- **Motion**: simple and snappy. Things arrive fast and settle (`--snap`), lines
  draw on, then one deliberate focus move. No bounce, no spin, no 3D.
- **Stepped feel**: export GIFs at 12 fps; it suits the style and keeps files small.
- If the host page or deck has its own palette (`--ink`, `--accent`, a white
  background), inherit it: map `--mark` to the accent and keep the yellow
  highlighter only if it does not clash.

### Base CSS (include once per page; tested)

```css
:root{--paper:#f4efe4;--ink:#191919;--mute:#c9c2b2;--mute-text:#8d8676;--hl:#ffd60a;--mark:#e5381c;
  --io:cubic-bezier(.645,.045,.355,1);--out:cubic-bezier(.165,.84,.44,1);--snap:cubic-bezier(.19,1,.22,1);
  --font:"Helvetica Neue",Helvetica,Arial,sans-serif}
.mo{display:block;background:var(--paper);color:var(--ink);font-family:var(--font)}
svg.mo{width:100%;height:auto;overflow:visible}
.mo text{font-family:var(--font);fill:currentColor}
.mo .ln{fill:none;stroke:currentColor;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.mo .pen{fill:none;stroke:var(--mark);stroke-width:3.5;stroke-linecap:round;stroke-linejoin:round}
.mo .hl{fill:var(--hl)} .mo .key{fill:var(--ink)} .mo .rest{fill:var(--mute)} .mo .rest-t{fill:var(--mute-text)}

/* B. data animation: play once; base state = final frame; keyframes only define `from` */
.mo [class*="d-"]{animation-duration:.5s;animation-delay:var(--at,0s);animation-fill-mode:both;animation-timing-function:var(--out)}
.mo .d-draw{stroke-dasharray:1;stroke-dashoffset:0;animation-name:d-draw;animation-timing-function:var(--io)}
.mo .d-grow{transform-box:fill-box;transform-origin:50% 100%;animation-name:d-grow;animation-duration:.7s;animation-timing-function:var(--snap)}
.mo .d-growx{transform-box:fill-box;transform-origin:0 50%;animation-name:d-growx;animation-duration:.7s;animation-timing-function:var(--snap)}
.mo .d-fade{animation-name:d-fade}
.mo .d-pop{transform-box:fill-box;transform-origin:50% 50%;animation-name:d-pop;animation-duration:.4s;animation-timing-function:var(--snap)}
.mo .d-swipe{transform-box:fill-box;transform-origin:0 50%;animation-name:d-swipe;animation-duration:.35s;animation-timing-function:var(--io)}
.mo .d-recede{animation-name:d-recede;animation-duration:.4s;animation-timing-function:ease;animation-delay:var(--focus,2s)}
.mo .d-fade.d-dim{animation-name:d-fade,d-dim;animation-delay:var(--at,0s),var(--focus,2s);animation-duration:.5s,.4s}
@keyframes d-draw{from{stroke-dashoffset:1;visibility:hidden}1%{visibility:visible}}
@keyframes d-grow{from{transform:scaleY(0)}}
@keyframes d-growx{from{transform:scaleX(0)}}
@keyframes d-fade{from{opacity:0}}
@keyframes d-pop{from{opacity:0;transform:scale(.5)}}
@keyframes d-swipe{from{transform:scaleX(0)}}
@keyframes d-recede{from{fill:var(--ink);stroke:var(--ink);color:var(--ink);opacity:1}}
@keyframes d-dim{from{color:var(--ink)}}
.mo .cost{fill:var(--mark)}
.mo .d-tomark{animation-name:d-tomark;animation-duration:.4s;animation-timing-function:ease;animation-delay:var(--focus,2s)}   /* ink until focus, then red */
@keyframes d-tomark{from{fill:var(--ink)}}
.mo .d-dim{animation-name:d-dim;animation-duration:.4s;animation-timing-function:ease;animation-delay:var(--focus,2s)}        /* text greys at focus */

/* A. explainer icons: loop; every element shares --loop and writes beats as % */
.xicon{--loop:5s}
.xicon *{transform-box:view-box;transform-origin:0 0}
.xicon .draw{stroke-dasharray:1;stroke-dashoffset:0}
.xicon .a-all{animation-name:x-all}                /* wrap the whole icon in <g class="a-all"> for the loop fade */
@keyframes x-all{0%{opacity:0}4%,95%{opacity:1}100%{opacity:0}}
.xicon .ball{fill:var(--mark)}
.xicon .glyph{fill:var(--mark);font:800 30px/1 var(--font);transform-box:fill-box;transform-origin:50% 60%;text-anchor:middle}
.xicon .c{transform-box:fill-box;transform-origin:50% 50%}   /* scale an element about its own centre */
.xicon [class*="a-"]{animation-duration:var(--loop);animation-iteration-count:infinite;animation-timing-function:linear;animation-fill-mode:both}

.mo.static [class*="d-"],.mo.static [class*="a-"]{animation:none!important}
@media print,(prefers-reduced-motion:reduce){.mo [class*="d-"],.mo [class*="a-"]{animation:none!important}}
```

Every motion graphic is an element with class `mo` and a `data-name`. Lines that
draw need `pathLength="1"`. **The base (un-animated) state is always the final,
finished frame**: that is what prints, what reduced-motion shows, and the still.

---

## A. Explainer icons

House example. Concept: *an agent with ambiguous instructions cannot commit to a
path.* Icon: one line splits into three; a ball travels to the fork, starts down
each branch in turn and pulls back; a question mark appears.

**Two tests before an icon ships.** *Cover test*: hide the headline; could a
viewer roughly state the slide's claim? *Freeze test*: stop the motion; if a
still says the same thing, the movement is not carrying the idea, so redesign.
Generic animated pictograms (spinning gear, pulsing lightbulb) fail both.

**Third test, the swap test.** Could this icon be dropped unchanged onto a slide
about a different subject? If yes, it is too generic. An icon made only of
lines, dots and circles almost always fails this. The motion carries the
*mechanism*; the drawn objects must carry the *subject*. Redraw with the
subject's own things until the icon could only belong to this slide.

**Process**

1. **Concept sentence**: the slide's claim as `actor + verb + consequence`, from
   the slide's own words. Do not invent a claim.
2. **Mechanism**: the verb the motion acts out. Pick a motif:

| Mechanism | Motion motif | Payoff |
| --- | --- | --- |
| Can't decide / ambiguity | mover probes each branch and retreats | `?` |
| Decides / routes | mover takes one branch, others dim | chosen path lit |
| Matches / reconciles | pairs connect one by one; one fails | `!` on the leftover |
| Bottleneck / approval wait | movers queue behind a gate that opens briefly | queue remains |
| Converges / consolidates | several movers merge into one node | single output |
| Splits / allocates | one mover divides into parts | parts in place |
| Filters / screens | many enter, few pass | the few |
| Accumulates / compounds | units stack, each step taller | tallest stack |
| Leaks / erodes | level drains through a gap | lower level |
| Loops / iterates | mover circles stations, one lights each pass | improved state |
| Hands off | mover passes between holders; pause at the seam | second holder lit |
| Depends on / blocks | a stuck link stops everything after it | stalled chain |
| Automates | slow manual steps collapse into one fast pass | one stroke |
| Verifies / controls | mover passes a checkpoint and is stamped | check mark |
| Drifts / variance | line tracks a target then pulls away | gap marked |
| Syncs / single source | scattered copies snap to one | one copy |
| Transforms | shape passes through a box and changes form | new shape |
| Escalates | mover climbs levels after being bounced | top level |
| Risk / exposure | boundary takes hits; one gets through | breach marked |
| Grows / scales | same unit repeats outward | filled grid |

   If nothing fits, invent one the same way: who is the actor, what does it do,
   what is left at the end.
3. **Cast the scene from the slide's own nouns.** List the concrete things the
   slide talks about and draw those, not abstract stand-ins:
   - **Actor**: what is actually moving or acting? A question, a query, a dollar,
     a journal entry, a loan file, an analyst, an agent. Draw it as that thing
     (speech bubble, code chip, coin, ledger row, folder, person, sparkle).
   - **Objects**: what does it act on? Tables, a documentation page, a
     dashboard, a GL, a branch, a calendar, a contract. Draw those.
   - **Vocabulary**: let the slide's words do the casting. SQL keywords, metric
     names and example values make an icon specific at once: a `SELECT` chip
     passes a locked gate while a `DROP` chip is bounced; "Australia" goes
     through a SYNONYMS box and comes out "AUS"; three tilted "REV" chips merge
     into one REVENUE box.
   Take each object from the icon set (see below) and choose the most specific
   icon for the noun; hand-draw only what the set lacks.
   A plain ball or dot is the last resort, used only when the actor really is
   abstract (a signal, "work"). Never use a row of identical circles where the
   slide names what those things are.
4. **Three beats**: setup (structure appears), action (the mover does the verb),
   payoff (glyph or end state; hold it).

**Build spec**

- Roles: recognisable objects = the subject matter; the actor (drawn as what it
  is, in `--mark`) does the verb; connecting lines only where there is a real
  path or link; a glyph = the payoff (`?` `!` check, cross, `≠` between results
  that should match, `=` beside something that came back unchanged). Keep each
  object's drawing consistent across a deck so viewers learn it once.
- `viewBox="0 0 120 120"`, 10px margin, round coordinates. Structure stroke 3;
  detail inside objects 1.5-2.5. Each object is a simple pictogram of 2-5
  strokes, about 20-40 units wide, readable at 120px. Up to about 6 objects.
- Text is allowed when it adds the subject: up to three short labels taken from
  the slide's own words (max about 9 characters each, 8.5-10px, weight 800),
  plus one payoff glyph. No sentences.
- Move a drawn object by wrapping it in a `<g>` and animating `translate` on the
  group. If an object needs both a fixed position and an animation, nest two
  groups: outer for position, inner for the animation.
- Structure in ink, actor and payoff in `--mark`. Unvisited/inactive structure at
  `opacity:.4`, raised to 1 while the actor is on it.
- Loop 4-6s. Single moves take 5-9% of the loop. Hold the payoff at least 15%.
  The payoff must be fully on screen by 85% of the loop and stay until 95%: the
  GIF export takes its first frame at 90%.
  Fade everything out over the last 5% so the loop restarts cleanly.
- Travel uses `--io`, appearing uses `--out`, set per keyframe with
  `animation-timing-function`. Hesitation or failure = short out-and-back.
- Move the actor with `transform:translate(Xpx,Ypx)` on a circle with no cx/cy.
  Hide a drawing line (`opacity:0` or `visibility:hidden`) until its draw starts,
  or its round cap shows as a stray dot.
- Prefix each icon's classes and keyframes with its own short name.
- Wrap the icon's contents in `<g class="a-all">` so the fade in/out at the loop
  seam is handled once; individual keyframes then just hold their end state to 100%.
- A path that draws on must be a single stroke. Put arrowheads or a second stroke
  in their own path and fade or draw them after the shaft.
- Several movers doing the same thing share one keyframe set, parameterised with
  a CSS variable: `style="--y:40px"` and `transform:translate(53px,var(--y))`.
- To recolour a multi-part object mid-animation, have its parts use
  `currentColor` and animate `color` on the group.
- Orbiting or a clock hand: put the part in a `<g>` and animate `rotate()`; for
  an orbit set `transform-origin` to the centre in viewBox units.
- Something that fills or grows in steps: scale a `.c` element through stepped
  keyframes.
- Dotted structure (a screen, a path): `stroke-dasharray:.1 7` with round caps.
  Dotted lines cannot also draw on; fade them in.
- After the frame sheet passes, be candid in the log about any icon that only
  marginally passes the cover or swap test, and add a short caption to it.

**Objects come from an icon set first (Lucide).** Do not hand-draw an object
that an icon set already has, and do not keep reaching for the same few shapes.
Lucide has about 2,300 outline icons (24x24, stroke 2, round caps, ISC licence)
that match this style exactly. Pick the icon that is most specific to the
slide's noun: a catalog is `book-open-text`, not a generic page; a dashboard is
`layout-dashboard`; a reviewer is `shield-check` or `bot`; a rating is
`thumbs-up`.

Setup (once per workspace): `npm install lucide-static` in a scratch directory.
Save this helper as `lucide.py` next to it:

```python
import sys, os, re, json
ROOT = next(r for r in ['node_modules/lucide-static', os.path.expanduser('~/iconsets/node_modules/lucide-static')] if os.path.isdir(r))
def inner(name):
    p = f'{ROOT}/icons/{name}.svg'
    if not os.path.exists(p): raise SystemExit(f'no Lucide icon named {name!r}; run: lucide.py find <words>')
    s = re.sub(r'<!--.*?-->', '', open(p).read(), flags=re.S)
    s = re.sub(r'<svg[^>]*>', '', s, flags=re.S).replace('</svg>', '')
    return ''.join(l.strip() for l in s.strip().splitlines())
def lu(name, x, y, size=28, cls='', color=''):
    """Inline <g> centred at (x,y) in the 120 viewBox; size in viewBox units."""
    col = f';color:{color}' if color else ''
    return (f'<g style="transform:translate({x}px,{y}px)"><g class="lu {cls}" '
            f'style="transform:scale({size/24:.3f}) translate(-12px,-12px){col}">{inner(name)}</g></g>')
if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['find']:      # lucide.py find lock permission
        tags = json.load(open(f'{ROOT}/tags.json')); words = [w.lower() for w in a[1:]]
        hits = sorted((-sum((3 if w in n else 1) for w in words if w in n+' '+' '.join(t)), n) for n, t in tags.items())
        print(' '.join(n for sc, n in hits[:40] if sc))
    elif a[:1] == ['g']:       # lucide.py g lock 60 46 28
        print(lu(a[1], float(a[2]), float(a[3]), float(a[4]) if len(a) > 4 else 28))
```

```css
.xicon .lu{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.xicon .plate{fill:var(--hl)}          /* rounded rect drawn behind a chosen icon */
.xicon .off{color:var(--mute-text)}    /* inactive / not chosen */
```

Using icons:
- **Always search, never guess a name**: `python3 lucide.py find <words>` returns
  real names; an unknown name stops the build. Add `<!-- Icons: Lucide (ISC) -->`
  to the page.
- **Size** 24-34 viewBox units for objects, 22-28 for the actor, up to 44 for a
  single hero object. Stroke scales with size, so keep one deck within that
  range for an even line weight.
- **Colour** is `currentColor`: set `color` on the icon group (`--mark` for the
  actor, `off` for inactive, ink for live) and animate `color` to change state.
- **Position and animate on wrappers.** The `lu()` output is a positioned group;
  to move it, replace the outer group with one whose `translate` you animate; to
  pop or pulse it, wrap it in `<g class="c a-...">` inside a positioned group.
  Never put an animation on the `.lu` group itself (it carries the scale).
- **Chosen / found**: draw a `.plate` rounded rect behind the icon and pop it.
- **Stamping a status on something**: a small `badge-check`, `shield-check`,
  `thumbs-up`, `stamp` or `triangle-alert` in `--mark`, popped in from scale 2
  onto the object's top-right corner.
- Icons are open strokes, so anything behind them shows through. Keep paths and
  other objects out from behind an icon, or give it a `--paper` plate.

Verified Lucide names by subject (use `find` for anything else):

| Subject | Icons |
| --- | --- |
| Data | `table-2` `sheet` `database` `database-zap` `layers` `server` `cloud` `network` |
| Documents and code | `file-text` `file-code-2` `file-spreadsheet` `scroll-text` `receipt-text` `book-open-text` `notebook-text` `braces` `terminal` `square-function` |
| Analytics | `layout-dashboard` `chart-column` `chart-line` `chart-pie` `gauge` `trending-up` `trending-down` `percent` `calculator` |
| People and agents | `user-round` `users` `bot` `sparkles` `briefcase` `handshake` `graduation-cap` |
| Conversation | `message-square` `message-square-warning` `circle-question-mark` `mail` `inbox` `send` `bell` |
| Control and trust | `lock` `lock-open` `key-round` `shield-check` `shield-alert` `eye` `pencil-line` `badge-check` `stamp` `triangle-alert` `bug` |
| Checks and lists | `clipboard-list` `clipboard-check` `list-checks` `target` `flag` `thumbs-up` `thumbs-down` `paperclip` |
| Flow | `workflow` `git-merge` `git-branch` `split` `merge` `route` `funnel` `refresh-cw` `repeat` `link-2` `unlink` `history` |
| Time | `clock` `timer` `hourglass` `calendar-days` `calendar-clock` |
| Banking and finance | `landmark` `building-2` `banknote` `coins` `wallet` `receipt-text` `credit-card` `scale` |
| Search and organise | `search` `folder` `folder-search` `tags` `languages` |
| Ideas and speed | `lightbulb` `rocket` `zap` `cpu` |

Other sets, if a deck already uses one: Heroicons outline (MIT, `npm install
heroicons`, 24x24 stroke 1.5), Material Symbols (Apache-2.0), Font Awesome Free
(CC BY 4.0, needs attribution, filled style). Use one set per deck; never mix.

**Variety check.** Before building a deck's icons, list the objects planned for
each slide side by side. The same icon may repeat only when it is the same
thing (the agent is always `bot`, a table is always `table-2`). If two slides
would otherwise look alike (same objects, same layout), recast one of them with
different nouns from its own slide or a different motif.

**Hand-drawn kit (tested).** Use these only for what an icon set does not have:
word chips, label boxes, result rows, gate bars, the multi-column table that
gains columns, a document that shows its own contents. Draw new ones in the same
manner (outline in ink on paper fill, one filled band or accent, thin inner
detail).

```css
.xicon .tbl rect.o{fill:var(--paper);stroke:currentColor;stroke-width:2.5}
.xicon .tbl .h{fill:currentColor}
.xicon .tbl path{stroke:currentColor;stroke-width:1.5;fill:none}
.xicon .chip rect{fill:var(--mark)}
.xicon .chip text{fill:var(--paper);font:800 9.5px/1 var(--font);text-anchor:middle}
.xicon .chipo rect{fill:var(--paper);stroke:currentColor;stroke-width:2.5}
.xicon .chipo text{fill:currentColor;font:800 9.5px/1 var(--font);text-anchor:middle}
.xicon .mag circle{fill:rgba(244,239,228,.55);stroke:var(--mark);stroke-width:3.5}
.xicon .mag path{stroke:var(--mark);stroke-width:4;stroke-linecap:round}
.xicon .lbl{font:800 8.5px/1 var(--font);letter-spacing:.05em;text-anchor:middle;fill:currentColor}
.xicon .warn .t{fill:currentColor}.xicon .warn .i{stroke:var(--paper);stroke-width:2;stroke-linecap:round;fill:none}
.xicon .spark{fill:var(--mark)}
.xicon .bot rect{fill:currentColor}.xicon .bot circle{fill:var(--paper)}
.xicon .pg rect{fill:var(--paper);stroke:currentColor;stroke-width:2}.xicon .pg path{stroke:currentColor;stroke-width:1.5;fill:none}
.xicon .box{fill:var(--paper);stroke:currentColor;stroke-width:2.5}
.xicon .bub{fill:var(--paper);stroke:currentColor;stroke-width:2.5;stroke-linejoin:round}
.xicon .lock rect{fill:currentColor}.xicon .lock path{fill:none;stroke:currentColor;stroke-width:3;stroke-linecap:round}
.xicon .clock circle{fill:var(--paper);stroke:currentColor;stroke-width:2.5}.xicon .clock path{stroke:currentColor;stroke-width:2.5;stroke-linecap:round;fill:none}
.xicon .hl{fill:var(--hl)}
```

```html
<!-- data table, 26x20: header band + grid -->
<g class="tbl" style="transform:translate(82px,16px)"><rect class="o" width="26" height="20" rx="2"/><rect class="h" width="26" height="6.5" rx="2"/><path d="M0 13.5H26M13 6.5V20"/></g>
<!-- documentation page, 40x44: a mini table sketch + text lines -->
<g class="tbl" style="transform:translate(14px,64px)"><rect class="o" width="40" height="44" rx="3"/><rect class="o" x="6" y="7" width="28" height="14" rx="1.5" style="stroke-width:1.8"/><path d="M6 12H34M20 7V21"/><path d="M6 28H34M6 34H34M6 40H24" style="stroke-width:2"/></g>
<!-- labelled file (a skill, a policy, a test list): page with header band and a label -->
<g class="tbl"><rect class="o" width="32" height="40" rx="3"/><rect class="h" width="32" height="10" rx="3"/><text class="lbl" x="16" y="24">SKILL</text><path d="M6 31H26"/></g>
<!-- small reference document, 18x14 -->
<g class="pg"><rect width="18" height="14" rx="2"/><path d="M4 5H14M4 9H11"/></g>
<!-- word chip as the actor (a term, a query, a keyword); size the rect to the word -->
<g class="chip a-chip"><rect x="-20" y="-9" width="40" height="18" rx="9"/><text y="3.4">active</text></g>
<!-- outlined chip (a setting applied to something, e.g. a join's cardinality) -->
<g class="chipo"><rect x="-15" y="-9" width="30" height="18" rx="9"/><text y="3.4">1 : N</text></g>
<!-- search lens as the actor -->
<g class="mag a-mg"><circle r="10"/><path d="M7.5 7.5L15 15"/></g>
<!-- the agent, as a four-point sparkle -->
<path class="spark" d="M0 -10C1 -3 3 -1 10 0C3 1 1 3 0 10C-1 3 -3 1 -10 0C-3 -1 -1 -3 0 -10Z"/>
<!-- a second agent / reviewer, as a bot head -->
<g class="bot"><rect x="-10" y="-9" width="20" height="18" rx="4"/><circle cx="-4" cy="-1" r="2.2"/><circle cx="4" cy="-1" r="2.2"/></g>
<!-- warning sign (an error, a failure); set color on the group to recolour -->
<g class="warn" style="color:var(--mark)"><path class="t" d="M0 -9L9 7H-9Z"/><path class="i" d="M0 -3V1.5M0 4.4V4.6"/></g>
<!-- lock (permission, read-only, a control); sits on top of a gate bar -->
<g class="lock"><path d="M-5 -3V-9a5 5 0 0 1 10 0V-3"/><rect x="-9" y="-4" width="18" height="14" rx="3"/></g>
<!-- clock; rotate the inner group to run the hand, animate color on the outer group to turn it red -->
<g class="clock"><circle r="10"/><g class="a-hand"><path d="M0 0V-6.5"/></g></g>
<!-- outlined label box (a metric definition); a .hl rect behind the text, scaled on X, gives a highlighter sweep -->
<rect class="box" width="52" height="18" rx="3"/><text class="lbl" x="26" y="12.2">METRIC</text>
<!-- lineage graph (stroke 2, filled circles) -->
<path d="M5 0H25L41 -6M25 0L41 6"/><circle cx="5" r="4.5"/><circle cx="25" r="4.5"/><circle cx="41" cy="-6" r="4"/><circle cx="41" cy="6" r="4"/>
<!-- chat bubble (a user, a channel, an answer) -->
<path class="bub" d="M87 44H105a5 5 0 0 1 5 5V61a5 5 0 0 1-5 5H97l-7 7V66H87a5 5 0 0 1-5-5V49a5 5 0 0 1 5-5Z"/>
<!-- result rows / a count without a number: short thick lines; more lines = more rows -->
<path class="ln" style="stroke-width:3.5" d="M96 31H112M96 38H112"/>
```

Colour carries state: an object in `--mute-text` is stale, ignored or wrong; in
ink it is live; a new, changed or failing part is `--mark`; the one that is
found or chosen is filled or swept with the yellow highlighter. A row of grey
tables reads as "the old, inconsistent state"; the single ink or highlighted
object reads as "the governed one".

Placement and staging rules learned in testing:
- A label sits directly beside or inside the object it names, on that object's
  own row. Never float a label between two objects.
- The actor stops just short of the object it reaches (2-4 units of gap). Do not
  park it on top.
- Detours and loops are routed wide enough that the actor never passes over
  another object. Check every frame of the sheet for overlaps, not just the last.
- An object waiting behind another must be `opacity:0` until its cue; do not
  rely on the object in front to hide it while that one is still fading in.
- When the thing that travels is the thing that changes (a corrected line going
  back into a document), let it land and stay as part of the object.
- Things going wrong turn `--mark` and multiply or shake; the fix arrives as a
  labelled chip and the scene settles back to ink.
- Label change: stack two texts (or two chips) in the same place and crossfade
  them with opposite opacity keyframes ("RUN 1" to "RUN 2", "Australia" to "AUS").
- Leave at least 6 units between repeated objects in a grid.

Casting with Lucide icons (tested):

| Slide point | Objects and motion |
| --- | --- |
| Gather context, write SQL, verify | a red `bot` visits a grey `layout-dashboard` then a `book-open-text` (each turns ink), comes down and produces a `file-code-2`, which gets a `shield-check` |
| Can look, cannot edit | an `eye` passes a `lock` gate with a check; a `pencil-line` is bounced, greys out, gets an × |
| Start with one use case | a `target` passes over six grey `database` icons and settles on one, which gets a yellow plate |
| Trusted function | a `circle-question-mark` enters a `square-function`, a `table-2` comes out, a `badge-check` is stamped on it, TRUSTED is highlighted |
| Corrections become tests | a `message-square-warning` turns red; a red line travels from it into a `clipboard-list` and stays as a new row |
| A good answer becomes an example | a `thumbs-up` lands on a `file-code-2` beside a `user-round`; a copy flies into a `folder` labelled EXAMPLES, which is highlighted |
| Start from the question | a `receipt-text` INVOICE and a `file-text` PO get an ink `=`; a `scroll-text` CONTRACT drops in on a yellow plate, a red `≠` appears and the invoice turns red |
| Give AI the agreed definitions | three grey `file-spreadsheet` workbooks each send a tilted red CAC chip into a RULES box; one CAC chip comes out, highlighted and checked |
| Evidence and a named approver | the cheaper `banknote` is struck out and a REASON chip slides out beside it; the other gets a yellow plate, a line to a `user-round` APPROVER, and a red `stamp` |
| Measure the work left behind | a red `bot` sends six rows into an `inbox` under TO CHECK beside a `user-round`; the pile turns red, a `paperclip` lands and it shrinks to two |
| Test rule changes both ways | RULE V1 flips to RULE V2 and a dotted sweep reruns three cases (chips A, B, C); A's red × becomes a highlighted check, B and C keep their checks |

Examples of casting (same mechanisms, topical objects):

| Slide point | Generic (avoid) | Topical (do this) |
| --- | --- | --- |
| A term maps to several entities | ball at a three-way fork | the word "active" on a chip, hesitating between three table icons |
| Docs go stale as the schema drifts | a square sliding away from a circle | a table gaining new red columns while the doc page beside it still shows two, greys out and is circled |
| The right table exists but is not found | ball wandering a grid of dots | a search lens crossing six tables, passing the highlighted one, stopping on a grey one |
| Each layer stops a different failure | dots hitting bars | warning signs stopped one by one at barriers labelled DATA, CHECKS, SKILLS |
| Check the trusted source first | ball going to the longest bar | the agent sparkle going straight to a METRIC box that gets highlighted, while lineage, SQL and a doc fade |
| A skill routes the question | ball through a diamond to a box | a "?" passing through a file labelled SKILL to one reference doc that turns yellow |
| A reviewer challenges the answer | ball bounced at a gate | a SQL chip bounced grey by a bot-headed gate, revised, then passed with a check |
| Same question, different answers | two unequal bars | a GOLD chip asks two tables; each returns a different stack of rows; `≠` appears between them |
| Read-only access | ball stopped at a wall | a SELECT chip passes a locked gate; a DROP chip is bounced, greys out, gets an × |
| A step costs time and changes nothing | ball going round a loop | a SQL chip detours around a reviewer bot while a clock runs red, and lands unchanged beside an `=` |
| Answers carry provenance | check mark on a box | an answer bubble fills with text, then a SQL chip slides out from under it and stays attached |
| One definition of a metric | dots merging into a node | three tilted REV chips from three grey tables merge into one REVENUE box that is highlighted |
| Test, fix, rerun | progress bar | a test list headed RUN 1 with three red ×; the header flips to RUN 2 and two turn into checks |
| Undeclared join multiplies rows | lines fanning out | two joined tables return three rows that swell to seven in red; a "1 : N" chip lands on the join and they settle back to three |

The worked example below shows the motion mechanics with a plain ball. In a real
icon, replace the ball and the branch ends with the slide's objects as above.

**Worked example (tested)**

```html
<svg class="mo xicon amb" data-name="amb" viewBox="0 0 120 120" role="img"
     aria-label="A ball reaches a three-way fork, starts down each path in turn, returns, and a question mark appears.">
  <path class="ln draw a-trunk" pathLength="1" d="M20 60H56"/>
  <path class="ln draw branch a-b1" pathLength="1" d="M56 60L100 24"/>
  <path class="ln draw branch a-b2" pathLength="1" d="M56 60H104"/>
  <path class="ln draw branch a-b3" pathLength="1" d="M56 60L100 96"/>
  <circle class="ball a-ball" r="6"/>
  <text class="q a-q" x="40" y="42" text-anchor="middle">?</text>
</svg>
```

```css
.amb .branch{opacity:.4}
.amb .ball{fill:var(--mark);transform:translate(56px,60px)}
.amb .q{fill:var(--mark);font:800 30px/1 var(--font);transform-box:fill-box;transform-origin:50% 60%}
.amb .a-trunk{animation-name:amb-trunk}
.amb .a-b1{animation-name:amb-fan,amb-hi1}.amb .a-b2{animation-name:amb-fan,amb-hi2}.amb .a-b3{animation-name:amb-fan,amb-hi3}
.amb .a-ball{animation-name:amb-ball}.amb .a-q{animation-name:amb-q}
@keyframes amb-trunk{0%{stroke-dashoffset:1;opacity:0}1%{stroke-dashoffset:1;opacity:1;animation-timing-function:var(--io)}9%,95%{stroke-dashoffset:0;opacity:1}100%{stroke-dashoffset:0;opacity:0}}
@keyframes amb-fan{0%,8%{stroke-dashoffset:1;visibility:hidden}8.1%{stroke-dashoffset:1;visibility:visible;animation-timing-function:var(--io)}18%,100%{stroke-dashoffset:0;visibility:visible}}
@keyframes amb-ball{
  0%{transform:translate(20px,60px);opacity:0}5%{transform:translate(20px,60px);opacity:1}
  18%{transform:translate(20px,60px);animation-timing-function:var(--io)}
  30%,34%{transform:translate(56px,60px);animation-timing-function:var(--io)}
  40%{transform:translate(72px,47px);animation-timing-function:var(--io)}
  46%,48%{transform:translate(56px,60px);animation-timing-function:var(--io)}
  54%{transform:translate(74px,60px);animation-timing-function:var(--io)}
  60%,62%{transform:translate(56px,60px);animation-timing-function:var(--io)}
  68%{transform:translate(72px,73px);animation-timing-function:var(--io)}
  74%{transform:translate(56px,60px)}
  80%{transform:translate(54px,60px)}84%{transform:translate(58px,60px)}88%,95%{transform:translate(56px,60px);opacity:1}
  100%{transform:translate(56px,60px);opacity:0}}
@keyframes amb-hi1{0%,33%{opacity:.4}38%,42%{opacity:1}47%,95%{opacity:.4}100%{opacity:0}}
@keyframes amb-hi2{0%,47%{opacity:.4}52%,56%{opacity:1}61%,95%{opacity:.4}100%{opacity:0}}
@keyframes amb-hi3{0%,61%{opacity:.4}66%,70%{opacity:1}75%,95%{opacity:.4}100%{opacity:0}}
@keyframes amb-q{0%,75%{opacity:0;transform:scale(.6);animation-timing-function:var(--out)}81%,95%{opacity:1;transform:scale(1)}100%{opacity:0;transform:scale(1)}}
```

---

## B. Data animation (charts, tables, figures)

The job: the viewer ends up looking at **the one number or comparison the slide
is about**, and understands why it matters.

**Process**

1. **Find the point.** From the headline and data, name the key number or
   comparison in one line ("Reconcile is 42 of 109 hours"). If the slide has no
   headline claim, write one from the data and use it as the takeaway headline.
2. **Pick the focus move** from the table below.
3. **Run the four beats** (play once, 3-4s total, then rest on the final frame):

| Beat | Time | What happens |
| --- | --- | --- |
| 1. Frame | 0-0.3s | axis/baseline draws, category labels fade in |
| 2. Build | 0.25-1.4s | all data arrives in neutral ink, staggered 80ms, in reading order; values fade in after |
| 3. Focus | `--focus` (about 2s) | everything that is not the point recedes to grey; the key mark stays ink |
| 4. Annotate | focus + 0.4s onward | marker circle/bracket/arrow draws to the key mark, then a highlighter sweep and the takeaway number or phrase |

Beat 2 shows the whole picture honestly before beat 3 edits attention. Never skip
straight to the highlighted state.

| Data shape | Build | Focus move | Annotation |
| --- | --- | --- | --- |
| Bar / column comparison | bars grow from baseline (`d-grow`) | other bars and their values recede | circle the key value, arrow, highlighted takeaway |
| Trend line | line draws left to right (`d-draw`), context series in grey | the segment that matters is drawn last, thicker, in ink; dot pops at the key point | bracket the change, highlight the level |
| Before vs. after / two values | both grow | the smaller recedes | bracket between them with the difference |
| Part of whole | segments grow in sequence (`d-growx` on a stacked bar; avoid pies) | other segments recede | highlight the share |
| Table | rows fade in top to bottom | non-key rows dim (`d-dim`) | highlighter sweep on the key cell |
| Single KPI / big number | number pops (`d-pop`) | n/a | highlighter sweep, one line of context fades in under it |
| Ranking | bars grow in rank order (`d-growx`) | all but the subject recede | marker underline on the subject's label |
| Distribution / scatter | points pop in clusters | points outside the story recede | circle the cluster or outlier |

**Build spec**

- Charts are hand-built inline SVG, `viewBox="0 0 640 340"`. No chart library.
  No gridlines, no legend (label directly), no y-axis unless the scale is the
  point. Baseline at y=290; value labels sit above marks; category labels below.
- Classes: key mark `key`; other marks `rest d-recede`; other value labels
  `rest-t d-recede`; marker paths `pen d-draw`; highlight rectangles `hl d-swipe`
  placed before the text they sit behind.
- Timing by inline `style="--at:1.2s"` (start time). Set `--focus` once on the
  `.mo` container; every `d-recede` / `d-dim` uses it.
- An element can run one `d-` animation. To grow *and* recede, nest:
  `<g class="d-grow" style="--at:.33s"><rect class="rest d-recede" .../></g>`.
- Tables are real `<table class="mo">` (add `display:table`). Rows:
  `<tr class="rest d-fade d-dim" style="--at:.2s">`; key row `keyrow d-fade`, bold.
  Key cell: `<span class="cellhl" style="--at:2s">410</span>` with
  `.cellhl{position:relative;z-index:0;display:inline-block;padding:2px 8px;margin:-2px -8px}`
  `.cellhl::before{content:"";position:absolute;inset:0;background:var(--hl);z-index:-1;transform-origin:0 50%;animation:d-swipe .35s var(--io) var(--at,0s) both}`
  and `tr.rest{color:var(--mute-text)}`.
- Numbers do not count up (it adds nothing and does not export cleanly). The key
  number arrives with the highlighter sweep.
- Marker circle around a label at (cx,cy), about 27px radius, drawn as one loose
  stroke that overshoots: e.g. around (116,62):
  `M90 60c1-17 14-25 28-24 15 1 27 10 26 26-1 15-13 23-29 22-15-1-27-9-24-27`.
- Keep annotation text clear of marks and pen strokes; check in the frame sheet.

**Worked example: bar chart (tested)**

```html
<svg class="mo" data-name="bars" style="--focus:2s" viewBox="0 0 640 340" role="img"
     aria-label="Hours per close step. Reconcile is largest at 42 of 109 hours.">
  <path class="ln d-draw" pathLength="1" d="M52 290H612"/>
  <g class="d-grow" style="--at:.25s"><rect class="key" x="80" y="80" width="72" height="210"/></g>
  <g class="d-grow" style="--at:.33s"><rect class="rest d-recede" x="188" y="150" width="72" height="140"/></g>
  <!-- ...more bars, +80ms each... -->
  <text class="val d-fade" style="--at:.95s" x="116" y="68">42</text>
  <g class="d-fade" style="--at:1.03s"><text class="val rest-t d-recede" x="224" y="138">28</text></g>
  <g class="d-fade" style="--at:.1s"><text class="cat" x="116" y="314">Reconcile</text><text class="cat" x="224" y="314">Accrue</text></g>
  <path class="pen d-draw" pathLength="1" style="--at:2.4s" d="M90 60c1-17 14-25 28-24 15 1 27 10 26 26-1 15-13 23-29 22-15-1-27-9-24-27"/>
  <path class="pen d-draw" pathLength="1" style="--at:2.85s;animation-duration:.4s" d="M300 66C255 40 200 42 156 56M156 56l15-9M156 56l12 12"/>
  <rect class="hl d-swipe" style="--at:3.2s" x="306" y="50" width="262" height="34"/>
  <text class="note d-fade" style="--at:3.3s" x="314" y="74">42 of 109 hours: 39%</text>
</svg>
```

with `.mo .val{font-size:20px;font-weight:800;text-anchor:middle}`
`.mo .cat{font-size:14px;font-weight:600;text-anchor:middle}`
`.mo .note{font-size:19px;font-weight:800}`.

**Recipes for each data shape (all six tested with real figures)**

- **Single KPI.** The number is the chart: `<text class="big d-pop">` at 150px,
  weight 800, centred; a highlighter rect behind it sweeps in at 0.9s (make the
  rect 20px wider than the number on each side); one bold line of context fades
  in below at 1.5s, an optional grey second line at 2.1s, and a loose marker
  underline under the phrase that matters. Keep the source's hedge ("~95%").
- **Before vs. after.** Two bars. The "before" bar and its value recede to grey
  at focus; the "after" bar stays ink. A marker arrow curves from the top of the
  small bar to the top of the tall one; the takeaway ("From 21% to over 95%")
  sits in the band above the plot. Keep qualifiers on the labels (`≤21%`, `>95%`).
- **Trade-off (one gain, several costs).** Horizontal bars from a vertical axis
  (`d-growx`), labels right-aligned to the left of the axis, values at the bar
  ends. All bars build in ink; at focus the cost bars turn red (`class="cost
  d-tomark"`, nested inside the `d-growx` group) and the gain stays ink. The
  takeaway pairs the gain with the worst cost; the arrow points at that cost.
- **Table with a key column.** Rows fade in; at focus every cell outside the key
  column greys (`td class="rest d-dim"`), the key column's header is ink, and
  each key cell gets a highlighter sweep (`cellhl`), staggered 0.3s. Use this
  when one option wins across several rows.
- **Part of whole, tiny share.** One long bar for the whole (`d-growx`, 1s),
  labelled with the total. At focus it greys and the share appears in red at its
  true width, even if that is under 2px; a marker circle and arrow make it
  findable, and the takeaway gives the count and the computed share ("Fewer than
  200 documented: under 0.25%"). Never widen the sliver to make it visible.
- **Trend with two points.** Zero-based scale. A grey dotted reference line at
  the starting level shows where it should have stayed; the ink line draws from
  start to end; the start dot is ink, the end dot red; a marker bracket at the
  right spans the gap with the computed change highlighted ("−30 pts").

**More data rules from practice**

- Put the highlighted takeaway in the empty band above the plot (y 4-38), with
  the marker arrow curving down to the key mark. Never place it over a value
  label, even a greyed one.
- Paired comparison (with vs. without, before vs. after): the reference bar
  stays ink, the bar that is the point is filled `--mark`, and any second pair
  recedes to grey. Label each bar directly underneath ("with docs" / "no docs")
  in small grey text and the pair in bold below that.
- A deck can mix both kinds: explainer icons for the idea slides and one data
  animation on the slide that carries the evidence.
- Export icons with `--width 480` and data figures with `--width 960`. Rendering
  a whole page of icons at 960 is slow; run the two sizes as separate passes.

**Data honesty (non-negotiable)**

- Every number shown comes from the source. Never invent, round misleadingly, or
  fill gaps. Derived figures (a share, a multiple) are computed from the source
  and shown with their inputs.
- Bars start at zero and are drawn to scale. Lines use one consistent scale.
- Receding is emphasis, not deletion: greyed data stays readable.
- The annotation states what the data shows, not more than it shows.

---

## Placement

- **Slide drafts (HTML, bound for PowerPoint)**: the motion graphic is the
  slide's main visual under a takeaway headline. Icons 280-420px; data figures
  fill the content area. Keep the headline as slide text, outside the `.mo`.
- **doc-to-infographic pages**: see "Pairing with doc-to-infographic" below.

## Pairing with doc-to-infographic (tested)

When both skills run on one document, doc-to-infographic owns the page (spine,
relationship inventory, section diagrams, captions) and this skill adds one
explainer icon per section that states a concept, plus a data animation where a
section's point is a number. Build the page with a small Python generator that
reads the infographic template, so icons and diagrams come from the same
`lucide.py` helper.

1. **Rebrand the template to the house palette** by editing its `:root` (the
   template invites this): `--ink:#191919; --muted:#5f594c; --faint:#8d8676;
   --line:#d9d2c2; --bg:#f4efe4; --panel:#ebe5d6; --accent:#191919;
   --accent-soft:#ebe5d6`. Also replace the two hardcoded colours: the sticky
   nav background (`rgba(244,239,228,.94)`) and the summary border
   (`var(--line)`). Then add `--paper:var(--bg)` with the motion tokens so icon
   backgrounds match the page exactly.
2. **Three meaningful colours across page and icons, with a legend**: ink = what
   the system or workflow does; yellow highlighter = what a person decides or
   the thing that is chosen; red = the gap or failure. Use the same roles in the
   diagram chips (`.ichip.ai{background:var(--ink);color:var(--bg)}`,
   `.ichip.hu{background:var(--hl);color:var(--ink)}`) as in the icons.
3. **Section header layout**: a two-column grid, icon on the left at 200px, then
   kicker + takeaway heading + one-line lead on the right
   (`grid-template-columns:200px 1fr; gap:30px; align-items:center`). The
   section's relational diagram goes full width underneath, then the caption
   and the expandable case.
4. **Icons in diagram chips come from Lucide too.** Drop the template's sprite
   and inline the icon: `<svg class="ic" viewBox="0 0 24 24">` + the Lucide
   paths + `</svg>` inside `.ichip`. One icon set on the whole page.
5. **Class clash**: the template has its own `.draw` (scroll-triggered, with a
   transition). Inside icons add `.xicon .draw{transition:none}` after the
   template's rule so icon line-draws follow the keyframes only.
6. **Icons wait until scrolled into view**: wrap each icon in the template's
   `.reveal` and add
   `.reveal:not(.in) .xicon [class*="a-"]{animation-play-state:paused}`.
7. **Soften the template's dimming of rejected branches** so they stay readable
   on paper: `[data-branch].decided .br-off{opacity:.62;filter:none}`.
8. **Keep diagram rows on one line**: node labels of four words or fewer, verbs
   of one or two words, at most five nodes per row; use a tighter edge width
   for rows of five (`.redge{flex:0 1 54px;min-width:44px}`). Check the full-page
   screenshot for any row that wraps with a dangling arrow.
9. **Do not duplicate the diagram in the icon.** The icon acts out the lesson's
   mechanism with a handful of objects; the diagram underneath carries the full
   chain of who does what. If they would show the same thing, change the icon's
   motif.
10. **A source with no numbers gets no data animation and no stat cards.** Say
    so in the summary band and the footer instead of inventing a metric.
11. **Close with the cross-link section** the infographic skill asks for (for
    example a lesson-by-owner matrix), using the same three colours.
12. **Verify both layers**: the icon frame sheets, and a full-page screenshot
    taken after scrolling to the bottom (so every reveal has fired), checking
    that no `.reveal` is still hidden and there are no script errors.

## Verify and export (required)

Save as `mo_frames.py` (needs Playwright + Pillow) and run
`python3 mo_frames.py page.html outdir --gif`. It seeks every animation to exact
times, writes an 8-frame sheet per graphic, and with `--gif` a GIF plus a still.
Looping icons export as looping GIFs; play-once data animations export as GIFs
that play once and hold the final frame (`--hold` seconds, default 4).

```python
import sys, os, io
from playwright.sync_api import sync_playwright
from PIL import Image
page_path, outdir = sys.argv[1], sys.argv[2]
def opt(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag)+1]) if flag in sys.argv else default
want_gif = '--gif' in sys.argv
fps, width, hold = opt('--fps', 12), opt('--width', 960), opt('--hold', 4.0)
loops, rest = opt('--loops', 3), opt('--rest', 2.5)   # icons: play N times (0 = forever), resting on the finished frame before each play
os.makedirs(outdir, exist_ok=True)
SEL = '.mo'
INFO = """(i)=>{const el=document.querySelectorAll('%s')[i];const an=el.getAnimations({subtree:true});
  const t=an.map(a=>a.effect.getComputedTiming());const loops=t.some(x=>x.iterations===Infinity);
  const total=loops?Math.max(0,...t.map(x=>x.duration)):Math.max(0,...t.map(x=>x.endTime));
  return {loops,total,name:el.dataset.name||('mo'+i)}}""" % SEL
SEEK = "([i,t])=>{document.querySelectorAll('%s')[i].getAnimations({subtree:true}).forEach(a=>{a.pause();a.currentTime=t;});}" % SEL
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width':1200,'height':900}, device_scale_factor=2)
    pg.goto('file://'+os.path.abspath(page_path)); pg.wait_for_timeout(300)
    els = pg.locator(SEL)
    for i in range(els.count()):
        el = els.nth(i); info = pg.evaluate(INFO, i); name, total, loops = info['name'], info['total'], info['loops']
        def shot(t):
            pg.evaluate(SEEK, [i, t]); return Image.open(io.BytesIO(el.screenshot())).convert('RGB')
        fr = [shot(total*k/8+1 if loops else total*k/7) for k in range(8)]
        w, h = fr[0].size; sheet = Image.new('RGB', (w*4, h*2), 'white')
        for k, im in enumerate(fr): sheet.paste(im, ((k%4)*w, (k//4)*h))
        sheet.thumbnail((2000, 1400)); sheet.save(f'{outdir}/{name}_sheet.png')
        if want_gif:
            n = max(2, int(round(total/1000*fps))); hgt = round(width*h/w)
            if loops:
                # start the loop at the held payoff (90%) so frame 1 is the finished icon
                frames = [shot((0.9*total + total*k/n) % total).resize((width,hgt), Image.LANCZOS) for k in range(n)]
                dur = [int(1000/fps)]*n; dur[0] = int(rest*1000)
                kw = dict(save_all=True, append_images=frames[1:], duration=dur, optimize=False)
                if loops == 0: kw['loop'] = 0
                elif loops > 1: kw['loop'] = loops - 1
            else:
                # play-once: open on the finished frame for 0.7s, then build, then hold
                final = shot(total).resize((width,hgt), Image.LANCZOS)
                frames = [final] + [shot(total*k/n).resize((width,hgt), Image.LANCZOS) for k in range(n+1)]
                dur = [700] + [int(1000/fps)]*(n+1); dur[-1] = int(hold*1000)
                kw = dict(save_all=True, append_images=frames[1:], duration=dur, optimize=False)
            frames[0].save(f'{outdir}/{name}.gif', **kw)
            pg.evaluate("(i)=>document.querySelectorAll('%s')[i].classList.add('static')" % SEL, i)
            Image.open(io.BytesIO(el.screenshot())).convert('RGB').resize((width,hgt), Image.LANCZOS).save(f'{outdir}/{name}_static.png')
            pg.evaluate("(i)=>document.querySelectorAll('%s')[i].classList.remove('static')" % SEL, i)
    b.close()
```

**Read every `*_sheet.png` before delivering** and check: beats appear in order;
nothing overlaps or leaves the frame; no stray dots before lines draw; the final
frame is legible alone; for icons the cover and freeze tests pass; for data the
eye lands on the key number in the last frames. Fix and re-render until true.

**A GIF's first frame must be the finished picture.** PowerPoint's editing view,
slide thumbnails, file previews and PDF exports show only frame 1 of a GIF. An
animation that starts from an empty canvas therefore looks like a blank box on
the slide (and on a paper-coloured slide, like nothing at all). The export
script handles this: looping icons start at the held payoff, and play-once data
animations open on the finished chart for 0.7s before building. After building a
deck, check it by converting the .pptx to PDF (`soffice --headless --convert-to
pdf`) and looking at the pages: every slide must show its graphic.

**Bundled scripts.** When this skill's folder has a `scripts/` directory, use
those files instead of retyping the code above: `mo_frames.py` (frame sheets,
GIFs, stills), `lucide.py` (icon search and inline output), `build_pptx.py`
(one graphic per slide) and `pageshot.py` (full-page screenshot after all
reveals have fired). They are the maintained versions. `assets/examples/` holds
tested pages, GIFs and decks for both categories and the infographic pairing.

**GIF size and background.** Quantize every frame of a GIF to one shared
48-colour palette (flat graphics need few colours; files drop to about 150 KB),
then force every palette entry within 3 of the page background to the exact
background colour. Pillow shifts palette values by a step when it writes a GIF,
and a background that is one step off shows as a faint box on the slide. The
bundled `mo_frames.py` does both and reads the background from the page's CSS.

**When motion starts.** The deliverable for PowerPoint is always a GIF (never
video). A GIF cannot wait for its slide: the viewer decides when it plays. In
PowerPoint's slide show a GIF plays when its slide is shown; a browser preview
or thumbnail view that lays out every slide runs them all at once. So that a
deck is calm wherever it is opened, icon GIFs do not loop forever by default:
each plays three times, resting 2.5s on the finished icon before each play, then
stops on the finished frame (`--loops 3 --rest 2.5`; `--loops 0` loops forever,
`--loops 1` plays once). Data animations already play once. In HTML, where it
can be controlled, motion always waits for focus: infographic icons pause until
scrolled into view, and in an HTML slide draft add
`.slide:not(.current) .mo [class*="a-"],.slide:not(.current) .mo [class*="d-"]{animation-play-state:paused}`
and restart a slide's animations when it becomes current (remove and re-add the
`.mo` element's `static` class, or re-insert the node).

**PowerPoint**: CSS animation does not convert to .pptx. Insert each `<name>.gif`
on its slide as a picture (python-pptx: `slide.shapes.add_picture('name.gif',
left, top, width, height)` keeps the frames). Keep `<name>_static.png` for PDF or
print versions. The GIF carries the `.mo` background colour, so set `--paper` to
the slide background before capture.

## Always

- Every graphic has `role="img"` (or a table caption/aria-label) describing what
  it shows and, for icons, what happens.
- Reduced motion and print show the final frame.
- Animate only `transform`, `opacity`, `stroke-dashoffset`, `visibility`, colour.

Easing curves adapted from richtabor/agent-skills `motion-design`
(https://github.com/richtabor/agent-skills).