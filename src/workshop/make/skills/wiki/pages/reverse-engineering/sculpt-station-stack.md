---
title: Re-authoring a sculpted mesh as a station stack
tags: [reverse-engineering, sculpt, organic, loft, station, section, ruled, thrusections, fidelity, iou]
aliases: [replicate a sculpt, rebuild an organic stl, horizontal sections, z-level loft, level loft, figurine rebuild, print-in-place figure]
sources:
  - "experience: a 17-body multi-colour print-in-place figure re-authored from its STL shells; hand-fitted section families reached IoU 0.60-0.91 per body, a measured station stack 0.989-0.998"
  - "toolchain: build123d 0.10 on OCP 7.9 (BRepOffsetAPI_ThruSections, BRepAlgoAPI, BRepGProp, BRepAlgoAPI_Section)"
  - shapely and manifold3d documentation (even-odd polygon fill, mesh slicing)
  - "experience: ruled then smooth lofts through 0.1 mm levels shaded as stripes and ripple; three rounds of split/bridge fixes each added seams, and the user chose a carried mesh"
related: [loft-organic-bodies, loft-pitfalls, mesh-to-step-conversion, authoring-from-a-reference, mesh-measurement, kit-assembly-clash-diagnosis]
updated: 2026-09-25
---

# Re-authoring a sculpted mesh as a station stack

When a supplied STL is a sculpt (skin texture, toes, ruffles, eyes set into a
face) and the rebuild has to match it, a hand-chosen section family cannot get
there: superellipse beads, lofted limbs and ellipsoid eyes top out around IoU
0.6-0.9 per body however well each row is fitted. What does get there is the
station table taken to its limit: one measured outline per level, lofted.

## Slice along the print axis

A part that prints flat changes continuously from the bed up, so cut it into
horizontal levels (0.1 mm apart, plus one level just under and one just over
every flat floor or roof, so a window keeps a sharp top). A floor that is only
nearly flat moves the outline millimetres between two such levels and the
straight band between them stands proud of the surface, touching the next
body; halve every gap where the section moves more than about 0.1 mm on
average (area changed over perimeter). Each level is the
shell's section as **nested rings**: depth 0 is skin, depth 1 a hole through it
(a joint window, a nostril, a socket), depth 2 an island standing in the hole
(a post, a cup). Loft each ring up the stack as its own lobe and compose by
depth: skin, minus holes, plus islands.

A ring's depth is **how many other rings' discs contain it**, not whether it
sits inside some hole: a bore through an island is depth 3, and calling it
depth 1 composes it with the holes, after which fusing the island back fills
the bore in again. Compose strictly by depth - fuse the even ones, cut the odd
ones, in order.

- Measure the shell **before** inlays are cut out of it, and cut the inlays in
  the source in the slicer's order (pupil over white, white over its host).
- Measure both bodies of a mirror pair; a sculpt is rarely exactly symmetric.
- Mesh slices are even-odd: holes come back as separate rings, so build each
  level by symmetric difference, never by union.

## Make the levels match, or the loft folds

**Wind every ring the same way first.** Chaining a section walks it from an
arbitrary segment in an arbitrary direction, so two consecutive levels can come
back wound oppositely; the ruled band between them is then a twist, and the
loft is self-intersecting or refused outright. Normalising the winding also
removes most apparent folds - a twisted band fails the fold test for a reason
that is not a fold.

A ruled loft joins equal **parameters** of consecutive curves, not equal point
indices. With the default chord-length spline parameters two levels of
different shape drift apart and the band twists; give every spline
`parameters=[0, 1, ..., n]` so point i meets point i. Then:

- Sample each outline by arc length, and start each level at the point
  nearest where the level below started. A fresh start per level jumps (the
  +Y crossing lands in a notch on one level and beside it on the next).
- Check every band before lofting: its section at height t is the spline
  through the blend `(1-t)*a + t*b`, so the band folds exactly when some blend
  is not a simple ring. Sample t finely (41 values); a fold can live in 2 % of
  the band.
- A band can also **skew** without folding: where a notch opens, arc-length
  points slide round the outline and the band leans off the surface while
  every blend stays simple. Compare the band's mid-height section with the
  mesh's at that height; a mean gap over about 0.05 mm is a skew.
