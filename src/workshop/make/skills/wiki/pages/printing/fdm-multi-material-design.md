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
  - "experience: a build review of a glow-trace inlay flagged nozzle wear, daylight colour and afterglow on thin traces"
related: [printed-part-count, fdm-surface-finish, fdm-layer-height-and-nozzle, overhangs-and-print-orientation, wall-thickness-and-hollowing]
updated: 2026-10-27
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
- A captive print-in-place part in its own colour (a swivel ring inside a
  frame) shares every layer it spans with its host, so it costs one filament
  change per layer: a 10 mm ring at 0.2 mm adds about 50 changes, half of
  them dark → light. Colouring only its top three layers costs nothing extra
  but hides it: a frame-coloured ring reads as part of the frame, and its
  tilt goes unseen. On a dual-nozzle printer, host and part each keep a
  nozzle and those changes become switches with next to no purge.

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

**Flattening relief into flush fields.** Turning a raised-and-carved design
into flush colour (for a part printed face down, or one that must feel
smooth) loses everything that read by height or shadow:

- A raised or carved detail in the colour of what surrounds it (a knot on its
  bow, a band on its body, a mouth carved into gold) vanishes. Recolour it in
  a colour that contrasts with its surroundings, or drop it and record that.
  "The darkest palette colour" is no rule on a dark body, where it is the body
  itself; there the detail goes light or goes.
- A height step between two same-colour details disappears, so the two read
  as one shape.
- Hairline gaps a raised design kept between a raised detail and a carve
  come back as body-colour hairlines. Use the full sketches and let the
  uppermost detail win the overlap.
- Then measure what the overlaps left. A strip of one colour pinched between
  two details that won over it can fall under two lines while every field's
  own sketch is wide, so a minimum-width check belongs on the resolved
  regions, not on the sketches. Measure the body colour over the whole face
  it shows on, edge rounds included: clipped to the inlay zone, every strip
  between an inlay and the zone edge reads as a sliver, though it joins the
  margin outside. A scattered dot kept less than a line from a field's edge
  leaves exactly such a sliver of body between them.
- Drop what is too thin with an opening (erode by half the minimum line, then
  dilate back) **with round joins, after every clip and every colour
  subtraction**. A mitred dilation grows past a sharp corner of the region it
  eroded: on a flush inlay that region then reached the edge cut and into a
  neighbouring colour, and the inlays overlapped by 0.5 mm3. Only the
  per-sub-cube volume check (host plus its inlays equals the bare host) saw it.
  Opening first and subtracting after leaves new slivers.
- A minimum line width does not catch a speck: an island 0.6 x 1.1 mm passes
  a 0.5 mm opening and still reads as dirt, not a dot. Drop every island whose
  minimum bounding rectangle is under the dot minimum across and under twice it
  along. Measure the body too: the hairline of body colour left between two
  colour regions is a region of its own. Hand each one under the line minimum
  to the colour it touches most, and draw designed gaps well above the minimum
  (0.8 mm, not 0.5 mm), or that fill merges them.
- **Snap the last clean-up to a grid.** Absorbing the tiny body pieces left
  between colours with float unions leaves edges 1e-4 mm apart. OCC then cut a
  host 10 mm3 deeper than its inlays, or split it into a second solid of 3e-7 mm3
  that `validate` failed as self-intersecting. Exact unions made self-touching
  rings OCC could not turn into faces. Run that pass with shapely `grid_size`
  (1e-3 mm), and assert that every decorated host is one valid solid. Measure
  hairlines with a pure round opening: an opening that also simplifies cuts
  fresh residue off every edge, so the check keeps finding work it made.
  Simplify every region once more after the last fill, before snapping: the fill
  and crumb passes add round-opening arcs and tiny edges, and leaving them in
  grew a print STEP from 64 MB to 462 MB, past Workshop's file limit.
- A colour that ran through the thickness (a stem, a cap, a scarf) becomes
  two face bands, and the wall shows the body colour between them.
- A field that meets a hole's rounded rim either clears the rim band (the
  round plus a detail clearance), covers it whole, or crosses it steeply. A
  field edge that runs along the rim inside the band leaves a thin wedge of
  colour on the round.

## Glow-in-the-dark filament

Glow PLA carries a phosphor powder (strontium aluminate), and three things
follow from that:

- **It is abrasive.** It wears a brass nozzle, so specify a hardened-steel
  nozzle in the print notes, and check the spool's datasheet, which usually
  says so.
- **In daylight it is a pale yellow-green or off-white,** not the saturated
  green it glows. Render it in its daylight colour, or the review judges a hue
  the print never shows by day. Put the glow's look in the report as
  unverified until a print is photographed in the dark.
- **Afterglow scales with phosphor volume and area.** Thin traces over a dark
  body are the dimmest case. Make the glow regions as wide as the art allows
  (two lines at least) and as deep as the inlay allows.

## A kit's plates have a filament budget

A snap kit printed as runner plates prints each plate in one job, so each
plate may need no more filaments than one multi-material unit holds (four on
an AMS). Paint each part (its fused body; a colour is the body inside a paint
volume, later paints winning) and then assign parts to plates by their colour
sets: a white-and-black thigh moved off the black plate that already carried
blue, red and gold. Keep the per-part and per-plate counts in the project's
spec audit, beside the plate-size check.

## The same art on both faces

A flat token meant to look the same from either side carries each colour field
twice, as a flush inlay in the top and in the bed face. The bed-face copy is a
colour change in the first layers, which a multi-material printer handles like
any other; nothing stands proud, so the part lies flat with no support. Seen
from below, the bed-face copy is mirrored, so choose the copy by the outline.
Art that is mirror-symmetric about an axis in the plan (a face, an emblem) uses
the same sketch on both faces. Asymmetric art inside a symmetric outline (text,
a logo, a profile on a round token) needs the bed copy mirrored about that axis,
so it reads the right way round when the token is turned over. Mirror about
the outline's own symmetry line, which need not be the part's datum axis: a
bow symmetric about a line 1.4 mm off a key's shank axis mirrors about that
line (on a pixel grid centred on it, reverse each row); mirroring about the
shank axis would shift every field off the bow. When the outline itself is
asymmetric (a die-cut silhouette, an off-axis ring loop), the bed copy must be
the same plan sketch: the outline seen from behind is already the mirror
image, and a mirrored copy would no longer sit inside it. Keep both copies
three layers deep for a light colour over a dark body, and put any sealed insert
between the two colour bands so the pause is not a colour-change layer.

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

- **Check each host, not the plate.** Assert that every host plus its own
  inlays has the bare host's volume. A region with a hole, built as one face
  from an outer and an inner wire of the wrong winding, extruded to an invalid
  solid of the right volume that every boolean ignored: the cut never happened
  and the inlay sat on top of the host. The posed-face art check passed it,
  and the fused-union print gates never see inlays. Cut holes as 2D face booleans and
  assert `is_valid` and the art's area x depth per solid.
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
