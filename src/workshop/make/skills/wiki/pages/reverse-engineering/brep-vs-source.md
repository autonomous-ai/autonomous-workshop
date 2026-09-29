---
title: What a B-rep keeps and what it destroys
tags: [step, brep, recovery, reverse-engineering, parametric, symmetric-difference, surface]
aliases: [decompile step, recover source from step, design history, ap242, step recovery refusal]
sources:
  - skills/step-to-source/scripts/step_recover
  - skills/step-to-source/scripts/step_verify
  - ISO 10303-242 (AP242 design-history entities)
  - "toolchain: step-to-source fixtures recover planes and cylinders at 0.000000 % symmetric difference, and include an identical-volume wrong-part pair"
related: [mesh-measurement, authoring-from-a-reference, mesh-to-step-conversion]
updated: 2026-09-23
---

# What a B-rep keeps and what it destroys

Read before promising that a supplied STEP can be made parametric, when a
recovery is refused, or before re-parameterising a recovered entry.

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

## Why re-parameterising runs in a fixed order

Naming the dimensions and restoring the relationships must not move a single
face. Re-applying fillets and chamfers deliberately changes the surface kinds.
So the first two steps are verified against the original STEP one at a time.
Otherwise a typo in step 1 surfaces in step 3 as a mystery. For step 3, expect
the face-kind lines to differ and the volume to move by the blend volume.
Re-applying a fillet in source also fixes an approximated fillet: recover the
sharp body, fillet it in source, and the result is both exact and editable.

Naming every vertex is noise, not parametrisation. Hoist the numbers that
carry meaning and leave incidental profile coordinates alone. Never type both
halves of a mate independently. A recovered file arrives full of exactly that
defect, because the relationship between the halves was lost at export.

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

Booleans between two nearly coincident solids go degenerate. That is the
normal case here, because a good recovery matches almost everywhere. Escalate
OpenCASCADE's fuzzy value only as far as needed, and report which value
answered, so the precision floor under the result stays visible. When no
tolerance can compute the comparison, report it as a failure, never as a
number.

Volume *is* the right measure for a mesh-to-STEP conversion
([[mesh-to-step-conversion#why-the-conversion-check-is-volume]]), because
there both shapes are meant to bound the same material and the mesh volume is
an independent reference.
