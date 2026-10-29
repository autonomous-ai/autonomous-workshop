---
title: Bed edges and rounded bodies on the print bed
tags: [overhang, orientation, bed, organic, fillet, chamfer, teardrop, support, sculpt, elephant-foot]
aliases: [rounded back, narrow bed footprint, support under a sculpt, section backing, bed chamfer, bed edge, bed-contact edge, base chamfer, bottom chamfer, elephant foot chamfer, bottom chamfer fails, teardrop bed edge, bed fillet]
sources:
  - skills/cad/scripts/check_overhang
  - https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/ (45° chamfer or radius on bed edges)
  - https://www.hydraresearch3d.com/design-rules (base chamfer ~0.3 mm, first layer + one layer)
  - "experience: a clipped rounded body and leading rim still grew too quickly from their bed contact; exact-section backing preserved their visible front curves"
  - "experience: filleted bed rims and hole mouths failed support checks until replaced by tangent teardrop profiles"
  - "experience: chamfered voxel parts failed check_overhang on their bed outlines"
  - "experience: a narrow bed chamfer failed the overhang gate at 52 deg from the bed and passed at 63 deg"
  - "experience: chamfer and section-offset both failed on the bed edges of a lofted flexi chain"
related: [overhangs-and-print-orientation, overhang-shape-recipes, fdm-first-layer-and-warping, fillet-chamfer-pitfalls, knife-edges-and-tapers, flexi-chain-joints, layer-anisotropy]
updated: 2026-10-10
---

# Bed edges and rounded bodies on the print bed

Every printed part meets the bed at an edge, and that edge is where the
overhang gate fails a part that is otherwise sound. This page is the one home
for how to break a bed edge, round it, and back a rounded body down to the
bed.

## Breaking the bed edge

