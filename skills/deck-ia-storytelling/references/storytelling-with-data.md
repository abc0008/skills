# Storytelling with Data — distilled reference

Source: Cole Nussbaumer Knaflic, *Storytelling with Data* (Wiley, 2015). Insights
below are paraphrased for use as an assessment reference.

## The core shift: explanatory, not exploratory
Analysis means opening ~100 oysters to find 2 pearls. When you *communicate*, show
the pearls — not all 100 oysters. Don't dump exploratory analysis on an audience to
prove how much work you did. Decide the specific thing you want to explain.

## Context first — who / what / how (Ch.1)
Answer these *before* building any slide:
- **Who** is the audience? Be specific; name the decision-maker. Avoid "internal and
  external stakeholders." Also consider your relationship to them and whether you need
  to build credibility.
- **What** do you need them to know or **do**? Always have an ask. If you can't state
  it, reconsider whether to communicate at all. Use action verbs (accept, approve,
  begin, change, invest, recommend, start…).
- **How** will data support the point? Data is evidence for the story, chosen after
  who/what.
- **Mechanism** sits on a continuum: **live presentation** (you control pace; keep
  slides sparse) ↔ **document/email** (audience controls; needs more detail). A single
  artifact forced to do both is a "slideument" and serves neither well.
- **Tone:** celebratory? urgent? clinical? It drives later design choices.

### Consulting-for-context questions (ask the requester)
- What background is essential? Who is the decision-maker and what do we know of them?
- What biases might make them resistant/supportive? What data strengthens the case?
- Where are the risks that weaken the case? What does success look like?
- **If you had one sentence to tell them what they need to know, what would it be?**

## The Big Idea & 3-minute story (Ch.1)
- **3-minute story:** if you had 3 minutes and no slides, what would you say? Frees you
  from dependence on the deck and lets you compress to any time slot.
- **Big Idea (Duarte):** one sentence that (1) states your unique point of view,
  (2) conveys what's at stake, (3) is a complete sentence.
- **Storyboard** *before* opening presentation software (sticky notes / whiteboard).
  Starting in PowerPoint creates premature attachment to slides you should cut.

## Choosing an effective visual (Ch.2)
A dozen visuals cover most business needs:
- **Simple text / a big number** — when you have just one or two numbers, don't bury
  them in a table or chart.
- **Table** — when the audience needs to look up specific values; reads in "audience
  mode." Use light/no borders so data is the signal (Gestalt).
- **Heatmap** — table values with saturation of a single color encoding magnitude.
- **Line graph** — continuous/time-series data.
- **Slopegraph** — two time points, emphasis on rate/direction of change.
- **Vertical bar / stacked bar / waterfall** — categorical comparisons; waterfall for
  start→changes→end.
- **Horizontal bar / stacked horizontal bar** — extremely easy to read; ideal for long
  category labels (text runs left-to-right as people read).
- **Square area** — for very different magnitudes.
- **Avoid:** pie and donut charts; **never use 3D**; avoid secondary y-axes (they're
  easily misread — label directly or use two charts instead).

## Clutter is your enemy (Ch.3)
Every element adds **cognitive load**. Maximize the **data-ink / signal-to-noise
ratio** (Tufte/Duarte): more of the ink should be data. Remove anything that doesn't
add informative value. Clutter makes a visual *feel* harder than it is, and the
audience disengages.

### The six Gestalt principles (use to find and cut clutter)
1. **Proximity** — objects close together read as a group; spacing alone can make eyes
   read down columns or across rows.
2. **Similarity** — same color/shape/size reads as related; can replace borders to
   guide the eye across rows.
3. **Enclosure** — light shading groups items; use it to separate e.g. actual vs.
   forecast.
4. **Closure** — people perceive complete shapes; chart borders & background fills are
   unnecessary — remove them and the chart still reads, and data stands out more.
5. **Continuity** — eyes follow the smoothest path; you can delete an axis line and
   bars still appear aligned via consistent white space.
6. **Connection** — connected objects (lines) group more strongly than color/size;
   basis of line graphs. Line thickness/darkness sets hierarchy.

### Visual order
- **Alignment:** create clean horizontal & vertical lines. Avoid center-aligned text
  (ragged edges look sloppy). Upper-left-most-justify titles/axis/legend so readers
  learn how to read the chart before reaching the data (people scan in a "Z").
- **Avoid diagonal elements.** Rotated text 45° is ~52% slower to read; 90° is ~205%
  slower. Keep text horizontal.
- **White space** = pauses in speech. Keep margins clear; size visuals to content
  rather than stretching; use emptiness strategically for emphasis (one number alone
  on a slide can be powerful).
- **Strategic contrast:** "easy to spot a hawk in a sky full of pigeons" — the more
  things differ, the less any one stands out. Make the one important thing the one
  thing that's different.

## Focus attention — preattentive attributes (Ch.4)
Iconic memory is tuned to **preattentive attributes** (size, color, position,
intensity, orientation, etc.). Used **sparingly**, they let the audience "see" the
point without reading every element (the "count the 3s" demonstration). Used
everywhere, they cancel out. They create a **visual hierarchy** that walks the audience
through the slide in the order you choose.
- **Size:** relative size = relative importance. Equal things, equal size; one
  important thing, make it big. Don't let layout accidents assign emphasis.
- **Position on page:** exploit the Z-path; put the key thing where eyes land first.
- **Test:** look away, look back — do your eyes go where you want? Or ask a colleague
  to narrate where their eyes travel.

(Color gets its own reference — see `color-and-theming.md`.)

## Narrative structure (Ch.7)
- **Two ways to persuade (McKee):** conventional rhetoric (bullets/stats — audience
  argues in their head) vs. **story** (unites idea + emotion). Story wins; "people are
  not inspired to act by reason alone." Red Riding Hood reduced to bullet points is
  lifeless.
- **Three acts (Aristotle → setup, conflict, resolution):**
  - **Beginning / setup:** setting, main character (frame it as *the audience*), the
    imbalance (what changed / the problem), the desired balance, and the solution.
    Answer "why should I care / what's in it for me?" Atkinson's questions: setting,
    main character, imbalance, balance, solution.
  - **Middle:** develop "what could be." Provide background, external comparisons,
    examples, data showing the problem, what happens if no action is taken, options,
    benefits of your recommendation, and why the audience is uniquely positioned to act.
  - **End:** an explicit **call to action**. Tie back to the opening tension; restate
    urgency.
- **Conflict/tension** ("what is" vs. "what could be," — Duarte) is essential. "But I
  don't have a problem" → reconsider; there's always tension worth framing.
- **Narrative flow / order:** the story must have a deliberate order.
  - **Chronological** (problem → data → analysis → finding → recommendation): good for
    building credibility or when the audience cares about process.
  - **Lead with the ending / call to action:** good for busy audiences who already
    trust you and want the "so what." Tells them up front what lens to use.
- **Repetition:** open with an executive-summary slide ("here's what we'll cover"),
  follow that flow, and close by repeating it ("here's what we covered") with the
  actions/decisions emphasized. Repetition makes the message stick.
- **Horizontal logic:** the slide titles, read top to bottom, should tell the story by
  themselves.
- **Spoken vs. written narrative:** live = sparse slides + voiceover carries the "so
  what"; leave-behind = the words must do the work because you're not there.
- **Nirvana** = effective visuals + a powerful narrative together. A strong narrative
  can rescue mediocre visuals, but don't rely on that.
