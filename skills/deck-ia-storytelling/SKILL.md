---
name: deck-ia-storytelling
description: >
  Assess and improve PowerPoint/Keynote/Google Slides decks using a scored rubric
  that combines website information-architecture principles with Cole Nussbaumer
  Knaflic's Storytelling with Data (SWD) best practices. Use this skill WHENEVER a
  user asks to review, critique, grade, score, audit, "make better," tighten, or
  improve a slide deck, presentation, pitch, or any .pptx/.key/Google Slides file —
  even if they don't say "rubric." Also use when building a deck from scratch and the
  user wants it to follow good design/storytelling principles, when checking a deck
  for clarity, clutter, color use, narrative flow, or executive-readiness, or when
  another agent needs a structured, repeatable scoring framework to evaluate and then
  edit a deck. Apply it for finance/business decks specifically (board decks, MD/CFO
  updates, analytics readouts) where an explicit takeaway and a clear "so what" matter.
license: Proprietary.
---

# Deck IA + Storytelling Assessment & Improvement

## What this skill is

A **two-pass operating procedure** for an AI agent to (1) score a deck against a
rubric, then (2) implement fixes in a defined priority order, then (3) re-score.

The rubric fuses two bodies of knowledge:

- **Information architecture (IA) from web design** — wayfinding, hierarchy,
  chunking, consistency, grid/alignment, proximity, signal-to-noise, scannability,
  flow, accessibility.
- **Storytelling with Data (SWD)** — Knaflic's lessons on context, choosing the
  right visual, eliminating clutter (Gestalt), focusing attention with preattentive
  attributes, strategic color, and narrative structure, plus tactics distilled from
  the SWD chart-makeover library.

Use it as a checklist + scoring sheet. Do not skip the storytelling dimensions:
a beautifully formatted deck that doesn't make its point still fails.

## How to run an assessment

1. **Read the deck.** If it's a `.pptx`, follow `/mnt/skills/public/pptx/SKILL.md`
   to extract slide text, titles, speaker notes, and to rasterize slides for visual
   inspection. Text extraction alone misses layout, color, and chart problems —
   rasterize pages where visual design matters.
2. **Establish context first** (Dimension 0). You cannot score "is the point clear"
   without knowing the audience and goal. If the user hasn't told you, ask the four
   context questions in `references/storytelling-with-data.md` before scoring.
3. **Score every slide** on Dimensions 1–13 using the 0–3 scale below. Score
   Dimension 14 (narrative flow) at the deck level.
4. **Flag any dimension scored ≤1** as a required fix.
5. **Apply fixes in the priority order** in the "Improvement workflow" section.
6. **Re-score** flagged items to confirm each reaches ≥2.
7. **Report**: per-slide scores, deck total, the prioritized fix list, and the
   before/after on anything you changed.

## Scoring scale (per dimension)

| Score | Meaning |
|---|---|
| 0 | Absent or actively violated |
| 1 | Major issues; obscures the message |
| 2 | Minor issues; works but improvable |
| 3 | Strong; exemplary |

---

## The rubric

### Dimension 0 — Context & Big Idea *(gate; score deck-level)*
*SWD Ch.1. This gates everything else — establish it before scoring the rest.*
- **Check:** Is there one identifiable audience (not "all stakeholders")? Is there a
  single-sentence **Big Idea** that (a) states a point of view, (b) conveys what's at
  stake, (c) is a complete sentence? Can the deck's purpose survive the **3-minute
  story** test? Is the communication mode (live vs. leave-behind) reflected in slide
  density?
- **Fix:** Force a Big Idea before touching slides. Narrow to one decision-maker.
  Right-size detail to the mode: sparse for live presentation, denser for standalone.

### Dimension 1 — Information scent / wayfinding
*Web IA + SWD "transforming slide titles."*
- **Check:** Does each slide have an **assertion-based title** (the takeaway as a full
  sentence — "Fee income grew 12% on treasury services" — not a label like "Revenue")?
  Section/progress markers for decks >10 slides?
- **Fix:** Rewrite label titles into takeaway sentences. Add section dividers/tracker.

### Dimension 2 — Hierarchy & visual weight
*Web IA + SWD preattentive "size" + "position on page."*
- **Check:** Exactly one focal point per slide? Does size/weight map to actual
  importance ("relative size denotes relative importance")? Is the key element in the
  primary zone (top-left / center along the natural Z-path)? Run the **"look away"
  test**: glance away, look back — do your eyes land where you intend?
- **Fix:** Establish a 3-tier type scale (headline / body / caption). Enlarge the one
  thing that matters; demote the rest. Reposition the key number/chart to the Z entry.