- Choose the point count per lobe by the mean gap between spline and ring, not
  the worst point (a spline rounds a joint's sharp corner whatever the count),
  but also refuse any spline standing more than about 0.02 mm **outside** the
  ring: across the mouth of a narrow notch it fills the notch, and the notch is
  where the neighbouring body's joint bar runs.
- Where a band folds or skews (a notch opening, a ring closing), end the lobe, start the
  next on the level above, and bridge them with a **prism** of the two rings'
  common part: straight walls cannot fold.
- Switch off `ThruSections.CheckCompatibility`: it re-seats start points and a
  loft through 100+ levels then fails outright.

## Close every end the levels leave open

The level grid stops one step short of wherever a lobe ends, and what to do
there depends on what is beyond it. Test it by the **fraction of the ring's own
area that is material at the next level**, not by one representative point: a
joint socket's mouth is partly open, and a point that lands in the open part
reads the whole socket as breaking through.

| lobe | beyond its end | what it needs |
|---|---|---|
| skin or island | material | a short prism that crosses into it - two lofts that only touch on a plane do not fuse |
| skin or island | air | a tip: scale the last ring to a few per cent and place it where the ring's shrinking rate says the surface closes. A flat cap leaves a visible disc on every dome and toe |
| hole | material | nothing: that is its roof |
| hole | air | the body ended and the hole opens through the surface. A film of skin left over it seals the void, and the sealed void comes back as an **inverted solid beside the body** |

Carry that hole on as an extra **level of the hole itself**, grown, not as a
second prism laid over its end: two overlapping cuts down one socket wall are
near tangent, and the second one fails past `ShapeFix_Shape`.

Two more things the grid does to a body if you let it:

- **A ring that splits and merges in the same step** is one level tall and
  cannot be lofted. Dropping it leaves a level of nothing in the middle of the
  body, and the halves fuse into two solids. Keep it as a prism half a level
  deep.
- **Drop a lobe by the volume of the body it is connected to, not its own.** A
  speck caught between two levels goes; a thin bottom cap that the chain broke
  off the body above it is not a speck, and dropping it costs the part its base.

## Keep the kernel's booleans solvable

Lofts that share a face or an edge break `BRepAlgoAPI_Fuse`/`Cut`: the result
is empty, a fraction of the body, or the tool itself.

- Where one lobe carries into another, keep the carried level 0.03 mm
  **inside** the other ring; a prism bridge reaches 0.02 mm past both lobes'
  caps and sits 0.03 mm inside them. Surfaces then cross instead of lying on
  each other.
- A hole that opens into a notch leaves a wedge of skin between the closed and
  the open level; carry the hole one level on, grown 0.03 mm.
- Drop lobes under about 0.5 mm³ (a bump's tip caught between two levels);
  they change nothing measurable and break booleans.
- Do not fuse an analytic primitive onto a loft that already follows it (a
  fitted knob sphere onto the lofted knob): two near-coincident surfaces fail
  the fuse. Keep the primitive as a datum.
- **Fusing every lobe in one call** stops a lobe vanishing into the result or
  staying a separate solid beside it, and the kernel never fuses two solids
  that already sit in one argument, so a later bridge cannot join them. But on
  a body of a few hundred B-spline faces that one call can hand back a single
  solid of exactly the right volume that `BRepAlgoAPI_Check` reports as
  **self-intersecting** - and `BRepCheck_Analyzer`, which is what a build
  normally asks, calls it valid. The same lobes fused one at a time give the
  same volume and no self-intersection. Whichever way you go, check for both
  failures: accumulate and assert the running volume never drops (the lobe that
  vanished) and that the body ends as one solid (the lobe that stayed beside
  it), and run `BRepAlgoAPI_Check` before believing the result.
- **Cut one tool at a time.** A cut by several tools at once came back
  plausible in volume and wrong in shape.
- **A cut that did nothing looks exactly like a cut that worked.** Where an
  inlay's surface nearly coincides with its host's, the kernel can fail to
  classify the two and hand the host straight back: valid, one solid, the right
  number of faces, and the inlay still inside it. `BRepAlgoAPI_Common` on the
  same pair reports an empty intersection and reports it as **done**. Two of
  nine inlay cuts on one figure failed this way, and nothing caught it until
  `interfere` found the inlay sitting in its host at the end of the run - the
  per-body comparison cannot, because it grades the stack BEFORE its inlays
  come out. Measure the overlap first, walking the fuzzy ladder from the
  smallest rung until one run finds it, then hold the cut to removing that
  much. 1e-5 mm found 80 mm3 where exact found nothing; the loosest rungs go
  back to reporting nothing, so stop at the first hit rather than the last.
  A zero intersection is only trustworthy after the ladder - and then it is
  genuinely useful, because an earlier cut in the order may have taken
  everything a later one would (a pupil inside an eye white meets nothing once
  the white is out of the head).
- `BRepCheck_Analyzer` is not the validity a STEP is judged on.
  `inspect validate` keys on `BOPAlgo_SelfIntersect` through
  `BRepAlgoAPI_Check`, which is a far stronger test and a far slower one -
  minutes per body, hours for a figure, and long enough that it is worth
  running per body during the build rather than discovering it at the gate.
  When it does fire it can name the whole solid and no face pair, which
  localises nothing.
- Check every result: valid, and a volume a fuse or cut could produce. A cut
  between lofts can come back with every face, edge and vertex sound and the
  solid flagged invalid; `ShapeFix_Shape` clears it without moving geometry.
- **A prism's ring is resampled by arc length like a level.** A buffer leaves
  points wherever it put them, including near-coincident ones, and a periodic
  spline interpolated through those with uniform parameters oscillates between
  them, crosses itself, and the prism comes back invalid.
- Fuzzy booleans rarely rescue these cases; try them only after the exact
  operation fails its check. When one is needed, walk the fuzz up from about
  1e-5 mm and take the first value that comes out valid, and accept it only if
  it lands on the volume the exact run reached - a looser tolerance that
  reshapes the body is not a repair. A cut between two dense lofts that
  `ShapeFix_Shape` cannot clear is usually cleared by the smallest rung.

## Measure it honestly

- `Solid.volume` (default `BRepGProp` precision) under-reads multi-span ruled
  B-spline lofts by up to 10 %; pass an explicit precision (1e-5) before
  trusting a volume.
- `BRepAlgoAPI_Section` against these surfaces comes back empty at about one
  height in four. Compare by slicing the kernel's own triangulation instead:
  mesh once, cut each triangle, chain segments by shared end points (a shared
  edge is meshed once), fill even-odd, and integrate intersection and union
  areas over heights between the table's levels.
- Report per-body IoU against the shell less its inlays, and the material
  missing and extra; volume agreement alone hides a moved feature.
- Count shells per solid. A hole that failed to break through leaves a sealed
  cavity, and volume, bbox and every section IoU still agree with the
  reference - the section cuts the void either way.
- **Measure a print-in-place clearance in 3-D, not in a slice.** A slice reads
  the least distance *in that plane*, and two surfaces approaching on a slant
  have their closest pair at two different heights, so the slice reads wide -
  enough to move a joint a whole fit class. Sample one surface densely and take
  the exact distance to the nearest triangles of the other
  ([[print-in-place-mechanisms#verify-in-cad-the-minimum-distance-not-no-interference]]).

## Where a level loft stops: seams and noise

A stack through levels 0.1 mm apart looks right by IoU (0.99+) and wrong to
the eye, and the two ways of lofting it fail in opposite directions:

- **Ruled** makes one face per band: an edge at every level, which a viewer
  shades as horizontal stripes.
- **Smooth (interpolating)** passes exactly through every measured point, and
  the points carry the mesh's facets. Measured as each point's distance from
  the mean of its neighbours above and below, the levels wobble 0.05-0.07 mm
  (p95) and up to 0.6 mm, where a real surface at that pitch wobbles about
  0.001 mm. The smooth skin turns that into ripple, overshoots at ledges, and
  folds.
- Splitting lobes where it folds, then bridging, carrying and pulling poles to
  hide the splits, adds a boolean seam at every split. Each fix leaves more
  horizontal marks than the one before: stop patching the surface.

So, before choosing:

1. **Measure the noise** in the levels (the wobble above) before building any
   smooth surface. A Gaussian along each point's column (sigma about 4
   levels) brings it to about 0.01 mm; smooth the data, then fit an
   approximating surface (`GeomAPI_PointsToBSplineSurface`), never interpolate
   the raw levels.
2. **Judge with a measure of the complaint.** IoU and volume cannot see
   stripes or ripple; count horizontal skin edges and measure ripple along Z,
   and look at a shaded render of one body before building all of them.
3. **Pilot on one body with the stop rule set first.** If the pilot misses it,
   report and stop; do not layer another fix.
4. If the user needs the result **guaranteed identical** to the mesh, no
   stack gives that: carry the mesh
   ([[mesh-to-step-conversion#carrying-a-mesh-as-the-deliverable]]).

## What it costs

The tables are data (a few MB of rows), each body builds in seconds, and a
body carries a few hundred B-spline faces. Pairwise booleans between such
bodies take minutes each, so `interfere` on a whole figure takes a long time:
search poses and locate clashes on the meshes first
([[kit-assembly-clash-diagnosis#search-the-pose-off-cad-build-cad-once]]) and
run the gate once.
