---
title: Loft pitfalls
tags: [loft, section, station, pchip, ruled, spline, smooth-max, blend, overshoot]
aliases: [multi-section loft, loft knot vector, huge step file, loft parameters, lofted surface, crumpled surface, loft failure, make_loft, surface ripple, loft to a point, loft vertex, pucker, loft end cap, leaf tip]
sources:
  - skills/cad/references/build123d-modeling.md (loft and blending sections; before the move)
  - skills/cad/references/repair-loop.md (loft failure diagnosis; before the move)
  - skills/image-to-cad/references/build123d-operations.md (loft API facts; before the move)
  - "toolchain: build123d 0.10-0.11 on OCP 7.9"
  - "experience: a head lofted to a vertex puckered its snout; leaves with a fused tip cap broke every later half-cut"
  - "experience: a bent witch-hat tip lofted from a horizontal base"
  - "experience: validate never finished on an 18-lobe loft from periodic-spline sections; per-lobe edges made it finish in 88 s"
related: [loft-organic-bodies, operation-families, frames-and-rotations, modeling-failure-modes, boolean-pitfalls]
updated: 2026-10-12
---

# Loft pitfalls

Every failure on this page produces a valid, watertight solid or a message
that names neither the station nor the cause. Only a render, a bracketing
experiment or an assert finds them.

## Sections match by index

A loft interpolates its sections point index by point index. If you sample
each station at fractions of THAT station's own width, a feature — a crest, a
silhouette edge — sits at a different index at every station, and the surface
twists between them to reconcile them. The result is valid, watertight,
bilaterally symmetric, passes `inspect validate`, and renders as **crumpled
foil** over every square metre. Nothing reports it.

Sample on **rails**: compute the lateral position of each feature line per
station and allocate a fixed number of points to each rail-to-rail band, so
index *i* means the same feature everywhere. Cluster samples toward the rails
— that is where curvature is worst, so even spacing inside a band leaves the
sharpest part of the curve least resolved.

Full elliptical sections can change their parameter seam when their major
and minor axes exchange. The outline remains the same ellipse, but the loft
joins different quarter-turns, producing a twisted panel or a self-intersection.
Define native conic half-arcs with fixed local angular endpoints to keep the
seams aligned, including a terminal section that becomes circular. When rails
and seams are already matched, disable ThruSections `CheckCompatibility` so
automatic matching cannot undo them. Native conics also avoid the larger knot
systems of sampled periodic splines when the intended section really is an
ellipse. Validate both the raw loft and the complete fused body with BOP checks;
ordinary `is_valid` alone does not establish that the junctions are sound.