The first layer spreads into elephant's foot, so a bed edge that must look or
fit right is broken by at least `FIRST_LAYER_H + LAYER_H` (about 0.3 mm,
Hydra Research; [[fdm-first-layer-and-warping#elephants-foot]]), or left sharp
for the slicer's elephant's-foot compensation. The overhang gate, not the
published advice (the Hubs FDM article: a 45° chamfer or radius on edges
that touch the plate), sets the break's shape:

- **No fillet.** A round on the bed edge is a fillet whose last few degrees
  face the bed: an overhang. Draw a round as the teardrop below.
- **No symmetric 45° chamfer.** Tessellated, some of its facets measure just
  under the limit, and on any part larger than a few millimetres the gate
  flags the bed-face outline ("overhang ... reaching inf" at z 0.3–0.4 mm).
- **An asymmetric chamfer, short leg on the bed face, leaning at most 30° off
  vertical** (60° or more from the bed). A 2 mm wide chamfer at 52° from the
  bed failed, its tessellated facets reading flatter than drawn, and 63°
  passed. 30° off vertical is the same line the teardrop below and a
  bed-face groove's flanks use
  ([[overhang-shape-recipes#low-points-leaning-reliefs-and-stacked-rounds]]).

```python
import math
BED_BREAK_IN = FIRST_LAYER_H + LAYER_H                     # ~0.3 mm: elephant's foot
BED_BREAK_UP = BED_BREAK_IN / math.tan(math.radians(30))   # ~0.52 mm: 30° off vertical
bed = body.faces().sort_by(Axis.Z)[0]
body = chamfer(bed.edges(), length=BED_BREAK_IN, length2=BED_BREAK_UP, reference=bed)
assert math.degrees(math.atan2(BED_BREAK_IN, BED_BREAK_UP)) <= 30.01, "bed chamfer flatter than 60° from the bed"
```

A part printed **on its side** has a whole side face as its bed face, so every
edge round of that face is a bed fillet; the gate flags the slivers under each
one. Break those edges with the same asymmetric chamfer, `reference` the side
face, and give the opposite face the same break so the part still reads
symmetric.

An edge whose wall already leans outward hangs flatter with any break across
it: leave it sharp
([[overhang-shape-recipes#a-break-on-an-edge-that-already-leans-out-hangs-flatter]];
the wedge such an edge leaves is in [[knife-edges-and-tapers]]).

## Rounding the edge on the bed face

A teardrop round: the arc runs from the wall to 30° from vertical, and its
tangent line carries on to the bed. On a 0.8 mm round the back's outline
sits 0.34 mm in and the line rises 0.4 mm; the 0.2 mm layers step those
0.8 mm anyway, so one band for the arc and one for the line read as round.
A hole's rim on the bed face is the same edge turned inward: a 0.5 mm fillet
there faced the bed over 4 mm². Cut the hole with one revolve of the hole and
its 30° flare, so the round meets the bore inside the cutter, and fillet only
the rim on the top face.

On an extruded plate (any outline, holes included) build the teardrop as two
edge operations on the bed face's edges, not as a swept profile. With radius
`R` and the arc stopping `a` off vertical, the line's legs are

```text
in = R (1 - cos a) + R (1 - sin a) tan a     along the bed face
up = in / tan a                              up the wall
```

(`R` 0.6, `a` 30°: 0.254 and 0.439). Chamfer every edge of the bed face with
`chamfer(edges, length=in, length2=up, reference=bed_face)`, then fillet the
loop of edges the chamfer left on the walls at `Z = up` with `R`: the fillet's
tangent length `R tan(a/2)` puts the arc's top at exactly `R` up the wall,
matching a top-edge round of the same `R`. In build123d, `length` is the leg on
the `reference` face (OCC `MakeChamfer.Add(d1, d2, edge, face)` measures `d1`
on `face`); give no reference and the legs land on whichever face comes first.
A square-stepped pixel outline with dozens of concave corners took both
operations at once and printed with no support region.

## A lofted belly: relieve the bed edge in the tools

A 45° chamfer on the edges where a lofted or scaled-sphere body meets the bed
fails outright (`Failed creating a chamfer, try a smaller length value(s)`,
every segment of a lofted chain, every length), and the fallback of offsetting
the body's bed section inward and extruding it with a taper fails too:
`offset()` of that section returns a Null shape. Put the relief into the tools
that made the faces instead: where two bodies meet on the bed, cut each face
back by the relief at z = 0 and return it to its place over the first few
layers, with the same cutter grown and tapered. A cylinder becomes a cone; a
wedge of half-angle `a` grown by `d` keeps its angle with its apex `d / sin(a)`
further back, and `extrude(face, amount, taper=)` draws it. Lean the taper no
flatter than any other bed break, 30° off vertical
([[rounded-bodies-on-the-print-bed#breaking-the-bed-edge]]): a 0.3 mm relief
rises about 0.52 mm. A plain step two layers
tall is not the same thing: its ceiling is a flat ledge that the overhang gate
reads as needing support. Other chamfer failures:
[[fillet-chamfer-pitfalls]].

## Exact-section backing for a reconstructed rear surface

An unobserved rear is not permission to cut a full-volume figurine flat for
the print bed. Preserve a coherent rounded continuation of its body unless
a flat back is part of the design brief or an accepted reconstruction choice.
Review a back view and both rear three-quarter views as well as the supplied
front views: a front silhouette can completely hide a planar rear truncation.
Changing print orientation does not require changing the exterior geometry.

A flat cut through the back of a rounded body can leave a narrow bed contact
whose next layers expand too quickly. Where that rear surface is reconstructed
and may change, take an exact cross-section at a station with a safe outer
slope and extrude it back to the existing bed plane, then fuse it into the
body. This gives the visible front curve support without a rectangular
pedestal; a rounded raised rim can use the same construction beneath its rear
half. Check that the new material preserves socket walls, assembly clearance
and every reference silhouette. This is a source geometry change, so rerun the
affected likeness and print gates; it is not permission to fill a defining
visible gap or flatten a known reference surface.

Never replace a reference-defining visible curve solely to hide a print-gate
failure. A faithful support-required concept and a verified support-free print
are different claims.
