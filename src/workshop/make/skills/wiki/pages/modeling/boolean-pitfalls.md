---
title: Boolean pitfalls
tags: [boolean, cut, fuse, union, intersect, occ, near-tangent, coincident, tool, performance]
aliases: [subtract, boolean failure, multi-tool cut, coincident faces, tangent surfaces, near-coincident surfaces, relief cut, slow boolean, clipping tool, torus crown]
sources:
  - skills/cad/references/build123d-modeling.md (boolean sections; before the move)
  - skills/cad/references/repair-loop.md (large lofted surface section; before the move)
  - "toolchain: OCC booleans on near-coincident B-spline faces collapse to zero intersection (reproducible)"
  - "toolchain: fusing rotated copies of one loft returns a null shape (reproducible)"
  - "experience: a voxel hat base cut to follow a lamp shade's skin"
  - "experience: a footprint clip ending on a torus crown left an invalid common and a failed chamfer"
  - "experience: a multi-tool cut between dense lofts came back plausible in volume and wrong in shape"
  - "experience: face openings cut into a ribbed periodic-spline loft were valid only as one multi-tool cut"
  - "experience: a cutter flush with a revolve tangent and two cutters 2 deg apart each left unmeshable slivers"
related: [kernel-validity, construction-strategy, loft-pitfalls, feature-recipes, text-patterns-and-surface-detail, fuse-pitfalls, occt-boolean-options, shapely-cutters, brep-vs-source]
updated: 2026-10-12
---

# Boolean pitfalls

OCC booleans fail worst on inputs that nearly agree: coincident, tangent, or
near-copies of each other. Many of the failures below exit 0 and validate
clean. Unions of pieces that share faces, and fuses that come back empty,
are [[fuse-pitfalls]].

## `intersect` returns a list

**`a.intersect(b)` returns a `ShapeList`, not a shape.** Chaining
  `.intersect(...).intersect(...)` fails with `'ShapeList' object has no
  attribute 'intersect'`. Use the `&` operator (`a & b & c`), which returns a
  shape you can test with `solids()`. Three extruded prisms from the side,
  section and plan intersected this way give a faceted vehicle hull in
  milliseconds, and `cadprint.hollow` shells a planar hull in under 0.1 s.

## Overshoot the tool

Extend cutting tools past the faces they enter and exit; for through-cuts, go
roughly 1 mm beyond both faces. Coincident or coplanar tool/target faces are a
classic kernel failure. A recess tool must break the rim plane by ≥ 1 mm.
Overlap operands you mean to union by something the model can afford (roughly
1 mm for a through-cut, a whole station for a loft): touching operands return
two solids, and a 0.01 mm nudge leaves a 0.01 mm feature in the geometry.

A clipping tool that only bounds a curved shell overshoots it too. A footprint
extrusion bounding a toroidal shell in plan whose cap ends exactly at the
torus crown makes a tangential face contact: the common returns one solid of
positive volume and invalid topology, and a later, unrelated chamfer then
fails. Extend the non-design cap past the crown by the named tool margin (the
shell still defines the finished surface), and check validity after each
boolean rather than shrinking the chamfer.

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
  disjoint-ish — still list-based, never pairwise. Between dense B-spline
  lofts even a staged batch came back plausible in volume and wrong in shape:
  there, cut one tool at a time and check after each.

On a ribbed periodic-spline loft, the opposite failure shows up. Cutting
openings one at a time left solids that failed `BRepAlgoAPI_Check`, or wrong
solids that passed it. Fusing the tools first silently dropped volume. One
`Shape.cut(*tools)` call with disjoint tools gave a valid solid. Volume
differences of such B-spline solids are too noisy to debug with. Probe with
`is_inside` and the BOP check instead.

Timed comparison of one list boolean against pairwise ones for a pattern:
[[text-patterns-and-surface-detail]].

## Near-tangent and near-coincident surfaces fail quietly

