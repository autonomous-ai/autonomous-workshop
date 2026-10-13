---
title: Fillet and chamfer pitfalls
tags: [fillet, chamfer, bevel, radius, sigsegv, spline, offset, taper]
aliases: [rounding, edge blend, retry ladder, BRep_API command not done, fillet failure, periodic spline, bed chamfer, elephant foot chamfer, bottom chamfer fails]
sources:
  - "experience: front-edge fillets on ten flat key plates, failing on sub-0.1 mm plan edges"
  - skills/cad/references/build123d-modeling.md (fillet, chamfer and periodic-spline sections; before the move)
  - skills/cad/references/repair-loop.md (fillet failure class; before the move)
  - skills/image-to-cad/references/build123d-operations.md (sketch fillet order; before the move)
  - "toolchain: build123d 0.10-0.11 on OCP 7.9"
  - "experience: chamfer and section-offset both failed on the bed edges of a lofted flexi chain"
  - "experience: a bevel round a flat-faced limb failed on the fused limb and on one mirrored side"
  - "experience: a rounded screen tray whose acute rear edge consumed the rim behind the lens"
  - "experience: a traced, freeform token outline whose top-edge fillet failed its walk at every sample count; rounded instead by ruled bands"
  - "experience: a key-plate outline of circles, ellipses and lines whose batch 2D fillet failed on one short edge, whose taper cap failed on its ellipses, and whose 3D top-edge fillet passed"
related: [construction-strategy, operation-families, kernel-validity, modeling-failure-modes, flexi-chain-joints]
updated: 2026-10-08
---

# Fillet and chamfer pitfalls

Fillets are the most failure-prone operation in the kernel: do them last,
after every boolean, and prefer putting the radius into the profile.

## Common causes and fixes

Likely causes of a fillet or chamfer failure:

- radius/length exceeds local geometry (fillet radius larger than the local
  edge geometry);
- selected edges include tiny or unintended edges;
- a boolean created complex edge topology.

Fix:

- reduce radius/length — but never silently reduce a radius the user
  specified;
- filter the selected edges more narrowly;
- apply fillets later in the model;
- split edge groups by feature intent;
- move the radius into the sketch profile as a 2D fillet, or into the lofted
  section.

## Retry ladders degrade silently

The `pipe()`-style retry ladder (`[bend, .7, .5, .3, 20]` around
`FilletPolyline`) exists for a good reason: one oversized corner otherwise
kills an entire build with `BRep_API: command not done`. But it converts a
hard failure into an invisible cosmetic regression.

Where a profile cannot accept the nominal radius, the ladder silently falls
back — a 6 mm rim fillet became ~2 mm on a 660 mm-diameter flange, which
tessellates as a visible sawtooth. The build reports success; only a render
cropped to ~5× shows it.

Do not rely on the ladder for cosmetic radii. Reshape the profile so the
intended radius genuinely fits (a knife-edged wafer cannot take any fillet;
merge it into its neighbour), then verify by cropping the render.

## An acute edge eats r / tan(t / 2) of each face

A round of radius `r` between two faces meeting at interior angle `t` is
tangent to each face `r / tan(t / 2)` from the edge: `r` at 90 deg, 0.58 r at
120 deg, and 3.3 r at 34 deg. On the acute rear edge of a tilted tray (top
face against an undercut), a 2 mm round would have eaten 6.5 mm of the top and
uncovered a lens pocket with a 2.5 mm rim. Size the round per edge from that
formula against the face's narrowest feature, and fillet in one
`BRepFilletAPI_MakeFillet` with a radius per edge (`Add(r, edge)` for each):
three radii on a convex wedge built in 0.1 s. Skip edges whose two faces are
tangent (a straight side running into a corner arc); filleting them fails.

**Per-edge radii at a tetrahedron's acute corners pass the B-rep checks and
fail `check_mesh`.** Sizing each round by its dihedral (radius from a constant
setback) left three degenerate corner patches: valid and `validate`-clean, but
the tessellation had boundary edges once its sub-micron slivers were dropped.
A single radius on every edge of the same body built watertight. Rounds also
recede an acute corner: 0.8 mm on a 30 deg wedge corner shortened the 80 mm
extent by about 4 mm, so state that in the spec instead of quoting the sharp
size.

**A large round meeting a small one at an acute corner can cross itself.**
The fillet builds, `BRepCheck_Analyzer` passes it, and the self-interference
check (`BRepAlgoAPI_Check(shape, True, True)`, what `inspect validate` runs)
fails it: 3 mm side rounds meeting a 0.6 mm round at a 34 deg corner left one
self-intersecting face per corner; 2 mm sides did not. Run the check on the
filleted part alone, before it is fused into anything that hides where the
fault came from.

