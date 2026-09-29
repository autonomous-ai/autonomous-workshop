---
title: Boolean pitfalls
tags: [boolean, cut, fuse, union, intersect, occ, near-tangent, coincident, tool, performance]
aliases: [subtract, boolean failure, multi-tool cut, coincident faces, tangent surfaces, symmetric difference, relief cut, slow boolean, polygon arc, shapely buffer]
sources:
  - skills/cad/references/build123d-modeling.md (boolean sections; before the move)
  - skills/cad/references/repair-loop.md (large lofted surface section; before the move)
  - "toolchain: OCC booleans on near-coincident B-spline faces collapse to zero intersection (reproducible)"
  - "toolchain: fusing rotated copies of one loft returns a null shape (reproducible)"
  - "experience: polygon-approximated arc prisms against lofted segments ran minutes; true cylinders seconds"
related: [kernel-validity, construction-strategy, loft-pitfalls, feature-recipes, text-patterns-and-surface-detail]
updated: 2026-09-28
---

# Boolean pitfalls

OCC booleans fail worst on inputs that nearly agree: coincident, tangent, or
near-copies of each other. Many of the failures below exit 0 and validate
clean.

## Overshoot the tool

Extend cutting tools past the faces they enter and exit; for through-cuts, go
roughly 1 mm beyond both faces. Coincident or coplanar tool/target faces are a
classic kernel failure. A recess tool must break the rim plane by ≥ 1 mm.
Overlap operands you mean to union by something the model can afford (roughly
1 mm for a through-cut, a whole station for a loft): touching operands return
two solids, and a 0.01 mm nudge leaves a 0.01 mm feature in the geometry.

## Multi-tool booleans

Never accumulate boolean tools pairwise — `body - a - b - c` re-runs the whole
intersection network per step and decays O(n²). Pass every tool in one list
operand: `body - [a, b, c, ...]`.

Two caveats, both measured:

- **Tools that overlap each other deep below the surface are pathological.**
  ~200 shallow spherical dimples cut with full spheres (radii ~15 mm for
  0.02 mm-deep stamps) ran >40 CPU-minutes with zero output; pre-clipping each
  stamp to a small disjoint "lens cap" (`Sphere & Cylinder` prototype,
  translated copies) cut the same field in 0.69 s. Keep tools small and
  mutually disjoint.
- **A single multi-tool cut whose tools overlap each other can emit wrong
  results.** A bore cylinder crossing a stack of thin ring cutters returned
  5 solids: the body, the bore's uncut PLUG kept as a detached solid, and
  knife-edge slivers. Every tool was individually valid; splitting the same
  tools into two staged subtracts (functional cuts, then finishing cuts)
  yielded one clean solid. Batch tool FAMILIES so each batch is internally
  disjoint-ish — still list-based, never pairwise.

Timed comparison of one list boolean against pairwise ones for a pattern:
[[text-patterns-and-surface-detail]].

## Near-tangent booleans silently drop material

Intersecting or subtracting nearly tangent surfaces (a huge shallow sphere
kissing a small revolve, a flat dome tool grazing a face) can succeed with
exit 0 and a validate-clean result while half a tool's material was simply not
removed — or a stray disjoint sliver is left floating inside the part. Only
visual review catches it. Build shallow domes as a single revolved profile
(`RadiusArc` in the section) instead of near-tangent boolean stacks; it is
also crisper.

## Near-coincident surfaces collapse the boolean

When two solids lie within hundredths of a millimetre of each other across
many B-spline faces — a rebuilt part compared with its reference — the OCC
boolean between them collapses, and a symmetric-difference measurement reports
the collapse **as a number**: `symmetric diff 200%` with `missing` and `extra`
each equal to the full volume means zero intersection, not a 200 % error. The
closer the rebuild gets, the worse the boolean behaves. Fuzzy values from 1e-7
to 1e-2 make it worse, not better (intersection went 1.4 mm³ → 0.0). A 2D
per-cut boolean fails the same way, returning 0.0 even where both sections are
the same annulus with areas agreeing to 0.001 mm².

Tell it apart from a real miss: check that both solids are valid and
FORWARD-oriented, that each intersects itself and a box correctly, and that
their section areas agree. If all that holds, the geometry is right and the
boolean is not.

Then measure the symmetric difference by point classification instead: sample
the union bounding box and ask each solid whether it contains the point. Build
**one** `BRepClass3d_SolidClassifier` per solid and reuse it — constructing one
per point runs at ~210 points/s and is unusable. Report the sampling standard
error alongside the figure, and record that the boolean comparison ran and
failed rather than quietly substituting the sampled number.

**Near-tangent skins cost minutes before they cost correctness.** Cutting a
wall-shrunk void loft from its outer loft took 1.4 s; fusing that hollow body
with a second hollow loft whose skin ran 1-8 mm inside the first took 150 s,
and cutting a fused void from a fused outer took the same. Nothing was wrong
with the result, so no gate notices. Two fixes that each removed it:

- do not fuse what the part does not need: clip each loft to the region the
  part keeps before any union (the upper half of a split figure needs only
  the body loft above the split);
