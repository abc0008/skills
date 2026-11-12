# motion-design

Editorial (Vox-inspired) motion graphics built in plain HTML, SVG and CSS, exported as GIFs for PowerPoint.

Two kinds of output:

- **Explainer icons**: small animated icons that act out the core concept of a slide or section, drawn with Lucide icons and short labels taken from the slide's own words.
- **Data animations**: charts, tables and key figures that build, then pull the eye to the one number the slide is about.

## Commands

| Command | What it makes |
| --- | --- |
| `/motion-design icons <source>` | Explainer icons only, one per major point |
| `/motion-design data <source>` | Data animations only, one per figure, table or key statistic |
| `/motion-design both <source>` (or no mode word) | Both, chosen per slide from the content |
| add `pptx` | Also exports GIFs, builds a deck with one graphic per slide, and render-checks it |
| add `gifs` | Exports the GIFs and stills only |

It pairs with `doc-to-infographic`: run both on a document to get an infographic page with one animated icon per section.

## Contents

- `SKILL.md`: the skill.
- `scripts/mo_frames.py`: renders an 8-frame sheet per graphic for review, and exports GIFs and stills. Icons play three times and rest on the finished frame; data animations play once. The first frame of every GIF is the finished picture, so slides are never blank in editing view.
- `scripts/lucide.py`: searches Lucide by keyword and outputs an icon ready to place in an icon.
- `scripts/build_pptx.py`: builds a deck with one graphic per slide from an example page.
- `scripts/pageshot.py`: full-page screenshot after every scroll reveal has fired.
- `assets/examples/`: tested pages, GIFs and decks (see below).

## Setup

```
pip install playwright pillow python-pptx && playwright install chromium
npm install lucide-static      # or set LUCIDE_STATIC to the package folder
```

`soffice` (LibreOffice) is used for the deck render check.

## Examples

| Folder | What is in it |
| --- | --- |
| `assets/examples/explainer-icons/` | Three pages of icons (22 in all, plus one data animation) made from articles on self-service analytics, with their GIFs. `lucide-icons.html` is the best reference for the current style. |
| `assets/examples/data-animation/` | Six data shapes (big number, before/after, trade-off, table, part of whole, trend) with GIFs, stills and a deck. |
| `assets/examples/infographic-pairing/` | A full infographic with five icons, the generator that builds it, the GIFs and a deck. |

The example pages paraphrase public articles from Anthropic, Robinhood, Databricks and Ramp; each page names its source. Figures shown come from those articles.

## Credits

- Icons: [Lucide](https://lucide.dev) (ISC licence).
- Easing curves adapted from [richtabor/agent-skills](https://github.com/richtabor/agent-skills) `motion-design`.
