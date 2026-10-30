---
title: Kernel validity checks
tags: [validity, brepcheck, bop-check, volume, inverted, shapefix, bounding-box, occ]
aliases: [is_valid, BRepCheck_Analyzer, BRepAlgoAPI_Check, negative volume, inverted solid, Null TopoDS_Shape, bbox]
sources:
  - skills/cad/references/build123d-modeling.md (validity and BOP-check sections; before the move)
  - "toolchain: build123d 0.10 on OCP 7.9 (Part(solid.wrapped) volume, Bnd_Box control-hull bounds)"
  - "toolchain: OCP 7.9 BRepBndLib.AddOptimal on Bezier and NURBS faces trimmed by a plane"
  - "experience: a revolve profile whose closing segment was collinear with its first failed the BOP check"
related: [boolean-pitfalls, modeling-failure-modes, construction-strategy, mass-properties-and-measurement, unmeshable-faces, freeform-surfaces-in-build123d, revolve-seam]
updated: 2026-10-12
---

# Kernel validity checks

A shape the kernel calls valid can still be inverted, BOP-faulty, or measured
wrong. Gate every boolean result with the checks below rather than trusting
the last operation.
Sphere and ellipsoid seams that make a sound fuse read as self-intersecting
are [[revolve-seam]].

## Validity is not positive volume

`Shape.is_valid` (and `BRepCheck_Analyzer`) can return **True for a shell with
a large negative volume** — an inverted orientation. Such a body exports and
renders as a hole in the world. Check both:

```python
def is_valid_shape(shape):
    return (shape is not None
            and BRepCheck_Analyzer(shape.wrapped).IsValid()
            and shape.volume > 0.0)
```

A boolean can also leave a body that is geometrically right but topologically
invalid — correct bounds and volume, one bad face. It survives until the next
boolean, which then fails with `Null TopoDS_Shape object` from a call nowhere
near the cause. `ShapeFix_Shape` repairs many of these.

A fillet on an invalid solid can do worse than raise: it can segfault the
interpreter inside `ChFi3d_FilBuilder` and take the whole build with it.
Check `is_valid` before every fillet on a body built from faces
([[freeform-surfaces-in-build123d#checks]]).

`scripts/inspect validate` runs both gates plus closure and self-intersection
over every occurrence. It measures volume **per solid**: an inverted member
inside a compound cancels against a sound one, so anything reading a
compound's aggregate volume sees nothing wrong.

## Gate tangency-prone results with the BOP check

`result.volume > 0` and even `BRepCheck_Analyzer.IsValid()` both accept
chamfer and V-groove-cut results whose skinny faces are BOP-faulty
(`BOPAlgo_SelfIntersect`, `BOPAlgo_TooSmallEdge`). The failure then surfaces
only in `scripts/inspect validate` (`selfIntersecting`), with no pointer to
the causing operation. After tangency-prone cuts and chamfers on wavy
outlines, gate with the same check validation uses — `BRepAlgoAPI_Check` — and
step the operation down or skip it when the check fails. It is far slower than
`BRepCheck_Analyzer` (minutes per body of a few hundred B-spline faces), so
run it per body during the build rather than meeting it at the gate; when it
fires it can name the whole solid and no face pair, which localises nothing.

**A fillet on a curved outline can pass every validity check and still poison
the cuts after it.** An R0.6 round along a chamfered face edge, over a
B-spline bulge of a plan outline, came back with two edges carrying a 10.2 mm
kernel tolerance. `is_valid` and validate both accepted it. The next
booleans went silently wrong: a pocket whose prism holds 175 mm³ removed
364 mm³, and a second pocket split the part into seven solids, one of them
of negative volume. Two checks catch it at the source. Read the largest
edge and vertex tolerance (`BRep_Tool.Tolerance`) after the round and refuse
anything above about 1e-3 mm. Then hold every cut to its own bookkeeping:
the volume removed must equal the cutter's prism volume. On that outline,
the fix was to keep the chamfer and drop the round.

## Part(solid.wrapped) has zero volume

Re-wrapping a bare `Solid` as `Part(solid.wrapped)` yields a shape whose
`.volume` is 0 (build123d 0.10), so volume-based guards silently discard real
geometry. Use the `Solid` directly as a compound child (Shape carries
`label`/`color`), or fuse before measuring.

## Face.is_valid is a property

`Face.is_valid` is a PROPERTY — calling `f.is_valid()` raises
`TypeError: 'bool' object is not callable`, which reads like a corrupt object.

## Bounding boxes over-report on B-spline faces

`Bnd_Box`'s ordinary `Add` bounds a B-spline face by its control hull, so it
over-reports — measured 0.56 mm too wide on a gear. Use
`BRepBndLib.AddOptimal_s` before freezing any bounding box into a validation
module.

build123d's `bounding_box()` is already optimal by default; the other
measurement traps are in [[mass-properties-and-measurement]].

Not always: a revolved spline solid cut by a half-space reported its
**untrimmed** surface even with `bounding_box(optimal=True)` — Y max 92.9 mm on
a tray whose furthest vertex, and whose cutting plane, was at 54.6 mm. Sampling
`face.position_at(u, v)` over the parameter range reads the untrimmed surface
too. For a trimmed revolve, read extents from `vertices()` or edges, and keep
the box for untrimmed lofts.

The cause is general: OCC bounds a freeform face by the parameter rectangle
round its trimming wire, so a B-spline or Bezier face trimmed *across* its
parameter lines still counts the part of its surface the trim removed. A
smooth skin of Bezier patches cut flat at Z = 0 read min(Z) -3.1 mm (six
patches crossing the cut), and a NURBS sphere tilted and cut by a plane reads
as the whole sphere. Vertices and edges are not enough when the extreme lies
inside a face; the exact extent is a distance query against a plane just
outside each side of the loose box (`BRepExtrema_DistShapeShape`), which is
what the print gates' `printlib.tight_box` does.

## A zero-volume cutter is a silent no-op

A subtraction whose tool sits entirely above the surface, or a clip that
returned an empty list, removes nothing and raises nothing. Assert the volume
change of every feature cut you rely on (see
[[sketch-and-extrude-direction#align-none-is-the-raw-occ-datum]] for the most
common cause).

What the kernel means by shape types, orientation and tolerance: [[occt-topology-and-tolerance]]; repairing imported shapes: [[occt-shape-healing]].

## A zig-zag revolve profile self-intersects silently

A stacked-tier outline (a fir tree, a pagoda) drawn as one zig-zag polygon and
revolved builds without error but `validate` reports `selfIntersecting` when a
tier's underside is steeper than the next tier's cone: the two conical faces
cross inside the solid. Revolve one simple polygon per tier, union them with a
core that passes through the notch points, and stop each tier's cone at the
next notch; a cone left running to the axis pokes a sliver through the tip.

## Collinear segments in a revolve profile

A profile with two consecutive collinear segments revolves into two faces on
the same cone, and `BRepAlgoAPI_Check` fails it. This includes the closing
segment back to the first point. Merge collinear runs cyclically before
revolving. A 2D `offset(kind=Kind.INTERSECTION)` of such a profile also fails.
