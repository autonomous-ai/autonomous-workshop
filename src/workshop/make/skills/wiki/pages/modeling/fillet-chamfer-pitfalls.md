---
title: Fillet and chamfer pitfalls
tags: [fillet, chamfer, bevel, radius, sigsegv, spline, offset, taper]
aliases: [rounding, edge blend, retry ladder, BRep_API command not done, fillet failure, periodic spline, bed chamfer, elephant foot chamfer, bottom chamfer fails]
sources:
  - skills/cad/references/build123d-modeling.md (fillet, chamfer and periodic-spline sections; before the move)
  - skills/cad/references/repair-loop.md (fillet failure class; before the move)
  - skills/image-to-cad/references/build123d-operations.md (sketch fillet order; before the move)
  - "toolchain: build123d 0.10-0.11 on OCP 7.9"
  - "experience: chamfer and section-offset both failed on the bed edges of a lofted flexi chain"
  - "experience: a bevel round a flat-faced limb failed on the fused limb and on one mirrored side"
related: [construction-strategy, operation-families, kernel-validity, modeling-failure-modes, flexi-chain-joints]
updated: 2026-09-29
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

## Sketch fillets go before the boolean

In 3D you fillet last; in a sketch you fillet **before** the boolean.
Reversed, `fillet(sk.vertices(), r)` walks into the subtracted circle's seam
vertex and raises `Vertex must connect exactly two edges` — verified on
build123d 0.11. When the corner radius is uniform, `RectangleRounded(w, h, r)`
skips the problem entirely. A 2D fillet on the sketch always succeeds where an
equivalent 3D fillet on the extruded solid may fail, which makes it the
escape hatch when `fillet()` on a solid raises an OCCT error.

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

Compute offsets NUMERICALLY on the sample loop (normal offset, prune points
closer than |delta| to the source polyline, resample, smooth) and build
bevelled bodies as one multi-section ruled loft so no coincident-face fuse
exists. The same Null-offset behaviour is why a spline-bounded solid is never
hollowed or inflated with `offset()` ([[feature-recipes#conformal-surface-decoration]]).

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