The same holds for rounding by Minkowski sum (inset the solid by `r`, hull
spheres of radius `r` at its corners). Hulling spheres alone also leaves an
oblique face faceted: no sphere vertex lies exactly on a plane tilted to the
sphere's axis, so the face lands up to `r (1 - cos(pi / n))` low and in many
slivers. Add every face of the inset solid pushed out by exactly `r` along its
normal to the hull points; the flat faces are then exact and the spheres only
fill the rounds.

## Tangent chains and multi-arc outlines

OCC `chamfer`/`fillet` on edges that belong to a tangent chain (a domed face
meeting cap cylinders) or to a multi-arc "blob" outline behaves three ways
depending only on exact dimensions: silent failure, minutes of CPU churn per
attempt, or an **uncatchable SIGSEGV** that kills the whole build. Chamfering
edges NEXT TO already-bevelled arcs can also hard-crash. Retry ladders
multiply the churn and hide the degradation.

Bake the bevel into construction instead: put it in the extruded/lofted
SECTION profile, or build the body straight-walled to `z_top - w` and cap it
with `extrude(..., taper=45)` (or per-arc `Cone` caps when the draft prism
itself fails). Constructive bevels also survive later booleans, which
chamfered edges often do not.

The taper cap has its own limit: on an outline that carries ELLIPSE edges,
`extrude(face, w, taper=45)` raises `BRepFill_TrimSurfaceTool::IntersectWith:
incoherent intersection` (build123d 0.11), the failure the dense-spline
section lists for splines. On a flat plate extruded from lines, circles and
ellipses joined by 2D fillets, the plain 3D `fillet` of the straight-walled
extrusion's top edges was the operation that worked (36 edges, r 0.6, under
0.1 s), so on an analytic outline try the fillet first and keep the cap for the
outlines where it fails.

**A sliver edge kills that fillet.** The 0.6 mm round over a plate's whole
top edge failed ("Failed creating a fillet with radius of 0.6") on plans that
carried an edge of 0.0003–0.07 mm: one primitive's corner landing exactly on
another's edge, a 0.01 mm overlap added at a seam, a band corner 0.2 mm from a
neighbouring curve. An edge of 0.17 between two tangent arcs filleted fine.
Keep a corner at least 0.3 mm inside the shape that covers it, bury the unused
half of an ellipse in its neighbour instead of trimming it at the seam, and
assert a minimum outline edge length (0.15 mm) in source before the build. A
corner-by-corner 2D round that falls back to a smaller radius in a narrow V
notch ends in the same failure one step later; closing the plan with
`offset(+r)` then `offset(-r)` (Kind.ARC) rounds every concave corner at once,
but fills any slit narrower than `2r`.

## Sketch fillets go before the boolean

In 3D you fillet last; in a sketch you fillet **before** the boolean.
Reversed, `fillet(sk.vertices(), r)` walks into the subtracted circle's seam
vertex and raises `Vertex must connect exactly two edges` — verified on
build123d 0.11. When the corner radius is uniform, `RectangleRounded(w, h, r)`
skips the problem entirely.

A 2D fillet does not always succeed. `fillet_2d` fits a tangent arc between
the two edges at the vertex and raises `Unable to find a tangent arc` or
`Fillet algorithm failed for Vertex(...)` when one of them is shorter than the
arc's tangent length: a line meeting an ellipse just past another corner, a
short rectangle edge left between two subtracted circles (build123d 0.11).
`fillet(sk.vertices(), r)` then fails for the whole outline. Fillet corners one
at a time instead, re-finding each vertex by position after every fillet, and
halve the radius at a corner that refuses, down to a floor below which the
corner stays sharp and is logged; one bad corner then costs one corner. Skip
vertices whose edges are already tangent. Where both edges are long enough the
2D fillet is still the escape hatch when `fillet()` on a solid raises an OCCT
error. A 2D fillet also **shrinks a small acute shape**: a 4.0 mm triangle with
R 0.7 corners came out 2.4 mm wide. Draw a small rounded shape as the hull of
its corner circles (`make_hull`), so its overall size is the measured one.

## Dense periodic spline profiles

On faces bounded by one periodic `Spline` fit through hundreds of samples,
several kernel operations fail or corrupt (verified on build123d 0.10 /
OCP 7.9):

- `extrude(face, taper=...)` throws `BRepFill_TrimSurfaceTool: incoherent
  intersection`;
