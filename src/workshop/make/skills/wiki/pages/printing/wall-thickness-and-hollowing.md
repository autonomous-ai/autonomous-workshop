---
title: Wall thickness and hollowing
tags: [wall, thickness, nozzle, hollow, shell, infill, knife-edge, taper, flute, web, fdm, resin]
aliases: [minimum wall, thin wall, shelling, offset shrink, sliver, feather edge, rib spacing]
sources:
  - "experience: 0.25 mm walls at every end of a base's segment grooves"
  - skills/cad/scripts/cadprint.py (min_wall, shell_wall, hollow, open_shell, savings)
  - skills/cad/scripts/check_thickness
  - "toolchain: build123d offset(solid, -wall) returns a smaller solid, not a shell (reproducible: Box 20 -> 4096 mm3)"
  - "experience: sub-nozzle walls, knife edges and over-hollowed parts that passed validate, interfere, check_fit and check_mesh"
  - "experience: sawtooth tips, a D-flat key and a sloped rib foot each failed the thickness gate as walls; lands, a square rib and a reversed slope cleared them"
related: [overhangs-and-print-orientation, printed-part-count, joints, resin-printing-design, print-time-and-material-estimation, ribs-and-stiffening, lightweighting-and-lattices, push-to-turn-indexer]
updated: 2026-10-04
---

# Wall thickness and hollowing

What a part costs to print, and whether the nozzle can lay a wall down at all,
is a question no soundness check asks. A wall the nozzle cannot lay down and a
solid core no one will ever see are both valid, closed, manifold solids. This
page holds the rules that decide wall, shell and edge geometry; the gate that
measures them is `check_thickness` (usage in
`skills/cad/references/print-optimisation.md`).

## `offset(solid, -wall)` does not hollow anything

The sign reads like "shell inward" and the result is a valid solid either way.

```python
offset(Box(20, 20, 20), -2, kind=Kind.INTERSECTION).volume    # 4096.0
```

4096 is 16 cubed. It **shrank the box**; a 2 mm shell is 3904. The same call on
a sphere returns the smaller ball, not a shell. Nothing downstream notices — the
part is closed, manifold, positive-volume and the right shape, just solid and
undersized, and every gate in the toolchain passes it.

The two forms that hollow:

```python
import cadprint
sealed = cadprint.hollow(part, cadprint.shell_wall(0.4))          # 3904.0
opened = cadprint.open_shell(part, wall, part.faces().sort_by(Axis.Z)[-1])
```

`hollow` is `part - offset(part, -wall)`. `open_shell` is `offset` with its
`openings` argument, the one path where a bare `offset` shells rather than
shrinks. Both refuse rather than return something plausible when the wall is
too thick for the part: a bare `offset` on a 3 mm slab at 2 mm raises
`ValueError: Null TopoDS_Shape object`, which reads like a corrupt model.

A sealed void exports as a mesh with **two shells**, an outer and an inner.
That is correct, not a defect.

## A moved copy is not an offset