- make an internal plate by leaving it behind, not by adding it: cut the void
  only above the plate's top (`void & above(z_plate)`), rather than unioning
  `slab & void` back on to the shell along the void's own skin.

## Swept reliefs: convex prisms, not rotated lofts

Building a clearance relief by rotating a lofted body about its joint and
unioning the copies fails twice over, and neither failure looks like one:

- `swept = swept.fuse(shape.rotate(axis, a))` over 8 angles returned a **null
  shape** on a lofted lens. The sweep silently became empty and cut nothing.
- Passing the copies as a tool list instead (`cut(*tools)`) avoids the null,
  but cutting a lofted body with nine near-copies of another lofted body
  **shatters the target**: 13 solids, one with *negative* volume — an inverted
  solid every later boolean inherits.

Rotated copies of one loft are near-tangent to each other and to the target
across dozens of B-spline faces, OCC's weakest input. Build the relief as a
**convex hull prism**, one per view, and intersect two views: take the
neighbour's silhouette points, rotate the 2D points about the joint at a few
sampled angles, convex-hull them, extrude. Planar faces, boolean-stable,
conservative in the safe direction.

Intersect the views — do not use one alone. A single side-view hull extruded
across the full width turned a 57 mm lens into a 57 mm **slab**: at ±20° it
removed 99.6 % of the neighbour (12,000 mm³ down to 43). Pitch ∩ yaw is the
smallest solid consistent with both silhouettes and left 92–100 % at ±10°.
Measure retained volume against swing before declaring an angle — the knee is
sharp and the honest angle is the one the bodies actually allow.

## Booleans against a large lofted surface

A subtract against a single large B-spline surface costs a full-surface
classification PER TOOL and grows superlinearly in tool count — measured on
one ~4,900-control-point skin: 1 tool 24 s, 4 tools 70 s, 41 tools did not
finish in 15 minutes, and a 44-tool build ran over seven hours without
completing. Batching into one list operand does NOT help; the cost is per
tool, not per accumulation.

Confirm rather than guess: the process stays at ~100 % CPU with the progress
file frozen on its first phase, and a stack sample shows
`Extrema_ExtPS::Perform` with `BSplSLib_Cache::BuildCache` rebuilding on
nearly every evaluation.

Fix by not cutting: shallow cosmetic recesses do not need to be booleans at
all. At 19 m rendered to 1920 px, 1 px is ~10 mm, so a 4 mm groove is
sub-pixel and reads only because the edge overlay draws feature edges. Keep
booleans for openings that change the silhouette, and build the rest
additively.

## Arcs drawn as polygons make cutters slow

A cutter extruded from a polygon that approximates arcs (a `shapely` buffer,
a circle as 64 segments) cuts a B-spline body in minutes where the same cut
with true circles takes seconds: every facet is a planar face the kernel
intersects with the spline. Eight lofted segments trimmed by 64-sided arc
prisms had not finished after two minutes; with `Cylinder` arcs and
straight-sided wedges the same eight took two seconds. Build every arc as a
circle, and keep polygons for straight-sided regions; when one must be grown,
mitre it (`buffer(d, join_style=2)`) so it keeps its vertex count instead of
gaining an arc at each corner.

## A fuse can come back empty: assert every step

Fusing several solids that all start from one point (five leaves rooted on a
knob's centre) returned an empty compound on the fifth fuse: no exception, a
valid shape, zero volume, and every later cut on the part ran on nothing. The
leaves' root caps were near-coincident. Start each one a little way out along
its own direction (still inside the knob), and after every fuse assert one solid
and a volume larger than before:

```python
grown = fan + leaf
assert len(grown.solids()) == 1 and grown.volume > fan.volume, "fuse came back empty"
```

A model assembled from many roles wants the same guard once, where the roles
are labelled: every role holds material, or the build stops.

## Cuts that refill, sever, or miss

- A hole cut before a union is silently refilled ([[construction-strategy#boolean-order]]).
- A full-width cylinder cut **severs** the body into pieces; clip the tool to
  one side ([[feature-recipes#subtractive-features]]).
- A decoration tool that misses the skin intersects to `None`, and the failure
  surfaces far downstream ([[feature-recipes#conformal-surface-decoration]]).
- A feature whose pitch equals its own size leaves neighbours touching at a
  point: valid solid, non-manifold mesh. Give the gap a name
  (`POCKET = PITCH - 0.1`) — see `skills/cad/references/repair-loop.md`,
  "Mesh defects the generator produced".
- Filling a cavity with its own complement (`ends = box - host`, then
  `host + ends`) lays every face of the fill on a face of the host. A mesh
  kernel keeps both sheets, and sewing the result fails on edges shared by four
  triangles. Union the whole box instead (`(host + box)`, then trim) when the
  box lies in the host but for the cavity, and use `box - host` only to assert
  what the fill adds: how many pieces, how big, how far from every inlay.

Kernel options behind these (fuzzy value, glue, argument analyzer, history): [[occt-boolean-options]].