Intersecting or subtracting nearly tangent surfaces (a huge shallow sphere
kissing a small revolve, a flat dome tool grazing a face) can succeed with
exit 0 and a validate-clean result while half a tool's material was simply not
removed — or a stray disjoint sliver is left floating inside the part. Only
visual review catches it. Build shallow domes as a single revolved profile
(`RadiusArc` in the section) instead of near-tangent boolean stacks; it is
also crisper.

**A cutting plane on a fillet's tangent seam.** An edge round's fillet meets
the wall along a tangent seam at a fixed height. A layer cut whose floor
lands exactly on that height breaks the result. In one case, a colour inlay
FACE_D deep ran to the outline, and FACE_D equalled the teardrop edge's
height (chamfer leg plus R·tan(half the arc), 0.6 for both). `validate` then
failed: the body came back with invalid topology and the field
self-intersecting, its vertices 1e-4 past the floor. Keep layer planes off
every edge treatment's seam heights. When a stack fixes both, either trim
the field a few hundredths inside the wall, or let its sketch overshoot the
outline so that no tool face lies on the wall.

**Near-coincident surfaces collapse the boolean.** Two solids within
hundredths of a millimetre of each other across many B-spline faces (a cap's
ring lying on the loft it closes, a rebuilt part against its reference) can
intersect to nothing with exit 0: a box cutting the solid returns nothing, a
`split` keeps the whole. The closer the surfaces, the worse it behaves, and no
fuzzy value reliably rescues it
([[occt-boolean-options#walk-the-fuzzy-value-up-from-exact]]). Keep surfaces
clearly apart or clearly crossing. Measuring a comparison the boolean cannot
compute: [[brep-vs-source#near-coincident-solids-collapse-the-comparison]].

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

**Cutters that graze a tangent or each other.** A cutter face flush with a
revolve's vertical tangent leaves a sliver face of about 0.01 mm^2. The sliver
does not mesh, and `check_mesh` then crashes with `'NoneType' object has no
attribute 'NbNodes'`. Move the cutter clear of the tangent. Two cutter faces
that meet about 2 deg apart leave an open-edge sliver. At 6 deg or more apart
they cut clean.

## A boss level with a rod's crest poisons later features

A boss, bead or plate fused to a round rod with its top at exactly the rod's
crest height (an eye at the end of a stick, a bit plate as thick as the stick)
leaves the two surfaces tangent along a line. The fuse succeeds, but a hole
cut there gets a rim split across both surfaces, and the rim fillet then fails
with `BRep_API: command not done`. Make the joined form stand clearly proud of
the crest (a bead 1 mm higher) or sit clearly below it (a plate 0.8 of the
rod's diameter, whose top plane cuts the rod in two clean lines); never equal.

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

## An underside that follows a supplied shell

To give an accessory a base that follows a host's curved skin, cutting the
block with a thin offset of the shell often fails to split it: seams at the
shell's rim leave a path around the cut, and the block comes back whole. Cut
the shell plus each upward-facing skin face extruded straight down, then keep
the highest piece. Bound the front with the rim plane, choosing the front-most
planar face with the right normal (not the largest, which can be an internal
face at the rear). Subtract neighbouring liner solids in a separate cut:
merging them into the same cutter broke the split. Where the curved skin rises
through a stepped profile, the step leaves a knife edge, so drop the step on
that side.

## Cuts that refill, sever, or miss

- A hole cut before a union is silently refilled ([[construction-strategy#boolean-order]]).
- A `Compound` of overlapping solids passed as one cutting tool can skip the
  cut with no error. Fuse the tools first, or pass a list of disjoint tools.
- A tube that crosses a loft's planar end-cap edge is dropped from a fuse or a
  cut with no error. Move the tube off the cap edge, or extend the loft past it.
- A loft section lying exactly in a cut plane returns an empty boolean, and so
  does a keep-solid lofted from rings offset off the same skin. Shift the
  plane off the section.
- `Box(x, y, z, align=None)` puts its minimum corner at the origin, not its
  centre. A cutter meant to be centred then misses and cuts nothing. Assert
  that every cut removed material.
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
Prism cutters from `shapely` polygons (faceted arcs, zero-area shards, which
way the prism runs): [[shapely-cutters]].
