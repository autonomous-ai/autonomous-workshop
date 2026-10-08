---
title: Designing for multi-material and multi-colour printing
tags: [multi-material, multi-colour, mmu, ams, purge, wipe-tower, color-change, filament-change]
aliases: [multicolor, multi color, colour change, color print, tool change, purge volume, prime tower, wipe tower, filament swap, inlay, colour region, shared face]
sources:
  - "experience: ten multi-colour key plates reviewed against their concept tiles"
  - "experience: re-fused colour regions of a flush inlay left one open edge; the union of primitives was watertight"
  - https://forum.prusa3d.com/forum/original-prusa-i3-mmu2s-mmu2-general-discussion-announcements-and-releases/tips-for-faster-prints-and-less-purge/
  - https://help.prusa3d.com/article/wipe-tower_125010
  - https://help.prusa3d.com/article/colorprint-with-the-mmu_124861
  - "experience: a multi-colour plate of inlays failed overhang and thickness on shared faces; its fused union passed"
  - "skills/cad/scripts/printlib.py"
related: [printed-part-count, fdm-surface-finish, fdm-layer-height-and-nozzle, overhangs-and-print-orientation, wall-thickness-and-hollowing]
updated: 2026-10-08
---

# Designing for multi-material and multi-colour printing

Every material change on one nozzle costs a purge of the old colour and a
wipe-tower layer. Print time and waste scale with **changes per layer ×
layers**, and that product is set by the model's geometry and orientation.
Design to keep it small.

## Two kinds of colour change

| kind | how | cost | fits |
|---|---|---|---|
| per-layer change (ColorPrint) | switch filament at chosen heights | one change per boundary; with "no sparse layers", each change adds only one wipe-tower layer | signs, logos, plaques, tiered objects: colour zones that are horizontal bands |
| per-region (painted/assigned parts) | switch within a layer wherever colours meet | changes on every layer where two colours share it | colour regions that overlap in Z |

A colour boundary designed as a horizontal plane is almost free; the same
boundary tilted 10° costs a change on every layer it crosses. For raised
letters on a flat plate, keep the letters a different height band from the
plate.

**Modelling a per-layer colour part.** Build the print from its primitives
(the lower-colour plate, the upper-colour plate, any relief) and split nothing
afterwards: each primitive is one colour region and one labelled solid, so the
STEP carries colours a multi-material slicer imports as objects, and the print
entry's `gen_print_union()` returns their union for the mesh gates. A relief
of the upper colour standing on the lower colour inside a window is a solid of
its own. An insert sealed at a pause ([[nfc-tags-in-prints]]) goes below the
colour change with its whole roof in the lower colour, so the pause and the
filament change are two different heights, both on layer boundaries — assert
them in source.

## Purge

- Default purge is **140 mm³** per change (Prusa forum tip). Similar colours
  (black → brown) can need as little as **60 mm³**; white → black up to
  **250 mm³**.
- Dark → light needs more purge than light → dark. Order filaments
  dark → light where the sequence is free.
- Purge into infill or into a sacrificial object saves most of the waste,
  never all of it (ramming still wastes some). Dark purge in the infill can
  show through light walls; add perimeters when you use it (Prusa wipe-tower
  article).
- A wipe object absorbs purge but shows slight artefacts, so it must be a
  part whose look does not matter.

## Design rules

From the Prusa tip thread:

- Count the materials in each layer, and orient the model so that fewer
  layers hold several materials.
- Never put a colour where it is not visible: an interior region of another
  colour is pure purge cost.
- Thicker layers mean fewer layers and fewer changes: 0.25 mm instead of
  0.15 mm cuts the layer count by more than a third
  ([[fdm-layer-height-and-nozzle]]).
- Plate several models together only if they share at least two materials.

The wipe tower's density adapts per layer, from sparse to dense, with the
number of changes. PrusaSlicer's "no sparse layers" skips tower layers that
have no tool change: in Prusa's test it cut print time by 3.16 % and
tower filament by 16.17 %.

**Relief in the body's own colour does not read on black or white.** A
concept drawn as lit same-colour relief (whiskers on a black cat, a moustache
on a white beard, a wand on a purple pot) lost the detail in the review render
and barely shows on the print: give it a contrasting colour, or 1.0 mm of
height. A light colour over a dark body needs three layers or more to keep its
hue; where a sealed insert caps a flush inlay at two layers, sink a 0.4 mm
recess with a 0.6 mm light floor instead, which keeps the same roof.

## Inlays fool the mesh gates; measure the union

A colour region built as an inlay (cut out of its host, so the two share every
face they meet on) is exactly what a multi-material slicer wants, and it breaks
the print gates' view of the part. They tessellate the plate as one mesh and
voxelize it inside/outside by crossing count, so every shared face flips the
count: a cream belly three layers thick under a mint body read as 2150 mm² of
overhang "with air below", and every inlay's rim and sunk base read as thin
walls. `check_mesh` also sees the shared edges as non-manifold (pass
`--assembly` for a plate of touching colour regions).

Measure the printed object on the union: fuse each group of touching solids,
run overhang and thickness on that (a print entry that also defines
`gen_print_union()` returning that union is what the mesh gates build, so the
colour plate and the gated object come from one entry), and keep the per-region numbers only for
what they do say, that a colour region thinner than two lines prints badly as
its own colour. Two rules keep regions sound:

Build that union from the primitives, not by fusing the resolved regions back
together: the resolver only moves volume between colours, so the printed object
is every primitive united, less the grooves. Re-fusing the regions re-joins each
inlay along the face it shares with its host, and a flush six-link emblem left a
sliver (one open edge) that failed `check_mesh` on geometry that was sound.

- **An inlay is its host's material and no one else's.** A claw cut from the
  tip of a toe that overlaps the next toe takes in that toe's side, and two
  claws then share material; subtract the neighbours from each region.
- **Cut an inlay square, not as a lens.** A cap cut off by a sphere tapers to
  nothing at its rim; cut by a plane, its rim keeps the angle of the surface.

## Checks

- Colour boundaries are horizontal wherever the design allows.
- No colour region is fully enclosed by another colour.
- The spec states the colour order, and whether purge goes to infill or to an
  object.
- Overhang and thickness are measured on the fused union of each part's colour
  regions, not on the plate of inlays.
- For a single-colour print, assign colours in the model anyway (per-solid
  labels) so that a later multi-material print is a slicer choice, not a
  remodel.
