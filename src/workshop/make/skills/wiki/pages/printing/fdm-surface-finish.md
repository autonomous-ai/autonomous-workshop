---
title: Surface finish, seams, ironing and fuzzy skin
tags: [surface-finish, seam, ironing, fuzzy-skin, appearance, stair-stepping, top-surface, texture]
aliases: [z seam, seam placement, scarf seam, ironing, fuzzy skin, textured walls, layer lines, cosmetic finish]
sources:
  - https://help.prusa3d.com/article/seam-position_151069
  - https://help.prusa3d.com/article/ironing_177488
  - https://help.prusa3d.com/article/fuzzy-skin_246186
  - https://www.hubs.com/knowledge-base/how-does-part-orientation-affect-3d-print/
  - https://www.protolabs.com/resources/design-tips/3d-printing-tolerances/
related: [fdm-minimum-feature-sizes, fdm-print-orientation-for-strength, overhangs-and-print-orientation, printed-part-count, post-processing-and-finishing, moulds-and-casting-from-prints]
updated: 2026-09-23
---

# Surface finish, seams, ironing and fuzzy skin

What a printed surface looks like is decided partly by the model: which way
faces point, where corners are, what is flat. Slicer finishes help only the
faces that geometry allows.

What sanding, filler, paint, epoxy and vapour smoothing add or remove, and
which faces to mask: [[post-processing-and-finishing]].

## Which faces look best

From the Hubs orientation guide:

| face | finish |
|---|---|
| top surfaces | smoothed by the nozzle |
| bed-contact face | typically glossy |
| support-contact faces | visible support marks |
| curved walls | stair-stepping, noticeable from about 0.2 mm layers (Protolabs) |

Put the face the viewer sees on top or on the bed, never on supports. A
gently sloped top shows every layer as a contour line; a flat top or a
vertical wall does not.

A mould copies every layer line into the casting:
[[moulds-and-casting-from-prints]].

## Seams

Every perimeter loop starts and ends somewhere, and that point leaves a
seam. Prusa's placement options:

| option | behaviour | use |
|---|---|---|
| Nearest | a concave, non-overhang vertex near the start, so the seam hides in the corner | models with sharp corners |
| Aligned | the same place every layer: one straight line | when a line is acceptable |
| Rear | aligned, toward the back of the bed | display objects with a front |
| Random | a different place each layer | spreads weak points and adds strength; scatters blemishes; poor on cylinders |
| Scarf joint | overlaps the loop ends | smooth curved perimeters; slower, poor at sharp corners and overhangs |

"Sharp corners are your allies." A seam at a sharp inside corner is
effectively invisible. A smooth cylinder has nowhere to hide it. **Design a
corner, groove or edge where the seam may go** on any visible round part, and
orient the part so that feature faces the back.

## Ironing

A second pass at the same layer height over flat top surfaces. The hot
nozzle flattens curled plastic and fills pinholes with a trickle of material
(Prusa). Good for nameplates, logos, box lids, and faces that will be glued.
Useless on round, organic or sloped surfaces. It adds print time, can clog
with PLA in a warm room, and slightly softens edges. Only a face parallel to
the bed benefits, so to get an ironed finish, design the face flat and
horizontal.

## Fuzzy skin

Resamples the perimeter with random in/out offsets to make a rough,
fibre-like texture that grips and hides layer lines (Prusa). Thickness is the
maximum offset each way (0.3 mm is rougher than 0.1 mm); point distance is
the spacing (0.5 mm is finer than 1.0 mm). It can be applied to outside
walls or all walls, per object, by modifier or by painting. It **changes the
wall's dimensions**, so never apply it to a mating, sliding or sealing face.
Paint it on the grip and handle only.

## Checks

- The visible face is up or down in print orientation, not on supports.
- Every round visible part has a designed seam line (corner, groove or
  parting edge).
- Ironed and fuzzy regions are named in the print notes; fuzzy skin stays off
  every face listed in the fit audit.