A ruled band has the same trap with no loft in sight:
`Face.make_surface_from_curves(wire1, wire2)` pairs edges by index and checks
neither edge count nor direction. A boundary wire and its mirror run opposite
ways and give unorientable band faces inside a solid of exactly the right
volume; build ruled bands edge by edge
([[freeform-surfaces-in-build123d#ruled-surfaces-make_surface_from_curves]]).

## Sections need one parametrisation, or the knots multiply

`Spline(*pts, periodic=True)` parametrises each section by its own chord
lengths, so N sections carry N different knot vectors, and the loft makes them
compatible by merging every knot into every section. The surface is fine; the
file is not: 28 sections of 180 points gave one lofted face a 15 MB STEP and a
4.6 s build. Passing the same list to every section,
`Edge.make_spline(pts, periodic=True, parameters=np.linspace(0, 1, len(pts) + 1))`,
gave 0.58 MB in 2.1 s with the surface unchanged to 0.0004 mm. Sections
sampled on one set of rails (above) can share one parameter list; a lofted
part whose STEP runs to megabytes for a handful of faces has this defect.

The merged knots cost more than file size. Every later operation pays for
them: booleans, the self-intersection check (`BRepAlgoAPI_Check`) and each
gate's tessellation. A periodic shell lofted from a couple of dozen rings of
about fifty points, each ring parametrised on its own, carried a thousand
poles round its circumference. `gen` ran four times slower, and `inspect
validate` was still running after two hours. Given one shared parameter list,
the same rings needed about a tenth of those poles, and validation finished
in minutes.

## Control curves that ruin the surface

- **`smoothstep` between control points makes a staircase.**
  `lerp(v0, v1, smoothstep(x0, x1, x))` has zero derivative at BOTH ends of
  every interval, so the curve is flat at each control point and steep between
  them. Lofting through such curves puts a crease at every knot. Use a
  monotone cubic (PCHIP) instead.
- **Measurement noise becomes surface ripple.** Station data traced off a scan
  carries ~a pixel of noise; a monotone interpolant reproduces it exactly and
  the loft turns it into visible waves. Smooth the control curve before
  lofting.

## One periodic spline per section makes one huge face

A lobed section drawn as one periodic spline lofts into a single B-spline face
around the whole body. `inspect validate`'s self-intersection check did not
finish on it in over 15 minutes, and it hung a `verify_project` batch for
hours. Draw each section as one spline edge per lobe, crease to crease. The
loft then has one face per lobe, and validate on the same body took under two
minutes.

## Smooth lofts overshoot; ruled lofts do not

A smooth (`ruled=False`) loft through control curves that collapse quickly at
the ends — a nose or a tail — can overshoot catastrophically: the C2
interpolation measured **z = 314 mm on an 80 mm-tall body**, with
`is_valid == True` and no warning. Use `ruled=True` with stations dense enough
(~2 mm pitch) that the faceting is invisible; the bounding box then matches
the control curves exactly.

A smooth `loft()` can also fail with `BRep_API: command not done` even though
every section is individually valid and they share one edge count. Try
`loft(..., ruled=True)`; with densely spaced sections the result is visually
equivalent.

A smooth alternative worth probing is `BRepOffsetAPI_ThruSections` with maximum
degree 3, C1 continuity and uniform (`Approx_IsoParametric`) section
parameterisation, using already matched rails and compatibility checking
disabled. This can bound a single continuous skin where a default higher-degree
loft overshoots and ruled sections leave visible joints. It is a candidate,
not a guarantee: assert the raw skin's envelope and positive adaptive volume,
then check its trimmed and fused result for one-solid continuity and BOP
validity before exporting.

The overshoot also runs **along** the loft. Sections at uneven spacing whose
outline turns vertical between two close stations — a sleeve's hanging edge
read off a front view — push the interpolated skin past the end section and
fold it back on itself: a 253 mm figure lofted to X = -119 with its first
section at -96. `is_valid` stays `True`; every boolean after it returns an
invalid shape or several bodies. Resample the station table to even spacing
with a monotone interpolant (`scipy.interpolate.PchipInterpolator`, which
never leaves the range between two readings) and loft ruled through ~4 mm
stations.

## loft() takes faces, make_loft() takes wires

`loft()` takes Faces/Sketches; `Solid.make_loft()` takes Wires. Passing wires
to `loft()` fails with `More than one wire is required`, which names the wrong
problem.

## Diagnosing "Failed to create valid loft"

"Failed to create valid loft" / "Recovery failed" names neither the station
nor the cause. Two checks, in this order:

1. **Loft increasing PREFIXES** (`faces[:5]`, `[:10]`, `[:20]`, …) to bracket
   where it breaks, and watch the reported volume as well as the exception — a
   loft that "succeeds" with an absurd volume is already failing.
2. **Loft every ADJACENT PAIR.** If every pair succeeds but the full set
   fails, the sections are individually fine and the problem is global —
   almost always that sections disagree on POINT COUNT. Guarantee a fixed
   sample count per section.

Silent causes worth ruling out before either:

- **A section that is genuinely disconnected** (two closed regions — a station
  cutting two separate nacelles, or crossing an open slot) produces a `Face`
  that raises nothing and reports a plausible area; only `Face.is_valid` is
  False. The loft then fails dozens of stations away. End the loft at the last
  connected station, or bridge the gap in the section and cut it back
  afterwards. (`Face.is_valid` is a property, not a method:
  [[kernel-validity#faceis_valid-is-a-property]].)
- **Samples dropped where a component does not exist** make counts vary
  station to station. Carry a value rather than dropping the sample.
- **A section wire that self-intersects.** `make_face` accepts a
  self-intersecting periodic spline and reports a valid, positive-area face,
  so each station looks fine in isolation; the loft then fails on whichever
  adjacent pair is worst. Bisect by lofting adjacent pairs to find the station.
  Common cause: two points straddling a crease offset along the corner's
  TANGENT lines rather than placed on the curve, so the outline doubles back.
- **A degenerate first or last station.** If a station must be a point, use a
  very small finite section instead.

## Blending volumes: a lobe that closes inside the body is a cliff

When sections are built by smooth-max/min over component volumes, any closed
convex profile meets its own silhouette on a **vertical tangent**. Where such
a lobe closes *inside* the body — against a neighbouring shelf or lobe — you
get a near-vertical wall no blend width and no sample density can round off.
Extra sampling does not help: the corner is in the function, not the
sampling.

- Widen the lobe until it OVERLAPS its neighbour and cut the real feature back
  in afterwards, rather than letting it close between them.
- Give a feature that needs its own width its own lobe. One half-width cannot
  serve both a wide fuselage and a narrow canopy.
- Prefer a **compact-support polynomial** smooth-max to the softplus /
  log-sum-exp form: softplus perturbs the surface everywhere and its curvature
  is unbounded as the blend narrows. Use the **cubic** (`h**3`) form, not the
  quadratic (`h*(1-h)`) one — the quadratic is only C1, so curvature JUMPS at
  the edge of the blend band, and a curvature jump on a specular surface draws
  a visible line.

## Closing a loft: a vertex puckers, a fused cap poisons

Two ways to close a loft's end both look fine and are not:

- **On a `Vertex`.** Every section's seam converges on the point and the
  surface dimples round it: a visible pucker in the middle of a snout or at a
  leaf's tip.
- **A cap fused onto the last section** (half an ellipsoid on the end face, or
  a whole one set a little back into the loft). The fuse succeeds and the
  solid is valid, but the cap's ring lies on or within hundredths of the
  loft's surface, and later booleans on the solid fail silently: a box cutting
  it in half returned nothing, and `split` kept the whole leaf, for some sizes
  and not others ([[boolean-pitfalls#near-tangent-and-near-coincident-surfaces-fail-quietly]]).

End the loft on a **small flat section** instead: pack stations towards the
end so the last is small enough to read as the tip and, for a toy, still wider
than the sharp-point probe. A tip that must be round is a profile whose width
falls as `(1 - s)^q` with `q < 1`, which is still round at the last station.

## A first section not square to the spine

A loft whose first section is not square to its spine (a horizontal start on
a leaning spine, like a witch hat's bent tip) split invalid on its symmetry
plane. A union with an end sphere of exactly the end radius then silently
returned a valid 89 mm^3 fragment. Keep every section square to the spine,
make the mating face square to the lean, and assert the volume after each
boolean.

## Booleans against a large lofted skin

A subtract against one large B-spline skin costs a full-surface
classification per tool: [[boolean-pitfalls#booleans-against-a-large-lofted-surface]].
