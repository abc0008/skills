# Color & theming sub-rubric

Source: *Storytelling with Data* Ch.4 + SWD makeover library, adapted into checks/fixes.
This expands Dimension 9 of the main rubric.

## Core principle
Color, used **sparingly**, is one of the most powerful attention tools you have. Used
generously, it's noise. "Easy to spot a hawk in a sky full of pigeons" — once the sky
fills with birds, the hawk disappears. **Every use of color should be an intentional
decision; never let the tool's defaults decide for you.**

## The base + accent model (the default to enforce)
- Design in **shades of grey** and pick **a single bold accent** to draw the eye.
- Base = **grey, not black**, because color stands out more against grey than black
  (more contrast headroom).
- Blue is a strong default accent: avoids colorblind issues, prints in B&W, neutral
  emotional tone. It is *not* the only option — deviate with reason.
- **Score 3:** neutral base, one reserved accent that lands exactly where the message
  is. **Score 0–1:** rainbow / many competing colors, nothing stands out.

## The five color lessons (each is a check)

### 1. Use it sparingly
Too many colors → "rainbow-land" → preattentive value lost (the "count the 3s"
problem; variance becomes distracting). For categorical-rank data, varying **saturation
of one color** (a heatmap) beats assigning every value its own rainbow hue, and
saturation carries an intuitive more/less meaning that rainbow categories don't.
- **Check:** count the distinct attention-colors per slide. >1–2 is a flag.
- **Fix:** collapse to grey + one accent; use single-hue saturation for magnitude.

### 2. Use it consistently (this is the theming check)
- A given color should mean the **same thing throughout** the deck. If four regions
  each have a color on slide 3, keep that exact mapping everywhere — and avoid reusing
  those colors for anything else.
- Don't change colors or chart types "so the audience doesn't get bored" — the *story*
  holds attention, not novelty. Consistent layout/chart type **trains** the audience to
  read faster and reduces fatigue.
- A **change in color signals a change** — so use a deliberate shift only when you want
  the audience to feel a change in topic or tone.
- **Check:** does category→color hold across all slides? Is the accent reused for
  unrelated things? Is type/chart styling consistent deck-wide?
- **Fix:** lock a category→color map; apply one template/master; normalize fonts and
  chart formatting.

### 3. Design with the colorblind in mind
- ~8% of men, ~0.5% of women are colorblind; usually red/green confusion.
- **Avoid red+green as the only distinction.** If you want the loss=red / growth=green
  connotation, add a second cue: bold, saturation/brightness, or a +/− sign.
- SWD's substitute pairing: **blue = positive, orange = negative** (recognizable, and
  colorblind-safe). Consider whether you even need to encode both ends — sometimes
  highlight just one.
- Test with simulators (Color Oracle, Vischeck-type tools, contrast checkers).
- **Check:** is meaning ever carried by color alone? Any red/green-only coding?
- **Fix:** pair color with text/saturation/symbol; recolor to blue/orange.

### 4. Be thoughtful of the tone color conveys
Color evokes emotion; match it to the message. A clinical statistical report may want
bold black + caps + a restrained palette; a light feature piece can use peppy colors
(hot pink/teal worked for an airline-magazine dating article — but never for a
quarterly report). For international audiences, color connotations differ by culture.
- **Check:** does the palette's mood fit the topic and audience?
- **Fix:** re-tone the palette (muted/clinical vs. bold/lively) to match intent.

### 5. Brand colors: leverage or not
- If brand colors are required, pick **one or two** as the "look-here" accents and keep
  the rest **muted grey/black**. Don't let the whole deck become brand-colored, or
  nothing stands out.
- If the brand accent is **too washed-out** to grab attention (insufficient contrast →
  visuals look faded), either draw attention with **bold black** against grey, or use a
  **complementary** attention color — just make sure it doesn't clash with the brand
  logo that appears on each slide.
- **Check:** are brand colors used as 1–2 accents over a muted base, and is the accent
  actually high-contrast? Does any chosen accent clash with the logo?
- **Fix:** restrict brand colors to accents; substitute black or a complementary color
  if the brand hue can't carry emphasis.

## Color + words (pairing) — drives the "so what"
Words and color together are a power pairing. When you write the takeaway/recommendation
in text, color the emphasized words the **same** color as the data points they describe,
so the audience instantly links the sentence to the evidence in the chart. (See
Dimension 10.)

## Quick theming checklist (apply across the whole deck)
- [ ] One template/master; consistent slide layouts.
- [ ] Neutral grey base; **one** reserved accent color.
- [ ] Category→color mapping fixed and reused identically everywhere.
- [ ] Accent reserved for emphasis only (not decoration, not every chart).
- [ ] One type system (heading/body/caption); consistent chart formatting.
- [ ] Colorblind-safe; no red/green-only coding; meaning never by color alone.
- [ ] Palette tone matches the message and audience.
- [ ] Brand colors (if required) limited to 1–2 accents over a muted base, logo-safe.
- [ ] Emphasized words color-matched to the data they reference.
