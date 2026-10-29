---
title: What a B-rep keeps and what it destroys
tags: [step, brep, recovery, reverse-engineering, parametric, symmetric-difference, surface]
aliases: [decompile step, recover source from step, design history, ap242, step recovery refusal]
sources:
  - skills/step-to-source/scripts/step_recover
  - skills/step-to-source/scripts/step_verify
  - ISO 10303-242 (AP242 design-history entities)
  - "toolchain: step-to-source fixtures recover planes and cylinders at 0.000000 % symmetric difference, and include an identical-volume wrong-part pair"
  - "toolchain: OCC booleans on near-coincident B-spline faces collapse to zero intersection (reproducible)"
  - skills/step-to-source/scripts/steplib.py (FUZZ_LADDER, compare)
related: [mesh-measurement, authoring-from-a-reference, mesh-to-step-conversion, occt-boolean-options, boolean-pitfalls]
updated: 2026-10-10
---

# What a B-rep keeps and what it destroys

Read before promising that a supplied STEP can be made parametric, or when a
recovery is refused. The order to re-parameterise a recovered entry in, and
why each step is verified on its own, is
`skills/step-to-source/references/what-survives.md`.

## Shape and source are two questions

"Can the shape be rebuilt?" and "can the source be recovered?" have different
answers. Treating them as one question is how a recovery gets oversold.

**Shape.** A STEP holds analytic surfaces with their true parameters. A bore
radius is the radius, not a value fitted to facets. A solid made of planes and
cylinders therefore rebuilds as the same solid: the toolchain's fixtures
recover at 0.000000 % symmetric difference with identical surface kinds.
Straight tapers (chamfers, countersinks, draft) also rebuild exactly, through
a ruled loft. Only surfaces that curve along the axis (fillets, freeform) are
approximated, and those are refused unless explicitly asked for.

**Source.** The export destroys everything that made the file *editable*, and
none of it can be inferred from the result:

| In the generator | In the STEP | Recovered as |
|---|---|---|
| `WHEEL_RADIUS = 27.0` | a cylinder of radius 27 | `27`, with no name and no meaning |
| `OUTER = INNER + WALL` | two radii | two literals; the relationship is gone |
| `cadfits.slot_for(AXLE_DIA, 0.25)` | a slot 0.25 wider than the axle | one number; the clearance is no longer a concept |
| `.fuse()`, `.cut()`, `.intersect()` | one boundary | a stack of slabs. A boolean is destructive, and its operands are not in the file |
| a part and its `mirror()` | two independent solids | two independent entries; nothing says they are a pair |
| `parts/`, `features/`, shared modules | one shape per solid | one flat entry per solid |
| a fillet applied to selected edges | torus faces | geometry, not a feature, until someone re-applies it |

The consequence that matters most in practice: **change one number and nothing
follows it**. A recovered entry runs correctly and is not parametric. Making it
parametric again is manual work, and it is the same work that was expensive
the first time.

AP242 does define a design-history entity. Substantially no CAD system exports
it, so assume it is absent rather than checking in hope.

## What a refusal is telling you

A refusal names the slab and the surface kind:

- **Curved taper (torus).** A fillet or round. Recover the sharp body and
  re-apply the blend in source, which is exact and parametric. Keeping the
  blend as lofted geometry is the fallback, and it has a reported cost.
- **No extrusion axis (sphere, freeform, multi-axis part).** The solid is not
  a stack of prisms in any orientation, so do not force it: re-author it from
  measurements. A purchased component that only has to be seated is not
  source at all. Seat it as a reference.
- **A profile curve that is neither a line nor an arc (ellipse, spline).**
  Usually the extrusion axis is slightly off rather than the shape being
  genuinely freeform: a cylinder cut on a tilted plane sections as an ellipse.
  Check the axis first. If the curve is real, author that profile by hand.
- **Topology that changes inside one slab** (a hole that starts or ends inside
  a taper). Give the feature its own boundary by splitting the model, or
  author the feature by hand.
- **A converted mesh of a mechanical part.** The common case, and neither
  freeform nor a tilted axis: tessellation left facets at every angle. The
  part is still simple to author, so re-author it. For a mechanical part
  converted from a mesh, expect this route. On one kit, 1 of the 7 simplest
  parts recovered. Refused does not mean hard.

**Surface kinds alone do not predict a refusal.** An M8 hex nut is the
counter-example. Its only tapers are cones, which loft exactly, yet it is
refused on a slab whose cross-section changes topology. Run the recovery
rather than predicting it.

## Why the comparison is a symmetric difference

Two solids can agree on volume, bounding box, face count and every surface
kind and still be different parts: move a bore 3 mm and all of those hold. The
material in one solid and not the other, measured both ways, cannot cancel
like that. That is why the symmetric difference is the number a comparison
exits on, and why volume deltas are reported but never decisive. The
toolchain's fixtures include exactly that pair (identical volume, wrong part),
so the property is checked, not just asserted.

Volume *is* the right measure for a mesh-to-STEP conversion
([[mesh-to-step-conversion#why-the-conversion-check-is-volume]]), because
there both shapes are meant to bound the same material and the mesh volume is
an independent reference.

## Near-coincident solids collapse the comparison

Booleans between two nearly coincident solids go degenerate, and that is the
normal case here, because a good rebuild matches its reference almost
everywhere: the closer it gets, the worse the boolean behaves. The collapse
is reported **as a number**: `symmetric diff 200%` with `missing` and `extra`
each equal to the full volume means zero intersection, not a 200 % error.
Two overlapping solids of positive volume cannot have an empty intersection,
so an empty one is a boolean that gave up. A 2D per-cut boolean fails the same
way, returning 0.0 even where both sections are the same annulus with areas
agreeing to 0.001 mm².

`step_verify` walks OpenCASCADE's fuzzy value up from exact, takes the first
value that gives a non-empty intersection, and reports which value answered,
so the precision floor under the result stays visible
([[occt-boolean-options#walk-the-fuzzy-value-up-from-exact]]). On analytic
recoveries (planes and cylinders) a rung answers. Between solids within
hundredths of a millimetre of each other across many B-spline faces none may:
every value from 1e-7 to 1e-2 left one such intersection smaller than exact
(1.4 mm³ → 0.0).

Tell that apart from a real miss: check that both solids are valid and
FORWARD-oriented, that each intersects itself and a box correctly, and that
their section areas agree. If all that holds, the geometry is right and the
boolean is not. Then measure the symmetric difference by point classification
instead: sample the union bounding box and ask each solid whether it contains
the point. Build **one** `BRepClass3d_SolidClassifier` per solid and reuse it
— constructing one per point runs at ~210 points/s and is unusable. Report the
sampling standard error alongside the figure, and record that the boolean
comparison ran and failed rather than quietly substituting the sampled
number: a comparison nothing could compute is a failure, never a number.
