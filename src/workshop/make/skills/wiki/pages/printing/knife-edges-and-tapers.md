---
title: Knife edges and tapers
tags: [knife-edge, taper, sliver, wall, thickness, wedge, fdm]
aliases: [knife edge, feather edge, sliver, acute edge, wedge edge, zero-thickness edge, tapered edge, thin region, star points, sawtooth tip, d-flat key, taper class, edge runs out]
sources:
  - "experience: a conformal foot on a cone and a strip gauge leaning on the same cone, both cut by planes square to the axis"
  - skills/cad/scripts/check_thickness
  - "experience: 0.25 mm walls at every end of a base's segment grooves"
  - "experience: sub-nozzle knife edges that passed validate, interfere, check_fit and check_mesh"
  - "experience: sawtooth tips, a D-flat key and a sloped rib foot each failed the thickness gate as walls; lands, a square rib and a reversed slope cleared them"
  - "experience: a rim band over a sloped underside and the points of a flat-printed star read as sub-wall knife edges"
  - "experience: a 50 deg wedge between a level face and a slope failed the thickness gate as a wall; a revolved flare ended in a knife edge at its foot"
related: [wall-thickness-and-hollowing, fdm-minimum-feature-sizes, overhang-shape-recipes, rounded-bodies-on-the-print-bed, push-to-turn-indexer, interlocking-joinery-for-prints, fit-derivation]
updated: 2026-10-12
---

# Knife edges and tapers

