---
title: Kernel validity checks
tags: [validity, brepcheck, bop-check, volume, inverted, shapefix, bounding-box, occ]
aliases: [is_valid, BRepCheck_Analyzer, BRepAlgoAPI_Check, negative volume, inverted solid, Null TopoDS_Shape, bbox]
sources:
  - skills/cad/references/build123d-modeling.md (validity and BOP-check sections; before the move)
  - "toolchain: build123d 0.10 on OCP 7.9 (Part(solid.wrapped) volume, Bnd_Box control-hull bounds)"
  - "toolchain: OCP 7.9 BRepBndLib.AddOptimal on Bezier and NURBS faces trimmed by a plane"
related: [boolean-pitfalls, modeling-failure-modes, construction-strategy, mass-properties-and-measurement, unmeshable-faces]
updated: 2026-10-05
---

# Kernel validity checks

A shape the kernel calls valid can still be inverted, BOP-faulty, or measured
wrong. Gate every boolean result with the checks below rather than trusting
the last operation.

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
step the operation down or skip it when the check fails.

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

## An ellipsoid's seam can make a sound fuse read as self-intersecting

Ellipsoids made by scaling a sphere (a leg, a paw, toes) and fused across one
another passed every other check and still failed `BRepAlgoAPI_Check` as
`selfIntersecting` (so `inspect validate` failed the part), and only for some
of the four legs. Two changes cleared it: fuse the pieces one at a time rather
than as one multi-tool union, and turn the sphere's seam meridian about its
pole before scaling so it faces away from where the other pieces cut it. With
the seam at +X or -X one leg or another still failed; turned to -Y all four
checked clean. The result depends on the seam, so run the same check the gate
runs on each built solid before writing the STEP, rather than after.