- kernel wire `offset` returns Null for some inward deltas;
- fusing two valid solids that share a coincident spline-bounded planar face
  can return an EMPTY result;
- a ruled loft to an inward offset is analyzer-invalid where the outer wire's
  corner radius is smaller than the offset.

- `fillet` on the one top edge of such a body fails its walk
  (`ChFiDS_WalkingFailure`, at any radius down to 0.3 mm) with 55-110 samples
  and runs for minutes without returning at 220; splitting the loop into G1
  spline segments fails the same way. A traced outline's edge round is never
  a fillet.

Compute offsets NUMERICALLY on the sample loop (normal offset, prune points
closer than |delta| to the source polyline, resample, smooth) and build
bevelled bodies as one multi-section ruled loft so no coincident-face fuse
exists. A round is the same loft: sections inset by `r(1 - cos t)` at height
`z0 + r sin t` for t in 15 deg steps, a sag of `r(1 - cos 7.5 deg)` = 0.9 %
of `r`, which no render or gate sees. Two conditions keep every section a
simple loop:

- **Sample spacing well under the least convex radius.** A smoothing
  spline sampled at uniform *parameter* gave 1.05-2.13 mm spacing round
  1.2 mm tine ends, and the 1.0 mm normal inset crossed itself there. Resample
  the loop by arc length at under half the least radius.
- **Interpolate every section at one set of parameters.** Left to itself
  each inset curve takes its own chord-length parameters, so a ruling joins
  point i of one section to a point beside point i of the next, and the band's
  slope no longer follows the inset. Pass the outline's own normalised chord lengths (closing
  point included: one more value than points, for a periodic spline) as
  `parameters=` to `Edge.make_spline` for every section.
- **Enforce the least radius after the last smoothing step.** A raster
  opening rounds every end to its disk, then the smoothing spline tightens
  the ends again (1.28 mm opening, 0.88 mm after the spline). Open and close
  the sampled polygon with buffers (`buffer(-r).buffer(r)`) last, and assert
  `least convex radius > inset + 0.2` from the points. The same Null-offset behaviour is why a spline-bounded solid is never
hollowed or inflated with `offset()` ([[feature-recipes#conformal-surface-decoration]]).

For a cosmetic underside inset, when a constant-distance offset is unnecessary,
scale the exact planar section about its own bounding-box centre before
extruding it. Restore its plane datum after scaling. Derive the scale from
the chosen width reveal and report the proportional reveal on the other axis;
this preserves the original spline topology but is not a uniform offset or
a mating-fit proof. Cosmetic shadow reveals are not `cadfits` clearances and
must not widen the fit table's assembly band.

## Chamfers on wavy outlines pass validity and fail BOP

A chamfer or V-groove on a wavy outline can pass `volume > 0` and
`BRepCheck_Analyzer` and still be BOP-faulty; gate it with `BRepAlgoAPI_Check`
([[kernel-validity#gate-tangency-prone-results-with-the-bop-check]]).

## A bed chamfer on a lofted belly

A 45° chamfer on the edges where a lofted or scaled-sphere body meets the bed
fails outright (`Failed creating a chamfer, try a smaller length value(s)`,
every segment of a lofted chain, every length), and the fallback of offsetting
the body's bed section inward and extruding it with a taper fails too:
`offset()` of that section returns a Null shape. Put the relief into the tools
that made the faces instead: where two bodies meet on the bed, cut each face
back by the relief at z = 0 and return it to its place over the first two
layers, with the same cutter grown and tapered. A cylinder becomes a cone; a
wedge of half-angle `a` grown by `d` keeps its angle with its apex `d / sin(a)`
further back, and `extrude(face, amount, taper=)` draws it. Keep the taper off
45 deg (0.3 mm over 0.4 mm is 37 deg). A plain step two layers tall is not the
same thing: its ceiling is a flat ledge that the overhang gate reads as needing
support.

## Bevel the pieces, then fuse

A chamfer round the outline of a fused union — a limb of bones and knobs
cut flat on one face — failed at every length: the outline has concave
corners where one piece meets the next, and the chamfer cannot close there.
Each piece's own outline is a single smooth curve that takes the full
chamfer. Chamfer every piece on its own and fuse the chamfered pieces; the
bevels meet in the union's concave corners by themselves.

The kernel can also refuse a chamfer on one side of a symmetric piece and
take it on the other. A loft centred on Y = 0 and cut on its −Y half refused
a chamfer at any length that the same loft cut on its +Y half took at full
size. When mirror pairs are built from symmetric pieces, build every one on
the side that works and `mirror` the result for the other side.