A boolean, a slope or a pattern can leave material that thins to nothing where
two faces meet at an acute angle. Nobody drew that wall, and every soundness,
clash and mesh check passes it; `check_thickness` reads it as a wall under the
minimum ([[wall-thickness-and-hollowing#derive-the-wall-from-the-nozzle]]).
This page says which tapers are defects, which constructions make them, and
how to repair them in the generator.

## A groove through a rounded rim leaves a sliver

A constant-depth groove (0.8 × 0.4 mm segment lines on a drum) fails the
thickness gate where it meets a filleted rim, both ways: stopped short of the
fillet it leaves a thin shelf between its end and the rim, and cut through it it
leaves a sliver between the fillet's curve and the groove floor. Either drop the
groove where it meets a round (it is texture at that size) or end it in a
flat-walled face well clear of the fillet. A ring groove on a curved chest adds
an overhang too: its inner wall along the lower arc is a roof.

## Knife edges are walls too

A boolean can leave a mathematically valid solid whose material tapers to zero:
a round port meeting a circular chamber almost tangentially, a triangular brace
ending at one point, or a constant-width radial slot breaking through a curved
rim. Soundness and mesh checks pass all three; the thickness gate correctly
finds the sub-nozzle wedge near the intersection.

Repair the construction, not the mesh and not the threshold:

- replace a point contact on a brace with a finite seating edge;
- give a port a planar or otherwise non-tangent throat into the chamber;
- flare a slot mouth continuously from the guide width, then fillet the two
  outer breakthrough edges;
- fillet exposed inner and outer rim edges when the print orientation turns
  them into unsupported knife edges.

A stepped mouth merely moves the defect from the outer rim to the step. Keep
the guide region at its derived `cadfits` width, start the flare with that same
width, and widen only toward the opening. Re-measure after every such repair.

These constructions make the same acute corner and are easy to miss because
each looks like a sensible feature:

- **A bed edge under an outward lean.** A wall leaning 38 deg out from the
  bed meets the bed plane at 52 deg. On a solid part (a lid) that knife edge
  is a wall to the gate; on a hollow rim it is only a taper. Extrude the
  part's own section from 1 mm up straight down as a foot, and stand the inner
  wall vertical for about the first millimetre.
- **A hole near the edge of a convex cap.** A pin hole drilled where the
  surface has already turned 40 deg or more from square to the hole leaves a
  sub-wall sliver on the downhill side. Place holes where the surface is
  within about 20 deg of square to their axis.
- **A sheet edge laid on a body.** A sheet's edge (a cape's collar) that rests
  on a body and stands 0.2 mm proud is a thin wall. Bury it at least 1.5 mm.

- **A sawtooth tip.** A ramp meeting a wall is a wedge between two flat faces,
  and that is always a wall to the gate however long the tooth. Cut the tip
  level (a land) as wide as the mechanism allows ([[push-to-turn-indexer#lands-on-the-tips]]).
- **A D-flat inside a bore.** The flat meets the bore at a few degrees, so the
  key it leaves is a crescent that tapers to nothing at both ends. Key with a
  square-sided rib standing out of the bore instead; its corners are 90 deg.
- **A sloped underside meeting a vertical face.** A 52 deg underside (sloped so
  it prints) that rises *away* from a vertical face -- a vertical rim band or lip
  above it -- meets it at 38 deg, and the gate reads that knife edge as a 0.2 mm
  wall however thick the band. Slope it the other way -- rising *toward* the
  face, 142 deg -- give it a level land under 1 mm at the face first, or lean
  the face out about 35 deg (still inside the overhang rule) so the edge opens
  to 73 deg.
- **Star points.** The points of a flat-printed star read as walls of about
  0.13 mm. Cut each point flat to at least three line widths.
- **A revolved flare meeting a flat foot face** (a stem's foot) ends in a knife
  edge. Add an upright band about 1 mm tall at the foot.

## Wedge angle

A level face meeting a 50 deg face makes a 50 deg wedge, and the thickness
gate calls its band (about 0.86 mm at a 0.4 mm nozzle) a wall. About 56 deg or
more passes, so chamfer the level face to open the wedge.

## A part that leans on a cone: cut it square to itself

A plate whose foot follows a cone (an ear on a lamp shade), or a strip that
lies on one (a placement gauge), leans 40-50 deg off the cone's axis. Any face
cut square to the axis meets it at that angle and leaves a long feather the
thickness gate fails as a wall (0.86-0.94 mm bands 45-104 mm long here):

- the bed face of the print pose, where the leaning part meets the bed;
- a slot's closed end cut by a plane square to the axis;
- a slot's side walls, if they follow the projected outline of what sits in
  them rather than planes through the axis.

Make every cut face square to the part instead: slot walls in planes through
the axis, a slot's end on a cone normal to the strip (`revolve` a line of slope
`-1/(dr/dz)`), and where the part must stand on the bed, a short wall square to
the bed (cut the foot's first millimetre with the host's section at that
height, pushed straight down) or a flat foot 3 layers thick standing outward.
A foot cut grown along the cone instead leaves a ledge facing down. A flat foot
ring whose inner radius equals the leaning face's radius exactly at its top is
tangent to it along a circle and the union came back with 85 open edges; set
it 0.2 mm inside the material.

## A fix for a knife edge must clear the minimum wall itself

A land, a chamfer face or a fillet flat added to remove a knife edge but
narrower than 2 × nozzle trades one finding for another. Seen in practice: a
0.5 mm flat land put on each ridge crest to remove a knife edge was itself below
the minimum wall and produced dozens of thin regions; widening it to 0.9 mm
cleared nearly all of them. The trade is invisible while a gate reports only
the single thinnest point — read the whole region list before editing.

## A wall is thin, an edge tapers: not the same finding

Thickness alone cannot tell a 0.5 mm panel from the rim where a hole breaks out
of a round post: both read under the minimum wall. The second is not a defect
and cannot be designed away — any hole crossing a curved surface, any
countersink, any two faces meeting at an angle leaves material that tapers to
nothing at the boundary.

What separates them is how wide the sub-minimum band is across the surface:

- **wall** — the band is wider than one minimum wall. Real material is missing;
  fix it in the generator.
- **taper** — the band is narrower than that, so what the slicer drops at the
  edge is less than a single wall's width of material. Acceptable within a small
  surface budget (the gate uses 2 %).

A straight knife edge is always a wall: its band is `2 × min_wall / sin(2a)`
for an apex angle `2a`, which is never narrower than two minimum walls however
sharp or short the edge is. The taper class does not excuse a knife edge, an
under-thick rib or a shrunken shell — only boundaries where a feature runs out
into a curved face.

**A coarse plate grid can call a row of small teeth one wall.** The gate
clusters thin samples closer than 4 × pitch into one region, and a runner
plate's grid is coarsened to fit the cell budget. A click stub's spline teeth
(about 1 mm apart) that pass on their own part at its fine pitch then merge into
one region whose summed band reads just over a minimum wall, and the verdict
flips with the plate's pitch (failed at 0.321 mm, passed at 0.317 with the same
geometry), so moving other parts on the plate changes it. Check the part entry
at its own pitch before repairing a runner wall that lands on such teeth; the
open gate fix is to re-measure a plate-pitch wall in a window at part pitch.

**Fine graphics are colour, not relief.** A raised spoke or rib under about
1.2 mm wide on a panel whose down-facing edges are cut back for printing thins
to a blade under the minimum wall. Draw fine graphics as colour regions on one
flat raised disc or plate instead. Slots cut into a wall that prints upright
should run past the panel's full height, so none has a ceiling. Rows of short
slots each leave a 1 mm ceiling and slats under two lines.

