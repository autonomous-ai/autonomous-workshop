---
title: Layer height, nozzle size and line width
tags: [layer-height, nozzle, line-width, extrusion-width, perimeter, resolution, print-time, strength]
aliases: [nozzle diameter, 0.4 mm nozzle, 0.6 mm nozzle, 0.25 mm nozzle, extrusion width, perimeters, wall loops, layer thickness]
sources:
  - https://help.prusa3d.com/article/layers-and-perimeters_1748
  - https://blog.prusa3d.com/everything-about-nozzles-with-a-different-diameter_8344/
  - https://www.cnckitchen.com/blog/the-influence-of-layer-height-on-the-strength-of-fdm-3d-prints
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://www.protolabs.com/resources/design-tips/3d-printing-tolerances/
related: [wall-thickness-and-hollowing, fdm-minimum-feature-sizes, fdm-print-orientation-for-strength, fdm-design-rule-tables, print-time-and-material-estimation]
updated: 2026-09-23
---

# Layer height, nozzle size and line width

Three numbers from the slicer profile fix every minimum on the other
printing pages: nozzle diameter, line (extrusion) width and layer height.
Write them into the parameter block as the print assumption, and derive walls,
pins and gaps from them ([[wall-thickness-and-hollowing#derive-the-wall-from-the-nozzle]]).

## Limits

| rule | value | who |
|---|---|---|
| maximum layer height | below 80 % of the nozzle diameter (0.32 mm on 0.4; 0.48 mm on 0.6) | Prusa KB, Prusa blog |
| layer height for strength | at most half the nozzle diameter (0.2 mm on 0.4) | CNC Kitchen |
| layer-height sweet spot on 0.4 | 0.15 mm; thinner layers did not bond better | CNC Kitchen |
| quality floor | below 0.10 mm the gain is "relatively minor with significantly longer print times" | Prusa KB |
| first layer | 0.20 mm in every Original Prusa profile | Prusa KB |
| perimeter line width (0.4 nozzle) | 0.45 mm baseline | Prusa KB |
| two perimeters at 0.2 mm layers | 0.86 mm, not 0.90: lines overlap | Prusa KB |
| visible stair-stepping | from about 0.2 mm layers on curved surfaces | Protolabs |

The 0.86 mm figure matters to the wall rule. Two lines are not
`2 × line width`, because adjacent lines overlap. Take the wall the slicer
actually produces for N perimeters, or design a hair above
`N × line width`. Stratasys Direct's slice → wall table shows the same
coupling on industrial machines ([[fdm-design-rule-tables#side-by-side]]).

## What the nozzle changes

- **Detail is XY only.** Nozzle diameter sets detail "almost exclusively in
  the horizontal plane"; Z detail is layer height (Prusa blog).
- **0.25 mm**: better printed text and XY resolution ("jewelry, logos"),
  significantly longer prints; impact test absorbed 3.6 % less energy than 0.4.
- **0.6 mm**: "print times up to twice as fast" at nearly 0.4 quality for most
  objects, and absorbed up to 25.6 % more impact energy than 0.4. Prusa's
  recommended single alternative nozzle.
- **1.0 mm**: up to 5× faster than 0.4, with visible layers and limited
  detail; example widths 1.10 mm perimeter, 1.12 mm infill.

Print time bounded by volumetric flow: [[print-time-and-material-estimation]].

## Strength

- Strength comes mostly from the **number of perimeters**, not the infill;
  Prusa profiles use at least two (Prusa KB).
- Layers thicker than half the nozzle cut layer adhesion sharply. On a
  0.4 nozzle, 0.3 mm layers kept about half the standing load and 0.4 mm
  essentially none. In-plane strength also fell at 0.3 and 0.4 mm
  (CNC Kitchen).

## Choosing

```python
NOZZLE = 0.4
LINE_W = 0.45                       # slicer perimeter width
LAYER_H = 0.2                       # or 0.15 for strength-critical parts
assert LAYER_H < 0.8 * NOZZLE, "slicer limit"
assert LAYER_H <= 0.5 * NOZZLE or not STRENGTH_CRITICAL, "layer adhesion falls off above half the nozzle"
```

Pick the nozzle from the smallest XY feature that must survive (text, thin
fins) and the largest part that must print in reasonable time. A model
designed for 0.6 mm lines must say so: its walls, text and gaps are sized
from that width, and they will not all hold on a 0.4 profile, or the
reverse.