A skin made by **moving** the outside, not offsetting it (a cap over a key cut
as the outside translated back along the insertion axis, or an inlay's floor),
is `t` thick along that axis and only `t · cos θ` square to the surface, where θ
is the angle between the surface normal and the axis. On a dome it is thinnest
where the dome slopes most: at 46° the wall is 0.69 of the move. Size the move
from the steepest slope under the part (`t = wall / cos θ_max`), and assert the
wall with a measured distance (`min_gap` between the inlay and the pocket), never
with the move you asked for. The same holds for a clearance made by moving a
surface: it is thinner than asked wherever the surface slopes to the axis.

## Derive the wall from the nozzle

```python
import cadprint
MIN_WALL = cadprint.min_wall(NOZZLE)        # 2 lines: the thinnest printable wall
SHELL    = cadprint.shell_wall(NOZZLE)      # 3 lines: a wall that also carries load
```

Below two extruded lines a slicer either drops the wall or prints two perimeters
with a gap between them, and neither shows up in any B-rep check — the STEP is
perfect and the print has a hole. A wall typed as `0.8` is the same defect
`cadfits` exists to prevent on the mating side: a number that stops being true
when the nozzle changes, with nothing to catch it
([[fit-derivation#write-the-mate-as-a-derivation]]). Shell at more than the
minimum, so there is a perimeter left for a fillet, a boss or a countersink.

## A repeated feature's count is a wall

The rule reaches one step further than the wall you drew, to the material left
*between* two copies of a feature you drew nowhere. A knurl, a flute, a vent
slot, a cooling fin, a tick ring: the count is nearly always typed for looks,
and it silently sets a wall.

    web = 2 R sin(pi / n) - 2 r        # n circular flutes of radius r on a rim R

24 flutes of R2.5 on a R22 rim leave **0.744 mm** against a 0.800 mm minimum
wall. Every soundness, clash, fit, mesh and overhang check passes it; only the
thickness gate finds it, after a full tessellation and voxelisation — the most
expensive place to learn it. So solve the count from the web rather than
checking the web after choosing the count:

```python
FLUTE_WEB = 2.0 * MIN_WALL      # twice the limit: the gate reads low by a step
FLUTE_COUNT = int(math.pi / math.asin((FLUTE_WEB + 2.0 * FLUTE_R) / (2.0 * DISC_R)))
```

At 20 the same rim leaves 1.883 mm. The count is the *output*. Written the
other way round — count typed, web asserted — the check restates the arithmetic
and cannot fail ([[fit-derivation#write-the-mate-as-a-derivation]]).

The pathological case is a pitch exactly equal to the feature size, where the
web goes to zero and neighbouring pockets touch at a point. That is a
**non-manifold edge** rather than a thin wall; the mesh gate catches it where
the thickness gate does not.

## Hollowing is worth less than the volume it removes

The volume that leaves the model is not the filament that stops being extruded.
The slicer was only going to put its infill fraction into that space anyway:

| | measured on a lofted body |
|---|---|
| solid | 16.18 cm3 |
| shelled at 1.2 mm | 3.72 cm3 |
| **removed from the model** | **12.46 cm3 (77 %)** |
| filament actually saved at 15 % infill | **1.87 cm3, 2.3 g** |

Reporting the first as if it were the second overstates the result by about six
times (`cadprint.savings()` returns both). Hollowing also adds material back —
the inner surface gets its own top and bottom skins — so treat the second
number as an upper bound too.

What hollowing is actually for: weight, cooling and warp on a thick section, and
resin volume. For FDM bulk material alone, lowering infill in the slicer gets
most of the same saving with none of the modelling risk.

Estimating the mass and time a hollowed part actually saves:
[[print-time-and-material-estimation]]. Stiffening a thin wall with ribs
instead of thickness: [[ribs-and-stiffening]].

A small pocket in a printed part can add mass, because its wall costs more
than the infill it replaces: [[lightweighting-and-lattices]].

## When not to hollow

- **A part under load.** The shell carries it alone once the infill is gone.
- **A part with a sealed void, printed in resin.** Uncured liquid has nowhere to
  go. An open shell, or a drilled drain, is the fix; every separate pocket a
  hollow creates needs its own drain.
- **A section already near the minimum wall.** Measure before choosing a wall;
  `hollow` refuses when the part is thinner than twice it, but a section at
  2.5 × wall passes and leaves a wall with no margin.
- **A thin feature already failing the thickness gate.** Fix that first —
  hollowing a part that has a 0.5 mm fin does not make the fin printable.

Resin hollowing — shell thickness, drain and vent holes, cupping — is in
[[resin-printing-design]].

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

Three constructions make the same acute corner and are easy to miss because
each looks like a sensible feature:

- **A sawtooth tip.** A ramp meeting a wall is a wedge between two flat faces,
  and that is always a wall to the gate however long the tooth. Cut the tip
  level (a land) as wide as the mechanism allows ([[push-to-turn-indexer#lands-on-the-tips]]).
- **A D-flat inside a bore.** The flat meets the bore at a few degrees, so the
  key it leaves is a crescent that tapers to nothing at both ends. Key with a
  square-sided rib standing out of the bore instead; its corners are 90 deg.
- **A sloped underside meeting a vertical face.** A 52 deg underside (sloped so
  it prints) that rises *away* from a vertical face meets it at 38 deg. Slope it
  the other way -- rising *toward* the face, 142 deg -- or give it a level land
  under 1 mm at the face first.

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

## Record the wall

A project that ships a hollowed part states the wall it was shelled at beside
the measurement that checked it; a volume in a chat log is not a record.

How nozzle, line width and layer height set the wall: [[fdm-layer-height-and-nozzle]]; published wall limits side by side: [[fdm-design-rule-tables]].

## Two cavities closer than twice the wall break the offset

`offset(part, -wall)` is the core of every hollow here. On a body with several
cavities cut into it (wheel arches and an open engine bay) the offset collapses
when two cavity faces are closer than `2 * wall`: a 3 mm web between a bay and an
arch at a 2.4 mm wall returned a core of 68 000 mm3 for a body of 1 600 000 mm3,
with no exception, and the "hollow" was nearly solid. A web of 6 mm worked.
Compute the core once without the cavities and once with them and compare the two
volumes (they differ by roughly the cavity volumes, not by a factor of twenty),
and keep every web at `2.5 * wall` or more.
