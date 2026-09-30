---
title: Printed hole accuracy
tags: [hole, polyhole, horihole, teardrop, undersize, accuracy, tolerance, bore, ream, thread]
aliases: [undersized holes, polyholes, horiholes, hole compensation, hole shrinkage, xy hole compensation, printed bore]
sources:
  - https://hydraraptor.blogspot.com/2011/02/polyholes.html (nophead, Polyholes)
  - https://gilesbathgate.com/2016/02/07/polyholes-revisited/
  - https://hydraraptor.blogspot.com/2020/07/horiholes_36.html (nophead, Horiholes)
  - https://www.hubs.com/knowledge-base/how-does-part-orientation-affect-3d-print/
  - https://www.stratasys.com/siteassets/sdm/resources/design-guidelines/fdm/fdm_design_guidelines_2017-1.pdf
  - https://www.hydraresearch3d.com/design-rules
related: [fit-derivation, joints, shafts-and-bearings, fdm-design-rule-tables, overhangs-and-print-orientation, fluid-fittings-and-pneumatics]
updated: 2026-09-23
---

# Printed hole accuracy

Holes print undersize even on a printer whose outside dimensions are right.
Know why before choosing a correction, because the corrections are not
interchangeable.

## Why a vertical hole comes out small

nophead identified four mechanisms:

1. **Faceting.** A cylinder exported as triangles is a polygon with its
   vertices *on* the circle, so its flats are inside it: the hole shrinks by
   `cos(π / n)`. It takes 10 vertices to get under 5 % error and 22 to get
   under 1 %.
2. **Segment pauses.** A stall between short segments lets plastic ooze into
   the hole.
3. **Arc shrinkage.** A bent strand has too much plastic on the inside of the
   curve and too little on the outside.
4. **Corner cutting** (the dominant one, in nophead's view): the strand
   resists the circular path and takes a shortcut, drawing a smaller circle.

Stratasys Direct says the same of industrial FDM: holes, including those in
bosses, are "generally fractionally undersized", and where tolerance matters
they are drilled or reamed.

## Polyholes, and why the simple rule is not universal

nophead's empirical polyhole: a polygon with `n = max(round(2 × d), 3)`
sides (d in mm), circumscribed so its flats sit on the nominal circle:

```python
import math
def polyhole(d):
    n = max(round(2 * d), 3)
    return n, (d / 2) / math.cos(math.pi / n)   # (sides, vertex radius)
```

On his machines every drill over 1 mm fitted its hole.

Giles Bathgate repeated the test and the `2 × d` rule failed: holes were too
small, and each drill needed the hole one size up. His revision compensates
arc shrinkage explicitly from the track width `t`:

```text
arc(r, t)          = (t + sqrt(t² + 4 r²)) / 2
polyhole(r, n, t)  = arc(r, t) / cos(180° / n)
```

With it, every drill from 1 to 10 mm fitted snugly, and "higher tolerance
requires more facets, not less". The lesson is that the correction depends
on track width, layer height, perimeter count and material, not on the hole
alone. **Calibrate on the printer, then write the correction as a function in
the parameter block.** Do not hard-code another printer's offsets.

## Horizontal holes: teardrops and horiholes

A hole whose axis lies in the bed plane has two problems. Its roof is an
overhang ([[overhangs-and-print-orientation]]). And the slicer samples each
layer at its mid-height, so the stair-step corners at top and bottom intrude
into the circle. The Hubs orientation guide notes that a horizontal cylinder
facets and loses accuracy, where a vertical one prints smooth and accurate.

nophead's **horihole** fixes both. Start from a truncated teardrop (45° roof),
then take the hull of that shape shifted up half a layer and down half a
layer. The steps then land on the circle instead of inside it. The shape is
specific to one layer height (his test: a 6 mm hole at 0.25 mm layers), and
plug gauges fitted 1–5 mm holes easily.

Teardrop sections for internal fluid channels:
[[fluid-fittings-and-pneumatics]].

## Rules

- Holes that must fit a part: calibrate, then use a compensation function
  (polyhole, arc-compensated polyhole or horihole). Otherwise, print a pilot
  and drill or ream (Stratasys Direct).
- Minimum printable hole: Ø2 mm on desktop FDM (3D Hubs poster; Hydra
  Research "> Ø2 mm"). Smaller holes are drilled.
- A hole axis in the bed plane prints worse than one along Z. Orient
  precision bores vertically where the load path allows
  ([[fdm-print-orientation-for-strength]]).
- Built-in threads: none below Ø1.6 mm (Stratasys Direct). Hydra Research
  models threads only above M5 / UNC #10. Otherwise tap, or use inserts
  ([[printed-threads-and-bosses]]).
- The fit between a hole and its partner still comes from `cadfits`
  ([[fit-derivation]]). Hole compensation corrects the *printer's* error, not
  the design clearance, and the two are applied separately.
