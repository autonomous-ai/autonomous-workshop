---
title: Minimum feature sizes and printed text
tags: [minimum-feature, pin, text, emboss, engrave, deboss, font, gap, fillet, detail]
aliases: [smallest feature, min pin diameter, embossed text, engraved text, debossed text, lettering, logo, font size, minimum gap]
sources:
  - https://mit.ek.dk/media/s4sf4t3k/3d_printing_design_rules-ultimaker.pdf (3D Hubs poster)
  - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/
  - https://www.hydraresearch3d.com/design-rules
  - https://forgelabs.com/design-guides/fdm
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://hlhrapid.com/knowledge/3d-printing-design-guide-adding-text-lettering-and-symbols/
  - https://blog.prusa3d.com/everything-about-nozzles-with-a-different-diameter_8344/
related: [fdm-design-rule-tables, wall-thickness-and-hollowing, fdm-surface-finish, fdm-layer-height-and-nozzle, text-patterns-and-surface-detail]
updated: 2026-09-23
---

# Minimum feature sizes and printed text

A feature smaller than a few extrusion lines either disappears in the slicer
or prints as a blob. The limits scale with line width in XY and with layer
height in Z. Prusa notes that nozzle diameter sets detail "almost exclusively
in the horizontal plane".

## Features, pins and gaps

| feature | value | who |
|---|---|---|
| general minimum feature | 2 mm | 3D Hubs |
| general minimum feature | > 1.8 mm or 4 × line width | Hydra Research |
| pin diameter | 3 mm | 3D Hubs, Forge Labs (industrial) |
| pin diameter | > 1.8 mm (4 × line width) | Hydra Research |
| vertical pin | reliable above 5 mm; below, take care | Hubs FDM article |
| unsupported edge (a free ledge) | < 0.9 mm (2 × line width) | Hydra Research |
| fillet | > Ø1 mm | Hydra Research |
| minimum gap | 0.5 mm | Forge Labs (industrial) |
| column or pin, special settings | down to 0.48 mm | Stratasys Direct (industrial) |

A pin's limit is a stiffness limit as much as a resolution one: a tall thin
pin sways under the nozzle. Hubs' 5 mm threshold is for vertical pins; a pin
lying along X/Y prints as extrusion lines and follows the 4-line-width rule.

```python
assert PIN_D >= 4 * LINE_W, "below four lines the slicer drops or blobs it"
assert PIN_D >= 5.0 or not VERTICAL_PIN, "Hubs: vertical pins under 5 mm need care"
```

## Text, logos and surface details

| face | emboss (raised) | engrave / deboss (cut) | who |
|---|---|---|---|
| any | 0.6 mm wide, 2 mm high | 0.6 mm wide, 2 mm deep | 3D Hubs, Formlabs table |
| horizontal (top/bottom) | > 0.9 mm wide, < 0.9 mm out | > 0.5 mm wide, < 0.9 mm deep | Hydra Research |
| vertical wall | > 0.9 mm wide, < 2 mm high | > 0.5 mm wide, < 2 mm deep | Hydra Research |
| any | 1 mm wide, 0.5 mm high | 1 mm wide, 0.3 mm deep | Forge Labs (industrial) |
| any | ≥ 0.3 mm high | ≥ 0.5 mm deep | HLH Rapid |

Font size:

- Stratasys Direct: **16 pt bold** on the top or bottom build plane, **10 pt
  bold** on vertical walls. Text on a vertical wall usually needs no
  support.
- HLH Rapid: font size 14 is "a safe minimum". Use a sans-serif font such as
  Arial; serifs and hairlines drop out.
- Forge Labs (industrial): embossed text 1.5 mm flat, 2 mm on vertical walls.

A plausible reason vertical text can be smaller (not stated by the sources): on a wall the letter's strokes are drawn
in X/Y by the perimeters at every layer. On a top face each stroke is a
region the infill must fill in a few passes.

Choose raised or cut from the stroke width. A stroke narrower than two lines
cuts better than it raises (Hydra's engrave width 0.5 mm vs emboss 0.9 mm):
an engraved groove needs one line's gap, a raised stroke needs two lines of
plastic.

A smaller nozzle is the tool for fine text: Prusa's 0.25 mm nozzle gives
"better looking printed texts" and "better resolution in XY… perfect for
jewelry, logos", at much longer print times
([[fdm-layer-height-and-nozzle]]).

Building the text in build123d — fonts, emboss on flat and curved faces:
[[text-patterns-and-surface-detail]].

## Checks

```python
assert STROKE_W >= (0.5 if ENGRAVED else 0.9), "Hydra Research stroke limits at 0.45 mm lines"
assert TEXT_PT >= (10 if ON_VERTICAL_WALL else 16), "Stratasys Direct text size"
```