### Dimension 3 — Chunking & progressive disclosure
*Web IA (Miller 7±2) + SWD on cognitive load.*
- **Check:** ≤5–6 discrete elements per slide? One idea per slide? Dense content split
  or moved to appendix/builds? (SWD makeover: "resist the urge to pack everything into
  one graph" — multiple focused graphs beat one overloaded one.)
- **Fix:** Split overloaded slides. Move detail to appendix. Use builds to reveal one
  point at a time in live settings.

### Dimension 4 — Clutter & signal-to-noise (data-ink)
*SWD Ch.3 + Tufte data-ink ratio.*
- **Check:** Chartjunk present — heavy gridlines, chart borders, background fills, drop
  shadows, redundant legends, 3D, decorative clipart? Every element earning its
  cognitive cost?
- **Fix:** Strip borders/gridlines/background shading (Gestalt closure says the chart
  still reads). Flatten any 3D. Remove decoration. Keep only ink that carries meaning.

### Dimension 5 — Gestalt grouping & proximity
*SWD Ch.3 — proximity, similarity, enclosure, closure, continuity, connection.*
- **Check:** Are labels adjacent to what they describe (legends near/on the data, or
  direct-labeled)? Does spacing communicate grouping (tight within a group, loose
  between groups)? Is enclosure/shading used to separate e.g. actual vs. forecast?
- **Fix:** Direct-label series instead of separate legends. Tighten intra-group and
  widen inter-group spacing. Use light shading to delineate regions.

### Dimension 6 — Alignment & grid
*Web IA + SWD "lack of visual order."*
- **Check:** Elements aligned to a consistent grid with clean horizontal/vertical
  edges? Margins kept clear? **Left-justified** text (center-alignment creates ragged
  edges and reads sloppy)? **No diagonal** text or connector lines (45° text is ~52%
  slower to read; 90° is ~205% slower)?
- **Fix:** Turn on gridlines/guides; snap to a grid. Left-justify. Upper-left-most
  justify chart titles/axis labels/legends so readers hit "how to read it" before the
  data. Remove diagonals.

### Dimension 7 — White space
*SWD Ch.3.*
- **Check:** Is white space preserved and intentional, or is every gap filled? Are
  visuals stretched to fill space rather than sized to content? Never add data just to
  fill space.
- **Fix:** Restore margins. Size visuals to content. Use white space for emphasis — if
  one thing is critical, consider making it the only thing on the slide.

### Dimension 8 — Choosing an effective visual
*SWD Ch.2 + makeover library.*
- **Check:** Is the chart type the easiest-to-read option for this data? Time series →
  line, not bars. One or two numbers → big simple text/number, not a chart or table.
  Lookup of precise values → table; an overarching message → graph. Long category
  names → horizontal bars. **No pie/donut charts; no 3D; no needless secondary y-axis.**
- **Fix:** Swap to the most-readable familiar chart. Convert standout single metrics to
  big text. Replace pies with bars. Drop the second y-axis or split into two charts.

### Dimension 9 — Strategic use of color *(theming + accent)*
*SWD Ch.4 — see the dedicated rubric in `references/color-and-theming.md`.*
- **Check (accent):** Is most of the deck in a neutral (grey) base with **one** accent
  color reserved for "look here"? Or is it rainbow/over-colored so nothing stands out
  ("a hawk in a sky of pigeons")?
- **Check (consistency / theming):** Does a color mean the **same thing** on every
  slide (e.g., a category or "our business" keeps its color throughout)? Color changes
  only to signal a real change in topic/tone? Single coherent palette, type, and chart
  styling deck-wide?
- **Check (accessibility):** Colorblind-safe (avoid red/green as the only distinction;
  ~8% of men affected)? Meaning never carried by color alone? Sufficient contrast?
- **Check (tone & brand):** Does the palette's emotional tone fit the message? If brand
  colors are required, are only **one or two** used as accents with the rest muted —
  and is the accent actually high-contrast enough to grab attention?
- **Fix:** Recolor to grey base + single accent. Lock a category→color map and apply it
  everywhere. Pair color with text/saturation/symbols for colorblind safety. If a brand
  color is too washed-out to be the accent, use bold black or a complementary
  attention color that doesn't clash with the logo.

### Dimension 10 — Words + color pairing (the "so what")
*SWD makeovers "is your point clear" + "power of pairing color & words."*
- **Check:** Is the takeaway written in words on the slide (not left for the audience
  to infer)? Is a recommended **action** stated? Do emphasized words share the **same
  color** as the data they reference, creating a visual link between text and chart?
- **Fix:** Add a takeaway sentence and an explicit action/next-step. Color-match the
  key words to the highlighted data points.

### Dimension 11 — Scannability
*Web IA + SWD executive-summary guidance.*
- **Check:** Core message graspable in <5 seconds? Key figures emphasized? Text in
  fragments, not paragraphs? For dense leave-behinds, are there section headers and
  grouped related content?
- **Fix:** Cut sentences to phrases, bold/keep key figures, front-load conclusions,
  break dense slides into labeled sections.

### Dimension 12 — Annotation & labeling integrity
*SWD Ch.3/4.*
- **Check:** Are units/`$`/`%` retained with numbers (don't make the reader remember
  the title said dollars)? Axis titles present and horizontal? Data labels used
  *sparingly* as "look here" signals rather than on every point?
- **Fix:** Re-attach units to numbers. Add horizontal axis titles. Label only the
  points that carry the message.

### Dimension 13 — Accessibility & legibility (room test)
*Web IA (WCAG) + SWD.*
- **Check:** Body ~18–24pt+, titles ~28pt+; readable from the back of a room / at
  thumbnail size? WCAG-AA contrast? No meaning by color alone (overlaps Dim 9)?
- **Fix:** Increase font sizes and contrast; add redundancy to any color coding; test
  at projection scale.

### Dimension 14 — Narrative flow *(score deck-level)*
*SWD Ch.7.*
- **Check:** Three-act arc — **setup → tension/conflict ("what is" vs. "what could
  be") → resolution/call-to-action**? Do the slide titles, read in sequence, tell the
  story on their own (horizontal logic)? Is there an executive-summary slide up front
  and a recap+CTA at the end (repetition)? Is the order deliberate (chronological to
  build credibility, or lead-with-the-answer for busy/ trusting audiences)? Does it end
  with an explicit ask?
- **Fix:** Reorder into the arc. Add a tension slide if the deck is "all rosy." Make the
  title string read as a narrative. Add opening summary + closing recap/CTA. Tie the
  ending back to the opening problem.

---

## Scoring bands

15 dimensions (0–14) × 3 = **45 max.**

| Band | Total (0–45) | Action |
|---|---|---|
| Strong | 38–45 | Polish only |
| Adequate | 28–37 | Targeted fixes |
| Weak | 16–27 | Substantial rework |
| Critical | <16 | Set the deck aside; rebuild from a Big Idea + storyboard |

If **Dimension 0 or 14 scores ≤1**, treat the deck as needing rework regardless of the
numeric total — the formatting can be perfect but the deck still won't land.

---

## Improvement workflow (fix priority order)

Apply fixes top-down; earlier fixes change what later ones need to do:

1. **Context & Big Idea (0)** — lock the audience + one-sentence Big Idea first.
2. **Narrative flow (14)** — sequence into setup → tension → resolution/CTA.
3. **Information scent / titles (1)** — assertion titles that read as a story.
4. **Words + the "so what" (10)** — write takeaways and the action onto slides.
5. **Hierarchy (2)** — one focal point; size/position for importance.
6. **Choose effective visuals (8)** — right chart; kill pies/3D/second axes.
7. **Chunking (3)** — one idea per slide; split overloaded slides.
8. **Clutter / signal-to-noise (4)** + **Gestalt (5)** — strip chartjunk; group.
9. **Color & theming (9)** — grey base + consistent single accent; colorblind-safe.
10. **Alignment/grid (6)** + **white space (7)** — clean lines; intentional space.
11. **Annotation integrity (12)** + **scannability (11)**.
12. **Accessibility/legibility (13)** — sizes, contrast, room test.

After fixes, **re-run the look-away test** on each changed slide and re-score every
flagged dimension to confirm ≥2.

---

## Reference files

Load these for depth when scoring or fixing the relevant area:

- `references/storytelling-with-data.md` — the SWD book distilled: context (who/what/
  how, Big Idea, 3-minute story, storyboarding), choosing visuals, clutter & the six
  Gestalt principles, preattentive attributes, and narrative structure.
- `references/color-and-theming.md` — the full color/theming sub-rubric: sparingly,
  consistently, colorblind, tone, brand, plus a concrete theming checklist.
- `references/makeover-principles.md` — tactics distilled from the SWD chart-makeover
  library (13 makeovers), each as a one-line check + fix.

## Output format for the agent

When reporting, produce:
1. A short **context recap** (audience + Big Idea you're scoring against).
2. A **per-slide table**: slide #, the worst 2–3 dimensions, score, one-line fix.
3. The **deck total + band**.
4. A **prioritized fix list** (in the order above).
5. If you edited the deck, a brief **before/after** note per change.

Keep commentary tight and executive — lead with the verdict, then the evidence.
